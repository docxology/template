# Testing philosophy — template_sia

## Principles

- **Real artifacts:** Tests read and write JSON, CSV, and markdown under `tmp_path` or the exemplar tree — no mocked filesystem or LLM responses.
- **Fixture replay default:** `run_sia_loop_project(..., live=False)` is the primary integration path; it must stay deterministic and fast.
- **Live mode is opt-in:** `@pytest.mark.requires_ollama` tests exercise `--live-sia` when Ollama and `requests` are available; CI skips them via marker expression.
- **Coverage:** `src/` ≥ 90%. Measured counts live in [`docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md).

## Fixture / live-mode separation (the public-exemplar boundary)

The single switch between modes is the `live` flag resolved by
`src.loop.build_run_config(project_root, *, live)`:

- `live=False` (and the committed default `sia.live: false`) sets
  `fixtures_dir` to `src/fixtures/recorded_generations/` and replays recorded
  artifacts — **no agent is executed, no subprocess is spawned**.
- `live=True` sets `fixtures_dir=None` and executes the reference agent.

`test_fixture_live_separation.py` pins this boundary so a refactor cannot blur
it: replay points at the recorded fixtures, ignores the *content* of the
reference agent (it is never executed), and **fails closed** — raising
`ValidationError` rather than fabricating a pass — when the fixtures (or any one
generation's fixtures) are missing. This is what lets the public exemplar
demonstrate self-improvement mechanics without implying autonomous live-code
execution in CI.

## Test modules

| File | Focus |
| --- | --- |
| `test_loop.py` | Settings, fixture replay, script smoke |
| `test_fixture_live_separation.py` | Fixture-vs-live boundary + fail-closed guardrails |
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
