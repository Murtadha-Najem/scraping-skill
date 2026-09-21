# Turning responses into rows without fooling yourself

A crash is the safe way to fail: it tells you something broke. The failures worth your worry produce plausible output that is silently wrong, and most of extraction is the habit of asking one question of every line
you write: **how could this give me a full, tidy, wrong answer, and what would I see if it did?**

## Choose the parser by what it must survive

| Job | Reach for | Why, and what was measured |
|---|---|---|
| Fast HTML parsing and CSS selectors at volume | **selectolax** | A C parser (Lexbor or Modest). 158 pages of a law-firm site: 0.34 s against 3.36 s for BeautifulSoup with lxml, about 10x, with identical titles and link counts on all 158. An earlier 80-page run gave 12x |
| Selectors inside Scrapy, or XPath | **parsel** | Scrapy's own layer over lxml; XPath can express things CSS cannot (axes, text predicates) |
| Very broken markup, a one-off | BeautifulSoup | Forgiving and slow, and its parser backend changes what it does with bad HTML |
| The main text of an article, without menus and ads | **trafilatura** | 135 pages of a law-firm site against the crawler's own cleaned Markdown: recall 0.91 Arabic, 0.96 English; precision 0.96 and 0.98; no empty outputs |
| The same, as a second opinion on English | jusText | Same 135 pages on defaults: recall 0.17 Arabic and 0.71 English, and 53 of 135 pages nearly empty |

The text-extractor numbers deserve honesty about their limits: the reference is one crawler's cleaning of one site, compared by word overlap, and jusText was not tuned. A likely cause of its Arabic failure is that it
classifies paragraphs by length and stoplist density, which suits long running prose and not a structured legal page of short headings, lists and FAQs; that is an explanation, not a proven cause. The gap is too wide for a better reference to reverse.
Re-measure on a different site, and read a few outputs by eye, before generalising. An earlier one-page check on an Arabic services page had said "jusText works with a caveat", and one page was not a sample.

selectolax in brief: `tree = HTMLParser(html)`, `tree.css_first("title")`, `.text(strip=True)`, `.attributes.get("href")`, `tree.css("a[href]")`; to get visible text only, `.decompose()` the `script, style, noscript` nodes first.

## Embedded data beats markup

When the page carries its own JSON (`__NEXT_DATA__`, `self.__next_f.push` chunks, JSON-LD), read that. It has the record the template drew from, not what the template chose to show. When a site moves from one format to another the data does not change and only
the reader must (a used-car site moved between the two formats overnight; its reader handled both, old first, and a canary caught the change before a single false 404 was written). Anchor regexes on whitespace-tolerant patterns, and when you hold an id the match must be that exact
record, because an id also appears inside its brand, its city and the cars shown beside it. Patch a parser with exact anchors and check for stray control characters afterwards: a `\b` inside a nested string became a literal backspace and could never match.

## How wrong data looks right

**Position instead of label.** A right-to-left table hands you columns in an order you did not expect. Parse by position and the annual figure lands where the first-quarter one belongs, for every row, forever, with no error. Read the header row, map label to index, and
carry unknown labels through instead of dropping them, so a new column shows up instead of vanishing.

**Patterns written in the wrong form.** If you fold letter variants and strip diacritics before matching, the patterns must look like text after that step, not like text a person writes. A pattern in natural form never fires, and the records it should catch fall into "unknown"
while announcing what they are in their own names. Assert that every alternative in a pattern fires at least once on the corpus: an alternative with zero hits is a bug until shown otherwise.

**Names typed from memory.** The same place is spelled differently by different sources. A mapping typed from memory got 4 of 18 wrong (641 false mismatches). Typing `Ninewa`, `Basrah`, `Muthanna` against a file that says `Ninawa`, `Al-Basrah`, `Al-Muthanna` silently failed 13 of 18 joins. The clever
alternative, a derived key that strips articles and vowels, was worse (1,286 mismatches) because it split two spellings that differ by a trailing letter and merged two that had to stay apart. When the set is small and closed, enumerate it: print both lists, write the map,
and assert that it fails loudly if either side gains a name it does not cover, in the same edit. Feeling that eighteen names are too few to guard is exactly the condition under which this error occurs. Build alias tables from the values actually present (direct matching recovered 25 of 621; aliases
read off the field took it to 312), and measure the join rate before and after so the table's value is a number.

**Names that collide.** Reducing a non-Latin filename to ASCII maps different inputs to one output and the second silently overwrites the first: 57,554 rows lost across six years, no error, the run reported success, and the overwriting file was tiny so it looked like a source with little data.
Use an index and a digest (`scrapekit.unique_names`) and assert the number of distinct names equals the number of inputs.

**A check that returns zero.** A search for `Total` found no subtotal rows, and that was taken as proof; the label was `Total chapter` and 506 subtotals were summed as data. A null result is evidence only if the test could have fired: match loosely first, look at what the field actually
contains, then tighten.

**Different names for the same thing.** One section stored phones under `phone_number`, others under `phone`, `whatsapp`, `SecondaryPhone`; hard-coding one key gave a column full for what you tested and empty elsewhere, which reads as "no data" instead of "wrong key". Walk the object, match
values against the pattern, and write one accessor that tries every known key and emits an "all values found" column so a miss is visible. Fields also change shape between records (`"country": "العراق"` in one, `{"title": {"AR": ...}}` in the next broke an export after 100,000 rows), so normalise doubtful fields through one helper,
and keep languages in separate columns.

**The singular and the zero.** A regex for "N results" matched only the plural, so ten one-book categories read as having no header, and the records still passed because the books were present. Feed every text pattern the 0, 1 and 2 forms, and Arabic dual and plural forms, before you trust it.

**The encoding guess.** A `text/html` answer with no charset makes `requests` guess latin-1, so a pound sign or any Arabic text arrives as mojibake and a collector that saves it saves it wrong. Set `r.encoding = "utf-8"` when the `Content-Type` names none (the runner template does), or decode `resp.content` yourself.

**Blank means different things.** A required owner that is blank is a gap worth closing; an optional owner that is blank may be the finding. Decide per entity type and write the decision down.

**Keyword classifiers that delete real records.** Entities are often named after things rather than being them (neighbourhoods, saints, founders). Ask what else in the domain carries that word as a name, require positive evidence before a destructive class, read what a rule excludes before shipping it,
and ship judgements as columns rather than filters.

**Links.** Resolve relative links against the fetched document's final URL with `urljoin`, not against the origin. A wave of 404s on links you extracted is a resolution bug before it is a source problem.

## Store the raw response next to the extraction

The schema you extract into encodes today's understanding of what matters. A field you skipped is indistinguishable from one that never existed once the raw is gone, and re-fetching 100,000 records is over 20 hours against about 800 MB of disk. The fix for the singular-case bug above cost no refetch
because the raw HTML was saved. Make full capture the default and reduction the opt-in, and say the storage cost up front so the trade is visible.

## Writing files

Fix these at the source, not after the failure: sanitise every value in one central function (serialise `dict` and `list` with `json.dumps(ensure_ascii=False)`, strip control characters with `openpyxl.cell.cell.ILLEGAL_CHARACTERS_RE`, truncate near 32,000 characters), because one bad cell otherwise aborts the write after every row is built.
Type by column, not by value: model names made of digits (`01`, `06`, `07`) lost their leading zero when cells were typed by what they looked like, and Sheets' `setValues` also parses digit strings. Use `utf-8-sig` for CSV with Arabic or Excel shows symbols, and prefer xlsx for a deliverable because a csv has no types.
Files written on Windows carry CRLF, and `grep -E "^[0-9]+$"` then matches nothing while a merge silently keeps 25 ids and reports success. Compute derived columns once at flatten time. Count by the right date: `SaveDate`, not `UploadedDate`, when the second is a renewal date.

## Documents and Arabic text

Text extracted from a PDF can be in visual order, faithful and unusable until reordered, so check a known string early. Percent-encode non-ASCII in paths before requesting, or the failure looks like a missing file. Parse JSON string literals with a JSON parser. Sample across producers before judging a corpus.

## Selectors that survive a redesign

Sites change and selectors break. The useful idea from the self-healing scrapers (anansi, which is not recommended to run) is cheap to do by hand: keep two or three independent selectors per field, track each field's fill rate per run, and let a sudden drop in one field raise an alert,
so a redesign is noticed the same night and not weeks later.
