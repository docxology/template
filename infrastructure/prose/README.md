# Prose Module

Prose analysis utilities for research manuscripts and prose-focused
projects. Sister module to `infrastructure/reference/` (citations) and
`infrastructure/search/` (literature discovery).

## Submodules

| Submodule | Purpose |
|---|---|
| [`analysis`](analysis/) | Pure functions: `compute_metrics`, `analyze_structure`, `analyze_quality`. |

Top-level files:

| File | Role |
|---|---|
| `markdown.py` | Strip front-matter / fences / inline code / links; read a manuscript directory. |
| `report.py` | `ManuscriptReport`, `analyze_manuscript`, `write_report`. |
| `cli.py` | `metrics` / `outline` / `quality` / `report` subcommands. |

## Quick start

```python
from infrastructure.prose import analyze_manuscript, write_report

report = analyze_manuscript("projects/my_project/manuscript")
write_report(report, "output/prose_report.json")

print(report.total_words)
print(report.avg_flesch_kincaid_grade)
print(report.citation_keys)
```

## CLI

```bash
uv run python -m infrastructure.prose.cli report \
    projects/template_prose_project/manuscript \
    --output output/prose_report.json
```

## Testing

```bash
uv run pytest tests/infra_tests/prose/ -v
```

50+ tests, no mocks: real-text inputs, real `tmp_path` files, real
subprocess invocation of the CLI.

See [SKILL.md](SKILL.md) for the agent-oriented API and
[AGENTS.md](AGENTS.md) for module invariants and editing rules.
