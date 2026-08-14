# Validation Gates

> Quality gates — checks that ensure contributions meet project standards before integration.

This document outlines the validation steps used to maintain code quality, correctness, and consistency in the Research Project Template.

## Overview

Before submitting a pull request or merging changes, contributors should ensure the following gates are passed:

| Gate | Purpose | How to Run | Status |
|------|---------|-------------|--------|
| **Infrastructure Tests** | Verify Layer-1 behavior and ≥60% coverage | `uv run python scripts/pipeline/stage_01_test.py --infra-only --infra-scope full` | Required |
| **Per-project Tests** | Verify one project in an isolated process and ≥90% `src/` coverage | `uv run python scripts/pipeline/stage_01_test.py --project templates/<name> --project-only` | Required for affected public projects |
| **Type Checking (MyPy)** | Catch type errors on public CI source paths | `SRC=$(uv run python -m infrastructure.project.public_scope source-paths); uv run python scripts/gates/mypy_ratchet.py $SRC` | Required (pre-commit + CI) |
| **Linting & Formatting (Ruff)** | Check the generated public lint surface | `LINT=$(uv run python -m infrastructure.project.public_scope lint-paths); uv run ruff check $LINT && uv run ruff format --check $LINT` | Required (pre-commit + CI) |
| **No-stand-ins policy** | Reject mock-framework syntax and semantic dependency replacements | `uv run python scripts/audit/verify_no_mocks.py && uv run python scripts/audit/verify_no_mocks.py --inventory --max-dependency-replacements 0` | Required (pre-push + CI) |
| **Docs and generated contracts** | Validate links, Mermaid, consistency, skill reachability, and generated-doc freshness | `uv run python scripts/audit/lint_docs.py --quiet` plus the source-owned `--check` generators in the pre-push hook | Required when applicable |
| **Confidentiality and artifact ownership** | Reject local-only resource paths and prohibited generated outputs | `uv run python scripts/audit/check_tracked_all.py && uv run python scripts/audit/check_tracked_generated_artifacts.py` | Required (pre-push + CI) |

Type checking and linting are blocking in CI and in the default pre-commit hook stage when you install hooks locally.

## Pre-commit Hooks (Recommended)

Install hooks after `uv sync` so local runs mirror CI:

- **Commit stage** (`pre-commit`): staged-secret scan, Ruff + mypy on
  generated public paths, and skill reachability.
- **Pre-push stage** (`pre-push`): generated-artifact, secret,
  confidentiality, and mirror-shape guards; both no-stand-ins checks; short
  pytest smoke; docs/generator contracts; Bandit; skills/operations manifests;
  `__all__` export audit; and skill reachability.

### Setup

```bash
uv run python scripts/maintenance/setup_pre_commit.py
```

This script installs commit and pre-push hooks, validates configuration, and can dry-run hooks.

### Manual Execution

```bash
# Commit-stage linters on all files
pre-commit run --all-files --hook-stage pre-commit

# Pre-push gates on all files
pre-commit run --all-files --hook-stage pre-push
```

### Hook Details

See [`.pre-commit-config.yaml`](../../.pre-commit-config.yaml) for the authoritative hook list. Typical entries:

| Hook | Stage | Notes |
|------|-------|-------|
| `ruff-ci` | pre-commit, manual | `ruff check --fix` + `ruff format` on public CI source paths |
| `mypy-ci` | pre-commit, manual | mypy on public CI source paths |
| `skill-reachability-check` | pre-commit, manual | Docs front-door links + generated skills-index completeness |
| `pre-push-quick` | pre-push, manual | Generated-artifact, tracked-secret, four-pool confidentiality, mirror-shape, lexical/semantic no-stand-ins guards, and `tests/infra_tests/git_hook_smoke/` |
| `docs-contract-guard` | pre-push, manual | Strict template drift, backlog/claim bindings, generated API/roster/count/publication-record checks, and the public-`AGENTS.md` memory boundary |
| `bandit-quick` | pre-push, manual | Bandit MEDIUM+ per `bandit.yaml` (mirrors the CI `security` job) |
| `skills-check` | pre-push, manual | Skill manifest (`.cursor/skill_manifest.json`) freshness |
| `operations-check` | pre-push, manual | Operations manifest (`.cursor/operations_manifest.json`) freshness |
| `all-exports-check` | pre-push, manual | `__all__` re-export audit |
| `bandit-low` | manual only | Strict LOW+MEDIUM+HIGH Bandit pass against the `bandit.yaml` allow-list |

## Coverage Gates

All code changes must maintain or improve test coverage:

- **Infrastructure code**: ≥60% coverage
- **Project code**: ≥90% coverage
- A lower measurement needs review and explanation even when the absolute floor
  remains green; coverage alone does not establish meaningful behavioral or
  scientific tests.

Run coverage locally:

```bash
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-fail-under=60 -m "not requires_ollama"
uv run pytest projects/templates/template_code_project/tests/ --cov=projects/templates/template_code_project/src --cov-fail-under=90 -m "not requires_ollama"
```

## Testing Policy

- **No stand-ins**: mock frameworks and semantic dependency replacement are
  prohibited. Use real behavior, local servers, temp files, and deterministic
  fixtures; narrow environment isolation is allowed.
- **Thin orchestrators**: Scripts in `scripts/` orchestrate; place logic in `infrastructure/` or project `src/`.
- **All new features require tests** (90% project, 60% infrastructure).

## Additional Checks

- **`verify_no_mocks.py`**: lexical scan plus a separate semantic inventory;
  run both modes shown above
- **`audit_filepaths.py`**: Validates file naming and placement conventions
- **`lint_docs.py`**: Markdown link, Mermaid, and consistency lint across docs
- **Rendered evidence**: when a change affects a public manuscript, regenerate
  from the producer and run that project's source-current render/publication
  audit. A source-only CI audit is not rendered release evidence.

Report every lane as `passed`, `failed`, `blocked`, `not run`, `not
applicable`, or `unavailable`. Missing optional tooling that produces a skip is
not a clean security, accessibility, scientific, or release result. Local gate
success also does not grant merge, tag, deposit, or publication authority.

## Related Documentation

- [Contributing Guide](contributing.md) — How to submit changes
- [Testing Guide](testing/testing-guide.md) — Writing effective tests
- [CI/CD Pipeline](../operational/build/ci-cd-integration.md) — Build and integration pipeline
- [No-Mocks Policy](../development/no-mocks-http-testing.md) — Real-only testing policy
- [Code of Conduct](code-of-conduct.md) — Community standards
