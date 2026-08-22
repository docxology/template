# Deep-Pass Session Report — ox-alpha (sixth independent session, 2026-08-21)

Scope: full-repository deep assessment + improvement pass per
`~/HermesWorkspace/instituteos_deep_pass/brief.md`, executed in a sixth
independent session. Prior sessions' reports: canonical backlog
`DEEP_PASS_2026-08-21.md`; `_dr-pai.md`, `_dr-pai-session.md`,
`_addendum_dr-pai-session-2.md`, `_ox-alpha.md`, `_ox-alpha-session2.md`.
Minor/medium findings fixed and verified; majors adopted by reference.

## State on arrival

- Branch `main`, HEAD `0db2afcbb` at session start (concurrent sessions were
  committing throughout; tip moved to `cb1db305b` during this session).
- Tree dirty with work owned by other sessions: rendering helpers + slides
  tests (`infrastructure/rendering/*`, `tests/infra_tests/rendering/*`),
  `template_active_inference` output-data provenance JSONs, docs
  (`docs/guides/extending-and-automation.md`, `docs/operational/runbook.md`,
  `.github/README.md`, staged `CHANGELOG.md`), and several test files
  (`test_cli.py`, `test_suite_runner.py`, `test_doc_pair_lint.py`,
  integration `test_run_sh.py` / `test_secure_run_sh.py`). All left
  untouched per the hard rules.

## Gates measured this session (fresh runs)

| Gate | Result |
| --- | --- |
| Ruff on full public lint surface (`public_scope lint-paths`) | **All checks passed** |
| mypy on import-safe source paths (`public_scope source-paths`, 1559 files) | **Success: no issues** |
| No-mocks lexical gate + semantic inventory | **Status: clear** — dependency_replacement 0, total 401 |
| Tracked-resource guards (`check_tracked_all.py`) | projects/fonds/rules/tools: **clean** |
| Tracked-secret scan | **No high-confidence credentials** |
| Template drift (`--strict`) | **no drift detected** |
| `__all__` exports audit | **0 violations** |
| Module line-count gate | 2 WARN only (`rendered_snapshot.py` 800, `full_verification.py` 929) — below fail threshold, ratchet-tracked |
| Pipeline smoke suite (`stage_01_test.py --infra-only --infra-scope pipeline-smoke`) | Initially **1 failure**, after fix **209 passed, 1 deselected in 77.85s** |

## Findings

### Minor (fixed)

- **F1 (flaky test class) — repo-default 10s pytest timeout kills the
  subprocess-heavy pipeline-executor tests under load.** Evidence: three
  distinct tests timed out across four smoke-suite runs, each hanging inside
  real `subprocess` work with no per-test override:
  - `tests/infra_tests/git_hook_smoke/test_tracked_generated_artifacts.py::test_current_repo_has_no_tracked_generated_artifacts`
    (its inner `subprocess.run(timeout=120)` is fine; the outer pytest-timeout
    10s cap fired first),
  - `tests/infra_tests/core/test_pipeline.py::TestPipelineExecutor::test_execute_full_pipeline_success`
    (22.10s standalone, passes),
  - `...::test_execute_core_pipeline_success` and
    `...::test_skip_llm_execution` (timeout stacks show real child-process
    wait / sysctl cleanup in `execution_boundary.py`, not deadlocks).
  Fix: explicit `@pytest.mark.timeout(60)` on all nine
  subprocess-executing tests in `test_pipeline.py` and
  `@pytest.mark.timeout(150)` on the generated-artifact scan test (measured
  ~39-41s for the underlying script). Verified by fresh runs:
  - affected files directly: `2 passed in 2.00s` / `9 passed in 41.67s`;
  - full smoke lane: **209 passed, 1 deselected in 77.85s, exit 0**
    (previously exit 1 with "1 failure(s) exceeds tolerance").
  Ruff + ruff-format clean on both edited files.

### Medium (deferred, ownership)

- **F2 — concurrent-session dirty state blocks some gates.**
  `check_mirror_symlinks.py` flags gitignored private content at
  `projects/active/project`, `projects/working/ap3`,
  `projects/working/Untitled`; provenance-coupled checks on
  `template_active_inference` outputs are unstable while another session's
  edits to those JSONs are uncommitted. Not mine to move/regenerate/commit;
  same conclusion as prior sessions' F4/M1/F2.

### Major (scoped, not implemented)

No new majors. The scoped majors in the canonical backlog
(`DEEP_PASS_2026-08-21.md` / `_ox-alpha.md`: coverage-provenance automation
coupling; Python 3.14 full-suite runtime architecture; oversized-module
decompositions) remain accurate and are adopted by reference.

## What I verified but did not change

- `scripts/docgen/api_reference.py --check`: clean (`stage_table.py` has no
  `--check` flag; its generator ran as a no-op against committed targets).
- Unified health (`infrastructure.core.health --workers 1/4`) was attempted
  twice and exceeded the 420s tool ceiling on this loaded multi-session
  machine; individual constituent gates above were each run and measured
  instead. The fifth session recorded an end-to-end health measurement.
- Docs lint not re-run end-to-end (time-boxed); the fifth session verified it
  with the raised gate ceiling.

## Commits (this session, path-scoped, not pushed)

- `deep-pass: raise pytest timeouts on subprocess-heavy executor/smoke tests (repo default 10s flakes under load)` -
  `tests/infra_tests/core/test_pipeline.py`,
  `tests/infra_tests/git_hook_smoke/test_tracked_generated_artifacts.py` only.

## Deliverable checklist

- [x] Classified findings with evidence (this file + canonical backlog)
- [x] Minor fixes implemented and verified by real runs
- [x] Path-scoped local commits of my files only
- [x] Summary printed to terminal


## Addendum (21:06) — commit race on the fix files

The first commit of this session's fix (`fcb7773e7`, 20:58:55) landed with the
report but **without the two test-file edits**: between my edits and the
path-scoped commit, concurrent deep-pass sessions were racing in this same
checkout and the working-tree test files were overwritten (the `-S` hit for
`@pytest.mark.timeout(60)` inside `fcb7773e7` was from this report's prose,
not the code). The fix was re-applied and committed as `1b6074262`
(path-scoped: only the two test files). Re-verification after re-commit:

- `pytest tests/infra_tests/core/test_pipeline.py -q --timeout=90`:
  **18 passed in 30.69s**
- `pytest tests/infra_tests/git_hook_smoke/test_tracked_generated_artifacts.py
  -q --timeout=200`: **9 passed**; ruff clean on both files
- Full smoke lane: **209 passed, 1 deselected in 45.61s, exit 0**

This is the same commit-race hazard prior sessions recorded (F5 in the
fifth-session report); treat any single-session file write here as
uncommitted-until-verified.
