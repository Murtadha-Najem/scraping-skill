"""Offline self-test for scrapekit. Run:  python selftest.py   (no network needed)."""
import os
import sys
import tempfile
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scrapekit as sk

sk.utf8_stdio()
fails = []


def check(name, cond):
    print(("PASS  " if cond else "FAIL  ") + name)
    if not cond:
        fails.append(name)


# classify: a 200 with the wrong type is not "no data"
check("200 json ok", sk.classify(200, "application/json; charset=utf-8", "json") == sk.OK)
check("200 html when json expected is WRONG_TYPE", sk.classify(200, "text/html", "json") == sk.WRONG_TYPE)
check("429 is RATE", sk.classify(429, "", "json") == sk.RATE)
check("403 is FORBIDDEN", sk.classify(403, "", "json") == sk.FORBIDDEN)
check("404 is GONE", sk.classify(404, "", "json") == sk.GONE)

# rate limiter: never more than max_calls in any window, across threads
lim = sk.RateLimiter(5, per_seconds=1.0)
stamps, lock = [], threading.Lock()


def worker():
    for _ in range(5):
        lim.acquire()
        with lock:
            stamps.append(time.monotonic())


ts = [threading.Thread(target=worker) for _ in range(3)]
[t.start() for t in ts]
[t.join() for t in ts]
stamps.sort()
worst = max(sum(1 for s in stamps if t0 <= s < t0 + 1.0) for t0 in stamps)
check("15 calls at 5/s across 3 threads: max in any 1s window <= 5 (got %d)" % worst, worst <= 5)
check("15 calls at 5/s took about 2s or more (got %.1fs)" % (stamps[-1] - stamps[0]), stamps[-1] - stamps[0] >= 1.9)

sm = sk.RateLimiter(10, per_seconds=1.0, smooth=True)
sm_stamps = []
for _ in range(6):
    sm.acquire()
    sm_stamps.append(time.monotonic())
span = sm_stamps[-1] - sm_stamps[0]
check("smooth limiter spaces 6 calls at 10/s over about 0.5s, not a burst (got %.2fs)" % span, 0.45 <= span <= 0.9)
burst = sk.RateLimiter(10, per_seconds=1.0)
b0 = time.monotonic()
for _ in range(6):
    burst.acquire()
check("default limiter allows the burst (6 calls in %.2fs)" % (time.monotonic() - b0), time.monotonic() - b0 < 0.2)

lim2 = sk.RateLimiter(100, per_seconds=60)
lim2.pause_all(0.4)
t0 = time.monotonic()
lim2.acquire()
check("pause_all blocks the next acquire (%.2fs)" % (time.monotonic() - t0), time.monotonic() - t0 >= 0.35)

with tempfile.TemporaryDirectory() as d:
    # jsonl survives a truncated last line
    p = os.path.join(d, "out.jsonl")
    w = sk.JsonlWriter(p, flush_every=1)
    for i in range(3):
        w.write({"id": i, "t": "عربي"})
    w.close()
    with open(p, "a", encoding="utf-8") as f:
        f.write('{"id": 3, "t": "cut off')
    check("read_jsonl skips a truncated tail and keeps Arabic", [r["id"] for r in sk.read_jsonl(p)] == [0, 1, 2])
    check("done_keys reads the file, not memory", sk.done_keys(p) == {0, 1, 2})

    # atomic write
    cp = os.path.join(d, "state", "cp.json")
    sk.atomic_write_json(cp, {"done": [1, 2], "n": "عراق"})
    check("atomic_write_json leaves no temp files", [f for f in os.listdir(os.path.dirname(cp)) if f.endswith(".tmp")] == [])

# unique names: two different Arabic inputs must not collide
names = sk.unique_names(["تقرير ٢٠٢٣", "تقرير ٢٠٢٤", "ملف"], ".json")
check("unique_names distinct for non-Latin inputs", len(set(names)) == 3)

# guards
class Box:
    def __init__(self, a): self.a = a
    def __call__(self): return self.a

g = sk.DryStreakGuard(sk.Canary(Box(True)), threshold=3)
for _ in range(10):
    g.record(False)
check("dry streak with canary served: keeps going", True)

g = sk.DryStreakGuard(sk.Canary(Box(False)), threshold=3)
raised = False
try:
    for _ in range(3):
        g.record(False)
except sk.StopRun:
    raised = True
check("dry streak with canary NOT served: StopRun", raised)

g = sk.DryStreakGuard(sk.Canary(Box(None)), threshold=3)
try:
    for _ in range(9):
        g.record(False)
    ok = True
except sk.StopRun:
    ok = False
check("inconclusive canary never trips the guard", ok)

# shared token: a burst of 401s renews once
mints = []
tok = sk.SharedToken(lambda: mints.append(1) or "T%d" % len(mints))
seen = tok.get()
for _ in range(5):
    tok.refresh(seen)
check("SharedToken renews once for 5 stale holders (mints=%d)" % len(mints), len(mints) == 2)

# reconciler
r = sk.Reconciler()
r.stage("extract", 100)
check("reconciler flags a mismatch", r.stage("load", 98) is False)

print("\n%d failed" % len(fails) if fails else "\nall passed")
sys.exit(1 if fails else 0)
