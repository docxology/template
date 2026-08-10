# AutoResearch Project TODO

This backlog is future-only. Completed validation and dated review evidence are preserved in
[`docs/maintenance/exemplar-backlog-history.md`](../../../docs/maintenance/exemplar-backlog-history.md)
or in source-owned generated receipts. Each active row must retain a stable ID, size, dependency,
proving artifact, acceptance command, and negative control; absence of an owner or external receipt
keeps a capability blocked rather than silently promoting it.

## Backlog operating rules

- Keep deterministic and offline defaults unchanged unless an upcoming row explicitly scopes an opt-in.
- Do not close a row until its producer, artifact, consumer, gate, and failing negative control are present.
- Treat unavailable network, LLM, container, formal-tool, and publication paths as explicit skips
  or blockers.
- Re-derive counts and receipts from live source data; never copy measurements into this planning file.

## Current best move

Consolidate maintainability and interpretation boundaries before adding broader
research behavior. The exemplar already demonstrates bounded ML execution,
machine-readable artifacts, citation source ledgers, deferred review gates,
local security evidence, and manuscript hydration. The next wave should make
those surfaces easier to maintain and harder to misread.

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

## Minor

### Manual approval boundary

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

### Module-size drift watch

- **Problem:** future table, diagnostics, or ML additions can re-create the large
  hubs that were just split.
- **Why it matters:** AutoResearch is the most logic-heavy public exemplar; small
  modules keep reviews and tests tractable.
- **Smallest next step:** add a short TODO closure note whenever a source module
  crosses the warning threshold and name the intended split target.
- **Acceptance:** `uv run python scripts/audit/check_template_drift.py --strict`
  stays clean for the exemplar.
- **Out of scope:** splitting modules preemptively when they are still coherent.

## Major

### Second deterministic task adapter

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

### Versioned review packets

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

## Minor upcoming

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `AR-REVIEW-BOUNDARY-1` | Minor | Human approval boundary | self-approval regression receipt | project review-artifact tests | generated approval without `human_review.yaml` must fail |
| `AR-MODULE-WATCH-1` | Minor | Module-size drift gate | module-size report | strict drift gate | oversized logic hub must fail the gate |

## Medium upcoming

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `AR-REVIEW-PACKET-V2` | Medium | Review-packet schema v1 | migration and v2 receipt | packet compatibility tests | v2 self-approval or unknown version must fail |

## Major upcoming

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `AR-METHOD-ADAPTER-1` | Major | Stable loop/report schemas | second deterministic adapter receipt | project suite and evidence validation | network or generated-code adapter must be unavailable |

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked major row is a deliberate boundary, not a skipped success.
