# template_pools_rules_tools TODO

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

## Integrity and template-status gaps

- Keep the three resource directories read-only: never write back to `fonds/`, `rules/`, or `tools/` from this project.
- Keep `src/tools/type_defs.py` the single source of truth for all TypedDict shapes; no inline dicts and no `Any` in public signatures.
- Keep graceful-fallback behavior everywhere — `src/` functions return `None` or empty collections when files are absent and never raise.
- Confirm every `pytest.mark.skipif` guard keeps an accurate resource file-path check as pool contents evolve.

## Configurable-surface gaps

- Extend the discovery adapters in `src/tools/integration.py` when new public fonds/rules/tools ship; do not duplicate the discovered roster in manuscript configuration.
- Any new resource-pool category must enter through a typed loader before it is wired into `integration.py`.

## Documentation and signposting gaps

- Keep `.agents/skills/template-pools-rules-tools/SKILL.md` aligned with the public resource-pool surface it discovers.
- Keep README, AGENTS, and CLAUDE guidance clear that repo-root resolution relies on `parents[4]` (in `fonds_reader.py`, `rules_applier.py`, `tools_invoker.py`) and that the module is named `type_defs.py` (never `types.py`).

## Test and validator gaps

- Keep malformed fonds/rules/tools payloads covered by regression-discriminating
  negative controls; every new constraint family needs a failing mutation case.
- Extend strong-rule semantic evaluation coverage as new formal constraints are added under `rules/templates/`.

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
| `P4-POOLS-DOMAIN-1` | partial | Medium | POOLS-FOURTH-FOND-1 where explicitly required; public resource admission | Execute actual bundled fonds, rules and tools; verify registry ownership, resource lookup and downstream use, and prove standalone exports contain all required public sibling resources. | native resource execution and isolated complete-resource export receipts | `OLLAMA_SKIP_TEST_MODEL_PULL=1 uv run --locked --no-sync --offline --project "$P4_PROJECT_ROOT" --directory "$P4_PROJECT_ROOT" python -m pytest tests/ --cov=src --cov-branch --cov-fail-under=90 --timeout=120 -m ""`; execute each declared opt-in capability producer under the root acceptance profile | missing siblings, private resource traversal, decorative tools or registry/source mismatch must fail |
| `P4-POOLS-MANUSCRIPT-1` | open | Medium | P4-POOLS-DOMAIN-1; reviewed per-project render/native producer contracts and prepared tools | Regenerate pool/rule/tool diagrams, capability tables and manuscript examples from actual execution; document public-only resource configuration and standalone layout. Audit configurable inputs, thin orchestration, injected variables and accessibility; repair only verified gaps. | current analysis/hydration/source bindings, all declared format outputs and visual/content negative controls | `uv run --no-sync --offline python scripts/pipeline/stage_02_analysis.py --project templates/template_pools_rules_tools`; then canonical `stage_03_render.py` and `stage_04_validate.py` with the same selection and the required native producer | stale variables, unresolved content, missing formats, incorrect figures/citations or wrong-source visual evidence must fail |
| `P4-POOLS-PORTABILITY-1` | open | Medium | P4-POOLS-DOMAIN-1; P4-POOLS-MANUSCRIPT-1; built genuine SDK/provider; reviewed packaging projection | Execute all supported runtime and installed-wheel cells and fresh disposable standalone setup/full own-suite/format replay before publication. Verify independent intended version, source/export digest, public resource completeness and reviewed packaging projection; remote promotion is a separate row. | complete runtime/installed and pre-push isolated export/reinstallation receipts | `uv run --no-sync --offline python scripts/gates/installed_public.py --project templates/template_pools_rules_tools --python "3.12=$P4_PYTHON312" --python "3.13=$P4_PYTHON313" --python "3.14=$P4_PYTHON314"`; then complete isolated exported suite and declared formats | parent-relative imports, editable provider substitution, absent cells, incomplete exports, invented publication metadata or remote content mismatch must fail |
| `POOLS-FOURTH-FOND-1` | blocked-external | Medium | Owner-approved fourth fond exemplar | Obtain the required owner or external receipt to unblock; run public-scope and standalone gates and attach public fond manifest and registry update. | public fond manifest and registry update | `uv run pytest projects/templates/template_pools_rules_tools/tests -q --no-cov --timeout=120` as prerequisite controls only; execute the declared real tool/provider/publication producer and attach its independently checked receipt; if no producer exists, implement it before closure | absent exemplar must remain blocked, not skipped as pass |

| `P4-POOLS-REMOTE-1` | open | Medium | P4-POOLS-PORTABILITY-1; P4-STANDALONE-MAIN-1; actual publication authority | After pre-push acceptance and authorized destination promotion, independently verify remote main commit, retrieved export-content/artifact hashes, genuine published version and working declared repository/publication URLs; retain existing releases and deposits. Keep unpublished projects explicit until genuine first receipts. | actual destination/version/commit, retrieval-content parity and applicable DOI/URL receipts | `git ls-remote "$P4_DESTINATION" refs/heads/main`; retrieve/reinstall the actual promoted artifact and rerun the isolated own-suite and declared format checks | a planned version, nonexistent destination, fabricated DOI, stale remote parent or mismatched retrieved export must fail |

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked row is a deliberate boundary, not a skipped success.
