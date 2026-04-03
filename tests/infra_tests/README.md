# tests/infra_tests/ - Infrastructure Module Tests

Infrastructure tests cover the reusable modules under `infrastructure/`. They use real files, real subprocesses, and real services when a test explicitly requires one.

## Coverage

```bash
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-report=html --cov-fail-under=60
uv run pytest tests/infra_tests/ -m "not requires_ollama"
```

## Current Areas

- `core/` - configuration, logging, files, runtime, pipeline helpers, security, telemetry, cleanup
- `documentation/` - figures, API docs, markdown helpers
- `llm/` - Ollama integration, prompts, context, streaming, sanitization, reviews
- `publishing/` - metadata, readiness, platform integration, citations
- `rendering/` - PDF, LaTeX, web, slides, combined rendering
- `reporting/` - report builders, parsers, dashboards, summaries, log analysis
- `scientific/` - benchmarking, stability, templates, validation
- `skills/` - skill discovery and manifest validation
- `steganography/` - watermarking, metadata, encryption, barcode helpers
- `validation/` - docs scanning, links, repo scanning, integrity, CLI checks

## Practices

- Keep tests behavior-focused.
- Use `pytest.mark.requires_*` for optional external services.
- Prefer explicit file and subprocess setup over mocks.
- Keep coverage-focused tests alongside behavior tests when they guard a real regression.

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../README.md`](../README.md)
