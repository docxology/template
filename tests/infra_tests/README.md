# tests/infra_tests/ - Infrastructure Module Tests

Infrastructure tests cover the reusable modules under `infrastructure/`. They use real files, real subprocesses, and real services when a test explicitly requires one. **No mocks** (`MagicMock`, `mocker.patch`, `unittest.mock`) are allowed anywhere.

## Coverage

```bash
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-report=html --cov-fail-under=60
uv run pytest tests/infra_tests/ -m "not requires_ollama"
```

Floor: **60%** (currently ~83%). Coverage is measured over `infrastructure/` only.

## Directory → Module Mapping

| Directory | Infrastructure module | Approx. test files |
|-----------|----------------------|-------------------|
| `core/` | `infrastructure/core/` — logging, files, runtime, pipeline, telemetry, security | ~66 |
| `documentation/` | `infrastructure/documentation/` — figures, API docs | ~7 |
| `llm/` | `infrastructure/llm/` — Ollama client, prompts, streaming, reviews, translations | ~66 |
| `publishing/` | `infrastructure/publishing/` — metadata, citations, Zenodo, arXiv | ~21 |
| `rendering/` | `infrastructure/rendering/` — PDF, LaTeX, web, slides | ~49 |
| `reporting/` | `infrastructure/reporting/` — pipeline reports, dashboards, executive summaries | ~53 |
| `scientific/` | `infrastructure/scientific/` — benchmarking, stability | ~8 |
| `skills/` | `infrastructure/skills/` — SKILL.md discovery, manifest | ~5 |
| `steganography/` | `infrastructure/steganography/` — watermarking, encryption | ~14 |
| `validation/` | `infrastructure/validation/` — docs scanning, links, repo scanning, integrity | ~56 |

Top-level files outside subfolders include `test_docs_discovery_consistency.py`, `test_documentation_index_invariants.py` (documentation invariants), and `test_cogant_coverage_table_check.py` (parses the COGANT staging `check_coverage_table.py` helper for manuscript Table 9 vs `coverage report`).

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
