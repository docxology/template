# template_autopoiesis TODO

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

- Keep the grammar the single source of truth in `manuscript/config.yaml` (`autopoiesis:` block) and all generation logic in `src/` (`grammar.py`, `expand.py`, `materialize.py`, `realize.py`, `sealing.py`, `verify.py`, `honesty.py`) — scripts stay thin orchestrators.
- Keep materialization routed through `src/template_autopoiesis/manuscript/emit_templates.py::emit_all` for
  every child-facing analysis, test, project, and manuscript file so standalone
  emitters and generated children cannot drift silently.
- Keep provenance recompute-based: verification must re-derive the tree hash from disk at check time and never trust a recorded manifest hash.

## Configurable-surface gaps

- Keep the placeholder-safe `manuscript/config.yaml.example` synchronized with the live config shape, including the list-form slot and dependency syntax.
- The optional `archetype_filters` mapping is the fork-owned selector for materializing a subset of the combinatoric product space; keep its values schema-validated and included in the grammar digest.

## Documentation and signposting gaps

- Keep README and `SYNTAX.md` clear that Stage 02 expands the grammar and materializes/verifies children, while Stage 03 renders the descriptive manuscript PDF.
- `SPEC.md` Phase 10 and `manuscript/preamble.md` are source-owned inputs to the deterministic manuscript contract; keep the checklist, explicit fences, and renderer-qualified receipt synchronized.

## Dependency-mode gaps

- `dep_mode="template"` remains intentionally loud (`NotImplementedError`) until a seam contract is defined that does not require parent infrastructure at child runtime.

## Test and validator gaps

- Keep figure fallback handling explicit for empty arrays, and require
  malformed or under-specified grammar shapes to fail before expansion with real
  negative controls.
- Keep mutation coverage per domain and permit an explicit skip only when a domain has no negative-control primitive; a second primitive must be used when available so the meta-gate cannot become green-by-construction.

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
behavior and at least 90% branch-aware combined statement and branch coverage; a focused test or previous revision's
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
| `P4-AUTO-MANUSCRIPT-1` | open | Medium | reviewed per-project render/native producer contracts and prepared tools | Regenerate grammar/child summaries, figures and hydrated manuscript; reconcile SPEC and preamble fences with actual renderer-qualified output and deterministic child artifacts. Audit configurable inputs, thin orchestration, injected variables and accessibility; repair only verified gaps. | current analysis/hydration/source bindings, all declared format outputs and visual/content negative controls | `uv run --no-sync --offline python scripts/pipeline/stage_02_analysis.py --project templates/template_autopoiesis`; then canonical `stage_03_render.py` and `stage_04_validate.py` with the same selection and the required native producer | stale variables, unresolved content, missing formats, incorrect figures/citations or wrong-source visual evidence must fail |
| `P4-AUTO-PORTABILITY-1` | open | Medium | P4-AUTO-MANUSCRIPT-1; built genuine SDK/provider; reviewed packaging projection | Execute all supported runtime and installed-wheel cells and fresh disposable standalone setup/full own-suite/format replay before publication. Verify independent intended version, source/export digest, public resource completeness and reviewed packaging projection; remote promotion is a separate row. | complete runtime/installed and pre-push isolated export/reinstallation receipts | `uv run --no-sync --offline python scripts/gates/installed_public.py --project templates/template_autopoiesis --python "3.14=$P4_PYTHON314" --python "3.15=$P4_PYTHON315"`; then complete isolated exported suite and declared formats | parent-relative imports, editable provider substitution, absent cells, incomplete exports, invented publication metadata or remote content mismatch must fail |
| `AUTOPOIESIS-SPEC-1` | blocked-tool | Medium | Pinned renderer and visual QA toolchain | Install or pin the renderer, or record its unavailable receipt; run the explicit Phase 10 visual gate and attach the tool-qualified receipt. | `SPEC.md` Phase 10 checklist + renderer receipt | `uv run pytest projects/templates/template_autopoiesis/tests -q --no-cov --timeout=120` as prerequisite controls only; execute the declared real tool/provider/publication producer and attach its independently checked receipt; if no producer exists, implement it before closure | missing renderer must report blocked-tool; fenced preamble/spec mismatch must fail |

| `P4-AUTO-REMOTE-1` | open | Medium | P4-AUTO-PORTABILITY-1; P4-STANDALONE-MAIN-1; actual publication authority | After pre-push acceptance and authorized destination promotion, independently verify remote main commit, retrieved export-content/artifact hashes, genuine published version and working declared repository/publication URLs; retain existing releases and deposits. Keep unpublished projects explicit until genuine first receipts. | actual destination/version/commit, retrieval-content parity and applicable DOI/URL receipts | `git ls-remote "$P4_DESTINATION" refs/heads/main`; retrieve/reinstall the actual promoted artifact and rerun the isolated own-suite and declared format checks | a planned version, nonexistent destination, fabricated DOI, stale remote parent or mismatched retrieved export must fail |

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked row is a deliberate boundary, not a skipped success.

## Workflowz review — 2026-11-10: retained open requests

The [original bounded review](https://github.com/docxology/template_autopoiesis/blob/7f4e9b7e991751b7418f1f82ff4bafa40e93c2ca/TODO.md#L69-L152)
reviewed base `eff704e8` without executing code. These requests remain unchecked;
the P4 child-execution receipts do not establish their particular QR, decoder,
or missing-vendor outcomes. Historical `src/*.py` evidence is retained at that
immutable link; current modules live under `src/template_autopoiesis/`.
Run the probes below from the standalone project root in its explicitly prepared
Python environment with the project package and declared dependencies installed.
The pytest commands are existing prerequisite controls, not closure by themselves.

- [ ] `WFZ-20261110-1` · P1 · Minor · Fail loudly when required `qrcode` is unavailable rather than returning a non-decodable 5×5 checkerboard.
  - Outcome: a generated QR encodes the actual seal payload; missing `qrcode` produces a clear dependency error or a seal that verification rejects, never a successful substitute.
  - Evidence: the original review cites `src/sealing.py:21-34`, the required dependency declaration, and the fallback-accepting seal assertion. The current corresponding fallback is `src/template_autopoiesis/gates/sealing.py::qr_matrix`; seal and cover controls are in `tests/gates/test_seal_child.py` and `tests/figures/test_cover_art.py`.
  - Acceptance / negative control:
    ```bash
    python -I - <<'PY'
    import sys
    from template_autopoiesis.gates.sealing import qr_matrix
    sys.modules["qrcode"] = None
    try:
        matrix = qr_matrix("seal-payload")
    except ImportError as exc:
        assert "qrcode" in str(exc)
    else:
        raise AssertionError(f"missing qrcode silently returned a {len(matrix)}-row matrix")
    PY
    python -I -m pytest tests/gates/test_seal_child.py tests/figures/test_cover_art.py -q --no-cov
    ```
    With the real dependency installed, retain a decodable payload round trip and the seal/cover happy paths. A checkerboard must not satisfy seal verification or its assertions.
  - Dependencies/constraints: keep `qrcode` required; no manifest weakening or silent minimal mode. Any reduced mode must be explicit opt-in. Coordinate QR generation with decoder availability and verification so unavailable or rejected evidence cannot pass as a valid seal.
  - Proving artifact: paired missing-dependency and real-QR regression results plus independently checked seal payload/verification evidence.

- [ ] `WFZ-20261110-2` · P1 · Minor · Reject missing vendored infrastructure rather than materializing a successful empty module or placeholder test.
  - Outcome: `materialize()` names the unavailable module/path and fails, or its child fails `verify_child_full`; the real-source happy path vendors actual functional bytes. The original stub-module/stub-test evidence remains at the immutable review link. Current custody is `src/template_autopoiesis/gates/materialize.py::_vendor_infra_module`, `_vendor_test_file`, and `_build_tree`; the latter now emits real primitive oracle tests, which does not establish that a missing dependency is rejected.
  - Acceptance / negative control: use the current grammar API and complete primitive/oracle inputs so an unrelated missing-file error cannot satisfy the probe.
    ```bash
    python -I - <<'PY'
    import shutil
    import tempfile
    from pathlib import Path
    from template_autopoiesis.core.grammar import parse_grammar
    from template_autopoiesis.core.expand import expand
    from template_autopoiesis.gates.materialize import materialize
    from template_autopoiesis.gates.verify import verify_child_full
    grammar = parse_grammar({
        "seed": 42,
        "slots": [
            {"name": "primitive_domain", "options": ["optimization"]},
            {"name": "dep_mode", "options": ["vendor"]},
            {"name": "figure_profile", "options": ["minimal"]},
            {"name": "qr_profile", "options": ["off"]},
            {"name": "integrity_profile", "options": ["sha256"]},
        ],
        "deps": ["glossary_gen"],
    })
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        template = root / "a" / "b" / "c"
        for relative in ("src/template_autopoiesis/primitives", "tests/primitives"):
            shutil.copytree(Path.cwd() / relative, template / relative)
        try:
            child = materialize(expand(grammar), root / "children", template)
        except (FileNotFoundError, ValueError) as exc:
            assert "glossary_gen" in str(exc) or "infrastructure" in str(exc), str(exc)
        else:
            assert not verify_child_full(child.root).all_passed, "missing vendor source verified clean"
    PY
    python -I -m pytest tests/gates/test_deps_vendoring.py tests/gates/test_materialize.py -q --no-cov
    ```
  - Dependencies/constraints: preserve the intentional `dep_mode="template"` `NotImplementedError` boundary, the actual `"vendor"` fixture literal, and routing through `src/template_autopoiesis/manuscript/emit_templates.py::emit_all`. Support genuine source resolution in the declared standalone/monorepo layouts; absent source remains an explicit blocker, not a stub.
  - Proving artifact: a missing-vendor regression paired with a real-source materialization/verification receipt; importability-only placeholder tests cannot close this request.

- [ ] `WFZ-20261110-3` · P2 · Minor · Distinguish unavailable/erroring QR decoding from a genuine no-payload result.
  - Outcome: `read_qr_matrix` signals missing optional `pyzbar` or a decode error distinctly; only an actual decoder reporting no data may yield the empty result. Original evidence is `src/sealing.py:44-51`; current code is `src/template_autopoiesis/gates/sealing.py::read_qr_matrix`.
  - Acceptance / negative control:
    ```bash
    python -I - <<'PY'
    import sys
    from template_autopoiesis.gates.sealing import qr_matrix, read_qr_matrix
    matrix = qr_matrix("seal-payload")
    sys.modules["pyzbar"] = None
    sys.modules["pyzbar.pyzbar"] = None
    try:
        result = read_qr_matrix(matrix)
    except (ImportError, OSError, RuntimeError):
        pass
    else:
        assert result != "", "unavailable decoder collapsed into the no-data result"
    PY
    python -I -m pytest tests/gates/test_seal_child.py tests/gates/test_sealing.py -q --no-cov
    ```
    Pair this with a real installed-decoder payload round trip and a real no-payload image. An unavailable optional decoder is an explicit skip/blocker, not a passing round trip; an unexpected decode failure must not be swallowed as no data.
  - Dependencies/constraints: keep `pyzbar` optional, retain deterministic/offline defaults, and scope any repair to error signalling consumed by seal verification.
  - Proving artifact: separately identified success, no-data, unavailable-decoder, and decode-error results from the same source revision.
