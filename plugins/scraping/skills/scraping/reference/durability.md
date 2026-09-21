# Designing for the run that dies

Assume every long run gets killed. Not "might": the laptop sleeps, the network drops, somebody closes the lid, or you interrupt it yourself to fix something. The design goal that follows is small and strict: **re-running the same command must always be the correct recovery**, with no
arguments to remember and no judgement needed at 2 a.m. `scripts/scrapekit.py` and `scripts/runner_template.py` implement what follows; start from them.

## State comes from what is on disk, not from what the process remembers

- **Append-safe records.** Plain JSONL, one record per line, flushed periodically. A compressed append-only file lost 13,000 records when a run was killed mid-write, because everything after the last complete frame became unreadable; plain lines lose one line, which a tolerant reader skips
  (`scrapekit.read_jsonl`). Compress afterwards. Any format with global framing, a trailer, or one enclosing array has this failure.
- **Checkpoint per unit, atomically.** An index written only at the end means a job killed at 95% produced nothing. Write to a temporary file and rename over the target (`scrapekit.atomic_write_json`) so a kill mid-write cannot leave a half-written index, which is worse than none.
- **Resume by unit, not by position.** Record which units are done, and read that from the output file itself (`scrapekit.done_keys`). "How far through was I" is a fact about a process that no longer exists.
- **Derive the work queue from the desired end state, not from the discovery event.** Failed items were never retried because the retry list was "items seen this pass", and a failed item had already been recorded so was no longer new. Define pending as "still missing the thing I want",
  with a failure counter so a permanently broken unit becomes visible instead of being retried forever. A failure is then temporary by construction instead of permanent by accident.
- **A unit is done only when it produced a payload or emptiness was confirmed.** If the fetch layer can fail silently, the loop marks everything complete with zero data and the progress file is poisoned: a restart skips it all. So keep three things apart, expensive discovery (`reference/`), per-item
  progress (`state`) and results (`raw/`), which lets you delete poisoned progress without paying to rediscover.
- **Keep a failures file with reasons** (`404`, `wrong_type`, `retries-exhausted`). Whether the problem is yours or the source's is visible in the distribution.
- **Watch progress from an append-only file.** `wc -l records.jsonl` is always safe; a state file rewritten often is regularly mid-write and fails intermittently.
- **Enumerate input files explicitly.** A glob's meaning widens as the directory grows; one pulled four regions into one and inflated a city's count by a third. List the inputs and assert the count.

## Silent failure is the expensive kind

- **A 200 with the wrong media type is a failure, never "no data".** SPAs and CDNs answer blocked, throttled or unmatched requests with an HTML page at status 200. Code that branched on the status found no records in a document it never parsed, recorded an empty result for every unit,
  and finished with green output and zero data. Branch on status and type together (`scrapekit.classify`), and make "200 but wrong type" its own path.
- **Retry the ambiguous answer once**, after a short pause and with fresh credentials. If it recurs, classify it "not available" and move on. A genuine block clears on retry; an invalid request never will, and without this bound every bad request costs the full back-off times thousands of requests
  (`scrapekit.guarded_get`).
- **A zero hit rate is a broken run.** The used-car site backfill ran ten hours finding nothing and wrote 127,998 false "gone" rows in a day against 7,858 and 2,557 the days before. A placeholder slug used a million times had become a signature and been blocklisted. The tool held the evidence and had no rule to act on it.
- **But a dry stretch is not always broken, and counting cannot tell them apart.** The first guard ("stop after N with no hit") aborted twice on genuinely empty stretches of id space: eight of eight ids already held still came back, twelve of twelve in the swept block did not. The corrected question is not
  "how long since the last hit" but "does something I know exists still come back?" So keep a small sample of records you already hold and, when the dry streak reaches a threshold, request one. Served: the stretch is real, reset and go on. Not served: the request shape is wrong, stop. A 429 or a network error is
  inconclusive and must not trip the guard, since a guard that trips on its own transient errors is worse than none (`scrapekit.DryStreakGuard` and `Canary`; the runner takes `--canary URL`). The floor must be a diagnosis, not a count.
- **A parameter that returns 200 may be ignored.** Diff the response with and without it.
- **An alert that cannot fail loudly is not an alert.** The wrapper checks the notifier's exit code and falls back to a raw `curl` when the notifier is broken; this happened, it was not hypothetical.

## Speed and cost are measurements

- **One process-wide limiter plus a few workers, not `sleep(N)`.** A 1.1 s sleep with a 0.4 s response is 40 requests a minute against an allowance of 100, so a 21-hour job took 31. The limiter enforces the ceiling while workers hide latency; set the target a little under the published limit.
  `scrapekit.RateLimiter(max_calls, per_seconds)`; `pause_all(s)` blocks every thread on a 429 so the others stop hitting the wall. The default allows a full-window burst first; `smooth=True` (the runner's `--smooth`) spaces calls evenly, which is kinder to a fragile server.
- **Measure sustained rate over two or three windows**, because a fresh token bucket permits a burst (a 67-second test showed 107 a minute against a configured 80). Or compute the estimate from the configured rate and unit-test the limiter's maximum per window instead of inferring it from wall-clock time.
- **Measure in units per second**, not requests per second: that predicts when the job finishes.
- **One credential, many workers:** each worker gets its own client (sessions are not thread-safe), and the shared token refreshes compare-and-swap (`scrapekit.SharedToken`) so a burst of 401s renews it once.
- **Smaller is not faster.** A change that made responses 30% smaller made the job six times slower, because it bypassed a cache; it had been recommended on size alone. Time both ways, end to end, on the real workload. Measure the outcome you care about, not a proxy that is easy to see.
- **Concurrency is a property of the source, and sometimes of your own machine.** The local Google Maps scraper ran 61 places a minute at 6 workers (85% CPU) and 53 at 12 (92% CPU): doubling made it slower because headless Chromium saturates the processor.
  Set it near logical cores minus two, capped by RAM at about 0.35 GB per worker.
- **Money.** Test that a field is populated at source before paying to enrich it: an upgrade bought for opening hours, amenities and descriptions moved all three by zero points because the owners had never filled them in. Pay for what you do not have rather than improving what you have: a field absent from
  the free layer went 0% to 55%, a field already present went 36% to 40%, at the same cost per record. Every filter or option may bill separately per record, and the advertised rate may not be your tier's. Batch billed work into one run, because de-duplication happens within a run and not across runs
  (five runs over one area cost 1.61 times one run). And a ten-cent sample outranks any argument: two paid tests cost $0.18 in total and redirected a $29 budget. Always set a hard per-run charge ceiling as a circuit breaker against a bug in your own query.

## Running long jobs

1. **Run a small end-to-end slice first**, a hundred records. Most bugs appear in the first hundred.
2. **Prove resumability by restarting, not by reading the code.** Run a slice (`--limit 5`), run the same command without the limit and confirm it fetches only the remainder, run it once more and confirm it does nothing, and check the on-disk count equals the union. (`--limit N` means "at most N new units this
   run", so repeating a limited command fetches the next N.) A stronger proof: kill the run with SIGKILL mid-way and restart. A tester did, on a 1,000-record detail pass: 240 records against 245 raw files, and the next run re-fetched the missing five and ended at exactly 1,000.
3. **Prevent sleep** on a laptop; it is the commonest cause of failed overnight runs.
4. **Show real progress with time remaining**, so the person can tell running from hung, and monitor from output files.
5. **Ownership follows duration.** Run minutes-long work yourself and report. For hours-long work verify a slice and hand over one exact command with the estimate and prerequisites. When told not to run things in the background, stop the ones already running and say so.
6. **A package for another machine** must be extracted to a clean directory outside the project and run there, entry point by entry point. Listing the archive proves the files are present, not that it runs. Hand large deliverables over as a path with a checksum, not as an attachment (two failed attachments left 22-byte empty archives).
7. **Do not create logs or persistent records on someone's personal machine** without asking; the time to add them is when the work moves to infrastructure the organisation controls.
8. If someone says a feature is missing that is present, look for the delivery defect (the documented command discarded its output; the labels rendered as garbage) before asserting it is there.

## Windows and terminals

Force UTF-8 at the top of every script (`scrapekit.utf8_stdio()`): the console defaults to cp1252 and any Arabic print raises `UnicodeEncodeError` and aborts a script after the real work succeeded. For throwaway analysis write the report to a UTF-8 file and read that.
Keep progress-bar labels in ASCII, since Arabic mixed with bar characters renders reversed or as boxes on `cmd.exe` and the person concludes "there is no progress bar". `tqdm` writes to stderr, so `python x.py > log.txt 2>&1` swallows the bar and the screen stays blank for hours: do not document that command for a long run,
use `tee`, and emit log lines through `tqdm.write`. Do not open a 65 MB file with a read tool. Write source files with a file-writing tool, not shell heredocs, when they hold quotes, backslashes or non-ASCII. Do not diagnose a bug from the output of a process you killed with a timeout: cleanup errors are artefacts of the kill.

## On a server

A nightly capture on a small Ubuntu server is a good reference design.

- **A systemd timer with a named zone:** `OnCalendar=*-*-* 00:00:00 Asia/Baghdad` (the host runs UTC) and `Persistent=true`, so a night missed to a reboot runs on the next boot.
- **Stop with SIGINT, never SIGKILL.** SIGKILL cannot be caught, so the collector dies without flushing. Use `timeout --signal=INT` and `KillSignal=SIGINT`. In a wrapper script run the collector in the background and trap the stop to forward one SIGINT, because `KillMode=mixed` signals only the wrapper and a shell
  waiting on a foreground command does not pass it on (systemd waited its five-minute timeout and killed everything, twice).
- **A long `Type=oneshot` unit holds `apt` hostage.** systemd keeps a oneshot in "activating" until ExecStart exits, so a needrestart after a library upgrade waited hours holding `dpkg/lock-frontend` and blocked another project's deploy. Prefer `Type=simple`, or short units started by a timer.
- **Leave room between jobs that share resources** (a 23:30 stop for a 00:00 job), with `Conflicts=` as the backstop and not the plan.
- **Alerts:** silent on a good night, because an alert that fires nightly is read by nobody. Name each hard failure in plain language ("every detail request was refused, usually expired proxies", not "scraper failed") and attach the cycle log. Add `OnFailure=` for a wrapper killed before it can report.
  Keep credentials in a mode-600 file, never in a script.
- **Quiet failures need their own checks:** a field the site stopped sending (judged per door: list-only fields legitimately read 0% on the other), and volume outside normal (compare against the same weekday using a median, because Fridays are thin, and require a relative, an absolute and a robust-spread test together;
  judge nothing before about 12 nights of history; keep one record per date so test runs cannot poison the baseline, which is how a false "1114% off" alert happened).
- **A rebuild must not decide the night's result:** run it after the capture without chaining with `&&`, so a stale table is not mistaken for a missed night.
- Test a wrapper's exit paths against a stub before installing it. **gosom** on both Windows and the server hangs after finishing a tile ("scrapemate exited" in its log while idle): run each tile in its own process group, watch the log for that line, wait 20 seconds and kill the group.

## Finish means documented

A capture is done when someone else can rerun it, understand its limits and know what is missing. Keep failed approaches beside the working one: each parser here carries a comment naming what was tried and why it failed, which is the highest-value documentation because working code explains itself and traps do not.
Record what a source does not publish so nobody retries a dead end. Put cost in exactly one internal file that never travels with a deliverable. Ship the script and readme with the workbook: a task closed with its output still on one laptop looks identical, in every system we have, to a task closed with its output delivered.
