"""runner_template.py: a resumable collector skeleton. Copy it next to your project and edit extract().

    python runner_template.py --urls urls.txt --out data --rpm 60 --workers 4 --limit 20
    python runner_template.py --urls urls.txt --out data --rpm 60 --workers 4      # same command resumes

What it already does (each line is a lesson from reference/durability.md):
  * resume by unit: what is done is read from data/records.jsonl, so re-running is always the recovery
  * a failure is never "done": failures go to data/failures.jsonl with the reason, and come back next run
    until --max-fail is reached; the retry set is derived from state, not from "seen this pass"
  * 200 with the wrong media type is a failure, never "no data"; an extract() that finds nothing is a failure
  * error bodies are saved to data/bodies/ (the body often names the layer that refused you)
  * raw response saved beside the extracted record, so a field you forgot can be re-derived without refetching
  * one shared rate limiter, per-thread sessions, plain JSONL appended and flushed, atomic state file
  * a canary (--canary URL, a page known to exist) stops the run if the request shape breaks
  * every stage prints its count and reconciles it against the stage before
  * Ctrl-C drains cleanly; use SIGINT, never SIGKILL, when stopping it on a server

One record per URL. For listing then detail pages, run it in passes: pass 1 on the listing URLs, then build the
detail URL list from pass 1's records (or from the saved raw HTML, no refetch) and run it again on that list with
its own --out. Test plural and zero cases in extract() ("1 result" versus "2 results"): a regex that matched only
the plural silently marked ten records as missing a field on a practice site.
"""
import argparse
import hashlib
import os
import signal
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scrapekit as sk

try:
    from selectolax.parser import HTMLParser
except Exception:
    HTMLParser = None


def make_get(impersonate):
    """One session per thread. curl_cffi with Chrome impersonation if asked, plain requests otherwise."""
    local = threading.local()

    def get(url):
        if not hasattr(local, "s"):
            if impersonate:
                from curl_cffi import requests as cffi
                local.s = cffi.Session(impersonate="chrome")
            else:
                import requests
                local.s = requests.Session()
        r = local.s.get(url, timeout=30)
        # A text/html answer with no charset makes `requests` guess latin-1 and mojibake the text
        # (a pound sign came out garbled on a practice site). Assume UTF-8 unless the server said otherwise.
        if "charset" not in (r.headers.get("content-type") or "").lower():
            r.encoding = "utf-8"
        return r
    return get


def extract(html, url):
    """EDIT ME. Return a dict of fields, or None/{} if the page holds nothing usable (that is a failure,
    not an empty result). Read table columns by header label, never by position."""
    tree = HTMLParser(html)
    title = tree.css_first("title")
    h1 = tree.css_first("h1")
    rec = {"title": title.text(strip=True) if title else None, "h1": h1.text(strip=True) if h1 else None}
    return rec if any(rec.values()) else None


def main():
    sk.utf8_stdio()
    ap = argparse.ArgumentParser()
    ap.add_argument("--urls", required=True, help="one URL per line; the URL is the unit id")
    ap.add_argument("--out", default="data")
    ap.add_argument("--rpm", type=int, default=60, help="requests per minute, set a little under the published limit")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--smooth", action="store_true", help="space requests evenly instead of allowing a burst")
    ap.add_argument("--limit", type=int, default=0,
                    help="fetch at most N NEW units this run (the same command again fetches the next N)")
    ap.add_argument("--max-fail", type=int, default=3)
    ap.add_argument("--impersonate", action="store_true", help="curl_cffi Chrome TLS (copy what a real browser sends)")
    ap.add_argument("--canary", help="a URL that is known to exist; a dry streak asks it before giving up")
    ap.add_argument("--expect", default="html", choices=["html", "json", "xml", "text"])
    a = ap.parse_args()

    os.makedirs(os.path.join(a.out, "raw"), exist_ok=True)
    rec_path = os.path.join(a.out, "records.jsonl")
    fail_path = os.path.join(a.out, "failures.jsonl")
    bodies = os.path.join(a.out, "bodies")

    units = [u.strip() for u in open(a.urls, encoding="utf-8") if u.strip()]
    units = list(dict.fromkeys(units))                       # stable de-dup
    raw_name = {u: hashlib.sha1(u.encode("utf-8")).hexdigest()[:12] + ".html" for u in units}
    assert len(set(raw_name.values())) == len(units), "raw file names collide"

    done = sk.done_keys(rec_path, "id")
    fails = {}
    for r in sk.read_jsonl(fail_path):
        fails[r["id"]] = fails.get(r["id"], 0) + 1
    todo = [u for u in units if u not in done and fails.get(u, 0) < a.max_fail]
    parked = [u for u in units if u not in done and fails.get(u, 0) >= a.max_fail]
    print("[plan] units=%d done=%d todo=%d parked(after %d failures)=%d" % (
        len(units), len(done & set(units)), len(todo), a.max_fail, len(parked)))
    if a.limit:
        todo = todo[:a.limit]

    get = make_get(a.impersonate)
    limiter = sk.RateLimiter(a.rpm, 60.0, smooth=a.smooth)
    writer, fwriter = sk.JsonlWriter(rec_path, 20), sk.JsonlWriter(fail_path, 1)
    stop = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: (print("\n[stop] draining..."), stop.set()))
    lock, counts = threading.Lock(), {"ok": 0, "failed": 0}

    def canary_fetch():
        if not a.canary:
            return None
        try:
            v, _ = sk.guarded_get(get, a.canary, a.expect, limiter, bodies)
        except Exception:
            return None
        return True if v == sk.OK else (None if v in (sk.RATE, sk.SERVER) else False)

    guard = sk.DryStreakGuard(sk.Canary(canary_fetch), threshold=50)

    def work(u):
        if stop.is_set():
            return
        try:
            verdict, resp = sk.guarded_get(get, u, a.expect, limiter, bodies)
        except sk.StopRun:
            raise
        except Exception as e:                                # network error is a failure, not an empty result
            verdict, resp = "error:%s" % type(e).__name__, None
        rec = None
        if verdict == sk.OK:
            rec = extract(resp.text, u)
            if rec:
                with open(os.path.join(a.out, "raw", raw_name[u]), "w", encoding="utf-8") as f:
                    f.write(resp.text)
                rec = dict(rec, id=u, raw=raw_name[u])
        with lock:
            try:
                guard.record(rec is not None)
            except sk.StopRun as e:
                print("[STOP] %s" % e)
                stop.set()
            if rec:
                writer.write(rec)
                counts["ok"] += 1
            else:
                fwriter.write({"id": u, "reason": verdict if verdict != sk.OK else "empty_extract"})
                counts["failed"] += 1

    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(work, todo))
    writer.close()
    fwriter.close()

    now_done = sk.done_keys(rec_path, "id")
    rc = sk.Reconciler()
    rc.stage("units in this pass", len(todo))
    rc.stage("ok + failed this pass", counts["ok"] + counts["failed"], why="(a StopRun or Ctrl-C leaves some untouched)")
    rc.stage("records on disk (total)", len(now_done & set(units)), expect_equal_to_previous=False)
    sk.atomic_write_json(os.path.join(a.out, "state.json"),
                         {"units": len(units), "done": len(now_done & set(units)), "last_pass": counts})
    print("[done] ok=%d failed=%d  (failures are listed with reasons in %s and are retried next run)" % (
        counts["ok"], counts["failed"], fail_path))


if __name__ == "__main__":
    main()
