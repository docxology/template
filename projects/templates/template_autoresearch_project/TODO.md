# AutoResearch Project TODO

This backlog is future-only. Completed validation and dated review evidence are preserved in
[`docs/maintenance/exemplar-backlog-history.md`](../../../docs/maintenance/exemplar-backlog-history.md)
or in source-owned generated receipts. Each active row must retain a stable ID, size, dependency,
next action, proving artifact, acceptance command, and negative control; absence of an owner or external receipt
keeps a capability blocked rather than silently promoting it.

## Backlog operating rules

- Keep deterministic and offline defaults unchanged unless an upcoming row explicitly scopes an opt-in.
- Do not close a row until its producer, artifact, consumer, gate, and failing negative control are present.
- Treat unavailable network, LLM, container, formal-tool, and publication paths as explicit skips
  or blockers.
- Re-derive counts and receipts from live source data; never copy measurements into this planning file.

## Current scope

This exemplar remains an offline, deterministic starter for bounded ML-loop
orchestration. The active contract is review readiness without publication
approval, source-ledger traceability, benchmark-boundary honesty, and local
security evidence. New adapters or review schema versions require a separately
scoped Minor or Medium row with its own fixture and negative control.

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

## Platform 4 acceptance scope

The rows below describe remaining acceptance and repairs, not a claim that
existing implementations are missing. Inspect current source and the dated
[program record](../../../docs/maintenance/platform-4-upgrade.md) first.
Set `P4_PROJECT_ROOT` to this project's absolute canonical checkout and prepare
its locked environment using the [runtime matrix guide](../../../docs/development/public-runtime-matrix.md).
Run one project per pytest process under the producer's declared finite outer
deadline and source-owned per-case limits. The whole-selection domain command
is an explicit acceptance opt-in: prepare its declared unpaid tool/model
prerequisites, disable test model pulls, and override default marker exclusions
with `-m ""`. Own-source acceptance requires nonempty complete collection, real
behavior and at least 90% branch coverage; a focused test or previous revision's
result does not close the row. Missing preparation remains blocked.

Native and live lanes additionally require actual producers, independent
content/visual/domain checks and current source/tool/model identities; ordinary
unit tests do not replace them. Apply the root `P4-RUNTIME-MATRIX`,
`P4-INSTALLED-MATRIX`, `P4-UNPAID-CAPABILITIES` and publication contracts.
Unavailable required tools/providers remain blocked. Independent intended
versions come from the program record and package metadata, and remain separate
from genuinely published versions.

## Minor upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Medium upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `P4-AUTORESEARCH-DOMAIN-1` | partial | Medium | P4-CACHE-RESUME-CUSTODY-1; fixed offline dataset | Independently recompute candidate scores, noise bounds and keep/reject/defer decisions; verify deterministic fixed-dataset scope and bounded execution across configured experiments. | independent score/noise/decision oracles and complete experiment receipts | `OLLAMA_SKIP_TEST_MODEL_PULL=1 uv run --locked --no-sync --offline --project "$P4_PROJECT_ROOT" --directory "$P4_PROJECT_ROOT" python -m pytest tests/ --cov=src --cov-branch --cov-fail-under=90 --timeout=120 -m ""`; execute each declared opt-in capability producer under the root acceptance profile | altered datasets, incorrect thresholds, fabricated improvements or nondeterministic decisions must fail |
| `P4-AUTORESEARCH-MANUSCRIPT-1` | open | Medium | P4-AUTORESEARCH-DOMAIN-1; reviewed per-project render/native producer contracts and prepared tools | Bind all result tables, plots and decision explanations to recomputed outputs; document the offline fixed-dataset boundary and configuration semantics. Audit configurable inputs, thin orchestration, injected variables and accessibility; repair only verified gaps. | current analysis/hydration/source bindings, all declared format outputs and visual/content negative controls | `uv run --no-sync --offline python scripts/pipeline/stage_02_analysis.py --project templates/template_autoresearch_project`; then canonical `stage_03_render.py` and `stage_04_validate.py` with the same selection and the required native producer | stale variables, unresolved content, missing formats, incorrect figures/citations or wrong-source visual evidence must fail |
| `P4-AUTORESEARCH-PORTABILITY-1` | open | Medium | P4-AUTORESEARCH-DOMAIN-1; P4-AUTORESEARCH-MANUSCRIPT-1; built genuine SDK/provider; reviewed packaging projection | Execute all supported runtime and installed-wheel cells and fresh disposable standalone setup/full own-suite/format replay before publication. Verify independent intended version, source/export digest, public resource completeness and reviewed packaging projection; remote promotion is a separate row. | complete runtime/installed and pre-push isolated export/reinstallation receipts | `uv run --no-sync --offline python scripts/gates/installed_public.py --project templates/template_autoresearch_project --python "3.14=$P4_PYTHON314" --python "3.15=$P4_PYTHON315"`; then complete isolated exported suite and declared formats | parent-relative imports, editable provider substitution, absent cells, incomplete exports, invented publication metadata or remote content mismatch must fail |

| `P4-AUTORESEARCH-REMOTE-1` | open | Medium | P4-AUTORESEARCH-PORTABILITY-1; P4-STANDALONE-MAIN-1; actual publication authority | After pre-push acceptance and authorized destination promotion, independently verify remote main commit, retrieved export-content/artifact hashes, genuine published version and working declared repository/publication URLs; retain existing releases and deposits. Keep unpublished projects explicit until genuine first receipts. | actual destination/version/commit, retrieval-content parity and applicable DOI/URL receipts | `git ls-remote "$P4_DESTINATION" refs/heads/main`; retrieve/reinstall the actual promoted artifact and rerun the isolated own-suite and declared format checks | a planned version, nonexistent destination, fabricated DOI, stale remote parent or mismatched retrieved export must fail |

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked row is a deliberate boundary, not a skipped success.
