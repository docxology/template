# tests/infra_tests/autoresearch/

Tests for `infrastructure.autoresearch`: deterministic AutoResearchClaw-inspired planning and readiness validation with real temporary project scaffolds.

## Files

- `test_autoresearch_plan_validation.py` — pipeline overlays and phased validation diagnostics.
- `test_autoresearch_config_models.py` — config defaults, method-contract fields, domain models, and report writers.
- `test_autoresearch_cli_overlay.py` — CLI validate/plan subprocess behavior and overlay entrypoints.
- `test_autoresearch_cli.py` — CLI commands, argument parsing, and exit codes.
- `test_orchestrator.py` — multi-phase AutoResearch loop orchestrator and event logging.
- `test_metrics.py` — metric parsing and noise statistics.
- `test_cli_schema.py` — CLI parameter schema generation.

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
