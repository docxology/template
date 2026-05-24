# tests/infra_tests/ - Infrastructure Module Tests

Infrastructure tests cover the reusable modules under `infrastructure/`. They use real files, real subprocesses, and real services when a test explicitly requires one. **No mocks** (`MagicMock`, `mocker.patch`, `unittest.mock`) are allowed anywhere.

## Coverage

```bash
uv run python scripts/01_run_tests.py --infra-only --infra-scope pipeline-smoke
uv run python scripts/01_run_tests.py --infra-only --infra-scope full
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-report=html --cov-fail-under=60
uv run pytest tests/infra_tests/ -m "not requires_ollama"
```

Floor: **60%** for the full scope. `pipeline-smoke` is intentionally coverage-free
and is used inside project pipelines as a fast real contract check. Coverage is
measured over `infrastructure/` only.

## Directory -> Module Mapping

| Directory | Focus |
|-----------|-------|
| `bench/` | Opt-in `pytest-benchmark` suites, skipped by default |
| `config/` | `infrastructure/config/` — secure_config schema expectations |
| `core/` | `infrastructure/core/` — logging, files, runtime, pipeline, telemetry, security |
| `core/config/` | Config schema extensions, strict loading, JSON schema |
| `core/pipeline/` | Lower-level pipeline helpers such as multi-project parallelism |
| `core/telemetry/` | Telemetry retention and report rotation |
| `documentation/` | `infrastructure/documentation/` — figures, API docs |
| `doctor/` | `infrastructure/doctor/` — diagnostics, safe fixes, undo, scorecards |
| `git_hook_smoke/` | Fast pre-push smoke coverage |
| `orchestration/` | `infrastructure/orchestration/` — CLI, menu, PipelineRunner, logs, secure wrapper |
| `project/` | `infrastructure/project/` — discovery, layout validation |
| `prose/` | `infrastructure/prose/` — readability, outline, editorial quality, reports |
| `reference/` | `infrastructure/reference/` — BibTeX parse/write, models, CLI |
| `search/` | `infrastructure/search/` — literature client, backends, cache, CLI |
| `llm/` | `infrastructure/llm/` — Ollama client, prompts, streaming, reviews, translations |
| `publishing/` | `infrastructure/publishing/` — metadata, citations, Zenodo, arXiv |
| `rendering/` | `infrastructure/rendering/` — PDF, LaTeX, web, slides |
| `reporting/` | `infrastructure/reporting/` — pipeline reports, dashboards, executive summaries |
| `scientific/` | `infrastructure/scientific/` — benchmarking, stability |
| `skills/` | `infrastructure/skills/` — SKILL.md discovery, manifest |
| `steganography/` | `infrastructure/steganography/` — watermarking, encryption |
| `validation/` | `infrastructure/validation/` — docs scanning, links, repo scanning, integrity |
| `validation/docs/` | Documentation linter regressions: Mermaid, links, consistency, doc pairs |

Top-level files outside subfolders include `test_docs_discovery_consistency.py`, `test_documentation_index_invariants.py` (documentation invariants), `test_cogant_coverage_table_check.py` (parses the COGANT staging `check_coverage_table.py` helper for manuscript Table 9 vs `coverage report`), and `test_cogant_manuscript_crossrefs_audit.py` (loads `audit_manuscript_crossrefs.py` against the staging manuscript tree).

## File Naming Convention

Prefer **one behavioral test module per production module**. Use
``@pytest.mark.parametrize`` for branch/error paths instead of spawning
``*_expanded_coverage*`` or ``*_full_coverage*`` companion files.

Legacy ``*_coverage*`` suffix files were removed in the 2026-05-24 wave-3
consolidation. Do not add parallel supplement tiers for new work.

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../README.md`](../README.md)
