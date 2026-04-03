# Changelog

All notable changes to the Research Project Template are documented here.

## [0.6.0] — 2026-03-10

### 🧹 Code Health: Desloppify Campaign (161 commits)

The largest code-quality improvement cycle since the template's inception. Every infrastructure
package and project module was subjected to systematic blind review and remediation across
26 review rounds, eliminating all AI-generated debt, convention outliers, and structural issues.

### Fixes

- **Import hygiene**: Removed unused imports across 8+ files; separated `TYPE_CHECKING` guarded imports from runtime imports; eliminated `sys.path` mutations from CLI modules
- **Exception handling**: Narrowed broad `except Exception` / bare `except` clauses throughout `integrity.py`, `logging_utils`, `config_loader`, and `llm` modules; fixed silent `JSONDecodeError` swallowing; restored exception context with `raise ... from exc`
- **Dead code removal**: Deleted orphaned `coverage_reporter.py` (zero importers); removed stub/passthrough wrapper methods across 10+ modules; eliminated dead HTML-entities dict from `InputSanitizer`
- **Type annotations**: Modernised legacy `typing` imports (`List[x]` → `list[x]`, `Optional[x]` → `x | None`) across 30+ modules; added `TypedDict` returns for integrity results; annotated CLI re-exports
- **API surface**: Consolidated `OllamaClientConfig` env-read wrappers (ABS-001); merged duplicate `PerformanceMetrics` naming conflict; removed `ProjectLogger` pure-forwarder abstraction; eliminated `calculate_file_hash` re-export from publishing boundary
- **Bug fixes**: Fixed inverted `scan_errors` bool in doc scanner; fixed stall-detection dead branch in pipeline reporter; fixed `config_files` path bug in `config_cli`; fixed `clean_output_directory` return type; fixed broken accessor imports after `core.py` hub elimination
- **Structural**: Eliminated `infrastructure/core/core.py` hub (delegated `validate_markdown_cli` to canonical location); extracted `_build_stage_list` to remove stage-list duplication; moved `MultiProjectResult` to `TYPE_CHECKING` to break `reporting→core` circular dep
- **Logging**: Removed nosy debug logs from LLM and environment modules; downgraded verbose entry logs; added `get_logger` to logic modules lacking structured logging
- **docstrings**: Stripped AI-generated boilerplate docstring bloat from 40+ functions; removed restating comments; cleaned banner comments
- **Tests**: Fixed test name collisions; added deterministic tests for `validate_review_quality` and exception types; added integration tests to `testpaths`; removed orphan test files
- **Dependencies**: Removed `scipy` from infrastructure env check; resolved stale findings in `psutil` guards; moved `matplotlib` to optional dep group

### Quality Gates (v0.6.0)

| Gate | Status |
| ---- | ------ |
| Desloppify blind reviews | **26 rounds completed** |
| Commits | **161** |
| Files changed | **948** |
| `ruff check` | ✅ Enforced |
| `mypy --strict` | ✅ 0 errors |
| `bandit -ll` | ✅ 0 MEDIUM+ findings |
| `pytest` | ✅ All pass |

---

## [3.0.0] — 2026-02-22

### 🎉 Production/Stable Release

Promoted from **Beta** to **Production/Stable** after completing comprehensive
quality gates across all 8 infrastructure packages (126 source files).

### Added (v3.0.0)

- **v2.12.0 — Ruff Format Enforcement**: Auto-formatted 280 files; `ruff format --check` blocking CI gate
- **v2.13.0 — mypy Strict Enforcement**: 140→0 errors in `validation/` (22 files) + `rendering/` (12 files); `disallow_untyped_defs = true` overrides
- **v2.14.0 — Security Hardening**: 7→0 MEDIUM Bandit findings (CWE-400, CWE-502, CWE-377); `pip-audit` blocking CI gate; Bandit `-ll` threshold
- **v2.15.0 — CI & Container Modernization**: Dockerfile `python:3.12` + `uv`; mypy pre-commit hook; docker-compose healthchecks
- **v2.16.0 — E501 Line Length Enforcement**: E501 removed from ruff ignore list; 342 code-line + 36 docstring per-file-ignores
- **v3.0.0 — Major Version Bump**: mypy strict for all 8 infrastructure packages (126 files, 0 errors); version 3.0.0; Production/Stable classifier

### Changed (v3.0.0)

- `pyproject.toml` version: `2.0.0` → `3.0.0`
- Classifier: `Development Status :: 4 - Beta` → `Development Status :: 5 - Production/Stable`
- Dockerfile: `python:3.11-slim` + `pip` → `python:3.12-slim` + `uv`
- docker-compose.yml: Removed deprecated `version` key; added Ollama healthcheck
- `.pre-commit-config.yaml`: Added mypy hook; ruff `v0.8.4` → `v0.9.7`; pre-commit-hooks `v4.6.0` → `v5.0.0`
- `ci.yml`: `pip-audit` now blocking; Bandit scans `infrastructure/ + scripts/ + projects/` at MEDIUM+

### Quality Gates (v3.0.0, all enforced in CI)

| Gate | Status |
| ---- | ------ |
| `ruff check` | Enforced (E501 included) |
| `ruff format --check` | Enforced |
| `mypy --strict` (validation, rendering) | Enforced |
| `mypy` (all 8 packages) | 0 errors |
| `bandit -ll` | 0 MEDIUM+ findings |
| `pip-audit` | Blocking gate |
| `pytest` (2,544 infra + 469 project) | All pass |

## [2.0.0] — 2026-02-18

### Added (v2.0.0)

- Two-Layer Architecture (Infrastructure + Projects)
- Build pipeline with thin orchestrator pattern
- Program-aware project discovery
- Executive reporting dashboard
- Standalone Project Paradigm with Graduation Pattern
