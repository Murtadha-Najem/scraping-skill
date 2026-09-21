# Trusting the result: how to try to prove yourself wrong

Collection without validation is just downloading. The habit is to attack your own result before anyone else does, using something the data did not come from. For enumerator-collected field survey data use the `data-quality-check` skill; this file is for scraped and derived data.

## A number is a claim with a chain behind it

Before you say anything about a figure, walk the chain: what was counted, in what unit, against what population, by which path through the code.

- **Reconcile counts at every stage boundary.** Every stage announces a number; each must equal the stage before, or you must be able to say why. This caught rows silently overwritten between stages and a source file counted twice, neither of which raised an error and neither of which was visible
  in the output, only in the arithmetic between stages (`scrapekit.Reconciler`).
- **A check only proves the path it runs through.** A governorate sheet shipped with a grand total that reconciled exactly (official towers 17,933, mapped sites 1,833, share 10.2%, every figure right) while 13 of 18 rows underneath were nonsense. The total was summed from the sources and never touched the join.
  Totals validate totals. To validate a join, count rows: 18 onto 18 must give 18.
- **Name the unit on top and the unit underneath before any ratio.** A crowd database counts cells and a regulator counts towers, and one tower shows up as six to fifteen cells: 51,546 over 17,933 gave 287%, impossible, and it would have read as excellent coverage.
- **Get the denominator right.** A check compared against an ever-growing archive would have quietly stopped detecting anything within weeks while still printing a plausible number. Ask what the ratio will read after the store has grown tenfold.
- **A filter defined by listing values can be wrong in both directions at once.** A site count of 1,347 was padded with 1,084 floodlight masts and missing 828 real communication towers; the errors partly cancelled and the total looked unremarkable. Audit both edges. Plausibility is not evidence.
- **Rows equal unique ids, fill rates per field, ranges, category distributions.** A 0% column is a bug, not missing data (a phone column was empty for two sections because the field was named differently there).
- **A check that returns zero must be shown able to fire** (extraction.md).

## What counts as evidence

- **Two independent sources agreeing** is real corroboration. 89 of 96 groupings agreed across two separate sources, and the rest sat on genuine borders.
- **A source cannot referee itself.** A cross-check between two levels of one reference source reported 427 problems, every one the source contradicting itself (each level simplified independently, so they no longer shared edges). The column was deleted rather than shipped. Hand-inspect what any new check flags before it
  ships, and prefer deleting a check you cannot justify to shipping it with a caveat, because a flag carries more authority than a raw value.
- **Internal redundancy is a free audit.** One figure published in two currencies should have a constant ratio equal to the real rate; a total and its parts; a percentage and its base. The ratio sat exactly at the official rate for each year in one job and returned nonsense in three years of another, locating mis-mapped columns in seconds.
- **The publisher's own headline is an exact target.** One extraction matched a published total to the dollar for one year and came out at exactly 2.0000x for another. A round multiple is a structural fault, not noise. Ship the comparison per period, and call a period with no published figure unverified, which is a different word from wrong.
- **The cheapest test that can refute a label is usually already in the data.** Two operator codes had been labelled from memory and swapped; one latitude column settled it (66% of the cells lay north of 35.2 degrees, inside Kurdistan, where that operator was founded), with no network call. Ask what the held data would have to look like if
  the label were wrong, then look.
- **A lookup that returns data does not confirm your labels.** The query succeeds on the identifier alone, so a wrong name beside it reads as correct. Take identifiers and names from the same authoritative listing.

## Distrust the striking number

A striking number is a reason to investigate, not to publish. A regional figure came out seven times the national norm; almost every record behind it was nameless, the owner fields held values that were not owners, and a fifth sat inside one square kilometre, one contributor's bulk entry. Construct the most plausible
"this is my bug", test it, and report the test with the result. An exact multiple is structural. Where doubt survives, ship both readings, one figure for what the data contains and one for what it can identify, with a sentence saying which is which.

Comparisons need the same ground. Two runs that searched different districts made one scraper look four times better (72% against 28% phone coverage); anchored on the same coordinates, 72% collapsed to 31%. Comparing two tools on two samples measures the samples. And a paginated result's page size is not the result:
"Fetched 93 of 100 items" was the page size requested, not the yield, and the wrong denominator gave 31% where the truth was 29%.

More ways a sample fools you: the head of an ordered list is almost never random (insertion date, alphabet and size each correlate with what you measure); an in-flight estimate extrapolated from the first group is biased if the order is grouped; a hypothesis confirmed on one sub-population can fail on its neighbour ("the provider names the
operator in the title" held 10 of 10 on one type and 40% on the next). Say how a sample was drawn, and change the claim if the method does not match it ("the newest" that was really "whatever was cached").

Low coverage may be the ceiling of the source, not a defect. Google Maps phone coverage is about 70% in northern Baghdad and 29% in the south across three different scrapers, so a low rate is not a scraping failure to re-run, and a citywide average hides a real gradient.
Report the coverage of a technique's signal, not only its accuracy where the signal exists: names carry a signal on a minority of records. Inspect crowd-contributed extremes for a single contributor's signature and label the artefact beside the number rather than dropping it quietly.

## Telling the reader

- **Collection is not analysis.** Gathering documents and turning the numbers in them into a comparable database are two projects, the second much larger. Say which one you delivered and what you deliberately did not derive.
- **Say what you did not capture.** After bounded probing that failed consistently, state what is unavailable, how many routes you tried, and what related data you captured instead. Declared partial completeness is worth more than claimed completeness.
- **Index before you bulk download.** One cheap pass that maps what exists answers whether the expensive pass is worth it, and the index is the download list.
- **Ship judgements as columns, not filters.** Anything removed silently is a number the reader cannot check, and can disagree with.
- **Make each deliverable self-contained**: sources, licences, method, findings, limits and what is outstanding travel inside the file, and two deliverables from one capture must not reference each other. Split by question and audience, not by shared capture. Carry attribution with the column that came from an open source.
- **Never merge silently.** Keep a `source` column. Proximity may merge records across two sources but within one source require the names to agree too: distance alone collapsed 190 distinct records in a dense city. Compare names on more than one axis (token overlap and a consonant skeleton catch different errors), and
  measure any clever normalisation against the naive baseline.
- **Do not soften, round away or omit an unflattering number.** State it beside what it means and what would improve it.
- **Do not modify a shared external store** (Drive, a shared sheet) without a per-action instruction. Do the work locally and hand the owner the change.
- **When told not to redo something,** state the evidence once and comply, and flag the consequence in the documentation instead of repeating the argument.
- **Search the wider workspace for existing assets** (boundary files, lookups) before acquiring them, and copy them into the project with their licence.
