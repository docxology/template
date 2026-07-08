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

## Current validation evidence

Current validation is the monorepo public-template gate set: per-project pytest
with 90% `src/` coverage, strict template drift, prerender validation, and the
normal analysis/render/validate/copy pipeline. This TODO records future work
only; shipped evidence belongs in generated artifacts, reports, tests, and the
README/AGENTS contract.

Live test counts and coverage are read from
[`docs/_generated/COUNTS.md`](../../../docs/_generated/COUNTS.md), not pinned
here. Edge-case coverage lives in `tests/test_edge_{config,ledger,loop,gates}.py`
and manuscript-token/format helpers in `tests/test_format_helpers.py`; keep both
green as the loop surfaces evolve.

## Invariants to keep

These are the load-bearing guardrails of the exemplar. Keep each one true; use
git history for how they were established.

| Surface | Behavior | Guardrail to keep |
| --- | --- | --- |
| Manual approval | `human_review.yaml` is the human-authored approval source; generated files can report readiness but cannot self-approve publication | default `publication_approved: false`; generated code must not mutate the human review file |
| Review readiness | `autoresearch_review_packet.json` and `review_decisions.json` distinguish review readiness from publication approval | validators fail on generated self-approval |
| Source ledger | `manuscript/source_ledger.yaml` is parsed through reusable project helpers and checked offline | citekeys stay present in ledger, BibTeX, and numbered manuscript prose |
| ML loop | bounded deterministic ML execution records baseline, candidate selection, metric improvement, and budget evidence | no runtime downloads, no generated-code execution, no network calls |
| Evidence reports | compact evidence registry, phase ledger, figure-quality report, rank stability, and calibration diagnostics are generated from shared data | report-size guard remains in place unless explicitly enabled |
| Evidence overview | `autoresearch_evidence_overview.json` and `.md` summarize readiness versus approval, claim evidence rows, source-ledger tier/age status, benchmark boundaries, and security/integrity status | overview must keep generated readiness separate from human publication approval |
| Benchmark boundary | `benchmark_boundary.json` records fixture scope, metric direction, baseline, candidate families, budget, and explicit non-claims | benchmark-adjacent prose must not imply broad empirical or leaderboard claims |
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

## Integrity and template-status gaps

Keep the exemplar forkable as an offline starter. Future hardening should
improve maintainability, schema compatibility, and review-boundary clarity
without changing the default no-network, no-LLM, no-autonomous-approval
contract.

## Configurable-surface gaps

New configurable behavior belongs in `manuscript/config.yaml`, the loop
configuration helpers, source ledgers, review-boundary files, or explicit task
adapters. Keep `manuscript/config.yaml.example` in top-level parity and scrubbed
of project-specific release values whenever config sections change.

## Documentation and signposting gaps

When adding an adapter, review artifact, publication field, or report surface,
update the nearest README/AGENTS signpost with when to use it, how to run it
through the monorepo, what validates it, and which claims remain deliberately
out of scope.

## Test and validator gaps

Every new research-loop surface needs a deterministic fixture, a positive test,
and a negative-control gate for hollow evidence, self-approval, stale source
ledger entries, or benchmark-boundary overclaiming. Avoid mocks for core loop
behavior; use tiny local fixtures instead.

## Ordered improvement ladder

1. Preserve review/publication separation and offline deterministic execution.
2. Keep source-ledger, evidence-overview, benchmark-boundary, and module-size
   gates green while refactoring.
3. Add a second task adapter only after current schemas and review packets stay
   stable through another full public-template verification pass.
4. Version reusable review-packet schemas before exposing downstream tooling.

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

- **Status:** shipped in this pass. `scripts/check_source_ledger.py` prints
  source-tier counts and checked-age buckets offline, and source-ledger tests
  fail on future dates, invalid tiers, non-HTTPS URLs, and missing ledger
  BibTeX/manuscript coverage.

### AR-LOOP-PHASES-1 - Declarative pre-extrinsic phase table

- **Status:** shipped. `PRE_EXTRINSIC_PHASES` in `src/loop_phases.py` owns
  payload refresh, visuals, and settlement pass 2; duplicate schema/research-object
  manifest writes removed from `loop.py`; edge tests split to
  `tests/test_edge_{config,ledger,loop,gates}.py`; scripts share
  `scripts/_bootstrap.py`.

### AR-MODULE-WATCH-1 - Keep split modules below drift thresholds

- **Problem:** future table, diagnostics, or ML additions can re-create the large
  hubs that were just split.
- **Why it matters:** AutoResearch is the most logic-heavy public exemplar; small
  modules keep reviews and tests tractable.
- **Smallest next step:** add a short TODO closure note whenever a source module
  crosses the warning threshold and name the intended split target.
- **Acceptance:** `uv run python scripts/audit/check_template_drift.py --strict`
  stays clean for the exemplar.
- **Out of scope:** splitting modules preemptively when they are still coherent.

## Medium

No active medium rows remain from this pass. `AR-REPORT-ERGONOMICS-1`,
`AR-BENCHMARK-ERGONOMICS-1`, and `AR-SOURCE-LEDGER-2` are implemented in the
generated evidence overview, benchmark boundary artifact, and source-ledger
contract tests. Keep this section empty until a new medium verifier improvement
has a proving artifact, gate, and negative control.

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
2. Do not add new evidence types until the evidence overview remains stable
   through another full project test run.
3. Do not add benchmark-adjacent claims unless they cite
   `output/data/benchmark_boundary.json` or a successor boundary artifact.
4. Attempt `AR-METHOD-ADAPTER-1` only after the current module-size and review
   boundaries stay clean through another release.
