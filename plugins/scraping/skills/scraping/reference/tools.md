# Tools: choosing, what is installed, and where each one is documented

## Choosing by mechanism

A tool is an answer to a mechanism: something the target checks, or something the job needs. So choose by asking what the target actually looks at and what the lightest thing is that satisfies it, not by which repo is popular
(a Google Maps scraper with 3,465 stars and an MIT badge was a commercial desktop product). Every step up the ladder multiplies time, memory and fragility by roughly an order of magnitude, so the burden of proof rises with it.
The five files in `tools/` each end with a "How to choose" section that reasons through the trade-offs in their category; this map is only the front door.

| What you are facing | Start with | What should make you move on |
|---|---|---|
| Data in the raw HTML, or an open JSON endpoint | `requests` or `httpx`, `selectolax` or `parsel` | A refusal a browser does not get: replay with the full header set, then check the handshake |
| Still refused after copying the browser's full header set, while a real browser is not refused | `curl_cffi` with `impersonate="chrome"` | Still refused through clean addresses with a matching handshake: it is behaviour or an application limit. Slow down, or stop and ask |
| Content is built by JavaScript | The page's own API found in the network panel; failing that Playwright with a response listener | Works headed and fails headless: real Chrome, persistent profile, lower concurrency. A challenge page: stop |
| A large or recurring crawl across many pages | Scrapy (with `scrapy-playwright` only for the pages that need it) | The crawl is one API and a few hundred URLs: a script is enough |
| Main text of articles | trafilatura | A structured page (FAQ, tables) it drops: read the embedded JSON or parse the markup |
| Dates, prices, phone numbers, Arabic names | `dateparser`, `price-parser`, `phonenumbers`, normalisation then `rapidfuzz` | The join fails silently: enumerate the small closed set and assert coverage |
| Places from Google Maps | scraperlink on Apify for lookups; gosom on your own machine for sweeps | A low phone rate is the neighbourhood, not the tool |
| PDFs and scans | Extract text and count characters; `pdfplumber` for tables | Zero characters: OCR, and that is a different project |
| Something that must survive a kill | JSONL plus atomic state, `scrapekit`, a canary, a systemd timer on the server | It runs for minutes on a laptop: a plain script is fine |
| A paid service | A ten-cent sample and a hard spend ceiling first | The free layer already holds the field: do not pay to improve it |
| Finding where a page's data comes from | Network panel, sitemap, JS bundle grep, `mitmproxy` for an app | Nothing found: ask the publisher or find another source |

## The reference environment (checked 21 Sep 2026, one Windows laptop)

| Tool | Version | Note |
|---|---|---|
| Python | 3.12.4 (Anaconda) | |
| Scrapy | 2.12.0 | Current is 2.19.0; the reactorless, httpx and aiohttp download handlers and `scrapy-impersonate` need a newer one |
| scrapy-playwright | 0.0.46 | Latest tag 0.0.48 |
| Playwright | 1.60.0 | Current is 1.63.0; upgrade it together with scrapy-playwright |
| playwright-stealth | 2.0.3 | Only tidies a couple of JavaScript properties |
| curl_cffi | 0.11.1 | Current is 0.16.3; HTTP/3 needs 0.11.4 or later |
| requests / httpx | 2.34.2 / 0.28.1 | httpx is in a maintenance gap; Pydantic publishes `httpx2` as a continuation. Isolate it behind one function |
| parsel / lxml | 1.8.1 / 6.1.3 | lxml was raised from 5.2.1 on 21 Sep when selectolax, justext and trafilatura were installed; Scrapy and parsel still work |
| selectolax / trafilatura / justext | 0.4.12 / 2.2.0 / 3.0.2 | Installed 21 Sep to measure them (extraction.md) |
| beautifulsoup4 | 4.12.3 | Older code still uses it |

Not installed on purpose: `scrapy-impersonate`, `patchright`, `news-please`, `anansi`. Browser tools for interactive work (dev-browser 0.2.9, agent-browser 0.38.1, playwright-cli 0.1.21, the chrome-devtools MCP, the built-in pane)
belong to the `browser-use` skill. Apify is reached through its MCP tools. A pip install into the global environment can move other packages (it moved lxml),
so prefer a venv for anything new and run `pip check` afterwards.

## Seven repos that were recommended and then checked

All are in scope, gated by this skill's line (transport.md). Verdicts are from GitHub metadata read on 21 Sep 2026 and from running them where noted; the code was not security-audited.

| Repo | Verdict |
|---|---|
| `rushter/selectolax` | **Adopt.** v0.4.12 (18 Sep 2026), 26 contributors. About 10x faster than BeautifulSoup with lxml on 158 pages of a law-firm site, identical titles and link counts |
| `jxlil/scrapy-impersonate` | **Only inside a Scrapy spider.** v1.9.0 (27 Aug 2026), MIT, needs Scrapy 2.14 or later and the asyncio reactor. A thin wrapper over curl_cffi, which the nightly capture already uses directly. Test the upgrade in a venv |
| `Kaliiiiiiiiii-Vinyzu/patchright` | **Rendering only, gated.** Very active (v1.63.0, 8 Sep 2026), Apache-2.0, Chromium only, disables the Console API, README carried by proxy-vendor sponsors, a patched third-party driver. Not installed. Never to get through a challenge page |
| `miso-belica/jusText` | **Second opinion only.** v3.0.2 (Feb 2025), has an Arabic stoplist, but on defaults left 53 of 135 pages of a law-firm site nearly empty and recalled 0.17 of Arabic body text. trafilatura (recall 0.91) is the default instead |
| `fhamborg/news-please` | **Do not adopt.** No GitHub release, last code merged Sep 2025, issues open since 2020. We have our own collectors |
| `niespodd/browser-fingerprinting` | **Reading only.** No licence file, so do not copy from it |
| `mdowis/anansi` | **Do not run on client work.** Young, installs from GitHub, ships an MCP server that lets a crawled page steer the model. The idea worth taking is selector repair with confidence scores |

The "Here" lines in `tools/` describe this reference environment, one person's laptop and server; treat them as an example of how to record status, not as your setup.

## Sizing a claim about any repo

Stars and a licence badge are not evidence of what a repo is. Read the metadata (last release, contributors, licence file), install it in a venv, run it on one real task of yours, and compare it with what you already use.
Benchmarks in a README are the author's, on the author's task. Each entry in `tools/` says which of its statements were checked and which come from general knowledge and are marked `(unverified)`; the maintenance
data was read from GitHub on 21 Sep 2026 and will age, so re-read it before relying on it.

## The full index

`tools/index.md` lists all 170 tools in one line each, grouped by file. It is deliberately not loaded here: read it only when you are hunting for a tool by name, and use `Grep` inside `tools/` to jump to an entry.
