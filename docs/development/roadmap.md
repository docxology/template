# 🗺️ Development Roadmap

This roadmap documents the evolution of the Research Project Template infrastructure.
For architecture details see [`architecture.md`](../core/architecture.md) and [`workflow.md`](../core/workflow.md).

## ✅ Completed Releases

### v2.0.0 — Foundation (2025)

Two-layer architecture, thin orchestrator pattern, 10-stage DAG pipeline, multi-project support.

### v3.0.0 — Production/Stable (2026-02-22)

mypy strict for all 8 infrastructure packages (126 files, 0 errors); Ruff format enforcement; Security hardening (Bandit + pip-audit CI gates); Dockerfile modernisation to `python:3.12` + `uv`.

### v2.1.0 — Unified Intelligent Logging

`ProjectLogger` with structured log format, `log_operation()` context manager, `format_duration()`.

### v2.1.1 — CI Zero-Mock Gate

`verify_no_mocks.py` CI gate, eliminated all mock/fake patterns from test suite.

### v2.2.0 — Orchestration Hermeticity

Script discovery, `get_subprocess_env()`, hermetic environment for subprocess calls.

### v2.3.0 — Type Safety

TypedDicts for config structures, `ResolvedTestingConfig`, `ProjectInfo` dataclass.

### v2.4.0 — Monkeypatch Elimination

Replaced `monkeypatch` with real `tmp_path` fixtures and environment isolation.

### v2.5.0 — Structured Log Assertions

`caplog`-based test assertions replacing stdout capture, `log_parser.py` utilities.

### v2.6.0 — Ruff Lint Remediation

**710 → 0 ruff errors** across `infrastructure/`, `scripts/`, `tests/`.

### v2.7.0 — Type Narrowing & mypy Baseline

**mypy: 100 → 0 errors** across 26 `infrastructure/core/` modules. 13 files type-narrowed.

### v2.8.0 — Error Reporting & Resilience

Typed `InfraError` constants in `errors.py`, standardized `❌ [CODE] message — suggestion` format, fixed flaky `test_print_summary`.

### v2.9.0 — Documentation Parity

`python3` → `uv run python` across docs, auto-generated API reference, roadmap refresh.

### v0.6.0 — Desloppify: Code Health Campaign (2026-03-10) ← **current**

161-commit systematic blind-review campaign across all 8 infrastructure packages:

- Import hygiene (unused imports, `sys.path` mutations, `TYPE_CHECKING` guards)
- Exception handling (narrow types, restore context, fix silent swallowing)
- Dead code removal (`coverage_reporter.py`, stub wrappers, passthrough methods)
- Type annotations modernised (legacy `typing` → built-in generics)
- API surface consolidation (`OllamaClientConfig`, `PerformanceMetrics`, `ProjectLogger`)
- Bug fixes (inverted bool, stall detection, path bugs, broken imports)
- Structural: eliminated `core.py` hub, extracted `_build_stage_list`, broke circular dep
- Logging noise reduction; docstring bloat; test name collisions resolved

---

## 🔲 Planned

### v0.7.0 — Exemplar Hardening

Make `projects/code_project/` fully compliant post-desloppify: zero ruff errors, no mock patterns, demonstrate all infrastructure tooling (`ProjectLogger`, `validate_interpreter()`, `ResolvedTestingConfig`, `load_config()`).

### v1.0.0 — Next Generation (vision)

- **Incremental pipeline**: Skip unchanged stages via content hashing
- **Parallel project execution**: Multi-process orchestration
- **Plugin architecture**: User-defined pipeline stages
- **Remote LLM providers**: OpenAI/Anthropic alongside local Ollama
- **Web dashboard**: Real-time pipeline monitoring and reporting

---

## 📊 Quality Metrics (v0.6.0)

| Metric | Value |
| ------ | ----- |
| Desloppify review rounds | **26** |
| Commits (desloppify campaign) | **161** |
| Files changed | **948** |
| Ruff lint errors | **0** |
| mypy errors | **0** (all 8 packages) |
| Test suite | All pass, 0 failures |
| Bandit MEDIUM+ findings | **0** |
| Core infrastructure packages | **8** |
| Error constants | 22 typed `InfraError` |

---

*Last updated: 2026-03-10*


## See Also

- **[Contributing](../development/contributing.md)** — How to contribute to the template
