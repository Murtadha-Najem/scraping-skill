# scraping skill for Claude Code

A Claude Code skill that teaches a way of thinking about getting data out of websites, APIs, apps and documents, and carries an encyclopedia of the tools for it. It is meant to help with any scraping request, from one page to a source that refuses you.

It is not a list of rules. It teaches how to read the problem, choose the cheapest honest path, find out why a request was refused, survive being killed halfway, and catch the failures that hurt most: data that looks right and is not.

## The idea

Hold three questions the whole way through:

- What claim do I need to be able to make, and to whom?
- Where is the truth, and what is each view of it hiding?
- How will I find out I am wrong?

Then ask eight questions in order (what is being claimed, where the data lives before it reaches the screen, what the cheapest honest attempt is, which layer refused, how it could be silently wrong, what it costs, what happens when it dies at 95%, what to tell the reader). The skill develops each in prose, with the real cases that taught it: a page showing 16 products while the site held 30, a "rate limit" that was 57 dead proxies out of 100, a 200 response that was an HTML block page, a run that wrote a hundred thousand false "gone" rows.

It scales the effort to the job: a single page is a ten-line script, a recurring collection gets the durable design.

## What is inside

```
plugins/scraping/skills/scraping/
  SKILL.md              the way of thinking, the questions, the moves that recur, the line
  reference/
    assess.md           reading a source: where data lives, what each view hides, coverage, estimates
    transport.md        access as a conversation: what can refuse you, the ladder, diagnosing by experiment
    extraction.md       turning responses into rows without fooling yourself
    durability.md       designing for the run that dies, speed and cost as measurements, running on a server
    validation.md       trying to prove yourself wrong, and telling the reader
    cases.md            about 35 situations: what was believed, what was true, how it was found out
    recipes.md          Google Maps, Apify, WordPress, Next.js, backfills, documents
    tools.md            problem to first tool, what to try next, seven checked repos
  tools/                the encyclopedia: 170 tools in five files, each ending with "How to choose"
    fetch-and-frameworks.md, browsers.md, parsing-and-extraction.md,
    discovery-documents-platforms.md, services-storage-orchestration.md, index.md
  scripts/
    probe.py            assess a source in about a dozen polite requests
    scrapekit.py        rate limiter, guarded fetch, JSONL, atomic state, canary guard, reconciler
    runner_template.py  a resumable collector to copy and edit
    selftest.py         offline tests for scrapekit
```

Each tool entry says what it is, what it does better than its neighbours and why, its limits and traps, its cost or risk, when to reach for it and when not, and its maintenance state. Maintenance data (stars, licence, last push, archived) for 137 repositories was read from GitHub on 21 September 2026 and will age. Features were checked against READMEs and PyPI where possible; anything that comes from general knowledge and was not checked is marked `(unverified)`.

## Install

As a Claude Code plugin:

```
/plugin marketplace add murtadha203/scraping-skill
/plugin install scraping@scraping-skill
```

Or copy `plugins/scraping/skills/scraping` to `~/.claude/skills/scraping`, then start a new session.

The scripts need Python 3.10 or newer and `pip install -r plugins/scraping/skills/scraping/scripts/requirements.txt` (`requests`, `curl_cffi`, `selectolax`; `trafilatura` optional). Set `PYTHONUTF8=1` on Windows, where the console dies on Arabic.

## Usage

Nothing to learn. Ask for anything that involves getting data from a site, in English or Arabic:

- "Scrape all the listings on this site and tell me how sure you are it is complete."
- "My scraper works on my laptop but every request gets 403 on the server."
- "Which tool should I use to pull the text out of 200 Arabic news articles?"
- "ليش الموقع يحجبني بعد كم ساعة؟"

## What was tested

Honest limits first: this was tested on practice sites and on reasoning problems, not on a long list of hard live sources.

- `scrapekit` has offline self-tests (rate limiter never exceeds its window across threads, a truncated JSONL tail is skipped, atomic writes, collision-proof names, the canary guard's three outcomes).
- `probe.py` was run on a static page, a JavaScript shell, a Next.js app-router site behind Vercel and a WordPress site.
- `runner_template.py` was run on a practice catalogue: a slice, then the same command resumed with only the remainder, then did nothing; a 404 was recorded with its reason and parked after three failures; a wrong media type failed instead of reading as empty. A separate agent used only `SKILL.md` to scrape a 1,000-book practice catalogue, proved completeness with three independent counts, and survived a SIGKILL restart.
- Measured on 135 pages of one Arabic and English site: trafilatura recalled 0.91 of the Arabic body text and 0.96 of the English, while jusText on defaults recalled 0.17 and 0.71 and left 53 pages nearly empty. selectolax parsed 158 pages about 10 times faster than BeautifulSoup with lxml, with identical titles and link counts. One site, one reference, word-overlap metric: re-measure on yours.
- A fresh agent given a "works on my laptop, 403 on the server" problem and a three-part tool-choice problem changed its answer because of the skill (it would otherwise have added proxies or a stealth browser, and chose a per-proxy headcount and a client-by-address grid instead).

## The line

Every source is run by someone, and your requests spend their capacity. The skill collects what any visitor may see without logging in, at a pace the server can carry, presenting itself as a browser does (real headers, the real TLS handshake through `curl_cffi`). It does not solve challenge pages or CAPTCHAs, does not rotate identities or proxies to get past a block, and does not go behind a login. The stealth and unblocking tools are catalogued so you can recognise them and weigh their risks, not as a recipe. Whether you may collect from a given source is your responsibility; this is not legal advice.

## Related

[browser-use skill](https://github.com/murtadha203/browser-use-skill): routes browser tasks (clicking, forms, logins) to the fastest tool. This skill is for the collection itself.

## License

MIT
