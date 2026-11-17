# LinkedIn access: logged-out vs logged-in

Research for issue #2. Date of observations: 2026-11-17. Single-user tool, one Run per day, residential IP.

Legend: **[verified]** = I observed it with a handful of unauthenticated requests today. **[source]** = stated by a primary source (linked). **[unverified]** = not tested (I did not log in) or secondary-source knowledge.

## Bottom line

- Logged-out guest access works today with plain HTTP (no browser, no JS, no login) **[verified]**. It exposes enough for a Local Filter on title / company / location / posted date, plus description, seniority, employment type and industry on the detail page.
- Logged-in scraping likely adds richer filters and fields, but it is the only mode that puts the user's real account at risk. LinkedIn's terms forbid scraping in both modes, but only logged-in use has an account to lose.
- For a roughly daily, low-volume job, guest mode has the better risk/reward. The main cost is Silent Failure risk: these are undocumented endpoints that can change, or start returning empty or auth-wall responses, without notice.

## Terms and robots.txt position

- User Agreement (effective 2025-11-03), section 8.2 forbids using "software, devices, scripts, robots or any other means or processes" to "scrape or copy the Services", bypassing "access controls or use limits", and using "bots or other unauthorized automated methods to access the Services". Section 3.4 and section 5: LinkedIn may "restrict, suspend, or terminate" the account. Source: https://www.linkedin.com/legal/user-agreement **[source]**
- Help page on prohibited software: LinkedIn does not permit third-party "crawlers, bots, browser plug-ins, or browser extensions"; users risk having accounts restricted or shut down; tools may stop working at any time. Source: https://www.linkedin.com/help/linkedin/answer/a1341387 **[source]**
- robots.txt (https://www.linkedin.com/robots.txt, fetched today): the header says automated access "without the express permission of LinkedIn is strictly prohibited"; the final group is `User-agent: *` / `Disallow: /`. The Googlebot group also explicitly disallows `/jobs-guest/` and `/jobs?runSearch*`. So the guest endpoints are disallowed to generic bots. Permission to crawl is by email to whitelist-crawl@linkedin.com; not realistic for a personal tool. **[source]**
- Net: both modes conflict with the terms and robots.txt. Logged-out, there is no account of the user's to sanction (whether browsewrap terms bind a non-logged-in visitor is a legal grey area). Logged-in, the user has expressly accepted the contract and LinkedIn has a named remedy against that account.

## Legal context (brief, not legal advice)

- hiQ v. LinkedIn, 9th Cir. (2019, reaffirmed 2022 after remand in light of Van Buren): scraping publicly accessible pages is likely not "without authorization" under the CFAA. This helps for logged-out public pages; it does not address contract claims. Opinion: https://cdn.ca9.uscourts.gov/datastore/opinions/2022/04/18/17-16783.pdf **[unverified: cited from memory, not re-read]**
- N.D. Cal., Nov 2022: the court held the User Agreement's scraping and fake-account bans enforceable against hiQ (which had also used fake accounts). Dec 2022 stipulated consent judgment: permanent injunction, $500k judgment, data deletion. Stipulation: https://s3.documentcloud.org/documents/23429042/hiq-stip.pdf ; summary (secondary): https://www.proskauer.com/blog/hiq-and-linkedin-reach-proposed-settlement-in-landmark-scraping-case
- 2025 suits against commercial scrapers using fake accounts: Proxycurl/Nubela (N.D. Cal. 3:25-cv-00828, shut down mid-2025) and ProAPIs (3:25-cv-8393). LinkedIn announcement: https://news.linkedin.com/2025/linkedin-takes-legal-action-to-defend-member-privacy ; case numbers are from secondary news, dockets not read.
- Practical takeaway (my assessment): LinkedIn litigates against large commercial resellers. For a single-user, once-a-day personal tool, the realistic consequence is account action (logged-in) or IP throttling (logged-out), not litigation.

## Logged-out (guest) mode

Endpoints observed **[verified]** (all HTTP 200 with plain `curl`, with a Chrome UA and also a `python-requests/2.32` UA; no cookies):

| Purpose | URL |
|---|---|
| Search results (HTML fragment) | `https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=...&location=...&start=N` |
| Detail (HTML fragment) | `https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{jobId}` |
| Full public job page | `https://www.linkedin.com/jobs/view/{jobId}` (about 330 KB; no authwall seen) |
| Public search page | `https://www.linkedin.com/jobs/search/?keywords=...&location=...` (about 300 KB; cards rendered server-side) |

Fields **on search result cards** **[verified]**: job id (`urn:li:jobPosting:ID`), title, company name and company URL, location text, posted date (`<time datetime="YYYY-MM-DD">` plus relative text), job URL with tracking params, company logo, optional "Actively Hiring" badge. No description, seniority or salary on cards in my sample.

Fields **on the detail fragment** **[verified]**: title, company, location, relative posted time, applicant count caption, full description (HTML), and a criteria list: Seniority level, Employment type, Industries (Job function when present). No `JobPosting` JSON-LD found in the `/jobs/view/` page I fetched. Salary was absent in my samples; presence on other postings is **[unverified]**.

Search filters a Search Profile can express. Accepted with HTTP 200 and cards returned **[verified]**: `keywords`, `location`, `f_TPR=r86400` (date posted, seconds window), `f_WT=2` (workplace type), `f_E=4` (experience level). I did not check that results honored each filter. Others commonly used by the public UI **[unverified]**: `geoId`, `distance`, `f_JT` (job type), `f_SB2` (salary bucket), `sortBy=DD|R`, boolean operators in keywords. `f_WT` values (1 on-site, 2 remote, 3 hybrid) are from convention. A Search Profile can mostly be stored as a query string.

Pagination **[verified]**: 10 cards per request. `start=100` returned 10 cards; `start=975` returned an empty 26-byte body (still HTTP 200); `start=1000` returned HTTP 400. So the cap is roughly 1000 results per query. With `f_TPR=r86400` a daily Run needs only a few pages.

Rate limits and anti-bot **[verified for light use]**: about 9 requests spaced 3 seconds apart from a residential IP: all 200, no CAPTCHA, no authwall, no 429. At higher rates or from datacenter IPs, HTTP 429, HTTP 999 (LinkedIn's custom block) and redirects to `/authwall` are widely reported **[unverified, secondary]**. I did not provoke these. `/authwall` appears in robots.txt **[source]**.

Browser required: no. Plain HTTP plus an HTML parser is enough. The failure mode is quiet: the end-of-results response was HTTP 200 with a 26-byte body. Silent Failure detection should therefore rely on Posting counts and a check that expected card markup (`base-search-card`) is present, not on status codes.

Account risk: none (no account). Risks are IP throttling and sudden endpoint or markup change.

## Logged-in mode **[all unverified: I did not log in, per instructions]**

- Reachable: the full jobs UI and its internal JSON API, with richer filters (e.g. Easy Apply, company, industry, network), possibly salary and applicant insights, and possibly no 1000-result cap.
- Needs valid session cookies or a login flow. LinkedIn fingerprints logged-in automation; checkpoints, CAPTCHAs, forced re-login, temporary restriction or permanent ban are the plausible consequences (help page above: accounts "restricted or shut down").
- A real browser is typically used to hold the session. Replaying the internal API with cookies is exactly the "bypass access controls or use limits" the terms forbid.
- Cookie expiry adds a further Silent Failure mode.
- The risk lands on the user's primary professional account, the asset most costly to lose.

## Comparison for the decision

| | Logged-out | Logged-in |
|---|---|---|
| Card fields | id, title, company, location, date | likely more (unverified) |
| Detail fields | description, seniority, type, industry | likely more (unverified) |
| Filters | keywords, location, date, workplace, experience | superset (unverified) |
| Results cap | about 1000 per query | unknown |
| Browser | no | probably yes |
| Account risk | none | real, ban possible |
| Terms | conflicts, no account to sanction | breach, account sanctionable |
| Silent Failure modes | endpoint/markup change, empty bodies, authwall/999 | those plus cookie expiry, checkpoints |

## Open uncertainties

- Behavior at higher request rates (429/999 thresholds) not tested.
- Filter semantics (`f_WT` values, `f_JT`, `f_SB2`, `geoId`, boolean keywords) not individually validated against results.
- Whether salary appears in guest detail for some postings.
- Logged-in details come from general knowledge, not testing.
- hiQ 9th Cir. opinion not re-read; 2025 case numbers come from news, not dockets.
- Guest endpoints are undocumented and may change without notice.
