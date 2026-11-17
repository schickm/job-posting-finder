# Job Posting Finder

A personal tool that collects job postings of interest from a fixed list of job aggregation websites, on a recurring schedule, without failing silently.

## Language

**Job Board**:
One job aggregation website on the predefined list (for example LinkedIn, Built In Chicago).
_Avoid_: Site, source, provider, aggregator

**Search Profile**:
The set of search criteria for one Job Board, in that Job Board's own shape. Each Job Board has its own Search Profile; there is no global profile shared across Job Boards.
_Avoid_: Query, filter set, global profile

**Posting**:
One job advertisement as found on a Job Board.
_Avoid_: Job, listing, ad

**Local Filter**:
Rules applied on this machine to scraped Postings, after the Job Board's own search, to decide which Postings are Matches. One set of rules applies to all Job Boards.
_Avoid_: Post-filter, Search Profile (that is the search on the Job Board)

**Match**:
A Posting that passed the Local Filter, for the user to review. A Match is either Viewed or not Viewed.
_Avoid_: Result, hit, candidate

**Silent Failure**:
Any situation where the system stops collecting Postings correctly and the user is not told: a scheduled run that never starts, a run that crashes, or a Job Board that returns empty or malformed results without an error.
_Avoid_: Outage, bug
