---
name: scraping
description: A way of thinking about collecting data from websites, APIs, sitemaps, apps and documents, and a full encyclopedia of the tools for it. Use for ANY scraping task, in English or Arabic: "scrape this site", "get the data from", "crawl", "extract all the listings", "reverse the API", "the page loads itself", "backfill", "nightly capture", "Google Maps places", "Apify", "which tool should I use to scrape", "why am I getting 403 / 429", "the scraper stopped finding anything", "is this data complete", "سكرب", "سكرابنك", "اسحب البيانات من الموقع", "سحب بيانات", "زحف", "ليش يطلع 403", "الموقع يحجبني", "شنو الطريقة الاسرع للسحب", "شنو الاداة الافضل", "سوي سكرابر". Teaches how to read a source, choose the cheapest honest path, diagnose a refusal by experiment, survive being killed, catch silent wrong data, and decide what to tell the reader; plus every tool with its strengths, limits and status (HTTP clients, curl_cffi, Scrapy, Playwright and stealth browsers, parsers, trafilatura, Apify, discovery, OCR, storage). Not for clicking through a site or filling a form (use a browser skill).
---

# scraping

A website is a system built for people, with its own purposes, and you are asking it for something it was not designed to give you in bulk.
Scraping well is the craft of finding the cheapest honest way to get the truth out of it, and of catching yourself when you are wrong.
Speed matters, but the expensive mistakes here are never slow code. They are data that looks right and is not.

Hold three questions the whole way through, and let them decide everything else:

- **What claim do I need to be able to make**, and to whom? "These are the 2,851 pharmacies in Baghdad" and "this is what one listing site shows
  about pharmacies" are different claims that need different work, and only one of them survives a client's question.
- **Where is the truth, and what is each view of it hiding?** Every page, sitemap, export and API is a view someone configured, with a policy behind it.
- **How will I find out if I am wrong?** Design for that from the first request, because the failures that hurt do not crash. They pass every check
  you thought to write.

## Scale the effort to the job

The same thinking applies at every size, but the amount of ceremony does not. A single page or one open API is a ten-line script: look at what comes back, parse it, check the count against what you can see, done. Do not build a resumable runner, a canary or a
tool comparison for it. A few hundred pages adds a rate limiter and saving the raw. A large, recurring or long-running collection is where the durable design, the coverage argument and the validation earn their cost. A hard source, one that refuses or hides its data,
is where the diagnosis experiments and the tool encyclopedia come in. Ask the person what the number is for and how often it must be refreshed, and let that set the size of the solution. The failure in both directions is real: over-building a one-off wastes their
time, and under-building a client deliverable ships a number nobody checked.

## How a good scraper approaches a new source

These are questions to ask, in this order, not steps to run. Each one is developed in the file named beside it, in prose, with the cases that taught it.

1. **What is being claimed, and what would "complete" and "correct" mean here?** Population or observation? Is there anything independent to measure against?
   Who will read the number and what will they do with it? (`reference/assess.md`)
2. **Where does this data live before it reaches the screen?** Data starts in a store, passes through a service, is often embedded in the page as JSON,
   then becomes markup, then pixels. Each step down costs fidelity and adds fragility. Go as far up as access allows. (`reference/assess.md`)
3. **What does the cheapest honest attempt look like?** Ask the way a browser would and look at what comes back: size, type, headers, who is in front.
   `scripts/probe.py` does this in a dozen polite requests. Descend to heavier tools only when a measurement says the lighter one cannot work. (`reference/transport.md`)
4. **If it refuses, which layer said no?** Edge, address reputation, handshake, the application's own limiter, or the request itself. Do not theorise;
   change one variable and watch. The refusal's body usually names its author. (`reference/transport.md`)
5. **How could this be silently wrong?** List the ways before you write the parser: a view showing a fraction, a 200 that is not data, a key present in one
   record type and named differently in another, a check that cannot fire. Put a count at every stage and a canary on the request shape. (`reference/extraction.md`, `reference/validation.md`)
6. **What will it cost in time and money, and what is the smallest experiment that would tell me?** Requests divided by rate, and the biggest lever is
   usually the number of requests. A ten-cent test outranks an hour of argument. (`reference/durability.md`)
7. **What happens when it dies at 95%?** Assume it will. Restarting the same command should be the whole recovery procedure. (`reference/durability.md`)
8. **What do I tell the reader, including what I did not get?** (`reference/validation.md`)

## Moves that keep recurring

- **Change one thing and watch.** Same address with a different client, same client from a different address, code against a real browser. The controlled
  experiment beats the clever theory every time: ten hours of theories about a "rate limit" ended when each proxy was tried once and 57 of 100 were dead.
- **Check the instrument before the subject.** A stable, oddly round result (40%, a half) usually means a fixed fraction of your parts is broken, not that the world is throttling you.
- **Ask for something you know exists.** It separates a broken request from an empty stretch of data in one call, which no amount of counting can.
- **Distrust absence and tidiness.** A count small and round enough to have been chosen by a person probably was. A good story about missing data will stop you looking for it.
- **Prefer the source's own list to yours.** Its filter block, sitemap, CMS totals, facet endpoints. Whatever it adds later appears on your next run; a list you wrote goes stale in silence.
- **Find the axis where every record must appear exactly once, and prove it with a second axis.** Coverage is an argument, and near-zero new records from an independent sweep is its evidence.
- **Try to explain your own headline away.** The likeliest cause of a striking number is the thing that measured it.
- **Measure, then say it with its date.** Concurrency, limits and blocking policy belong to the operator and change. What you inherited from the last site is a hypothesis.
- **Keep the raw.** The schema you extract into encodes today's understanding; the raw response is what lets tomorrow's understanding cost nothing.

## Tools

Tools answer mechanisms: what does the target actually check, and what is the lightest thing that satisfies it? Choose by that, not by popularity (a repo with thousands of stars and an
MIT badge turned out to be a commercial desktop product). `reference/tools.md` is the map from problem to tool and holds verdicts on seven recently recommended repos;
the full encyclopedia, 170 tools each with what it is, where it beats its neighbours, where it fails, its cost and its maintenance state, is in `tools/`:
`fetch-and-frameworks.md`, `browsers.md`, `parsing-and-extraction.md`, `discovery-documents-platforms.md`, `services-storage-orchestration.md`. Each file ends with a "How to choose" section that reasons through its category.
Read the entry you need (`Grep` its name inside `tools/`), not the whole file; `tools/index.md` is a one-line-per-tool index for when you are hunting by name.

## Where this skill draws its line, and why

Every source is run by someone, and your requests spend their capacity. The skill collects what any visitor may see without logging in, at a pace the server can carry, and presents itself as a
browser does: real headers, and the real TLS handshake through `curl_cffi`. That is not a trick; it is being a well-formed visitor. A challenge page or a CAPTCHA is the site saying no.
The skill does not solve it, and does not rotate identities or proxies to get round a block, because a blocked domain costs more than a slow crawl and the relationship with a source outlasts one project.
Nor does it scan an id range to find content when the source has a listing path. When the line is unclear, stop, save the refusal, work out which layer refused and why, and put the options to the person you work for:
a slower pace, another path, or asking the publisher. Going further is only defensible with the source's consent: in one case an address-reputation block was diagnosed, the publisher was asked, and their office replied in
writing that they had no objection, and the scope was then limited to exactly that site. An agent never grows a proxy pool, rotates identities, or points a pool at a new refusal on its own. The reasoning is in
`reference/transport.md`, and the one exception for walking ids is in `reference/assess.md`.

## Before you start

Check whether you already hold notes or an earlier scraper for the source: how it behaved, what it blocked, its page format, the limits you measured, each with its date. Facts about a source decay, so treat old notes as a
hypothesis to re-measure on a short probe, not a promise. Keep field notes per source as you go; the next job on the same source starts from them.

## Files

- `reference/assess.md`, `transport.md`, `extraction.md`, `durability.md`, `validation.md`: the thinking, stage by stage, each grounded in cases.
- `reference/cases.md`: the situations behind all of it, told as what was believed, what was true and how it was found out. Read it when a problem feels familiar.
- `reference/recipes.md`: how the recurring jobs are done (Google Maps, Apify, WordPress, Next.js, backfills, rolling windows, documents).
- `tools/`: the encyclopedia (see above).
- `scripts/`: `probe.py` (assess a source), `scrapekit.py` (limiter, guarded fetch, JSONL, atomic state, canary, reconciler; `selftest.py`), `runner_template.py` (a resumable collector to copy), `requirements.txt`.
  Set `PYTHONUTF8=1`: the Windows console dies on Arabic.

## Neighbours

Skills for adjacent jobs, if you have them: a browser-driving skill such as [browser-use](https://github.com/Murtadha-Najem/browser-use-skill) for opening a site, clicking, logging in and forms; a PDF, spreadsheet or
document skill for deliverables; a data-quality skill for field-collected survey data.

## Delivering

Say what was collected, from where, when and how, what was not captured and why, and whether each layer is a population or an observation. Ship the script and a readme with the data. Keep cost figures in one internal file,
never in a client deliverable. Anything a client reads should read as written by a person who checked it: plain punctuation, no decorative bullets, no emoji marking sections. Reply in the language the person used.
