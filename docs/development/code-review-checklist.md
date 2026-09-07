# Code Review Checklist

This document is the **single source of truth** for what "ready to merge" means in
this repository. Every PR is reviewed against the **eight criteria** below. They
apply uniformly to `infrastructure/`, `scripts/`, `tests/`, and project
`src/`/`tests/` trees.

The criteria are intentionally short. The authoritative *how-to* lives in the
linked documents; this file enumerates **what must be true** before a change is
accepted.

---

## The Eight Criteria

| # | Criterion | One-line definition | Authoritative gate |
|---|-----------|---------------------|--------------------|
| 1 | **Clarity** | Module purpose obvious from `__init__.py` docstring; public APIs documented; no dead code. | Reviewer reading + `ruff` (E/W/D rules where enabled). |
| 2 | **Composability** | Dependency direction follows the owning `AGENTS.md`; cross-cutting behavior belongs at a genuinely shared layer and imports remain cycle-free. | Public import/export gates, focused tests, and reviewer judgement. |
| 3 | **Functionality (SSOT)** | Business logic lives **only** in `infrastructure/` or `projects/<name>/src/`. Scripts and tests never re-implement it. | [Thin-orchestrator ADR](../architecture/adrs/001-thin-orchestrator-pattern.md) + `scripts/audit/verify_no_mocks.py`-style reviewer scan. |
| 4 | **Testability / Tested** | Coverage gates met (infra **60%**, project **90%**); mock frameworks and semantic dependency replacements absent; deterministic seeds; `tmp_path` for I/O; local real HTTP for HTTP boundaries. | Stage-01 coverage contracts, both `verify_no_mocks.py` modes, and [Zero-mock ADR](../architecture/adrs/004-zero-mock-testing-policy.md). |
| 5 | **Validation** | Inputs validated at the system boundary (CLI, public function). No hard-coded host paths. Narrow `except` (not bare `except Exception`). | `bandit -c bandit.yaml -r -ll infrastructure/ scripts/ projects/` + reviewer. |
| 6 | **Documentation** | Module has a guide in `docs/modules/guides/<module>-module.md`. Public functions have docstrings. Changes to architecture have an ADR. | `infrastructure/validation/docs/` linters + reviewer. |
| 7 | **Conventions** | Type hints on public APIs. Consistent error/logging via `infrastructure.core.logging.utils.get_logger`. PEP 8 + project style. | `uv run ruff check` + `uv run mypy` on public CI source paths. |
| 8 | **Reproducibility** | Declared deterministic outputs bind canonical inputs, configuration, code, and toolchain; fixed RNG seeds and injectable time are used where promised. | Producer-specific negative controls, manifests/freshness receipts, and byte comparison only for artifacts whose contract promises bitwise identity. |

If a change cannot meet a criterion, raise an ADR explaining the deviation — do
not silently merge.

Decision rationale follows the repository memory contract in
[`docs/rules/memory_and_decision_records.md`](../rules/memory_and_decision_records.md):
use `WHY:` comments for counterintuitive local choices, ADRs for structural
rules, generated docs for volatile facts, and negative controls for verifier
claims.

---

## Mapping to the Reviewed Trees

| Tree | Most-load-bearing criteria | Secondary |
|------|---------------------------|-----------|
| `infrastructure/` | 1, 2, 3, 6, 7 | 4, 5, 8 |
| `scripts/` | 3 (thin orchestrator), 7 | 1, 4, 5, 6 |
| `tests/` | 4 (no-mocks, real data, tmp_path), 8 (determinism) | 1, 7 |
| `docs/` | 1, 6, 7 | — |
| `projects/<name>/src/` | 1, 4, 6, 8 | 3 |

---

## Quick Self-Check Before Opening a PR

Run the applicable local contracts below. Hosted platform/version matrices and
external repository settings remain CI/administrator evidence; no single local
command mirrors those exactly.

```bash
LINT=$(uv run python -m infrastructure.project.public_scope lint-paths)
SRC=$(uv run python -m infrastructure.project.public_scope source-paths)
uv run ruff check $LINT
uv run ruff format --check $LINT
uv run python scripts/gates/mypy_ratchet.py $SRC
uv run bandit -c bandit.yaml -r -ll infrastructure/ scripts/ projects/
uv run python scripts/audit/verify_no_mocks.py
uv run python scripts/audit/verify_no_mocks.py --inventory --max-dependency-replacements 0
uv run python scripts/pipeline/stage_01_test.py --infra-only --infra-scope full
uv run python scripts/pipeline/stage_01_test.py --project templates/<name> --project-only
uv run python scripts/audit/lint_docs.py --quiet
uv run python scripts/audit/check_tracked_all.py
uv run python scripts/audit/check_tracked_generated_artifacts.py
pre-commit run --all-files --hook-stage pre-commit
pre-commit run --all-files --hook-stage pre-push
```

A clean pass on applicable lanes is necessary but not sufficient. Record
capability-driven skips and unrun lanes, inspect the diff, and keep engineering,
scientific, accessibility, owner-approval, merge, release, and publication
status separate.

---

## What "Concisely Enshrined" Means

Every criterion above is intentionally bound to **one authoritative artefact**:

1. An **ADR** under [`docs/architecture/adrs/`](../architecture/adrs/) when the
   criterion expresses a constitutional rule (e.g. ADR 001 thin-orchestrator,
   ADR 004 zero-mock).
2. A **gate** in CI (`.github/workflows/ci.yml`) or pre-commit
   (`.pre-commit-config.yaml`) when the criterion is mechanically checkable.
3. A **module guide** under [`docs/modules/guides/`](../modules/guides/) when
   the criterion is module-specific.

If you find a criterion enforced in code but not documented in (1) or (2) — or
documented but not enforced — open an issue tagged `criteria-drift`.

---

## Related Documents

* [`docs/architecture/adrs/`](../architecture/adrs/) — constitutional rules
* [`docs/development/validation_gates.md`](validation_gates.md) — gate details
* [`docs/development/testing/testing-guide.md`](testing/testing-guide.md) — test patterns
* [`docs/rules/memory_and_decision_records.md`](../rules/memory_and_decision_records.md) — rationale, ADR, local-memory, and negative-control policy
* [`docs/best-practices/best-practices.md`](../best-practices/best-practices.md) — style and structure
* [`docs/modules/guides/`](../modules/guides/) — per-module specifics
* [`.github/AGENTS.md`](../../.github/AGENTS.md) — CI job names + coverage floors
* [`CLAUDE.md`](../../CLAUDE.md) — copy-paste commands

This file is the **index of expectations**; the linked documents are the **detail**.
