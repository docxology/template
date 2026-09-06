# Software Heritage archival — docxology repositories

> Status snapshot: 2026-09-06 (full 61-origin census via the read-only
> `--check-status` refresh; see "Verified census" below). Records which docxology
> public repositories have been archived by Software Heritage (SWH), which remain,
> and how to finish + verify. Scope agreed: **docxology's own public repos
> (software + papers)** — forks and private repos are excluded (see rationale below).

## How SWH archival works here

- **SWH continuously auto-harvests public GitHub.** Every public docxology repo will
  be archived over time with no action. "Save code now" only **expedites a fresh
  snapshot** of a specific repo.
- **Submission channel:** the public form at <https://archive.softwareheritage.org/save/>
  (origin type `git`, the repo's `.git` clone URL). No account needed; an automatic
  browser proof-of-work (Anubis) clears transparently.
- **Anonymous rate limit.** SWH throttles anonymous "Save code now" to a small burst —
  ~10–12 requests before returning *"The rate limit for 'save code now' requests has
  been reached."* The window resets after a cool-down (≈1 hour). **Logging in to SWH
  raises the limit substantially**, which is the fastest way to submit the full set.
- **Verify a repo** at: `https://archive.softwareheritage.org/browse/origin/?origin_url=<repo-url>`
  (a freshly *accepted/pending* request 404s here until the scheduled visit completes).
- **Read-only refresh (no submission):** `uv run python scripts/runner/archive_publication.py
  --project <name> --providers software_heritage --check-status` queries the
  credential-free save-queue and origin-visits endpoints and prints a receipt whose
  `extra.state` uses the tracker taxonomy — `verified`, `accepted`, `pending`,
  `excluded`, `unavailable`, `rate-limited` — with an as-of timestamp. It never
  posts, so it needs no authorization and cannot trigger a save.
  For the whole roster, see the 2026-09-06 census below and
  `docs/audit/BACKLOG-CLOSURE-2026-09-06.md`.

## Verified census — 2026-09-06 (17 of 61 archived)

Full roster refreshed via the read-only `--check-status` endpoint (save-queue +
origin-visits, strongest evidence across the `.git`/bare URL variants; per-repo
receipts recorded in the operator cache, summarized here):

| Repo | Type | Save request | Visits | State |
| --- | --- | --- | --- | --- |
| `template` | framework | accepted | 4 | verified |
| `template_active_inference` | exemplar | accepted | 4 | verified |
| `template_autoresearch_project` | exemplar | accepted | 3 | verified |
| `template_autoscientists` | exemplar | accepted | 3 | verified |
| `template_code_project` | exemplar | accepted | 3 | verified |
| `template_gold_refinement` | exemplar | accepted | 2 | verified |
| `template_literature_meta_analysis` | exemplar | accepted | 4 | verified |
| `template_madlib` | exemplar | accepted | 4 | verified |
| `template_newspaper` | exemplar | accepted | 3 | verified |
| `template_prose_project` | exemplar | accepted | 2 | verified |
| `template_sia` | exemplar | accepted | 1 | verified |
| `template_template` | exemplar | accepted | 3 | verified |
| `template_textbook` | exemplar | accepted | 2 | verified |
| `democreate` | software | accepted | 1 | verified |
| `CogSecSkills` | software | accepted | 2 | verified |
| `BeeStack` | scholarly | accepted | 2 | verified |
| `AGEINT` | scholarly | accepted | 2 | verified |

As-of timestamp for every row: 2026-09-06 (16:5x UTC, single pass). The 2026-06-27
snapshot's "submitted — accepted/pending" list has fully landed: all 11 entries are
now `verified`, and `template_sia`, `template_template`, `template_textbook`
(previously queued), plus `CogSecSkills`, `BeeStack`, and `AGEINT` were archived
since — most by automatic harvesting rather than save requests.

## Not yet archived — 43 confirmed + 1 unverified (as of 2026-09-06)

`unavailable` — no save request on record and no origin visits:

**Template exemplars:** `template_bioinformatics_project`

**Original software:** `codomyrmex`, `entofile`, `steganographer`, `dotscope`,
`ivm-xyz`, `QuadCraft`, `QuadMath`, `timeline_generator`, `opentir`, `coasys`,
`p3if`, `active-inference-pocket-lab`, `qr_live_protocol`, `hhs-opendata`,
`crescent-city`, `sunspot`, `godel_ivm`, `active_inference`, `active_torchference`,
`markdown_decision_process`, `course`, `links`, `multi-time`, `snake`, `transformer`

**Scholarly / paper / Zenodo-linked:** `itrace` (Zenodo DOI 10.5281/zenodo.20614908),
`grateful_data`, `cohereants`, `crescent_city`, `blake_jiang`, `ntqr_llm`,
`ento_linguistics`, `realizing_emptiness`, `biology_textbook`,
`cognitive_case_diagrams`, `docxology`, `MetaInformAnt`, `ant_stack`, `biol-1`,
`biol-8`, `literature`, `curriculum`

**Unverified (API rate limit mid-census):** `institute_website` — the refresh was
throttled before its evidence completed; its state is unknown, not absent. Re-run
`--check-status` after the cool-down before acting on it.

Submission URL pattern for each: `https://github.com/docxology/<name>.git`
(public archival submission requires owner authorization; `--check-status` itself
performs no submission).

## Excluded — by design

- **Forks** (e.g. `pymdp`, `flybody`, `cogames`, `TradingAgents`, `RxInferExamples.jl`,
  `spm`, `Ludii`, `ngc-learn`, and ~40 more): these are other authors' projects; SWH
  archives the upstream originals already. Not "docxology software." Can be added on
  request.
- **Private repos** (`projects`, `alphacogant`, `instituteos`, `CA_public_records`, the
  many `*-private` mirrors, etc.): SWH can only archive **public** origins. Making a repo
  public is a deliberate access-control decision left to you — not something done here.

## How to finish the remaining ~44

Pick one:

1. **Log in to SWH** (top-right "login", e.g. via GitHub OIDC) — authenticated save
   requests have a much higher rate limit; the full list can then go in one pass.
2. **Throttle over time** — submit ~10 per hour anonymously across the day.
3. **Do nothing** — SWH's automatic GitHub harvesting will archive all public repos
   eventually; the manual saves above just expedite the most important ones first.

## Method notes (for reproducing)

- The save form's JS validation requires **real keystrokes** in the Origin URL field;
  setting the value programmatically (DOM `value`) submits an empty/invalid request that
  silently no-ops. Use focus + type + click Submit, and confirm the green
  *"request has been accepted"* banner before the next entry.
- A red banner = rate limit reached → stop and wait for the cool-down.
