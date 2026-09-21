# Recipes: how the recurring jobs are done here

The thinking is in the other files; this is the practice. Each recipe names the decision and where it came from, so you can tell when the reason no longer holds.
Prices and limits change: re-check the ones marked with a date. For any tool named here, its full entry (strengths, limits, status) is in `tools/`.

## Places from Google Maps

**Default tool: `scraperlink/google-maps-scraper` on Apify** (decision 13 Sep 2026). Measured against
`compass/crawler-google-places`: identical output quality (Arabic intact, 100% coordinates, same phone rate on the
same ground), at $0.50 against $3.00 per 1,000 places at an entry (BRONZE) tier. The choice held at every
tier (6x cheaper at BRONZE, 3.75x at GOLD, about 2x at DIAMOND). Standing settings for Iraq: `gl: iq`, `hl: ar`,
`num: 200`. Leave `reviews` and `popularTimes` off: each adds $0.25 per 1,000 and neither is needed.

Read your own price row, not the headline: the page lists every tier and the `$1.50` visible on compass's page was the
GOLD row. And compass bills per filter, per place ("final price = places x filter price x number of filters"); three
filters roughly doubles the bill. Other add-ons stack the same way. `scraperlink` has no filter surcharge.

**Do not use an Apify grid to cover a city on a small balance.** `scraperlink`'s bounding box does not confine results:
a 5 x 5 km box with a 1 km grid returned results a median 5.5 km from the cell centre, and only 23 of 300 fell inside the
box, because `num` is per query and the cap is spent on the first cells and on spill. Use Apify for targeted lookups
with a small `num`. Sweep areas with the local scraper for free.

**Local scraper: gosom `google-maps-scraper`** (a Go binary; `baghdad_schools_sweep_pc\google-maps-scraper.exe`). It
supports `-grid-bbox` with de-duplication, `-c` concurrency, `-email` (crawls the listing's website for addresses),
and gave phone in local format (`0783 ...`), Arabic flawless, 100% coordinates. A 9-cell box over central Baghdad gave 66
unique places with no duplicates in 95 seconds, no proxies. About 42 places a minute; Baghdad at 1 km cells is about 1,600
cells, roughly 4.7 hours a category at the measured 10.5 s a cell. Limits measured:

- Concurrency is CPU-bound: `-c 6` gave 61 places a minute, `-c 12` gave 53 (durability.md).
- It hangs after a tile finishes ("scrapemate exited" in the log). Run each tile in its own process group, watch the log
  for that line, wait 20 s and kill the group. Both the Windows runner and the server script needed this.
- Blocking at real volume is untested: about 120 detail fetches were made unproxied with no captcha; 1,600 cells is a
  different proposition and may need proxies (a question for the person you work for, per the line in transport.md).

**Phone coverage is a property of the neighbourhood, not the scraper.** About 70% in Mansour and Harthiya against 29%
in Dora and Zafaraniya, identical across scraperlink, gosom and compass. Do not treat a low phone rate as a scraping
failure to engineer around.

**Beware repo signals.** `omkarcloud/google-maps-scraper` has thousands of stars and an MIT badge but is a commercial
desktop product (free 200 searches a month, then paid tiers). Stars and a licence label are not evidence of what a repo is.
Google's own data is dirty (a Baghdad pharmacy carried a US number); neither scraper invented it.

## Running an Apify actor

The Apify MCP tools are available: `search-actors`, `fetch-actor-details` (read the README and the input schema before
running), `call-actor`, `get-actor-run`, `get-dataset-items`. Prefer an actor with higher usage and ratings, and read the
pricing by event, not the headline. Set a hard spend ceiling per run as a circuit breaker against a bug in your own
query. Run once with all queries rather than several runs (de-duplication happens within a run only; five runs over one
area billed 1.61x). Test the cheapest sample first: two $0.18 tests redirected a $29 budget. The credit and balance are
the owner's; ask before a run that could spend a meaningful share.

## Listing pages, then detail pages, then a second axis (a whole catalogue)

Worked end to end by a tester on a practice catalogue (1,000 books, 50 listing pages, 50 categories), in about 1,150 requests:

1. Pass 1 on the listing pages (`runner_template.py`). Build the detail URL list from its records or its saved raw HTML.
2. Pass 2 on the detail pages, with its own `--out`. Listing and detail must agree on the fields they share (title, price,
   rating, availability): agreement on all 1,000 is evidence the extraction is right.
3. Second axis for coverage: the category pages. Header counts summed to 1,000, the enumerated URL set was identical to
   the listing set, and the category on each detail page matched its header count. Three independent counts, plus the
   site's own stated total ("1000 results", 50 pages, page 51 returning 404), is what "complete" looks like.
4. Field checks: fill rate per column, ids without gaps, unique UPCs, and read the oddities (a title that ends in "..."
   at source, a duplicated title that is two distinct books).

## A WordPress site

`/wp-json/wp/v2/<type>?per_page=100&page=N`; the total is in the `x-wp-total` and `x-wp-totalpages` headers. Compare with
the sitemap and with the listing page (ANA SHISHE: the page showed 16 products, the API and sitemap said 30). Custom post
types are visible at `/wp-json/wp/v2/types`. Store the raw JSON.

## A Next.js site

Look for `__NEXT_DATA__` (pages router) or `self.__next_f.push` chunks (app router) in the HTML, and read that instead
of the markup (extraction.md). `_next/data/<buildId>/...json` endpoints exist for pages-router sites. The build id changes
on each deploy, so read it from the page every run.

## A site with a sitemap

Sitemap first: it lists what is live. Compare its count with the site's own claimed count and with an id-space sample
(assess.md, "Every view has a policy behind it"). For a full crawl, a small sitemap-driven crawler is a good model: sitemap-driven, page type detection, cleaned Markdown beside raw HTML, structured FAQ and sources, one index
row per page, polite delay.

## News and article text

Take article text with **trafilatura** (extraction.md), not jusText. For an ongoing news pipeline (collection, relevance gate, grouping, classification), build it as a scheduled job on these ideas; for a one-off article crawl use this skill directly.

## A historical backfill by id (the used-car site pattern)

Only when removal is a flag and the id space is the inventory (assess.md, "Sequential ids: why not, and the one case where yes").

1. Sitemaps give the live ids; short gaps between live ids are deleted records (sampled 45/45 real); long runs with no
   live id are blocks the sequence never issued (2/45 real). Skip the never-issued blocks by default; take them last, with
   a flag.
2. Phases: `sitemaps`, `expand`, `resolve`, `build`; resumable; one command to continue.
3. Two doors behave differently: the list API (the list API on its own subdomain) needed no proxy and no impersonation; the detail pages
   needed both (transport.md).
4. A canary guards the run (durability.md). 404 needs two sightings.
5. Describe the result as "everything recoverable, with the holes stated", never "everything ever published": there is no
   ground truth to check completeness against, and hard-deleted records are unrecoverable.
6. The nightly job then keeps it growing: list pass for changes, detail pass only for unseen ids, and a sweep above the
   watermark for listings published and withdrawn between two runs.

## A rolling-window capture (the classifieds site pattern)

The classifieds site purges removed listings, so history is a rolling window of about 110 days plus Wayback snapshots. The window
rolls forward daily, so a delay costs history: decide early. A HEAD on `/ar/search/<id>` classifies an id with no body
(200 Iraqi, 301 Iraqi and purged, 410 other).

## Older than the site keeps

The Internet Archive holds captures (the classifieds site: 95,773 unique Iraq listing ids, 2019 to 2026, the only source older than
May 2026); Common Crawl was negligible there. Check both before declaring a period unrecoverable. A parked domain
registered in 2013 is not a business operating since 2013: the platform's first id and first archived content set the
real floor (the used-car site: id 259, 19 October 2020).

## Documents, PDFs and OCR

Extract text and count characters on 8 to 10 files across different producers before choosing: zero characters means
images, and OCR is a different project. Reversed Arabic is a visual-order artefact (extraction.md). The `pdf` skill covers
reading PDFs, and `tools/discovery-documents-platforms.md` (part C) has pdfplumber, PyMuPDF, camelot, the OCR engines and the visual-order repair.

**A PDF price list into a table.** Think of it as three separate problems and check each. Is there a text layer at all (count characters on a few pages across the file; zero means OCR)? Where do the columns really sit (read the header row and map by
label, never by position, and remember a right-to-left table lists its first column last)? Are the numbers what they look like (Arabic-Indic digits, decimal marks, and text in visual order)? Then reconcile: rows per page against what you can see, a total or
page count the publisher states, and a hand-checked sample with its error rate written down. List the pages that failed instead of dropping them, and ask whether the client holds the original spreadsheet, which beats any extraction.

**Choosing the articles from one site.** Take them from the sitemap or the CMS list, not from the head of a listing page (the newest are not a random sample of anything). Say how they were chosen: "200 articles from one site, drawn across 2024 to 2026" is
a claim you can defend; "200 articles" is not.

**A place category in one city (Najaf pharmacies).** Google Maps gives an observation, not a register. The honest deliverable states the fill rate of each field by district (phone coverage follows the neighbourhood), names the sources it did not have, and
does not claim a count without an independent second source to measure against.

## Mobile-only or app-only sources

A Flutter release build can hold its content inside the compiled binary: one legal-reference app's package had no `.db`, `.sqlite` or `.json`, yet `lib/arm64-v8a/libapp.so` held 18.8 million characters of Arabic law text as Dart string constants, and nothing came from a server. Dart stores each string with a length prefix (`varint(length<<1 | is_two_byte)`, then the characters, UTF-16 for Arabic); walk that framing, because a plain scan for UTF-16 runs splits strings at newlines. The limit: which law an article belongs to and the display order are not in the strings, they live in the app's list objects and need a Dart decompile (Blutter), so check that neighbouring strings are related before claiming an order. For an app that does call a server, its traffic is the place to look for the API. Whether a given app's content may be taken is a question to settle first; the technique does not answer it.

## Public data that a regulator or ministry publishes

Official portals often run old single-instance software: check the server banner, take a deliberately slow pace and write it in the script header. Read the export's own page for its window (assess.md, "Every view has a policy behind it").
