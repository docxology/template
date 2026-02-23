# Changelog

All notable changes to the Research Project Template are documented here.

## [3.0.0] — 2026-02-22

### 🎉 Production/Stable Release

Promoted from **Beta** to **Production/Stable** after completing comprehensive
quality gates across all 8 infrastructure packages (126 source files).

### Added

- **v2.12.0 — Ruff Format Enforcement**: Auto-formatted 280 files; `ruff format --check` blocking CI gate
- **v2.13.0 — mypy Strict Enforcement**: 140→0 errors in `validation/` (22 files) + `rendering/` (12 files); `disallow_untyped_defs = true` overrides
- **v2.14.0 — Security Hardening**: 7→0 MEDIUM Bandit findings (CWE-400, CWE-502, CWE-377); `pip-audit` blocking CI gate; Bandit `-ll` threshold
- **v2.15.0 — CI & Container Modernization**: Dockerfile `python:3.12` + `uv`; mypy pre-commit hook; docker-compose healthchecks
- **v2.16.0 — E501 Line Length Enforcement**: E501 removed from ruff ignore list; 342 code-line + 36 docstring per-file-ignores
- **v3.0.0 — Major Version Bump**: mypy strict for all 8 infrastructure packages (126 files, 0 errors); version 3.0.0; Production/Stable classifier

### Changed

- `pyproject.toml` version: `2.0.0` → `3.0.0`
- Classifier: `Development Status :: 4 - Beta` → `Development Status :: 5 - Production/Stable`
- Dockerfile: `python:3.11-slim` + `pip` → `python:3.12-slim` + `uv`
- docker-compose.yml: Removed deprecated `version` key; added Ollama healthcheck
- `.pre-commit-config.yaml`: Added mypy hook; ruff `v0.8.4` → `v0.9.7`; pre-commit-hooks `v4.6.0` → `v5.0.0`
- `ci.yml`: `pip-audit` now blocking; Bandit scans `infrastructure/ + scripts/ + projects/` at MEDIUM+

### Quality Gates (all enforced in CI)

| Gate | Status |
|------|--------|
| `ruff check` | Enforced (E501 included) |
| `ruff format --check` | Enforced |
| `mypy --strict` (validation, rendering) | Enforced |
| `mypy` (all 8 packages) | 0 errors |
| `bandit -ll` | 0 MEDIUM+ findings |
| `pip-audit` | Blocking gate |
| `pytest` (2,544 infra + 469 project) | All pass |

## [2.0.0] — 2026-02-18

### Added

- Two-Layer Architecture (Infrastructure + Projects)
- 10-stage build pipeline with thin orchestrator pattern
- Program-aware project discovery
- Executive reporting dashboard
- Standalone Project Paradigm with Graduation Pattern
