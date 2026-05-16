# tests/infra_tests/ - Infrastructure Module Tests

Infrastructure tests cover the reusable modules under `infrastructure/`. They use real files, real subprocesses, and real services when a test explicitly requires one. **No mocks** (`MagicMock`, `mocker.patch`, `unittest.mock`) are allowed anywhere.

## Coverage

```bash
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-report=html --cov-fail-under=60
uv run pytest tests/infra_tests/ -m "not requires_ollama"
```

Floor: **60%** (currently ~83%). Coverage is measured over `infrastructure/` only.

## Directory -> Module Mapping

| Directory | Focus |
|-----------|-------|
| `bench/` | Opt-in `pytest-benchmark` suites, skipped by default |
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

Several directories contain files with `_coverage`, `_full`, `_expanded_coverage`, or `_additional` suffixes. These are **complementary test suites** that fill coverage gaps in the base file — they are not duplicates. All are collected and run by pytest.

| Suffix pattern | Meaning |
|----------------|---------|
| `test_foo.py` | Core behavior tests |
| `test_foo_coverage.py` | Additional test cases that push coverage higher |
| `test_foo_full.py` | Comprehensive end-to-end scenarios |
| `test_foo_expanded_coverage.py` | Edge-case and branch coverage additions |

Duplicate class names across these files are intentional — pytest collects each class independently. Do not merge them without verifying coverage does not drop.

## Practices

- Keep tests behavior-focused.
- Use `pytest.mark.requires_*` for optional external services (Ollama, LaTeX, etc.).
- Prefer explicit file and subprocess setup over mocks.
- Add `_coverage` variants when adding branch coverage for existing modules rather than expanding the base test file beyond ~400 lines.

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../README.md`](../README.md)
