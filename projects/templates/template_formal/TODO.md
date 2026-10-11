# template_formal TODO

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

## Optional formal side-spec

- Formal side-specs (Lean 4 + TLA+) are non-default, run via `scripts/check_formal_specs.sh`.
- Keep the Lean and TLA+ side-specs optional but real: the formal-check script
  must invoke the actual tools when installed, report unavailable tools
  explicitly, and never turn a skipped side-spec into a pass claim.
- Keep theorem and invariant claims non-vacuous, zero-`sorry`, and paired with
  a runtime or typed negative control when the protocol surface changes.

## Integrity and template-status gaps

- Keep this exemplar as the smallest reliable control-positive path for illegal-state-unrepresentable, session-typed, affine-discipline design applied to a decentralized multiagent domain.
- Keep the manuscript's claim-scoping section ("what mypy --strict proves" vs "what is a runtime discipline") in lockstep with `tests/mypy_fixtures/` — every strong claim needs a live ISC-numbered test, not just prose.
- Keep the formal side-specs (Lean/TLA+) wired to `scripts/check_formal_specs.sh` for as long as they ship; do not let either drift to vestigial/unwired status (ISC-36 anti).

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` as the richer copy-and-customize template for publication, LLM, testing, and steganography toggles.
- Any future fault-injection or protocol-timing parameters must enter through typed source loaders (`network/bus.py::FaultConfig`) rather than ad hoc YAML reads in scripts.

## Documentation and signposting gaps

- Keep README quick-start commands aligned with the qualified project name `templates/template_formal`.
- Link new public artifacts from README, AGENTS, and `docs/_generated/exemplar_roster.md` through the generator (a later registration stage owns this).

## Test and validator gaps

- Keep a negative control before widening any typed-invariant claim beyond the ISC-1..40 surface already covered.
- The public roster and generated documentation are generator-owned; use the current public-scope, drift, tracked-path, and generated-document gates rather than recording registration state in this TODO.

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
| `P4-FORMAL-DOMAIN-1` | partial | Medium | FORMAL-SPEC-1; prepared pinned Lean and TLC | Run strict project typing, real network-fault cases, Lean and TLC; prove expected invariant violations, closed-database behavior, bounded launch policy and descendant cleanup with actual tools. | native compiler/model-checker/network-fault and cleanup receipts | `OLLAMA_SKIP_TEST_MODEL_PULL=1 uv run --locked --no-sync --offline --project "$P4_PROJECT_ROOT" --directory "$P4_PROJECT_ROOT" python -m pytest tests/ --cov=src --cov-branch --cov-fail-under=90 --timeout=120 -m ""`; execute each declared opt-in capability producer under the root acceptance profile | decorative specs, skipped required tools, unexpected invariant success, stale pins or surviving processes must fail |
| `P4-FORMAL-MANUSCRIPT-1` | open | Medium | P4-FORMAL-DOMAIN-1; reviewed per-project render/native producer contracts and prepared tools | Bind formal specifications, protocol diagrams, counterexamples and manuscript claims to actual bounded tool outputs while distinguishing mathematical and runtime evidence. Audit configurable inputs, thin orchestration, injected variables and accessibility; repair only verified gaps. | current analysis/hydration/source bindings, all declared format outputs and visual/content negative controls | `uv run --no-sync --offline python scripts/pipeline/stage_02_analysis.py --project templates/template_formal`; then canonical `stage_03_render.py` and `stage_04_validate.py` with the same selection and the required native producer | stale variables, unresolved content, missing formats, incorrect figures/citations or wrong-source visual evidence must fail |
| `P4-FORMAL-PORTABILITY-1` | open | Medium | P4-FORMAL-DOMAIN-1; P4-FORMAL-MANUSCRIPT-1; built genuine SDK/provider; reviewed packaging projection | Execute all supported runtime and installed-wheel cells and fresh disposable standalone setup/full own-suite/format replay before publication. Verify independent intended version, source/export digest, public resource completeness and reviewed packaging projection; remote promotion is a separate row. | complete runtime/installed and pre-push isolated export/reinstallation receipts | `uv run --no-sync --offline python scripts/gates/installed_public.py --project templates/template_formal --python "3.12=$P4_PYTHON312" --python "3.13=$P4_PYTHON313" --python "3.14=$P4_PYTHON314"`; then complete isolated exported suite and declared formats | parent-relative imports, editable provider substitution, absent cells, incomplete exports, invented publication metadata or remote content mismatch must fail |
| `FORMAL-SPEC-1` | blocked-tool | Medium | Optional Lean/TLA+ tools | Install or pin the required tool, or record its unavailable status; run the explicit formal script when available and attach a real formal-spec receipt. | real formal-spec receipt | `uv run pytest projects/templates/template_formal/tests -q --no-cov --timeout=120` as prerequisite controls only; execute the declared real tool/provider/publication producer and attach its independently checked receipt; if no producer exists, implement it before closure | decorative or skipped spec must not report pass |

| `P4-FORMAL-REMOTE-1` | open | Medium | P4-FORMAL-PORTABILITY-1; P4-STANDALONE-MAIN-1; actual publication authority | After pre-push acceptance and authorized destination promotion, independently verify remote main commit, retrieved export-content/artifact hashes, genuine published version and working declared repository/publication URLs; retain existing releases and deposits. Keep unpublished projects explicit until genuine first receipts. | actual destination/version/commit, retrieval-content parity and applicable DOI/URL receipts | `git ls-remote "$P4_DESTINATION" refs/heads/main`; retrieve/reinstall the actual promoted artifact and rerun the isolated own-suite and declared format checks | a planned version, nonexistent destination, fabricated DOI, stale remote parent or mismatched retrieved export must fail |

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked row is a deliberate boundary, not a skipped success.
