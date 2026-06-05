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
| 2 | **Composability** | No sibling-to-sibling coupling; cross-cutting concerns flow *up* through `infrastructure/core/`. No circular imports. | `import-linter` patterns + reviewer judgement. |
| 3 | **Functionality (SSOT)** | Business logic lives **only** in `infrastructure/` or `projects/<name>/src/`. Scripts and tests never re-implement it. | [Thin-orchestrator ADR](../architecture/adrs/001-thin-orchestrator-pattern.md) + `scripts/verify_no_mocks.py`-style reviewer scan. |
| 4 | **Testability / Tested** | Coverage gates met (infra **60%**, project **90%**). No mocks. Deterministic seeds. tmp_path for I/O. `pytest-httpserver` for HTTP. | `uv run pytest --cov-fail-under=...` + [Zero-mock ADR](../architecture/adrs/004-zero-mock-testing-policy.md). |
| 5 | **Validation** | Inputs validated at the system boundary (CLI, public function). No hard-coded host paths. Narrow `except` (not bare `except Exception`). | `bandit -c bandit.yaml -r -ll infrastructure/ scripts/ projects/` + reviewer. |
| 6 | **Documentation** | Module has a guide in `docs/modules/guides/<module>-module.md`. Public functions have docstrings. Changes to architecture have an ADR. | `infrastructure/validation/docs/` linters + reviewer. |
| 7 | **Conventions** | Type hints on public APIs. Consistent error/logging via `infrastructure.core.logging.utils.get_logger`. PEP 8 + project style. | `uvx ruff check` + `uv run mypy` on public CI source paths. |
| 8 | **Reproducibility** | Deterministic outputs given the same inputs. Fixed RNG seeds. No reliance on wall-clock except through injectable helpers. `MPLBACKEND=Agg` for headless plotting. | Pipeline re-run yields byte-identical artefacts (steganographic checks excepted). |

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

Run these locally; they mirror CI exactly:

```bash
SRC=$(uv run python -m infrastructure.project.public_scope source-paths)
uvx ruff check --fix $SRC tests/ scripts/
uvx ruff format $SRC tests/ scripts/
uv run mypy $SRC
uv run bandit -c bandit.yaml -r -ll infrastructure/ scripts/ projects/
uv run python scripts/verify_no_mocks.py
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-fail-under=60
uv run pytest projects/<name>/tests/ --cov=projects/<name>/src --cov-fail-under=90
pre-commit run --all-files
pre-commit run --hook-stage pre-push --all-files
```

A clean pass on all of the above is necessary but not sufficient — a human still
reads the diff against the eight criteria.

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
