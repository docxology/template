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
| `TEST-ISOLATION-SYSPATH-1` | open | Medium | Root and infra `conftest.py` sys.path loaders | Execution-ready recipe (2026-09-06 exploration): adopt the nested unique package per exemplar — move each `src/*.py` module into `src/<exemplar-name>/` while KEEPING the `src/` directory (all layout consumers stay valid: `public_capabilities`, `public_scope`, `project_info`, `working_render`, `export_smoke`, `stage_01_test` discovery) and keeping `src/__init__.py` as an empty namespace shim (the forkability contract is drift-gated by `checks_exemplar.py`); rewrite the ~480 `from src.`/`import src` sites to the unique package; delete all 24 `tests/__init__.py` (importlib groundwork landed); retarget the 11 regression alias loaders (`_PKG_ALIAS` registration) at `src/<name>/__init__.py`; give `checks_exemplar.check_all_export_drift` a package-init resolver; drop `tests/__init__.py` from required files; madlib `pythonpath ["."]`→`["src"]` + helpers→conftest fixtures; methods_paper pinned contract test rewrite; search_project explicit `packages`+`package-dir`; sia/autoresearch pythonpath cleanup; rebase the advanced→literature cross-exemplar symlinks (+1 `../`); note 9 exemplars are already pre-nested and textbook/literature have multi-package `src/` roots (only their flat `from src.` modules move; top-level packages stay). Verify: per-exemplar pytest ×24, the two-tree single-process acceptance below, regression manifest gate, full infra suite, exemplar matrix + provenance refresh. | isolation restructure record | `uv run pytest projects/templates/template_autopoiesis/tests projects/templates/template_sia/tests --collect-only -q` | two exemplar trees collected in one process must not resolve another tree's modules |
| `TEST-MODULE-LINE-1` | open | Medium | `tests/**` test modules + `scripts/gates/module_line_count_check.py` | Split the 14 remaining test modules above the 800-line composability budget by behavior cluster, using the same split pattern as the eight previously split modules; extend the module line-count gate to cover `tests/` so the budget is enforced rather than re-measured. | updated test modules + extended gate | `uv run python scripts/gates/module_line_count_check.py` passes with `tests/` in scope and the largest test module under 801 lines (today: `tests/infra_tests/rendering/test_slides_accessibility.py` at 4,627) | an 850-line test module must surface at the top of the size report and fail the extended gate |
| `SLOW-PROFILE-1` | open | Medium | pytest slow marker + CI test-infra lane | Implementation landed on `agent/slow-profile-1` (PR #82, open); close after hosted merge shows the scheduled test-infra-slow lane green with 116 slow tests collected. | PR #82 + scheduled slow-lane run receipt | `uv run pytest tests/infra_tests/ -m slow --collect-only -q` reports >0 collected and the scheduled CI lane runs them green | a broken slow-marked test must fail the scheduled lane while PR CI stays green — silent green on both lanes voids the row |
| `PRIVATE-IMPORT-1` | open | Medium | `tests/infra_tests` private-seam imports | Implementation landed on `agent/private-import-cutover` (PR #88, open): the nine listed seams re-pointed across 20 test modules at public entrypoints or observable behavior; close after hosted merge keeps `grep -rEn "from infrastructure\.[a-z.]+ import _" tests/` at 0 hits and the infra suite green. | updated test modules | `grep -rEn "from infrastructure\.[a-z.]+ import _" tests/` returns 0 hits and `uv run pytest tests/infra_tests/ -q` stays green | renaming `_render_pipeline_impl` in source must not break any test after the change |
| `CI-WIRING-1` | open | Medium | `tests/integration/` suite + ci.yml | Implementation landed on `agent/ci-wiring-1` (PR #83, open); close after hosted merge runs the `test-integration` job green. | PR #83 + green hosted test-integration job | `grep -n "tests/integration" .github/workflows/ci.yml` is non-empty and the job is green | renaming `run.sh` must fail the suite locally (`uv run pytest tests/integration/ -q`) while pre-wiring CI stayed green |
| `DEPRECATION-SHIM-POLICY-1` | open | Medium | `infrastructure/publishing/` flat shims + 4 live consumers | Migrate the four live old-path consumers (`infrastructure/publishing/metadata/metadata_export_cli.py`, `infrastructure/publishing/arxiv/README.md`, `tests/infra_tests/publishing/test_pypi.py`, `scripts/publish/test_pypi.py`), delete the 15 unconsumed flat shims (10 metadata/release + 5 transmission), and document the retire-when-zero-consumers policy for the three retained re-export surfaces (`platforms`, `api`, `pypi_release`) in `infrastructure/publishing/AGENTS.md`. | removed shim files + policy section | `uv run pytest tests/infra_tests/publishing/ -q` green and no `Backwards-compat shim` docstrings remain in `infrastructure/publishing/` | `uv run python -c "import infrastructure.publishing.release_receipts"` must raise ModuleNotFoundError after retirement (it succeeds today) |
| `CI-SLOWMARK-SHARD-1` | open | Medium | ci.yml test-project matrix | Implementation landed on `agent/ci-slowmark-shard-1` (PR #84, open); close after hosted merge shows slow project cells deselected on push/PR and included on schedule. | PR #84 + hosted run receipts | `grep -n "include-slow" .github/workflows/ci.yml` shows conditional gating rather than a bare flag on the PR path | a slow-marked project-test regression must fail only the scheduled lane, never silently pass PR CI |
| `REHEARSAL-PARALLEL-1` | open | Medium | release-rehearsal.yml + `scripts/maintenance/release_rehearsal.py` | Implementation landed on `agent/rehearsal-parallel-1` (PR #85, open); close after a hosted two-cell matrix run passes with equal determinism digests. | PR #85 + hosted matrix run receipt | `grep -n "matrix:" .github/workflows/release-rehearsal.yml` finds the two-cell strategy and the job stays green | unequal run digests must still fail the job — parallel cells must not weaken the two-run determinism comparison |
| `CONFTEST-DUP-1` | open | Minor | `tests/**/conftest.py` | Implementation landed on `agent/conftest-dedup-1` (PR #90, open): duplicates removed, `_test_helpers.py` shim dropped, the real helper moved to `tests/helpers/network.py`; close after hosted merge keeps both suites green with 0 `MPLBACKEND` hits outside the root conftest. | conftest edits | `grep -rn "MPLBACKEND" tests/infra_tests/conftest.py tests/integration/conftest.py` returns 0 and both suites stay green | any env-dependent regression (e.g. matplotlib backend) must fail its suite, proving the root conftest still covers children |
| `CORE-TESTING-SHIM-CUTOVER-1` | open | Minor | `infrastructure/core/` flat shims + `scripts/pipeline/stage_01_test.py` | Implementation landed on `agent/core-shim-cutover` (PR #87, open, with `STAGE-01-CLI-POLICY-1`): 11 shims deleted, all importers migrated, subprocess-policy sources re-pointed at `infrastructure/core/testing/*`; close after hosted merge keeps the canonical testing import working and the old-path import raising ImportError. | deleted shim files | old-path grep returns 0 and `uv run python -c "import infrastructure.core.test_runner"` raises ImportError | `uv run python -c "from infrastructure.core.testing.test_runner import run_per_project_pytest"` must keep working before and after |
| `CACHE-GATE-LOGGING-1` | open | Minor | `infrastructure/core/cache_gate.py` | Implementation landed on `agent/cache-gate-logging` (PR #93, open); close after hosted merge keeps `uv run pytest tests/ -k cache_gate -q` green and `grep -n "print(" infrastructure/core/cache_gate.py` at 0. | updated module | `grep -n "print(" infrastructure/core/cache_gate.py` returns 0 and `uv run pytest tests/ -k cache_gate -q` is green | a caplog test asserting the gate failure path logs ERROR must fail on the pre-change code |
| `STAGE-01-CLI-POLICY-1` | open | Minor | `scripts/pipeline/stage_01_test.py` + `stage_05_copy.py` | Implementation landed on `agent/core-shim-cutover` (PR #87, open): policy extracted to `infrastructure/orchestration/stage_policy.py` and applied to both `stage_01_test.py` and `stage_05_copy.py` with unchanged `--help`; close after hosted merge. | refactored stage scripts | `wc -l scripts/pipeline/stage_01_test.py` reports ≤ ~130 and `uv run python scripts/pipeline/stage_01_test.py --help` output is unchanged | dropping the `--public-projects requires --project-only --all-projects` guard must fail the extracted policy's unit tests |
| `CI-UV-CACHE-1` | open | Minor | `.github/actions/setup-python-env` | Implementation landed on `agent/ci-efficiency-batch` (PR #92, open); close after hosted merge shows the lockfile-keyed uv cache restore and CI stops re-downloading environments. | action.yml cache step | `grep -n "cache" .github/actions/setup-python-env/action.yml` shows a lockfile-keyed restore | reverting the cache step must make CI show environment re-downloads |
| `CI-PLAYWRIGHT-SCHEDULE-1` | open | Minor | ci.yml test-infra Playwright step | Implementation landed on `agent/ci-efficiency-batch` (PR #92, open); close after hosted merge shows the step gated on `schedule`/`workflow_dispatch` and still executing on a scheduled run. | ci.yml condition | `grep -n "playwright" .github/workflows/ci.yml` shows the step gated on `schedule`/`workflow_dispatch` | the step must still execute on a scheduled run — a permanent skip voids the row |
| `CI-COV-SCOPE-1` | open | Minor | ci.yml test-infra coverage flags | Implementation landed on `agent/ci-efficiency-batch` (PR #92, open); close after hosted merge shows the coverage floor enforced only on the Codecov-uploading cell. | ci.yml conditional cov flags | `grep -n "cov-fail-under" .github/workflows/ci.yml` shows the flag on the uploading cell only | a coverage regression must still fail the uploading cell — the floor must not disappear |
| `CI-LEAN-CACHE-1` | open | Minor | ci.yml fep-lean job | Implementation landed on `agent/ci-efficiency-batch` (PR #92, open); close after a hosted fep-lean run shows a cache hit skipping the `lake` rebuild. | ci.yml cache steps | `grep -n "elan" .github/workflows/ci.yml` shows the two cache restores | unchanged sources must yield a cache hit that skips `lake build` |
| `REHEARSAL-SCHEDULE-1` | partial | Minor | release-rehearsal.yml triggers | Monthly cron trigger landed on `agent/rehearsal-minor-batch` (PR #89, open); close after the first scheduled hosted run produces a clean-checkout receipt. | release-rehearsal.yml trigger + scheduled run link | `grep -c "cron" .github/workflows/release-rehearsal.yml` returns 1 | without the trigger, receipt staleness is undetectable until the next manual dispatch |
| `REHEARSAL-ARTIFACT-1` | partial | Minor | release-rehearsal.yml artifact upload | `run_id`-suffixed artifact names + `retention-days: 365` landed on `agent/rehearsal-minor-batch` (PR #89, open); close after two consecutive hosted dispatches produce two retrievable artifacts. | release-rehearsal.yml upload steps + two artifact links | the artifact name contains `github.run_id` and retention is explicit in the workflow | two consecutive dispatches must produce two retrievable artifacts — the old overwrite behavior must not recur |
| `REHEARSAL-SUMMARY-1` | partial | Minor | release-rehearsal.yml summarize step | Receipt-not-produced guard landed on `agent/rehearsal-minor-batch` (PR #89, open); close after a hosted receipt-less dry run prints the guard message and a receipt-ful run still prints the full receipt. | release-rehearsal.yml summary step + run link | `grep -n "receipt not produced" .github/workflows/release-rehearsal.yml` finds the guard and a receipt-less dry run passes the step | with a receipt present, the summary must still print it — the guard must not hide real receipts |
| `AUDIT-DOC-MODULE-REF-1` | open | Minor | docs/ + README.md + AGENTS.md module references | Implementation landed on `agent/doc-module-ref-gate` (PR #86, open): thin script + `infrastructure/documentation/doc_module_refs.py` logic + CI lint-job registration + README/RUN_GUIDE roster rows; close after hosted merge runs the gate green in CI. | new audit script + registration | the new gate passes on the current tree and `uv run python scripts/audit/check_doc_module_refs.py` exits 0 | a doc snippet referencing `infrastructure.publishing.nonexistent_module` must produce a failing finding |
| `AUDIT-PRINT-GUARD-1` | open | Minor | `CACHE-GATE-LOGGING-1` | Implementation landed on `agent/cache-gate-logging` (PR #93, open); close after hosted merge keeps `uv run ruff check --select T20 infrastructure/` green with the CLI ignores in place. | pyproject/ruff config change | `uv run ruff check --select T20 infrastructure/` is green with the CLI ignores in place | adding `print("x")` to a non-CLI library module must fail lint while existing CLI entrypoints stay clean |
| `CI-STACKED-MERGE-1` | open | Minor | PRs #82-#93 (12 stacked PRs) | Merge the stacked series in order #82 -> #83 -> #84 -> #85 -> #89 (rehearsal minors), then the six independent batch PRs #86/#87/#88/#90/#91/#92/#93 in any order; close each landed row above as its hosted receipt arrives. | merged PR list + hosted CI receipts | `gh pr list --state open --repo docxology/template` no longer lists the 12 heads and main CI is green | closing any row without its hosted receipt voids it |
| `SEC-PUSH-PROTECTION-FIXTURES-1` | open | Minor | credential-shaped fixtures across `tests/` | GitHub push protection rejected three pushes of synthetic fixtures (Slack `xoxb-`, AWS `AKIA`/40-char, `hf_` 40-char tails). Audit `tests/` for any remaining complete provider-token-shaped literals beyond `test_git_guards.py`, document the runtime-assembly pattern in the testing guide, and add a negative-control audit so new fixture literals fail lint. | audit report + guide section | sweep over tracked files finds zero complete provider-token-shaped literals outside the allowlist and push protection accepts pushes | a newly added tracked token-shaped literal must fail the audit |
| `SEC-SECRET-PATTERNS-1` | open | Minor | `infrastructure/project/git_guards.py` | Implementation landed on `agent/secret-patterns` (PR #91, open): four new families with every provider-shaped fixture runtime-assembled (GitHub push-protection validated the branch across three rejected iterations); close after hosted merge keeps `uv run pytest tests/ -k tracked_secret -q` green. | updated patterns + fixtures | `uv run pytest tests/ -k tracked_secret -q` green and `uv run python scripts/audit/check_tracked_secrets.py` stays green on the tree | a fixture containing an `xoxb-`-shaped token must be flagged while allowlisted documented fixtures are not |

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
