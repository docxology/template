# tests/infra_tests/prose/

## Overview

Behaviour tests for editorial prose tooling: pure analysis functions (`analysis/metrics.py`, `structure.py`, `quality.py`), `markdown.py` stripping, `report.py` aggregation, and `cli.py` subcommands (subprocess-invoked).

| File | Scope |
| --- | --- |
| `test_metrics.py` | Flesch/FKGL/Fog syllable and sentence splits |
| `test_structure.py` | Headings and outline rendering |
| `test_quality.py` | Passive, hedges, long sentences |
| `test_markdown_helpers.py` | `normalise_for_prose` and fence stripping |
| `test_report.py` | `ManuscriptReport` / directory aggregation |
| `test_cli.py` | CLI exit codes and output paths |

## Run

```bash
uv run pytest tests/infra_tests/prose/ -v
```

## See also

- [`README.md`](README.md)
- [`../../../infrastructure/prose/AGENTS.md`](../../../infrastructure/prose/AGENTS.md)
