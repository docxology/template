# Template drift detection

Detects documentation/code drift in canonical exemplar projects and enforces
thin-orchestrator rules on root and project scripts.

## Entry points

- `scripts/check_template_drift.py` — CLI wrapper
- `infrastructure.project.drift.run_drift_checks()` — programmatic API

## Detectors

**Per exemplar (9 checks each)** — see [`AGENTS.md`](AGENTS.md) for the full list
(doc/code parity, script inventory, output conventions, etc.).

**Repo-level (2 checks):**

- `check_repo_docs_hardcoded_counts` — stale numeric claims in long-lived docs
- `check_repo_thin_orchestrator_scripts` — AST + line-count on root `scripts/`

**Project scripts (all discovered exemplars):**

- `check_project_scripts` — AST thin-orchestrator enforcement on `projects/*/scripts/`

## Related gates

- Module line count: `infrastructure.validation.line_count` via
  `scripts/gates/module_line_count_check.py`
- Unified health: `uv run python -m infrastructure.core.health`
