# Development Roadmap

This roadmap documents the evolution of the Research Project Template
infrastructure. Architecture details:
[`architecture.md`](../core/architecture.md) and
[`workflow.md`](../core/workflow.md).

**Last verified:** 2026-05-05 (metrics defer to [`TO-DO.md`](../../TO-DO.md) live snapshot unless this file is re-measured)

## Completed Releases

### v3.0.0 — Production / Stable (2026-02-22)

- mypy strict adopted as the baseline gate for `infrastructure/` (live
  counts in [`TO-DO.md`](../../TO-DO.md))
- Ruff format enforcement
- Security hardening: Bandit MEDIUM+ gate in CI; pip-audit blocking since **v0.7.2**
  (ignore list + retries — see [`CHANGELOG.md`](../../CHANGELOG.md))
- Dockerfile modernised to `python:3.12` + `uv`

### v2.x — Foundation Series (2025–2026)

| Release | Theme |
| ------- | ----- |
| `v2.0.0` | Two-layer architecture, thin orchestrator pattern, declared DAG pipeline, multi-project support |
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

- **`TO-DO.md`** — authoritative backlog and live audit snapshot (metrics and open items — verify there before copying numbers here).
- **M7** — Roadmap hygiene: link to sources instead of duplicating drift-prone counts.

Shipped elsewhere (do not re-track here): **M2** pip-audit blocking CI (**v0.7.2**), **M4** Bandit LOW triage via `bandit.yaml`, **docs-lint** CI job (**MED4** in [`CHANGELOG.md`](../../CHANGELOG.md)), per-project test runner (**MED3** — `infrastructure.core.test_runner`). **DOC-MERMAID-1** in [`TO-DO.md`](../../TO-DO.md) is separate backlog for legacy Mermaid `noqa` cleanup — not the MED4 docs-lint ship label.

---

## Quality Metrics

Authoritative counts and gate outputs live in the **Live state snapshot**
table in [`TO-DO.md`](../../TO-DO.md) (re-baseline there after substantive
changes). This roadmap avoids duplicating numbers that drift between audits.

| Topic | Where to verify |
| ----- | ---------------- |
| mypy / ruff / Bandit / pip-audit / health | [`TO-DO.md`](../../TO-DO.md) |
| CI wiring | [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml), [`.github/AGENTS.md`](../../.github/AGENTS.md) |
| Coverage gaps | [`coverage-gaps.md`](coverage-gaps.md) |

---

## See Also

- **[Contributing](contributing.md)** — how to contribute to the template
- **[`../../TO-DO.md`](../../TO-DO.md)** — active backlog with acceptance
  criteria
- **[`../../CHANGELOG.md`](../../CHANGELOG.md)** — historical release notes
