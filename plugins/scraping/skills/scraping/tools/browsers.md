# Browsers, rendering and automation

Status data (stars, licence, last push, archived flag, latest release) comes from the GitHub metadata table read on 21 Sep 2026. Versions and Python requirements come from PyPI on the same day. Statements marked "the author reports" or "the README claims" are the project's own claims, not something checked here. A line ending `(unverified)` comes from general knowledge and was not checked. Nothing in this category is archived.

## 1. What "automation detection" looks at, and why each tool exists

A website (or the anti-bot vendor it pays) asks one question from several angles: is a person driving this browser, or a program? Each angle is a different layer, and each stealth tool exists to change one layer. Knowing the layer tells you what class of check a tool can and cannot affect.

| Layer | What is inspected | Which tools touch it, and how |
|---|---|---|
| Automation flag and driver artefacts | `navigator.webdriver`, variables a WebDriver injects into the page, objects Playwright injects for its own use, launch flags such as the automation infobar flag | undetected-chromedriver patches the chromedriver binary. nodriver, zendriver and DrissionPage drop chromedriver and speak CDP directly. Patchright edits Playwright's default launch flags and runs its own scripts in isolated contexts. Camoufox runs Playwright's page agent in a sandbox inside Firefox. playwright-stealth only overrides JavaScript properties. |
| CDP side effects | Chromium automation libraries switch on protocol domains (Runtime, Console). Page JavaScript can observe the side effects, for example in how console output and error objects are serialised, so a page can tell a debugger is attached | Only tools that change how they talk to the browser: patchright (its README says it avoids Runtime.enable and disables the Console API, so console features stop working), camoufox (uses Firefox's Juggler protocol, not CDP), nodriver and zendriver (the authors claim CDP-direct resists this; the mechanism was not checked). Stock Playwright, Puppeteer and Selenium-with-CDP all use these domains. |
| Headless differences | Headless builds and modes differ from a headed Chrome in features, window metrics, pointer type and sometimes the user-agent string | Running headed, or headed on a virtual display (nodriver's README recommends Xvfb on servers; Camoufox's Python library can start a virtual display), needs no special tool. Camoufox patches Firefox headless mode itself. |
| Navigator and WebGL surface | User agent, platform, languages, screen, fonts, GPU vendor and renderer, canvas and audio output, and whether these agree with each other | playwright-stealth overrides some properties. Camoufox generates a whole fingerprint and its own README warns that fingerprints must be internally consistent, because an impossible combination (a Windows user agent with an Apple GPU) is itself a flag. Botasaurus makes similar claims (README, not checked). |
| Network identity | TLS and HTTP/2 fingerprint, IP reputation and type (datacentre versus home), cookies earned earlier | No browser tool changes your IP. undetected-chromedriver's README says plainly that a datacentre IP will likely fail whatever the driver does, and Byparr's README says the same about needing a legitimate public IP. A real browser already presents a browser TLS fingerprint, which is why curl_cffi with browser impersonation (measured here on a used-car listing site, 0/12 became 8/8) is the cheap fix for the TLS layer without launching a browser. |
| Behaviour | Mouse paths, keystroke timing, scroll, request rate, time on page | Botasaurus advertises human-like mouse movement (README claim). For everyone else the honest lever is rate: slow, jittered, low concurrency. |
| Challenge pages and captchas | An interstitial or widget that must be passed before content appears | This is not detection avoidance, it is a challenge being solved. FlareSolverr, Byparr, SeleniumBase `solve_captcha()`, nodriver `cf_verify()`, Botasaurus `bypass_cloudflare`, playwright-captcha and the paid "unblocker" browsers all live here. |

### Where this skill's line sits

Rendering a JavaScript page in a real browser is normal, and so is copying what a real browser sends (headers, TLS, a headed Chrome with a persistent profile, sensible pacing). Using a tool to get through a challenge page, rotating identities or proxies to get past a block, or anything behind a login is not something this skill does. So the engineering ladder in this category ends at "ask a person", not at a stealthier tool. The stealth tools are described below so the reader understands what they are and what they cost, not so they can be reached for when a request returns 403.

### The risk profile of the stealth tools

- Patched third-party binaries. undetected-chromedriver rewrites a chromedriver binary it downloads. Patchright ships a modified Playwright driver. Camoufox is a rebuilt Firefox you download as a binary (the repository builds it, but you run the release artefact). Byparr depends on `invisible-playwright`, a patched Firefox wrapper from a different author, and on `playwright-captcha`. FlareSolverr bundles its own copy of the undetected-chromedriver code and, in its Docker image and Windows executable, a whole browser. You are running code and binaries from a handful of individuals, on a laptop that also holds firm data. Treat them like any unvetted download: a throwaway VM or container, no firm credentials on the machine, no shared profile.
- Sponsor-driven READMEs. The Patchright READMEs open with proxy-vendor banners and discount codes (NodeMaven, Swiftproxy, RapidProxy) and a scraping-API sponsor (Scrappey). Camoufox's README has a long sponsor list of proxy sellers and scraping APIs. DrissionPage's README leads with residential-proxy vendors. Byparr's README carries an affiliate proxy recommendation. These are not evidence of quality, they are evidence of who pays for the project and which product the reader is being steered toward: rotating residential proxies to defeat blocks, which is on the wrong side of this skill's line.
- Maintenance state, from the metadata: undetected-chromedriver last push 2025-07-05 (over fourteen months before the metadata date; PyPI 3.5.5 dated 2024-02-17), effectively dormant. nodriver last push 2026-05-13 with no GitHub releases, and zendriver's README says contributions to nodriver are heavily restricted and fixes sat unmerged (the zendriver author's account). Camoufox's README says there was a year gap in maintenance and that it may not be suitable for stable production use, and its current release tag is a beta. playwright_stealth last push 2026-04-04. Botasaurus last PyPI release 2026-01-06. Botasaurus's last push was 2026-07-26; everything else in this file was pushed in August or September 2026.
- Licences. undetected-chromedriver is GPL-3.0. nodriver and zendriver are AGPL-3.0. Lightpanda is AGPL-3.0. Byparr is GPL-3.0. Browserless is SSPL-1.0 or a commercial licence. DrissionPage carries a custom licence that permits only personal, study and lawful non-profit use and forbids commercial use without the author's authorisation (read from its LICENSE file, which is written in Chinese). Using a GPL or AGPL tool internally is generally low risk, but you should not embed one in a product or client-facing service without checking (unverified, not legal advice). DrissionPage and Browserless should be treated as unusable for firm work until the licence question is answered.
- A README claim that a tool "passes Cloudflare, Kasada, Datadome" is a snapshot of the author's own test on one day. Vendors change their checks continuously, so the same tool can fail next month. None of these claims were tested here and none should be quoted to a client.

## 2. Protocols: CDP, WebDriver classic, WebDriver BiDi

- **CDP (Chrome DevTools Protocol).** A JSON-over-WebSocket protocol built into Chromium for its own DevTools. Rich and low level: network events with response bodies, console, DOM, tracing, input, emulation. Chrome-only in practice (Puppeteer's README also lists Firefox via BiDi, not CDP). Playwright uses it for Chromium. It is the most powerful option and the one automation detection focuses on, because it needs domains switched on that ordinary browsing does not.
- **WebDriver classic (the W3C standard).** Command and response over HTTP through a per-browser driver executable (chromedriver, geckodriver). Deliberately narrow: navigate, find, click, execute script, cookies, screenshots. One HTTP round trip per command. It has no first-class way to read the network traffic, and the driver adds well-known artefacts, which is the reason undetected-chromedriver exists. Selenium is built on it.
- **WebDriver BiDi.** The newer W3C standard, a WebSocket protocol that adds what classic lacked: events, network interception, console and script realms, across browsers. Puppeteer's README says it drives Chrome or Firefox over CDP or BiDi, and Lightpanda's README says it serves CDP and BiDi. Selenium 4 supports BiDi (unverified). It is the standardised route to the CDP-like capabilities on Firefox.
- **Firefox specifics.** Playwright drives Firefox and WebKit through its own patched builds and protocols (Camoufox's README names Firefox's Juggler, a custom protocol, as what Playwright uses there). That is why Camoufox is a Playwright-compatible Firefox rather than a Chromium.
- **Why it matters for choosing.** If you need to read what the page's own API returned, you need events and response bodies: CDP or BiDi, not classic WebDriver. If you need to attach to a browser that is already open, that browser must expose a debugging endpoint. Chrome 136 and newer ignore remote-debugging flags on the default profile (dev-browser's README), so an attachable Chrome needs a dedicated profile directory; chrome-devtools-mcp's `--autoConnect` route needs Chrome 144 or newer with remote debugging switched on at `chrome://inspect/#remote-debugging` (its docs).

## 3. The mainstream frameworks

### Playwright, Node (TypeScript, Apache-2.0, 96k stars, pushed 2026-09-21, not archived, latest release v1.63.0 2026-09-04)
- **What it is:** a browser automation library with its own driver process that drives Chromium over CDP and patched Firefox and WebKit builds over Playwright's own protocols, with auto-waiting locators and a test runner (`@playwright/test`).
- **Best at:** the most complete general tool: three engines, contexts (cheap isolated sessions in one browser), routing and response events (you can read the page's own JSON responses), HAR record and replay, persistent profiles, tracing.
- **Limits and traps:** stock Chromium in headless mode is a separate headless-shell build, which some sites treat differently from headed Chrome (unverified). The stock build carries the automation and CDP artefacts described in section 1, so it is a poor choice for a target that checks for them.
- **Cost or risk:** free, actively maintained, releases roughly monthly. Each browser is a few hundred MB on disk and the process tree is heavy (numbers in the Python entry).
- **Reach for it when / not when:** reach for it when a page must render and you want to read its own API calls. Not when the data is in the raw HTML or an open JSON endpoint, where a plain HTTP client is faster and cheaper by one to two orders of magnitude (unverified as a general ratio; measure on the target).
- **Versus:** Puppeteer is Chrome-first and Node-only with a smaller API. Selenium is the older, narrower WebDriver model. Patchright and Camoufox are Playwright-compatible forks.
- **Here:** the environment notes list the Python package, not a Node Playwright library; the Node tools installed are dev-browser, agent-browser, playwright-cli and the chrome-devtools MCP.

### Playwright, Python (Python, Apache-2.0, 15k stars, pushed 2026-09-15, not archived, latest release v1.63.0 2026-09-15; PyPI requires Python 3.10 or newer)
- **What it is:** the same driver as the Node library, wrapped in a sync and an async Python API. The Python package launches the Node driver as a child process (consistent with the 116 MB driver process measured here).
- **Best at:** our default browser tool, because it lives in the same language as Scrapy, pandas and the data pipeline. Supports `launch_persistent_context(user_data_dir=...)` for a profile that keeps cookies and storage, `page.route` for interception, `page.on("response")` and `response.json()` for reading the page's own API replies, and `connect_over_cdp` to attach to a Chrome you started with a debugging port and a non-default profile directory (attach detail unverified beyond the Chrome 136 note above).
- **Limits and traps:** Windows is fully supported (the README table lists Chromium, Firefox and WebKit on Windows). Playwright Test is a Node runner, so the Python side uses pytest-playwright (unverified). Version drift: the installed 1.60.0 is three minors behind 1.63.0. The `scrapy-playwright` plugin pins to Playwright versions it has tested, so upgrade the two together.
- **Cost or risk:** free. Measured here (Playwright 1.60.0, headless shell, Windows 11, a local 500-paragraph page loaded with `set_content`, no network): browser launch about 0.1 s, first page about 0.15 s, process-tree resident memory about 285 MB with one page and about 890 to 940 MB with ten pages in one context (two runs). Windows resident size counts shared pages, so treat these as upper bounds; a real site with images and scripts costs more. These are one machine and one synthetic page, not a benchmark.
- **Reach for it when / not when:** reach for it when the page builds its content in the browser, or when the site's own API needs a token the page computes. Not for bulk fetching of server-rendered pages.
- **Versus:** patchright is the same API with a patched driver. Node Playwright has the test runner and, sometimes, features a little earlier (unverified).
- **Here:** installed, Playwright 1.60.0 with playwright-stealth 2.0.3 and scrapy-playwright 0.0.46 (latest tag 0.0.48). Patchright is not installed on purpose.

### Puppeteer (TypeScript, Apache-2.0, 95k stars, pushed 2026-09-21, not archived, latest release puppeteer-core-v25.11.0 2026-09-14)
- **What it is:** Google's Node library that controls Chrome or Firefox over CDP or WebDriver BiDi (its README), headless by default, downloading Chrome for Testing on install.
- **Best at:** direct, thin control of Chrome and the largest set of CDP-level examples. It is what chrome-devtools-mcp, dev-browser and browserless build on or accept.
- **Limits and traps:** Node only, so nothing in our Python pipeline calls it directly. Modern package managers block install scripts, so the browser download may silently not happen and you must run `npx puppeteer browsers install` (its README). Firefox support goes through BiDi and is less complete than Chrome's (unverified).
- **Cost or risk:** free and very actively maintained. Same automation artefacts as any stock CDP tool. The `puppeteer-extra-plugin-stealth` package that Python's playwright-stealth descends from has been reported discontinued (unverified).
- **Reach for it when / not when:** reach for it when a Node tool already exists for the job, or you are connecting to Lightpanda, browserless or a remote CDP endpoint. Not when Playwright Python does the same thing in your own language.
- **Versus:** Playwright has a richer API, three engines and contexts. Puppeteer is smaller and Chrome-centred.

### Selenium (Java with bindings for Python, Node and others, Apache-2.0, 34k stars, pushed 2026-09-21, not archived, latest release selenium-4.49.0 2026-09-09; PyPI requires Python 3.10 or newer)
- **What it is:** the reference implementation of the W3C WebDriver standard, talking to browsers through a driver executable, with Selenium Manager fetching the right driver automatically and a Grid for running many browsers.
- **Best at:** cross-browser test suites and organisations that already run a Grid. The standardised model works with every browser vendor and is what most Python tutorials use.
- **Limits and traps:** classic WebDriver has no built-in way to read the page's own network responses, so the scraping technique of capturing an XHR body needs BiDi, CDP access or a proxy (unverified in detail). It is the slowest of the three because each command is an HTTP round trip through a driver process. The driver is a detection surface, which is the origin of the entire undetected-chromedriver family.
- **Cost or risk:** free, actively maintained. Windows fine.
- **Reach for it when / not when:** when a legacy script or test harness already uses it, or SeleniumBase is wanted for its runner. Not as a first choice for a new scraper.
- **Versus:** Playwright is faster and has network access; Selenium is the standard-conformant one. FlareSolverr and undetected-chromedriver are built on Selenium.

## 4. Chromium automation without the WebDriver artefacts

### undetected-chromedriver (Python, GPL-3.0, 12k stars, last push 2025-07-05, not archived, no GitHub releases; PyPI 3.5.5 dated 2024-02-17)
- **What it is:** a Selenium-compatible wrapper that downloads chromedriver and patches the binary, then launches Chrome with adjusted flags, to remove the artefacts a stock chromedriver leaves.
- **Best at:** historically, making an existing Selenium script look less like Selenium with a one-line import change.
- **Limits and traps:** the README's own advice: it does not hide your IP, and a datacentre IP will likely fail anyway. Headless is described as officially unsupported. The author himself names nodriver as its successor. Dormant for over fourteen months, so a current Chrome release can break it, and pins around Selenium 4.9 in its notes.
- **Cost or risk:** GPL-3.0, an unmaintained patch of a binary from an unrelated project, and no security fixes. FlareSolverr bundles a copy of its code.
- **Reach for it when / not when:** not for new work. Only to understand what FlareSolverr does inside.
- **Versus:** nodriver and zendriver replace it by removing chromedriver entirely; SeleniumBase UC mode is the maintained heir to the same idea.

### nodriver (Python, AGPL-3.0, 4k stars, last push 2026-05-13, not archived, no GitHub releases; PyPI 0.50.3 requires Python 3.9 or newer)
- **What it is:** an asyncio Python library that drives an installed Chrome, Chromium, Edge or Brave directly over CDP, with no chromedriver and no Selenium.
- **Best at:** simple, fast scripting against a real Chrome with a fresh throwaway profile each run, cookie save and load to a file, text-based element finding that also searches iframes, and attaching to a Chrome debug session that is already running (README).
- **Limits and traps:** it needs a real browser on the machine; headless servers need Xvfb or headless mode (README). It has a Cloudflare-checkbox helper (`cf_verify`) that needs opencv, which is challenge solving and outside this skill's line. Contributions to the repository are described by the zendriver authors as heavily restricted. Its "expert mode" disables web security and, per its README, makes it more detectable. The README claims resistance to anti-bot systems; that is not tested here.
- **Cost or risk:** AGPL-3.0 (do not embed in a service you offer to others without review). Single-maintainer, slower update cadence than zendriver.
- **Reach for it when / not when:** when you want a CDP-direct Python driver and accept a small ecosystem, and only for rendering. Not for passing challenge pages.
- **Versus:** zendriver is the community fork with a more open issue tracker; Playwright has far more features and a large maintained team.

### zendriver (Python, AGPL-3.0, 1k stars, pushed 2026-08-16, not archived, latest release v0.16.0 2026-08-16; PyPI requires Python 3.10 or newer)
- **What it is:** a fork of nodriver that merges its unmerged pull requests and adds static analysis, an open issue tracker and a documented Docker template (Linux-only, GPU-accelerated non-headless).
- **Best at:** the same CDP-direct approach as nodriver with more active maintenance and typing.
- **Limits and traps:** version 0.x with a small user base, so API changes are likely. Its "undetectable" wording is a README claim ("almost impossible to detect"), not something measured here. Still needs a real Chrome.
- **Cost or risk:** AGPL-3.0, small maintainer team.
- **Reach for it when / not when:** only when you have decided a CDP-direct Python driver is right and nodriver's maintenance bothers you. Otherwise Playwright.
- **Versus:** nodriver (parent, less responsive), patchright (keeps the Playwright API, not CDP-direct scripting).

### Patchright, driver, Python and Node packages (driver repo: TypeScript, Apache-2.0, 4k stars, pushed 2026-09-13, latest release v1.63.0 2026-09-08. patchright-python: Python, Apache-2.0, 1k stars, pushed 2026-09-20, latest release v1.62.0 2026-08-17, PyPI patchright 1.63.0 dated 2026-09-20. patchright-nodejs: TypeScript, Apache-2.0, 787 stars, pushed 2026-09-13, latest release tag v1.59.1 dated 2026-04-01; none archived)
- **What it is:** Playwright with a patched driver. Per its README it avoids the Runtime.enable call by running scripts in isolated execution contexts, disables the Console API entirely (so console reading stops working), changes the launch flags Playwright passes, and can reach into closed shadow roots.
- **Best at:** keeping your existing Playwright code (a one-line import change) while changing the driver-level artefacts. It is the tool whose mechanism most directly maps onto the "CDP side effects" layer in section 1.
- **Limits and traps:** the README says it passes most but not all Playwright's own tests and lists known bugs. It works only with Chromium-based browsers. Its init scripts are injected through routing and the README concedes they can be found by timing attacks. The README advises real Chrome with a persistent profile, headed, no custom headers, which is also simply the behaviour of an ordinary user. A fix after a Playwright release can take "a few days" (README). The Node package's release tag lags Playwright by several minor versions, so check npm before relying on it.
- **Cost or risk:** patched third-party driver binary, sponsor-heavy README (section 1), maintenance keeps pace with Playwright for now. Free.
- **Reach for it when / not when:** not needed for ordinary rendering. Reach for it only for the harmless use, a headless-versus-headed rendering difference on a site that has no challenge, and only after a plain headed Playwright with a real Chrome channel failed. Not to pass challenges.
- **Versus:** playwright-stealth patches JavaScript properties only and leaves the driver alone; camoufox changes the browser engine; nodriver and zendriver drop the Playwright API.
- **Here:** deliberately not installed.

### Camoufox (C++ build repository with a Python wrapper, MPL-2.0, 12k stars, pushed 2026-09-14, not archived, latest release v152.0.4-beta.30 2026-09-01; PyPI camoufox 0.5.6 dated 2026-09-06, MIT, requires Python 3.10 or newer)
- **What it is:** a rebuilt Firefox with a patched Juggler protocol layer, so Playwright's page agent runs isolated from page JavaScript, plus generated fingerprints and a Playwright-compatible Python interface.
- **Best at:** the only tool here that does not use Chromium and CDP at all, which sidesteps the CDP side-effect layer by construction (README: Playwright's internals are sandboxed, headless mode is patched to look like a normal window, inputs go through the real input handlers). The README claims a small memory footprint (about 200 MB) and stripped Mozilla services; not measured here.
- **Limits and traps:** the README's own warnings: "under development, may not be suitable for stable production use", a year gap in maintenance, performance degraded by an old base Firefox, and newly found fingerprint inconsistencies. The fingerprint must stay internally consistent or it becomes the flag. Firefox is a different engine, so sites tuned to Chrome can render differently.
- **Cost or risk:** you run a large binary from one individual, downloaded at first use (unverified detail). Sponsor list is proxies and scraping APIs. It is a beta.
- **Reach for it when / not when:** to understand what a non-CDP browser is, or for a firm-approved rendering job where Chromium is provably the problem. Not for anything that needs stability, and not to pass challenges.
- **Versus:** patchright keeps Chromium and patches the driver; Camoufox changes the whole engine. Byparr (below) also fronts a patched Firefox, from a different author.

### playwright-stealth, the Python package (Python, MIT, 267 stars, pushed 2026-04-04, not archived, no GitHub releases; PyPI playwright-stealth 2.0.3 dated 2026-04-04, requires Python 3.9 or newer; repository Mattwmaster58/playwright_stealth)
- **What it is:** a fork of a port of the `puppeteer-extra-plugin-stealth` evasions: init scripts that override navigator properties and similar JavaScript-visible values on every page, applied through a wrapper such as `Stealth().use_async(async_playwright())`.
- **Best at:** cheap, dependency-light tidying of the most obvious JavaScript-surface tells (`navigator.webdriver`, languages, plugins) inside stock Playwright.
- **Limits and traps:** the README says not to expect it to bypass anything but the simplest bot detection and calls itself a proof of concept. It does nothing about CDP side effects, headless build differences or the network layer. Its own TODO says it does not yet work with `launch_persistent_context`, which is the mode for keeping a login state. Overriding properties inconsistently can create a new tell.
- **Cost or risk:** MIT, small, low risk. The risk is false confidence, not security.
- **Reach for it when / not when:** when a harmless page checks only `navigator.webdriver` and a headed Chrome is not available. Not as a general anti-detection answer.
- **Versus:** patchright changes the driver; camoufox changes the engine; this changes only scripts.
- **Here:** installed, version 2.0.3, the latest on PyPI.

## 5. Challenge solvers and all-in-one stealth frameworks

These are on this skill's line. They are described so that their existence, mechanism and risk are understood. None is recommended.

### FlareSolverr (Python, MIT, 15k stars, pushed 2026-09-12, not archived, latest release v3.5.2 2026-09-12)
- **What it is:** an HTTP proxy service on port 8191. You post a URL; it launches a Selenium-driven Chrome using its own bundled copy of undetected-chromedriver, waits for a Cloudflare or DDoS-Guard challenge to clear or time out, and returns the HTML and cookies (README).
- **Best at:** returning clearance cookies so another HTTP client can continue the session (the README notes you must reuse the same User-Agent). Runs as a Docker image, and for Windows as a release executable.
- **Limits and traps:** one new browser per request unless you use sessions, and the README warns of heavy memory use and that sessions must be closed. Do not expose it to the internet (README). Chromium does not work on Windows, so it needs real Chrome there (README). The Turnstile support relies on pressing Tab N times (`tabs_till_verify`). Cloudflare changes break it periodically (unverified).
- **Cost or risk:** its purpose is to defeat a protection the site owner chose, so it is outside this skill's line. It also runs a patched, bundled browser stack from the internet.
- **Reach for it when / not when:** not for firm work. If a source is behind such a challenge, the answer is to ask whether the data is offered another way.
- **Versus:** Byparr has the same purpose and default port with a different browser core; SeleniumBase's UC and CDP modes do it in code.

### Byparr (Python, GPL-3.0, 1k stars, pushed 2026-09-18, not archived, latest release v3.0.4 2026-08-18)
- **What it is:** a FastAPI service on port 8191, described as a way to "get valid antibot cookies". Its `pyproject.toml` requires Python 3.14 exactly, Playwright 1.63, `invisible-playwright` (a patched-Firefox wrapper from another author) and `playwright-captcha` (whose PyPI summary lists click-based and API-based, 2captcha, solving of Cloudflare Turnstile and reCAPTCHA).
- **Best at:** a container that fronts the challenge solving with an API and an Open WebUI loader endpoint.
- **Limits and traps:** its README says it does not guarantee a pass and that a legitimate public IP matters. Support for NAS and ARM devices is minimal (README). Python 3.14 exactly does not match the laptop's 3.12.4.
- **Cost or risk:** dependence on a patched Firefox and a captcha-solving package; sponsor/affiliate proxy recommendation in the README.
- **Reach for it when / not when:** not for firm work.
- **Versus:** FlareSolverr (Chrome and undetected-chromedriver) has the older, larger user base; Byparr moved to a Playwright plus Firefox core.

### SeleniumBase, UC mode and CDP mode (Python, MIT, 13k stars, pushed 2026-09-18, not archived, latest release v4.54.10 2026-09-18; PyPI requires Python 3.10 or newer)
- **What it is:** a large Selenium-based test framework (pytest, behave, reports, a GUI runner) that also offers a UC mode (an undetected-chromedriver derivative), a "CDP mode" that drops to CDP after page load, and a `sb_cdp` pure-CDP API, plus a `solve_captcha()` helper (README).
- **Best at:** the most actively maintained single package in this family, and a legitimate, good Selenium framework for testing (Windows, macOS, Linux per the README).
- **Limits and traps:** it is a large framework with its own conventions and CLI, and some modes only run under pytest. The stealth modes' claims ("bypasses bot-detection") are the author's. The captcha and Cloudflare examples in the README are exactly what this skill does not do.
- **Cost or risk:** MIT, single main maintainer, fast release cadence, heavy API surface.
- **Reach for it when / not when:** for a test suite or for plain automation with good tooling. Not for UC mode, CDP mode or `solve_captcha` against a protected site.
- **Versus:** Playwright is the cleaner API for a scraper; SeleniumBase is the choice if Selenium is a fixed requirement.

### DrissionPage (Python, licence marked NOASSERTION in the metadata (custom, non-commercial), 12k stars, pushed 2026-09-14, not archived, latest GitHub release v4.1.0.17 2025-03-21; PyPI 4.1.1.4)
- **What it is:** a Chinese-origin Python library with its own CDP-based browser controller (no WebDriver) that can also switch to an `requests`-like packet mode on the same session, with cross-iframe element lookup and access to closed shadow roots (README).
- **Best at:** fast scripting with combined browser and HTTP modes, popular in the Chinese scraping community. Documentation is mainly Chinese.
- **Limits and traps:** the licence text (Chinese) allows personal, study and lawful non-profit use only and forbids commercial use without written authorisation; it also forbids collecting data that robots.txt disallows. A commercial firm cannot use it as is. Its README is led by residential-proxy sponsors.
- **Cost or risk:** licence risk above all; documentation language; sponsor-driven README.
- **Reach for it when / not when:** not for firm work, on licence grounds alone.
- **Versus:** nodriver and zendriver are the closer CDP-direct Python peers, with AGPL rather than a non-commercial licence.

### Botasaurus (Python, MIT, 5k stars, pushed 2026-07-26, not archived, no GitHub releases; PyPI 4.0.97 dated 2026-01-06, requires Python 3.7 or newer)
- **What it is:** an all-in-one scraping framework: `@browser` and `@request` decorators around its own driver, caching, parallelism, proxy and profile handling, and a generator that turns a scraper into a desktop app or web UI (README).
- **Best at:** batteries-included convenience for one-person scraping tools, such as caching results and running parallel workers.
- **Limits and traps:** the README's tone is promotional ("passes every bot test") and shows `bypass_cloudflare=True`, a Cloudflare challenge helper. It is the author's snapshot, not verified here. The README links the author's other products (for example a Google Maps scraper demo) and does not describe how its driver is maintained.
- **Cost or risk:** MIT, but a single individual's framework and a large opinionated surface. GitHub push in July, last PyPI release in January.
- **Reach for it when / not when:** not needed; Scrapy plus Playwright covers the same ground with more mainstream support, and the challenge helpers are off the table.
- **Versus:** Scrapy with scrapy-playwright is our stack for crawling.

## 6. Infrastructure and lightweight engines

### Browserless (TypeScript, licence marked NOASSERTION in the metadata (actually SSPL-1.0 or a commercial licence), 13k stars, pushed 2026-09-21, not archived, latest release v2.56.7 2026-09-10)
- **What it is:** a Docker image that runs headless Chromium, Firefox and WebKit behind a WebSocket and REST server, so Puppeteer or Playwright scripts connect to it with `connect` instead of launching a local browser. It queues sessions and caps concurrency.
- **Best at:** running many browsers on a server without each script managing a browser lifecycle, with a debug viewer and standard, unforked Puppeteer and Playwright clients (README).
- **Limits and traps:** the licence: the README says commercial, closed-source or CI use needs a purchased commercial licence, and the alternative is SSPL. A market research firm running it internally for its own commercial work is probably in the "needs a licence" case (unverified; ask). Its stealth, captcha solving (BrowserQL) and residential-proxy features are in the paid cloud or enterprise product, and are unblocking features.
- **Cost or risk:** free for non-commercial use, otherwise paid (check current pricing). Memory equals however many Chromium instances you allow.
- **Reach for it when / not when:** when a server runs dozens of parallel browser jobs and the licence is settled. Not for one job on a laptop.
- **Versus:** running Playwright directly is simpler for a handful of jobs; managed browsers (Browserbase, Bright Data) do the same as a service.

### Lightpanda (Zig, AGPL-3.0, 35k stars, pushed 2026-09-21, not archived, releases are a rolling "nightly" tag only)
- **What it is:** a headless browser written from scratch, not a Chromium fork: an HTTP loader (libcurl), an HTML parser, a DOM and the V8 JavaScript engine, with no layout or paint. It serves CDP and WebDriver BiDi, so Puppeteer or Playwright can `connect` to it. It has a `fetch` command that dumps HTML, Markdown or text, an MCP server and an experimental agent mode.
- **Best at:** cheap JavaScript execution for pages that only need scripts to run and XHR or fetch to fire. The author reports 123 MB versus 2 GB peak memory and 5 s versus 46 s per 100 pages against headless Chrome on an EC2 m5.large; those are the author's numbers on their own crawl, not measured here.
- **Limits and traps:** no native Windows binary (use WSL2; the README says so). Linux and macOS nightlies only, glibc only on Linux. Its own status list is a subset of the web platform, so pages that depend on layout, canvas or newer APIs may behave differently and fail silently (the difference is checked by comparing its output with a real browser's, unverified as a general rule). `--dump png` gives a text-only rendering, not a real screenshot. Telemetry is on by default (`LIGHTPANDA_DISABLE_TELEMETRY=true` turns it off). Beta-stage stability (unverified).
- **Cost or risk:** AGPL-3.0, a rolling nightly means no pinned release, and it is a younger project. It respects robots.txt with `--obey-robots`.
- **Reach for it when / not when:** for volume rendering on the Ubuntu server where a page is mostly scripts and JSON, after checking output parity with Playwright on a sample. Not on the Windows laptop, and not for pages that need real layout.
- **Versus:** headless Chromium is complete but 10x or more heavier (author's figures); a plain HTTP client is lighter still but does not run scripts.

## 7. Browsers made for AI agents (interactive, not batch)

These are for a person or a model exploring a site and reading a page interactively, not for a thousand-page crawl. Their value is that the page is returned as a compact accessibility tree with stable references rather than as raw HTML or a screenshot.

### Chrome DevTools MCP (TypeScript, Apache-2.0, 52k stars, pushed 2026-09-21, not archived, latest release chrome-devtools-mcp-v1.9.0 2026-09-08)
- **What it is:** Google's MCP server that controls a live Chrome through Puppeteer and exposes DevTools features to an agent: page actions, console messages with source-mapped stack traces, network request list and detail, performance traces, Lighthouse audit, heap snapshot, emulation.
- **Best at:** debugging and inspecting a page: reading the network panel the way a developer does is the fastest way to find the JSON endpoint behind a page, which is the route to skipping the browser afterwards.
- **Limits and traps:** each action is one model call, so it is slow and costs tokens for anything repeated. Officially supports Google Chrome and Chrome for Testing only. It exposes the browser's contents to the model, so use a clean profile for anything sensitive. Google collects usage statistics by default (opt out with `--no-usage-statistics`) and performance tools may call the CrUX API (opt out with `--no-performance-crux`).
- **Cost or risk:** free. It attaches to a running Chrome with `--autoConnect` (Chrome 144 or newer, switched on at `chrome://inspect/#remote-debugging`), `--browserUrl` or `--wsEndpoint`. By default it uses its own persistent profile under the user's cache directory, or `--isolated` for a temporary one.
- **Reach for it when / not when:** to explore a site, find the API a page calls, and debug. Not as the collection engine.
- **Versus:** Playwright MCP is more general and drives three engines; dev-browser and agent-browser are CLIs with lower token cost per step.
- **Here:** installed as an MCP server (skill `browser-use`).

### dev-browser (TypeScript with a bundled Bun and Puppeteer binary, MIT, 6k stars, pushed 2026-09-05, not archived, latest release v0.2.9 2026-07-15)
- **What it is:** a CLI where an agent runs short JavaScript scripts against a Chrome that stays open between calls; named pages persist, snapshots are accessibility trees with element refs, and the scripts get a real Puppeteer Page API.
- **Best at:** an efficient explore loop: navigate once, inspect, act, verify, without relaunching. It can launch its own isolated Chrome or attach with `--connect` to one started with `dev-browser chrome`. Profiles, cookies and login state stay on disk when a launched browser closes (README), and launched browsers close after 30 minutes idle by default.
- **Limits and traps:** the README says macOS and glibc Linux are supported and Windows is not yet, but the installed package here ships a `windows-x64` executable that runs (checked with `--help`), so the README is stale or Windows support is recent; verify before relying on a specific feature. The README also warns that its `node:vm` script isolation is not a security sandbox.
- **Cost or risk:** free, small and fast-moving.
- **Reach for it when / not when:** to explore a site interactively at low token cost, including with a persistent profile. Not as a batch collector.
- **Versus:** agent-browser is a separate Rust CLI with a fuller command set; chrome-devtools MCP has more debugging depth.
- **Here:** installed, 0.2.9 (skill `browser-use`).

### agent-browser (Rust, Apache-2.0, 42k stars, pushed 2026-09-21, not archived, latest release v0.38.1 2026-09-16)
- **What it is:** a native Rust CLI plus a daemon, from Vercel Labs, that drives Chrome (downloaded as Chrome for Testing, or an existing Chrome, Brave, Playwright or Puppeteer install) over CDP. The agent calls `open`, `snapshot`, `click @e2`, `fill` and similar, and the page comes back as an accessibility tree with refs.
- **Best at:** the widest command set at low token cost: network interception and request lists with `--type xhr,fetch` filters, HAR recording with response bodies, cookies and storage, tabs, sessions, an MCP mode and a `--engine lightpanda` option. It can attach with `connect <port>` or `--auto-connect`, and persists login state by profile path, Chrome profile name, or `--session ... --restore`.
- **Limits and traps:** state files hold session tokens in plaintext unless you set an encryption key (README). Exposing `--remote-debugging-port` lets any local process control the browser. Browser providers are pluggable (AgentCore, Browserbase, Browserless, Browser Use, Kernel), so a command can silently run in a paid cloud browser if configured.
- **Cost or risk:** free. Rapid version turnover (0.x).
- **Reach for it when / not when:** to explore a page, harvest the JSON a page loads (the HAR route), and run a supervised session with a persistent profile. Not for batch collection.
- **Versus:** dev-browser has a script model on Puppeteer; agent-browser has a command model with more built-in features.
- **Here:** installed, 0.38.1 (skill `browser-use`).

### Playwright MCP and playwright-cli (playwright-mcp: TypeScript, Apache-2.0, 37k stars, pushed 2026-09-18, not archived, latest release v0.0.82 2026-09-18; playwright-cli is not in the metadata table)
- **What it is:** Microsoft's MCP server that exposes Playwright to a model as accessibility-tree snapshots, needing Node 18 or newer. The README itself recommends the separate CLI-plus-skills route (playwright-cli) for coding agents, because CLI calls avoid loading large tool schemas and snapshots into the model's context.
- **Best at:** an agent that needs a persistent browser state and rich introspection over many steps. It supports a persistent profile by default (one browser per profile at a time), `--isolated` in-memory profiles, `--storage-state`, `--cdp-endpoint`, and a browser extension (`--extension`) that connects to a tab in your running Edge or Chrome and its logins.
- **Limits and traps:** headed by default (`--headless` to change). The verbose snapshot in every reply eats context. Its allowed and blocked origin flags are documented as not a security boundary. Reading the page's own API responses is not something its README highlights (unverified).
- **Cost or risk:** free; pre-1.0 version numbers (0.0.x).
- **Reach for it when / not when:** when an agent must act inside your real logged-in browser through the extension. Otherwise the CLIs above are cheaper per step.
- **Versus:** chrome-devtools MCP for debugging depth; agent-browser and dev-browser for token efficiency.
- **Here:** playwright-cli 0.1.21 is installed (skill `browser-use`); its `--version` printed the version and then a libuv assertion on Windows exit, which is harmless noise as far as tested.

## 8. LLM-driven browsers (they need a model, and it costs money)

These replace a selector with a model call at every step. That buys robustness to layout change and a natural-language interface, and it costs latency, tokens and non-determinism.

### browser-use (Python, MIT, 115k stars, pushed 2026-09-18, not archived, latest release 0.13.10 2026-09-04; PyPI requires Python 3.11 or newer)
- **What it is:** an agent loop: it takes the page state (DOM and, optionally, a screenshot), asks an LLM what to do next, executes the click or type through a browser, and repeats until a task is done, returning a final result.
- **Best at:** open-ended tasks on pages whose structure you cannot predict, low volume and high value, where writing a selector script is not worth it. Supports many model providers through wrappers (OpenAI, Anthropic, Google, Ollama, Groq, Mistral, OpenRouter and more in its `llm` folder).
- **Limits and traps:** it needs a model, and the model is a paid API key. The README's quickstart asks for an OpenAI key, or a Browser Use key for their own hosted "BU2" model, and offers a hosted cloud with a browser-hour price, a stealth browser and captcha solving (the README states a price of $0.02 per browser-hour and $15 credit for new sign-ups; these are README claims, check current pricing). A local Ollama model avoids the fee, but small local models handle agent tool use poorly (unverified). Each step is a model call, so a 30-step task costs 30 calls; the output can vary between runs; a hostile page can attempt prompt injection against the agent. Its README advertises the agent handling a CAPTCHA, which this skill does not do. Telemetry is documented in the project docs.
- **Cost or risk:** software free, model and cloud paid. Roughly the same cost class as the model chosen, per step.
- **Reach for it when / not when:** when a task is a one-off exploration, or a form flow no script could follow, on a public page, with a budget. Not for bulk extraction, not where a stable script can be written, and not anywhere a login or captcha is involved.
- **Versus:** Stagehand mixes code and model calls; agent-browser or dev-browser under Claude Code do the exploring with your existing model access rather than a second one.

### Stagehand (TypeScript with Python and Go SDKs, MIT, 24k stars, pushed 2026-09-20, not archived, latest release tag @browserbasehq/stagehand@3.7.3 2026-08-28)
- **What it is:** a Browserbase library with three model-backed primitives on top of a Playwright-style page: `act("click the sign in button")`, `extract(...)` with a Zod or Pydantic schema, and `observe(...)`, which returns real selectors so credentials never have to reach the model (README).
- **Best at:** a hybrid: deterministic code for the parts you know, one model call for the fragile step, with schema-validated output, self-healing when a page changes, and caching so an identical call the second time spends no tokens (caching described for the Browserbase-hosted path).
- **Limits and traps:** it also needs a model key. The README example passes an OpenAI key; the alternative in the README is Browserbase's Model Gateway, which needs a Browserbase account. So yes, a paid model key or a paid Browserbase account is required. The README documents version 4 (with a Go SDK at 4.0.0) while the latest tag in the metadata is 3.7.3, so check which line is current before adopting. Local runs need Chrome installed.
- **Cost or risk:** software free (MIT), model calls and Browserbase paid (check current pricing). Tied to Browserbase's product direction.
- **Reach for it when / not when:** when a Node or Python job has a few unstable steps (a login-free multi-step form) and you want a repeatable script with a model repair layer. Not when the site is stable enough for selectors.
- **Versus:** browser-use is a free-running agent; Stagehand is a scripted flow with model steps.

## 9. Managed remote browsers (from knowledge, none checked, all pricing unverified)

- **Browserbase.** Hosted headless Chrome sessions that you connect to over CDP from Playwright or Puppeteer (or through Stagehand), with session recording and replay, persistent contexts, and, as optional features, proxies and stealth or captcha handling. Pricing is by plan and by browser time (check current pricing). It is the vendor behind Stagehand. (unverified)
- **Bright Data Scraping Browser.** A remote browser you drive with Puppeteer, Playwright or Selenium, with automatic proxy rotation, fingerprint handling and captcha solving handled by the service; billing is by traffic, with a per-GB rate (check current pricing). Its selling point is unblocking, which puts it on the wrong side of this skill's line. (unverified)
- **Trade-offs common to both.** Page content and any credentials you type pass through a third party, which matters for client-confidential targets and is impossible for anything behind a login. Latency is higher than local. Costs scale with usage in a way a laptop does not. IPs are outside Iraq unless the provider offers Iraqi exit points, and some Iraqi sites may treat foreign IPs differently (unverified). The genuine benefit is scale and not maintaining Chrome, not getting past blocks. Both pair well with an API-first approach: check the plain HTTP route and Apify actors before paying for browser time.

## 10. Practical facts side by side

Entries marked (u) are unverified. "Read page API" means reading the JSON the page itself fetched.

| Tool | Protocol | Windows | Headless or headed | Attach to running Chrome | Read page API responses | Persistent profile |
|---|---|---|---|---|---|---|
| Playwright | CDP for Chromium, own protocols for Firefox and WebKit | yes (README) | both, headless by default (u) | connect over CDP (needs a debugging port and non-default profile) | yes, route and response events, HAR | yes, persistent context |
| Puppeteer | CDP or BiDi (README) | yes (u) | headless by default (README), headed optional | yes, connect to a WebSocket endpoint (u) | yes (u) | yes (u) |
| Selenium | WebDriver classic, BiDi in 4.x (u) | yes | both | attach through a debugger address option (u) | not in classic; BiDi or CDP or proxy (u) | yes, profile argument (u) |
| nodriver, zendriver | CDP direct | needs installed Chrome; Windows not stated in README (u) | both, Xvfb suggested on servers (README) | yes, connect to a debug session (nodriver README) | via CDP event handlers (README) | fresh profile by default, cookie save and load (README) |
| patchright | patched Playwright, CDP | as Playwright (u) | headed real Chrome recommended (README) | as Playwright (u) | yes, but Console API is disabled | yes, persistent context recommended (README) |
| Camoufox | Juggler (Firefox) with Playwright API | yes, a Windows build target exists (README) | headless patched, virtual display fallback (README) | no, it is its own browser | via Playwright routing (u) | unverified |
| SeleniumBase | WebDriver, UC mode, CDP mode | yes (README) | both | unverified | limited in classic mode (u) | yes (u) |
| DrissionPage | own CDP core | yes (u) | both (u) | yes (u) | yes (u) | yes (u) |
| Lightpanda | serves CDP and BiDi | no native, WSL2 only (README) | headless only | not applicable | yes, network interception listed (README) | cookies listed; profile unverified |
| chrome-devtools MCP | Puppeteer over CDP | yes (running here) | headed default, `--headless` option (README) | `--autoConnect`, `--browserUrl`, `--wsEndpoint` (docs) | yes, network request tools | own persistent profile, or `--isolated` |
| agent-browser | CDP | yes (runs here) | headless or headed (u) | `connect <port>`, `--auto-connect` (README) | yes, network requests and HAR (README) | `--profile`, `--session --restore` (README) |
| dev-browser | Puppeteer over CDP | executable runs here; README says not supported | headless flag; launches Chrome otherwise (README) | `--connect` to one started with `dev-browser chrome` | via the Puppeteer page API | yes, profiles kept on disk (README) |
| Playwright MCP | Playwright | yes (Node 18 or newer) | headed by default (README) | `--extension`, `--cdp-endpoint` (README) | not highlighted in README (u) | persistent by default, `--isolated` option |

Speed and memory in one place: the only number measured here is Playwright Python on headless shell (about 285 MB for the process tree with one page, about 890 to 940 MB with ten pages, launch around 0.1 s, on a synthetic local page). Lightpanda's 123 MB versus 2 GB per 100 pages is the author's figure. Camoufox's roughly 200 MB is the README's claim. Selenium adds an HTTP round trip per command (mechanism). FlareSolverr starts a fresh browser for each request unless a session is used (README). A model-driven browser adds a model call per step, so it is the slowest and most expensive per page by a wide margin.

## How to choose

Start by asking whether a browser is needed at all, because every step up the ladder multiplies time, memory and fragility by an order of magnitude. Open the page's network panel (or use the chrome-devtools MCP, agent-browser or dev-browser to read it) and look for the request that carries the data. If the data is in the raw HTML, use an HTTP client and a parser. If it comes from a JSON endpoint the page calls, call that endpoint directly, with the headers a real browser sends; if the block is a TLS fingerprint, curl_cffi with browser impersonation is the cheap fix (measured here, 0/12 became 8/8 on a used-car listing site). Only when the content truly does not exist in any response you can reproduce, for example because a script computes a signed token or assembles the page client-side, do you need a browser. That is the evidence that justifies moving up.

The first browser rung is Playwright in Python, headless, with a response listener that captures the page's own JSON, so you render once and then, ideally, learn the API and drop back to HTTP. Use the agent CLIs (agent-browser, dev-browser) or the chrome-devtools MCP only for exploration, since their per-step cost makes them a poor collector. The next rung is not a stealth tool: it is a headed real Chrome (`channel="chrome"`), a persistent profile, sensible pacing and lower concurrency. The evidence that justifies stepping here is concrete: the same request works headed and fails headless, or the page depends on state a fresh profile lacks. On the Ubuntu server, if a job is many pages of mostly scripts and JSON and Chromium's weight is the bottleneck, try Lightpanda after comparing its output with Playwright's on a sample; drop it the moment pages need layout. For parallel volume on a server, Browserless or a managed browser solves scale (not blocking), subject to a licence or pricing check.

The stealth rung is where a good engineer stops and asks. If a plain headed Chrome with a real profile still meets a challenge page, the evidence you have collected is that the owner has decided automated access is not welcome, and this skill's rule is not to defeat that. The right move then is a different route: an official API or export, a partner or licensed data source, a manual or human-supervised session in your real browser, or dropping the source and saying so in the methodology. Patched drivers and challenge solvers (patchright, camoufox, nodriver, zendriver, FlareSolverr, Byparr, SeleniumBase UC and CDP modes, Botasaurus, DrissionPage) are catalogued here so you can recognise them, weigh their supply-chain and licence risks, and explain why they are not used; playwright-stealth is the one mild exception, and it is only a tidy-up of a couple of JavaScript properties. LLM-driven browsers come last and only for a narrow job: an exploratory or low-volume flow whose structure changes, with a budget, on a public page, using a paid model key that you have decided to spend. Once the model has worked out the path, capture it as a deterministic script (Stagehand's caching, Lightpanda's recorded scripts, or a Playwright script you write from what you saw) and stop paying per step.

What would make you change your mind at each rung is evidence, not a hunch: a request you can replay outside the browser (go down a rung), a difference between headed and headless (go to real Chrome), a memory or throughput ceiling you measured (go to a lighter engine or a farm), and a challenge page (stop, and ask).
