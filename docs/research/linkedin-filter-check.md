# LinkedIn guest search: which filters apply

Task for issue #9. Observed 2026-11-18 from this machine's residential IP, Python `urllib` default User-Agent, no cookies. 38 requests in three batches. Raw data: [`linkedin-filter-check/`](linkedin-filter-check/) (`p1.json`–`p3.json` = parsed cards and detail criteria per probe; `requests.jsonl` = every request and status; `probe.py` + `p*.py` = the scripts).

Baseline query: `keywords=software engineer`, `location=Chicago, Illinois, United States`. Guest endpoint: `/jobs-guest/jobs/api/seeMoreJobPostings/search`. Logged-out UI: `/jobs/search/`.

## Result per filter

| Filter | Guest search | Logged-out UI | Evidence |
|---|---|---|---|
| `keywords` | applied | applied | results follow the words |
| `keywords` with `"quotes"` | applied | not tested | `"site reliability"`: 8 of 10 titles contain the phrase, rest are JPMorgan SRE-adjacent roles |
| `keywords` with `OR` | applied (probably) | not tested | `golang OR rust`: Go / Rust / SRE titles, none of the baseline list |
| `keywords` with `NOT` | applied | not tested | `engineer NOT senior`: zero "Senior" titles; graduate / entry-level / non-software engineers |
| `location` | applied | applied | Austin → all cards `Austin, TX` |
| `geoId` | applied | applied | `103112676` → Chicago, `90000064` → Austin, no `location` text needed |
| `distance` | applied | applied (UI control exists, default 25 mi) | Naperville `distance=0` → all cards `Naperville, IL`; `distance=50` → Chicago cards. (Chicago 5 vs 100 mi was identical on page 1: dense city, not evidence.) |
| `f_TPR` | applied | applied (UI control) | `r86400` → all dates 11-17 / 11-18; `r604800` → all dates 11-12…11-18 |
| `f_WT` (1, 2, 3, `1,2`) | **ignored** | **ignored** | all four values return the identical 10 cards in the identical order |
| `f_E` (2, 5) | **ignored** | **ignored** | `f_E=2` (Entry) and `f_E=5` (Director) return the unfiltered list; detail pages say `Mid-Senior level` for both |
| `f_JT` (`C`, `I`) | **ignored** | not tested | Contract and Internship return the unfiltered list |
| `f_SB2` (`7`) | **ignored** | not tested | returns the unfiltered list |
| `sortBy` (`DD`, `R`) | **ignored** | **ignored** | identical lists, not in date order |

"Unfiltered list": LinkedIn serves the baseline query in one of two orderings (call them A and B) that alternate between requests regardless of parameters. Every ignored-filter probe returned exactly A or B. The logged-out UI probes with `f_WT=2`, `f_E=5`, `sortBy=DD` returned list B, showed the same `4,000+` count, and showed only the Distance filter as applied.

## The logged-out UI's filter bar

The server-rendered logged-out `/jobs/search/` page offers only three filters: **Distance** (0, 5, 10, 25, 50 mi), **Company** (`f_C`), **Date posted** (`f_TPR`: past 24 h, week, month). No workplace type, experience level, job type, salary, or sort. So those values cannot be copied from the logged-out UI, and adding them to the URL by hand changes nothing.

## Rate limit

- Batch 1: 3–6 s random delay. Requests 1–14 → 200; request 15 → **429**, empty body (about 60 s in).
- After 5 min idle: one request → 200.
- Batch 2: 10–15 s delay. Requests 1–14 → 200; request 15 (a detail fetch) → **429** (about 3 min in, plus the 1 probe before it).
- Batch 3, after about 7 min idle: 8 requests at 8–12 s → all 200.

So the block looks like a count budget of roughly 14–15 requests per window (window length unknown, under 5 min to recover), shared by search and detail endpoints, and not avoided by slower pacing. No `999`, no `/authwall` redirect seen. The planned per-Run maximum (10 search pages + 50 detail requests) does not fit.

## Does the Playwright fallback help?

No. The fallback in issue #4 is a browser on the **logged-out** UI. That UI ignores the same filters (it has no controls for them, and hand-added URL params change nothing). A browser would cost a Recording per Run and gain nothing. Only logged-in search applies these filters, and issue #4 ruled logged-in out.

## Fields available to a Local Filter instead

- Workplace type: not a structured field on cards or the detail fragment. Only free text: the location text and the description (both baseline postings mention "remote").
- Seniority level, Employment type, Industries: structured criteria on the detail fragment.
- Salary: no structured field seen; only text inside the description (`$` present in the sampled descriptions).
