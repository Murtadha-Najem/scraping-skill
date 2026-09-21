# Reading the source: where the data lives and what each view hides

An hour spent here saves a day of building on a wrong assumption, because the assumptions that matter are all cheap to test now and expensive to unwind once a
parser sits on top of them. `python scripts/probe.py <url>` does the first pass (a dozen polite requests: what comes back, whether it is a shell, embedded JSON, who is in front,
robots and sitemaps, WordPress totals). The rest of this file is how to think about what it shows you.

## Start from the claim, not the site

Before any request, decide what you will have to be able to say. Some sources are **populations**: a register, a licence list, the companies listed on an exchange. An authority decides
who is in, so completeness is achievable and you can claim it. Others are **observations**: listing sites, directories, volunteer maps, Google Maps. They hold whatever somebody happened to record,
so you can never know what you missed. Confusing the two turns "we collected 2,851" into "there are 2,851", which nobody counted. Decide which you are dealing with, write it next to the number,
and if there is any independent source, even a poor free one, find it now: it will tell you how much a paid source adds and what it misses (a paid source returned 2.5 times a free one, and the free
one still held 18% the paid one never found, so the right answer was both).

## The chain the data travels

Data begins in a store, passes through a service, is frequently embedded in the page as JSON, becomes markup, and finally pixels. Every step down loses fidelity and gains fragility: markup changes with
a redesign, a rendered grid shows what a template chose, pixels need OCR. So the question for any page is **where does this come from before it reaches the screen?** The way up is almost always cheaper and
cleaner than parsing what you see. A site that draws on a canvas has no DOM to scrape at all, which sounds like bad news and is good news: it must be getting the data from somewhere structured.

Ways to find the origin, roughly cheapest first:

- **`robots.txt` and the sitemaps it declares.** Sometimes the whole list is right there. Fetch every declared resource and check its status and type, because declarations outlive the resources they point to.
- **`view-source`.** `og:image` and `<link>` tags often name the backend or CDN host. Embedded payloads to look for: `__NEXT_DATA__` (Next.js pages router), `self.__next_f.push([...])` chunks
  (app router, the same fields as escaped JSON strings), `__NUXT__`, `window.__INITIAL_STATE__`, JSON-LD. Parse a string literal with the format's own parser, never a generic unescape, which mangles non-Latin text.
- **The network panel or a HAR, filtered by host first.** A HAR is mostly other applications' noise (a 65 MB capture held a few dozen useful requests). Check whether response bodies were recorded at all.
- **The JavaScript bundle.** The client contains every base URL, path and parameter it uses. Dynamic paths appear as fragments (a base constant plus a template), so reconstruct and confirm each live:
  ```bash
  grep -ohE '"/(api|content|v[0-9])[a-zA-Z0-9_/{}$.-]*"' *.js | sort -u
  grep -ohE '\$fetch\(`[^`]{0,90}`' *.js | sort -u
  grep -ohE '(BASE|API) *= *"[^"]+"' *.js
  ```
- **A live browser, with an interaction.** A server-rendered page shows no data call at load because the first payload is in the HTML. Scroll, paginate or filter so the call that loads more fires, then capture it.
  A browser-driving skill or the chrome-devtools MCP can read the network and pull the page's own API responses.
- **App traffic**, for a mobile app, through an intercepting proxy such as mitmproxy, on your own device and for public data.

Do not guess endpoint paths. Guessing produced a run of 404s; one look at the request list produced the exact endpoint, including that it needed POST. Names mirror the site without matching it literally:
singular in one place, plural in another (`/brand/x` on the site, `/brands/x` in the API, `context_type=brand` in the filter), so try both, and hyphen and underscore, before deciding a feature does not exist.
And a root URL that returns nothing is a fact about one URL: one source looked dead at the top and was fully alive a directory down.

## Talking to an API that was not written for you

An API tells you its contract if you ask badly on purpose. Send an out-of-range value: `?limit=1000` answering "Expected number to be less or equal to 100" is the maximum and the parameter's name in one reply.
Then test each parameter differentially, with and without: a 200 does not mean it was honoured, and an endpoint that accepted `?ids=` and ignored it would have carried a whole design on a lie.
Authenticate before you probe which paths exist, or every path returns the same auth error and real and imaginary endpoints look alike.

Most "protected" APIs are protected by a formality: a token the first page load issues to any visitor, a `/guest` endpoint. Decode the JWT (no `exp` means it never expires) and copy the full header set from a real
request, then remove headers one at a time to learn which are required. Using one guest token as one visitor is ordinary. Minting many to slip under a rate limit is a different act, and this skill does not do it.

## Every view has a policy behind it

This is the idea that catches the most silent errors. A page is a view someone configured, and it will never tell you it is showing a fraction.

- The **Products page** of a manufacturer showed 16 items with no pagination. Its own WordPress API said 30 in an `x-wp-total` header, and the sitemap agreed. The other 14 were live and indexed, just not in the widget.
  A scraper on the grid would have returned 16 clean, correct rows that pass every check, because what is missing leaves no trace in what you collected.
  The tell is a count round and small enough to have been chosen by a person. Ask the system, not the storefront, and get a count from a second source before trusting the first.
- A **sitemap** is what is live, not what exists. The used-car site's sitemaps listed 463,437 cars, the live third. Removal was a flag: 58 of 60 cars that had dropped out of the sitemap still answered with full data marked
  `Deleted`. It also biases the analysis the wrong way, because what is still live is what has not sold.
- A **bulk export** is a view with a policy. One was taken as the archive; its own download page said it held the last eighteen months, so 96% of the records were missing and one operator's whole network was absent,
  and its zero was then written up as a finding. A fuller public mirror existed, 26 times larger. Find the sentence that says what an export includes.
- A **paginated list** may be capped far below the total. The **facet** endpoints that fill filter dropdowns return hundreds of entries uncapped (342 entities in two calls against 144 from an exhaustive list).

Whenever you catch yourself explaining an absence ("that operator must have closed"), stop: a good story about missing data ends the search, and you have not checked yet.

## Coverage is an argument you have to make

Pick the **primary axis where every record appears exactly once**. Every product has one seller, but 16% had no brand, so seller is a full axis and brand has holes. Choose by inspecting a sample record, not by convenience.
Then **prove coverage with a second, independent axis**: if sweeping it yields about nothing new, the first was complete. Say plainly that this is evidence, not proof. When there is no list of a kind of entity, snowball:
use each discovered entity as the context for another facet call until the additions approach zero (477 entities in the end against 144 from the direct list). A field that is empty on part of the records may simply be empty at source, so check before you call it a defect.

## Sequential ids: why not, and the one case where yes

Content addressed by an incrementing number, with a listing that shows only the newest few, makes walking the range look like the only option and one line of code. It cost an hour of total lockout on one source: the block covered
the whole domain, static files included. A listing path almost always exists (each entity's own page often carries its whole history), and a blocked domain costs more than a slow crawl. If you truly cannot find one, that is a finding.

The exception is real, and the reasoning matters more than the rule. When removal is only a flag and the id space is the only inventory (the used-car site backfill), walking ids is the method. It was safe because the source's tolerance was
measured first at a low rate, cheap probes classified ids where possible (a HEAD on the classifieds site), a canary confirmed the request shape kept working, and the pace stayed under the level that draws a block. The classifieds site's edge blocked one address
at about 200 requests a second for over ten minutes and was fine at 30; a later measurement found it counts requests per address rather than the rate, blocking after roughly 1,400 to 2,000 whatever the pace, for hours. Re-measure; do not copy numbers.

## Documents

Extract text and count characters on eight to ten files across different producers before deciding: zero characters means images, images mean OCR, and OCR is a different project. Sample across producers, not items: a source was
judged unusable after two unreadable files and 8 of 10 were fine. Right-to-left text can extract in visual order, so a known string checked early saves a late surprise.

## Estimate after you enumerate

Time is requests divided by sustained rate, and both terms are usually wrong. Requests: look for a bulk endpoint before committing (`?ids=a,b,c`, `/bulk`, a POST with a list), and prove the parameter is not ignored. One request per hundred
records against one per record is 20 minutes against 21 hours. Rate: measure it on a sample longer than the limiter's window. Run a cheap discovery that prints the real counts, then quote; if a running job invalidates an estimate you gave
(20 minutes became 65 when discovery found three times the entities), correct it out loud.

## Present the contract before you build

Probe read-only until you can state the endpoints, the auth model, the pagination model, the rate limit, the record schema and the volume. Reconnaissance is not "writing code", so it does not break a plan-first instruction. Present that with
the options and their costs. For anything that will occupy a machine for hours, verify a small slice end to end and hand over one exact command with the estimate, rather than running it on the person's laptop unasked.
