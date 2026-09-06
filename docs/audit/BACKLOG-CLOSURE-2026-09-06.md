# Backlog closure record — 2026-09-06

Root `TO-DO.md` is future-work-only; completed rows move verbatim to this dated
evidence record in the same commit. Continuation of
[BACKLOG-CLOSURE-2026-09-05.md](BACKLOG-CLOSURE-2026-09-05.md).

## `ARCHIVAL-TRACKER-MIN-1` — closed 2026-09-06

> | ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
> | --- | --- | --- | --- | --- | --- | --- | --- |
> | `ARCHIVAL-TRACKER-MIN-1` | blocked-external | Medium | Credential-free provider evidence and current public roster | Refresh the archival tracker only from current queue/browse evidence and record accepted, pending, verified, unavailable, rate-limited, and excluded states with as-of dates. | archival tracking receipt | `uv run python scripts/runner/archive_publication.py --project templates/template_code_project --providers software_heritage` | missing credential/provider or standalone bundle must never report a completed deposit |

### How it was closed

The row's dependency was mislabeled `blocked-external`: tracking Software
Heritage's public state needs **no credentials, no submission, and no owner
authorization** — only read-only `GET` evidence. Two pieces landed:

1. **Credential-free refresh machinery.** `SoftwareHeritageProvider.check_status`
   (exposed as `check_publication_status` and via
   `archive_publication.py --check-status` / `archival_cli --check-status`)
   queries the save-queue and origin-visits endpoints, aggregates the `.git`/bare
   URL variants (SWH keys origins by exact URL; Git remotes carry `.git`), parses
   both the object- and list-shaped save payloads the live API returns, and
   records `extra.state` in the tracker taxonomy — `verified`, `accepted`,
   `pending`, `excluded`, `unavailable`, `rate-limited` — with an as-of timestamp.
   It never posts; the negative control holds structurally (a transport failure
   yields `status="error"`, a 429 yields `rate-limited`, and neither is ever
   reported as a deposit).

2. **Full-roster census with as-of dates.** All 61 documented own-public origins
   refreshed 2026-09-06 (single pass, read-only): **17 verified** (visit evidence,
   save requests `accepted`), **43 unavailable** (no save request, no visits),
   **1 rate-limited mid-census** (`institute_website` — state unknown, not absent).
   The tracker snapshot [docs/maintenance/software-heritage-archival.md](../maintenance/software-heritage-archival.md)
   now carries the dated census table; the prior 2026-06-27 "accepted/pending"
   list has fully landed (all 11 verified). Per-repo receipts are in the operator
   cache (`swh-tracker-refresh-2026-09-06.json`); the committed doc is the durable
   record.

### Out of scope (unchanged)

Submitting the remaining ~44 origins (save-code-now `POST`s) is a public
archival submission and still requires explicit owner authorization. The
tracker records where things stand; it does not authorize the next deposit.
