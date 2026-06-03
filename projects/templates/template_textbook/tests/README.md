# `tests/` — the engine test suite

Tests for the textbook engine in [`../src/`](../src/). The suite enforces a
**90% project coverage minimum** (currently ~95% across 75 tests) and follows the
repository's **no-mocks policy** — every test uses real data, real files, and
real computation.

## Suite map

| File | Covers |
| --- | --- |
| `conftest.py` | Shared fixtures (e.g. `tmp_path`-based project trees). |
| `test_config.py` | `textbook.config` — `load_config`, `iter_chapters`, `validate_config`. |
| `test_toc.py` | `textbook.toc` — chapter numbering and part/chapter labels. |
| `test_content.py` | `textbook.content` — scaffolding (`scaffold_chapter`/`scaffold_lab`/`scaffold_question_bank`) and `validate_chapter` / `count_stub_markers` / `count_words`. |
| `test_models.py` | `textbook.models` — the worked formalisms (logistic growth, saturating response, decay, half-life, linear fit, descriptive statistics, unit-interval normalisation). |
| `test_visualization.py` | `visualization.plots` / `_scaffold` — deterministic figure generation. |
| `test_mermaid.py` | `mermaid.diagrams` / `renderer` — diagram generation and the `.mmd` fallback. |
| `test_paths_io.py` | `textbook_paths` / `textbook_io` — path resolution and atomic writes. |
| `test_manuscript_integrity.py` | Whole-book gate — every declared chapter/lab/question exists and satisfies the structural contract. |

## No-mocks policy

No `MagicMock`, `mocker.patch`, or `unittest.mock`. Use real temp files
(`tmp_path`), real numeric inputs, and subprocess where a CLI must be exercised.
Determinism is required — fixed seeds, no wall-clock dependence.

## Running

```bash
# full suite with coverage
uv run --extra dev python -m pytest tests --cov=src --cov-report=term-missing

# a single file or test
uv run --extra dev python -m pytest tests/test_models.py -v
uv run --extra dev python -m pytest tests/test_content.py::test_validate_chapter -v
```

## Integrity & audit gates

`test_manuscript_integrity.py` is the in-suite gate: it fails if a declared
chapter, lab, or question is missing or violates the `textbook.constants`
contract. The matching CLI gate is `scripts/audit_textbook_quality.py`, which
runs the same checks and prints a fill-progress table for use in CI or before
publication.
