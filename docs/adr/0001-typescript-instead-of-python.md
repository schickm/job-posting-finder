# TypeScript on Node instead of Python

The map first settled on Python + uv. We switched to TypeScript on Node 24 LTS (pinned with mise, `.ts` run directly through type stripping, no build step) with pnpm as the package manager for all project code, because the user knows TypeScript and its tooling better. Python's scraping libraries were the main thing given up; both Job Boards work with plain HTTP, so no Python-only library is needed. The Python probe scripts from the research tickets stay as a historical record and are not rewritten.

## Considered Options

- **Bun**: built-in SQLite, test runner and package manager, but less proven for an unattended daily job.
- **Deno**: good TypeScript support, but not installed here and weaker npm compatibility.
