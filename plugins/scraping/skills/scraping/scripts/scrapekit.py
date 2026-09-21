"""scrapekit: the small pieces every collector needs. Standard library only.

Import it from a collector:  sys.path.insert(0, SKILL_DIR / "scripts"); import scrapekit

Each piece exists because a real run failed without it. The reference that explains
the failure is named next to it. Nothing here does networking; pass in your own
`get` function (requests, httpx, curl_cffi all work).
"""
import hashlib
import json
import os
import sys
import tempfile
import threading
import time
from collections import deque


def utf8_stdio():
    """Call first. The Windows console defaults to cp1252 and dies on Arabic (durability.md)."""
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass


# ---------------------------------------------------------------- verdicts
OK = "ok"                # status 200 and the media type we expected
WRONG_TYPE = "wrong_type"  # 200 but not what we asked for: a block page, an SPA shell, a bad parameter
RATE = "rate"            # 429 or 503
FORBIDDEN = "forbidden"  # 401 or 403
GONE = "gone"            # 404 or 410: NEVER final on one sighting
SERVER = "server"        # other 5xx
OTHER = "other"


def classify(status, content_type, expect="json"):
    """Map a response to a verdict. A 200 with the wrong media type is its own verdict and
    must never fall through to 'no data' (transport.md, the silent-failure section)."""
    ct = (content_type or "").lower()
    if status == 200:
        wanted = {"json": "json", "html": "html", "xml": "xml", "text": "text", "any": ""}[expect]
        return OK if wanted in ct else WRONG_TYPE
    if status in (429, 503):
        return RATE
    if status in (401, 403):
        return FORBIDDEN
    if status in (404, 410):
        return GONE
    if 500 <= status < 600:
        return SERVER
    return OTHER


def guarded_get(get, url, expect="json", limiter=None, bodies_dir=None, pause=8.0, refresh=None):
    """One request with the retry rule from the lessons.

    Ambiguous answers (WRONG_TYPE, RATE) are retried ONCE after a short pause, calling
    `refresh()` first if given (new token, new session). If it recurs it is returned as-is,
    which the caller records as a failure, never as an empty result. The body of any
    non-OK answer is saved to `bodies_dir`, because the body often names the layer that
    refused you (read-the-error-body lesson).
    Returns (verdict, response).
    """
    resp = None
    for attempt in (0, 1):
        if limiter:
            limiter.acquire()
        resp = get(url)
        verdict = classify(resp.status_code, resp.headers.get("content-type", ""), expect)
        if verdict != OK and bodies_dir:
            save_body(bodies_dir, url, resp)
        if verdict not in (WRONG_TYPE, RATE) or attempt == 1:
            return verdict, resp
        if limiter:
            limiter.pause_all(pause)
        time.sleep(pause)
        if refresh:
            refresh()
    return verdict, resp


def save_body(bodies_dir, url, resp, limit=20000):
    os.makedirs(bodies_dir, exist_ok=True)
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
    path = os.path.join(bodies_dir, "%d_%s.txt" % (resp.status_code, digest))
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("URL: %s\nSTATUS: %s\nHEADERS: %s\n\n" % (url, resp.status_code, dict(resp.headers)))
            f.write((resp.text or "")[:limit])


# ---------------------------------------------------------------- pacing
class RateLimiter:
    """One process-wide limiter shared by all threads: at most `max_calls` per `per_seconds`.

    Use this instead of sleep(N) after each request (fixed sleeps add to latency and use a
    fraction of the published allowance). Set max_calls a little under the published limit.
    `pause_all(s)` blocks every thread, so one 429 stops the whole pool, not one worker.
    Benchmark for 2 to 3 windows, not one: a fresh bucket allows a burst that flatters the rate.
    """

    def __init__(self, max_calls, per_seconds=60.0, smooth=False):
        # smooth=True also spaces calls evenly (per_seconds / max_calls apart) instead of allowing a
        # full-window burst at the start. Use it for polite pacing on fragile servers.
        self.max_calls, self.per, self.smooth = max_calls, per_seconds, smooth
        self.times = deque()
        self.lock = threading.Lock()
        self.blocked_until = 0.0
        self.next_slot = 0.0

    def pause_all(self, seconds):
        with self.lock:
            self.blocked_until = max(self.blocked_until, time.monotonic() + seconds)

    def acquire(self):
        while True:
            with self.lock:
                now = time.monotonic()
                if now < self.blocked_until:
                    wait = self.blocked_until - now
                elif self.smooth and now < self.next_slot:
                    wait = self.next_slot - now
                else:
                    while self.times and now - self.times[0] >= self.per:
                        self.times.popleft()
                    if len(self.times) < self.max_calls:
                        self.times.append(now)
                        if self.smooth:
                            self.next_slot = now + self.per / self.max_calls
                        return
                    wait = self.per - (now - self.times[0]) + 0.01
            time.sleep(max(0.01, wait))


class SharedToken:
    """A credential shared by many workers, refreshed compare-and-swap so a burst of 401s
    renews it once, not once per worker. Give each worker its own HTTP client."""

    def __init__(self, mint):
        self.mint, self.value, self.lock = mint, None, threading.Lock()

    def get(self):
        with self.lock:
            if self.value is None:
                self.value = self.mint()
            return self.value

    def refresh(self, seen):
        with self.lock:
            if self.value == seen:   # nobody renewed it since we read it
                self.value = self.mint()
            return self.value


# ---------------------------------------------------------------- storage
class JsonlWriter:
    """Append one JSON record per line, flush every `flush_every`. Plain text on purpose:
    a killed run loses at most the last line, where gzip or a JSON array loses everything
    after the last complete frame. Compress AFTER the run."""

    def __init__(self, path, flush_every=50):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.f = open(path, "a", encoding="utf-8")
        self.n, self.flush_every, self.lock = 0, flush_every, threading.Lock()

    def write(self, rec):
        with self.lock:
            self.f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            self.n += 1
            if self.n % self.flush_every == 0:
                self.f.flush()

    def close(self):
        with self.lock:
            self.f.flush()
            self.f.close()


def read_jsonl(path):
    """Yield records, skipping a truncated or corrupt line instead of dying on it."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except ValueError:
                continue


def done_keys(path, key="id"):
    """Resume by unit: what is finished is read from the output file itself."""
    return {r[key] for r in read_jsonl(path) if key in r}


def atomic_write_json(path, obj):
    """Temp file then rename, so a kill mid-write cannot leave a half-written checkpoint."""
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
    os.replace(tmp, path)


def unique_names(inputs, ext=""):
    """Output names that cannot collide: index plus a digest of the original. Sanitising a
    non-Latin name to ASCII maps different inputs to one name, and the second silently
    overwrites the first (it cost 57,554 rows once). Asserts distinctness before any write."""
    names = ["%05d_%s%s" % (i, hashlib.sha1(str(x).encode("utf-8")).hexdigest()[:8], ext)
             for i, x in enumerate(inputs)]
    assert len(set(names)) == len(inputs), "output names collide"
    return names


# ---------------------------------------------------------------- guards
class StopRun(Exception):
    """Raised by a guard when the run's own assumption has failed. Stop, do not log and continue."""


class Canary:
    """A known-good unit that must still come back. `fetch_known()` returns True when a
    record we already hold is still served, False when it is not, and None when the answer
    is inconclusive (429, network error). Counting misses cannot tell a dry stretch of
    id space from a broken request shape; asking for something that is known to exist can."""

    def __init__(self, fetch_known):
        self.fetch_known = fetch_known

    def check(self):
        return self.fetch_known()


class DryStreakGuard:
    """After `threshold` consecutive results with nothing found, ask the canary.
    served       -> the dry stretch is real, reset and carry on
    not served   -> the request shape is wrong, raise StopRun (writes no more false negatives)
    inconclusive -> neither answer, keep going and ask again at the next threshold
    """

    def __init__(self, canary, threshold=200):
        self.canary, self.threshold, self.streak = canary, threshold, 0

    def record(self, found):
        if found:
            self.streak = 0
            return
        self.streak += 1
        if self.streak >= self.threshold:
            answer = self.canary.check()
            if answer is True:
                self.streak = 0
            elif answer is False:
                raise StopRun("canary not served after %d empty results: request shape or access changed"
                              % self.streak)
            else:
                self.streak = 0   # inconclusive: do not trip on our own transient errors


class Reconciler:
    """Every stage announces a count; each must equal the stage before, or you can say why.
    Rows silently overwritten between stages and a file counted twice were both found this way."""

    def __init__(self):
        self.last = None

    def stage(self, name, n, expect_equal_to_previous=True, why=""):
        note = ""
        if self.last is not None and expect_equal_to_previous and n != self.last[1]:
            note = "  <-- MISMATCH with %s (%s)%s" % (self.last[0], self.last[1], (" " + why) if why else "")
        print("[count] %-28s %d%s" % (name, n, note))
        self.last = (name, n)
        return not note
