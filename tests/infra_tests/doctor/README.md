# doctor/ - Quick Reference

Tests for `infrastructure.doctor`, the repository health and safe-fix module.

## Run

```bash
uv run pytest tests/infra_tests/doctor/ -q
```

## Contents

| File | Purpose |
| --- | --- |
| `test_cli.py` | CLI smoke and JSON/text output |
| `test_detectors.py` | Individual detector behavior |
| `test_fix_pipeline.py` | Detect -> plan -> apply -> undo flow |
| `test_safety.py` | Mutation chokepoint and path safety |
| `test_scorecard_and_reporter.py` | Score math and renderers |

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../README.md`](../README.md)
