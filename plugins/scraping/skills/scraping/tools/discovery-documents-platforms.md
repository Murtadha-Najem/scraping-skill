# Category: Discovery and inspection, documents and OCR, platform-specific sources

Status data (stars, licence, last push, archived, release) is copied from `ghmeta.tsv`, read from GitHub on 21 Sep 2026. Lines marked `(unverified)` come from general knowledge that I did not check. Lines marked "tested" are experiments I ran on 21 Sep 2026 and are described so they can be repeated. Lines marked "the author reports" are README claims, not measurements.

A note on ordering: the four parts follow the order in which a source usually gets understood: A finds where the data really comes from, B does the same for apps, C turns files and recordings into text, D covers platforms that have their own rules.

---

# A. Finding where the data comes from

### Browser DevTools network panel and HAR export (built into Chrome and Firefox; not on GitHub)
- **What it is:** the browser records every request the page makes (URL, method, headers, timing, body). "Copy as cURL" gives one request as a runnable command, and "Save all as HAR" gives the whole session as a JSON file.
- **Best at:** showing the request the page itself uses to load its data, so you replay that one call instead of parsing the page. Filtering to Fetch/XHR usually leaves a handful of calls (unverified).
- **What a HAR contains (HAR 1.2, unverified):** a `log.entries` list; each entry has request (method, URL, headers, cookies, query string, post body), response (status, headers, `content` with size, MIME type and usually the text, base64 when binary) and timings, plus server IP and connection id.
- **What a HAR does not contain (unverified):** the TLS handshake or JA3 fingerprint, the raw bytes on the wire, JavaScript state or the rendered DOM, requests made before recording started or on a page you navigated away from without "Preserve log", and reliably the body of large or evicted responses. WebSocket frames are outside the HAR standard; Chrome adds a non-standard field for them (unverified).
- **Limits and traps:** a HAR holds live cookies, bearer tokens and CSRF values, so it is a credential file. Never paste one into a ticket, a repo or a chat. Chrome offers a "sanitized" export that strips sensitive headers (unverified, check the current option name). The request that works in the browser can still fail from Python because of the TLS fingerprint, not the headers.
- **Reach for it when / not when:** always first, before writing any parser. Not enough when the site checks something you cannot see in the panel (fingerprint, timing, a token minted by obfuscated JS).
- **Versus:** mitmproxy sees the same traffic from outside the browser and works for apps; DevTools cannot.
- **Here:** the chrome-devtools MCP is installed and exposes network listing and per-request body retrieval; the dev-browser, agent-browser and playwright-cli tools sit behind the `browser-use` skill.

### mitmproxy (Python, MIT, 45k stars, last push 2026-09-10, not archived, latest v12.2.3 2026-05-12)
- **What it is:** an intercepting proxy that terminates TLS with its own certificate authority, so a client that trusts that CA shows its decrypted HTTP/1, HTTP/2 and WebSocket traffic. Three front ends: `mitmproxy` (console), `mitmweb` (browser UI), `mitmdump` (command line, "tcpdump for HTTP").
- **Best at:** capturing traffic from things that are not browsers: a phone app, a desktop client, a script. Modes per the docs: regular proxy, local capture (Windows, Linux, macOS, per-process), WireGuard (external devices or individual Android apps), reverse, and others. Python add-ons can rewrite or record flows.
- **Limits and traps:** the client must trust the mitmproxy CA (the CA is generated uniquely on first start). A client with certificate pinning refuses it; the docs say such apps must be patched, and list tools for that. Capture proves what a request looks like, not that you may make it.
- **Cost or risk:** free, actively maintained, needs Python 3.12 or newer from PyPI (Windows installer available). The CA private key is on disk: protect it.
- **Reach for it when / not when:** when the source is an app or a desktop client, or when DevTools hides the call (service worker, another process). Not when a page is plainly a website; DevTools is cheaper.
- **Versus:** Charles, Fiddler, Burp, ZAP and Proxyman (next entry) do the same job with a GUI; mitmproxy's edge is that it is scriptable and free.

### Charles, Fiddler, Burp Suite, OWASP ZAP, Proxyman (desktop proxies; ZAP is Apache-2.0, 15.8k stars, last push 2026-09-18, not archived per GitHub; the rest are not on the metadata table)
- **What they are:** GUI intercepting proxies with the same TLS-terminating mechanism as mitmproxy. Charles and Proxyman are commercial (Proxyman is macOS-centred), Fiddler has a Windows client with a free tier, Burp has a free Community edition and a paid Professional one, ZAP is free and open source. (unverified, check current pricing and editions)
- **Best at:** point-and-click inspection, breakpoints and rewrite rules; Burp and ZAP add scanners and extensions (InQL runs inside Burp).
- **Limits and traps:** the scanners in Burp and ZAP send attack traffic; do not run active scans against a site you do not own. Same CA and pinning limits as mitmproxy.
- **Reach for it when / not when:** when someone on we prefers a GUI or already has a licence. Otherwise mitmproxy plus DevTools covers the need.
- **Here:** a Fiddler binary directory appeared on the laptop's PATH when I listed it; I did not check whether it is a working install.

### curlconverter (TypeScript, MIT, 8k stars, last push 2026-03-10, not archived, latest v4.12.0 2025-02-07)
- **What it is:** parses a curl command (with real Bash quoting, heredocs and environment variables) and emits equivalent code in Python (requests, the default), Node, Go, R, Rust, HTTPie and about 25 other targets, or a HAR.
- **Best at:** turning DevTools "Copy as cURL (bash)" into a first working script in seconds, with `--verbose` printing warnings when a curl flag has no equivalent.
- **Limits and traps:** install it with npm. The PyPI name `curlconverter` (1.0.1, 2023) is a different, older project. The generated Python uses `requests`, whose TLS fingerprint differs from a browser, so a request that works in curl may still be blocked in the generated script. Redirect and gzip defaults differ between curl and the target library, and the README says so. The pasted command carries your cookies and tokens: scrub before saving.
- **Reach for it when / not when:** to convert one discovered request into code. Not a discovery tool; it only translates what you already found.
- **Versus:** HAR-to-code converters do a whole session; curlconverter is per request and has better Bash parsing.

### hurl (Rust, Apache-2.0, 19k stars, last push 2026-09-21, not archived, latest 8.0.1 2026-04-29)
- **What it is:** a command-line runner for plain-text files that list HTTP requests, capture values from responses (XPath, JSONPath, regex) and assert on the results, so a login-then-fetch chain is a text file.
- **Best at:** repeatable request chains where a step needs a value from the previous step (a CSRF token from a form page). The README example captures a token by XPath and posts it.
- **Limits and traps:** no JavaScript, so it cannot reproduce a token minted by page script. A curl-based client presents curl's TLS fingerprint, not Chrome's (unverified). Chains that log in are outside this skill's line.
- **Reach for it when / not when:** to document and re-run a discovered API sequence, or to smoke-test an endpoint before writing the scraper. Not for bulk collection; there is no scheduler or retry policy.
- **Versus:** HTTPie is for one-off human-readable calls; hurl is for a stored, asserted sequence.

### HTTPie (Python, BSD-3-Clause, 38k stars, last push 2024-12-17, not archived, latest 3.2.4 2024-11-01)
- **What it is:** a command-line HTTP client (`http`, `https`) with short syntax for headers, JSON bodies and sessions, and coloured output.
- **Best at:** hand-probing an endpoint and reading the response comfortably; persistent sessions store cookies between calls.
- **Limits and traps:** it is built on Python `requests` (unverified), so it inherits requests' TLS fingerprint: a block that stops requests will stop HTTPie too. No release since November 2024, and the README notes the project lost its stars after a repository incident.
- **Reach for it when / not when:** for quick manual probes. Not for anything where TLS fingerprint matters.
- **Versus:** curl is the reference for what a server sees; `curl_cffi` is the tool when the fingerprint is the problem.

### Postman and Bruno (API clients; Bruno is on GitHub as usebruno/bruno, MIT, 47k stars, last push 2026-09-21, not archived; Postman is closed)
- **What they are:** GUI clients for building requests, storing them in collections, and importing OpenAPI files or curl commands. Bruno keeps collections as plain files on disk that can go in Git; Postman is centred on an account and cloud workspaces. (unverified beyond Bruno's metadata)
- **Best at:** exploring an API that already has a spec, and sharing a collection with a colleague.
- **Limits and traps:** they are clients, not discovery tools; they know only what you give them. Postman collections synced to a cloud workspace can carry tokens off the laptop (unverified, check settings).
- **Reach for it when / not when:** when a documented OpenAPI file exists. Not when you are still finding out what the site calls.

### gau (Go, MIT, 5k stars, last push 2026-03-20, not archived, latest v2.2.4 2024-10-28)
- **What it is:** fetches known URLs for a domain from four archives: Wayback Machine, Common Crawl, AlienVault OTX and URLScan (per README), in parallel, with filters for date range, status code and MIME type.
- **Best at:** a fast first list of every path ever recorded for a domain, in one command (`gau example.com --subs`).
- **Limits and traps:** it returns URLs only, not bodies. OTX and URLScan are security-community sources, so for a small commercial site they add little. Listed URLs include images, tracking parameters and dead paths; the status filters use the archived response, not today's. Default config at `%USERPROFILE%\.gau.toml`. In oh-my-zsh the name clashes with the git alias `gau` (README).
- **Reach for it when / not when:** to see the URL shapes of a site before crawling. Not when you need history with content; query the Wayback CDX API directly (below) so you control fields, collapsing and paging.
- **Versus:** waybackurls uses Wayback only; the raw CDX API gives more control; Katana crawls the live site instead.

### waybackurls (Go, no licence declared, 4k stars, last push 2024-05-01, not archived, latest v0.1.0 2022-04-05)
- **What it is:** reads domains on stdin and prints every URL the Wayback Machine knows for `*.domain`.
- **Best at:** being tiny. It is the original of the pattern that gau extends.
- **Limits and traps:** no licence file, so reuse rights are unclear; no release since 2022; Wayback only; no filters by status or date in the README.
- **Reach for it when / not when:** almost never; a ten-line CDX query in Python does the same with more control.
- **Versus:** gau (more sources and filters), the CDX API (full control).

### Wayback Machine CDX API (web service of the Internet Archive; not on GitHub, documented in internetarchive/wayback)
- **What it is:** a query interface to the archive's capture index. Each row is one capture: timestamp, original URL, status, MIME type, content digest, length. Endpoint `https://web.archive.org/cdx/search/cdx`.
- **How to query (checked against the README and tested):** `url=` with `matchType=exact|prefix|host|domain` (or a trailing `/*` or leading `*.`), `output=json`, `fl=` to choose fields, `from=`/`to=` for dates, `filter=statuscode:200` (regex filters, negatable), `collapse=urlkey` for one row per URL or `collapse=digest` for one per content change, `limit=` and `showResumeKey=true` with `resumeKey=` for paging, `showNumPages=true` to size a query first. A tested query for `example.com` with `matchType=prefix&collapse=urlkey` returned rows with status 200, 302 and 404 together.
- **What it holds:** what a crawler or a user caused the archive to save, at the moments it did so. Not everything on a site; listing pages are common, deep pages are patchy.
- **Gaps and traps:** rows include redirects and errors (tested: 302 and 404 rows appear), so filter by status. The same page appears under several URLs (http and https, `:80` in the URL, `www`, tracking parameters), so normalise before counting. A row proves a capture was attempted, not that the body is usable. Raw bytes are fetched from `web.archive.org/web/<timestamp>id_/<url>` (unverified). Rate limits exist and are not documented in the README; go slowly (unverified).
- **Here:** for the classifieds site we found 95,773 unique Iraq listing ids in Wayback (all categories, 2019 to 2026), the only source older than May 2026. Of these the Autos pass found about 4,300 usable car listings, 1,550 of them from 2019 to 2024. An id list is not a content list: expect the usable share to be small.
- **Versus:** Common Crawl (next) is a sample of the whole web by month; Wayback is deeper for one site's history.

### Common Crawl index (web service and open dataset; not on GitHub)
- **What it is:** a monthly crawl of a large sample of the web, published as WARC files on S3, with one CDX-style index per crawl at `https://index.commoncrawl.org/<crawl-id>-index`. A list of crawls is at `/collinfo.json`.
- **How to query (tested 21 Sep 2026):** `collinfo.json` listed 128 indexes, the newest `CC-MAIN-2026-39`. A request like `.../CC-MAIN-2026-39-index?url=example.com&matchType=domain&output=json&limit=2` returned JSON with `urlkey`, `timestamp`, `url`, `mime`, `status`, `digest`, `length`, `offset`, `filename`. `showNumPages=true` sizes a query. The record body is fetched from the WARC file with an HTTP range request using `offset` and `length` (unverified detail).
- **Gaps and traps:** it is a sample, not an archive of every page, and one query covers one crawl, so a history means looping over crawls. Redirects and errors sit in separate `crawldiagnostics` files (tested: a 302 row pointed there). The index server timed out with a 504 on my first request and answered on the second, so retry. A columnar (Parquet) index for bulk analysis also exists (unverified).
- **Here:** for the classifieds site we found Common Crawl negligible. A domain query of the September 2026 crawl I ran returned only a few pages of index for the whole domain.
- **Reach for it when / not when:** for large sites and for text corpora. Not for a mid-size listings site; try it once for ten minutes, and if the count is small, stop.

### Katana (Go, MIT, 17k stars, last push 2026-09-14, not archived, latest v1.7.0 2026-08-05)
- **What it is:** a crawler from ProjectDiscovery, a security tooling vendor. Standard mode follows links; headless mode drives Chrome; `-jc` parses JavaScript files for endpoints; `-xhr` extracts XHR URLs; `-kf` reads robots.txt and sitemap.xml; `-td` fingerprints technologies; scope flags control what it follows; JSONL output.
- **Best at:** mapping a site's endpoints, including ones only named inside JavaScript, quickly and as a list.
- **Limits and traps:** the defaults are aggressive for a small site: concurrency 10 and a rate limit of 150 requests per second (README), so set `-rl` and `-rd` deliberately. Our note on a classifieds site recorded a WAF block after about 200 requests per second from one IP, so the default sits in the danger zone. Building from source needs a recent Go toolchain (README says Go 1.26 or newer) and cgo. Headless mode is marked experimental in its own help.
- **Cost or risk:** free; built for authorised security testing, so run it only against public pages, slowly.
- **Reach for it when / not when:** to inventory a site you have not seen. Not as the production scraper; use Scrapy or your existing stack once you know the endpoints.
- **Versus:** gau and CDX look at the past; Katana looks at the live site. Scrapy is the production crawler.

### ultimate-sitemap-parser (Python, GPL-3.0, 257 stars, last push 2026-06-16, not archived; real repo GateNLP/ultimate-sitemap-parser; PyPI ultimate-sitemap-parser 1.8.1, Python 3.10 or newer)
- **Name resolution:** the metadata row for `ultimate-sitemap-parser/ultimate-sitemap-parser` is MISSING because that owner does not exist. The project lives under GateNLP, and its docs and PyPI page point there.
- **What it is:** given a homepage, it finds sitemaps (from robots.txt and by guessing common paths), walks index files, and yields a tree of pages. Formats: XML, Google News and image sitemaps, plain text, RSS 2.0, Atom 0.3 and 1.0 (README).
- **Best at:** the messy real world: tolerant of common sitemap bugs, streaming so huge hierarchies do not fill memory, and the README says it was field-tested on about a million URLs at Media Cloud.
- **Limits and traps:** it supports a custom web client, which matters: a default client that hits a TLS-fingerprint block will find nothing, so pass one that already works on the site. `lastmod` is the site's claim, not the truth. A sitemap lists what the owner chooses to expose; absence proves nothing.
- **Cost or risk:** GPL-3.0. Using it in an internal script is fine; embedding it in something you distribute triggers the licence (unverified legal reading, ask before shipping).
- **Reach for it when / not when:** to enumerate URLs before fetching. Not when Scrapy is already the crawler (it ships its own sitemap spider, unverified detail).

### Protego (Python, BSD-3-Clause, 94 stars, last push 2026-09-21, not archived, latest 0.6.2 2026-06-25, Python 3.10 or newer)
- **What it is:** a pure-Python robots.txt parser implementing RFC 9309 rules and matching, plus `Crawl-delay`, `Request-rate`, `Visit-time` and `Host`. It does not fetch the file; fetching, status-code handling, redirects and caching are left to you (README).
- **Best at:** correct matching. Tested with a rules file containing `Disallow: /*/profile` and `Disallow: /private$`: Protego blocked both, while the standard library `urllib.robotparser` on Python 3.12.4 allowed both, because it ignores the `*` and `$` wildcards.
- **Limits and traps:** argument order is `can_fetch(url, user_agent)`, the reverse of the standard library. You must decide what to do when robots.txt itself returns 403 or 5xx.
- **Reach for it when / not when:** whenever you check robots.txt in code. Robots.txt is the owner's stated preference, a signal to read and respect, not a licence to take.
- **Versus:** reppy (next) and the standard library both mishandle or drop something; Protego is the maintained one.

### reppy (Python and C++, MIT, 197 stars, last push 2024-01-12, not archived, no release on PyPI since 0.4.14 in Sep 2019)
- **What it is:** a robots.txt parser with a C++ core built through Cython and helpers for fetching and cache lifetimes.
- **Limits and traps:** the README requires fetching git submodules when building from source, and the open issue titles include failing pip installs and GCC build failures. I did not try it on Python 3.12; treat it as unmaintained.
- **Reach for it when / not when:** not for new work.
- **Versus:** Protego is pure Python, maintained, and RFC 9309 compliant.

### WhatWeb (Ruby, GPL-2.0, 6k stars, last push 2026-04-02, not archived, latest v0.6.4 2026-04-02)
- **What it is:** identifies what a site runs (CMS, framework, server, analytics, JavaScript libraries) using over 1,800 plugins that match patterns in headers, cookies, HTML and URLs. An aggression level trades speed and stealth against reliability, and a higher level sends more requests (README).
- **Best at:** a one-shot guess at the stack, which tells you whether an admin API path, a known JSON endpoint or a known pagination scheme is likely.
- **Limits and traps:** it is a security scanner from the penetration-testing world; the higher aggression levels probe rather than just read the page. It reads the same page you already fetched, so for one site your own eyes on headers and page source are as good.
- **Reach for it when / not when:** when surveying many unfamiliar sites. Not on a single target; view-source is cheaper.
- **Versus:** Wappalyzer-style rule sets, next.

### Wappalyzer and its successors (status checked)
- **Status:** the open-source Wappalyzer repository went private in August 2023 (stated in the README of enthec/webappanalyzer); `wappalyzer/wappalyzer` returns 404 today. The rule set lives on as `enthec/webappanalyzer` (GPL-3.0, 578 stars, last push 2026-09-16, not archived, same JSON format), the Go library `projectdiscovery/wappalyzergo` (MIT, 1.1k stars, last push 2026-09-20), and the Python wrapper `chorsley/python-Wappalyzer` (GPL-3.0, ARCHIVED, last push 2024-04-03). The commercial Wappalyzer service and browser extension continue (unverified).
- **Best at:** rule-based fingerprinting from headers, cookies, script URLs and HTML patterns, which is quick and needs no scanning.
- **Limits and traps:** rule files go stale as sites change; the archived Python wrapper will not track new rules. Katana's `-td` flag also does technology detection.
- **Reach for it when / not when:** for a tech survey across many sites, using wappalyzergo or the rules directly. Not for a single site.

### GraphQL introspection and InQL (InQL: Kotlin, Apache-2.0, 1k stars, last push 2026-09-09, not archived, latest v6.1.2 2026-02-16)
- **What introspection is:** a GraphQL server can answer a special query (`__schema`, `__type`) with its whole schema: every type, field and argument. When it is enabled you can read the full API without guessing. Many production servers disable it (unverified).
- **InQL:** a Burp Suite extension (v6). It reads an endpoint or a saved introspection file, generates every query, mutation and subscription, adds a GraphQL tab in Burp's message editors, and includes GraphiQL and Voyager viewers. The older standalone InQL on PyPI (4.0.5) was last released in 2021.
- **Limits and traps:** it needs Burp. Two of its features are attack tools: batched queries meant to slip past weak rate limits, and a bruteforcer that rebuilds a schema when introspection is off. Both are outside this skill's line. Read introspection when it is on; do not reconstruct a schema the owner turned off.
- **Reach for it when / not when:** when DevTools shows requests to `/graphql`. Try the introspection query and read the schema with any GraphQL viewer first (unverified); InQL adds convenience, not access.
- **Versus:** for a plain schema dump, a curl request plus a viewer is enough.

### OpenAPI and Swagger discovery (a convention, not a tool)
- **What it is:** many back ends publish a machine-readable API description at predictable paths, and sometimes a browsable UI. Typical paths (unverified): `/openapi.json`, `/swagger.json`, `/v3/api-docs`, `/api-docs`, `/swagger-ui/`, `/docs` and `/redoc` (FastAPI defaults), `/graphql`. Also `robots.txt` and the sitemap sometimes reveal API hosts.
- **Best at:** the cheapest full map of an API: every route, parameter and response shape, with no crawling.
- **Limits and traps:** a public spec may describe routes that need credentials, and a route existing in the spec is not permission to call it. Specs can be out of date or list internal routes.
- **Reach for it when / not when:** after the network panel shows a JSON API, spend one minute checking these paths. Not worth more than a minute of guessing; if it is not there, read the JS bundle.
- **Versus:** GraphQL introspection is the equivalent for GraphQL; a JS bundle is the fallback.

### Reading a JavaScript bundle and source maps (a technique)
- **What it is:** the site's own front-end code names its endpoints, base URLs, parameter names and sometimes feature flags. Download the script files listed in the page (or in the DevTools Sources panel), and search them.
- **Search patterns (unverified):** `fetch(`, `axios`, `XMLHttpRequest`, `baseURL`, `/api/`, `/v1/`, `graphql`, `operationName`, `.get(`, `.post(`, `apiKey`, `client_id`, `sourceMappingURL`, and URL-like string literals. Framework markers: `__NEXT_DATA__` and `/_next/data/<buildId>/` (Next.js), `__NUXT__` (Nuxt), `window.__INITIAL_STATE__`, `<script type="application/ld+json">`.
- **Source maps:** a `.js.map` file, named at the end of a script by `//# sourceMappingURL=`, can contain the original unminified source in `sourcesContent`. If it exists it is far easier to read; if it does not, a prettifier makes minified code legible (unverified).
- **Limits and traps:** minified names are meaningless, and endpoint strings can be assembled at runtime. Any key you find belongs to the site owner; noting that a key exists is discovery, using it to call something you would not otherwise reach is not. Katana's `-jc` does some of this automatically.
- **Reach for it when / not when:** when the network panel shows the call but not how the parameters are built, or when a route exists only for logged-in flows and you need to know only that it is there. Not first; the network panel is cheaper.

---

# B. Mobile and app sources

### jadx (Java, Apache-2.0, 50k stars, last push 2026-09-12, not archived, latest v1.5.6 2026-07-10)
- **What it is:** a decompiler from Android Dalvik bytecode (APK, dex, aar, aab) to Java source, also decoding `AndroidManifest.xml` and resources, with a GUI (`jadx-gui`) that has full-text search, jump-to-declaration and a deobfuscator.
- **Best at:** reading a native Android app written in Java or Kotlin: finding base URLs, request builders and hard-coded constants by text search.
- **Limits and traps:** the README warns that not all code decompiles and errors will occur. It shows nothing useful for a Flutter app, whose logic is compiled Dart in `libapp.so`, not Dalvik. Needs Java 11 or newer, 64-bit.
- **Reach for it when / not when:** first for a native Android app. Not for Flutter or React Native bundles (search the JS bundle for those, or use blutter for Flutter).
- **Versus:** Apktool works at smali and resource level, jadx at readable Java.

### Apktool (Java, Apache-2.0, 25k stars, last push 2026-09-19, not archived, latest v3.0.3 2026-07-20)
- **What it is:** decodes an APK to its resources in near-original form and to smali (readable Dalvik assembly), and can rebuild the APK after changes.
- **Best at:** reading the decoded resources and manifest, network security config and XML strings; unpacking an APK cleanly.
- **Limits and traps:** rebuilding and re-signing changes the app; its README says it is not for piracy. A decoded resource tree is not code: pair it with jadx.
- **Reach for it when / not when:** to inspect resources and manifest, or when jadx fails on a class and you need smali. Not to read logic.
- **Versus:** jadx for code; Apktool for resources and low-level.

### frida (dynamic instrumentation toolkit; repo Meson/C, licence wxWindows Library Licence 3.1 (GitHub shows NOASSERTION), 21k stars, last push 2026-09-16, not archived, latest 17.18.0 2026-09-09)
- **What it is:** injects a JavaScript engine into a running process so you can hook functions, read arguments and return values, and change them. Installed as `frida` and `frida-tools` from PyPI, with a matching helper running on the device (unverified detail).
- **Best at:** seeing what an app does at runtime, where static reading fails: encrypted payloads, values computed at run time, and the functions that build a request.
- **Limits and traps:** it needs an instrumentable device or emulator, and matching versions of client and server (unverified). Anti-tampering in an app can detect it. It is a reverse-engineering tool, and hooking a third-party app to alter or bypass its protections is a step beyond reading it.
- **Cost or risk:** free; licence is a LGPL-style library licence with an exception, so internal use is unproblematic (unverified legal reading).
- **Reach for it when / not when:** when static analysis showed a computed value you cannot reproduce. Not when the data is plainly inside the package (see the Flutter finding below).

### objection (Python, GPL-3.0, 9k stars, last push 2026-09-17, not archived, latest 1.12.5 2026-06-02, Python 3.10 or newer)
- **What it is:** a toolkit on top of frida that gives a ready shell for exploring a mobile app at runtime: file system, keychain, memory, heap objects, and, per the README, "Bypass SSL pinning". Supports iOS and Android, without a jailbreak in some setups (README).
- **Best at:** getting frida's capabilities without writing scripts.
- **Limits and traps:** its own README frames it as a security-assessment tool. Its pinning bypass is the feature that matters here, and it turns a capture tool into a way around a control the app owner put there. That step is where this skill's line begins to bite (see the pinning entry).
- **Reach for it when / not when:** for an app you own or have permission to test. Not to get around a third party's protection as a shortcut to their data.
- **Versus:** raw frida gives control; objection gives speed.

### blutter (C++, MIT, 2k stars, last push 2026-08-18, not archived, no releases)
- **What it is:** a reverse-engineering tool for Flutter apps. It compiles the Dart AOT runtime matching the app's Dart version, loads `libapp.so` (Android arm64 only, per README) and outputs assembly with symbols (`asm/`), a nested dump of the object pool (`objs.txt`, `pp.txt`) and a frida script template.
- **Best at:** getting the compiled Dart objects that hold an app's data and structure, which strings extraction alone cannot give.
- **Limits and traps:** Android `libapp.so` for arm64 only. It supports recent Dart versions, and needs a very recent C++ compiler (g++ 13 or clang 16 or newer); the author recommends Linux, and Windows needs Visual Studio with the C++ workload. On first run it fetches and compiles the Dart source for the app's version.
- **Here:** for one legal-reference app the app used Dart 3.13.1 while blutter supported 3.11. We ported blutter with seven patches, all from one root cause (Dart 3.13 merged the VM and isolate snapshots into one blob); one patch alone cleared 424 of 431 compile errors because the rest were cascades. That build had the code analyser compiled out, so its `asm/` output was not trustworthy and only the object dumps were used.
- **Reach for it when / not when:** when a Flutter app's content sits in `libapp.so` and you need which string belongs to which list, and in what order. Not when the content is in an ordinary asset or a server call.
- **Versus:** jadx cannot read Dart; frida can, at runtime, with more effort.

### mitmproxy for app traffic and certificate pinning (concept)
- **Mechanism:** an app talks to its server over TLS. To read that traffic you place a proxy between them and make the phone trust the proxy's certificate authority. Certificate pinning is when the app ships with the expected certificate or key and refuses any other, so a proxy CA no longer works. Pinning is the obstacle to seeing app traffic.
- **What the mitmproxy docs say:** apps that pin must be patched manually, and they list several tools for Android and jailbroken iOS. Local capture and WireGuard modes exist to route a device or a single app through the proxy.
- **Where this skill's line sits:** watching your own device's traffic to a public, unauthenticated endpoint is discovery. Modifying a third party's app to remove its pinning defeats a protection the owner placed there, and the traffic behind it may need a login or an app token. A study of one legal-reference app stayed static: nothing was run and no server was queried. I do not describe bypass steps here.
- **Reach for it when / not when:** when the app clearly calls an unauthenticated API and you have permission. Not when pinning blocks you and there is no consent to work around it; ask the owner, or use the data that is inside the package.

### The Flutter finding: 18.8 million characters of Arabic law inside libapp.so
- **What we found (one Android legal-reference app built with Flutter):** the package had no `.db`, `.sqlite` or `.json` file, yet `libapp.so` held 31,519 Arabic strings, 18.8 million characters, as Dart string objects. Dart stores each string with a length prefix and two-byte (UTF-16) characters for Arabic, so walking that framing recovers each string exactly. A plain scan for UTF-16 runs split strings at newlines. The strings sit in a hash-ordered table, so which law an article belongs to and the app's display order were not in the strings; they were recovered from the Dart list objects with the patched blutter.
- **Lesson:** for a Flutter release build, look in `lib/arm64-v8a/libapp.so` first. No data file does not mean no data. The Civil Code text was stored in Arabic presentation forms, so normalise with NFKC before matching.
- **A separate question, stated plainly:** whether an app's content may be taken is a different question from whether it can be read. The laws are public, but our own note says the compiled corpus is the developer's compilation (ordering, English translations) and that redistributing it is a question to settle before building a dataset from it. The same binary held an embedded third-party credential; our note is to not test it and not use it. Being able to read a thing does not make it ours.

---

# C. Documents, OCR, audio and video

### The general workflow (read this before choosing any tool)
- **Step 1, extract the text layer and count characters before choosing OCR.** Open each PDF with a text extractor (pdfplumber or PyMuPDF) and count characters per page. Near zero on a page means image-only: OCR. Plenty of characters means there is a text layer: use it, since it is exact, fast and free.
- **Step 2, judge the text layer, not just its size.** A large count can still be garbage: `(cid:123)` placeholders (a font with no text mapping, unverified), replacement characters `U+FFFD`, private-use codepoints, wrong letter order, or Arabic in shaped presentation forms. Count the share of Arabic letters and replacement characters, and read a page by eye. Decide per page: a scanned document with a few text pages needs both paths.
- **Step 3, choose the OCR on a sample.** Hand-type the truth for ten to twenty representative pages, run two or three engines, and measure character error rate on your own documents. Do not rely on README benchmarks; the authors report numbers on their own test sets.
- **Step 4, keep provenance.** Store which pages came from the text layer and which from OCR, plus any confidence score, so a reader can see how far to trust a figure.

### Reversed Arabic text from PDFs (visual order)
- **What happens:** many PDFs place glyphs in visual order and may use shaped glyph forms (Arabic Presentation Forms, U+FB50 to U+FDFF and U+FE70 to U+FEFF). An extractor then returns letters in display order (right to left on the page, but reading left to right in the string), with shaped forms instead of base letters, and Latin words and numbers in odd places.
- **Tested here:** I drew a shaped, visually ordered Arabic line with digits into a PDF (a synthetic PDF, with the ReportLab library) and extracted it with pdfplumber and PyMuPDF. Both returned presentation-form codepoints in visual order with the number first. Reversing the whole string was wrong because of the digits. The fix that reproduced the original logical text was `bidi.algorithm.get_display(unicodedata.normalize("NFKC", line))`: NFKC turns presentation forms back into base letters and the bidi algorithm restores logical order.
- **Caveats:** this was one synthetic PDF. Real PDFs made by Word and other tools often carry a text mapping that returns logical order already, so check each source on a page before you fix anything, and check numbers, dates and Latin runs after fixing. Test that the line search you plan to do (for example an article number) finds the right hits.
- **Here:** one such study recorded that the Civil Code stores its text in presentation forms and that NFKC normalisation is needed before matching.
- **Libraries:** `python-arabic-reshaper` (MIT, 447 stars, last push 2026-04-28) shapes logical text for display in tools that lack Arabic support, and `python-bidi` (LGPL-3.0, 126 stars, last push 2026-06-30) implements the Unicode bidirectional algorithm. Use them in that direction (for drawing text), and use NFKC plus bidi for repairing extracted text.

### pdfplumber (Python, MIT, 10k stars, last push 2026-08-06, not archived, latest v0.11.10 2026-06-15)
- **What it is:** a layer over pdfminer.six that exposes every character, line and rectangle with coordinates, plus table finders and visual debugging images.
- **Best at:** tables in text-based PDFs, where the ruling lines and character positions let you define cells; and any case where position matters (columns, headers, footers).
- **Limits and traps:** no OCR; the README says it works best on machine-generated PDFs. Arabic comes out in visual order with presentation forms (tested, above). Table finder settings need tuning per document.
- **Cost or risk:** MIT; the README says it is tested on Python 3.10 to 3.14. Pure Python, so slower than PyMuPDF (unverified).
- **Reach for it when / not when:** for coordinate-level control and table extraction from clean PDFs. Not for scanned pages, and not when speed on thousands of pages matters most.
- **Versus:** PyMuPDF is faster and can render pages but is AGPL; camelot and tabula specialise in tables.

### PyMuPDF (Python, AGPL-3.0 or commercial, 10k stars, last push 2026-09-21, not archived, latest 1.28.2 2026-08-06, Python 3.10 or newer)
- **What it is:** Python bindings to MuPDF from Artifex: fast text, image and metadata extraction, page rendering, editing. Wheels exist for Windows, macOS and Linux; no mandatory dependencies (README). OCR uses Tesseract, installed separately.
- **Best at:** speed and breadth on text-layer PDFs: one library for text, images, annotations, rendering pages to images for OCR. `pymupdf4llm` (same licence) converts to Markdown.
- **Licence consequence (checked in PyPI metadata and the README):** it is dual licensed, AGPL-3.0 or an Artifex commercial licence, and some features (PyMuPDF Pro) need a licence key. The AGPL is a strong copyleft licence that also covers use over a network: if you distribute a program that includes it, or run it as a service that users reach over a network, you must offer that program's source under the AGPL, or buy the commercial licence. A private batch script that turns PDFs into a dataset is a different case, but that reading is not legal advice (unverified). Do not put it inside a client-facing app or dashboard back end without a decision.
- **Limits and traps:** the same visual-order Arabic behaviour as pdfplumber (tested). It gives you geometry and text, not structure such as tables.
- **Reach for it when / not when:** for fast internal extraction and page rendering. Not inside anything we distribute or hosts for a client, unless the licence question is settled.
- **Versus:** pdfplumber (MIT) is the licence-safe alternative for text and tables; pdfminer.six (MIT) is the engine beneath it.

### pdfminer.six (Python, MIT, 7k stars, last push 2026-03-13, not archived, latest 20260107, Python 3.10 or newer)
- **What it is:** a pure-Python PDF parser and layout analyser (community fork of pdfminer), used by pdfplumber underneath.
- **Best at:** being a permissively licensed, dependency-light parser you can embed anywhere.
- **Limits and traps:** slow on large batches (unverified); layout parameters (`LAParams`) change how lines and words are grouped; Arabic order as above.
- **Reach for it when / not when:** when you need the parser without pdfplumber's table features. Otherwise use pdfplumber.

### camelot (Python, MIT, 3k stars, last push 2026-09-19, not archived, latest v2.0.0 2026-06-04, Python 3.10 or newer)
- **What it is:** table extraction from text-based PDFs. Five parsers per README: `lattice` for ruled tables, `stream`, `network` and `hybrid` for whitespace-separated ones, and an optional neural `ml` (Table Transformer), plus `flavor="auto"`. The default page-image backend (pdfium) is bundled, so no system dependencies.
- **Best at:** ruled tables, where lattice is deterministic; with a heavier optional ML backend for borderless ones.
- **Limits and traps:** the built-in parsers need a text layer (README); scanned pages need the optional `[ml,ocr]` extras. Cell text comes from the PDF's text layer, so Arabic order issues carry over.
- **Reach for it when / not when:** for a table-heavy, text-based PDF. Not for scans without the OCR extras.
- **Versus:** tabula needs Java; pdfplumber gives finer control; docling and marker handle tables inside a wider layout model.

### tabula-py (Python, MIT, 2k stars, last push 2024-12-05, not archived, latest v2.10.0 2024-10-17)
- **What it is:** a Python wrapper around tabula-java that returns tables as pandas data frames.
- **Limits and traps:** needs Java 8 or newer on PATH (README); the README says it was confirmed on macOS and Ubuntu and that some users made it work on Windows 10. Text-based PDFs only. No release since October 2024.
- **Reach for it when / not when:** when a Java runtime is already there and the layout is simple. For new work, camelot 2 has no system dependencies.

### docling (Python, MIT, 67k stars, last push 2026-09-21, not archived, latest v2.129.0 2026-09-18)
- **What it is:** a document converter that runs layout and table-structure models over PDFs and Office files, keeps reading order, and exports Markdown or JSON. README: OCR for scanned pages, audio input through ASR, video parsing, and runs on macOS, Linux and Windows. The docs' examples show pluggable OCR engines (Tesseract, RapidOCR, Surya).
- **Best at:** turning a complex PDF into structured text with tables in one call, feeding an analysis pipeline.
- **Limits and traps:** it downloads model weights and is much heavier than a text extractor. The README says individual models carry their own licences, so check each one. How well it reads Arabic depends on the OCR engine you select, and I did not measure it.
- **Reach for it when / not when:** when layout matters (multi-column, tables, headings) and a GPU or patience is available. Not when a text layer is clean and simple; pdfplumber is enough.
- **Versus:** marker and MinerU do a similar job with different models and licences.

### marker (Python, code Apache-2.0, model weights under a modified AI Pubs Open Rail-M licence, 39k stars, last push 2026-09-13, not archived, latest v2.0.0 2026-07-20)
- **What it is:** converts PDF, images, Office files, HTML and EPUB to Markdown or JSON using layout and OCR models built on the same authors' surya. Optional `--use_llm` mode improves accuracy by sending content to an LLM service you configure.
- **Best at:** fast conversion with good reading order; the authors publish a benchmark table (the author reports).
- **Limits and traps:** the README says the code is free including commercially, but the model weights are free only for research, personal use and startups under 5 million dollars in funding or revenue; beyond that a paid licence applies. The LLM mode sends page content to an external API such as Gemini, Claude or OpenAI, so client documents leave your machine. The README's claim of "all languages" was not tested for Iraqi Arabic.
- **Reach for it when / not when:** for research use on non-confidential documents, or if we is under the threshold. Not for confidential client files with `--use_llm`.

### MinerU (Python, "MinerU Open Source License" (Apache-2.0 with extra terms; GitHub shows NOASSERTION), 80k stars, last push 2026-09-21, not archived, latest mineru-4.0.5 2026-09-20, Python 3.10 to 3.14)
- **What it is:** converts PDFs, scanned images and Office files to Markdown or JSON. The README describes four parsing tiers (Flash, Basic, Standard, Advanced), a default CPU install (ONNX) and a full install for NVIDIA GPUs; on Windows the GPU build of torch has to be installed separately.
- **Licence, read from the LICENSE file:** Apache-2.0 plus two terms. A separate commercial licence is required if you and your affiliates exceed 100 million monthly active users or 20 million dollars monthly revenue, and anyone offering an online service based on it must state prominently that MinerU is used. We is far below the threshold, but the attribution term applies if it ever exposes a service.
- **Limits and traps:** Arabic support is not stated in the parts of the README I read; test it. Heavy install.
- **Reach for it when / not when:** when you want a strong open pipeline and are content with the licence terms. Not when the licence terms must be simple.
- **Versus:** docling (MIT) has a plainer licence; marker's model weights have a revenue cap.

### Tesseract (C++, Apache-2.0, 76k stars, last push 2026-09-11, not archived, latest 5.5.3 2026-07-24)
- **What it is:** the long-standing open-source OCR engine. Since version 4 it uses an LSTM neural engine focused on line recognition, with UTF-8 output and more than 100 languages through separate `traineddata` files (README). Arabic is `ara.traineddata`, present in the `tessdata_best` repository (last push 2024-03-09).
- **Best at:** cheap, local, CPU-only OCR on clean, high-resolution printed text, with no GPU or model server. Runs anywhere; a wrapper such as `pytesseract` only calls the binary.
- **Limits and traps:** it needs the binary and the language data installed; the README stresses that image quality drives results. Arabic quality: weaker on low-resolution scans, ornate fonts, diacritics and mixed Arabic, Latin and digits, and it can return digits or Latin runs in the wrong order (unverified, measure on your own scans). On the laptop the `tesseract` binary was not on PATH when I checked on 21 Sep 2026.
- **Reach for it when / not when:** as the baseline and for clean printed pages. Not when a scan is skewed, noisy or in a decorative font; a document-VLM may do better but costs more.
- **Versus:** EasyOCR and PaddleOCR are neural pipelines that need torch or Paddle; Tesseract is the lightest.

### EasyOCR (Python, Apache-2.0, 30k stars, last push 2025-12-05, not archived, latest v1.7.2 2024-09-24)
- **What it is:** a two-stage neural OCR (a text detector, then a CRNN recogniser) with 80 or more languages including Arabic in one reader object; `gpu=False` runs on CPU (README).
- **Best at:** getting text and boxes from photos and scene text with almost no set-up, in many scripts.
- **Limits and traps:** no release since September 2024 and no commit since December 2025, so no path to newer models. Needs PyTorch. The README example uses Chinese, not Arabic, and I did not test Arabic.
- **Reach for it when / not when:** for a quick multi-language pass on photos of signs or forms. Not as the long-term pipeline.
- **Versus:** Tesseract for printed pages; PaddleOCR for a maintained neural option.

### PaddleOCR (Python, Apache-2.0, 89k stars, last push 2026-09-16, not archived, latest v3.7.0 2026-06-11)
- **What it is:** an OCR and document-parsing toolkit on the PaddlePaddle framework: detection and recognition models (PP-OCR series), PP-StructureV3 for layout to Markdown or JSON, and PaddleOCR-VL, a small vision-language model.
- **Best at:** the widest maintained set of document tools. What the README claims for Arabic: PP-OCRv5 has a multilingual recognition model covering 109 languages including Arabic, and PaddleOCR-VL supports 109 languages including Arabic. The newer PP-OCRv6 lists 50 languages (Chinese, English, Japanese and 46 Latin-script ones), which does not include Arabic per that text.
- **Limits and traps:** it needs the PaddlePaddle framework, which is a separate install from PyTorch and can be awkward on Windows (unverified). Which model handles Arabic depends on the version and pipeline you choose. The README benchmarks are the author's.
- **Reach for it when / not when:** when you need layout-aware output or a maintained neural OCR and can test Arabic first. Not if you want a single small dependency.

### surya (Python, code Apache-2.0, model weights under a modified AI Pubs Open Rail-M licence, 21k stars, last push 2026-09-11, not archived, latest v0.22.1 2026-07-20)
- **What it is:** OCR, layout analysis, reading order and table recognition in 90 or more languages (README claim), from the marker authors. It runs a model behind a local inference server that it starts itself: vLLM with Docker and NVIDIA Container Toolkit on a GPU, or llama.cpp on CPU or Apple Silicon.
- **Best at:** page-level OCR with layout and reading order together, faster on a GPU.
- **Limits and traps:** the weights carry the same revenue and funding cap as marker (free for research, personal use and startups under 5 million dollars). The set-up needs Docker or llama.cpp, so it is heavier on a Windows laptop than Tesseract. The README's benchmark figures are the author's own.
- **Reach for it when / not when:** for a GPU box (the Ubuntu server) processing scanned documents in bulk. Not for one-off pages on the laptop.

### chandra (Python, code Apache-2.0, model under OpenRAIL-M, 12k stars, last push 2026-06-26, not archived, latest v0.2.0 2026-03-18)
- **What it is:** a vision-language OCR model for complex tables, forms, handwriting and full layout, run through a vLLM server or Hugging Face, with 90 or more languages and an Arabic example in the README.
- **Best at:** hard layouts and handwriting that classical OCR fails on.
- **Limits and traps:** commercial self-hosting needs a licence (README), and the authors' hosted platform is described as more accurate than the open weights. A generative model can produce fluent text that is not on the page (unverified for this model), so validate against the character counts, the page image and a hand-typed sample.
- **Reach for it when / not when:** for pages that classical OCR gets wrong, with the licence read first. Not as the bulk engine on the laptop.
- **Versus:** surya is the layout-and-OCR stack from the same authors; chandra is the heavier VLM.

### yt-dlp (Python, Unlicense, 192k stars, last push 2026-09-16, not archived, latest 2026.08.19 2026-08-19, Python 3.10 or newer)
- **What it is:** a downloader for audio and video from thousands of sites, using per-site extractors and choosing formats.
- **Best at:** getting the audio of a public video or reel for transcription. On Windows a standalone `yt-dlp.exe` exists.
- **Limits and traps:** ffmpeg is needed for merging and audio extraction (the binary, not the Python package of that name); full YouTube support needs the `yt-dlp-ejs` component and a JavaScript runtime such as Deno or Node (README); impersonation of a browser TLS profile goes through `curl_cffi`. Extractors break when sites change, so update often. Downloading media can conflict with a platform's terms and with copyright on the content.
- **Cost or risk:** many sites now demand cookies (`--cookies-from-browser`) for the logged-in view; using a logged-in session is outside this skill's line, so accept that some sites are out of reach.
- **Reach for it when / not when:** for public, anonymous video or audio you are allowed to process. Not as a way in behind a login.
- **Versus:** instaloader is Instagram-specific.

### whisper (Python, MIT, 109k stars, last push 2026-08-31, not archived, latest v20250625 2025-06-26)
- **What it is:** OpenAI's speech-recognition model family (tiny to large, plus `turbo`), multilingual, also translating to English, needing ffmpeg. The README gives VRAM figures of about 10 GB for large and 6 GB for turbo, and says `turbo` is not trained for translation. `faster-whisper` (MIT, PyPI 1.2.1) is a separate re-implementation for speed.
- **Best at:** clean speech in major languages; free and local.
- **Limits and traps:** the README shows accuracy varying widely by language in a chart. Arabic is uneven, and we recorded that Iraqi Arabic is the weakest link in any Arabic speech pipeline: expect dialect words and code-switching to come out wrong or invented, and numbers and names to be unreliable. Recordings that are noisy, several people at once, or WhatsApp-compressed make it worse. Long audio can loop or hallucinate text (unverified, check on your recordings).
- **Reach for it when / not when:** for English or standard Arabic audio, as a first draft. Plain Whisper is reported weaker on Iraqi-dialect speech than on standard Arabic (a team's recorded experience, not measured here), so plan for a human correction pass on dialect interviews.
- **Versus:** faster-whisper for speed; a hosted model for accuracy on dialect, at a cost and with data leaving the machine.

---

# D. Platform-specific sources

### Telethon (Python, MIT, 12k stars, last push 2026-02-21, ARCHIVED on GitHub; Codeberg repo active; PyPI 1.45.0, 2026-09-10)
- **What it is:** an asyncio MTProto client library: it speaks Telegram's own protocol as a user or a bot account, so it can read channel history, join chats and download media.
- **Why it is archived, and what replaced it (checked):** the GitHub repository's first line says it moved to `codeberg.org/Lonami/Telethon` and that the GitHub copy may be deleted, and the last GitHub commit (2026-02-21) is "Migrate off GitHub". The Codeberg copy is alive: commits on 2026-09-10 (bump to v1.45) and 2026-09-14, and the PyPI project's Source and Download links point there. So nothing replaced it: it is archived because it moved. Pin `telethon` from PyPI and watch Codeberg. Pyrogram, a similar library, is archived on GitHub with its last PyPI release in April 2023; `kurigram` (PyPI 2.2.26, 2026-09-12) is a maintained fork of it (unverified).
- **Limits and traps:** it needs a real Telegram account and an `api_id` and `api_hash` from my.telegram.org tied to a phone number. Telegram states that all API client libraries are strictly monitored, that accounts using unofficial clients are automatically put under observation, and that flooding, spam or faking counters gets accounts banned. A session file is a login credential.
- **Where this skill's line sits:** a user session is a login. Reading public channels this way is a logged-in access and is outside this skill's rule of public data only. Use it only with explicit approval and a dedicated account.
- **Reach for it when / not when:** never as the default for public channels; see the web preview below. Not for anything that looks like user scraping or joining private groups.

### Telegram public channel preview `t.me/s/<channel>` (web page, tested)
- **What it is:** for public channels, Telegram serves a login-free HTML preview of recent posts at `https://t.me/s/<channel>`.
- **Tested:** `t.me/s/telegram` returned HTTP 200 with 20 message blocks (`tgme_widget_message_wrap`), message text in `tgme_widget_message_text`, and a `data-before` marker used for paging older posts.
- **Limits and traps:** only public channels, and only where the preview is available; there is no full-history guarantee, and the markup can change at any time. The rendered text loses some formatting.
- **Reach for it when / not when:** for a public channel's recent posts, with a polite rate. Not for private chats or full history.
- **Versus:** Telethon reads more but needs a login; the Bot API cannot read a channel it has not been added to.

### Telegram Bot API (official HTTP API; documentation at core.telegram.org/bots)
- **What it is:** the official interface for bots, created through @BotFather; the bot receives updates by long polling or webhook and sends messages.
- **Limits, from the Bots FAQ (checked):** about one message per second in a single chat; no more than 20 messages a minute in a group; about 30 messages a second across a broadcast unless paid broadcasts are enabled (up to 1,000 a second at 0.1 Stars per message over the free amount). `getFile` works only for files up to 20 MB, and bots can send files up to 50 MB. A bot receives messages from private chats and from channels where it is a member; with privacy mode on it sees only commands and replies in groups.
- **What it cannot do:** it is not a way to read the history of a channel it has not been added to, and a bot cannot start a conversation with a user who has not started it (unverified). Updates are kept only for a limited time if unread (about 24 hours, unverified).
- **Reach for it when / not when:** to send alerts from a pipeline (we already ships archives to Telegram that way) or to take input from users. Not as a collection tool for other people's channels.

### instaloader (Python, MIT, 13k stars, last push 2026-09-06, not archived, latest v4.15.3 2026-07-26, Python 3.9 or newer)
- **What it is:** downloads profiles, posts, stories, hashtags, comments and captions from Instagram, with a built-in rate controller and resume support.
- **Best at:** the most complete open tool for Instagram data, with sane pacing.
- **Limits and traps (from its docs):** it assumes it is the only client consuming requests, and restarting it often causes 429 errors. Cloud, VPN and proxy IPs face stricter limits for anonymous access, while logged-in access "does not seem to be affected". Private profiles need an approved follow. Login problems and Instagram's checkpoint challenge are documented. The README says it is unofficial and to use it at your own risk.
- **Terms and account risk (unverified):** Instagram's terms forbid automated collection, and accounts used for it are checkpointed, restricted or banned. A personal or work account is not something to risk.
- **Where this skill's line sits:** public data only, and nothing behind a login. That leaves anonymous public profile reads, slowly, and the API's limits will decide how far that goes.
- **Reach for it when / not when:** for a small number of public profiles or hashtags, with authorisation from the client. Not for bulk, and not with a logged-in session.
- **Versus:** yt-dlp for a single public reel; Apify actors and the platform's own APIs for anything larger, with the terms read.

### snscrape (Python, GPL-3.0, 5k stars, last push 2023-11-15, not archived, PyPI 0.7.0.20230622)
- **What it is:** a scraper for social sites that returned posts for users, hashtags and searches without API keys.
- **State (checked):** its maintainer wrote on 2025-02-13 in issue #1045 that Telegram and Weibo work, Mastodon works on old 3.x servers only, Facebook and Instagram have had issues for a long time, Reddit depended on Pushshift which is no longer public, VK is broken, and Twitter is broken due to the login wall. Tested: `pip install snscrape` on Python 3.12.7 succeeds, but running `snscrape --help` fails at import with `'FileFinder' object has no attribute 'find_module'`, so the released package does not run on Python 3.12 (its tracker has issues and pull requests about the removed `find_module`).
- **Reach for it when / not when:** not for new work. For public Telegram channels use the web preview above.
- **Versus:** instaloader (maintained), and official APIs.

### Overpass API (engine: C++, AGPL-3.0, 924 stars, last push 2026-02-19, not archived, release osm3s_v0.7.62.4 2024-11-21; the public instance is a service, not the repo)
- **What it is:** a read-only query engine for OpenStreetMap data with its own language (Overpass QL). You send a query such as `[out:json][timeout:90]; area["ISO3166-1"="IQ"]->.a; nwr["man_made"="mast"](area.a); out count;` and get elements back; `out count;` gives a cheap size before you download.
- **Best at:** asking for exactly the tagged features in an area, without downloading the whole country.
- **Limits and traps:** on the main instance (`overpass-api.de`, run by FOSSGIS) the wiki says you do not disturb other users under about 10,000 queries and 1 GB per day, and to send a User-Agent that identifies you. Tested: several of my count queries on 21 Sep 2026 came back with HTTP 429 or 504 and an HTML error page ("the server is probably too busy"), and succeeded on retry, so check for `"elements"` in the body and back off. Other public instances have different policies; you can also run your own or use Geofabrik regional extracts. The response carries a data timestamp (`timestamp_osm_base`), which you should record.
- **Data licence:** the response states the data is made available under ODbL; that licence carries attribution and share-alike duties for derived databases (unverified detail, read it before delivering a dataset).
- **Reach for it when / not when:** for tag-based feature extraction of a region. Not for continuous heavy use of the public instance.
- **Versus:** osmnx (next) wraps it for street networks and GeoDataFrames; a Geofabrik extract is better for very large pulls.
- **Here, the tag-filter finding (we used OSM for telecom sites):** a filter on `man_made=mast` can be padded and incomplete at once. Reproduced on 21 Sep 2026 for area `ISO3166-1=IQ`, counting nodes and ways: `man_made=mast` gave 1,118 objects; `tower:type=communication` on any object gave 945; both together gave only 99. Of the 945 typed as communication, 798 are `man_made=tower` and only 99 are masts (the other 48 carry some other or no `man_made` value), so a mast filter misses 846 of them (the OSM wiki says `tower:type` is used with `man_made=tower` as well as `man_made=mast`). And 1,019 of the 1,118 masts carry no `communication` type (they may be lighting, siren or untyped masts). `man_made=communications_tower` is a third tag, with 25 objects. Untyped masts may still be telecom, so "padded" means unproven, not wrong. Use a union of tags and check a sample of each subset by eye.

### osmnx (Python, MIT, 5k stars, last push 2026-07-31, not archived, no GitHub releases listed; PyPI 2.1.1, 2026-07-21, Python 3.11 or newer)
- **What it is:** a library that downloads, models and analyses OpenStreetMap street networks and other features into GeoDataFrames and graphs, using Overpass for the data (unverified detail of the calls).
- **Best at:** road networks, routing and features inside a named place polygon, with a Python-native result ready for geopandas.
- **Limits and traps:** it needs a compatible geospatial stack (geopandas, shapely) and Python 3.11 or newer. It inherits Overpass's limits and its data gaps. A place name is resolved by a geocoder, so a wrong match silently changes the polygon.
- **Reach for it when / not when:** for network analysis and polygon-based feature pulls. Not for exact tag counts where you want to see the raw query; use Overpass directly.

### Google Places API (New) vs scraping (official service; pricing not on GitHub)
- **What it is:** Google's official interface to place data: Text Search, Nearby Search and Place Details, billed per request and per field group (check current pricing). It needs an API key and a billing account (unverified).
- **What is checked from Google's documentation (21 Sep 2026):** Text Search (New) returns 20 results per page and at most 60 across all pages (the limit is subject to change), so a wide area needs many small queries. The policy page says you must not pre-fetch, cache or store Places content beyond the allowed exceptions, and that `place_id` is exempt from caching limits.
- **Best at:** legitimate, stable, structured data that will not break next month, with support.
- **Limits and traps:** the caching rule matters for a firm that delivers stored datasets: the official route is not automatically the compliant route for a dataset you keep. Cost grows with fields requested, so ask for only the fields you need with a field mask. Coverage of phone numbers depends on what businesses entered, as with scraping.
- **The alternative:** scraping Google Maps breaches Google's terms (unverified but widely stated) and needs proxies and upkeep at volume; this skill's line rules out rotating proxies to get past a block.
- **Reach for it when / not when:** for small, defined jobs, live lookups and anything shown to a client with attribution. For large stored datasets, read the policy first and decide with the client.
- **Versus:** gosom and Apify actors for bulk; the results we measured show phone coverage came from the neighbourhood, not the tool.

### gosom/google-maps-scraper (Go, MIT, 5k stars, last push 2026-09-20, not archived, latest v1.18.1 2026-09-20)
- **What it is:** a browser-driven Google Maps scraper with a CLI, a web UI and a REST API, using Playwright, output to CSV, JSON, PostgreSQL or S3. The README lists 33 or more data points, email extraction, and proxy support, and its legal notice says unauthorised scraping may violate terms of service.
- **Best at:** a free, self-run bulk pull with no per-place fee. The author reports about 120 places a minute; that was not what we measured (below).
- **Limits and traps:** the README is a wall of sponsor banners, including proxy sellers; the sponsors are not endorsements. The optional agent workflow needs Docker and, on Windows, WSL. Coverage of the data it returns depends on Google's listing.
- **Here:** the binary is available on the laptop. Measured: identical phone coverage to scraperlink and compass on the same ground; CPU-bound (6 workers gave 61 places a minute and 12 workers gave 53); it hangs after finishing a tile. Phone coverage is a property of the neighbourhood (about 70% north Baghdad, 29% south), not of the tool.
- **Reach for it when / not when:** for many places on your own hardware, with tiles small enough to finish. Not if you need results without babysitting, and not with rotating proxies to get past blocks.
- **Versus:** scraperlink (Apify) costs $0.50 per 1,000 places against $3.00 for compass (BRONZE tier); its bounding box does not confine results (23 of 300 inside).

### omkarcloud/google-maps-scraper (no language; repository MIT, 3k stars, last push 2026-09-12, not archived, no releases)
- **What it is (from the README and a listing of the repository):** a commercial desktop application, not open-source software. The repository holds only the README, three documentation pages, a deployment note, screenshots and a MIT LICENSE file; there is no source code. The README tells you to download the app from omkar.cloud (Windows, Mac, Linux), built with the same author's Botasaurus Desktop framework.
- **The badge and the stars:** the MIT licence and star count belong to a documentation repository that markets the product. The README states the free plan is 200 searches a month; its pricing section lists Starter at 16 dollars a month for 5,000 searches and Unlimited at 48 dollars a month (the author's figures, check current pricing). The README also advertises email and "decision-maker" enrichment; that is personal data, which needs its own consideration. Its enrichment code is open in a separate repository.
- **Limits and traps:** you cannot audit, patch or pin what the desktop app does. The MIT licence applies to the repository contents, not to the app (unverified legal reading).
- **Reach for it when / not when:** not for our pipelines; there is nothing to install from GitHub. It is a paid product to evaluate like any vendor.
- **Versus:** gosom is real source you can read and run; scraperlink and compass are pay-per-result Apify actors.

---

# How to choose

**Discovering where a page's data comes from, in the cheapest order.** Start with what costs nothing and shows the most. First, fetch the URL and read the raw response: if the data is in the HTML, in a JSON-LD block, or in an embedded state object such as `__NEXT_DATA__`, you are done and no browser is needed. Second, read robots.txt and the sitemaps (Protego, ultimate-sitemap-parser) for the owner's own list of pages and stated preferences. Third, open DevTools, filter to Fetch and XHR, and find the call that returns the data; copy it as cURL, run it without your cookies to see what it really needs, and convert it (curlconverter). If it works in curl but not in Python, suspect the TLS fingerprint before the headers. Fourth, check the cheap conventions: OpenAPI paths and a GraphQL endpoint with introspection. Fifth, if the call is built by script, search the JS bundle and any source map. Sixth, if you need history or a full id list, ask the archives: query the Wayback CDX API directly, and give Common Crawl one ten-minute look (for the classifieds site the first held 95,773 ids and the second was negligible, so try both before building anything, but do not expect either to hold the page bodies you want). Seventh, for an app, look inside the package first (a Flutter app's `libapp.so` held 18.8 million characters of law), then read with jadx or blutter, and only then consider watching traffic, remembering that pinning is a protection the owner placed there. A crawler such as Katana is for a live inventory of a site you have not mapped, and its defaults are fast enough to trip a WAF, so set the rate yourself. The evidence that should make you switch tools is concrete: the data is not in the raw HTML (go to the network panel), the call works in a browser but not in code (fingerprint, then a browser), the id list from an archive is large but few bodies are usable (the archive is the wrong source, ask the owner).

**Turning files and recordings into text.** Count first: extract the text layer, count characters per page and check the share of Arabic letters, then decide per page whether OCR is needed. Repair the order (NFKC plus bidi) before searching or counting anything, and check on a real page that the repair worked. For OCR, run Tesseract as the cheap baseline, then try one or two heavier engines (PaddleOCR, surya, chandra, docling with a chosen engine) on twenty hand-typed pages and pick by measured character error rate, not by README numbers. Read the licences of the model weights before adopting one: several are free only below a revenue or funding threshold, and PyMuPDF is AGPL. For speech, run Whisper on standard Arabic and English, and expect Iraqi dialect to be the weak point; keep a human check on any figure or name that comes from audio.

**Official API, scraping, or asking.** These are not ranked by effort; they are ranked by what you are allowed and what you can stand behind. Use the official API when one exists that returns the fields you need, at a price that fits, and whose terms let you keep the result for the use you have in mind: read the policy, because the Google Places terms forbid storing most content, so the "official" route can be the wrong one for a delivered dataset. Scrape when the data is public, anonymous and the volume is modest, when you pace requests, identify yourself honestly, copy only what a real browser sends, and treat a refusal as an answer: this skill does not defeat anti-bot challenges, rotate identities or proxies to pass a block, or go behind a login, which rules out user sessions on Telegram and Instagram and the logged-in modes of yt-dlp and instaloader. Ask when the answer to any of these is no, and when the volume would strain the site: our work on a classifieds site concluded that a full sweep would need the owner's consent. The same ordering applies to apps: the fact that a binary can be read does not settle whether its content may be taken, and a compiled corpus is someone's compilation. If two routes are both allowed, take the one that breaks least often: an API or a public export over a scraper, a scraper over a browser, a browser over a phone app.
