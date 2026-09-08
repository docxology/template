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
| `REHEARSAL-ANALYSIS-EXIT-1` | partial | Medium | Hosted re-dispatch of the quick-profile public matrix | Diagnosability hardened 2026-09-07: the rehearsal now persists each run's public-matrix receipt plus full redacted failed-command logs beside the top-level receipt (``--artifact-dir``, uploaded by CI), so a hosted exit-1 is triageable after the runner is gone. 2026-09-08: hosted run 34186872361 failed on the health docs-lint gate — CI=true makes the mermaid gate strict while fresh clones lack mmdc; fixed by provisioning the docs-lint toolchain in the rehearsal job (``setup-docs-lint``) and by rendering ``runtime_error`` in every docs-lint emission path (was: a silent empty-output exit). Root cause found and fixed 2026-09-07 (local probe with the exact all-projects flags): (1) the deterministic exit 1 behind an all-green receipt was the receipt's output-isolation check — every exemplar's declared Stage-01 verifier legitimately regenerates manifest-declared outputs (``artifact_provenance.json`` re-pins ``source_commit`` to the current HEAD), so the before/after digest flipped on any fresh clone at a newer commit; the isolation comparison now excludes each project's ``output/reports/artifact_manifest.json``-declared paths (negative control preserved: undeclared output mutations still fail; see ``test_receipt_rejects_test_generated_output_drift``). (2) The probe also surfaced storybook's quick-profile floor gap — resolved 2026-09-07 by unmarking the 7 slow-marked rendering tests (16.6s of real PIL rendering; the 90% floor now holds in every profile, quick lane exit 0 verified). Remaining: re-dispatch the hosted quick-profile matrix and close ``CLEAN-CHECKOUT-MAJ-1`` with the green receipt. | changelog 2026-09-07 entry + local probe receipt | `uv run python scripts/pipeline/stage_01_test.py --project-only --all-projects --public-projects --profile quick --project-workers 2 --receipt /tmp/rr.json` (exit 0) | a silent exit 1 with all tests passing must not be treated as a green rehearsal |

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
