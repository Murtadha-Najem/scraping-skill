# Cases: what we believed, what was true, how we found out

These are the situations the rest of the skill was distilled from. Each is told the same way so the pattern is easy to spot the next time a problem feels familiar. The point of each is the move, not the site, and the numbers are evidence of scale,
not thresholds: they were measured on one source on one day, and your source will differ.

## Reading a source

**16 products or 30.** Believed: the Products page lists the catalogue. True: it was a widget showing 16; the site's WordPress API said 30 in `x-wp-total` and the sitemap agreed. Found by: asking the CMS instead of the storefront. Move: get a count from a second source before trusting the first;
a count small and round enough to have been chosen by a person probably was.

**The sitemap is the live third.** Believed: 463,437 ids in the used-car site's sitemaps were the whole history. True: they were what was still live. 4,153 cars from an August snapshot had vanished from the September sitemap, yet 58 of 60 re-fetched by id returned full data flagged `Deleted`. Found by: comparing two snapshots you already held.
Move: treat a sitemap as a query result ("what is published now"), not an inventory ("what ever existed").

**The export that held eighteen months.** Believed: a public export was the archive. True: its own download page said it held only the last eighteen months. 96% of the records were missing, one operator's whole network was absent, and its zero was then written up as "this operator has closed". A fuller public mirror
existed, 26 times larger. Move: read the sentence that says what an export includes, and never explain an absence before verifying it.

**The dead root.** Believed: a source was dead because its top-level URL returned nothing. True: it was fully alive one directory deeper, thirty seconds from being written off. Move: a broken entry point is a fact about one URL.

**Two samples are not a sample.** Believed: a source was unusable, after two of two documents came back unreadable. True: widened to ten, eight were fine; the first two were the exception. Move: sample across the producers, and treat a verdict drawn from fewer items than producers as provisional.

**342 against 144.** Believed: the paginated list of sellers was all of them. True: the endpoint that fills the filter dropdown returned 342 in two calls, and snowballing (each discovered entity as the context for another facet call) reached 477. The list, exhaustively paged, had 144. Move: find the endpoint the interface uses for itself, and
stop snowballing when the additions approach zero.

**The axis with a hole.** Believed: sweeping by brand would reach every product. True: about 16% of products had no brand, and every product had exactly one seller. Move: choose the axis every record must appear on exactly once, and use the others as the cross-check.

**The free yardstick.** Believed: the paid source was simply better. True: it returned about 2.5 times what a free source held, and the free source still held 18% the paid one never found. Move: measure a paid source against a free one before choosing; they were additive, not competing.

## Access and refusal

**The 40% that was 43 of 100.** Believed: a rate limit was capping success at 40%. Ten hours went into worker counts, pacing, TLS and back-off, and each theory produced a plausible result. True: 57 of the 100 proxies were dead, recycled addresses already flagged. Found by: trying each proxy once, four minutes. Move: verify each channel before tuning the strategy;
a stable round plateau is a headcount problem first.

**The handshake, not the address.** Believed: a 429 from the used-car site detail pages meant the proxy addresses were in trouble. True: through the same exit address, a Windows client got 200 and an Ubuntu server got 429, and impersonating Chrome fixed it (0/12 became 8/8). Found by: holding the address constant and changing the client. Move: address
and client are separate axes, and "it works on my machine" is a real diagnosis.

**The 429 that named its author.** Believed: an edge rate limiter, so weeks went into proxies and per-address pacing. True: the saved 429 body carried `gssp: true`, meaning the application's own server function had run, so the limiter was inside the application and more addresses could never help. Move: save the body of any
error you act on; it often names the layer.

**The controller that strangled itself.** Believed: cutting workers when throughput collapsed was the safe response. True: the hit rate was 27% at 5.8 workers and 22% at 2, so backing off bought nothing and cost four times the speed; and the recovery path deadlocked because the ceiling could only rise after a worker had been added, which needed the ceiling.
Move: show a remedy helps before wiring it in, and give every downward move an independent way back up.

**404 is not final.** Believed: four ids that logged 404 were hard-deleted. True: re-fetched minutes later all four returned 200, the site emits spurious 404s under load, and the four were within 180 ids of each other, one glitch and not four events. Move: never let one observation of "gone" be final.

**A news publisher's WAF.** Believed (at first): a block on datacentre addresses or on the country, which a second server abroad might fix. True: an address-reputation block on AWS WAF, not country, not datacentres as a class, not fingerprint. From a home connection in Baghdad: 200. From a rented VPS: 403 even impersonating Chrome and Safari. From 56 datacentre addresses worldwide, one request each: 31 got in and 24 did not, the same country and even the same network giving both. The publisher was asked and replied in writing that they had no objection to the operator solving it from their side. Move: diagnose which layer refused, ask the person who can say yes, and scope what you do to exactly what was agreed.

**The walked id range.** Believed: scanning sequential ids was the only way to reach older content. True: it locked out the entire domain for an hour, static files included, and the entity's own page carried its whole history in one request. Move: look harder for a listing path. The exception (the used-car site, where removal is a flag and the id space is the inventory) was safe only with measured tolerance, a canary and a bounded pace.

## Silent failure

**A whole run, green and empty.** Believed: a run that ended "done" had collected. True: blocked requests came back as an HTML page at status 200; the code tested `status == 200 and json`, fell through to `return None`, recorded zero for every unit and finished with a full progress file. Move: classify an unexpected type explicitly. It is a failure, never "no data".

**Poisoned progress.** Believed: resumability was safe. True: because units were marked done on empty results, the progress file blocked the retry that would have fixed it. Move: separate discovery, progress and results so poisoned state can be deleted without rediscovering.

**Ten hours finding nothing.** Believed: a dry night. True: a placeholder slug used a million times had become a signature and been blocklisted; the run wrote 127,998 false "gone" rows in a day. Found by: fifteen candidate url shapes in one script, two minutes. Then the fix for that (stop after N misses) aborted twice on genuinely empty id space, and the correction was to ask for a
record already held. Move: a floor must be a diagnosis, not a count.

**The format changed at midnight.** Believed: nothing. True: the used-car site moved its detail page from the Next.js pages router to the app router, and a listing already held stopped coming back. The canary stopped the run before a false 404 was written and the alert named it a request-shape problem, not a rate limit. Move: the cheap guard that can fail loudly is worth more than any amount of care.

**One value, three keys.** Believed: the phone column was empty for two sections because there were no phones. True: those sections named the field differently. Move: locate a field by the shape of its value and emit "all values found".

**The plural that wasn't.** Believed: a category page had no results header. True: the regex matched "results" and not "1 result", ten one-book categories read as missing, and the records passed because the books were present. The saved raw HTML made the fix free. Move: feed every text pattern the singular and zero forms.

## Wrong numbers that looked right

**The filename that collapsed six years.** Believed: outputs named after their inputs were safe. True: in Arabic every non-ASCII character became the same separator, different sources mapped to one name and the second overwrote the first: 57,554 rows lost with no error and a "success" report. Move: index plus digest, and assert distinct names.

**Eighteen names from memory.** Believed: the governorates would join. True: `Ninewa`, `Basrah`, `Muthanna` against a file saying `Ninawa`, `Al-Basrah`, `Al-Muthanna`; 13 of 18 failed silently while the grand total reconciled. Move: print both lists, write the map, assert coverage in the same edit.

**Cells are not towers.** Believed: mapped 51,546 over official 17,933 was a coverage ratio. True: 287%, impossible; one tower appears as six to fifteen cells. Move: name the unit above and the unit below before any ratio.

**Padded and missing at once.** Believed: an OSM count of 1,347 was a reasonable site count. True: it included 1,084 floodlight masts (`tower:type=lighting`) and missed 828 communication towers, and the two errors partly cancelled. Move: audit both edges of any filter defined by listing values.

**Seven times the norm.** Believed: a regional figure was a finding. True: almost every record behind it was nameless, the owner fields held non-owners, and a fifth sat within one square kilometre. Move: a striking number is a reason to investigate.

**72% against 28%.** Believed: one scraper was decisively better at phone numbers. True: the two runs had searched different districts; anchored on the same coordinates 72% collapsed to 31% (later corrected to 29%, from a wrong denominator). Phone coverage is a property of the neighbourhood: about 70% in northern Baghdad and 29% in the south across three scrapers.
Move: compare on the same ground, and check the denominator.

**Zero points for the upgrade.** Believed: paying for enrichment would fill opening hours, amenities and descriptions. True: all three moved zero percentage points, because the owners had never filled them in. Found by: a $0.18 sample. Move: measure fill rate on free data before paying, and buy a ten-cent sample before a large purchase.

## Speed, cost and survival

**Smaller and six times slower.** Believed: a header that shrank responses by 30% would speed the job. True: it bypassed a cache and made it six times slower, and it had been recommended on size alone. Move: time both, end to end, on the real workload.

**A habit carried across.** Believed: a rate-limit habit from one site applied to the next. True: the second site had no limit, and the habit had turned a parallel job serial for hours. Move: re-measure per source and date it.

**The sleep that used 40% of the budget.** Believed: `sleep(1.1)` after each request was polite and efficient. True: with a 0.4 s response that is 40 a minute against an allowance of 100, turning a 21-hour job into 31. Move: one shared limiter plus workers; measure over more than the burst window.

**The 13,000 lost records.** Believed: a compressed append-only file was tidy. True: a kill mid-write made everything after the last frame unreadable. Move: plain JSONL, compress afterwards.

**The stop that killed nothing.** Believed: `systemctl stop` drained the collector. True: `KillMode=mixed` signalled only the wrapper script, and the collector never heard, so systemd waited five minutes and SIGKILLed everything, twice. Move: trap the stop in the wrapper and forward one SIGINT.

**The apt lock.** Believed: a long collector unit was independent. True: as a `Type=oneshot` it sat "activating" all day, so a needrestart after a library upgrade waited hours holding `dpkg/lock-frontend` and blocked another project's deploy. Move: think about what else shares the machine.

## Tools

**jusText on Arabic.** Believed: an earlier one-page check (an Arabic services page: menu dropped, body kept) meant jusText worked. True: on 135 pages of one site it recalled 0.17 of the Arabic body text and left 53 pages nearly empty, while trafilatura recalled 0.91. Move: one page is not a sample; measure a tool on the population it will meet.

**Stars and a badge.** Believed: a Google Maps scraper repo with 3,465 stars and an MIT badge was open source. True: it was a commercial desktop product with a free tier of 200 searches a month. Move: stars and a licence label are not evidence of what a repo is; read what it does.

**A grid that does not confine.** Believed: `boundingBox` plus `gridSpacingKm` would cover a 5 x 5 km box. True: results came a median 5.5 km from the cell centre and 23 of 300 fell inside the box, because the cap is per query and is spent on the first cells and on spill. Move: test that a control actually controls before paying for a sweep.
