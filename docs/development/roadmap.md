# 🗺️ Development Roadmap

This roadmap documents the evolution of the Research Project Template infrastructure.
For architecture details see [`architecture.md`](../core/architecture.md) and [`workflow.md`](../core/workflow.md).

## ✅ Completed Releases

### v2.0.0 — Foundation (2025)

Two-layer architecture, thin orchestrator pattern, 8-stage pipeline, multi-project support.

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

### v2.9.0 — Documentation Parity (current)

`python3` → `uv run python` across docs, auto-generated API reference, roadmap refresh.

---

## 🔲 Planned

### v2.10.0 — Code Project Exemplar

Make `projects/code_project/` fully compliant: zero ruff errors, no mock patterns, demonstrate all infrastructure tooling (`ProjectLogger`, `validate_interpreter()`, `ResolvedTestingConfig`, `load_config()`).

### v3.0.0 — Next Generation (vision)

- **Incremental pipeline**: Skip unchanged stages via content hashing
- **Parallel project execution**: Multi-process orchestration
- **Plugin architecture**: User-defined pipeline stages
- **Remote LLM providers**: OpenAI/Anthropic alongside local Ollama
- **Web dashboard**: Real-time pipeline monitoring and reporting

---

## 📊 Quality Metrics (v2.9.0)

| Metric | Value |
|--------|-------|
| Ruff lint errors | **0** |
| mypy errors | **0** (26 files) |
| Test suite | **1201 passed**, 0 failures |
| Test failures (pre-existing) | **0** |
| Core modules | 26 |
| Error constants | 22 typed `InfraError` |

---

*Last updated: 2026-02-21*
