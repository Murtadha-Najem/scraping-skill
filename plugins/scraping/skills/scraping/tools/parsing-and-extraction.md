# Parsing, extraction, text and record matching

Status fields come from ghmeta.tsv (read from GitHub on 21 Sep 2026); stars there are rounded. Five tools are not in that table (BeautifulSoup, html5lib, pyquery, inscriptis, html2text); I read their status from GitHub, PyPI and crummy.com on the same day and say so in each entry.
Version numbers marked "PyPI" are the latest release on PyPI on 21 Sep 2026 and can differ from the GitHub release in the table.

How this file was checked. I ran small tests on the laptop (Python 3.12.4, Windows 11) and quote them as "tested". Packages I installed into a scratch folder for a test only: phonenumbers 9.0.39, price-parser 0.5.1, dateparser 1.4.3 (and 1.2.1, which was already present), pyarabic 0.6.15, readability-lxml 0.9, goose3 3.1.22, newspaper4k 0.9.6.
The text-extractor numbers reuse our own harness (135 pages of a law-firm site corpus, word-overlap recall and precision against the crawler's cleaned Markdown) and reproduce our trafilatura and jusText figures exactly, which is the reason I trust the extra rows. One site is one site: read them as "on this corpus".
`pip list` also showed dateparser 1.2.1, arabic-reshaper 3.0.0, python-bidi 0.6.3, RapidFuzz 3.10.0, html5lib 1.1, htmldate 1.10.0, jmespath 1.0.1, cssselect 1.2.0 and soupsieve 2.5 on the laptop. They are outside our stated install list (most are probably dependencies of something else), so no entry below treats them as chosen tools.
A line ending "(unverified)" comes from my own knowledge and I did not check it.

---

## A. HTML and XML parsers and selectors

### How the parsers differ on broken HTML (tested) and on encodings (tested)

Test input: `<div><p>one<p>two<b>bold<i>both</b>italic</i><table><tr><td>a<td>b</table><a href=x>link<div>inside</div></a><p>tail`
- html.parser (standard library, behind BeautifulSoup): repairs nothing. It leaves `<p>` inside `<p>` and `<td>` inside `<td>` and closes them all at the end, so a selector like `div > p` sees a different tree from the one a browser builds.
- lxml (libxml2's HTML parser, an HTML 4 era algorithm): closes `<p>` and `<td>` sensibly, does not insert `<tbody>`, leaves the `<div>` inside the `<a>`, and does not reopen the italic after a mis-nested `</b>`.
- html5lib, selectolax Lexbor and selectolax Modest: all three produced the same tree here, the one a browser builds by the HTML5 algorithm: `<tbody>` inserted, `<i>` reopened after `</b>`, `<a>` split around the `<div>`.
- Why it matters: a selector or XPath copied from browser DevTools describes the browser's tree. An XPath containing `/tbody/` finds nothing under lxml because lxml never inserts `tbody`. Use an HTML5 tree (Lexbor, html5lib) when copying from DevTools; use lxml when you write your own selectors and want speed and XPath.

Encodings, given the same Arabic sentence as bytes (tested):
- lxml `html.fromstring(bytes)`: honours `<meta charset>`, but with no declaration it assumes latin-1 and returns mojibake for UTF-8 Arabic, with no error.
- selectolax Lexbor given bytes: assumes UTF-8 and ignores a `<meta charset="windows-1256">`, returning replacement characters. Selectolax Modest given bytes honoured the meta tag.
- BeautifulSoup uses its own detector (UnicodeDammit); on a windows-1256 page with no meta tag it guessed a wrong Cyrillic-like decoding, again silently.
- lxml given a str that starts with an XML encoding declaration raises ValueError; given an empty string it raises ParserError. Selectolax returns an empty tree without raising, so an empty response becomes "field not found" instead of a crash.
- The safe rule: decide the encoding yourself (HTTP header charset, then meta tag, then a detector such as charset_normalizer), decode to str, save the raw bytes, and give the parser a str. Our own note says the same about `requests` guessing latin-1 when a text/html answer names no charset.

### CSS versus XPath (tested where marked)
- Only XPath can go up or sideways: `parent::`, `ancestor::`, `preceding-sibling::` (tested: `//h2[text()="Kia"]/parent::div/@class`). "Find the label, then take the value next to it" is an XPath sentence; in CSS you have no parent selector and only following siblings.
- Only XPath can filter on text and compute: `contains(text(),...)`, `count()`, `string-length()`, `normalize-space()`, and regex through the EXSLT `re:test()` that lxml and parsel expose (tested in parsel). It can also return attribute and text nodes directly.
- Only CSS gets class tokens right cheaply: `.a` matches class "a b" but not "ab"; the XPath `contains(@class,"a")` matched both (tested), and the correct XPath is the long `contains(concat(" ",normalize-space(@class)," ")," a ")`.
- CSS reads better for the common case. `:has()` worked in parsel, soupsieve, Lexbor and Modest and `:not()` in parsel (tested); the selectolax README also shows `:nth-child()` and `:not()` on Lexbor. Text matching in CSS is non-standard and differs per engine: `:contains()` in parsel, `:-soup-contains()` in soupsieve, `:lexbor-contains()` in Lexbor.
- XPath 1.0 (the only version lxml has) treats only space, tab, CR and LF as whitespace: `normalize-space()` left a non-breaking space (U+00A0) in place (tested). Prices and labels scraped from Arabic sites often carry NBSP, so normalise it in Python.
- Selectolax has no XPath at all (tested). Choose the engine by whether you need the gaps above, not by taste.

---

### BeautifulSoup 4 (Python, MIT, not on GitHub: hosted at crummy.com; PyPI 4.15.0 released 2026-06-07; not in the metadata table)
- **What it is:** a tree-navigation and search API on top of a pluggable parser: `html.parser`, `lxml`, `lxml-xml` or `html5lib`. CSS selection is done by the soupsieve library.
- **Best at:** forgiving, readable code for one-off jobs and for editing a tree (decompose, replace, wrap). The parser backend can be switched without changing your code.
- **Limits and traps:** the backend changes the tree (see the broken-HTML test above). If you do not name a parser it uses the best one installed, so the same script can build different trees on the laptop and the Ubuntu server when lxml is missing on one (unverified). Python-level `find_all` loops are slow. Encoding detection is a guess that fails silently.
- **Cost or risk:** slowest option here. MIT licence, actively released. No supply-chain concerns known to me.
- **Reach for it when / not when:** reach for it for a small page count, unusual markup or tree surgery; not for volume, where the parse time dominates.
- **Versus:** parsel and selectolax select faster; BeautifulSoup's edge is a tolerant API and tree editing, not speed, and it has no XPath.
- **Here:** 4.12.3 installed (PyPI is at 4.15.0). Measured: selectolax about 10x faster than BeautifulSoup with lxml on 158 pages (0.34 s against 3.36 s) with identical titles and link counts on all 158.

### lxml (table says Python; compiled bindings to libxml2 and libxslt in practice (unverified), BSD-3-Clause, 3k stars, last push 2026-09-10, not archived, latest release lxml-6.1.3-1 on 2026-09-02)
- **What it is:** the standard Python binding to libxml2 and libxslt: an HTML parser (`lxml.html`), an XML parser, XPath 1.0, XSLT, XML Schema, and `iterparse` for streaming large XML.
- **Best at:** XPath and XML. It is also the engine under parsel, BeautifulSoup's fast backend, trafilatura, readability-lxml, goose3, Scrapling and pyquery, so it is nearly always already in the environment.
- **Limits and traps:** HTML 4 era tree (no tbody, no adoption agency); bytes with no meta charset are read as latin-1 (tested); a str with an encoding declaration raises ValueError (tested); empty input raises ParserError (tested). The HTML sanitiser `lxml.html.clean` lives in the separate package `lxml-html-clean` since lxml 5.2 (unverified as to the exact version; the package exists on PyPI at 0.4.5), which is why some libraries list `lxml[html-clean]`.
- **Cost or risk:** wheels exist for Windows and Linux; keep it current because it wraps a C library that receives security fixes. BSD licence.
- **Reach for it when / not when:** reach for it when you need XPath, XML, streaming a big XML dump, or a dependency-light parser; not when you need the browser's exact tree or maximum speed on plain CSS.
- **Versus:** selectolax is faster for CSS but has no XPath; html5lib and Lexbor give the browser tree; parsel is lxml with a nicer selector API.
- **Here:** 6.1.3 installed (raised from 5.2.1 on 21 Sep for selectolax, jusText and trafilatura; Scrapy 2.12 and parsel still import and select).

### parsel (Python, BSD-3-Clause, 1k stars, last push 2026-09-21, not archived, latest release v1.11.0 on 2026-01-29; PyPI requires Python 3.10 or newer)
- **What it is:** Scrapy's selector library. It wraps lxml and gives one `Selector` object with CSS (translated to XPath by cssselect), XPath, JMESPath for JSON, and `.re()` for regular expressions.
- **Best at:** mixing CSS and XPath in one chain, and non-standard but handy pseudo-elements `::text` and `::attr(href)` (tested). It is Scrapy's own layer, so selector code moves between a script and a spider unchanged.
- **Limits and traps:** it is lxml underneath, so every lxml trap applies (HTML 4 tree, encoding guesses). CSS features are whatever cssselect can translate. `.get()` returns None on a miss instead of raising (unverified), which is how a silent empty column starts.
- **Cost or risk:** BSD licence, maintained by the Scrapy project. Speed is lxml speed: fast, but slower than a pure C CSS engine on selector-heavy pages.
- **Reach for it when / not when:** reach for it inside Scrapy, or when a field needs XPath (sibling or parent navigation) and CSS on the same page; not when all you do is CSS at volume, where selectolax is faster.
- **Versus:** selectolax has no XPath and a different API; BeautifulSoup is tolerant but slower; raw lxml has no CSS or `::text` helpers of its own.
- **Here:** 1.8.1 installed (the table's latest is 1.11.0).

### selectolax (Cython, MIT, 1k stars, last push 2026-09-18, not archived, latest release v0.4.12 on 2026-09-18)
- **What it is:** Python bindings to two C HTML5 parsers with CSS selectors. `selectolax.lexbor.LexborHTMLParser` uses Lexbor; `selectolax.parser.HTMLParser` uses Modest.
- **Best at:** speed and an HTML5-conformant tree in a small API (`css`, `css_first`, `.text()`, `.attributes`, `.parent`). Lexbor supports `:has`, `:not`, `:nth-child` and `:lexbor-contains()` for text (`:has` and `:lexbor-contains` tested, all four in the README). The README says Lexbor is the preferred backend since 2024 and that the C library under Modest "is not maintained anymore".
- **Limits and traps:** no XPath (tested). Bytes handling differs by backend (tested): Lexbor assumes UTF-8 and ignores the meta charset; Modest honoured it. An empty document returns an empty tree without raising (tested). Licences differ: selectolax is MIT, Lexbor Apache-2.0, Modest LGPL 2.1 (README). Building from source needs Cython on new Python versions; wheels install cleanly on Windows here.
- **Cost or risk:** MIT, actively released (a release on the day the table was read). The author reports 754 home pages in 2.39 s (Lexbor) and 2.94 s (Modest) against 9.09 s for BeautifulSoup with lxml and 61.02 s for BeautifulSoup with html.parser; treat that as the author's workload, not yours.
- **Reach for it when / not when:** reach for it for CSS extraction at volume; not when you need XPath or tree editing.
- **Versus:** parsel/lxml add XPath and are slower; BeautifulSoup is slower and more forgiving of API misuse, not of markup. Scrapling's README table shows selectolax about 99x slower than Scrapling on the workload it chose, which contradicts our own measurement of speed against BeautifulSoup; workloads differ, and we have not measured Scrapling.
- **Here:** 0.4.12 installed. Measured about 10x faster than BeautifulSoup with lxml on 158 pages, identical titles and link counts. The brief does not record which backend that run used.

### html5lib (Python, MIT, 1.2k stars, last push 2026-04-21, not archived; latest PyPI release 1.1 dated 2020-06-22; not in the metadata table, read from GitHub and PyPI)
- **What it is:** a pure-Python implementation of the HTML5 parsing algorithm, with tree builders for ElementTree, DOM and lxml. Used as a BeautifulSoup backend.
- **Best at:** producing the same tree a browser produces (tested: identical to Lexbor on the broken-HTML input).
- **Limits and traps:** pure Python, so the slowest backend; the last release is from 2020, though the repository still receives pushes.
- **Cost or risk:** MIT. Maintenance is thin, but the algorithm is a fixed specification.
- **Reach for it when / not when:** reach for it when you need the browser tree and are already in BeautifulSoup for a small job; not at volume, where Lexbor gives the same tree far faster.
- **Versus:** Lexbor/Modest are the same algorithm in C; lxml is a different (older) algorithm.

### pyquery (Python, licence field NOASSERTION on GitHub and BSD on PyPI, 2.4k stars, last push 2026-07-27, not archived; PyPI 2.1.0 released 2026-07-27; not in the metadata table)
- **What it is:** a jQuery-style chainable API (`d("div.card h2").text()`) over lxml and cssselect (both are its declared dependencies).
- **Best at:** familiarity for people who think in jQuery.
- **Limits and traps:** it is lxml, so the HTML 4 tree and the encoding traps apply; the licence field is ambiguous on GitHub, so read the PyPI classifier and the LICENSE file before bundling.
- **Cost or risk:** low; maintained.
- **Reach for it when / not when:** only if a team already writes jQuery selectors; otherwise parsel covers the same engine with more features.
- **Versus:** parsel (same engine, XPath and JMESPath, `::text`), selectolax (faster, different engine).

---

## B. Structured data inside pages, and JSON handling

### Reading a page's own data instead of its markup
The page often carries the record its template was drawn from, in a form more stable and more complete than the visible HTML. In rough order of how often it appears:
- JSON-LD: `<script type="application/ld+json">`, schema.org objects, often as one `@graph` array of several typed nodes (WebSite, Organization, Product, Article). Plain JSON, but some real pages ship trailing commas, comments or unescaped control characters (unverified), so wrap the parse and count failures.
- Next.js pages router: `<script id="__NEXT_DATA__" type="application/json">` holds plain JSON, with the page's data under `props.pageProps` (from memory, unverified).
- Next.js app router: there is no `__NEXT_DATA__`. Data is pushed as `self.__next_f.push([1,"..."])` calls (tested on a saved app-router page in the scratchpad: 44 calls, no `__NEXT_DATA__`). Each call carries a string chunk; concatenate all chunks first, because a row can be split across calls (chunks came in around 4,096 characters), then split on newlines. Rows look like `hexid:` plus a type letter or bracket (module references, arrays of React elements, text rows). This is React's internal streaming format, not a public API, so it can change without notice (undocumented, unverified beyond the sample). Find your record by locating a known key and decoding from the brace with `json.JSONDecoder().raw_decode`.
- Nuxt 3: `<script type="application/json" id="__NUXT_DATA__">`, serialised by the `devalue` library (read in Nuxt's source): a flat array whose entries refer to each other by index, so you must resolve the references before the data looks like records. The same payload is also served as a JSON file the client fetches (the `_payload.json` route name is from memory, unverified). Nuxt 2 used `window.__NUXT__=(function(a,b){return {...}}(...))`, a JavaScript expression and not JSON (unverified).
- Apollo/GraphQL sites: `window.__APOLLO_STATE__` (the name appears in Apollo's documentation), a normalised cache where objects are keyed like `Type:id` and link to each other with `{"__ref": "..."}` (unverified as to the exact shape). Redux-style `window.__INITIAL_STATE__` is similar (unverified).
- When the JSON beats the markup: it holds fields the template hides (ids, coordinates, ISO timestamps, unformatted numbers, phone numbers shown only after a click); it survives redesigns because it follows the data model, not the CSS; it is smaller and cheaper to parse. Our reader for a used-car site handles the old and the new format, old first, and a canary caught the 16 Sep 2026 change.
- When it does not: the blob may hold only the first page of a list; it may include neighbours (related cars, the brand, the city), so anchor on the exact id you hold, because an id also appears inside those (our lesson); values may be in different units or stale relative to what the user sees; and when the site fetches data after load, the blob is empty and the API call is the source.

### extruct (Python, BSD-3-Clause, 972 stars, last push 2026-04-01, not archived, no GitHub release; PyPI 0.18.0 released 2024-11-08)
- **What it is:** one call, `extruct.extract(html, base_url=...)`, that returns JSON-LD, microdata, OpenGraph, microformats (through mf2py), RDFa (experimental, through rdflib) and Dublin Core. `syntaxes=[...]` selects which and `uniform=True` flattens the shapes (README; RDFa is not uniformed).
- **Best at:** getting every metadata syntax in one pass with tested parsers, notably microdata, which is awkward by hand.
- **Limits and traps:** it only finds what the site publishes; many local Iraqi sites publish little beyond OpenGraph tags (unverified). Its dependencies (rdflib, pyrdfa3, mf2py, html-text, jstyleson) are heavier than the job when you only want JSON-LD. The last PyPI release is older than the repository's latest push, so the repository may hold fixes that pip does not.
- **Cost or risk:** BSD. Moderate maintenance signal.
- **Reach for it when / not when:** reach for it when you need microdata or several syntaxes; not when the only thing you want is JSON-LD, where ten lines of selector plus `json.loads` are lighter and easier to make tolerant.
- **Versus:** reading `__NEXT_DATA__` yourself gives the app's whole state, not just what it chose to annotate for search engines.

### jmespath (Python, MIT, 2k stars, last push 2026-04-20, not archived, no GitHub release; PyPI 1.1.0)
- **What it is:** a declarative query language for JSON with projections and filters: `data.items[?year>`2019`].name` (tested), multiselect hashes `{n:name,p:price}` (tested), and built-in functions such as `contains()` (tested).
- **Best at:** reshaping known-depth JSON into rows in one expression; a missing path returns None instead of raising (tested). Parsel exposes it directly (README).
- **Limits and traps:** no regular expressions and no recursive descent, so it cannot say "find the key `price` at any depth" (unverified); literals need backticks, which is easy to get wrong in a shell.
- **Cost or risk:** MIT, tiny, stable.
- **Reach for it when / not when:** reach for it for API responses of a known shape; not for hydration blobs of unknown depth.
- **Versus:** jsonpath-ng can search at any depth and match regexes; plain Python `dict.get` chains are clearer for two or three levels.

### jsonpath-ng (Python, Apache-2.0, 733 stars, last push 2026-08-01, not archived, latest GitHub release v1.7.0 on 2024-10-11; PyPI 1.8.0 released 2026-02-28)
- **What it is:** a JSONPath implementation whose expressions are parsed into objects. The extension parser (`from jsonpath_ng.ext import parse`) adds filters (`[?(@.price > 5)]`), regex match `=~`, arithmetic, `len`, `sorted` and `sub` (README).
- **Best at:** `$..key` searches at any depth, which is what an app-state blob needs, and in-place `update` and `filter` on the matched nodes.
- **Limits and traps:** filters and regexes work only from `jsonpath_ng.ext`, not from the base import. Filter values can only be compared to static values (README). Expressions are parsed at runtime and I did not measure speed, but a pure-Python parser is slower than jmespath on large data (unverified).
- **Cost or risk:** Apache-2.0; maintained (a PyPI release newer than the GitHub release).
- **Reach for it when / not when:** reach for it when the JSON is deeply nested or its depth changes between pages; not for high-volume flat API rows.
- **Versus:** jmespath is cleaner for known shapes and cannot recurse.

---

## C. Article and main-text extraction

Measured during this catalogue on our 135-page harness (63 Arabic and 72 English pages of one site, reference is the crawler's cleaned Markdown, word-overlap recall and precision). Rows 1 and 2 are our own numbers, reproduced exactly; the others are new. Defaults unless stated. Arabic goose3 used its `StopWordsArabic`; newspaper4k was given `language`.

| Tool | Arabic recall / precision | English recall / precision | Pages nearly empty (of 135) |
|---|---|---|---|
| trafilatura 2.2.0 | 0.91 / 0.96 | 0.96 / 0.98 | 0 |
| jusText 3.0.2, defaults | 0.17 / 0.30 | 0.71 / 0.87 | 53 |
| readability-lxml 0.9 | 0.78 / 0.92 | 0.83 / 0.94 | 3 |
| goose3 3.1.22 | 0.20 / 0.43 | 0.76 / 0.97 | 39 |
| newspaper4k 0.9.6 | 0.30 / 0.54 | 0.34 / 0.45 | 50 |
| jusText, stopword thresholds 0.15 and 0.20, length 40 and 100 | 0.70 / 0.90 | 0.87 / 0.95 | 8 |

The last row was tuned on the same pages it is scored on, so it is optimistic; it is there to show that the thresholds matter, not to recommend those values. Run time in the same run: trafilatura 4.1 s, readability-lxml 3.1 s, goose3 13.3 s, newspaper4k 42.8 s (our earlier run: 3.2 s for trafilatura against 1.6 s for jusText).
Mind the newspaper4k row: English 0.34 is low enough that a site-specific interaction or a configuration slip on my side is possible; do not generalise it.

### trafilatura (Python, Apache-2.0, 6k stars, last push 2026-09-11, not archived, latest release v2.2.0 on 2026-07-31)
- **What it is:** a text and metadata extractor and light crawler. Its own rule-based extractor (structural rules plus text-density heuristics) runs first, with jusText and readability-lxml as fallbacks (README; source read: the jusText fallback uses the page language's stoplist and a merged stoplist when the language is unknown). Output as text, Markdown, JSON, XML, TEI, CSV; metadata (title, author, date via htmldate, site name, tags).
- **Best at:** article-shaped pages in any language, because its main path is structural, not stoplist-driven; it also has sitemap and feed discovery (README). The README cites third-party benchmarks (Bevendorff et al. 2023, ScrapingHub's article-extraction benchmark); those are its claims and I did not rerun them.
- **Limits and traps:** it decides what is "main", so listings, data tables, forms and short structured pages can be truncated or dropped; use `favor_recall`, `include_tables`, or a selector-based parser for those (option names from memory, unverified). Its built-in `fetch_url` is a plain HTTP client with an ordinary Python fingerprint; when a site needs a browser-like TLS fingerprint, fetch with curl_cffi and pass it the HTML string. Dates inherit htmldate's limits (below).
- **Cost or risk:** Apache-2.0 from v1.8.0; earlier versions are GPLv3 or later (README), so do not pin an old release. Dependencies: courlan, htmldate, justext, lxml, charset_normalizer, urllib3 (PyPI).
- **Reach for it when / not when:** reach for it as the default for "give me the body text of this page"; not when you want fields (price, phone, mileage), where selectors or embedded JSON are right.
- **Versus:** jusText, goose3 and newspaper4k lean on stopword counts and fell over on Arabic here; readability-lxml is close on structure and slightly behind on recall; Mozilla's Readability needs a DOM.
- **Here:** 2.2.0 installed. Measured: recall 0.91 Arabic and 0.96 English, precision 0.96 and 0.98, no empty outputs, on 135 pages of one site; our default text extractor.

### jusText (Python, BSD-2-Clause, 825 stars, last push 2026-08-18, not archived, latest release v3.0.2 on 2025-02-25)
- **What it is:** splits the page into blocks at block-level tags, then classifies each block from its length, its link density and the share of its words found in a per-language stoplist (defaults from its documentation: link density 0.2, length 70 and 200, stopword density 0.30 and 0.32), then re-classifies short blocks from their neighbours. Built for cleaning web corpora, so it favours long grammatical prose.
- **Best at:** stripping menus and link lists from prose-heavy pages in languages whose stoplist density sits near the thresholds (English worked here at 0.71 recall).
- **Limits and traps:** it needs a stoplist per language and silently classifies as boilerplate whatever does not look like prose; structured pages of short headings, lists and FAQs suffer. It returns paragraphs, not metadata.
- **Cost or risk:** BSD-2; small; the algorithm is documented, so behaviour is predictable once you know it.
- **Reach for it when / not when:** reach for it as a second opinion on English long-form text, or when you tune its thresholds against labelled pages; not as an Arabic default.
- **Versus:** trafilatura uses it as a fallback only; readability-lxml scores nodes by text and class names instead of stoplists.
- **Here:** 3.0.2 installed. Measured on defaults: recall 0.17 Arabic and 0.71 English, and 53 of 135 pages nearly empty. An earlier one-page check on an Arabic services page had looked fine, which is the reminder that one page is not a sample.
- **Why it fails on Arabic (an explanation, not a proven cause):** the algorithm needs a block to look like prose by stopword density above 0.30 to 0.32, computed by splitting on spaces and matching tokens to the list. I measured the density of blocks of 200 characters or more on 60 pages per language: the median was 0.23 for Arabic against 0.44 for English, and only 16% of the Arabic blocks passed 0.30, against 95% of the English blocks (the Arabic stoplist has 2,770 entries, so it is not a small list). Lowering the thresholds and length limits recovered most of the text (table). Candidate reasons, which I did not separate: Arabic attaches conjunctions and prepositions to the next word, so exact-token matching finds fewer function words; Arabic uses fewer free-standing function words per token than English; the thresholds were fitted on other languages; and our note that this site's pages are short headings, lists and FAQs, which the length rule penalises whatever the language.

### readability-lxml, the "python-readability" port (table language shows HTML; Apache-2.0, 2k stars, last push 2026-08-27, not archived, latest release 0.9 on 2026-08-26; PyPI readability-lxml 0.9, Python 3.8.2 or newer and below 3.15)
- **What it is:** a Python port of Arc90 Readability: it scores candidate nodes by text length and by the class and id names around them, picks the best one plus qualifying siblings, and returns cleaned HTML (`Document(html).summary()`) and a title.
- **Best at:** article pages where the container is recognisable; on this corpus it was the only non-trafilatura extractor that held up on Arabic (0.78 recall, 3 of 135 nearly empty).
- **Limits and traps:** returns an HTML fragment, not text, and no metadata; the sanitising module is the split-out `lxml-html-clean` dependency. Scoring is on text and names, not language, but I did not check how it counts punctuation such as the Arabic comma (unverified). The README's own claim of a second-place F1 of 0.975 among ten engines on 181 pages is the author's report.
- **Cost or risk:** Apache-2.0; the release is new after a long quiet period (unverified as to history).
- **Reach for it when / not when:** reach for it as a second opinion next to trafilatura, or when you want HTML back; not when you need dates and authors.
- **Versus:** Mozilla's Readability is the reference implementation in JavaScript; this port tracks it "to match the latest readability.js" (README).

### Mozilla Readability (JavaScript, Apache-2.0, 11k stars, last push 2026-08-04, not archived, no GitHub release; distributed on npm (unverified))
- **What it is:** the code behind Firefox Reader View. It works on a DOM: you give it a `document` and call `new Readability(doc).parse()`; `isProbablyReaderable()` tells you whether a page is worth trying (`charThreshold` default 500, README).
- **Best at:** matching what Reader View would show; well tested on real browser DOMs; a natural fit when a browser or jsdom already holds the page (for example a Playwright page you evaluate in).
- **Limits and traps:** it needs a DOM implementation, so from Python you run Node with jsdom or evaluate inside a browser; jsdom must not run the page's scripts. The README says plainly that it does not sanitise and that untrusted input should go through DOMPurify.
- **Cost or risk:** licence and maintenance are good; the cost is a Node dependency and a process boundary.
- **Reach for it when / not when:** reach for it when you are already in a browser context; not in a plain Python pipeline where trafilatura or readability-lxml does the job with no Node.
- **Versus:** readability-lxml is the Python port of the same idea.

### goose3 (table language shows HTML; Apache-2.0, 914 stars, last push 2026-07-23, not archived, latest release v3.1.22 on 2026-07-23)
- **What it is:** a Python port of the Goose article extractor: it finds the top node by counting stopwords in candidate paragraphs, then cleans it, and extracts title, meta description, top image and dates.
- **Best at:** English news pages with images and metadata, where its outputs are precise (0.97 precision on English here).
- **Limits and traps:** it needs a stopwords class per language; the README says that for Arabic you must pass `StopWordsArabic`. Even with it, Arabic recall here was 0.20 and 39 of 135 pages were nearly empty. Same mechanism family as jusText, same failure.
- **Cost or risk:** Apache-2.0, maintained; its dependencies include Pillow, langdetect and pyahocorasick (PyPI).
- **Reach for it when / not when:** reach for it for English news with images; not for Arabic pages.
- **Versus:** trafilatura is language-agnostic on its main path; goose3 is stoplist-driven.

### newspaper4k (Python, MIT, 1k stars, last push 2026-08-24, not archived, latest release 0.9.6 on 2026-07-19; PyPI needs Python 3.10 or newer)
- **What it is:** a fork of newspaper3k that downloads pages, parses articles (text, authors, date, top image, videos), optionally runs `nlp()` (keywords, summary) and can build a whole news source (`newspaper.build`), with Google News integration through an extra.
- **Best at:** the convenience layer: URL in, article object out, source-level crawling, and 80-plus languages listed in the README.
- **Limits and traps:** the README itself says that if the language is wrong or unsupported, "chances are that no article text will be returned". Here, with the language set, Arabic recall was 0.30 and English 0.34, and it was the slowest extractor (42.8 s for 135 pages). It downloads with `requests`. Optional language extras pull nltk and others.
- **Cost or risk:** MIT, actively maintained; bulk crawling with it can get an IP blocked (README says so).
- **Reach for it when / not when:** reach for it when you want its source-level crawling and news conveniences on English or supported-language sites; not as the text extractor for Arabic.
- **Versus:** trafilatura extracted better on this corpus and takes any fetched HTML string.

### markitdown (Python, MIT, 186k stars, last push 2026-09-16, not archived, latest release v0.1.7 on 2026-07-29; needs Python 3.10 or newer)
- **What it is:** Microsoft's converter from files to Markdown: PDF, Word, PowerPoint, Excel, images, audio, HTML, CSV, JSON, EPUB, ZIP. For HTML its declared dependencies are BeautifulSoup and markdownify, so it is a whole-page tag-to-Markdown conversion (unverified as to boilerplate handling; I did not run it).
- **Best at:** one call that turns mixed office documents into text an LLM can read, keeping headings, lists and tables.
- **Limits and traps:** it is not a main-content extractor, so a web page's menus come along (unverified). OCR of images inside documents needs a plugin and a vision-model client, and silently skips OCR when no client is given (README). Scanned Arabic PDFs need real OCR (another category). The README warns it reads files and URLs with the privileges of the process, so sanitise inputs.
- **Cost or risk:** MIT; large dependency set (magika, requests, defusedxml, charset-normalizer, markdownify, BeautifulSoup); optional Azure Document Intelligence is a paid service (check current pricing).
- **Reach for it when / not when:** reach for it to normalise Office and PDF files before an LLM step; not for picking the article out of a web page.
- **Versus:** trafilatura (Markdown output too) for web articles; Unstructured for element-level partitioning; PDF-specific libraries for tables.

### Unstructured (table language shows HTML; Apache-2.0, 15k stars, last push 2026-09-21, not archived, latest release 0.27.6 on 2026-09-14; PyPI requires Python 3.11 to 3.13)
- **What it is:** an ETL library that partitions documents (HTML, PDF, Word, email and more) into typed elements (title, narrative text, list item, table) with metadata, ready for chunking and vector stores; it also has hosted and enterprise products (README).
- **Best at:** turning many file types into a uniform element list for retrieval pipelines.
- **Limits and traps:** heavy install: declared dependencies include spacy, numba, numpy, rapidfuzz and langdetect; PDF and image work needs tesseract and other system packages (README); Python 3.14 is excluded by its metadata. For plain web pages it is more machinery than trafilatura needs.
- **Cost or risk:** open source is free; the hosted API and pipelines are commercial (check current pricing).
- **Reach for it when / not when:** reach for it when a mixed-format corpus must become chunks; not for extracting one site's articles.
- **Versus:** markitdown is lighter and returns Markdown, not typed elements.

### inscriptis (Python, Apache-2.0, 345 stars, last push 2026-09-14, not archived, latest release 2.7.4 on 2026-08-10; not in the metadata table, read from GitHub and PyPI; PyPI needs Python 3.10 or newer)
- **What it is:** an HTML to text converter built on lxml that renders layout: lists, indentation and tables as aligned columns, following CSS display rules (unverified as to the detail; I did not run it).
- **Best at:** text that keeps the visual structure of tables, useful for diffing or for feeding a model a page's table without losing rows.
- **Limits and traps:** it converts the whole document, so boilerplate stays; column alignment counts characters, which is not display width for mixed Arabic and Latin text (unverified).
- **Cost or risk:** Apache-2.0; active; lxml-bound.
- **Reach for it when / not when:** when the table layout matters in plain text; not when you want the article body only.
- **Versus:** html2text targets Markdown; trafilatura removes boilerplate first.

### html2text (Python, GPL-3.0, 2.2k stars, last push 2025-10-28, not archived, latest release 2025.4.15; not in the metadata table, read from GitHub and PyPI; PyPI licence GPL-3.0-or-later)
- **What it is:** an HTML to Markdown-like text converter (originally Aaron Swartz's).
- **Best at:** quick conversion of a fragment such as an email body or a description block.
- **Limits and traps:** it wraps lines at a default width unless you set `body_width=0` (unverified); whole document, no boilerplate removal.
- **Cost or risk:** GPL-3.0-or-later, so bundling it into something you hand to a client raises a copyleft question; internal pipeline use is a different matter (unverified legal reading, ask before shipping).
- **Reach for it when / not when:** internal one-offs; not in a delivered tool.
- **Versus:** inscriptis (Apache, layout-aware), trafilatura Markdown output (Apache, boilerplate-aware).

### htmldate (Python, Apache-2.0, 157 stars, last push 2026-09-10, not archived, latest release v1.10.0 on 2026-06-01; PyPI needs Python 3.10 or newer)
- **What it is:** publication and update date extraction in three stages: markup in the header (meta and link elements, OpenGraph), structural markers in the body (`time`, `abbr` and known attributes), then, in `extensive` mode, patterns in the bare text with a disambiguation step (README). Its dependencies include dateparser.
- **Best at:** dates that exist in markup, and the URL; the author reports F-score 0.925 (fast) and 0.949 (extensive) on 1,000 pages against 0.705 to 0.810 for goose3, newspaper4k and three other packages (the author's benchmark).
- **Limits and traps (tested):** with `article:published_time`, a `<time datetime>` or a date in the URL it was right. On body text it fails for Arabic: "نُشر في 14 آذار 2025" returned 2025-01-01 in extensive mode (a bare year turned into January first, plausible and wrong) and None in fast mode; Arabic-Indic numerals returned None; "14/03/2025" in ASCII digits worked in extensive mode. Treat any result that ends in -01-01 with suspicion.
- **Cost or risk:** Apache-2.0, maintained.
- **Reach for it when / not when:** reach for it to read machine-readable dates and as a cross-check on the URL; not to read Arabic dates written in words; use dateparser plus a month map for those.
- **Versus:** newspaper4k and goose3 have their own weaker date extraction; trafilatura calls htmldate.
- **Here:** htmldate arrives with trafilatura 2.2.0 as its dependency.

---

## D. Field-level parsers

Three problems recur across all of them.
- Arabic-Indic digits (U+0660 to U+0669) and Persian digits (U+06F0 to U+06F9) both appear on Iraqi pages. In Python, `int("٣٥")` works and a str regex `\d` matches them (tested), but `float("٣٫٥")` raises because the Arabic decimal separator U+066B is not a dot, and the thousands separator U+066C is not a comma. NFKC normalisation does not turn these digits into ASCII (tested). Fold digits and separators with one translate table before you parse (tested), or use `re.ASCII`.
- Mixed-direction text: a price inside an Arabic sentence is a left-to-right run inside a right-to-left line, and copied text often carries invisible marks (U+200E, U+200F, U+202A to U+202E, U+2066 to U+2069, U+061C, and joiners U+200C and U+200D). Keep the string in logical order, strip those marks in matching keys only, and never hand display-ordered text to a parser. PDF text can arrive in visual order, which is the same trap from the other side (our note).
- Scale words: "25 مليون" and "15 ألف" are numbers in words. A generic price parser reads the 25 and drops the scale (tested below), so you must handle scale yourself.

### dateparser (Python, BSD-3-Clause, 2k stars, last push 2026-09-16, not archived, latest release v1.4.3 on 2026-09-03; PyPI needs Python 3.10 or newer)
- **What it is:** a rule-based parser for human dates in more than 200 language locales (README), absolute and relative ("3 hours ago"), with language auto-detection and non-Gregorian calendar support.
- **Best at:** one call over messy multilingual date strings, with `languages=[...]`, `DATE_ORDER` and `RELATIVE_BASE` settings.
- **Limits and traps (tested on the latest 1.4.3; the Levantine month names and the 12/03/2025 ambiguity gave the same results on 1.2.1):** with `languages=["ar"]` it parsed "14 اكتوبر 2024" and "5 مايو 2025" (Gulf and Egyptian month names) and "منذ 3 ساعات", but returned None for every Levantine and Iraqi month name I tried: كانون الثاني, شباط, آذار, نيسان, آيار, حزيران, تموز, أيلول, تشرين الأول, تشرين الثاني, كانون الأول. It also returned None for "قبل يومين" and "قبل 5 دقائق". Without `languages`, "10 اب 2025" came back as the current date and time, a plausible wrong value. "12/03/2025" is 12 March under `languages=["ar"]` but 3 December under auto-detection, with no warning: always pass the language and `DATE_ORDER`.
- **Cost or risk:** BSD; slow relative to a regex because it loads locale data; results depend on the library's locale tables, so pin the version.
- **Reach for it when / not when:** English and Gulf-style dates, and relative times, after you fold digits; not Iraqi Arabic month names without your own map.
- **Versus:** htmldate finds the date in a page but does not read Arabic words; a twelve-entry month map plus `datetime` is more reliable than any of them for Iraqi names. Write that map against the normalised form of the month names (see part F).

### price-parser (Python, BSD-3-Clause, 348 stars, last push 2026-08-06, not archived, no GitHub release; PyPI 0.5.1 released 2026-03-19)
- **What it is:** `Price.fromstring(text)` separates an amount (as Decimal) and a currency symbol or code from a raw string.
- **Best at:** decimal and thousands separators in Latin-script prices ("1.250.000 IQD" and "1,250,000 IQD" both gave 1250000; "IQD 12,500" gave 12500; tested).
- **Limits and traps (tested on 0.5.1):** Arabic currency words and abbreviations are not recognised (دينار, دولار, د.ع all returned no currency). The Arabic thousands separator broke it: "١٥٬٠٠٠ دينار" returned 15, dropping three zeros silently. Scale words are ignored in Arabic and in English: "25 مليون دينار" gave 25, "15 ألف دولار" gave 15 and "25 million IQD" gave 25. "3,5 مليون" gave 3.5.
- **Cost or risk:** BSD; small. The risk is the silent factor of 1,000 or 1,000,000 in a price column.
- **Reach for it when / not when:** reach for it after you have folded Arabic digits and separators to ASCII and handled scale words yourself; not on raw Arabic price strings.
- **Versus:** a purpose-written regex over normalised text is as short and does what the site's own convention needs; pyarabic's `text2number` reads number words, with the errors noted in part F.

### python-phonenumbers (Python, Apache-2.0, 3k stars, last push 2026-09-21, not archived, no GitHub release; PyPI 9.0.39 released 2026-09-10)
- **What it is:** the Python port of Google's libphonenumber: parse, validate, format, classify by number type, and find numbers in free text with `PhoneNumberMatcher`.
- **Best at:** turning every written form of a number into one canonical E.164 string. Tested with region "IQ", all of these gave `+9647701234567`: "0770 123 4567", "07701234567", "+964 770 123 4567", "00964 770 123 4567", "964770 123 4567", "770 123 4567", and the Arabic-Indic digits "٠٧٧٠١٢٣٤٥٦٧" (the parser reads Arabic digits itself).
- **Limits and traps:** `is_possible_number` is a length check and returns True for a nine-digit "0770123456" that `is_valid_number` rejects, so use validity. Mobile prefixes were labelled by the carrier lookup: 075x Korek, 077x Asiacell, 078x and 079x Zain (from the library's data); those labels reflect the prefix allocation, not necessarily the operator today (unverified). Baghdad fixed lines such as "01 234 5678" validate as fixed line; a landline typed with a stray digit ("0 1 5433 2109") parsed as possible but invalid. Without a default region, a local "07..." number cannot be parsed.
- **Cost or risk:** Apache-2.0; the metadata is bundled, so updates track Iraq's numbering plan only as fast as the library is upgraded.
- **Reach for it when / not when:** always, for phones, once a column has been extracted; not to decide who owns a number.
- **Versus:** hand regexes for local formats break on 00964, spaces and Arabic digits.
- **Here:** Google Maps outputs from our scrapers give phones in local format ("0783 ..."), so a `region="IQ"` normalisation step before de-duplicating is the natural use. Phone coverage is a property of the neighbourhood, not the tool, so a low rate is not a parsing bug.

---

## E. Learned and LLM extraction

### autoscraper (Python, MIT, 7k stars, last push 2026-07-29, not archived, latest release v1.1.14 on 2022-07-17)
- **What it is:** you give it a page (URL or HTML) and sample values you can see on it, and it learns rules that locate those values; it then returns similar elements on the same page or the same elements on other pages (README). It sits on requests, BeautifulSoup and lxml (PyPI).
- **Best at:** prototyping a scrape of a list with no selector writing; the model can be saved and loaded (README).
- **Limits and traps:** the rules are structural paths learned from your examples (internal mechanism unverified), so "similar" can sweep in sidebars and recommendations that share the markup. The sample text has to match the page exactly, including whitespace and digits. There is no validation: a wrong rule returns a plausible list. The last packaged release is from 2022 even though pushes continue. It downloads with requests unless you pass `html=`.
- **Cost or risk:** MIT, free; the risk is silent drift and no test story.
- **Reach for it when / not when:** reach for it for a one-off throwaway list; not for a repeated collection, where a written selector with a fill-rate check is more honest.
- **Versus:** Scrapling's adaptive mode re-finds a specific element after a redesign; autoscraper builds rules from examples once.

### Scrapling (Python, BSD-3-Clause, 82k stars, last push 2026-09-19, not archived, latest release v0.4.15 on 2026-08-23; PyPI needs Python 3.10 or newer)
- **What it is:** a framework with a parser (lxml plus cssselect, orjson and others per PyPI), fetchers (HTTP, browser, and "stealth" browser), a spider layer, an MCP server and a Markdown converter. The adaptive part is what this category cares about.
- **Best at:** adaptive selectors, verified in its docs. With `auto_save=True` it stores the element's properties in a database (SQLite by default) keyed by domain and an identifier; later, with `adaptive=True`, if the selector finds nothing it searches the page for the element most similar to the saved one. `find_similar()` returns elements like a given one.
- **Limits and traps:** it returns the closest candidate, which may be the wrong element; the docs do not describe a confidence check, so validate the value's type and range downstream (README does not say more, unverified). Adaptive data is isolated per domain, so a domain move needs `adaptive_domain`. The base install has the parser only; fetchers and spiders need extras (README).
- **Cost or risk:** BSD-3-Clause, very active. Its fetchers include ones marketed as bypassing anti-bot systems and Cloudflare Turnstile (README). Our line: copying what a real browser sends is fine, defeating challenges or rotating identities to pass a block is not, so use only the parser layer, and treat the stealth fetchers as out of bounds for client work. Its MCP server strips hidden text before a model reads a page, which addresses the prompt-injection risk of pages steering an agent (README claim, not tested).
- **Reach for it when / not when:** reach for its parser when a long-running collection breaks whenever a class name changes; not as a stealth crawler, and not without a downstream value check.
- **Versus:** anansi does a similar repair with confidence scores and much more bundled behaviour; the by-hand equivalent (two or three independent selectors per field plus a per-run fill-rate alarm) is in our notes and needs no library.
- **Here:** not installed and not measured. The author's benchmark (Scrapling 1.99 ms against selectolax 197 ms) uses a workload the README does not describe; we have not measured Scrapling.

### anansi (Python, Apache-2.0, 115 stars, last push 2026-09-02, not archived, latest release v1.2.0 on 2026-09-02; repository created 2026-05-14)
- **What it is:** a self-healing scraper: per-field CSS selectors carry confidence scores in SQLite; when one fails, four strategies compete (text-pattern match, fuzzy attribute match, structural context, XPath fallback) and the winner is stored (its docs). It first reads JSON-LD, OpenGraph and microdata for each field, checks each response for a JavaScript shell and silently retries in a stealth browser, and ships an MCP server with 17 tools so a model can drive crawls.
- **Best at:** the idea of scored, persisted selectors and a structured-data pre-pass, which is worth copying by hand.
- **Limits and traps:** install trap, verified: `pip install anansi` on PyPI is a different, unrelated project ("Asyncio data modeling library", 0.0.dev55). The README installs this one from GitHub, so a typo or a copied command can pull the wrong package. Two contributors, four months old on the day I read it. The MCP server means crawled page content can reach a model that holds tools.
- **Cost or risk:** its README describes presenting a matched TLS fingerprint, persona and headers "to slip past detection" and handling Cloudflare, Akamai and DataDome. That is evasion tooling; this skill's rule excludes defeating challenges, and our notes recommend not running it on client work.
- **Reach for it when / not when:** never for client work; read its how-it-works page for the healing design.
- **Versus:** Scrapling's adaptive mode is the same idea in a bigger, older project.
- **Here:** not installed, on purpose.

### LLM extraction (approach, not a package)
- **What it is:** send page text or a trimmed DOM to a language model with a schema and ask for the fields as JSON. Framework wrappers exist in other categories (crawl4ai, ScrapeGraphAI, Firecrawl); Scrapling's MCP narrows pages by selector first.
- **Best at:** free text and one-off pages with no stable template: an ad description that says "تويوتا كامري 2018 فل مواصفات 15 مليون", a PDF letter, a page you will read once. It handles synonyms, mixed Arabic and English and layout changes with no selector work.
- **Cost:** input tokens dominate and scale with the page, so convert to text or the embedded JSON first (a 367 KB app-router page in the scratchpad carries a 95 KB payload, and the fields you want are a small fraction of that). Arabic usually tokenises to more tokens per word than English (unverified). Prices change: check current pricing per model, and cache by a hash of the input.
- **Determinism:** the same page can return different values on two runs even at temperature zero, and a model version change can change every output (unverified). Pin the model, store the raw input, output and version, and diff runs.
- **Hallucination on numbers:** the dangerous failures look right: a price with a scale slip (15 مليون read as 15,000), digits transliterated between Arabic-Indic and Latin, a year completed from context, a phone number with a digit repaired. Defend by requiring the model to quote the source span, then check by machine that every number in the output appears in the normalised source text, reject on mismatch, sample by hand, and compare a regex or selector baseline on a labelled set before trusting it.
- **Reach for it when / not when:** reach for it for long-tail, unstructured, low-volume extraction where a wrong field is caught by a check; not for templated pages at volume (a selector is cheaper and exact), and not for a figure you will publish without an independent verification.
- **Versus:** selectors and embedded JSON are exact and free; LLMs trade exactness for reach. Treat page text as untrusted: hidden instructions inside a page can steer the model.

---

## F. Arabic text and record matching

### Normalisation choices (for match keys; keep the original string for display and storage)
Every fold below loses information, so apply it to a copy used only for matching and joining. Tested where marked.
- Diacritics (U+064B to U+0652, plus U+0653 to U+065F and the superscript alef U+0670): strip. Tatweel (U+0640): strip. Invisible direction marks and joiners: strip.
- Alef variants أ إ آ ٱ to plain ا: safe for names and places; the cost is the hamza distinction, which rarely separates two different entities.
- Alef maksura ى to ya ي: safe. Persian and Kurdish keyboard variants ک (U+06A9) to ك and ی (U+06CC) to ي: needed when Kurdish or Persian keyboards leak in.
- Ta marbuta ة to ha ه: common in informal writing, and it makes مدرسة and مدرسه equal; it is also the most lossy fold. Decide it by counting what it merges in your own data.
- Hamza carriers ؤ ئ: folding to و ي or ء is aggressive; test before adopting.
- Kurdish letters (ە U+06D5, ڕ, ڵ, ۆ, ێ, ڤ) are not Arabic variants: folding ە to ه merges different Kurdish spellings, so do not fold them when matching Sulaymaniyah or Erbil names.
- Digits: fold Arabic-Indic and Persian digits and the separators U+066B, U+066C and the Arabic comma U+060C to ASCII (tested translate table). NFKC alone does not do it (tested); NFKC does restore reshaped presentation-form letters (tested), which matters for text copied out of PDFs.
- Do not strip the definite article "ال" or spaces blindly. Our derived key that stripped articles and vowels did worse than the plain baseline (1,286 mismatches) because it separated two spellings that differ by a trailing letter and merged two that must stay apart. "عبدالله" and "عبد الله" are one name; a comparison that removes spaces treats them as equal (score 100 in the test below).
- Our two lessons, both from its extraction notes: (1) patterns must be written in the post-normalisation form. After folding, "مدرسة" is "مدرسه" and "أربيل" is "اربيل"; a pattern typed the way a person writes never fires, and the records it should catch fall into "unknown". Assert that every alternative in a pattern fires at least once on the corpus. (2) Name maps are copied from the data, not typed from memory. A map typed from memory got 4 of 18 wrong (641 false mismatches); typing Ninewa, Basrah and Muthanna against a file that says Ninawa, Al-Basrah and Al-Muthanna silently failed 13 of 18 joins; alias tables read off the field took a direct 25 of 621 matches to 312, and the gain was measured as a join rate before and after.

### camel_tools (Python, MIT, 579 stars, last push 2026-06-08, not archived, latest release v1.6.0 on 2026-06-08; PyPI needs Python 3.11 or newer)
- **What it is:** the CAMeL Lab (NYU Abu Dhabi) Arabic NLP suite: morphological analysis and generation, disambiguation, tokenisation, tagging, named-entity recognition, sentiment, dialect identification, and small utilities (`camel_tools.utils.normalize` has `normalize_alef_ar`, `normalize_alef_maksura_ar`, `normalize_teh_marbuta_ar`, `normalize_unicode`; `dediac_ar` strips diacritics; all read in the source).
- **Best at:** real Arabic linguistics: lemmas, part of speech, dialect ID and NER, from a research group that maintains data packages for them.
- **Limits and traps:** heavy. The README requires Python 3.11 to 3.14 and a Rust compiler, plus cmake and Boost on Linux; the models come from a separate `camel_data -i light|defaults|all` download into `%APPDATA%\camel_tools` on Windows or `~/.camel_tools`; PyPI's declared dependencies include torch, transformers, scikit-learn, pandas and scipy. The README says dialect identification is not available on Windows, so it is an Ubuntu-server-only feature. Whether its analysers cover Iraqi dialect well I could not verify.
- **Cost or risk:** MIT, maintained; the cost is install size and setup time.
- **Reach for it when / not when:** reach for it for lemmatisation, dialect ID or NER on text you analyse; not to fold letters or strip diacritics, where ten lines of your own code do the same work with no torch.
- **Versus:** pyarabic is a light utility set; camel_tools is the analytical toolkit.

### pyarabic (Python, GPL-3.0, 491 stars, last push 2026-01-16, not archived, latest GitHub release v0.6.16 on 2023-04-16; PyPI 0.6.15)
- **What it is:** small Arabic utilities: letter classification, tokenising, `araby.strip_tashkeel`, `strip_tatweel`, `normalize_hamza`, `normalize_alef`, `normalize_teh`, `normalize_ligature`, and a `number` module that converts number words to digits and back (`text2number`, `number2text`, `extract_number_phrases`); all present in the source.
- **Best at:** the number-word reader and the diacritic and tatweel strippers in one dependency-free package.
- **Limits and traps (tested on 0.6.15):** `normalize_hamza` with its default method maps every hamza carrier to a bare hamza, so "أحمد" becomes "ءحمد", not "احمد"; use `normalize_alef` if you want the alef fold, and do not mix the two. `text2number` was right on "خمسة عشر مليون" (15,000,000), "خمسة وعشرون ألف" (25,000) and "مئتان وخمسون ألف" (250,000), and silently wrong on "ثلاثة ملايين ونصف" (gave 3,000,000, should be 3,500,000) and "مليون ومئتين الف" (gave 1,000,200, should be 1,200,000). Verify any number it reads against the digits on the page.
- **Cost or risk:** GPL-3.0, which matters if you ship it inside a client tool; fine for an internal pipeline (unverified legal reading, ask before shipping). Release cadence is slow.
- **Reach for it when / not when:** reach for it for number words in ad prices, with a check; not as your normaliser if you do not want a GPL dependency (write the fold yourself).
- **Versus:** camel_tools has linguistically grounded normalisers and much more, at a much larger install.

### python-arabic-reshaper (Python, MIT, 447 stars, last push 2026-04-28, not archived, latest release v3.0.1 on 2026-04-28; PyPI needs Python 3.10 or newer)
- **What it is:** rewrites Arabic letters into their joined presentation forms (Unicode Arabic Presentation Forms-B, U+FE70 to U+FEFF), so that a renderer with no Arabic shaping draws connected letters.
- **Best at:** drawing Arabic in libraries that do not shape it (its README's examples are PIL drawing).
- **Limits and traps (tested):** the output is a different set of code points: the reshaped "سوق بغداد" no longer contains the string "بغداد", so search, comparison and deduplication all fail on it. It is display-only. Never store it, match on it, or put it in a file or database column; do the reshape at the last moment in the drawing call. Modern renderers (browsers, Word, Qt, PIL with libraqm) shape and reorder text themselves, and reshaping first would double-process it (unverified). NFKC turns the shaped letters back into base letters (tested) but does not undo a visual reordering.
- **Cost or risk:** MIT; small.
- **Reach for it when / not when:** reach for it when you draw Arabic labels with a library that lacks shaping; not for anything that is stored or joined.
- **Versus:** python-bidi does the ordering; they are used together.

### python-bidi (Python, LGPL-3.0, 126 stars, last push 2026-06-30, not archived, latest release v0.6.11 on 2026-07-01)
- **What it is:** the Unicode bidirectional algorithm: `get_display(text)` returns the string in visual order for a renderer that draws left to right. Two implementations (README): the pure-Python V5 one at `bidi.algorithm`, and a wrapper over the Rust `unicode-bidi` crate at top-level `bidi`, which the README says seems to implement a higher version of the algorithm "albeit with some missing".
- **Best at:** getting mixed Arabic and Latin text to display in the right order in libraries that do not do it.
- **Limits and traps (tested with 0.6.3):** the output is in visual order, which is the reverse of reading order for Arabic (the reshaped and displayed "سوق بغداد 2025" begins with "2025" and ends with the letters of "سوق"), so like the reshaper it is display-only and must never be the stored value. The README's development instructions need a Rust toolchain.
- **Cost or risk:** LGPL-3.0, fine as a dependency; matters only if you copy or modify its code into a distributed product.
- **Reach for it when / not when:** when drawing text into an image or PDF with a non-shaping library; not for storage, search or web output.
- **Versus:** the browser does this for you in HTML and charts, so a dashboard label does not need it.

### rapidfuzz (Python and C++, MIT, 4k stars, last push 2026-09-12, not archived, latest release v3.14.6-1 on 2026-08-30; PyPI needs Python 3.11 or newer)
- **What it is:** fast string similarity: Levenshtein, Indel, Jaro-Winkler, and fuzzywuzzy-style scorers (`fuzz.ratio`, `partial_ratio`, `token_sort_ratio`, `token_set_ratio`, `WRatio`), plus `process.extractOne` and `process.cdist` for many-to-many comparison (README).
- **Best at:** speed (C++ core; the README says `cdist` is much faster than looping) and a choice of metrics.
- **Limits and traps (tested on 3.10.0):** the default `processor` is None, so it does no case-folding or trimming ("ABC" against "abc" scored 0.0). It works on code points, so unfolded alef and ya variants cost score (أحمد against احمد 92 raw, 100 after folding). Scores on Arabic names mislead in specific ways: "عبد الله محمد" against "عبد الرحمن محمد", two different people, scored 79; `partial_ratio("علي","علياء")` scored 100 because one is a substring of the other; `token_set_ratio("صيدلية الشفاء","صيدلية الشفاء الاهلية")` scored 100 because one is a subset, which may or may not be the same shop; "عبدالله محمد" against "عبد الله محمد" scored 96 as `ratio` but 72 as `token_set_ratio`, and 100 with spaces removed.
- **Cost or risk:** MIT; on Windows it needs the Visual C++ redistributable (README).
- **Reach for it when / not when:** reach for it once both sides are folded, with a threshold chosen on labelled pairs from your own data; not with a threshold copied from an English tutorial.
- **Versus:** splink combines several such comparisons into a probability across fields; rapidfuzz scores one pair of strings.
- **Here:** RapidFuzz 3.10.0 was present on the laptop; it is not in the stated install list.

### splink (Python, MIT, 2k stars, last push 2026-09-19, not archived, latest release v4.0.17 on 2026-09-03; PyPI needs Python 3.10 or newer and below 4)
- **What it is:** probabilistic record linkage (Fellegi-Sunter): you declare comparisons per column (exact, fuzzy, with term-frequency adjustment) and blocking rules, it learns match weights by unsupervised estimation, scores pairs, and clusters them into entity ids. Runs on DuckDB by default, Spark or PostgreSQL by extras (README).
- **Best at:** linking or deduplicating records across sources with several imperfect fields (name, address, district, phone), and explaining why a pair matched; it adjusts for common values, which matters for names like محمد and علي.
- **Limits and traps:** the README says it performs best with several columns that are not highly correlated, and is not designed for a single "bag of words" column such as a lone company name. It needs blocking rules or the pair count explodes. It does not normalise Arabic for you: fold names first. It needs a labelled sample or a careful look at its charts to trust the thresholds. Declared dependencies include altair, duckdb, igraph and pandas.
- **Cost or risk:** MIT; free; the cost is the learning curve and the time to build a check set.
- **Reach for it when / not when:** reach for it when you link registries, shop lists or Google Maps places across sources with name, phone, district and coordinates as blocking and comparison fields; not for a few thousand records with a clean key such as a validated E.164 phone number, where a join and a rapidfuzz check are simpler.
- **Versus:** rapidfuzz is one string pair; a hand-built pipeline of phone key plus fuzzy name plus distance is the lighter alternative (a recordlinkage-style library also exists, unverified).

---

## How to choose

Choosing a parser. Start from what the markup will be like and whether you need to walk upward. For volume and CSS, selectolax with Lexbor is the default here: fast, an HTML5 tree that matches what a browser shows, and installed. If a field is defined by a neighbour ("the value next to the label", "the row containing this heading"), XPath is the honest tool and parsel (or lxml) is the choice, because CSS cannot go up and selectolax has no XPath; parsel is also the right layer inside Scrapy. BeautifulSoup is for small jobs and tree surgery, and pyquery and html5lib have no case on this laptop that parsel or Lexbor does not cover better. Whatever you choose, decode to str yourself and keep the raw bytes: three of the parsers above mis-decode Arabic silently in different ways, and selectolax will turn an empty response into a quiet "not found". Switch when a measured fill rate drops on one field (selector drift: add a second independent selector or try Scrapling's adaptive re-find behind a value check), when a DevTools-copied XPath finds nothing (you are on lxml's tree, not the browser's), or when a table walk gives columns in the wrong order (read the header labels, not positions).

Choosing a text extractor. Use trafilatura first for anything that is an article or a page of prose, in Arabic or English: it was the only one of the five extractors here that gave high recall and precision on both languages, and it does not depend on stopword counts. Keep readability-lxml as the second opinion when trafilatura returns too little, since it held up on Arabic (0.78) where the stoplist family did not. Do not use jusText, goose3 or newspaper4k as the Arabic extractor on the strength of English results, and if you must use jusText, tune the thresholds on labelled pages of your own site rather than trusting defaults. Neither trafilatura nor readability is right for structured pages (listings, prices, phone numbers): those want selectors or the embedded JSON. markitdown and Unstructured are for files (PDF, Office), not web pages. Switch when the extraction is short against the visible text on a sample you read by eye, and measure on a second site before generalising: this comparison is one site, and our earlier "jusText works" came from a single page.

When to stop parsing markup and read the embedded JSON. Look at the page source before writing a single selector: search for `application/ld+json`, `__NEXT_DATA__`, `__next_f`, `__NUXT_DATA__` and `__APOLLO_STATE__`. If the record you want is in there, read it: it has ids, coordinates, ISO dates and unformatted prices that the template hides, and it survives redesigns because it follows the data model. Go further and look for the API request the page makes, which is the same data without the page. Stay with markup when the blob holds only the first page of a list, when it lacks the field you need, or when the site fills the data after load and the payload is empty. Guard both routes the same way: match on the exact id you hold (an id appears inside neighbouring records), and keep a canary field that alerts when the format changes.

Fields, Arabic text and matching. After extraction, turn text into typed values in a fixed order: strip invisible marks, fold digits and separators, handle scale words yourself, then parse. Use python-phonenumbers with region "IQ" for phones (it read every local, international and Arabic-digit form I tried). Do not trust dateparser or price-parser on raw Iraqi Arabic: Levantine month names and Arabic currency and scale words are outside them, and the failures are silent (a plausible date, a price one thousand times too small). Write a small explicit month map and scale map against the normalised spelling. For matching, fold a copy of each name (alef, ya, diacritics, tatweel, digits, and ta marbuta only if the data justifies it), score with rapidfuzz, set the threshold on labelled pairs from your own data, copy every alias table from the values actually present, and assert that each rule and each map entry fires. Move to splink when you have several fields per record and several sources, and to camel_tools only when you need real linguistics. Reshaper and bidi belong at the last step of drawing text, never in storage. LLM extraction earns its cost where the input is free text with no template and a wrong value gets caught by a machine check against the source; everywhere else a selector or the page's own JSON is cheaper and exact.
