# Category: Fetching and crawl frameworks

Status data for every GitHub project below comes from ghmeta.tsv (read from GitHub on 21 Sep 2026). Where I checked PyPI, a project README, a changelog or the laptop itself on 21 Sep 2026, the line says so. A line that ends `(unverified)` is from my own knowledge. Stars are the table's rounded figures. No project in this file is marked archived in the table. Star counts measure attention, not maturity or fit.

Three findings worth knowing before reading the entries:

- The Python HTTP client `httpx` is in a maintenance gap. Its last stable release is 0.28.1 (Dec 2024); 1.0 pre-releases exist (1.0.dev6, 31 Aug 2026); and Pydantic now publishes `httpx2` (2.13.0, 14 Sep 2026), which its README calls a continuation, and which Scrapy 2.18 and Crawlee already depend on.
- `rnet` was renamed. The GitHub repo `0x676e67/rnet` now redirects to `wreq-python`, the maintained PyPI package is `wreq` (0.12.2, Apache-2.0, Python >= 3.11), and the old PyPI name `rnet` is stale (last release Oct 2025, and its 2.4.2 metadata says GPL-3.0 while the repo says Apache-2.0).
- The installed Scrapy (2.12.0) and curl_cffi (0.11.1) are well behind current releases (2.19.0 and 0.16.3 stable). This matters for HTTP/3 (curl_cffi) and for the reactorless, httpx and aiohttp download handlers (Scrapy).

---

## A. HTTP clients

### A0. What a server can see of a client, and why impersonation clients exist

A server, or the CDN in front of it, learns about a client in layers. Every layer below the HTTP body is decided by the client library, not by the headers you set.

- **IP and network.** The address, its ASN (hosting company, ISP, mobile carrier) and its history. A client cannot change this; a proxy does (section B).
- **TLS ClientHello.** The first message of the handshake lists TLS versions, cipher suites, extensions, supported groups, signature algorithms, ALPN protocols and (in browsers) random GREASE values, each in a particular order. Python's `ssl` (OpenSSL), Go's `crypto/tls`, Node's `tls` (OpenSSL), Schannel (Windows curl.exe) and BoringSSL (Chrome, Safari-like stacks) each produce a different, recognisable ClientHello. (unverified as a general statement; curl-impersonate's README describes the same mechanism)
- **JA3 and JA4.** JA3 is a hash of the ClientHello fields in the order sent. Chrome began shuffling extension order in 2023, which made JA3 unstable for real Chrome; JA4 sorts the fields first and splits them into sections, so it survives shuffling. Servers and CDNs compare the hash to lists of known browsers and known library signatures, at the edge, before any HTTP request is read. (unverified in detail)
- **HTTP/2 connection settings.** Right after the handshake the client sends a SETTINGS frame (window sizes, max concurrent streams, header table size), a WINDOW_UPDATE, sometimes priority frames, and then pseudo-headers in a set order. Browsers differ on all of these, so a hash of them (often called the Akamai fingerprint) identifies the browser family. curl-impersonate's README confirms HTTP/2 settings are a second fingerprinting layer. A client that speaks only HTTP/1.1 to a site where every browser negotiates HTTP/2 is itself a signal. (the last point unverified)
- **HTTP headers.** Which headers are present, their casing and their order, `Accept-Encoding` values (Chrome offers zstd now), the `Sec-CH-UA` and `Sec-Fetch-*` families, `Accept-Language`. A Chrome User-Agent over a Firefox-shaped handshake is a contradiction the server can test.
- **HTTP/3 and QUIC.** A separate handshake over UDP with its own transport parameters, fingerprinted the same way. curl_cffi and tls-client both claim HTTP/3 fingerprints (their READMEs).
- **Behaviour.** Connection reuse (a browser keeps one connection per origin and multiplexes), cookies carried across requests, the pattern of sub-resources fetched (a browser pulls CSS, scripts and images; a script pulls one HTML document), timing and request cadence. A client with no cookie jar looks like a new visitor on every request.

Why impersonation clients exist: `requests`, `httpx` and `aiohttp` all ride on Python's OpenSSL, so their ClientHello matches no browser. Some sites therefore serve a different response or a block to that handshake, whatever the User-Agent says. Impersonation clients reproduce a real browser's ClientHello and HTTP/2 settings. There are two techniques: compile against the same TLS library with the same options (curl-impersonate and curl_cffi on BoringSSL; wreq and primp in Rust, also BoringSSL per wreq's README), or take a normal TLS library and rewrite the ClientHello it sends (utls in Go). The header set must then agree with the handshake.

Measured here: on a used-car listing site, plain `requests` on Ubuntu could not pass even through clean proxies (0 of 12), and `curl_cffi` with `impersonate="chrome"` passed 8 of 8. That is a TLS-fingerprint block, and it is the strongest single argument for putting an impersonating client early in the ladder.

Where this skill's line sits: sending what a real browser sends (its headers and its TLS handshake) is inside the line. Defeating a challenge (Turnstile, interstitials, CAPTCHAs), rotating identities to get past a block, or anything behind a login is outside it. Several READMEs below carry sponsor banners for services on the far side of that line; the libraries themselves are on the near side.

### A1. Capability table

Cells marked (u) are from my knowledge, not checked. Others come from a README, a changelog, PyPI, or a measurement on this laptop (21 Sep 2026).

| Client | HTTP/2 | HTTP/3 | Async | Windows | Impersonates a browser |
|---|---|---|---|---|---|
| requests | no | no | none (use threads) | yes | no |
| httpx | yes, opt-in `http2=True` plus the `h2` package (measured here: HTTP/2 when on, HTTP/1.1 by default) | no | yes, `AsyncClient` and sync | yes | no |
| aiohttp | no in the client (u; curl_cffi's README table says the same) | no | async only | yes, wheels on PyPI | no |
| urllib3 | listed as experimental in its changelog | no | no | yes | no |
| curl (CLI) | build-dependent | build-dependent | not applicable | ships with Windows 11 | no |
| curl_cffi | yes | yes since 0.11.4 (README); not on the installed 0.11.1 | yes, `AsyncSession` | yes, win_amd64 and win_arm64 wheels | yes |
| curl-impersonate | yes | yes (README: built with HTTP/3) | not applicable (CLI and C library) | yes, prebuilt binaries per README | yes |
| tls-client (Go) | yes | yes (README) | Go goroutines; Python and Node bindings via FFI | via shared library (u) | yes |
| hrequests | yes | not stated | gevent and goroutines (README) | no Windows wheel on PyPI; a Go binary is fetched after install | yes |
| wreq (ex rnet) | yes | not stated in the README I read | yes, async and blocking | yes, wheels | yes |
| primp | yes (docs list HTTP2 fingerprinting) | not stated | yes, `AsyncClient` | yes, wheels | yes |
| utls (Go) | not its job (TLS layer only) | not its job | Go | yes | ClientHello only |
| got (Node) | yes (option) | no (u) | promises | yes | no |
| undici (Node) | opt-in `allowH2` (docs) | no (u) | promises | yes | no |
| axios (Node) | experimental (README) | no (u) | promises | yes | no |

---

### requests (Python, Apache-2.0, 54k stars, last push 2026-09-07, not archived, latest v2.34.2 2026-05-14)
- **What it is:** synchronous HTTP/1.1 client over urllib3 with sessions, cookie jar, redirects and a very familiar API. Python >= 3.10 (PyPI).
- **Best at:** being the lowest-friction way to fetch a page or call an API, with the most examples and the most tools built to mimic it.
- **Limits and traps:** no async and no HTTP/2 (measured: HTTP/1.1). Its ClientHello is OpenSSL's and matches no browser, which is what failed on a used-car listing site. It reads proxy settings from the environment and `.netrc` by default, a surprise behind a corporate or Windows proxy setup (unverified). Its default header set and order are recognisably its own.
- **Cost or risk:** none; actively maintained.
- **Reach for it when / not when:** for open APIs and friendly pages where nothing filters on the handshake. Not when a site blocks by fingerprint, or when you need more than a few dozen requests in parallel.
- **Versus:** httpx adds async and HTTP/2; curl_cffi keeps the same call shape and fixes the fingerprint.
- **Here:** requests 2.34.2 installed.

### httpx (Python, BSD-3-Clause, 15k stars, last push 2026-03-29, not archived, latest 0.28.1 2024-12-06)
- **What it is:** sync and async HTTP client on httpcore, with opt-in HTTP/2 through the `h2` package (`httpx[http2]`) and optional SOCKS and Brotli extras (PyPI extras).
- **Best at:** one API for sync and async, timeouts that are explicit by default, HTTP/2 multiplexing to one origin.
- **Limits and traps:** HTTP/2 is off unless asked for (measured: `http2=True` gave HTTP/2, default gave HTTP/1.1). Still OpenSSL, so still a non-browser ClientHello. Redirects are not followed by default, unlike requests.
- **Cost or risk:** maintenance. Stable release unchanged for about 21 months; 1.0 dev pre-releases exist; Pydantic's `httpx2` (BSD-3-Clause, 1.4k stars, pushed 2026-09-21, read from GitHub, not in the table) describes itself as the continuation and Scrapy 2.18 calls it the successor. For new code, prefer to isolate the client behind a small function so the swap is one line. I have not tested httpx2.
- **Reach for it when / not when:** async fetching of friendly targets, or HTTP/2 to an API. Not when the fingerprint matters.
- **Versus:** aiohttp has no client HTTP/2; curl_cffi has the fingerprint and HTTP/2 but a different async engine.
- **Here:** httpx 0.28.1 installed; the interpreter I used also had h2 3.2.0, which satisfies httpx's `h2<5,>=3` extra.

### aiohttp (Python, Apache-2.0 AND MIT per PyPI, 16k stars, last push 2026-09-19, not archived, latest v3.14.3 2026-07-22)
- **What it is:** asyncio client and server framework with its own connection pool, cookie jar and WebSocket support. Python >= 3.10.
- **Best at:** very high concurrency of plain HTTP/1.1 fetches with low overhead; the most direct asyncio primitive.
- **Limits and traps:** async only; HTTP/1.1 in the client; OpenSSL ClientHello. The default connection limit is a total of 100 (unverified), a silent throttle if you expect more. On Windows the optional `aiodns` resolver needs the selector event loop (unverified).
- **Cost or risk:** none; very active.
- **Reach for it when / not when:** when you want raw asyncio throughput on cooperative APIs and already live in asyncio. Not for fingerprint-sensitive sites.
- **Versus:** httpx is friendlier and has HTTP/2; curl_cffi's `AsyncSession` gives the same concurrency with browser handshakes. Scrapy 2.19 adopted aiohttp for its reactorless mode (Scrapy release notes).
- **Here:** observed 3.9.5 on the interpreter I ran (not in the brief's installed list); not otherwise used.

### urllib3 (Python, MIT, 4k stars, last push 2026-09-20, not archived, latest 2.8.0 2026-09-15)
- **What it is:** the connection pooling, retry and TLS layer under requests (and under many others).
- **Best at:** being the thing you use directly when you need fine control of pooling, retries with backoff, or a custom SSL context without a client's extras.
- **Limits and traps:** sync only; HTTP/2 is labelled experimental and "early development" in its changelog (I did not test it); no fingerprint control beyond passing your own `ssl.SSLContext`, which changes cipher lists but not the whole ClientHello (unverified).
- **Cost or risk:** none.
- **Reach for it when / not when:** for retry and pool policy inside your own tooling. Not as a scraping client in itself.
- **Versus:** requests is urllib3 with a friendlier API.

### curl, the command-line tool (C, MIT-style licence, not in the table) (unverified except the two lines marked "here")
- **What it is:** the reference HTTP tool; libcurl underneath is what curl_cffi and curl-impersonate patch.
- **Best at:** one-off diagnosis: `-v` shows the TLS negotiation, `-I` the headers, `--http2` or `--http3` force a version if the build has it; and copying a request out of browser DevTools ("Copy as cURL") to replay it.
- **Limits and traps:** the Windows build ships with Schannel as its TLS library, so its ClientHello is Windows's, not a browser's. Feature flags vary by build.
- **Cost or risk:** none.
- **Reach for it when / not when:** to test whether a URL answers at all and what it sends back. Not for crawls.
- **Versus:** curl-impersonate is curl rebuilt to look like a browser.
- **Here:** `C:\Windows\System32\curl.exe` is 8.21.0 with Schannel and no HTTP/2 or HTTP/3 in its feature list; a request to https://example.com reported HTTP/1.1 (measured 21 Sep 2026). The Git Bash curl on the PATH is 8.18.0 (Schannel, no HTTP/2 in its feature list either) and the Anaconda folder has a third copy. Do not assume which one a command runs.

### wget and aria2 (C, GPL, not in the table) (unverified, from knowledge, and not installed here; `which` found neither on 21 Sep 2026)
- **What it is:** wget is a non-interactive downloader with recursive mirroring, cookie support and WARC output. aria2 is a segmented, resumable multi-connection downloader for HTTP, FTP and BitTorrent, controllable through a JSON-RPC daemon.
- **Best at:** wget for mirroring a small static site or capturing one URL to WARC; aria2 for pulling large files fast and resumably.
- **Limits and traps:** neither executes JavaScript; wget speaks HTTP/1.1 only (as I recall) and obeys robots.txt in recursive mode by default; both have non-browser TLS.
- **Cost or risk:** none; recursive wget will happily hammer a server, so set `--wait`.
- **Reach for it when / not when:** wget for a quick static mirror or a WARC of one page; aria2 for big files (a dataset, a PDF corpus). Not for anything that needs parsing logic.
- **Versus:** ArchiveBox wraps wget among other extractors; HTTrack is the GUI-era equivalent (see section C).

### curl_cffi (Python, MIT, 6k stars, last push 2026-09-20, not archived, latest release v0.16.4b1 2026-09-20 which is a beta; PyPI stable 0.16.3)
- **What it is:** Python bindings (cffi) to the lexiforest fork of curl-impersonate, a libcurl build on BoringSSL that reproduces Chrome, Safari, Firefox and Edge TLS and HTTP/2 handshakes; `requests`-like `Session` and asyncio `AsyncSession`.
- **Best at:** passing fingerprint checks with almost no code change: `impersonate="chrome"` selects the newest Chrome profile the installed version knows. It also does HTTP/2, HTTP/3 with fingerprints, WebSockets and native retries (README table), and takes custom `ja3=` and `akamai=` strings.
- **Limits and traps:** profiles age with the installed version, so an old install impersonates an old browser, which can itself look odd; `curl-cffi update` (README, since 0.15.1) fetches newer fingerprints. It fixes the handshake, not the behaviour: no JavaScript, no sub-resource loads, and a passed fingerprint says nothing about rate limits or app-level checks. The README's sponsor section advertises services for solving Cloudflare, Akamai, DataDome and Kasada challenges; those are outside this skill's line, the library is not.
- **Cost or risk:** low. MIT, very active, but a small maintainer group with a commercial arm (impersonate.pro) selling extra fingerprints; the free set covers Chrome, Safari and Firefox (README).
- **Reach for it when / not when:** first choice when plain requests gets 403 or a reset and a browser does not. Not when the page is built by JavaScript (use the API behind it, or a browser).
- **Versus:** primp and wreq are Rust alternatives with similar profiles; hrequests is unmaintained; tls-client is the Go option.
- **Here:** 0.11.1 installed. On that version `http_version="v3"` raised a TypeError (measured), consistent with the README's HTTP/3 start at 0.11.4; HTTP/2 worked (it reported curl's code 3, which is HTTP/2); `AsyncSession` ran three concurrent requests under Windows's default ProactorEventLoop without a warning (measured, local server). Scrapling's `fetchers` extra wants curl_cffi >= 0.16.1, so install it in its own virtual environment.

### curl-impersonate, lexiforest fork (Shell and C, MIT, 2k stars, last push 2026-09-16, not archived, latest v2.2.3 2026-09-16)
- **What it is:** curl patched and rebuilt against BoringSSL, with HTTP/2 settings and TLS options set to match named browser versions; ships as a command-line tool (wrapper scripts such as `curl_chrome146`) and as a library.
- **Best at:** replaying a request from a shell or from any language with libcurl bindings using a browser handshake; the README lists ECH, zstd, post-quantum key shares (X25519Kyber768 and X25519MLKEM), HTTP/3 fingerprints and Windows, Arm and RISC-V builds. It is the engine under curl_cffi.
- **Limits and traps:** one binary per release; profiles run from Chrome 99 to Chrome 150, Safari 15.3 to 18 and Firefox, but I did not verify that every listed profile is current; the README's own header says "current stable 2.0.0" while the release list shows v2.2.3, so the README lags. Fingerprint only, no JavaScript.
- **Cost or risk:** low. Note this is a fork; the original (lwthiker) is the older, less maintained line.
- **Reach for it when / not when:** for shell-level checks ("does a Chrome handshake get through?") or non-Python stacks. Not when you are in Python already: use curl_cffi.
- **Versus:** curl_cffi is the same engine with a Python API.

### tls-client (Go, BSD-4-Clause per the table, 1k stars, last push 2026-09-04, not archived, latest v1.16.0 2026-09-02)
- **What it is:** a Go `net/http`-style client built on Carcraftz's `fhttp` and `utls` forks, with named browser profiles, HTTP/1.1, HTTP/2 and HTTP/3 (README), custom header order, cookie jar, proxies and WebSockets; also usable from Python, Node and C# through a shared library (README).
- **Best at:** Go programs that need a browser handshake and header-order control, and cross-language use through its FFI layer.
- **Limits and traps:** the PyPI package named `tls-client` is a separate wrapper by a different author, last uploaded Feb 2024, so treat it as stale; check which wrapper you are importing. The FFI shared library is a native binary you fetch and trust. The BSD-4-Clause licence is unusual (advertising clause); confirm against the LICENSE file (unverified).
- **Cost or risk:** moderate: native binary supply chain, wrapper churn.
- **Reach for it when / not when:** when the codebase is Go. Otherwise curl_cffi is simpler and better maintained in Python.
- **Versus:** curl_cffi (BoringSSL curl) and utls-based clients differ in TLS stack: utls imitates the ClientHello inside Go's TLS, curl_cffi uses the browser's own library family.

### hrequests (Python over a Go backend, MIT, 1k stars, last push 2024-12-01, not archived, latest v0.9.2 2024-12-01)
- **What it is:** a `requests`-shaped client whose HTTP engine is a Go binary with browser TLS profiles, plus BrowserForge header generation, a fast HTML parser, and a browser mode driving Camoufox or Patchright (README).
- **Best at:** in its day, one library for HTTP fingerprints and browser fallback.
- **Limits and traps:** no commit in about 21 months as of 21 Sep 2026, so its browser profiles are old. PyPI shows only a pure-Python wheel and an sdist, so on Windows the Go binary is downloaded by `python -m hrequests install` at setup. The README carries an advertisement for a residential-proxy vendor.
- **Cost or risk:** high: unmaintained, native binary fetched at install.
- **Reach for it when / not when:** not for new work. Use curl_cffi.
- **Versus:** curl_cffi and primp are maintained equivalents.

### wreq, formerly rnet (Rust with Python bindings, Apache-2.0, 1k stars, last push 2026-09-18, not archived, latest v0.12.2 2026-09-16; table row is for 0x676e67/rnet, which the GitHub API now reports as wreq-python)
- **What it is:** a Rust HTTP client on BoringSSL with per-request control of TLS, JA3/JA4 and HTTP/2 settings and 100+ browser "emulation" profiles (README); Python bindings with `Client` in async and blocking forms, cookie store, redirect policy, rotating proxies, WebSocket upgrade. Install with `pip install wreq` (Python >= 3.11).
- **Best at:** fine-grained protocol control; README states it runs faster than requests, httpx, aiohttp and curl_cffi on its own benchmark, "for reference only" (author-reported; I did not run it).
- **Limits and traps:** the rename is the trap: `pip install rnet` gets a stale package. Python >= 3.11 excludes older environments. The README does not mention HTTP/3. A solo maintainer offers paid support.
- **Cost or risk:** moderate: single maintainer, fast-moving API (0.x).
- **Reach for it when / not when:** when you want a Rust-speed alternative to curl_cffi or need a profile curl_cffi lacks. Not as a first choice: curl_cffi has more users and docs.
- **Versus:** primp is similar in idea; curl_cffi rides libcurl rather than a Rust stack.

### primp (Rust with Python bindings, MIT, 604 stars, last push 2026-09-13, not archived, latest v2.0.1 2026-09-12)
- **What it is:** a Rust HTTP client that impersonates Chrome (144 to 153), Safari, Edge, Firefox and Opera profiles, selectable by OS (README); Python `Client` and `AsyncClient`. `pip install primp`, Python >= 3.10, Windows wheels on PyPI.
- **Best at:** small install, quick start, profile names that map to real versions.
- **Limits and traps:** the README I read does not state HTTP/3 support; its own disclaimer says "educational purposes only, use at your own risk"; smaller community than curl_cffi.
- **Cost or risk:** low to moderate; MIT and active, a small maintainer group.
- **Reach for it when / not when:** as a second impersonating client if curl_cffi lacks a needed profile or misbehaves. Not needed otherwise.
- **Versus:** curl_cffi has more users and HTTP/3 documented; wreq exposes more low-level control.

### utls (Go, BSD-3-Clause, 2k stars, last push 2026-08-02, not archived, latest v1.8.2 2026-01-13)
- **What it is:** a fork of Go's `crypto/tls` that lets you write or copy the ClientHello (parroting a browser, or randomising it); the handshake itself is still Go's, and the README states "there is no parroting beyond ClientHello".
- **Best at:** the layer several Go clients build on (tls-client uses a utls fork, README). Built for anti-censorship, so its README talks about resisting blocklists.
- **Limits and traps:** it does not do HTTP/2 settings or header order: the caller must supply an HTTP layer that does (which is why tls-client also forks `net/http`). Parroting can be imperfect and lag new browsers (README warns about compatibility risks).
- **Cost or risk:** low; a library for Go developers.
- **Reach for it when / not when:** only when writing Go network code. You will meet it as a dependency, not as a tool.
- **Versus:** curl-impersonate matches the browser's TLS library family; utls imitates from within Go's.

### got (TypeScript for Node, MIT, 14k stars, last push 2026-09-20, not archived, latest v16.0.0 2026-08-30)
- **What it is:** a promise-based Node client with retries, hooks, streams, pagination helpers, cookie jar and HTTP/2 support (README lists HTTP/2).
- **Best at:** ergonomics for Node scrapers and API clients: retry policy, hooks and stream handling built in.
- **Limits and traps:** ESM only, no CommonJS export (README warning). Node's TLS is OpenSSL, so the ClientHello is Node's and not a browser's (the httptoolkit article cited in tls-client's README describes this). Apify's `got-scraping` layer adds browser-like headers and TLS (unverified).
- **Cost or risk:** low; one maintainer, very active.
- **Reach for it when / not when:** Node projects hitting cooperative APIs. Not for fingerprint-sensitive sites, where `impers` (lexiforest's Node binding to curl-impersonate, named in curl_cffi's README) or Apify's `impit` (Apache-2.0, 593 stars, pushed 2026-09-21, read from GitHub, not in the table) are the routes; I did not test either.
- **Versus:** undici is lower-level and faster; axios is more widely known but browser-first.

### undici (JavaScript for Node, MIT, 7k stars, last push 2026-09-21, not archived, latest v8.10.2 2026-09-04)
- **What it is:** the HTTP client written for Node.js itself; the built-in `fetch()` is powered by a bundled undici (README). Offers `request`, `stream`, `pipeline`, pooling, HTTP/1.1 pipelining, `ProxyAgent`, `MockAgent`, and opt-in HTTP/2 (`allowH2` in the Client docs).
- **Best at:** throughput and control; its README benchmarks (author-reported) show it ahead of node-fetch and axios-style clients.
- **Limits and traps:** built-in `fetch` lacks `ProxyAgent` and other APIs, so proxies need the installed module (README). No browser handshake.
- **Cost or risk:** low; maintained by the Node project.
- **Reach for it when / not when:** high-volume Node fetching or when you want `fetch` semantics with proxy support. Not for fingerprints.
- **Versus:** got gives friendlier retries and hooks; axios has interceptors.

### axios (JavaScript, MIT, 109k stars, last push 2026-09-16, not archived, latest v1.20.0 2026-08-24)
- **What it is:** promise client for browser and Node with interceptors and pluggable adapters (`xhr`, `http`, `fetch`), plus experimental HTTP/2 in the Node `http` adapter (README).
- **Best at:** familiarity and interceptors for API calls in front-end and Node code.
- **Limits and traps:** the HTTP/2 note in its README says behaviour differs by runtime and Node version; `httpVersion` and `http2Options` are adapter-specific. Node's OpenSSL ClientHello applies. The star count comes from front-end use, not scraping quality.
- **Cost or risk:** low; but axios sits on the npm supply-chain path that gets attacked, so pin versions and lock files (unverified as a specific incident).
- **Reach for it when / not when:** if a codebase already uses it. Not chosen for scraping.
- **Versus:** got and undici are the better Node scraping bases.

---

## B. Proxies and identity

Everything in this section is background from my own knowledge (unverified) except our measurements and line. It is about understanding, not about getting past a block.

### B1. Kinds of proxy

- **Datacentre.** IPs from hosting providers. Cheap, fast, stable, and identifiable as hosting by ASN. Sold per IP per month or in bulk lists.
- **Residential.** IPs of real home connections, leased through provider networks. Look like ordinary users, cost per gigabyte, slower and less stable. How the provider obtained the peers' consent varies and is a reputational and legal question to ask about.
- **Mobile.** IPs from carrier networks, usually behind carrier-grade NAT so many real users share each address; a site is reluctant to block them. Most expensive; often per port or per GB.
- **ISP (static residential).** Datacentre-hosted machines announced under a consumer ISP's ASN: residential reputation with datacentre speed, fixed address, per-IP pricing.
- **Rotating versus sticky.** A rotating gateway hands out a different exit IP per request (or per short interval); a sticky session holds one exit for minutes or hours via a session token in the credentials. Flows that bind to an IP (a session, a cart, pagination with server-side state) need sticky; independent single-page fetches work either way.
- **Protocols.** HTTP CONNECT and SOCKS5 are the two; with SOCKS, whether DNS resolves locally or at the proxy matters (`socks5h` style). curl_cffi accepts both http and socks proxies (README). `requests` needs its SOCKS extra (unverified).
- **Pricing models.** Per GB (residential, mobile: page weight matters, so a browser that loads images and scripts costs far more than an HTML fetch), per IP per month (datacentre, ISP), per port (mobile), or per successful request (scraping APIs, which bundle proxy, retries and sometimes rendering). One vendor advertises residential from $0.49/GB in a README banner (author-reported advertisement; check current pricing).

### B2. How IP reputation works, and why two datacentre IPs behave differently

- **Sources.** Commercial IP-intelligence feeds classify an address by ASN (hosting, ISP, mobile, education), by known proxy or VPN exit lists (found by scanning, by provider disclosure and by observed abuse), and by abuse history; CDNs also keep their own telemetry across all their customers, so an IP that misbehaved on one site can carry a score on many. Scores often apply to a whole /24 or a provider's range, and they decay with time.
- **Why some datacentre IPs pass and others do not.** The site's policy (many sites never check the hosting flag at all, some only score it), the specific history of that address, the reputation of its neighbours in the range, whether it is shared by many customers of the proxy vendor, and whether it sits on a list of known proxy exits. Two IPs in the same range can therefore differ.
- **Our measurement, as given to me:** of 100 datacentre proxies tested, 57 were dead, and of 56 (as briefed, I do not have the denominator's definition) 31 were ok. "Dead" (no working connection) and "flagged" (works, then blocked) are different failures, and the high dead rate is what a list of cheap or free proxies would be expected to show (an inference, unverified). The lesson is that a proxy list has to be tested before it is trusted and retested regularly, and that "ok" has to mean a real response from the real target.

### B3. Testing a proxy: one request each

- Send one request through the proxy to an IP-echo endpoint and record connect success, the exit IP and country, latency, and whether headers such as `Via` or `X-Forwarded-For` reveal the client.
- Send one request to the actual target and judge by content (a marker string or a parsed field), not just status 200, since a block page can be a 200.
- Classify: dead (refused, timeout, 407), alive but blocked (403, 429, challenge page), ok (real content). Do not loop retries at the target through every proxy: a test that hammers the target is a load test.
- Never send credentials or personal data through a proxy you do not control; for plain HTTP the proxy can read everything, and for HTTPS a proxy that asks you to trust its certificate can too.

### B4. What a proxy cannot fix

- **The TLS and HTTP/2 fingerprint.** Measured here: a used-car listing site blocked plain `requests` through clean proxies (0 of 12) and let `curl_cffi` through (8 of 8). The IP was never the problem.
- **Application-level limits.** A cap keyed to an API key, an account, a cookie or a session id is unaffected by the exit IP; so is a limit enforced by the site's own logic. It only changes the address, not who you appear to be to the application.
- **Behaviour and rendering.** Missing sub-resources, no JavaScript, robotic timing and header order are all still yours.
- **Costs.** Latency, another failure point, per-GB bills, and, for residential networks, an ethics and provenance question.

### B5. Our line

Public data only. Using a proxy as plain infrastructure (a fixed exit, a server in a chosen country, a vantage point to see what a visitor there sees) is an operational choice. Rotating proxies or identities to get past a block is not permitted. My reading, to confirm with whoever sets the policy: a geographic restriction or hosting-range block that a fixed, single exit resolves is a grey area to raise, not to decide alone. If the fix for a 403 is more IPs, stop, apply the diagnosis ladder (TLS fingerprint, headers, API endpoint, slower pace), and report the block if it remains.

---

## C. Crawl frameworks

### Scrapy (Python, BSD-3-Clause, 64k stars, last push 2026-09-21, not archived, latest 2.19.0 2026-09-10)
- **What it is:** an event-driven crawl framework on Twisted. The Engine drives everything: the Scheduler (priority queue plus a duplicate filter on request fingerprints) hands requests to the Downloader; downloader middlewares sit between them (retry, redirect, cookies, robots.txt, user agent, HTTP cache, proxies); the response goes to your Spider; items go through Item Pipelines; spider middlewares sit on the spider side (architecture docs). Feed exports write JSON, JSONL, CSV or XML to local disk, S3 and other targets.
- **Best at:** scale and discipline: per-domain concurrency and delay slots (`CONCURRENT_REQUESTS` default 16), AutoThrottle (off by default; it sets the delay from measured latency, targeting a concurrency), `JOBDIR` pause and resume, request dedup, retries, stats, and one place for each concern. The extension ecosystem is the largest of any Python crawler.
- **Limits and traps:** Windows: Python's default loop on Windows is Proactor but Twisted's asyncio reactor needs the selector loop, and Scrapy sets `WindowsSelectorEventLoopPolicy` itself (source of `scrapy/utils/reactor.py`); installing with pip may need Microsoft C++ Build Tools, and the docs recommend conda-forge (install docs). For Arabic output: `FEED_EXPORT_ENCODING` defaults to utf-8 in current docs but falls back to `None` (escaped `\uXXXX` JSON) when a project has no settings, so set it explicitly. Its default HTTP stack uses pyOpenSSL, so its handshake is not a browser's. Docs for 2.19 show `DOWNLOAD_DELAY` and `ROBOTSTXT_OBEY` defaults that differ between a generated project and a bare run (fallback values 0 and False); read the docs for your installed version. No JavaScript.
- **Cost or risk:** none in licence; the risk is a Twisted learning curve and API churn: 2.14 dropped Python 3.9 and documented the custom download handler API, 2.15 added an experimental reactorless mode, 2.18 made the Twisted HTTP/2 handler non-experimental, 2.19 added an aiohttp-based handler (reactorless default), a `RemoteControl` extension and a Scrapy MCP server (release notes).
- **Reach for it when / not when:** many pages, many sites, recurring crawls, need for polite pacing and clean pipelines. Not for a handful of URLs or a single JSON API: a script with curl_cffi is shorter.
- **Versus:** Crawlee is async-first with built-in browser crawlers; Scrapling and colly are lighter; Scrapy's advantage is maturity and extensions.
- **Here:** Scrapy 2.12.0 installed, seven minor versions behind, so none of the 2.15 to 2.19 features above exist locally; upgrade before relying on them. The current docs say new projects have the asyncio reactor configured by default; check `TWISTED_REACTOR` in your project settings, since scrapy-playwright and scrapy-impersonate both require it.

### scrapy-playwright (Python, BSD-3-Clause, 1k stars, last push 2026-09-07, not archived, latest v0.0.48 2026-07-10)
- **What it is:** a Scrapy download handler that fetches marked requests through Playwright and returns the rendered page; unmarked requests use the normal handler.
- **Best at:** adding JavaScript rendering to an existing Scrapy crawl without changing scheduling or pipelines; supports persistent contexts, CDP and remote browsers, and a pluggable browser provider (patchright and camoufox are named as examples).
- **Limits and traps:** needs the asyncio reactor. On Windows Playwright runs in a ProactorEventLoop in a separate thread because Twisted needs the selector loop and Playwright needs subprocess support (README); this works but adds moving parts. Pages, contexts and memory are your responsibility (close pages you open).
- **Cost or risk:** CPU and RAM per browser context; still 0.0.x versioning.
- **Reach for it when / not when:** when a few sites need rendering inside a Scrapy project. Not when you can call the JSON API the page uses.
- **Versus:** scrapy-splash is dormant; Crawlee's PlaywrightCrawler is the framework-native alternative.
- **Here:** 0.0.46 installed with Playwright 1.60.0 and playwright-stealth 2.0.3; latest is 0.0.48.

### scrapy-impersonate (Python, MIT, 242 stars, last push 2026-08-27, not archived, latest 1.9.0 2026-08-27)
- **What it is:** a Scrapy download handler that fetches through curl_cffi when a request sets `meta["impersonate"]`; includes a `RandomBrowserMiddleware` that varies the profile (README).
- **Best at:** giving a Scrapy crawl a browser handshake without leaving Scrapy.
- **Limits and traps:** requires the asyncio reactor; set `USER_AGENT` to an empty value so curl_cffi picks a matching one (README). Random browser rotation per request produces an inconsistent identity within one session; pin one profile per crawl. Small project (242 stars).
- **Cost or risk:** small maintainer base; its pace tracks curl_cffi.
- **Reach for it when / not when:** a large Scrapy crawl of a fingerprint-checking site. Not when a script suffices.
- **Versus:** calling curl_cffi inside a spider callback blocks the reactor unless done carefully; the handler does it properly.
- **Here:** not installed on purpose.

### scrapyd (Python, BSD-3-Clause, 3k stars, last push 2026-09-21, not archived, table release 1.4.1 2023-02-10; PyPI shows 1.5.0 Oct 2024 and 1.6.0 Jul 2025, so the table's release column is stale for this repo)
- **What it is:** a daemon with a JSON API to upload Scrapy projects as eggs and schedule, list, cancel and log spider runs (README).
- **Best at:** running Scrapy spiders as scheduled jobs on a server with one web endpoint and per-job logs.
- **Limits and traps:** no built-in scheduling (call the API from cron or a scheduler); minimal UI; deployment through eggs is a dated pattern. On Windows it should run but I did not check (unverified).
- **Cost or risk:** low; slow but alive.
- **Reach for it when / not when:** a dedicated always-on crawl server with many spiders. Not for a few jobs that a systemd timer or cron line can run.
- **Versus:** plain cron plus `scrapy crawl` does the same for small setups.

### spidermon (Python, BSD-3-Clause, 562 stars, last push 2026-09-09, not archived, table release 1.24.0 2025-04-11; PyPI shows 1.27.0)
- **What it is:** a Scrapy extension that runs monitors at spider close: assertions over crawl statistics (item counts, error counts, coverage of fields), item validation against schemas, and notifications (README: data validation, stats monitoring, notification messages).
- **Best at:** turning "the run finished" into "the run finished with the right amount of the right data", which is the silent-failure defence for scheduled crawls.
- **Limits and traps:** it tells you a stat is off, not why; thresholds need tuning per site; notification back-ends need configuration (Slack, email and others, unverified in detail).
- **Cost or risk:** low; slower cadence than Scrapy.
- **Reach for it when / not when:** any recurring Scrapy crawl. Not for one-off runs.
- **Versus:** hand-written checks in an item pipeline or a post-run script achieve the same with more effort and less structure.

### scrapy-redis (Python, MIT, 5k stars, last push 2026-09-17, not archived, latest v0.9.1 2024-07-06)
- **What it is:** replaces Scrapy's scheduler, duplicate filter and pipeline with Redis-backed ones so many spider processes share one request queue and one seen-set; items can be pushed to Redis for separate post-processing (README).
- **Best at:** distributing one broad crawl across several machines.
- **Limits and traps:** you now operate Redis, and a crashed worker can leave requests in limbo; Redis is not officially a Windows product (unverified). The last tagged release is two years old though commits continue.
- **Cost or risk:** operational overhead more than money.
- **Reach for it when / not when:** a crawl too large for one server, or many workers on many hosts. Not on one laptop plus one server, where `JOBDIR` and a single process go far.
- **Versus:** Scrapy's own single-process scheduler with `JOBDIR`.

### scrapy-splash (Python, BSD-3-Clause, 3k stars, last push 2025-02-11, not archived, table release 0.10.0 2025-01-21; PyPI shows 0.11.1 on 2025-02-11)
- **What it is:** integration for Splash, a JavaScript-rendering HTTP service built on Twisted and Qt5 (Splash README).
- **Best at:** was the standard way to render pages from Scrapy before Playwright.
- **Limits and traps:** dormant. No commits since Feb 2025; the Splash repo itself was last pushed 2024-08-02 and has no GitHub releases. Its Qt WebKit engine is older than current Chrome, so modern sites can fail to render (unverified).
- **Cost or risk:** high: unmaintained rendering engine and a service to run.
- **Reach for it when / not when:** never for new work; use scrapy-playwright.
- **Versus:** scrapy-playwright drives a current Chromium.

### Crawlee for Python (Python, Apache-2.0, 9k stars, last push 2026-09-21, not archived, latest v1.10.1 2026-09-16)
- **What it is:** an asyncio crawling library from Apify with crawler classes for HTML (BeautifulSoup, Parsel), for Playwright, and an adaptive crawler (extras verified on PyPI), a persistent request queue, autoscaled concurrency, session and proxy rotation helpers, and datasets written to `./storage`.
- **Best at:** one interface across HTTP and browser crawling, with a pluggable HTTP client: the default is `ImpitHttpClient` (Apify's Rust impersonating client; README), with `httpx` and `curl-impersonate` extras.
- **Limits and traps:** Python >= 3.10. Younger ecosystem than Scrapy; fewer ready extensions; features tuned for the Apify platform. It runs on asyncio with no Twisted, so Playwright and the crawler share a normal event loop (unverified on Windows, but simpler than the Scrapy path). The README's "fly under the radar of modern bot protections" is a marketing claim; the mechanism is default headers and a browser-like handshake, not a guarantee.
- **Cost or risk:** low; Apache-2.0, corporate-backed.
- **Reach for it when / not when:** a new asyncio project that wants queue, concurrency and browser fallback in one package. Not when you are already productive in Scrapy.
- **Versus:** Scrapy has the extension ecosystem and feed exports; Crawlee has friendlier browser handling.

### Crawlee for JS (TypeScript, Apache-2.0, 25k stars, last push 2026-09-21, not archived, latest v3.18.1 2026-08-12)
- **What it is:** the original: HTTP crawlers (Cheerio-based `http-crawler`), Playwright and Puppeteer crawlers, persistent queue, autoscaling, proxy and session management, `npx crawlee create` templates. The HTTP layer is a pluggable `@crawlee/http-client` with an optional impit client (package manifests); I did not determine which is the default.
- **Best at:** Node teams that want crawling plus browser control in one framework.
- **Limits and traps:** the README says Node 16 or higher, but the repo's own manifest pins Node 24, so check the package `engines` before installing; the Python and JS versions differ in details and version numbers.
- **Cost or risk:** low.
- **Reach for it when / not when:** if we is JavaScript. Our tooling is Python, so not otherwise.
- **Versus:** Scrapy for Python; colly for Go.

### colly (Go, Apache-2.0, 25k stars, last push 2026-09-16, not archived, latest v2.2.0 2025-03-27)
- **What it is:** a callback-style Go scraping framework: `OnHTML(selector, fn)`, `OnRequest`, `OnResponse`, with goquery selectors, per-domain delay and concurrency limits, cookie handling, on-disk cache, robots.txt support and Redis or other storage extensions for distributed runs (README feature list; the README claims over 1,000 requests per second on a single core, author-reported).
- **Best at:** small, fast, single-binary crawlers on a server, with low memory.
- **Limits and traps:** no JavaScript; Go's standard TLS gives a non-browser handshake (plug in a utls-based transport if needed); go.mod requires Go 1.24, the last release is 18 months old though commits continue. The README carries proxy-vendor sponsor banners.
- **Cost or risk:** low.
- **Reach for it when / not when:** if you are writing Go. Not in a Python shop.
- **Versus:** Scrapy is the Python analogue with more features; Katana is a Go crawler for URL discovery, not extraction.

### Katana (Go, MIT, 17k stars, last push 2026-09-14, not archived, latest v1.7.0 2026-08-05)
- **What it is:** a ProjectDiscovery command-line crawler for mapping a site's URLs and endpoints, with standard and headless modes, JavaScript parsing, scope controls, automatic form filling and an ML page-type classifier (README).
- **Best at:** discovering the URL space of a site fast, including endpoints referenced only inside JavaScript, when there is no sitemap; output as URLs or JSON lines.
- **Limits and traps:** built as a security-recon tool; its default posture and form-filling feature are aimed at attack-surface mapping, so it belongs only on public sites you are entitled to crawl, and form filling on a login is outside this skill's line. It lists URLs and does not extract fields. Building needs a very recent Go (README says 1.26+); prebuilt binaries exist.
- **Cost or risk:** low; set a rate limit and depth explicitly (the flags exist; check `-help`).
- **Reach for it when / not when:** to enumerate URLs of a site before writing the extractor. Not to collect data.
- **Versus:** a sitemap or the site's own API is cheaper; colly and Scrapy extract as they crawl.

### Scrapling (Python, BSD-3-Clause, 82k stars, last push 2026-09-19, not archived, latest v0.4.15 2026-08-23)
- **What it is:** three things in one package: an HTML parser that can save an element's fingerprint and relocate it after a redesign ("adaptive" selection), fetchers (`Fetcher` on curl_cffi with impersonation and HTTP/3; `DynamicFetcher` on Playwright; `StealthyFetcher` on patchright with spoofed fingerprints and an option to solve Cloudflare's challenge), and a Scrapy-like `Spider` class with pause and resume, per-domain autothrottle, blocked-request retry, robots.txt option and proxy rotation. PyPI: the `fetchers` extra pulls curl_cffi, playwright, patchright and browserforge.
- **Best at:** getting parser, HTTP client, browser fallback and a small crawler from one install; the `Fetcher` with `impersonate` is a tidy curl_cffi wrapper, and `capture_xhr` records the API calls a page makes.
- **Limits and traps:** version 0.4.x, pre-1.0. Adaptive relocation can quietly return a similar but wrong element after a redesign, so assert on the extracted values. `StealthyFetcher` and `solve_cloudflare` are the features this skill does not use: defeating anti-bot challenges is outside its line. The README is largely sponsor banners for proxy and unblocking vendors; the star count reflects that promotion as well as merit (an inference).
- **Cost or risk:** moderate: young API, a heavy dependency set, and on the laptop a clash with the installed curl_cffi 0.11.1 and Playwright 1.60.0 (the extra wants >= 0.16.1 and >= 1.62).
- **Reach for it when / not when:** for a mid-size extraction that wants impersonated HTTP plus a parser in one small package, in its own virtual environment. Not for a large recurring crawl (Scrapy's ecosystem is safer), and not for its stealth or challenge features.
- **Versus:** Scrapy is the mature choice; curl_cffi plus selectolax is the leaner one.
- **Here:** not installed.

### ArchiveBox (Python, MIT, 28k stars, last push 2026-09-21, not archived, latest stable v0.7.4 2026-05-18; a v0.9.31-rc pre-release exists)
- **What it is:** a self-hosted archive: for each URL it runs a set of extractors (wget mirror, SingleFile HTML, headless Chrome PDF, screenshot and DOM, WARC, yt-dlp media, readability text, git) and stores them as ordinary files with a SQLite index and a web UI (README).
- **Best at:** preserving evidence: a dated copy of a listing or article that may vanish, to cite in a report.
- **Limits and traps:** not a data extractor; storage heavy (several copies of every page). The stable 0.7.4 line declares `Requires-Python <3.12` on PyPI (so it will not pip-install on the laptop's Python 3.12.4), and the 0.9 line that the README pushes needs Python 3.13 via `uv` or Docker. The README lists supported systems as Ubuntu, macOS and Docker, not native Windows. Archiving with a logged-in browser profile is supported but the wiki warns about security; this skill does not crawl behind logins.
- **Cost or risk:** disk and upkeep; version state is in flux.
- **Reach for it when / not when:** long-term proof of what a page said on a date. Not to build a dataset.
- **Versus:** `wget --warc-file` captures one page to WARC with no UI; a browser "print to PDF" is the manual version.
- **Here:** not installed.

### wget and HTTrack style site mirroring (from knowledge, unverified; neither installed here)
- **What it is:** recursive downloaders that walk links from a start URL, save pages and assets, and rewrite links so the copy browses offline. wget: `-r`, `-l` depth, `-np` no parent, `-k` convert links, `-p` page requisites, `--wait`, `--warc-file`. HTTrack: the same idea with a GUI and project files.
- **Best at:** copying a small static site or an old HTML archive as-is, cheaply.
- **Limits and traps:** they store what the server sends; a page built by JavaScript arrives empty. No extraction step. Deep recursion can pull thousands of files; both are HTTP/1.1 with non-browser TLS.
- **Cost or risk:** politeness risk if unthrottled; HTTrack's release cadence is slow.
- **Reach for it when / not when:** to keep a static reference site. Not for anything dynamic, and not when you need parsed data.
- **Versus:** ArchiveBox runs a browser and wget together; Scrapy extracts data instead of copying files.

### Firecrawl (TypeScript, AGPL-3.0, 182k stars, last push 2026-09-21, not archived, latest v2.11.0 2026-06-19)
- **What it is:** a web-data API: `scrape` (URL to Markdown, HTML, screenshot or schema-shaped JSON), `crawl`, `map` (URL discovery), `search`, `batch scrape`, `interact` and `agent` endpoints (README). It is open source and also a paid hosted service (check current pricing). Behind a request there is a fetcher (plain fetch, Playwright, and in the cloud a proprietary engine named Fire-engine), an HTML-to-Markdown cleaner, and an optional LLM step for structured extraction.
- **Best at:** turning arbitrary URLs into clean Markdown for LLM pipelines with almost no code, with rendering handled for you and a single call for crawl plus scrape.
- **Limits and traps:** the README's "96% of the web" and latency figures are the vendor's own (unverified). Self-hosting per the repo's guide runs bundled Playwright with a basic fetch fallback, no model provider by default, and treats Fire-engine as a separate thing you connect, so the self-hosted product is not the same as the cloud one. The JSON extraction mode uses an LLM (cost, non-determinism; see the LLM note below). Using the cloud sends your target URLs and page content to a third party.
- **Cost or risk:** AGPL-3.0 is network copyleft: running it internally is common, but modifying it and offering it to others as a service creates source-sharing duties (confirm with counsel, unverified). The SDKs are MIT (PyPI `firecrawl-py`). Self-hosting means you own security and upgrades (its stack is API, workers, Playwright, Redis, RabbitMQ, PostgreSQL).
- **Reach for it when / not when:** feeding pages to a model or RAG index across many unfamiliar sites. Not for tabular extraction from one known site, where a parser is cheaper, exact and free per page.
- **Versus:** Crawl4AI is the local open-source equivalent; Scrapy plus trafilatura is the deterministic route.
- **Here:** not used.

### Crawl4AI (Python, Apache-2.0, 84k stars, last push 2026-09-18, not archived, latest v0.9.3 2026-08-31)
- **What it is:** an async crawler that always renders through a Playwright-driven browser, then cleans the DOM into Markdown (with heuristic and BM25 filters, citations, "fit" output) and offers extraction strategies: CSS or XPath schemas (no model), LLM-based extraction with your provider, and chunk-and-cosine selection. Includes deep-crawl (BFS and DFS), a browser pool, sessions, proxies and a Docker server with an API (README).
- **Best at:** local, free (no per-page fee) page-to-Markdown at moderate scale, plus a schema mode that is deterministic once written.
- **Limits and traps:** a browser per fetch costs seconds and memory, which is wasteful for static pages. Security has been the theme of recent releases: v0.9.3 closes five advisories (file write, SSRF and denial of service in the PDF path, two XSS in the Docker playground), v0.9.0 made the Docker server secure by default, and v0.8.7 fixed critical issues including remote code execution and an auth bypass (README). Do not expose the Docker API beyond loopback without the token. A hosted Cloud API is in closed beta per the README. I did not measure its Markdown against trafilatura, which is the extractor we measured (0.91 recall on Arabic).
- **Cost or risk:** LLM tokens only if you choose an LLM strategy; otherwise CPU. Fast-moving 0.9.x releases and patch-level security fixes mean pinning and reading release notes.
- **Reach for it when / not when:** to build a Markdown corpus from JavaScript-heavy sites or to prototype extraction. Not for high-volume static pages (a plain fetch plus trafilatura is far lighter).
- **Versus:** Firecrawl is hosted and AGPL; ScrapeGraphAI pushes everything through an LLM; Scrapling is a parser and fetcher set, not a Markdown pipeline.
- **Here:** not installed.

### ScrapeGraphAI (Python, MIT, 31k stars, last push 2026-09-07, not archived, latest v2.2.4 2026-09-07)
- **What it is:** a library that builds a small pipeline (a graph of nodes) per task: fetch the page with a headless browser (Playwright), parse and chunk the content to fit a model's context, send each chunk with your prompt to an LLM (OpenAI, Ollama, others) and merge the answers into JSON. Variants handle one page, several pages, or a search first (README). The PyPI package `scrapegraph-py` is a different thing: an SDK for the vendor's hosted API. Needs Python >= 3.12 (PyPI).
- **Best at:** getting structured answers from pages you have not studied, in plain language ("list the founders and links"), with no selectors.
- **Limits and traps:** what the model does is read the page text and produce a JSON answer, so the output can omit, invent or normalise values without any signal; the same page can yield different output on another run. Every page costs tokens roughly in proportion to its cleaned length; Arabic generally costs more tokens per word (unverified). Hidden or hostile text on a page can be read by the model as instructions (a general prompt-injection risk with any LLM extractor; not tested in this tool). Data goes to whichever provider you configure.
- **Cost or risk:** cost is pages x tokens per page x the model's price (check current pricing); a local Ollama model removes the fee but not the errors, and small local models are weaker at Arabic (unverified). The README steers readers to the hosted service.
- **Reach for it when / not when:** a one-off pull of a few facts from prose-heavy or one-of-a-kind pages, or quick prototyping. Not for recurring crawls of one template (write selectors once), not for exact values like prices, phone numbers or ids, and not at thousands of pages.
- **Versus:** Crawl4AI's schema mode and a parsel or selectolax extractor are deterministic and free per page.
- **Here:** not installed.

### What the LLM-era crawlers actually do, and when they beat a parser
The mechanism is the same in all three: fetch (often with a browser), strip the page to text or Markdown, then optionally ask an LLM to fill a schema. Only the last step is new. Everything before it is what trafilatura, a selectolax parse or Scrapy already do, and on our own test trafilatura recalled 0.91 of Arabic body text and 0.96 of English. So the value of these tools splits in two: the Markdown conversion is worth having and is deterministic; the LLM extraction is convenient and is not. The LLM step is probabilistic (two runs may differ), it costs tokens per page, it can fill a field with something plausible that the page does not say, and it hides a changed page layout instead of failing loudly. A plain parser fails loudly when the selector stops matching, which is what you want from a job that runs unattended.

A model wins when the page has no stable structure (free-text notices, varied registry entries, one-off documents), when there are few pages, or when it is used once to write the selectors that then run without it. A parser wins for any listing site with a repeating template, for volume, for exact identifiers, and whenever a JSON API sits behind the page. If an LLM extractor is used, keep the loop honest: check that each extracted value literally appears in the source text, keep the raw page, and sample outputs by hand.

---

## How to choose

### A. HTTP clients

Start with the cheapest thing that answers and let evidence move you up. Fetch one URL with curl or `requests` and read what came back: a 200 with the real content means you are done, and the question is only concurrency. If you get a 403, a reset, or an empty or different page for a URL a browser loads fine, and the block lives at the handshake, `curl_cffi` with `impersonate="chrome"` is the next step; on a used-car listing site that took the same proxies from 0 of 12 to 8 of 8. The evidence that says "fingerprint" rather than "IP" or "JavaScript" is: same result through clean proxies, a browser succeeds from the same IP, and the response arrives instantly before any page logic. For async at scale, `httpx` (HTTP/2, friendly) or `aiohttp` (raw throughput) on cooperative targets, `AsyncSession` on fingerprint-sensitive ones. Treat `httpx` as usable but isolate it behind a function, given the maintenance gap and the httpx2 successor. Keep `primp` or `wreq` as second opinions if a profile misbehaves; skip `hrequests`, and treat tls-client and utls as Go-only. In Node, `undici` for speed, `got` for ergonomics, and impers or impit when the handshake matters. Before adding HTTP/3, note it needs a curl_cffi newer than the installed 0.11.1. Switch away from a client when the page content is built in the browser (then find the API, or use a browser tool from `browser-use`), or when the block persists with a matching handshake (then it is behaviour or an application limit, and the answer is to slow down or stop, not to add tooling).

### B. Proxies and identity

Ask first whether you need a proxy at all. Most public Iraqi sites respond to a normal client at a polite rate from your own IP or server, and the measured cases here were solved by the client (TLS) and not by the network. A proxy earns its place for a legitimate operational reason (a server in a particular country, a fixed egress) and then a plain, tested datacentre or ISP address is enough. If you do buy or borrow proxies, test each with one request to an echo endpoint and one to the real target, judge by content, and expect a large share of a cheap list to be dead (57 of 100 here). Residential and mobile cost per GB, so keep browsers off them or block heavy assets. The evidence that should make you stop and not add IPs: the block is unchanged across clean addresses, or the limit is tied to an account, key or cookie. Rotating to get past a block is outside this skill's line; report the block instead.

### C. Crawl frameworks

For a few URLs or one API, no framework: a `curl_cffi` script, `selectolax` or `parsel`, write to disk, and resume on a saved list of finished URLs. Move to Scrapy when the crawl is large, recurs, or spans sites and you need per-domain pacing, dedup, retries, stats and feed export; add `spidermon` for scheduled crawls, `scrapyd` or cron for running them, `scrapy-playwright` for the few sites that need rendering, and `scrapy-impersonate` only where the fingerprint blocks and the crawl is big enough to justify it (upgrade Scrapy from 2.12.0 first, since its handler API has been reworked). Choose Crawlee if you are starting fresh in asyncio and want browser and HTTP crawlers in one package; colly if we is Go; Katana to enumerate URLs of a site with no sitemap, then extract with something else; Scrapling for a mid-size job that wants parser plus impersonating fetcher in one install, never for its stealth features; `scrapy-splash` never; `scrapy-redis` only when one machine is not enough. Use ArchiveBox or `wget --warc-file` only when the deliverable is a preserved copy, not data. Reach for Firecrawl, Crawl4AI or ScrapeGraphAI when the goal is Markdown or answers from unfamiliar pages for a model, and even then use their Markdown step and a schema of selectors you write once, keeping the LLM extraction for the irregular pages and checking every value against the source. What should make you switch: a selector-based crawl that keeps breaking (consider a model for a fallback), an LLM crawl that costs more than the value of the data (write selectors), a browser crawl on static pages (drop the browser), or a block at the handshake (go back to section A).
