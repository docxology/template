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
| `SECURITY-PRIVATE-PROMOTION-1` | blocked-external | Medium | Owner authorization, redaction, and export evidence | Obtain an owner-approved private-sidecar promotion record before any promotion; keep the public tree and generated receipts free of private paths and content. | owner promotion receipt | `uv run python scripts/audit/check_tracked_all.py` | private path, sidecar content, credential, or unredacted export must fail public guards |
| `TEST-ISOLATION-SYSPATH-1` | open | Medium | Root and infra `conftest.py` sys.path loaders | Recipe state after the 2026-09-11 split (04f016915, #99): the 8 namespace-shim exemplars (`template_code_project`, `template_sia`, `template_search_project`, `template_prose_project`, `template_pools_rules_tools`, `template_methods_paper`, `template_madlib`, `template_eda_notebook`) keep `src/__init__.py` as an empty namespace shim with all modules under `src/<pkg>/`, their `tests/__init__.py` deleted, and their scripts/tests/regression tables importing the unique package (e.g. `from template_code_project.core.optimizer import ...`). Remaining: move the four exemplars that still legitimately carry flat top-level modules (`template_pitch_deck`, `template_gold_refinement`, `template_active_inference`, `template_textbook` — only their flat `from src.` modules move; top-level packages stay), sweep residual `from src.`/`import src` sites in the 13 exemplars still shipping `tests/__init__.py`, retarget the remaining `_PKG_ALIAS` regression loaders (madlib, gold_refinement), and finish the per-exemplar items from the 2026-09-06 recipe (madlib pythonpath, methods_paper pinned contract, search_project packaging, sia/autoresearch pythonpath cleanup, advanced→literature symlink rebase). Verify: per-exemplar pytest ×24, the two-tree single-process acceptance below, regression manifest gate, full infra suite, exemplar matrix + provenance refresh. | isolation restructure record | `uv run pytest projects/templates/template_autopoiesis/tests projects/templates/template_sia/tests --collect-only -q` | two exemplar trees collected in one process must not resolve another tree's modules |
| `SLOW-PROFILE-1` | open | Medium | pytest slow marker + CI test-infra lane | Implementation landed on `agent/slow-profile-1` (PR #82, open); close after hosted merge shows the scheduled test-infra-slow lane green with 116 slow tests collected. | PR #82 + scheduled slow-lane run receipt | `uv run pytest tests/infra_tests/ -m slow --collect-only -q` reports >0 collected and the scheduled CI lane runs them green | a broken slow-marked test must fail the scheduled lane while PR CI stays green — silent green on both lanes voids the row |
| `CI-WIRING-1` | open | Medium | `tests/integration/` suite + ci.yml | Implementation landed on `agent/ci-wiring-1` (PR #83, open); close after hosted merge runs the `test-integration` job green. | PR #83 + green hosted test-integration job | `grep -n "tests/integration" .github/workflows/ci.yml` is non-empty and the job is green | renaming `run.sh` must fail the suite locally (`uv run pytest tests/integration/ -q`) while pre-wiring CI stayed green |
| `CI-SLOWMARK-SHARD-1` | open | Medium | ci.yml test-project matrix | Implementation landed on `agent/ci-slowmark-shard-1` (PR #84, open); close after hosted merge shows slow project cells deselected on push/PR and included on schedule. | PR #84 + hosted run receipts | `grep -n "include-slow" .github/workflows/ci.yml` shows conditional gating rather than a bare flag on the PR path | a slow-marked project-test regression must fail only the scheduled lane, never silently pass PR CI |
| `REHEARSAL-PARALLEL-1` | open | Medium | release-rehearsal.yml + `scripts/maintenance/release_rehearsal.py` | Implementation landed on `agent/rehearsal-parallel-1` (PR #85, open); close after a hosted two-cell matrix run passes with equal determinism digests. | PR #85 + hosted matrix run receipt | `grep -n "matrix:" .github/workflows/release-rehearsal.yml` finds the two-cell strategy and the job stays green | unequal run digests must still fail the job — parallel cells must not weaken the two-run determinism comparison |


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
