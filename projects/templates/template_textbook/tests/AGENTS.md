# `tests/` — agent notes

Tests cover the engine in [`../src/`](../src/). Two hard requirements:

1. **No mocks.** Never use `MagicMock`, `mocker.patch`, `unittest.mock`, or any
   mocking framework. Use real temp files (`tmp_path`), real numeric inputs, and
   subprocess for any CLI. HTTP (if ever needed) uses `pytest-httpserver`.
2. **90% project coverage minimum.** Adding logic to `src/` requires a real test
   here. Verify before claiming done:

   ```bash
   uv run --extra dev python -m pytest tests --cov=src --cov-report=term-missing
   ```

## Where to add a test

| If you changed... | Add/extend |
| --- | --- |
| `textbook.config` | `test_config.py` |
| `textbook.toc` | `test_toc.py` |
| `textbook.content` (scaffold/validate) | `test_content.py` |
| `textbook.models` (formulas) | `test_models.py` |
| `visualization/` | `test_visualization.py` |
| `mermaid/` | `test_mermaid.py` |
| `textbook_paths` / `textbook_io` | `test_paths_io.py` |
| structural/whole-book contract | `test_manuscript_integrity.py` |

## Determinism

Fixed RNG seeds, headless matplotlib (`MPLBACKEND=Agg`), no wall-clock or
environment-dependent assertions. Figure and diagram outputs must be byte-stable
so they can be diffed.

## Gates

- `test_manuscript_integrity.py` — in-suite gate; fails on a missing or
  contract-violating chapter/lab/question. Do not weaken its assertions.
- `scripts/audit_textbook_quality.py` — the CLI counterpart; same contract,
  exits non-zero on failure, prints a stub/word-count progress table.

Verify the suite actually *collected and ran* tests (not just exited 0) before
reporting green.
