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

## `SECURITY-OWNERSHIP-1` — closed 2026-09-06

> | ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
> | --- | --- | --- | --- | --- | --- | --- | --- |
> | `SECURITY-OWNERSHIP-1` | blocked-external | Medium | Administrator branch-protection and CODEOWNERS receipt | Obtain administrator evidence for required checks, review, force-push protection, and sensitive-path review; local health must remain distinct from authority. | administrator authority receipt | `uv run python scripts/gates/security_scan.py` | repository files or a green local run must not imply remote protection |

### How it was closed

The owner (repository administrator) authorized configuration this session; the
platform state is the evidence, captured live from the GitHub API
(`GET /repos/docxology/template/branches/main/protection`, 2026-09-06):

- `required_status_checks.contexts = ["CI Gate"]` — the static gate job added
  in PR #55; `strict = false`.
- `allow_force_pushes = false`, `allow_deletions = false`.
- `enforce_admins = true`.
- `required_pull_request_reviews = null` — **deliberate deviation** from the
  row's "review" item: the maintainer works solo, and a self-review
  requirement would be ceremony without a second reviewer. Owner-authorized.

The negative control holds by construction: a green local run implies nothing
about remote protection — the receipt cites the live API state, and the first
protection-enforced merge (PR #58, `5db56301d`) merged only with a green
`CI Gate` check run on the platform.
