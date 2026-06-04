# AutoResearch Project TODO

> Project-level roadmap for `template_autoresearch_project` after the survey
> integration, RedTeam hardening, and `v3.1.0` template release. Keep this
> exemplar deterministic, offline, evidence-governed, and explicitly
> unapproved by default.

## Current best move

Consolidate maintainability and interpretation boundaries before adding broader
research behavior. The exemplar already demonstrates bounded ML execution,
machine-readable artifacts, citation source ledgers, deferred review gates,
local security evidence, and manuscript hydration. The next wave should make
those surfaces easier to maintain and harder to misread.

## Shipped state

The long checklist-heavy hardening plan that previously lived here is complete.
Use git history for line-by-line closure detail; keep this file focused on work
that remains live.

| Surface | Shipped behavior | Guardrail to keep |
| --- | --- | --- |
| Manual approval | `human_review.yaml` is the human-authored approval source; generated files can report readiness but cannot self-approve publication | default `publication_approved: false`; generated code must not mutate the human review file |
| Review readiness | `autoresearch_review_packet.json` and `review_decisions.json` distinguish review readiness from publication approval | validators fail on generated self-approval |
| Source ledger | `manuscript/source_ledger.yaml` is parsed through reusable project helpers and checked offline | citekeys stay present in ledger, BibTeX, and numbered manuscript prose |
| ML loop | bounded deterministic ML execution records baseline, candidate selection, metric improvement, and budget evidence | no runtime downloads, no generated-code execution, no network calls |
| Evidence reports | compact evidence registry, phase ledger, figure-quality report, rank stability, and calibration diagnostics are generated from shared data | report-size guard remains in place unless explicitly enabled |
| Module shape | ML, figure, diagnostics, manuscript table, and source-ledger responsibilities have been split below drift thresholds | future additions go into the right leaf modules, not back into large hubs |

## Non-negotiable invariants

- Default execution performs no network calls, no LLM calls, no runtime dataset
  downloads, no generated-code execution, and no autonomous publication approval.
- Numbered manuscript prose keeps run-derived facts tokenized through
  `{{TOKEN}}` hydration and registry-backed figure blocks.
- Generated review artifacts may become ready for review while publication
  remains unapproved.
- Security artifacts remain local integrity evidence only: no external signing,
  no production SLSA claim, and no runtime monitoring claim.
- `scripts/regenerate_mnist_fixture.py` remains manual maintenance tooling only;
  default pipeline scripts and loop execution must not import or call it.

## Minor

### AR-REVIEW-BOUNDARY-1 - Keep manual approval impossible to fake

- **Problem:** future report or writer changes could accidentally collapse review
  readiness into publication approval.
- **Why it matters:** this exemplar must never imply autonomous publication
  authority.
- **Smallest next step:** add one focused regression whenever a new review output
  is introduced, proving generated artifacts stay unapproved without
  `human_review.yaml`.
- **Acceptance:** generated review outputs remain distinct from human approval,
  and the validator reports a blocking issue for self-approval.
- **Out of scope:** building an external review workflow.

### AR-SOURCE-FRESHNESS-1 - Keep the source ledger fresh offline

- **Problem:** `checked_as_of` dates and source-tier counts can drift without a
  lightweight maintenance signal.
- **Why it matters:** the manuscript cites current-trends sources while the
  tests intentionally avoid live URL validation.
- **Smallest next step:** make the offline ledger check print age buckets and
  source-tier counts, with failures only for malformed or future-dated entries.
- **Acceptance:** the source-ledger script runs without network calls and exits
  nonzero for future dates or invalid tiers.
- **Out of scope:** crawling live sources or asserting URL availability.

### AR-MODULE-WATCH-1 - Keep split modules below drift thresholds

- **Problem:** future table, diagnostics, or ML additions can re-create the large
  hubs that were just split.
- **Why it matters:** AutoResearch is the most logic-heavy public exemplar; small
  modules keep reviews and tests tractable.
- **Smallest next step:** add a short TODO closure note whenever a source module
  crosses the warning threshold and name the intended split target.
- **Acceptance:** `uv run python scripts/check_template_drift.py --strict`
  stays clean for the exemplar.
- **Out of scope:** splitting modules preemptively when they are still coherent.

## Medium

### AR-REPORT-ERGONOMICS-1 - Make evidence reports easier to scan

- **Problem:** the evidence surface is correct but still dense for humans
  checking release readiness.
- **Why it matters:** reviewers should see readiness, approval, metric, source,
  and security status without reading every JSON file.
- **Smallest next step:** add a compact Markdown summary generated from existing
  JSON artifacts, with links back to the machine-readable files.
- **Acceptance:** the report summary is generated offline and contains review
  status, source-ledger counts, ML comparison, and security evidence status.
- **Out of scope:** replacing the JSON artifacts.

### AR-BENCHMARK-ERGONOMICS-1 - Clarify benchmark boundaries

- **Problem:** the bounded ML loop can be misread as a general benchmark claim.
- **Why it matters:** the exemplar should show a reproducible pattern, not claim
  state-of-the-art AutoResearch.
- **Smallest next step:** generate a small benchmark-boundary artifact that
  states fixture scope, baseline, candidate families, budget, and non-claims.
- **Acceptance:** manuscript variables or report prose can cite the artifact, and
  tests fail if a benchmark claim lacks boundary metadata.
- **Out of scope:** adding new datasets or external leaderboards.

### AR-SOURCE-LEDGER-2 - Promote ledger checks into the project contract

- **Problem:** ledger correctness is spread across helper tests and manuscript
  integration checks.
- **Why it matters:** source governance should be a visible project contract,
  not only a manuscript-variable side effect.
- **Smallest next step:** make the source-ledger checker part of the standard
  project gate and document its offline-only semantics.
- **Acceptance:** project tests fail for missing ledger citekeys, invalid tiers,
  future dates, or manuscript citekeys absent from the ledger.
- **Out of scope:** live freshness validation.

## Major

### AR-METHOD-ADAPTER-1 - Add a second deterministic research task adapter

- **Problem:** the exemplar proves one bounded ML-loop shape, but the adapter
  boundary would be clearer with a second tiny offline task.
- **Why it matters:** a second adapter can prove that AutoResearch orchestration
  is not hard-coded to the current fixture.
- **Smallest next step:** design a toy offline task with a small fixture, clear
  baseline, deterministic candidate family, and the same approval boundaries.
- **Acceptance:** both tasks run through the same evidence/reporting contract and
  preserve project coverage at or above the public gate.
- **Out of scope:** network datasets, generated-code execution, or live LLM
  research.

### AR-REVIEW-PACKET-V2 - Make review packets schema-versioned artifacts

- **Problem:** review packets are machine-readable but not yet a versioned
  compatibility surface.
- **Why it matters:** downstream review tools need stable schemas if this
  exemplar becomes a reusable project pattern.
- **Smallest next step:** define `template-autoresearch-review-packet-v2` with
  explicit compatibility notes and a migration test from the current packet.
- **Acceptance:** v1 and v2 packets validate, and v2 remains unapproved unless
  backed by the human-authored review file.
- **Out of scope:** changing the default publication policy.

## Suggested order

1. Keep `AR-REVIEW-BOUNDARY-1` and `AR-SOURCE-FRESHNESS-1` green whenever the
   manuscript, reports, or source ledger changes.
2. Land `AR-REPORT-ERGONOMICS-1` before adding new evidence types, so reviewers
   have one human-readable status surface.
3. Land `AR-BENCHMARK-ERGONOMICS-1` before any new benchmark-adjacent claim.
4. Attempt `AR-METHOD-ADAPTER-1` only after the current module-size and review
   boundaries stay clean through another release.
