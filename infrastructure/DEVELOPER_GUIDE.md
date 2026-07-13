# Infrastructure Developer Guide

> **Note:** This file was previously stored as a corrupt single-line JSON blob and has been
> restored as a minimal accurate stub. The canonical developer reference is split across the
> per-package `AGENTS.md` files listed below.

## Quick orientation

| Topic | Canonical source |
|-------|-----------------|
| Architecture overview | [`infrastructure/AGENTS.md`](AGENTS.md) |
| Module map and import patterns | [`infrastructure/SKILL.md`](SKILL.md) |
| Core utilities (logging, config, exceptions) | [`infrastructure/core/AGENTS.md`](core/AGENTS.md) |
| Validation | [`infrastructure/validation/AGENTS.md`](validation/AGENTS.md) |
| Rendering | [`infrastructure/rendering/AGENTS.md`](rendering/AGENTS.md) |
| Publishing | [`infrastructure/publishing/AGENTS.md`](publishing/AGENTS.md) |
| Reporting | [`infrastructure/reporting/AGENTS.md`](reporting/AGENTS.md) |
| LLM integration | [`infrastructure/llm/AGENTS.md`](llm/AGENTS.md) |
| Orchestration | [`infrastructure/orchestration/AGENTS.md`](orchestration/AGENTS.md) |
| Doctor (diagnostics) | [`infrastructure/doctor/AGENTS.md`](doctor/AGENTS.md) |
| Steganography | [`infrastructure/steganography/AGENTS.md`](steganography/AGENTS.md) |
| Prose analysis | [`infrastructure/prose/AGENTS.md`](prose/AGENTS.md) |
| Literature search | [`infrastructure/search/AGENTS.md`](search/AGENTS.md) |
| Reference / BibTeX | [`infrastructure/reference/AGENTS.md`](reference/AGENTS.md) |
| Scientific utilities | [`infrastructure/scientific/AGENTS.md`](scientific/AGENTS.md) |
| Skill discovery | [`infrastructure/skills/AGENTS.md`](skills/AGENTS.md) |
| Project management | [`infrastructure/project/AGENTS.md`](project/AGENTS.md) |

## Key conventions

- **Thin orchestrator pattern** — scripts coordinate, modules implement. Never put business logic in `scripts/`.
- **No mocks** — all tests use real data and computations (`pytest-httpserver` for HTTP, real `tmp_path` for files).
- **Coverage floors** — infrastructure ≥ 60%, projects ≥ 90%.
- **Logging** — always `from infrastructure.core.logging.utils import get_logger; logger = get_logger(__name__)`.
- **Exceptions** — all errors extend `TemplateError` from `infrastructure.core.exceptions`.
- **Optional dependencies** — guard with `try/except ImportError`; document in pyproject.toml `[project.optional-dependencies]`.
- **Run commands** — `uv run` (never `python` directly).

## Running tests and checks

```bash
# Infrastructure tests with coverage
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-fail-under=60

# Type checking
uv run mypy infrastructure/

# Linting
uv run ruff check infrastructure/ --fix
uv run ruff format infrastructure/

# Security scan
uv run bandit -c bandit.yaml -r -ll infrastructure/

# Repository health (all gates)
uv run python -m infrastructure.core.health

# Doctor (diagnose local checkout)
uv run python -m infrastructure.doctor
```

## Adding a new infrastructure module

1. Create `infrastructure/<name>/` with `__init__.py`, `AGENTS.md`, `README.md`, `SKILL.md`.
2. Implement business logic with ≥ 60% test coverage in `tests/infra_tests/<name>/`.
3. Declare an explicit `__all__` in `__init__.py` (required by `infrastructure.skills check --all-exports`).
4. Add an entry to the SKILL.md table in `infrastructure/README.md`.
5. Regenerate the skill manifest: `uv run python -m infrastructure.skills write`.
