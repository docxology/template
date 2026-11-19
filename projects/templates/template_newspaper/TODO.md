# template_newspaper TODO

This backlog is future-only. Completed validation and dated review evidence are preserved in
[monorepo review history](https://github.com/docxology/template/blob/main/docs/maintenance/exemplar-backlog-history.md#bounded-workflowz-reviews--2026-11-10) (not bundled in standalone exports)
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

- Keep edition content fictional unless a fork adds real source provenance and fact-checking validators.
- Keep ReportLab layout logic in `src/`, with scripts as thin orchestration only.
- The machine-readable `layout_audit` artifact records page geometry and
  glyph-clearance findings separately from `all_pages_fit`, overset, and
  missing-image checks; keep all four signals distinct.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` aligned with publication metadata and render toggles.
- A minimal one-page fork schema example is required in the same row if
  `content/edition.yaml` ever gains required fields.

## Documentation and signposting gaps

- Keep README and docs clear that the newspaper PDF is produced by project scripts, while the manuscript PDF is produced by the monorepo renderer.
- Link any new content schema fields from `docs/syntax_guide.md` and the README quick-start.
- Verify platform-dependent font fallback with genuine supported environments; preserve precise coverage/tool limitations and avoid dependency replacements.

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
| `P4-NEWSPAPER-DOMAIN-1` | partial | Medium | P4-REQUIRED-PROFILE-DEFINITION-1; native producer contract; pinned fonts and raster renderer | Render every configured edition and independently verify print geometry, fonts, overflow, raster layout and edition content separation at actual print scale. | edition-qualified geometry/font/raster/content receipts | `OLLAMA_SKIP_TEST_MODEL_PULL=1 uv run --locked --no-sync --offline --project "$P4_PROJECT_ROOT" --directory "$P4_PROJECT_ROOT" python -m pytest tests/ --cov=src --cov-branch --cov-fail-under=90 --timeout=120 -m ""`; execute each declared opt-in capability producer under the root acceptance profile | overflow, font substitution, edition leakage, stale raster evidence or wrong paper dimensions must fail |
| `P4-NEWSPAPER-MANUSCRIPT-1` | open | Medium | P4-NEWSPAPER-DOMAIN-1; reviewed per-project render/native producer contracts and prepared tools | Complete visual review of edition PDFs and source-bound page/content maps; keep design configuration, accessibility and documentation consistent with the actual layouts. Audit configurable inputs, thin orchestration, injected variables and accessibility; repair only verified gaps. | current analysis/hydration/source bindings, all declared format outputs and visual/content negative controls | `uv run --no-sync --offline python scripts/pipeline/stage_02_analysis.py --project templates/template_newspaper`; then canonical `stage_03_render.py` and `stage_04_validate.py` with the same selection and the required native producer | stale variables, unresolved content, missing formats, incorrect figures/citations or wrong-source visual evidence must fail |
| `P4-NEWSPAPER-PORTABILITY-1` | open | Medium | P4-NEWSPAPER-DOMAIN-1; P4-NEWSPAPER-MANUSCRIPT-1; built genuine SDK/provider; reviewed packaging projection | Execute all supported runtime and installed-wheel cells and fresh disposable standalone setup/full own-suite/format replay before publication. Verify independent intended version, source/export digest, public resource completeness and reviewed packaging projection; remote promotion is a separate row. | complete runtime/installed and pre-push isolated export/reinstallation receipts | `uv run --no-sync --offline python scripts/gates/installed_public.py --project templates/template_newspaper --python "3.14=$P4_PYTHON314" --python "3.15=$P4_PYTHON315"`; then complete isolated exported suite and declared formats | parent-relative imports, editable provider substitution, absent cells, incomplete exports, invented publication metadata or remote content mismatch must fail |

| `P4-NEWSPAPER-REMOTE-1` | open | Medium | P4-NEWSPAPER-PORTABILITY-1; P4-STANDALONE-MAIN-1; actual publication authority | After pre-push acceptance and authorized destination promotion, independently verify remote main commit, retrieved export-content/artifact hashes, genuine published version and working declared repository/publication URLs; retain existing releases and deposits. Keep unpublished projects explicit until genuine first receipts. | actual destination/version/commit, retrieval-content parity and applicable DOI/URL receipts | `git ls-remote "$P4_DESTINATION" refs/heads/main`; retrieve/reinstall the actual promoted artifact and rerun the isolated own-suite and declared format checks | a planned version, nonexistent destination, fabricated DOI, stale remote parent or mismatched retrieved export must fail |

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked row is a deliberate boundary, not a skipped success.

## Workflowz review — 2026-11-10: retained open requests

The [immutable owner review](https://github.com/docxology/template_newspaper/blob/66d538eaaef5c7b44a2b67b2f6601378d687a651/TODO.md#L67-L71)
is not superseded by generic P4 layout acceptance. Both requests remain unchecked.
Run these probes from the standalone project root in the prepared project
environment; `newspaper` is the current package, not a `src` compatibility import.

- [ ] `WFZ-20261110-01` · P1 · Minor · Reject an invalid enabled spot color rather than silently rendering without it.
  - Outcome: `render.spot_color: true` with malformed `render.spot_hex` fails loading or rendering with an actionable `spot_hex` configuration error. Valid hex still creates a ReportLab color; disabled spot color still returns `None`.
  - Evidence: `src/newspaper/config.py:107-117` catches every `HexColor` error and returns `None`; `src/newspaper/engine.py` consumes that value. The immutable review preserves the original line evidence.
  - Acceptance: `python -I -c 'from newspaper.config import NewspaperConfig; NewspaperConfig(spot_color=True, spot_hex="not-a-color").spot()'` must fail specifically for `spot_hex`, not an import or preparation error.
  - Paired control: `python -I -c 'from newspaper.config import NewspaperConfig; assert NewspaperConfig(spot_color=True, spot_hex="#9E1B32").spot() is not None; assert NewspaperConfig(spot_color=False, spot_hex="not-a-color").spot() is None'` must succeed.
  - Dependencies/constraints: existing PyYAML/ReportLab only; preserve disabled-spot behavior and deterministic rendering defaults. Proving artifact: a regression that rejects malformed enabled colors alongside the valid/disabled controls; generic render success cannot close the request.

- [ ] `WFZ-20261110-02` · P1 · Minor · Parse render booleans strictly rather than truthiness-coercing quoted strings.
  - Outcome: actual YAML booleans retain their values; non-boolean `draft_grid` or `spot_color` values raise a clear `ValueError`.
  - Evidence: `src/newspaper/config.py:102-103` applies `bool(...)` to YAML values, so `"false"` becomes `True`.
  - Acceptance / negative control: `python -I -c 'from newspaper.config import NewspaperConfig; NewspaperConfig.from_dict({"render": {"spot_color": "false"}})'` must fail for the invalid field/value; repeat for `draft_grid`.
  - Paired control: `python -I -c 'from newspaper.config import NewspaperConfig; c=NewspaperConfig.from_dict({"render": {"draft_grid": True, "spot_color": False}}); assert c.draft_grid is True and c.spot_color is False; c=NewspaperConfig.from_dict({"render": {"draft_grid": False, "spot_color": False}}); assert c.draft_grid is False and c.spot_color is False'`.
  - Dependencies/constraints: no new dependency; preserve actual YAML boolean support and strict unknown-key validation. Proving artifact: behavioral tests for both fields, with quoted `"false"` rejected and both real boolean values retained.
