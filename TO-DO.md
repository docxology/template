# Repo TO-DO — future cross-cutting work

> **Design ethos:** modular, intelligent, functional, logged, tested, and
> documented. Real methods only; never mocks or fakes. Every release ships with
> green tests, source-bound evidence, and accurate documentation.

This is the root repository backlog and contains future work only: cross-cutting
infrastructure, CI, documentation, release, security, and reproducibility
improvements. Completed work is preserved in [`CHANGELOG.md`](CHANGELOG.md) or
the dated maintenance records; generated facts remain owned by their
generators; exemplar-specific work belongs in the relevant public
`projects/templates/*/TODO.md`.

Every active row has a stable ID and the complete contract
`ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control`.
Active work is decomposed into Minor or Medium slices. A missing owner,
external receipt, or optional tool is a blocker, never an implicit success.

## Live baseline and constraints

The public roster is authoritative in
[`docs/_generated/active_projects.md`](docs/_generated/active_projects.md), and
measured facts are authoritative in
[`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md). Re-derive them before
editing this file or closing a row.

The deterministic default is offline and one-process-per-project. Network,
LLM, live-data, container, formal-tool, raster, and publication paths are
explicitly opt-in and fail closed when unavailable. Private sidecars,
rotating projects, branch protection, CODEOWNERS review, and owner-authorized
promotion are outside the evidence a local checkout can establish.

## Active root backlog

These are the prioritized scoped improvements and remaining root-level actions, classified by Minor, Medium, and Major categories.

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `CLEAN-CHECKOUT-MAJ-1` | blocked-external | Medium | Local disposable rehearsal and hosted Linux runner | Run two deterministic hosted-Linux rehearsals and attach the owner/platform receipt; local generated render output is restored only inside the disposable clone after path-boundary validation. | clean-checkout rehearsal receipt | `uv run python scripts/maintenance/release_rehearsal.py --execute --receipt /tmp/template-clean-checkout.json` | non-generated mutation, dirty final tree, changed revision, or unequal deterministic runs must fail |
| `SECURITY-PRIVATE-PROMOTION-1` | blocked-external | Medium | Owner authorization, redaction, and export evidence | Obtain an owner-approved private-sidecar promotion record before any promotion; keep the public tree and generated receipts free of private paths and content. | owner promotion receipt | `uv run python scripts/audit/check_tracked_all.py` | private path, sidecar content, credential, or unredacted export must fail public guards |
| `TEST-ISOLATION-SYSPATH-1` | open | Medium | Root and infra `conftest.py` sys.path loaders | Execution-ready recipe (2026-09-06 exploration): adopt the nested unique package per exemplar — move each `src/*.py` module into `src/<exemplar-name>/` while KEEPING the `src/` directory (all layout consumers stay valid: `public_capabilities`, `public_scope`, `project_info`, `working_render`, `export_smoke`, `stage_01_test` discovery) and keeping `src/__init__.py` as an empty namespace shim (the forkability contract is drift-gated by `checks_exemplar.py`); rewrite the ~480 `from src.`/`import src` sites to the unique package; delete all 24 `tests/__init__.py` (importlib groundwork landed); retarget the 11 regression alias loaders (`_PKG_ALIAS` registration) at `src/<name>/__init__.py`; give `checks_exemplar.check_all_export_drift` a package-init resolver; drop `tests/__init__.py` from required files; madlib `pythonpath ["."]`→`["src"]` + helpers→conftest fixtures; methods_paper pinned contract test rewrite; search_project explicit `packages`+`package-dir`; sia/autoresearch pythonpath cleanup; rebase the advanced→literature cross-exemplar symlinks (+1 `../`); note 9 exemplars are already pre-nested and textbook/literature have multi-package `src/` roots (only their flat `from src.` modules move; top-level packages stay). Verify: per-exemplar pytest ×24, the two-tree single-process acceptance below, regression manifest gate, full infra suite, exemplar matrix + provenance refresh. | isolation restructure record | `uv run pytest projects/templates/template_autopoiesis/tests projects/templates/template_sia/tests --collect-only -q` | two exemplar trees collected in one process must not resolve another tree's modules |
| `CORE-TESTING-REHOME-1` | open | Medium | Established `_`-prefix re-export shim pattern (`security.py`→`_validation.py`) | Re-home the ~16-module pytest/testing cluster (~3,600 lines: `test_runner`, `pytest_orchestration`, `public_matrix_receipt`, `test_performance`, `pytest_profiles`, `script_discovery`, …) from the flat `infrastructure/core/` top level into an `infrastructure/core/testing/` package with one-line re-export shims at the old paths; update AGENTS/SKILL module maps. | re-home record with import-parity check | `uv run python scripts/audit/check_tracked_all.py && uv run pytest tests/infra_tests/core/ -q` | an old import path that stops resolving must fail the parity check |
| `RENDERING-PANDOC-ARGS-1` | open | Minor | Shared `_output_text.py` dedup landed | Extract the combined-pandoc-args assembly (resource-path triple, formalism filter, pandoc-crossref probe, citeproc+bibliography args) duplicated across `_combined_exports.py` DOCX/EPUB/HTML lanes and `ebook_stage.py` into one builder so the resource-path contract cannot drift per edition. | dedup record | `uv run pytest tests/infra_tests/rendering/ -q` | a lane missing one resource-path leg must fail the parity test |
| `TEST-MODULE-SPLITS-1` | open | Medium | Section-banner conventions in the eight oversized modules | Split the eight >800-line test modules (test_combined_exports 1,347; test_pipeline 1,333; test_slides_renderer_core 1,213; test_web_renderer 1,067; test_output_validator 980; test_publishing 842; test_counts_doc; test_artifact_manifest_semantics) along their existing section banners into per-production-module files; pure moves, no behavior change. | split record with collection-parity check | `uv run pytest tests/infra_tests/ -q --co` | collected test count before/after the split must match exactly |
| `RENDERING-LAYERING-1` | open | Medium | Compat-alias re-export pattern | Remove the rendering→publishing layering inversion: `_manuscript_source.py`, `_combined_exports.py`, and `pipeline.py` import `publishing.transmission_bookends`; re-home the `transmission_*` family into a rendering-owned module (or `infrastructure/transmission/`) with publishing-side compat aliases, then decouple the four flat publishing prefix families (`metadata_*`, `release_*`) as subpackages. | layering record | `uv run pytest tests/infra_tests/rendering/ tests/infra_tests/publishing/ -q` | an import-lint rule forbidding rendering→publishing imports must pass |
| `REHEARSAL-ANALYSIS-EXIT-1` | open | Medium | Hosted rehearsal receipt (run 34062060327) and local probe | Triage the deterministic exit 1 in the fresh-clone release-profile run: active_inference's test stage reports 'All tests passed - ready for analysis' and the stage then exits 1 silently (log ends at the resource-usage line; 2026-09-06 run on main `9c0022745`, pre-dating batch-1). Machinery upgraded 2026-09-06: receipts now carry a bounded redacted output tail on failure (digest-only receipts were undiagnosable), and the plan's matrix command runs the quick profile with two project workers (the serial release profile cannot fit any sane job budget — one exemplar alone exceeded 60 minutes in the local probe). Triage findings 2026-09-06 (disposable-clone probes): (1) the project test stage itself is green — active_inference release: 898 passed, 92.67% coverage, declared verifier passed; (2) a same-clone run that executes the infra suite AFTER the project pass fails `test_every_public_exemplar_declares_output_artifact` because the project stage legitimately regenerates tracked outputs (`test_results.json/md` embed run durations; `artifact_provenance.json` re-hashes) — CI never sees this because its infra and project lanes run on separate checkouts, so any diagnostic run must use `--project-only` and must not follow with infra validation in one clone; (3) the runner's report records `failed: 1, failed_tests: []` for infra failures — the failing test's identity is not captured (fold into the output-tail work). Hosted re-dispatch (run 34088286458) isolated it precisely via the new failure tails: both fresh-clone runs' `stage_01_test.py --project-only --all-projects --public-projects --profile quick --project-workers 2 --receipt …` commands print an all-green receipt (every exemplar row OK, combined coverage 94.08% >= 75%, matrix receipts written) and then EXIT 1 (183.6s and 175.9s; both runs identical) — a deterministic bug in the all-projects aggregation path, not in any exemplar. CI never exercises this path: the only lane running all-projects+receipt is the schedule-only public-matrix-receipt job. Next: reproduce locally with the exact flags in a fresh clone (fast under the quick profile), trace the runner's exit aggregation after the verifier passes (stage_01_test.py / multi-project aggregation), fix, re-dispatch, and close CLEAN-CHECKOUT-MAJ-1 with the green receipt. The hosted runner's git handles `clone --no-local --revision` (verified: run-1 reached stage_01). | rehearsal failure record + fix | `uv run python scripts/maintenance/release_rehearsal.py --execute --receipt /tmp/rr.json` (exit 0, equal digests) | a silent exit 1 with all tests passing must not be treated as a green rehearsal |

## Verification order

Run the bounded deterministic gates before any optional authority or provider
work:

```bash
uv run pytest tests/infra_tests/documentation/ tests/infra_tests/publishing/ -q --no-cov --timeout=120
uv run pytest tests/regression/ -q --no-cov --timeout=120
uv run python scripts/audit/check_backlog.py --strict
uv run python scripts/docgen/counts.py --check
uv run python scripts/audit/check_claim_bindings.py --json
uv run python scripts/audit/check_public_template_contract.py --strict
uv run python scripts/audit/check_template_drift.py --strict
uv run python scripts/audit/check_tracked_all.py
uv run python scripts/audit/check_tracked_generated_artifacts.py
uv run python scripts/audit/check_tracked_secrets.py
```

Then run the isolated public matrix, infrastructure coverage gate, Ruff,
mypy, Bandit, no-mocks, generated-document, manuscript/render, and
accessibility checks. Optional paths must emit `skipped` or `blocked` receipts
when their tools or external authority are unavailable.

## Backlog operating rules

- Re-derive measured facts instead of copying old counts into prose.
- Keep private or rotating project names out of public docs; use the generated roster.
- Prefer real files, subprocesses, deterministic fixtures, and negative controls.
- Keep business logic in `infrastructure/` or project `src/`; scripts remain thin orchestrators.
- Preserve project coverage floors, confidentiality, generated-artifact guards,
  provenance boundaries, and explicit optional-tool skips.
- When an item is complete, move its dated evidence to the changelog or review
  record and remove it from this file in the same change.
