# Testing philosophy — template_sia

## Principles

- **Real artifacts:** Tests read and write JSON, CSV, and markdown under `tmp_path` or the exemplar tree — no mocked filesystem or LLM responses.
- **Fixture replay default:** `run_sia_loop_project(..., live=False)` is the primary integration path; it must stay deterministic and fast.
- **Live mode is opt-in:** `@pytest.mark.requires_ollama` tests exercise `--live-sia` when Ollama and `requests` are available; CI skips them via marker expression.
- **Coverage:** `src/` ≥ 90%. Measured counts live in [`docs/_generated/canonical_facts.md`](../../../../docs/_generated/canonical_facts.md).

## Test modules

| File | Focus |
| --- | --- |
| `test_loop.py` | Settings, fixture replay, script smoke |
| `test_loop_live.py` | Single live generation (optional) |
| `test_reports.py` | Manuscript variables and resolved tree |
| `test_generation_records.py` | Run summary parsing |
| `test_reference_agent.py` | Task reference agent |
| `test_src_reference_agent.py` | `src/reference_agent.py` unit paths |

## Commands

```bash
# Default CI-equivalent (from repo root)
uv run python scripts/01_run_tests.py --project templates/template_sia --project-only

# From project directory
uv run --extra dev pytest tests -m "not requires_ollama" --cov=src --cov-fail-under=90
```

Infrastructure harness tests: `uv run pytest tests/infra_tests/sia/ -q`
