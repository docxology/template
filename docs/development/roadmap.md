# Development Roadmap

This roadmap documents the evolution of the Research Project Template
infrastructure. Architecture details:
[`architecture.md`](../core/architecture.md) and
[`workflow.md`](../core/workflow.md).

**Last verified:** 2026-05-04 (re-baselined against live audit)

## Completed Releases

### v3.0.0 — Production / Stable (2026-02-22)

- mypy strict adopted as the baseline gate for `infrastructure/` (current
  state: see TO-DO M1 — a small residual is open against re-export
  attribute exports)
- Ruff format enforcement
- Security hardening: Bandit MEDIUM+ gate in CI, pip-audit job present
  (still informational; see TO-DO M2)
- Dockerfile modernised to `python:3.12` + `uv`

### v2.x — Foundation Series (2025–2026)

| Release | Theme |
| ------- | ----- |
| `v2.0.0` | Two-layer architecture, thin orchestrator pattern, 10-stage DAG, multi-project support |
| `v2.1.0` | Unified intelligent logging — `ProjectLogger`, structured format, `log_operation()`, `format_duration()` |
| `v2.1.1` | CI Zero-Mock gate (`verify_no_mocks.py`); mock/fake patterns eliminated from suite |
| `v2.2.0` | Orchestration hermeticity — script discovery, `get_subprocess_env()`, hermetic subprocess env |
| `v2.3.0` | Type safety — TypedDicts for config, `ResolvedTestingConfig`, `ProjectInfo` dataclass |
| `v2.4.0` | Monkeypatch elimination — real `tmp_path` + env-isolation fixtures |
| `v2.5.0` | Structured log assertions — `caplog`-based, `log_parser.py` |
| `v2.6.0` | Ruff lint remediation: 710 → 0 errors across `infrastructure/`, `scripts/`, `tests/` |
| `v2.7.0` | Type narrowing & mypy baseline: 100 → 0 errors across `core/` |
| `v2.8.0` | Error reporting & resilience — typed `InfraError` constants, standardized error format |
| `v2.9.0` | Documentation parity — `python3` → `uv run python`, auto-generated API reference |

### v0.6.0 — Desloppify Code-Health Campaign (2026-03-10)

161-commit systematic blind-review campaign across all infrastructure
packages:

- Import hygiene (unused imports, `sys.path` mutations, `TYPE_CHECKING` guards)
- Exception narrowing (specific types, context restoration, no silent swallowing)
- Dead-code removal (`coverage_reporter.py`, stub wrappers, passthrough methods)
- Type annotations modernised (legacy `typing` → built-in generics)
- API surface consolidation (`OllamaClientConfig`, `PerformanceMetrics`, `ProjectLogger`)
- Bug fixes (inverted bool, stall detection, path bugs, broken imports)
- Structural: eliminated `core.py` hub, extracted `_build_stage_list`, broke circular dep
- Logging noise reduction; docstring bloat; test name collisions resolved

---

## Planned

### v0.7.0 — Exemplar Hardening

Make `projects/template_code_project/` fully compliant post-desloppify:
zero ruff errors, no mock patterns, demonstrate all infrastructure tooling
(`ProjectLogger`, `validate_interpreter()`, `ResolvedTestingConfig`,
`load_config()`).

### v1.0.0 — Next Generation (vision)

- **Incremental pipeline**: skip unchanged stages via content hashing
- **Parallel project execution**: multi-process orchestration
- **Plugin architecture**: user-defined pipeline stages
- **Remote LLM providers**: OpenAI/Anthropic alongside local Ollama
- **Web dashboard**: real-time pipeline monitoring and reporting

---

## Next Up

The active backlog is [`TO-DO.md`](../../TO-DO.md). It is regenerated
against a live audit; the roadmap intentionally does not duplicate the
items there. The current top items (verify against `TO-DO.md` for the
authoritative form):

- **M1** — Close residual mypy strict errors (re-export `__all__` audit)
- **M2** — Make CI pip-audit a blocking gate (remove `continue-on-error`)
- **M3** — Resolve the 3 remaining MEDIUM Bandit findings (`B314` ×2, `B615` ×1)
- **M4** — Triage / suppress the LOW Bandit pile
- **M7** — Roadmap freshness sweep (this document is its output)
- **MED3** — Per-project test-runner factor (lifts the open-coded loop in
  `ci.yml` into infrastructure)
- **MED4** — Documentation linter as a CI job (Mermaid + cross-tree links
  + module-count consistency + ghost-project detection)

---

## Quality Metrics (live, 2026-05-04)

| Metric | Value | Source |
| ------ | ----- | ------ |
| `pyproject.toml` version | `3.0.0` | `pyproject.toml` |
| Ruff lint errors | **0** | `uv run ruff check infrastructure/` |
| mypy strict errors (`infrastructure/`) | **19** in 12 files (residual `__all__` re-exports — TO-DO M1) | `uv run mypy --strict infrastructure/` |
| Bandit MEDIUM+ findings | **3 MEDIUM** (`B314` ×2 in `search/`, `B615` ×1 in `scripts/fixtures/`) — TO-DO M3 | `uv run bandit -r -ll infrastructure/ scripts/` |
| Bandit LOW findings | 90 (allow-list / triage pending — TO-DO M4) | same |
| Test suite | **5246 passing**, 8 skipped | `pytest tests/infra_tests/` |
| Infrastructure coverage | **76.83 %** (gate ≥ 60 %) | `pytest --cov=infrastructure` |
| `infrastructure/` Python packages | 15 (+ 3 config dirs) | `infrastructure/` tree |
| pip-audit CI gate | informational (`continue-on-error: true`) — TO-DO M2 | `.github/workflows/ci.yml:405` |

Numbers above are re-measured each time this file is touched. Do not
copy them forward without re-running the source command.

---

## See Also

- **[Contributing](contributing.md)** — how to contribute to the template
- **[`../../TO-DO.md`](../../TO-DO.md)** — active backlog with acceptance
  criteria
- **[`../../CHANGELOG.md`](../../CHANGELOG.md)** — historical release notes
