# Access: a conversation with a system that has its own purposes

A server decides, request by request, whether to answer you. Getting data is largely understanding what it looked at to decide, and giving it the least it needs to be satisfied. This file is about that reasoning.

## What can refuse you, and what each one sees

A refusal has an author, and the fix depends on which layer wrote it.

- **The address.** Reputation lists flag whole ranges, and datacentre addresses are flagged more often than home connections. It is not all-or-nothing: from 56 datacentre addresses, one request each, 31 got in and 24 did not, the same country
  and even the same network giving both.
- **The edge (CDN or WAF).** Cloudflare, CloudFront with AWS WAF, Vercel's checkpoint. It sees the address, the TLS handshake, the HTTP/2 settings and header order, sometimes runs a JavaScript check, and answers before the application is involved.
- **The handshake.** The way a client opens TLS and speaks HTTP/2 is a signature. Scripting libraries have a default posture that a browser does not share, so a server can tell them apart with no cookie and no header.
- **The application.** Its own logic can rate-limit by session, token or address, and can return errors that look like edge blocks. A 429 body carrying `gssp: true` meant the server-side function had run, so an edge firewall could not have written it,
  and hours of proxy work had been aimed at the wrong layer.
- **The request itself.** A missing `Referer`, `Accept-Language` or fetch-metadata header, a bad parameter, a placeholder path. A 403 that vanished once a referer and a few browser headers were added was never a block.
- **Behaviour over time.** Volume, regularity, the shape of what you ask for (a sequential walk looks like an enumeration attack).

## The ladder is a cost gradient, not a checklist

Each rung is heavier than the last. Stay on the lowest one that works, and move down only when a measurement, not a feeling, says the lighter one cannot.

| Rung | What it is | It works when | Its cost |
|---|---|---|---|
| 1 | The source's own API or embedded JSON | it exists (assess.md) | least fragile, cleanest |
| 2 | Plain HTTP with a full browser header set | the refusal was a missing header | cheap |
| 3 | HTTP with a browser's TLS handshake (`curl_cffi`, `scrapy-impersonate` inside Scrapy) | rung 2 is refused but a browser is not | still cheap |
| 4 | A real browser (Playwright, `scrapy-playwright`) | the data appears only after JavaScript runs | slow, heavy |
| 5 | A browser with automation artefacts patched (patchright) | rung 4 renders on a normal browser but the site treats automation differently | slowest, plus a patched third-party driver |

Before rung 3, do rung 2 properly: replay the request with everything a browser sends (`Referer`, `Accept`, `Accept-Language`, `Sec-Fetch-*`, a real `User-Agent`), copied from the browser's own request. The diagnostic is simple:
if a browser succeeds where your code fails, find what differs.

Rung 3 is worth understanding because it is a different kind of fix. The change is not to any header but to the handshake beneath them:

```python
from curl_cffi import requests as cffi
r = cffi.get(url, impersonate="chrome", proxies=proxies, timeout=30)   # curl_cffi 0.11.1 is installed
s = cffi.Session(impersonate="chrome")                                  # one session per thread
```

The worked example is a used-car listing site. Same proxy exit address, same listing ids, minutes apart:

| client | proxy | result |
|---|---|---|
| `requests`, Windows | 38 datacentre proxies | 12/12 = 200 |
| `requests`, Ubuntu | same proxies | 0/12 = 429 |
| `curl_cffi` chrome, Ubuntu | none | 0/8 = 429 |
| `curl_cffi` chrome, Ubuntu | same proxies | 8/8 = 200 |

Two independent things were wrong at once: the server's own address was refused at the edge, and even a clean address still refused the stock Ubuntu handshake. Only together did they work. What was measured is that swapping the TLS layer
flipped 0/8 to 8/8 with everything else held constant; the JA3 and JA4 hashes were never captured, so calling it a fingerprint is an inference. Three things follow from it. Address and client are separate axes, so a clean address with a flagged handshake looks
exactly like a dirty address. "It works on my machine" becomes a real diagnosis, so test from the host that will run the job. And a defence that a two-line change defeats is filtering the default posture of scripting libraries, not a determined scraper.

Inside Scrapy, `scrapy-impersonate` wraps the same thing (its README: replace the `http` and `https` download handlers with `scrapy_impersonate.ImpersonateDownloadHandler`, set `USER_AGENT = ""` so curl_cffi picks the matching UA, use the asyncio
reactor, and pass `meta={"impersonate": "chrome"}` per request). It needs Scrapy 2.14 or later and the installed one is 2.12, so test the upgrade in a throwaway venv before touching the global environment.
A plain script should use `curl_cffi` directly, which is the same thing without the framework.

Rung 5, `patchright`, is a drop-in for Playwright (change the import, then `patchright install chromium`; its README recommends real Chrome with `channel="chrome"` in a persistent context). It is Chromium only, disables the Console API altogether, and is a patched third-party
driver whose README is carried by proxy-vendor sponsors, so pin the version, use a throwaway profile, and never sign in to an account with it. Its purpose is to avoid being detected as automation, which is why the line below governs it.

## Diagnosing a refusal is an experiment, not a debate

Change one variable and watch which result moves. Same address, different client. Same client, different address. Your code against a real browser doing the same thing. The table above is that method.

A concrete plan for the commonest shape, "works on my laptop, refused on the server", whether the answer is a 403 or a 429 (the reasoning is the same): first save the body and headers of one refusal and ask who wrote it (a CDN or WAF page, or the
application). Then build the grid of client by address by host, holding two of the three fixed each time: the server with no proxy and a plain client with a full browser header set; the same with a browser-handshake client; then that client through the
proxies; then the laptop as the control. Each cell you fill removes a hypothesis. Then test each proxy alone with the client that works, plus one record you already hold as a canary, because an overall success rate is an average over parts that may not
all be alive (how to test a proxy is in `tools/fetch-and-frameworks.md`, section B). Only after the grid and the headcount do you tune workers and delays, and often you no longer need to. If a clean address with a matching handshake is still refused,
it is behaviour or an application limit, and the remaining options are slowing down, asking the publisher, or stopping.

Some further habits that came out of the same cases:

- **Read the body of every error you plan to act on, and save it.** It often names the layer, as the `gssp: true` case did. `scrapekit.guarded_get` saves them for you.
- **Do not trust one 404.** The same site emitted spurious 404s under load, and four "deleted" ids answered 200 minutes later. Confirm "gone" on a second attempt, by a different path, before recording it. The one verdict most pipelines treat as permanent
  is the one that silently discards a real record.
- **Verify each channel before tuning the strategy.** A scraper sat at 40% for a day and ten hours went into theories about workers, pacing, TLS and back-off. Then the 100 proxies were each tried once: 57 were dead and 43 worked, so the "40%" was
  43/100. A stable, oddly round plateau is a headcount question first, before any model of the system.
- **Show that a remedy helps before you build it in.** The hit rate was 27% at 5.8 workers and 22% at 2, statistically flat: cutting the pool bought no better acceptance and cost four times the throughput. And any downward move needs an independent
  way back up (driven by elapsed quiet time, not by progress the recovery itself must create), or the first bad hour becomes the permanent operating point.
- **Ask for something you know exists.** A dry streak and a broken request look identical from the outside. One request for a record you already hold separates them (durability.md builds this as a canary).
- **Test the fix against the case that motivated it**, and ask what changes when the input mix changes: a `continue` that skipped the pacing sleep was harmless until that branch became the common path.

## Pace is part of the conversation

Match it to the server's age and the operator's patience, not to your own. Official portals often run old single-instance software: seven seconds between requests turned 150 requests into twenty minutes, nothing, and never once faltered.
Concurrency is a property of the source, not a constant: one source degraded above two workers, another ran clean at sixteen, and a habit carried from the first to the second turned a parallel job serial for hours on a site with no limit at all.
Read `x-ratelimit-*` and `retry-after`; the server states the budget. Politeness is cheapest at the start: the block you avoid costs nothing, and the block you trigger costs the source.

## The line, and the reasoning under it

Our rule is not squeamishness. It comes from what each choice costs. Being a well-formed visitor (public pages, real headers and handshake, a bearable pace) is cheap, keeps you welcome and is in production.
A challenge page or CAPTCHA is the site saying no, and getting past it is an arms race you lose over time and a relationship you spend. Rotating tokens, identities or proxies to beat a limit is the same act at scale.
Anything behind a login, or with no public endpoint, was not offered to you: write "not available" instead. Scanning ids when a listing path exists risks the whole domain for a shortcut you did not need.

Practice is not always tidy, and it is better to say so. A rented proxy pool can be legitimate infrastructure (a fixed exit, a vantage point), and where one is already configured for a source, using it as configured is ordinary operation. The case for going further than that is the source's consent. An address-reputation block on a news publisher's site was diagnosed (not the country, not the fingerprint), the publisher was asked, and their publishing office replied in writing that if the operator could solve it from their side they had no objection. The scope was limited to that one domain, and the publisher's sister site, which runs a bot challenge, was left alone. Without that kind of consent an agent does not add proxies, rotate identities or route around a refusal on its own; extending a pool to a new source is a question to put to the person you work for.

When you meet a challenge or a block you cannot explain: stop, save the body, work out which layer refused, and offer the options (slower, another path, ask the publisher for an allowlist). Do not attempt the workaround.

## Understanding detection, for reading

`niespodd/browser-fingerprinting` explains how systems like Cloudflare and DataDome recognise bots. It has no licence file: read it, do not copy from it. In general, detection weighs the handshake, header order and set, the JavaScript environment, behaviour over time and
address reputation. Which is why "copy what a browser sends" is legitimate and cheap, and fighting a determined detector is a different activity from ordinary collection.
