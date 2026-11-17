# Built In Chicago access

Research for [#3](https://github.com/schickm/job-posting-finder/issues/3) (parent map [#1](https://github.com/schickm/job-posting-finder/issues/1)). Observed 2026-11-17 from a residential IP with about 10 light, unauthenticated requests. Sources are Built In's own pages, robots.txt, Terms, and first-party JS. `builtinchicago.org` is the Chicago-scoped front of the same platform as `builtin.com`.

## Summary

- **Access method: server-rendered HTML plus embedded JSON.** No official API, RSS or Atom feed was found. Plain HTTP works: no browser, no login, no Cloudflare challenge seen. Search pages are fully server-rendered and carry a schema.org `ItemList` JSON-LD block. Detail pages carry a schema.org `JobPosting` JSON-LD block with the full description.
- **A Search Profile is a URL path plus a few query params.** Filters live mostly in path segments (remote preference, category, subcategory, experience level, industry, company size) plus `daysSinceUpdated`. Free-text `?search=` exists but is disallowed by robots.txt.
- **Stable ID is a numeric job id** (`/job/<slug>/<id>`, `JobPosting.identifier.value`). Dedupe on it.
- **Pagination is a Silent Failure trap.** `?page=N` is 25 per page, and a page past the end returns HTTP 200 with zero cards. robots.txt allows only `page=1`, `2`, `3` on `/jobs*`.
- **Terms and robots.txt conflict with automation.** Community Terms of Use section 3(f) prohibits access "through the use of bots, spiders, scrapers, web crawlers...". This is a policy risk to accept knowingly, not a technical blocker.

## Access method

| Option | Finding |
|---|---|
| Official API | None found. No developer docs linked from the site, robots.txt or sitemaps. |
| RSS/Atom | No `<link rel="alternate">` feed on `/jobs` pages. |
| Internal JSON endpoints | None needed. The site's own search UI (`main.bundle.js`) does not call a JSON API. It fetches the same URL with `handler=SearchResults` and injects the returned **HTML fragment** into `#jobs-list`. |
| Server-rendered HTML | Yes. 25 job cards per page are in the initial HTML. |
| Browser required | No. `curl` with a default UA and with a `python-httpx/0.27` UA both returned 200 with full content. |

Sizes seen: search page about 100-340 KB HTML, detail page about 84 KB, responses under 0.5 s.

The first-party JS (`https://static.builtin.com/jobs/js/main.bundle.<hash>.js`) builds the search URL in `updateJobs()`. It appends path segments in this order: remote preference alias, category alias, subcategory alias(es), experience alias(es), industry alias(es), company-size alias(es). It then adds query params (below). The bundle filename contains a content hash; do not hard-code it.

## Search filters and URL shape

Base: `https://www.builtinchicago.org/jobs`. Chicago is implied by the host (criteria JSON shows `city: Chicago, state: Illinois, geoName: Greater Chicago Area`).

Path form: `/jobs[/<remote>][/<category>[/<subcategory>]][/<experience>][/<industry>][/<company-size>]`

| Filter | Mechanism | Values (from the embedded `Builtin.jobBoardInit({...})` JSON on every `/jobs` page) |
|---|---|---|
| Work arrangement | path | `remote` (Fully Remote), `hybrid`, `office` (On Site). Multiple allowed as extra segments. |
| Category | path | List in `categoriesFilterOptions`, for example `dev-engineering`, `ai-machine-learning`. |
| Subcategory | path | Per category, for example `dev-engineering/python`. |
| Experience level | path | `internship`, `entry-level` (0-1y), `junior` (1-2y), `mid-level` (2-5y), `senior` (5-9y), `expert-leader` (9+y), `not-specified`. |
| Industry | path | Hundreds of aliases in `industryFilterOptions`. |
| Company size | path | `1-10`, `11-50`, `51-200`, `201-500`, `501-1000`, `1000+`. |
| Date posted | query `daysSinceUpdated` | `1`, `3`, `7`, `30` (UI: 24 hr, 3 day, week, month). Confirmed: criteria JSON echoed `daysSinceUpdated: 7`. |
| Keywords | query `search=` | In the UI. **Disallowed by robots.txt** (`Disallow: /jobs*?search=`). Not tested. |
| Skills | query `skills=` | Per the bundle; only honored with a search term or category. Not tested. |
| Early applicant | query `earlyApplicant=true` | Per the bundle. Not tested. |
| Company | query `companyId=` | Per the bundle. Disallowed on builtinchicago.org robots.txt. |
| Location | query `city`, `state`, `country`, `searcharea` (`5mi`..`100mi`), `allLocations=true` | Per the bundle. Not tested. |
| Salary | none | No salary filter. Salary is a displayed field only. |

Worked example (tested, HTTP 200): `/jobs/hybrid/dev-engineering/python?daysSinceUpdated=7&page=2`. The embedded criteria JSON showed `remotePreferences:"3"`, `daysSinceUpdated:7`, `pageNumber:2`.

Quirks: the `/jobs/dev-engineering/python` page's criteria JSON had `"search":"python developer"` pre-populated, and the hybrid/python URL was titled "Best Hybrid Software Engineer Jobs" (not "Python"). Page titles and criteria JSON are not reliable evidence of what filter applied, so the Search Profile should store the URL path and query directly. There is no "at least this seniority" filter; list experience aliases explicitly.

## Posting fields: search results vs detail

**Search result card (HTML):** job id, title, URL `/job/<slug>/<id>`, company name and `/company/<slug>`, relative age ("22 Days Ago"), work arrangement text ("Remote", "Hybrid", "In-Office"), location text ("Chicago, IL"), experience level text ("Senior level"), salary text when present ("160K-220K Annually", free-form string, many cards have none), industry tags, a short summary blurb, skill tags.

**Search page JSON-LD `ItemList`:** position, `name` (title), `url`, and a short `description` for each of the 25 items. Easy to parse for id and title; has no company, date, or location.

**Detail page JSON-LD `JobPosting`:** `title`, full HTML `description`, `identifier.value` (job id), `datePosted` (absolute date, for example `2026-10-26`), `validThrough`, `employmentType`, `jobLocationType` (`TELECOMMUTE` for remote), `applicantLocationRequirements`, `hiringOrganization` (name, company URL), `industry[]`, `jobBenefits[]`, `jobLocation` (the remote example had only country `USA`). The detail page also shows an Apply control.

For the Local Filter: title, company, relative age, arrangement, location, level and (sometimes) salary text are available without fetching details. The absolute posted date and full description need the detail page.

## Identifiers and duplicates

- `/job/<slug>/<numeric id>`; the same id appears as `id="job-card-<id>"`, `data-builtin-track-job-id`, and `JobPosting.identifier.value`. Use the integer id as the Posting key within the Site.
- Slugs repeat across different postings (`senior-software-engineer-python/11895953` and `/9949537`), so never key on the slug.
- Ids are not ordered by date (ids from about 8.3M to 12.2M appeared among postings 4-30 days old), so do not use them as a "newer than" cursor.
- Unknown: whether a repost keeps its id.

## Pagination

- 25 results per page; `?page=N`, 1-based.
- Tested on a narrow search: page 2 had 6 cards, and **page 3 returned 0 cards with HTTP 200** and normal page chrome. An empty page and a broken parse are indistinguishable by status code, so the parser must check card count and `numberOfItems`.
- The pager also linked to pages beyond the last (page 4 was linked from page 2), so do not follow pager links blindly. Stop on the first page with fewer than 25 cards.
- No total result count was found in the page text, so loop until a short page.
- Pages 2+ carry `<meta name="robots" content="NOINDEX">`.

## Cost of detail pages

- One extra GET per new, filter-passing Posting: about 84 KB, about 0.3-0.5 s.
- The description is in the JSON-LD as an HTML string; no further requests or JS needed.
- A daily Run is a few search requests plus one request per new Posting that passes the filter.

## Anti-bot controls

- Behind Cloudflare (`server: cloudflare`, `__cf_bm` cookie, `cf-ray` header).
- About 10 requests with about 3 s gaps: no challenge, 403, or 429. A default `curl` UA, a Firefox UA and a `python-httpx` UA were all accepted. No cookies or special headers were needed.
- That is a small sample. Cloudflare bot scoring can change without notice, so treat any non-200, a challenge body, or a page missing the `ItemList` JSON-LD as a failure and log it. This is the main Silent Failure surface for this Site.

## robots.txt

`https://www.builtinchicago.org/robots.txt`, `User-agent: *`:

- Disallowed that matter here: `/jobs*?search=`, `/jobs*?f*`, `/jobs*?companyId=`, `/jobs*?trending*`, `/jobs/office*`, `/jobs/workspace*`, `/jobs/vendor*`, `/jobs/*size`, `/jobs*%`, `/search`, `/apply/`, `*?page=`, `*?region_id=`, `/views/ajax?*`.
- Allowed by exception: `/jobs*?page=1$`, `?page=2$`, `?page=3$` (the more specific Allow beats `Disallow: /jobs*?page=`). Page 4 and above are disallowed.
- Not disallowed: `/jobs`, `/jobs/<remote|hybrid>/<category>/<subcategory>/<experience>`, `/job/<slug>/<id>`, and `daysSinceUpdated`.
- `/jobs/office*` and `/jobs/*size` are disallowed, so On Site and company-size path filters are off limits to a compliant crawler; `remote` and `hybrid` are not.
- AI bots (`GPTBot`, `OAI-SearchBot`, `ChatGPT-User`, `PerplexityBot`) are disallowed site-wide. Not directly relevant to a personal script.
- `builtin.com/robots.txt` additionally disallows `/jobs*chicago` and `*?page=`, so the Chicago host is the right one.
- No `Crawl-delay`.

Practical effect: at most 3 pages x 25 = 75 results per search path are robots-compliant. For more coverage, split into narrower paths (subcategory, experience, arrangement) or use `daysSinceUpdated=1` to cap daily volume. Keyword matching should be done by the Local Filter, since `?search=` is disallowed.

## Terms of service

Built In Community Terms of Use, dated May 23, 2025: https://builtin.com/legal/community-terms-of-use (linked from the builtinchicago.org footer). Section 3, "Your Conduct": you may not "(f) access, use or copy any portion of the Site or Services through the use of bots, spiders, scrapers, web crawlers, indexing agents, or other automated devices or mechanisms". The terms bind all visitors and users of the Built In sites. Disputes go through pre-arbitration and AAA arbitration (section 7).

A separate Business Terms of Use (`builtin.com/terms-use`) applies to paying customers; not reviewed. No public API terms or developer license was found.

Reading: an unattended daily scraper breaches 3(f) as written, even at low volume. Enforcement against a personal low-volume tool is unlikely, and the realistic consequence is IP blocking. This is the owner's call; flagged, not resolved here.

## Recommendations for the spec

- Use plain HTTP and parse the JSON-LD blocks in preference to CSS selectors. Use card HTML only for fields JSON-LD lacks (company, relative age, level, salary text).
- Store each Search Profile entry as a URL path plus query, each within the 3-page limit.
- Silent Failure signals to log per Site: HTTP status, presence of the `ItemList` block, `numberOfItems` versus card count, zero cards on page 1 of a profile that normally has results, and a detail page without a `JobPosting` block.
- Keep a polite pace (this research used about 3 s gaps).

## Open uncertainties

- `?search=`, `?skills=` and location params: not tested (some robots-disallowed).
- Whether reposts get a new id, and how long expired jobs stay reachable.
- Cloudflare behavior over weeks of daily use; only about 10 requests were observed.
- Stability of HTML class names. The JSON-LD is the safer contract.
