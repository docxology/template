# tests/infra_tests/autoresearch/

Tests for `infrastructure.autoresearch`: deterministic AutoResearchClaw-inspired planning and readiness validation with real temporary project scaffolds.

## Files

- `test_autoresearch.py` — config defaults, pipeline overlays, validation diagnostics, report writers, and CLI validate behavior.

## Standards

- Keep fixtures file-backed and deterministic.
- Do not add network, LLM, or autonomous execution dependencies.
- Use `tmp_path` scaffolds for project layouts and subprocess calls for CLI behavior.

## Running

```bash
uv run pytest tests/infra_tests/autoresearch/ -v
uv run pytest tests/infra_tests/autoresearch/ --cov=infrastructure.autoresearch --cov-report=term-missing
```

## See Also

- [`../../../infrastructure/autoresearch/AGENTS.md`](../../../infrastructure/autoresearch/AGENTS.md)
