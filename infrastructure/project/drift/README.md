# Template drift detection

Detects documentation/code drift in canonical exemplar projects and enforces
thin-orchestrator rules on root and project scripts.

## Entry points

- `scripts/audit/check_template_drift.py` — CLI wrapper
- `infrastructure.project.drift.run_drift_checks()` — programmatic API

## Detectors

**Per exemplar (9 checks each)** — see [`AGENTS.md`](AGENTS.md) for the full list
(doc/code parity, script inventory, output conventions, etc.).

**Repo-level (2 checks):**

- `check_repo_docs_hardcoded_counts` — stale numeric claims in long-lived docs
- `check_repo_thin_orchestrator_scripts` — AST + line-count on root `scripts/`

**Project scripts (all discovered exemplars):**

- `check_project_scripts` — AST thin-orchestrator enforcement on `projects/*/scripts/`

## What `--strict` does (and does NOT) mean

`--strict` is a **severity promotion**, not a broader scan. In
`exit_code_for_report` it only changes one thing: existing **WARNING**-level
findings flip the exit code to `1` instead of `0`. It does **not** enable any
additional checks, and it must not be read as "comprehensive". The exact same
set of detectors runs in both modes; `--strict` simply refuses to tolerate the
advisory (WARN) findings.

The WARNING tier today is limited to heuristic advisories: fat-script
detection (`orchestrator.py`), oversize-`src`, blanket-`except`, and
publication-metadata advisories (`checks.py`). Everything else is either an
ERROR (hard fail in both modes) or not checked at all.

### Known non-goals (intentionally NOT enforced by drift, in any mode)

These are out of scope for the drift checker — do not assume `--strict` covers
them; they are caught (if at all) by other gates or not at all:

- **Coverage-floor _value_ thresholds.** `check_coverage_floor_consistency`
  only verifies that the `fail_under` value quoted in docs equals
  `pyproject.toml`; it does not assert that an exemplar's floor is `>= 90`.
- **Extended mock primitives in project tests.** The drift mock check uses a
  narrower pattern set than `infrastructure.validation.output.no_mock_enforcer`
  (`validate_no_mocks`). The authoritative, broadest no-mocks enforcement is
  `scripts/audit/verify_no_mocks.py`, which scans the repo `tests/` tree **plus**
  every public exemplar's `tests/` directory.
- **External URL liveness / markdown anchors.** `cross_link_lint` strips
  anchors and skips `http(s)` links entirely; link reachability is not checked.
- **Historical / behavioral prose claims.** Narrative statements about past
  behavior pass both drift and `lint_docs`.

## Related gates

- Module line count: `infrastructure.validation.line_count` via
  `scripts/gates/module_line_count_check.py`
- Unified health: `uv run python -m infrastructure.core.health`
