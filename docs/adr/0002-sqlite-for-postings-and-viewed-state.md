# SQLite for Postings and Viewed state

The map first said to start with plain files for storage. We chose one SQLite database file (in `~/.local/share/job-posting-finder/`, opened with the built-in `node:sqlite` module) because two processes write: the Sweep writes Postings and the Match review web app writes the Viewed state. SQLite in WAL mode with a `busy_timeout` handles both writers safely, gives the web app easy "not Viewed, newest first" queries, and keeps Postings linked to the Sweeps that found them. Plain JSON files that a person can `cat` were the main thing given up. Migrations are ordered SQL files tracked by `PRAGMA user_version`, so no ORM is needed.

## Considered Options

- **Plain files, one writer for each file** (one JSON file per Posting, a separate marker file per Viewed Match, atomic rename): safe, readable with `jq`, but every query reads the whole directory and relations between Postings and Sweeps are manual.
- **`better-sqlite3`**: stable, but a native addon that must be built or downloaded for each Node version. `node:sqlite` prints an `ExperimentalWarning` on Node 24; mise pins Node, so an API change only arrives with a deliberate upgrade.
- **Drizzle**: type-safe queries and migrations, but the only reason for it was migrations, and `PRAGMA user_version` with SQL files covers that.
