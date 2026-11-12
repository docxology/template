# template_data_descriptor TODO

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

- Keep rendered manuscript outputs, figures, and descriptor-review artifacts regenerated after schema or fixture changes. Recompute fixture checksums/row counts and update `data/example_descriptor.json` whenever `data/fixtures/` changes.
- Re-run `scripts/generate_figures.py` and `scripts/generate_release_artifacts.py` after any change to `src/data_descriptor/` so `output/figures/figure_registry.json` and `output/reports/*` stay in sync with the source.

## Configurable-surface gaps

- Extend `manuscript/config.yaml.example` when new descriptor fields become first-class.

## Documentation and signposting gaps

- Keep README, AGENTS, STANDALONE, and the per-directory README/AGENTS pairs aligned with the descriptor validator, verification, and figure modules.

## Workflowz review — 2026-11-10

These requests remain **open**, independently of the broader P4 acceptance rows.
Their dated owner record is preserved at
[`995db6122be90d7d7d2f4ba5c467b7d5fa27158b`, `TODO.md:60–64`](https://github.com/docxology/template_data_descriptor/blob/995db6122be90d7d7d2f4ba5c467b7d5fa27158b/TODO.md#L60-L64).
The probes below are repair acceptance criteria, not passing receipts; neither
request is implemented or closed by retaining it here. Run them from a prepared
standalone project root (or this canonical project's root with its checkout SDK
binding), not the monorepo root.

- [ ] **WFZ-DD-1 — P1 — Make malformed `fields` descriptors return findings instead of raising.** Size: Small.
  - **Outcome:** `validate_descriptor` and `build_descriptor_report` handle a non-iterable `fields` value through the normal invalid-descriptor result path, while valid descriptors retain their existing fingerprints.
  - **Evidence:** [`src/data_descriptor/descriptor.py:63–72`](https://github.com/docxology/template_data_descriptor/blob/995db6122be90d7d7d2f4ba5c467b7d5fa27158b/src/data_descriptor/descriptor.py#L63-L72) iterates `fields` directly, even though report construction later guards non-list values at [`descriptor.py:96–103`](https://github.com/docxology/template_data_descriptor/blob/995db6122be90d7d7d2f4ba5c467b7d5fa27158b/src/data_descriptor/descriptor.py#L96-L103). The current source owner is still `src/data_descriptor/descriptor.py`.
  - **Next action:** Guard malformed field containers before fingerprint iteration and add a regression through the public validation/report APIs, retaining the normal findings vocabulary.
  - **Proving artifact:** Failing-before/passing-after malformed-container regression and unchanged fingerprints for the valid fixture descriptors.
  - **Acceptance probe:** `uv run python -c 'from data_descriptor.descriptor import build_descriptor_report; report = build_descriptor_report({"name":"n","version":"1","license":"CC-BY-4.0","files":[],"fields":None,"provenance":[]}); assert not report.valid; assert report.field_count == 0; assert report.findings'`
  - **Negative control / dependencies / constraints:** The original review identifies a `TypeError` before repair; retain that failure as the regression's before-state rather than accepting an exception as an invalid report. Valid descriptors must retain deterministic fingerprint ordering. No external dependency is required; preserve the existing malformed-container validation vocabulary where applicable.

- [ ] **WFZ-DD-2 — P2 — Distinguish an unsafe/non-file declared path from a genuinely absent file.** Size: Small.
  - **Outcome:** A declared existing directory or other non-regular path receives a failing verification status rather than the non-failure `absent` classification, so metadata-only release semantics remain limited to files that are actually not present.
  - **Evidence:** [`src/data_descriptor/verification.py:10–12`](https://github.com/docxology/template_data_descriptor/blob/995db6122be90d7d7d2f4ba5c467b7d5fa27158b/src/data_descriptor/verification.py#L10-L12) defines absent files as legitimately referenced but not bundled, whereas [`verification.py:211–221`](https://github.com/docxology/template_data_descriptor/blob/995db6122be90d7d7d2f4ba5c467b7d5fa27158b/src/data_descriptor/verification.py#L211-L221) combines `not path` and `not resolved.is_file()` into `STATUS_ABSENT`; [`verification_summary`, lines 164–176](https://github.com/docxology/template_data_descriptor/blob/995db6122be90d7d7d2f4ba5c467b7d5fa27158b/src/data_descriptor/verification.py#L164-L176) aggregates the verification classifications. The current source owner is still `src/data_descriptor/verification.py`.
  - **Next action:** Separate genuinely missing files from unsafe or existing non-file paths and ensure the latter contribute to the failing summary.
  - **Proving artifact:** Directory/non-regular-path regressions, a failing verification summary, and passing controls for genuinely missing metadata-only files.
  - **Acceptance probe:** `uv run python -c 'import tempfile; from pathlib import Path; from data_descriptor.verification import STATUS_ABSENT, verify_descriptor_files, verification_summary; root=Path(tempfile.mkdtemp()); (root/"fixtures").mkdir(); result=verify_descriptor_files({"files":[{"path":"fixtures","checksum":"sha256:"+"0"*64,"rows":0,"media_type":"text/csv"}]}, root)[0]; assert result.status != STATUS_ABSENT; assert verification_summary((result,))["mismatch"] == 1'`
  - **Negative control / dependencies / constraints:** An existing directory must not be accepted as an absent metadata-only file. Preserve `absent` for genuinely missing files and retain the existing [symlink/escape checks at `verification.py:186–210`](https://github.com/docxology/template_data_descriptor/blob/995db6122be90d7d7d2f4ba5c467b7d5fa27158b/src/data_descriptor/verification.py#L186-L210). No new media reader or network access is required.

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
| `P4-DATA-DOMAIN-1` | partial | Medium | DATA-MEDIA-1; local descriptor/media contract | Exercise invalid required descriptors, checksums, row counts, constraints and licenses; complete licensed non-CSV fixture acceptance and genuine sandbox release/replay. | descriptor/media oracles, license custody and actual sandbox replay receipts | `OLLAMA_SKIP_TEST_MODEL_PULL=1 uv run --locked --no-sync --offline --project "$P4_PROJECT_ROOT" --directory "$P4_PROJECT_ROOT" python -m pytest tests/ --cov=src --cov-branch --cov-fail-under=90 --timeout=120 -m ""`; execute each declared opt-in capability producer under the root acceptance profile | invalid required descriptors, unsupported media, malformed rows, checksum drift or fabricated release identity must fail |
| `P4-DATA-MANUSCRIPT-1` | open | Medium | P4-DATA-DOMAIN-1; reviewed per-project render/native producer contracts and prepared tools | Bind schema/data dictionaries, figures, accessibility and manuscript claims to actual validated datasets and licenses across every declared output format. Audit configurable inputs, thin orchestration, injected variables and accessibility; repair only verified gaps. | current analysis/hydration/source bindings, all declared format outputs and visual/content negative controls | `uv run --no-sync --offline python scripts/pipeline/stage_02_analysis.py --project templates/template_data_descriptor`; then canonical `stage_03_render.py` and `stage_04_validate.py` with the same selection and the required native producer | stale variables, unresolved content, missing formats, incorrect figures/citations or wrong-source visual evidence must fail |
| `P4-DATA-PORTABILITY-1` | open | Medium | P4-DATA-DOMAIN-1; P4-DATA-MANUSCRIPT-1; built genuine SDK/provider; reviewed packaging projection | Execute all supported runtime and installed-wheel cells and fresh disposable standalone setup/full own-suite/format replay before publication. Verify independent intended version, source/export digest, public resource completeness and reviewed packaging projection; remote promotion is a separate row. | complete runtime/installed and pre-push isolated export/reinstallation receipts | `uv run --no-sync --offline python scripts/gates/installed_public.py --project templates/template_data_descriptor --python "3.14=$P4_PYTHON314" --python "3.15=$P4_PYTHON315"`; then complete isolated exported suite and declared formats | parent-relative imports, editable provider substitution, absent cells, incomplete exports, invented publication metadata or remote content mismatch must fail |
| `DATA-PUBLICATION-1` | blocked-external | Medium | A real fork and owner receipt | Obtain the required owner or external receipt to unblock; run project tests and standalone export check and attach publication receipt + standalone replay. | publication receipt + standalone replay | `uv run pytest projects/templates/template_data_descriptor/tests -q --no-cov --timeout=120` as prerequisite controls only; execute the declared real tool/provider/publication producer and attach its independently checked receipt; if no producer exists, implement it before closure | fabricated publication receipt must fail |
| `DATA-MEDIA-1` | blocked-external | Medium | Real licensed non-CSV fixture | Obtain a real licensed non-CSV fixture and attach its checksum/row manifest before promoting the media claim. | media checksum/row manifest + license receipt | `uv run pytest projects/templates/template_data_descriptor/tests -q --no-cov --timeout=120` as prerequisite controls only; execute the declared real tool/provider/publication producer and attach its independently checked receipt; if no producer exists, implement it before closure | unsupported media, malformed rows, symlink escape, or wrong checksum must fail |

| `P4-DATA-REMOTE-1` | open | Medium | P4-DATA-PORTABILITY-1; P4-STANDALONE-MAIN-1; actual publication authority | After pre-push acceptance and authorized destination promotion, independently verify remote main commit, retrieved export-content/artifact hashes, genuine published version and working declared repository/publication URLs; retain existing releases and deposits. Keep unpublished projects explicit until genuine first receipts. | actual destination/version/commit, retrieval-content parity and applicable DOI/URL receipts | `git ls-remote "$P4_DESTINATION" refs/heads/main`; retrieve/reinstall the actual promoted artifact and rerun the isolated own-suite and declared format checks | a planned version, nonexistent destination, fabricated DOI, stale remote parent or mismatched retrieved export must fail |

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked row is a deliberate boundary, not a skipped success.
