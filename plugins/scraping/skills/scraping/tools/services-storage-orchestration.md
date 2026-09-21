# Managed services, storage, orchestration and support libraries

Compiled 21 Sep 2026. Status lines for GitHub projects are taken verbatim from ghmeta.tsv (read from GitHub on 21 Sep 2026). Things I ran myself on the laptop or fetched from vendor docs on 21 Sep 2026 are stated as facts. Anything from memory ends with `(unverified)`. Prices and limits of commercial services end with `(check current pricing)` and no dollar figure is given unless I read it from a vendor page or from our own notes.

Laptop check (pip list in the Python 3.12.4 that Bash uses, 21 Sep 2026): present are duckdb 1.5.4, pandas 3.0.5, pyarrow 21.0.0, openpyxl 3.1.5, xlsxwriter 3.2.9, shapely 2.0.6, geopandas 1.1.3, osmnx 2.1.0, tenacity 9.1.4, tqdm 4.70.0, diskcache 5.6.3, Rtree 1.0.1, pyogrio 0.12.1, python-bidi 0.6.3, arabic-reshaper 3.0.0. Not present: polars, aiolimiter, pyrate-limiter, requests-cache, prefect, dagster, apache-airflow. (I installed polars 1.44.2 into a scratch folder only, to measure it.)

---

# A. Managed scraping platforms and APIs

## What you are actually paying for

A managed service sells some mix of five things. Knowing which one you need tells you whether to buy at all.

- IPs: a pool of addresses (datacenter, or residential and mobile) so requests come from many places. Billed by gigabyte or folded into a per-request price. Residential pools carry a sourcing question: whose device is the exit node, and did they agree (unverified).
- Unblocking: solving challenges, matching browser fingerprints, retrying with other configurations until a page comes back. This is the most expensive component and the one this skill's rule excludes when it is used to get past a block (see this skill's line below).
- Rendering: someone else's headless browser time, for pages that build themselves in JavaScript. Usually a multiplier on the price of a plain fetch.
- Parsing: the vendor returns fields instead of HTML (product, article, search result, place). Saves you maintaining selectors; costs you flexibility and trust in their extractor.
- Compute and scheduling: a place to run your own code (an Apify Actor, a hosted browser) so nothing runs on your laptop.

The line, so nobody has to rediscover it: public data only; copying what a real browser sends is fine; defeating anti-bot challenges, rotating identities or proxies to get past a block, or anything behind a login is not. A product whose headline feature is "we solve the challenge and rotate the identity for you" does exactly what this skill's rule forbids doing by hand, so buying it does not make it acceptable. What remains open to we is buying rendering, compute, parsing and search-result APIs for targets that permit access, and using a proxy pool where the publisher has consented in writing (the news publisher case).

## The general rule

A managed service is worth it when the target is a hard one you will scrape once (or rarely), because you are buying someone else's maintenance for a job whose lifetime is shorter than the maintenance you would write. Self-hosting is worth it when volume is high and the target is easy, because the managed price is per record forever and the self-hosted price is a one-off build plus a server that already exists. The break-even is not the sticker price: it is (records x price per record) against (your hours to build and repair + server time + the chance the run fails silently). Two things flip it early: a target that fights back (your repair hours grow) and a run that must finish tonight (your time to first data matters more than money).

## How to decide with a ten-cent sample and a hard spend ceiling

1. Write down the one thing the paid service must do that your free path cannot (a field that is absent, a page that will not render for you, a volume you cannot reach in time). If you cannot name it, do not buy.
2. Buy the smallest sample that can show it: 10 to 50 items, a small `num`, one area. On Apify pass a per-run maximum total charge. The Apify API documents `maxTotalChargeUsd` as capping "the total amount charged for all pricing models" (docs.apify.com, 21 Sep 2026).
3. Measure on the same ground as the free alternative. Comparing two tools on two different samples measures the samples: our first Maps comparison showed 72% against 28% phone coverage and was entirely a confound of different districts.
4. Compute cost per usable record from the bill, not from the price page, then extrapolate and set the ceiling near 1.5x the expected cost.
5. Read the row for your own tier and every add-on that bills per record.

Our own evidence: two paid tests cost $0.18 in total and redirected a $29 budget. Also from our notes: pay for what you do not have rather than improving what you have (a field absent from the free layer went from 0% to 55%; a field already present went from 36% to 40%), and test that a field is populated at the source before paying to enrich it.

---

### Apify (commercial platform; Actors written by Apify and by independent developers)
The open-source libraries around it, from the metadata table: crawlee-python (Python, Apache-2.0, 9k stars, last push 2026-09-21, not archived, v1.10.1 2026-09-16) and crawlee (TypeScript, Apache-2.0, 25k, last push 2026-09-21, not archived, v3.18.1 2026-08-12). Crawlee is covered in the frameworks category.
- **What it is:** a serverless platform that runs Actors (containerised programs) on demand. Every run gets a default dataset (append-only structured items, exportable as JSON, CSV, XML, Excel, HTML, RSS or JSONL) and a key-value store (docs.apify.com/storage/dataset). Reached from our machine through the Apify MCP tools (search-actors, fetch-actor-details, call-actor, get-actor-run, get-dataset-items, get-key-value-store-record, abort-actor-run, plus docs search). Named datasets are kept indefinitely, unnamed ones expire after 7 days (docs).
- **Best at:** paying for a finished, maintained scraper for a hard, shared target (Google Maps, social platforms, marketplaces) without owning a server. The Store search lets you find an Actor before writing code, and one call gives you a dataset you can page through.
- **Pricing mechanism:** pay per event. An event is an action the Actor charges for: a result, an Actor start (one event per GB of memory, minimum one), or an add-on. Each event has a tiered price for account tiers FREE, BRONZE, SILVER, GOLD, PLATINUM and DIAMOND. The headline price on a Store page is often the best tier, not yours. Verified 21 Sep 2026 with fetch-actor-details: scraperlink/google-maps-scraper is titled "$0.40/1K Results" but its BRONZE price is $0.0005 per result, $0.50 per 1,000; compass/crawler-google-places is $0.004, $0.003, $0.002, $0.0015, $0.00126, $0.000756 per place from FREE to DIAMOND. (check current pricing)
- **Limits and traps (measured by us):** compass bills an add-on per place for each filter applied ("Final price = places scraped x filter price x number of filters"), so category plus minimum stars plus has-website is three filters and roughly doubles the bill at BRONZE. scraperlink has no filter surcharge, but its bounding box does not confine results: a 5 x 5 km box with a 1 km grid returned 23 of 300 results inside the box, and a request for thousands of places timed out (num 5000 streamed nothing for 4 minutes, num 300 streamed 45 places in 43 s). A run reported SUCCEEDED with 0 items after a 504 from the Actor's own backend; read the item count and the ERRORS record. A page size is not the yield ("Fetched 93 of 100" was the page size, not the run's result). De-duplication happens within a run only: five runs over one area billed 1.61x, one run 1.00x.
- **Cost or risk:** you hand your query list to a third party's code that can change price, break, or vanish. Apify stops at the account's usage limit, not the prepaid balance, so a run without a charge cap can bill a card. We caps every run.
- **Reach for it when / not when:** reach for it for a hard target you need once, for targeted lookups with a small `num`, or when the free tool is too slow for tonight's deadline. Do not use an Apify grid to cover a whole city on a small balance, and do not use it for an easy target you will hit nightly (a plain API or curl_cffi costs nothing per record).
- **Versus:** Zyte, ScrapingBee and the others sell a fetch (you write the extraction); Apify sells a finished extractor for one site. Firecrawl sells page-to-markdown. The free counterpart for Maps is gosom (a binary already on the laptop).
- **Here:** default Google Maps actor is scraperlink (decision 13 Sep 2026): same phone coverage as gosom and compass on the same ground, at $0.50 against $3.00 per 1,000 places at BRONZE. Reviews and popularTimes stay off (each adds $0.25 per 1,000). Balance went $12 to $7 to about $6.3 across the schools work; every run carries a charge cap.

### Zyte API (commercial; Zyte, the company behind Scrapy, not on GitHub)
- **What it is:** one HTTP endpoint that fetches a URL either as a plain HTTP response or through a rendering browser, optionally returning automatically extracted fields.
- **Best at:** a priced-per-difficulty fetch. From the vendor docs (21 Sep 2026): pricing depends on target site and request type, sites fall automatically into one of five tiers per request type, browser features (actions, network captures, screenshots) cost extra, automatic extraction has per-data-type fees, "You are only charged for successful responses. Rate-limiting and unsuccessful responses are free", and volume commitments discount by 25 to 52%.
- **Limits and traps:** the tier is assigned to you, not chosen ("New combinations start with a temporary tier until enough data is gathered"), so the price of a new site is a surprise until you meter it. Extraction is their model of the page. (check current pricing)
- **Cost or risk:** per successful response, so a hard site costs more per page than an easy one. Integration with Scrapy exists through a Zyte-published plugin (unverified). Where the tier is high because the site actively blocks, you are buying unblocking, and this skill's line above applies.
- **Reach for it when / not when:** when you need reliable rendering or extraction on a target with many pages and no consent to worry about. Not for an easy API you can call yourself.
- **Versus:** ScrapingBee and ScraperAPI use credit multipliers you choose per request; Zyte assigns a price tier by site and bills only successes. Bright Data leads with the unblocker and proxy network.

### Bright Data (commercial, not on GitHub)
- **What it is:** a proxy network with a product family on top. From the docs page fetched 21 Sep 2026: Web Unlocker is a single endpoint that "handles proxy rotation, anti-bot challenges and CAPTCHA solving in 1 call", returns HTML or JSON, and charges "only for successful requests to your target domain"; it is not for scripted browser actions and search queries go to a separate SERP API. Also sold: residential and datacenter proxies billed by data volume, a hosted scraping browser, and ready-made datasets (unverified).
- **Best at:** getting a response from a target that refuses ordinary clients, and buying finished datasets so you never scrape.
- **Limits and traps:** the product is challenge-solving and identity rotation, which is precisely what this skill does not do to get past a block. The docs quote a 98% success rate; that is the vendor's own claim, not measured here.
- **Cost or risk:** per successful request or per GB (check current pricing). Proxy-network sourcing and a vendor's terms about targets are risks to read before use (unverified).
- **Reach for it when / not when:** only for targets where access is permitted and the block is incidental (for example a CDN that rejects datacenter ranges) and a written go-ahead exists. Not as a way past a refusal the site meant.
- **Versus:** Zyte prices by tier and difficulty; ScrapingBee and ScraperAPI are smaller, credit-based and simpler.

### ScrapingBee (commercial, not on GitHub)
- **What it is:** one API call that returns a page, with options for rendering and proxy class, priced in credits.
- **Best at:** small jobs where you want to pay a known multiplier. From the docs fetched 21 Sep 2026: a basic request is 1 credit, JavaScript rendering (on by default) is 5, a premium proxy without rendering is 10, with rendering 25, a stealth proxy (needs rendering) is 75. `mode=auto` tries configurations from cheapest to most expensive and charges only the one that succeeds; a failed auto request costs 0; `max_cost` caps it; the spent cost is returned in the `Spb-auto-cost` header.
- **Limits and traps:** rendering is on by default, so an unattended call to an easy static page costs 5 credits rather than 1 until you turn it off. The 75-credit stealth class is an identity-evasion product (firm line). Credit prices per plan change. (check current pricing)
- **Reach for it when / not when:** a few hundred to a few thousand pages, render needed, no server. Not for a static site or JSON API (use plain HTTP), and not for 100,000+ pages where a multiplier dominates (unverified as a rule of thumb; do the arithmetic on your own volume).
- **Versus:** ScraperAPI is the same shape with different multipliers (I could not read its multiplier page: unverified); Zyte bills per success by site tier.

### ScraperAPI (commercial, not on GitHub)
- **What it is:** a credit-priced fetch API with options for rendering, premium residential proxies and country targeting (unverified). I could not retrieve its billing page on 21 Sep 2026, so multipliers and failed-request policy are unknown to me.
- **Best at:** same job as ScrapingBee: one URL in, page out.
- **Limits and traps:** credit costs per option and per certain domains may differ from the headline; read the billing page first. (check current pricing)
- **Reach for it when / not when:** as a second quote when pricing ScrapingBee. Not preferred over Zyte where you want per-success billing.
- **Versus:** ScrapingBee, Zyte, Bright Data as above.

### Oxylabs (commercial, not on GitHub)
- **What it is:** a proxy network company with a Web Scraper API (rendering, parsing, source-specific parsers) and search-oriented APIs (unverified; the docs page I tried returned 404, so I have no verified mechanism).
- **Best at:** the same class as Bright Data, positioned at enterprise scale (unverified).
- **Limits and traps:** same firm-line issue as any unblocker. Residential proxy sourcing is a diligence question (unverified).
- **Reach for it when / not when:** rarely, for our volumes and rule. Included for completeness so a vendor pitch can be placed.
- **Versus:** Bright Data (nearly the same product family), Zyte (priced by site tier).

### SerpAPI and Serper (commercial search-result APIs, not on GitHub)
- **What it is:** an API that returns Google (and other engine) results as structured JSON so you do not scrape the search page. From serper.dev (21 Sep 2026): endpoints for search, images, news, maps, places, videos, shopping, scholar, patents and autocomplete; credit per query; "2,500 free queries" without a card. The page showed no per-query price (check current pricing). SerpAPI is the older service with many engines and per-search plans (unverified).
- **Best at:** getting ranked results, place listings and news for a query list cheaply and cleanly, with country and language parameters. For Iraq work set the country and language deliberately.
- **Limits and traps:** you get Google's ranked view for that query and locale on the day, not a complete index. Coverage of Iraqi businesses in a places endpoint is a property of Google's data (we measured phone coverage as a property of the neighbourhood, not the tool). Google's terms on automated querying are a risk the service either absorbs or passes to you (unverified).
- **Reach for it when / not when:** discovery of URLs and names, rank tracking, a few thousand queries. Not for completeness, and not when an official API or a free source answers the question.
- **Versus:** Apify Maps actors return place records with fields; Serper's places and maps endpoints return search-shaped results.

### Firecrawl cloud and the firecrawl repo (TypeScript, AGPL-3.0, 182k stars, last push 2026-09-21, not archived, latest release v2.11.0 2026-06-19)
- **What it is:** an API that scrapes or crawls a URL and returns clean markdown or structured data. Open source (the repo) plus a hosted service; the README says the SDKs and some UI components are MIT and the rest AGPL-3.0.
- **Best at:** turning pages into LLM-ready markdown at scale with no parser of your own. Cloud billing verified from docs.firecrawl.dev/billing (21 Sep 2026): scrape and crawl are 1 credit per page, search is 2 credits per 10 results, JSON (LLM extraction) adds 4 per page, zero data retention adds 1, and "Firecrawl returned a document: 1 credit per page ... regardless of HTTP status codes returned by the target site". No document means 0 credits.
- **Limits and traps:** a blocked page that Firecrawl returns as a document is billed. Self-hosting is not the same product: the docs list Fire-engine (their advanced anti-bot layer), screenshots and page actions, several specialised formats and proxy/anti-bot services as missing from the default self-hosted stack. AGPL means offering a modified version to others over a network triggers a source-sharing duty; internal use is the common case but read the licence before embedding it in a client-facing service (unverified legal reading).
- **Cost or risk:** credits (check current pricing). Stars are enormous (182k) and say nothing about fit; the metadata table shows a fast-moving project.
- **Reach for it when / not when:** when the output you want is markdown for reading or an LLM, over many arbitrary sites. Not when you need every record's exact fields from one known site (a targeted extractor is cheaper) or when the site is an API in disguise.
- **Versus:** trafilatura and Crawl4AI (other categories) do extraction locally for free; Firecrawl cloud adds fetching infrastructure you pay for.

### Browserbase and Stagehand (Browserbase: commercial; Stagehand: TypeScript, MIT, 24k stars, last push 2026-09-20, not archived, @browserbasehq/stagehand@3.7.3 2026-08-28)
- **What it is:** Browserbase rents remote headless browsers with isolated sessions. Its docs (21 Sep 2026) also list web search and fetch, functions, a model gateway, and "agent identity solutions" through partnerships to get past anti-bot and authentication. Stagehand is their open-source SDK that adds natural-language selectors and self-healing on top of a browser session.
- **Best at:** running many parallel browsers without operating them, and letting an LLM drive a page that changes shape.
- **Limits and traps:** the fetched docs page did not state how billing is metered (check current pricing). Browsers run in a cloud region, which may matter for geo-restricted Iraqi sites (unverified). The identity and anti-bot features are outside this skill's line. A remote browser is still a browser: it costs seconds per page.
- **Reach for it when / not when:** when you need dozens of concurrent real browsers for a few hours. Not for one-off page reading (the local browser tools already installed cover that) and not for sites you can call by JSON.
- **Versus:** local Playwright on our server is free but you keep it patched and cap it by CPU (the gosom scraper saturated at 6 workers on 8 cores). Browserbase trades money for that operations burden.

---

# B. Storage formats and their failure modes

Rule that follows from every entry below: write raw output in a format that a kill cannot ruin, then convert once, after the run, into the format a reader wants. Decide by what a killed process leaves behind.

### JSONL (plain text, one JSON object per line)
- **What it is:** a text file where each line is one record; the writer appends and flushes.
- **Best at:** surviving kills. Measured: a 5-line file cut mid-line kept 4 records with a tolerant reader (`try: json.loads(line) except: skip`); no earlier line is disturbed. Our rule: plain JSONL flushed periodically, compress after the run.
- **Limits and traps:** no types beyond JSON's, and appends duplicate on re-runs, so dedupe by key when reading (resume by unit, not by position). Use `ensure_ascii=False` for readable Arabic and always open with `encoding="utf-8"` on Windows: the default console and file encoding here is cp1252, and printing Arabic raised UnicodeEncodeError during this very session. A stricter reader fails on the truncated tail: DuckDB `read_json_auto` on a file whose last line was cut raised "Malformed JSON ... unexpected end of data", and with `ignore_errors=true` it returned the good rows plus one row of all NULLs for the bad line (verified), which then poisons counts.
- **Cost or risk:** large (235.8 MB for 1M rows of nine columns in my test against 21.4 MB as Parquet). Two writers to one file can interleave partial lines (unverified), so use one writer per file.
- **Reach for it when / not when:** the raw landing format of every long or killable run. Not as a delivery format.
- **Versus:** SQLite gives transactions and dedupe at the cost of one writer and a binary file; CSV needs quoting care.
- **Here:** the archive's `metrics.jsonl` held every run, not every night, and produced a false volume alert (21 Sep); the fix was one record per date. Append-only files record events, so the reader must define which events count.

### gzip and framed compression (gzip, and by the same mechanism zstd frames)
- **What it is:** a deflate stream with a CRC and length trailer at the end. Concatenated members are valid.
- **Best at:** small archives (about 4 to 10x on repetitive text, unverified) once the run is finished.
- **Limits and traps:** a kill leaves a stream without its trailer. Measured with Python's gzip on 20,000 lines: cut in half, line iteration returned 9,942 lines and then raised `EOFError`; with only the last 8 bytes missing, all 20,000 lines came back and then `EOFError`. But `.read()` raised with nothing returned, so a naive loader gets zero rows, and data still sitting in the writer's buffer at kill time is gone. Appending with `gzip.open(path, "ab")` writes each call as its own member and reads back as one stream (verified); with the last member cut, iteration returned 4,996 of 5,000 lines. So the truncation costs you the unflushed tail plus whatever reader you choose to trust. We lost 13,000 records when a compressed append-only file was killed mid-write.
- **Cost or risk:** you cannot inspect it with `tail` and `wc -l`, which is how we watches progress on an append-only file.
- **Reach for it when / not when:** compress finished files, or write one small gzip file per unit. Not as the live append target of a long run.
- **Versus:** plain JSONL loses one line; gzip loses the buffer and can fail a strict reader.
- **Here:** Our collector design flushes every 100 records; after two SIGKILLs on 11 Sep the gzip was intact and text files ended on complete lines.

### CSV
- **What it is:** delimited text; no schema, no types.
- **Best at:** the universal exchange format and a good server-side master (we keep the CSV as master and delivers xlsx).
- **Limits and traps:** Excel needs a byte-order mark to read Arabic as UTF-8: write with `encoding="utf-8-sig"` (pandas `to_csv(..., encoding="utf-8-sig")` writes bytes EF BB BF, verified). Types are guessed by the reader: pandas read a column containing 01 and 06 as the integers 1 and 6 (verified), and our Google Sheets seed from a csv did the same to model names (`07` became 7). Embedded newlines need `newline=""` and a real CSV writer. A file written on Windows has CRLF line endings: our seed id file with CRLF made `grep -E "^[0-9]+$"` match nothing and a merge silently kept 25 ids while reporting success.
- **Cost or risk:** 145.8 MB for 1M rows against 21.4 MB Parquet in my test; a read of the CSV took 3.44 s in pandas.
- **Reach for it when / not when:** server master, exchange with tools that accept only text. Not for anything with identifiers that look like numbers unless every reader is told the dtype.
- **Versus:** xlsx carries types; Parquet carries types and is far smaller.

### xlsx via openpyxl or xlsxwriter
- **What it is:** a zip of XML. openpyxl reads and writes; xlsxwriter only writes and is built for large outputs.
- **Best at:** the deliverable a colleague opens. It keeps each cell's type, so `01` stays text; it can freeze the header and set a filter. We decided on 13 Sep to deliver xlsx to Drive for exactly this reason.
- **Limits and traps (all measured 21 Sep 2026, openpyxl 3.1.5, xlsxwriter 3.2.9):** openpyxl raises `IllegalCharacterError` for a control character such as `\x0b` in a cell; xlsxwriter accepts it and stores it escaped as `_x000B_`. Excel's cell holds 32,767 characters: openpyxl saved a 40,000-character string without any error and it read back as 32,767, so text is silently truncated; xlsxwriter's `write_string` returns -2 for an over-long string and does not raise, so check return codes or pre-truncate on purpose. xlsxwriter's `write()` kept `"01"` as text, but the option `strings_to_numbers=True` turned it into the number 1. Digit strings lose their leading zeros whenever any step re-types them by value (Excel opening a CSV, Sheets `setValues`, a writer told to convert). An Excel sheet holds 1,048,576 rows (unverified from memory), and a 52-column, 700,000-row file is large: our rebuilt workbook is 220 MB and takes about 7 minutes.
- **Cost or risk:** slow and heavy compared with Parquet; not appendable.
- **Reach for it when / not when:** delivery to people who will open it. Not for storage, and not as the only copy.
- **Versus:** openpyxl edits existing workbooks; xlsxwriter writes new ones faster and has a low-memory mode (unverified).
- **Here:** build_year_xlsx.py types by column (quantities and ids as numbers, true/false as booleans, everything else text). 65 car models named 01, 06, 07 stayed intact in the rebuild; 37 rows in the live Sheet still read 1, 6, 7.

### SQLite (stdlib module; server-less database file)
- **What it is:** a transactional database in one file, bundled with Python. Python 3.12.4 on the laptop reports SQLite 3.45.3 (verified).
- **Best at:** resumable state and dedupe: primary key with `INSERT OR IGNORE`, a status column for pending/done/failed, atomic commits so a kill loses at most the current transaction (documented behaviour, unverified here). Write-ahead logging switched on with `PRAGMA journal_mode=wal` (verified), so readers do not block the writer. The default `synchronous` here was 2 (FULL) (verified).
- **Limits and traps:** one writer at a time; a second writer waits or errors. Keep it on a local disk, not a synced folder or share (locking, unverified). No native array type. Commit in batches, not per row, or a big backfill crawls (unverified).
- **Cost or risk:** none; public domain (unverified).
- **Reach for it when / not when:** the ledger of a long job (what is done, failed, retried) and mid-size datasets you query. Not for a hundred million rows of analytics or many concurrent writers.
- **Versus:** JSONL is simpler and more kill-tolerant for raw capture; DuckDB is better for analytics over big files.

### DuckDB (C++, MIT, 41k stars, last push 2026-09-21, not archived, latest v1.5.5 2026-07-22; laptop has 1.5.4)
- **What it is:** an in-process analytical SQL engine that reads files directly (CSV, JSONL, Parquet) and remote Parquet.
- **Best at:** questions over files that are too big for comfortable pandas, without loading them. Measured on the 236 MB, 1M-row JSONL: a group-by straight from the file took 0.99 s. It also queried Overture Maps Parquet on S3 with a bounding box and returned in 38 s without downloading the dataset.
- **Limits and traps:** one process at a time may open a database file for writing: a second process got `IOException ... being used by another process` (verified on Windows). Reading a truncated JSONL is strict (see above). It is columnar and built for batches, not for many single-row inserts.
- **Cost or risk:** MIT; new minor versions arrive often, so pin a version in a scheduled job.
- **Reach for it when / not when:** ad hoc analysis, converting JSONL to Parquet (`COPY (SELECT ...) TO 'x.parquet' (FORMAT parquet)` worked), spatial and remote queries. Not as the live database a nightly job appends to from several processes.
- **Versus:** SQLite for transactional state; polars and pandas when you want dataframes in Python.

### Parquet (columnar file format; pyarrow 25.0.1 on PyPI, 21.0.0 on the laptop)
- **What it is:** a typed columnar file with compression and a metadata footer.
- **Best at:** analysis and archives. My 1M-row test: 21.4 MB against 145.8 MB CSV and 235.8 MB JSONL; pandas read it in 1.06 s against 3.44 s for the CSV. Types survive, including strings that look like numbers.
- **Limits and traps:** the footer is written last, so a truncated Parquet file is unreadable (pyarrow raised `ArrowInvalid ... Could not read schema` on a copy with 1,000 bytes cut off). It is not appendable: write a new part file per batch or per night and read the folder. Do not write it live in a run that gets killed.
- **Cost or risk:** none; you need pyarrow or DuckDB or polars to read it.
- **Reach for it when / not when:** the after-the-run conversion of raw JSONL, and the archive of record for a night's capture. Not as a live append target.
- **Versus:** CSV (text, no types), xlsx (delivery), SQLite (mutable state).

### pandas 3.0.6 (Python, BSD-3-Clause, 49k, last push 2026-09-21) versus polars 1.44.2 (Rust, MIT, 39k, last push 2026-09-21)
- **What it is:** two dataframe libraries. pandas is the ecosystem default (Excel, plotting, statistics); polars is a multi-threaded engine with a lazy mode.
- **Best at (measured here, 1M rows x 9 columns, 235.8 MB JSONL with Arabic strings, one run each, so read the ratios, not the digits):** reading the JSONL: pandas `read_json(lines=True, dtype=False)` 23.6 s, polars `read_ndjson` 0.70 s, polars lazy `scan_ndjson` with a group-by 0.40 s, DuckDB group-by from the file 0.99 s. The group-by itself on loaded data was 0.11 s in pandas and 0.05 s in polars, so on this size the difference is the reader, not the analysis. In-memory size: pandas 152 MB, polars estimated 119 MB (different estimators). pandas 3.0 gives strings the `str` dtype by default (verified on 3.0.5).
- **Limits and traps:** polars is not installed on the laptop and its API differs from pandas enough that code does not transplant. pandas is where `to_excel`, `read_excel` and most tutorials live. Both need explicit dtypes for identifier columns (`dtype=str` in pandas, `schema_overrides` in polars (unverified name)), or 01 becomes 1.
- **Cost or risk:** polars requires Python 3.10 or newer, pandas 3.0 requires 3.11 or newer (PyPI, 21 Sep 2026); the laptop's 3.12.4 satisfies both.
- **Reach for it when / not when:** polars to read large JSONL or Parquet and aggregate; pandas for Excel I/O and small to medium tables. Below about a million rows either works; the choice is the reader.
- **Versus:** DuckDB does the same reading in SQL and needs no dataframe at all.

### Google Sheets pushed through Apps Script
- **What it is:** a script bound to a Sheet, deployed as a web app, that receives a POST and writes rows with `setValues`.
- **Best at:** giving non-technical colleagues a live view of a nightly capture with no server of theirs.
- **Limits and traps:** it is slow. Our push takes about 60 seconds before Apps Script answers (51 s at 197K rows on 9 Sep, about 60 s at 205K), and on 17 Sep the `ids` call returned HTTP 404 three times running; a rerun an hour later worked. We raised retries to 5 with backoff 30, 60, 120, 240 seconds (about eight minutes), because a failed night heals on the next push. Vendor limits (fetched 21 Sep 2026): a script may run 6 minutes per execution for both consumer and Workspace accounts, and trigger runtime is 90 minutes a day (consumer) or 6 hours (Workspace). A spreadsheet holds 10 million cells or 18,278 columns, and cells over 50,000 characters are removed when converting an Excel file. At 52 columns, 10 million cells is about 192,000 rows (my arithmetic), so a wide archive must be split by year or trimmed to fewer columns. `setValues` parses digit strings, so `07` becomes 7 unless the columns are formatted as text first. A sheet can also be edited by hand: we found 986 rows with no numeric id that the push never writes.
- **Cost or risk:** free, but the sheet is a shared surface anyone can change, so it is a view, not a master.
- **Reach for it when / not when:** small, human-facing output. Not as the store of record, and not for a job that cannot tolerate a 60 s call failing.
- **Versus:** an xlsx or CSV delivered as a file keeps types; Sheets guesses.
- **Here:** push_sheet.py types by value and Code.gs does not set text formatting, which is the open fix for the leading-zero rows.

### When to keep raw HTML or JSON beside the extracted records
- **Keep it when:** extraction may change or was wrong (the used-car site detail page moved from the Next.js pages router to the app router on 16 Sep; a saved copy would have let the new parser be checked against the old pages), when the source can disappear (listings withdrawn between two runs), when a field turns out to be needed later, and when a dispute about "what did the page say" is possible.
- **Skip it when:** it is large and re-fetchable at low cost, when it holds personal data you do not need (phone numbers, names) and no purpose justifies keeping it, or when the API response is already the record.
- **How:** raw beside parsed, one file per unit or one JSONL of responses, compressed after the run; keep discovery output, per-item progress and results in separate places so bad state can be deleted without repaying for discovery. Sizes are a decision: our list snapshot is about 36 MB a night (13 GB a year on a 96 GB disk), while one 170 KB detail page times about 900 a night is roughly 150 MB uncompressed (my arithmetic, whether the pages are kept is not recorded in the notes I read).

---

# C. Orchestration and reliability

### systemd timers (Linux; the server's scheduler)
- **What it is:** a `.timer` unit that starts a `.service` unit.
- **Best at:** unattended nightly jobs with catch-up and logging. Verified from the systemd manual (github.com/systemd/systemd man pages, 21 Sep 2026): `Persistent=` stores the last trigger time on disk and, when the timer is activated, triggers immediately if it would have fired while inactive; it only affects `OnCalendar=` timers; and if the service is already active when the timer elapses it is not restarted ("simply left running"). Zone in the expression, as we use: `OnCalendar=*-*-* 00:00:00 Asia/Baghdad` on a UTC host (in production on Ubuntu 24.04).
- **Limits and traps:** `Type=oneshot` keeps the unit "activating" until ExecStart exits and its start timeout is disabled by default (both from the manual). Our sweep ran 23.5 hours as a oneshot; on 11 Sep a needrestart after a glibc upgrade waited on it, and `apt` held `dpkg/lock-frontend` for hours and blocked another project's deploy. Prefer `Type=simple` or `exec` for long windows, or a timer that starts short units. For stopping: `KillMode=mixed` sends SIGTERM (or `KillSignal=`) to the main process only and SIGKILL to the rest after the stop timeout (manual). A wrapper shell waiting on a foreground command does not forward that signal, so the collector never heard it, systemd waited 5 minutes and killed everything, twice on 11 Sep. `KillSignal=SIGINT` on the unit plus a wrapper that runs the collector in the background and traps the stop fixes it. `Conflicts=` is the backstop, not the plan. `OnFailure=` reports a wrapper killed before it could report on itself.
- **Cost or risk:** none; the accuracy default and randomised delay can move a start by seconds to a minute (unverified). `systemd-analyze calendar "<expr>"` prints when an expression next fires (unverified).
- **Reach for it when / not when:** anything on the server. Not on the Windows laptop.
- **Versus:** cron has no catch-up and no built-in overlap guard; Task Scheduler is the Windows counterpart.
- **Here:** Our nightly job runs at 00:00 Baghdad with `Persistent=true`; the sweep at 00:40 with a stop at 23:30 sent as SIGINT by `timeout --signal=INT`; a 23:30 stop leaves the half-hour before the midnight job so both never need the same 38 proxies.

### cron (Unix)
- **What it is:** a per-minute scheduler reading crontab lines.
- **Best at:** very simple recurring jobs on any Unix box.
- **Limits and traps (all unverified):** if the machine is off at the scheduled minute the run is skipped (anacron exists for that); it runs with a minimal environment and PATH, so scripts that work in a shell fail; the time zone is the host's; no overlap protection unless you wrap the job in `flock`; output goes to mail unless redirected.
- **Cost or risk:** none.
- **Reach for it when / not when:** a throwaway job you do not need catch-up for. Not when a missed night matters.
- **Versus:** systemd timers give `Persistent=`, a named zone, journal logs and `OnFailure=`.

### Windows Task Scheduler and keeping a laptop awake
- **What it is:** the OS scheduler (schtasks, or PowerShell `Register-ScheduledTask`).
- **Best at:** starting a job on a laptop at a time or a logon.
- **Limits and traps (measured 21 Sep 2026 with `New-ScheduledTaskSettingsSet`, the defaults for a PowerShell-created task):** `DisallowStartIfOnBatteries` True and `StopIfGoingOnBatteries` True, `StartWhenAvailable` False (no catch-up after a missed start, the counterpart to `Persistent=true`), `WakeToRun` False, `ExecutionTimeLimit` PT72H, `MultipleInstances` IgnoreNew. So a laptop job on battery does not start, or is stopped when unplugged, and a missed start is skipped until you turn `StartWhenAvailable` on. Task Scheduler stops a task by terminating it rather than sending a catchable signal (unverified), so design for a hard kill: append-only files and resume by unit. To hold the machine awake from Python, `SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)` through `ctypes` runs and returns the previous state (verified callable); `powercfg /requests` needs an administrator prompt (verified refusal). Closing the lid may still sleep the machine depending on power settings (unverified). Files under the OneDrive Desktop and Documents folders are synced: we found two zips that failed to send left as 22-byte empty archives inside the OneDrive folder (cause not proven), so keep large live outputs on a non-synced path (inference, unverified).
- **Cost or risk:** our skill says preventing sleep is the commonest cause of failed overnight runs on a laptop.
- **Reach for it when / not when:** a job that must run on the laptop for its data or its residential IP. Anything that runs nightly or for hours belongs on the server.
- **Versus:** systemd timers on the server; a tmux session for a one-off.

### Prefect (Python, Apache-2.0, 23k stars, last push 2026-09-20, not archived, latest 3.8.6 2026-09-14)
- **What it is:** a Python orchestrator: decorate functions as `flow` and `task`, then `flow.serve(...)` starts a long-lived process that runs scheduled deployments; activity is tracked on a self-hosted Prefect server or Prefect Cloud (README).
- **Best at:** retries, scheduling, run history and a UI around ordinary Python with little ceremony.
- **Limits and traps:** you now operate a scheduler process and its server or pay for cloud; it needs Python 3.10 to below 3.15 (PyPI). Pinning is needed because the API moves.
- **Cost or risk:** open source; cloud tier prices (check current pricing).
- **Reach for it when / not when:** several dependent steps, many owners, a need for a run UI. Not for one nightly job on one server: systemd already gives schedule, catch-up, logs and failure hooks.
- **Versus:** Airflow is heavier and Linux-only; Dagster models data assets rather than tasks.

### Airflow (Apache Airflow; Python, Apache-2.0, 46k stars, last push 2026-09-21, not archived, latest 3.3.2 2026-09-17)
- **What it is:** a DAG scheduler with a metadata database, web server, scheduler and workers.
- **Best at:** large fleets of scheduled pipelines with dependencies, backfills and operators for many systems.
- **Limits and traps:** verified in its README: it runs on POSIX systems; on Windows use WSL2 or Linux containers, and Windows support "is not a high priority". Only Linux distributions are recommended for production. Several services to keep alive, each a failure mode.
- **Cost or risk:** open source; operational weight.
- **Reach for it when / not when:** a data team with tens of pipelines. Not for a fifteen-person research firm with a few nightly captures.
- **Versus:** Prefect is lighter; systemd is lighter still.

### Dagster (Python, Apache-2.0, 16k stars, last push 2026-09-18, not archived, latest 1.13.23 2026-09-16)
- **What it is:** an orchestrator built around declared data assets ("define the assets you want to build as Python functions", README) with lineage and observability.
- **Best at:** keeping derived tables fresh and showing what depends on what.
- **Limits and traps:** you must adopt its asset model; a service and a UI to run.
- **Cost or risk:** open source.
- **Reach for it when / not when:** a warehouse of derived tables with many dependencies. Not for capture jobs whose whole point is to survive being killed.
- **Versus:** Prefect is task-shaped; Airflow is DAG-shaped.

### Healthchecks and dead-man switches (healthchecks: Python, BSD-3-Clause, 10k stars, last push 2026-09-14, not archived, latest v4.4 2026-08-31)
- **What it is:** a service that listens for pings from jobs and alerts when a ping does not arrive. Open source (Django, PostgreSQL/MySQL/MariaDB per its README) and hosted at healthchecks.io.
- **Best at:** the failure a job cannot report itself: the box is dead, the timer never fired, the network is down. From the docs (21 Sep 2026): the job calls a ping URL; `/start` marks a start, `/fail` a failure, `/<exitcode>` an exit status; a check has a period and a grace time (or a cron expression), goes "late" then "down" after the grace time.
- **Limits and traps:** the monitor must live off the machine it watches. Ping at the end, after the output is validated, not at the top. A job that finishes but writes garbage still pings green: pair it with content checks (volume against the same weekday, fields still present). Self-hosting gives you another service to watch; the hosted plan has limits (check current pricing).
- **Cost or risk:** BSD-3-Clause; the ping URL is a secret-ish identifier.
- **Reach for it when / not when:** any scheduled job where silence is the failure. Not as the only alert, since it says "late", not "why".
- **Versus:** a Telegram alert speaks when something fails inside the job; a dead-man switch speaks when nothing does.
- **Here:** the nightly capture is silent on a good night by design, so it needs something to notice absence. Its alert list includes "never started" but the mechanism is not recorded in the notes I read; I did not find a healthchecks service in them.

### Telegram bot alerts
- **What it is:** an HTTP call to the Bot API `sendMessage` or `sendDocument`.
- **Best at:** an alert to a phone in seconds, with a log attached, no infrastructure.
- **Limits and traps:** from the Bot FAQ (21 Sep 2026): about one message per second per chat, 20 per minute in a group, about 30 per second for bulk, bots upload files up to 50 MB and download up to 20 MB, and excess returns 429. The token is a secret: keep it in a mode-600 file, never in scripts. A message text limit of 4,096 characters is from memory (unverified). An alert path that fails silently is not an alert: our wrapper checks the notifier's exit code and falls back to a raw `curl`, "which happened, it was not hypothetical".
- **Cost or risk:** free; depends on Telegram being reachable from the server and on one bot account.
- **Reach for it when / not when:** short alerts with an attached log. Not for moving data.
- **Versus:** email is slower to notice; healthchecks adds absence detection.
- **Example:** a Telegram bot for alerts, with credentials in a mode-600 file, never in a script. Nine named hard failures in plain language (never started, list API unreachable, canary failed, every detail request refused, capture failed, run cut short, detail pass struggling, live count moved sharply, table not rebuilt), two quiet-failure checks (a field the site stopped sending, volume outside normal), silent on a good night.

### Docker
- **What it is:** containers: an image with the runtime and dependencies, run isolated.
- **Best at:** a repeatable environment on the server, and packaging a collector for another machine.
- **Limits and traps (all unverified, from memory):** `docker stop` sends SIGTERM and after a default 10 seconds SIGKILL, so a collector that only handles SIGINT never drains: set `--stop-signal`, `--stop-timeout` or the compose equivalent, and use `--init` or `exec` so the signal reaches your process rather than a shell (the same lesson as `KillMode=mixed`). Data written inside the container layer is lost with the container: mount a volume. Docker Desktop on Windows carries licence conditions for larger companies; check the current terms for a firm of about fifteen.
- **Cost or risk:** another layer to keep patched; a venv was enough here.
- **Reach for it when / not when:** when the environment is fragile or the job moves between machines. Not when a venv and systemd already work.
- **Versus:** a venv plus a systemd unit (what we use).
- **Here:** no Docker use appears in the notes I read; a nightly job runs from a virtualenv under systemd.

### tmux, nohup and setsid
- **What it is:** ways to keep a process running after your SSH session ends.
- **Best at:** a one-off long run on the server (unverified for each): `nohup` ignores SIGHUP and writes to nohup.out; `tmux` keeps a terminal you can reattach; `setsid` starts a process in its own session detached from the terminal.
- **Limits and traps:** none survive a reboot, none restart a crashed job, and none give catch-up. The command must be resumable, log to a file, and write a state file. Output that goes only to the terminal is lost.
- **Cost or risk:** none.
- **Reach for it when / not when:** a job that will run once for hours. Not for anything recurring, which belongs to a timer.
- **Versus:** systemd, which restarts, schedules and logs.
- **Here:** long jobs on the server run under systemd; hand-run jobs use the same resumable command so re-running is always the recovery.

---

# D. Support libraries

### tenacity (Python, Apache-2.0, 8k stars, last push 2026-09-01, not archived; GitHub release 9.2.0 dated 2026-08-05, but PyPI's latest is 9.1.4 dated 2026-02-07, so pip does not yet show the newer tag)
- **What it is:** a decorator and context manager for retrying with stop, wait and retry conditions, for sync and async code.
- **Best at:** replacing hand-written retry loops with declared policy. Measured: by default it retries forever with no wait (README); with `stop_after_attempt(3)` a persistent failure raises `RetryError` wrapping the last exception, and with `reraise=True` it raises the original `ValueError` (verified 21 Sep 2026). `wait_exponential_jitter` exists in the installed 9.1.4 (verified).
- **Limits and traps:** it retries any `Exception` unless you say which (`retry_if_exception_type`), so a bug or a 404 is retried like a timeout. Retrying a non-idempotent request repeats its effect. A retry storm multiplies your request count against a rate limit, so pair it with a limiter and a server-sent Retry-After where available. Ambiguous answers (a 200 with the wrong content type) need a classifier before the retry, not after.
- **Cost or risk:** small, Apache-2.0.
- **Reach for it when / not when:** wrapping calls to a flaky API. Not as the whole reliability plan, and not around a fetch whose failure means "blocked, stop".
- **Versus:** urllib3's Retry and Scrapy's retry middleware retry at the transport level, tenacity at your function's level; our guarded_get retries the ambiguous answer once and then classifies it.

### aiolimiter (Python, MIT, 780 stars, last push 2026-09-21, not archived, v1.3.0 2026-09-07)
- **What it is:** an asyncio rate limiter (leaky bucket). `AsyncLimiter(100, 30)` allows up to 100 entries in a 30-second window (README).
- **Best at:** capping requests per period in an async crawler with a few lines.
- **Limits and traps:** verified in the source docstring: "up to `max_rate` acquisitions are allowed within this time period in a burst", so it starts with a full burst; we measured the same for its own token bucket (107 a minute against 80 configured in a 67-second test) and uses `smooth=True` for fragile servers. It limits rate, not concurrency: pair it with a semaphore. One event loop only, no cross-process sharing.
- **Cost or risk:** MIT; Python 3.10 or newer.
- **Reach for it when / not when:** a single asyncio process. Not for threads (use a thread-safe limiter), multiple processes, or several concurrent rates.
- **Versus:** PyrateLimiter handles several rates, per-key limits and shared backends.

### PyrateLimiter (Python, MIT, 523 stars, last push 2026-09-01, not archived, v4.5.0 2026-08-30)
- **What it is:** a rate limiter with pluggable algorithms (sliding-window log by default, fixed window, GCRA or token bucket) and backends: in-memory, SQLite, Redis, Postgres, multiprocess (README).
- **Best at:** multiple rates at once (for example 5 per second and 1,000 per hour), per-key limits, and sharing a limit across processes or restarts, in sync and async code.
- **Limits and traps:** v4 has breaking changes from v3 (the README points to a migration guide), so v3 snippets fail. Python 3.10 or newer.
- **Cost or risk:** MIT; small project.
- **Reach for it when / not when:** a per-host, multi-rate or multi-process crawler. Not for a single loop that needs one number.
- **Versus:** aiolimiter is simpler and async-only; our scrapekit RateLimiter also offers a process-wide `pause_all` on a 429.

### requests-cache (Python, BSD-2-Clause, 1k stars, last push 2026-09-19, not archived, GitHub v1.3.0 2026-02-02, PyPI 1.3.3)
- **What it is:** a `CachedSession` that extends `requests.Session` and stores responses, in SQLite by default (README).
- **Best at:** developing a parser against saved pages without re-hitting the site, and polite re-runs. Options from the README: `expire_after`, `cache_control`, `allowable_codes`, `allowable_methods`, `match_headers`, `stale_if_error`.
- **Limits and traps:** it works by patching `requests.Session` (compatibility docs), so a curl_cffi or httpx client is not covered by it (unverified for those two). Only certain status codes are cached by default (the README example widens them, so the default is narrower: unverified which). A cached block page served for days looks like a working site. It keys on method and URL, not on headers, unless you set `match_headers`.
- **Cost or risk:** BSD-2-Clause; slows nothing, but stale data is the danger.
- **Reach for it when / not when:** iterating on extraction, or a slow rebuild that reuses fetched pages. Not in a freshness-critical capture, and not with TLS-impersonating clients.
- **Versus:** diskcache is a general store you call yourself; keeping raw files beside records is a deliberate archive, a cache is disposable.

### diskcache (Python, licence shown NOASSERTION in the table but Apache-2.0 per its README and PyPI, 2k stars, last push 2024-08-10 (over two years before 21 Sep 2026), not archived, no GitHub release, PyPI 5.6.3)
- **What it is:** a disk and file backed cache, thread-safe and process-safe (README), implemented over SQLite and files with no server.
- **Best at:** persistent memoisation of expensive results and a shared seen-set across restarts. Also queue-like and dict-like structures (unverified detail).
- **Limits and traps:** maintenance is quiet: no push for over two years, so treat it as finished rather than actively developed. Non-primitive values are pickled by default (unverified), which is an unpickling risk for anything from an untrusted place. Keep the directory off synced folders (unverified).
- **Cost or risk:** small; stagnant upstream is the risk.
- **Reach for it when / not when:** a memoised function or a dedupe set that should survive a kill. Not when a plain SQLite table would do (our ledgers), or where you need an actively maintained dependency for years.
- **Versus:** requests-cache is HTTP-shaped; SQLite directly gives more control.

### tqdm (Python, licence NOASSERTION in the table, MPL-2.0 AND MIT per PyPI, 31k stars, last push 2026-09-20, not archived, v4.70.1 2026-09-11)
- **What it is:** a progress bar wrapper for iterables.
- **Best at:** showing a run is alive with a rate and an estimate.
- **Limits and traps (measured here):** it writes to stderr: a script run with stdout redirected to a file left that file at 0 bytes and the bar in the stderr file. `python x.py > log.txt 2>&1` puts the bar into the log and leaves the screen blank for hours, which the user reads as "there is no progress bar". On Windows when stderr is redirected, the default encoding is cp1252: the Arabic label came out as backslash-u escape codes (a literal backslash, the letter u and four hex digits per letter) with an ASCII `#` bar, and on `cmd.exe` we report Arabic mixed with bar characters renders reversed or as boxes. Use ASCII labels, keep Arabic prose on its own lines, use `tqdm.write` for log lines, and watch a file with `wc -l` for hours-long jobs.
- **Cost or risk:** none.
- **Reach for it when / not when:** interactive runs. Not the only signal for an unattended job, which needs a log line every N units and a state file.
- **Versus:** a periodic log line is redirect-safe; tqdm is for a terminal.

### shapely (Python with GEOS, BSD-3-Clause, 4k stars, last push 2026-09-21, not archived, 2.1.2 2025-09-24; laptop has 2.0.6)
- **What it is:** planar geometry in Python: points, boxes, polygons, tests such as contains and intersects, and an STRtree index.
- **Best at:** the bounding-box and point-in-polygon checks that decide whether a scraped place is inside the area you asked for.
- **Limits and traps:** coordinate order is x then y, that is longitude then latitude: `box(44.2, 33.2, 44.6, 33.5)` contains `Point(44.40, 33.31)` and does not contain the swapped `Point(33.31, 44.40)` (verified). It is planar, so distances and box sizes in degrees are not metres: convert to a metric CRS first (UTM zone 38N, EPSG:32638, is the zone for 44.4 degrees east, computed and verified by projecting a Baghdad point to about 444,141 m E, 3,684,706 m N). `contains` excludes points on the boundary; `intersects` or `covers` includes them (unverified detail). Testing every point against every polygon is slow: build an index first and test only candidates (STRtree, or geopandas' spatial index, or a vectorised `contains_xy` (unverified name)).
- **Cost or risk:** none.
- **Reach for it when / not when:** post-filtering scraper output by your own polygon. Do it even when the scraper takes a bounding-box parameter: scraperlink returned only 23 of 300 results inside the box it was given.
- **Versus:** geopandas wraps shapely and adds tables, CRS handling and joins.

### geopandas (Python, BSD-3-Clause, 5k stars, last push 2026-09-20, not archived, v1.1.4 2026-06-26; laptop has 1.1.3)
- **What it is:** pandas with a geometry column, a CRS, and spatial joins.
- **Best at:** joining points to polygons at scale (district of each place) with `sjoin`, reading and writing GeoPackage, GeoJSON and shapefiles, and reprojecting with `to_crs`. A GeoSeries exposes a `sindex` spatial index (verified: `SpatialIndex`); `sjoin` uses one (unverified).
- **Limits and traps:** always set the CRS: data from scrapers is longitude and latitude in EPSG:4326, and area or distance needs a projected CRS. Shapefiles limit column names to 10 characters and have encoding pitfalls with Arabic attributes (unverified); prefer GeoPackage or GeoParquet. Dependencies (shapely, pyogrio, pyproj) make installs heavier than pandas.
- **Cost or risk:** none.
- **Reach for it when / not when:** a table of places against a boundary layer. Not for a single point-in-polygon test, where shapely is enough.
- **Versus:** DuckDB's spatial extension does similar joins in SQL (unverified detail); osmnx builds on geopandas for OpenStreetMap.

---

# E. Free public bulk sources to check before scraping anything

The reflex to build: before writing a scraper, ask who already publishes this, and measure what the free source holds. A free bulk file has no rate limit, no block, no per-record price and usually a licence you can read.

- **Official statistics portals.** All answered a HEAD request with HTTP 200 from the laptop on 21 Sep 2026 (reachability only, content not assessed): Iraq Central Statistical Organization (cosit.gov.iq), Kurdistan Region Statistics Office (krso.gov.krd), Central Bank of Iraq (cbi.iq), the Humanitarian Data Exchange Iraq group (data.humdata.org/group/irq) and World Bank Iraq (data.worldbank.org/country/iraq). The IOM DTM Iraq page returned 403 to my scripted request; I did not investigate or work around it. Expect bulletins as PDF or Arabic-labelled workbooks, publication lag, and gaps for recent months (unverified). A statistics table beats a scraped estimate for population, prices and macro series; scrape only what they do not publish.
- **OpenStreetMap.** Geofabrik serves an Iraq extract, `iraq-latest.osm.pbf`, 90.5 MB, last modified 20 Sep 2026 (verified by HEAD). Overpass gives bounding-box queries; we measured 2,391 school points in the Baghdad bounding box, 2,049 with Arabic names, and 31 with a phone (free, via Overpass). The public Nominatim geocoder allows at most 1 request per second and a stricter 4 per minute for regular bulk work, single-threaded, one machine, cached results, and an identifying User-Agent (policy fetched 21 Sep 2026): so do not geocode a scraped table through it. osmnx (Python, MIT, 5k stars, last push 2026-07-31, no GitHub release, PyPI 2.1.1; laptop 2.1.0) downloads OSM data and builds street graphs; Overpass-API (C++, AGPL-3.0, 924 stars, last push 2026-02-19, osm3s_v0.7.62.4 2024-11-21) is the server software. OSM data licence terms (ODbL, attribution, share-alike on derived databases) need reading before client delivery (unverified).
- **Overture Maps.** Places, buildings and roads as Parquet on S3, queryable by DuckDB with `httpfs` and a bounding-box filter without downloading the dataset. Measured on 21 Sep 2026, release 2026-08-19.0, places theme, box 44.2 to 44.6 E and 33.2 to 33.45 N: 20,819 places, 16,854 with a phone and 6,435 with a website, in 38 s. Its phone rate is a property of Overture's upstream sources and is not comparable with our Google Maps figures (about 70% north Baghdad, 29% south). Licence per theme: read the attribution page (I did not).
- **Wikidata.** SPARQL at query.wikidata.org, entities with Arabic labels, coordinates and identifiers. Coverage for Iraq is thin: a query for instances of hospital (and subclasses) in Iraq with coordinates returned 22 on 21 Sep 2026. Good for governorates, districts, banks, universities and linking names to identifiers; not a directory of businesses. Keep queries small and send a descriptive User-Agent.
- **Common Crawl.** 128 crawls listed at index.commoncrawl.org, newest CC-MAIN-2026-39 (verified). An index query for a used-car listing site in that crawl returned 200 captures (my limit; 198 were HTTP 200), so the archive already holds pages from a site we scrapes nightly. Use it to check what exists before fetching, to sample a site's structure, and to pull historic pages by offset (unverified). It is a sample, not a complete copy, and holds nothing behind a login.
- **Wayback Machine.** The CDX endpoint returned captures of a used-car listing site from 2013 (first row 2013-04-17, verified). Use it to see old page formats, recover removed pages, and find URL patterns. gau (Go, MIT, 5k stars, last push 2026-03-20, not archived, v2.2.4 2024-10-28) and waybackurls (Go, no licence declared, 4k stars, last push 2024-05-01, not archived, v0.1.0 2022-04-05) list archived URLs for a domain; a repository with no licence gives you no grant to reuse its code, so read it rather than vendor it. The Wayback "available" endpoint over https returned an empty body in my test (not investigated). Be gentle: many requests to a shared archive is an imposition (unverified guidance).
- **The free-yardstick idea.** Measure the paid or difficult source against a free one before you commit to it. In practice: take one small area, pull it from the free source (Overture, OSM, an official list), pull the same area from the paid tool, match by name and distance, and report each source's coverage and the union. Our Maps work is the template: three independent scrapers gave the same phone coverage on the same ground, so buying a different scraper could not raise it, and the free OSM layer (31 phones among 2,391 school points) showed where the real gap was. Pay for the fields the free layer lacks, not for polishing fields it has.

---

# How to choose

**Managed or self-hosted.** Start from what the target refuses. If it answers a plain client or a real-browser fingerprint, you do not need a managed service: an API call or curl_cffi costs nothing per record and survives on your server. If it needs rendering and the volume is small, a local browser is free and a credit-priced fetch (ScrapingBee, Zyte) buys a known multiplier; measure the multiplier on ten pages and beware defaults that turn rendering on. If the target is a hard, shared one and you need it once (Google Maps, a social platform), an Apify Actor is the right buy: pay the sample, read your own tier's row and every per-record add-on, cap the run, and use small requests rather than a huge one. Anything whose selling point is solving challenges or rotating identities to get past a refusal is outside this skill's rule whichever vendor sells it; use those vendors only for permitted targets with a written go-ahead. Switch from managed to self-hosted when the bill per record times your volume passes your build and repair hours, and from self-hosted to managed when repairs recur or a deadline makes waiting the expensive option. What would change the decision is evidence: the sample's cost per usable record, whether the field you lack appeared, and whether the free path (gosom at 61 places a minute, an official list, OSM, Overture) already covers what you are about to buy.

**Storage for a job that must survive being killed.** Write the raw stream to plain JSONL with periodic flushes, and derive resume state from the output itself (done keys read from the file), so the same command is always the recovery. Checkpoint anything else atomically (write a temp file, rename it). Use SQLite when you need a ledger of pending, done and failed items with primary-key dedupe; keep it local. Never compress or write Parquet or xlsx live: compress after the run, convert JSONL to Parquet once (DuckDB or polars do this in seconds), keep the CSV as the server master with `utf-8-sig` if Excel will open it, and deliver xlsx typed by column so identifiers stay text. Guard the silent edges: xlsx truncates a long cell without an error, openpyxl refuses control characters, DuckDB turns a bad last line into a NULL row with `ignore_errors`, and a CSV's digit strings get re-typed by whoever opens it. Keep raw pages or responses beside parsed records when the page format may change or the source may vanish. Keep Google Sheets as a view: at 60 seconds a push, retry with backoff, check the 10-million-cell cap, and format text columns.

**Scheduling.** On the server use a systemd timer with a named zone and `Persistent=true`, a service that stops on SIGINT (`KillSignal=SIGINT`, a wrapper that forwards it, `timeout --signal=INT` for windows of work), `OnFailure=` for a wrapper that dies silently, and a short-lived unit rather than a 23-hour `Type=oneshot` that can hold apt hostage. Leave the half-hour before the next job clear. On the Windows laptop, use Task Scheduler only for what must run there, and change the defaults: allow start on battery, do not stop on battery, turn on StartWhenAvailable, and keep the machine awake; accept it is a hard kill and rely on the append-only design. Use tmux, nohup or setsid only for a one-off run of a resumable command. Reach for Prefect, Dagster or Airflow only when many dependent steps and many owners make a run UI worth another service to keep alive; for one or a few nightly captures they are overkill, and Airflow does not run natively on Windows.

**Alerting.** Silent on a good night, loud and specific on failure (Telegram with the cycle log attached, credentials in a mode-600 file, notifier exit code checked with a curl fallback), plus a dead-man switch off the box (healthchecks or similar) for the failure nothing on the box can report, plus content checks for the quiet failures (a field the site stopped sending, volume outside the same-weekday norm, a zero hit rate, a canary record that no longer comes back).

**Support libraries.** tenacity for retry policy with `reraise=True` and specific exception types, a limiter set a little under the published rate (aiolimiter for one asyncio loop, PyrateLimiter for several rates or processes; both start with a burst), requests-cache only while developing a parser against requests, tqdm for a terminal with ASCII labels and never the only sign of life, shapely and geopandas with your own polygon and an index first, in a projected CRS for anything measured in metres.

**Order a good engineer tries things in.** Official statistics and free bulk files, then a documented API, then a plain client or curl_cffi on your own server, then a local browser, then a managed Actor or fetch API for the residue, each step gated by a ten-cent sample and a hard ceiling. Switch up only on measured evidence that the cheaper step cannot deliver the field or the volume.
