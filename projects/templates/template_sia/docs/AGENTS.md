# `template_sia/docs/` — Agent Guide

## Purpose

Central documentation for the SIA harness exemplar: Meta → Target → Feedback loops,
public/private task splits, fixture replay (default CI), and opt-in live mode.

Agents must read [`agent_instructions.md`](agent_instructions.md) before editing
`src/`, `tasks/`, `scripts/`, or `tests/`.

## File inventory

| File | Role |
| --- | --- |
| [`README.md`](README.md) | Hub navigation and Mermaid map |
| [`AGENTS.md`](AGENTS.md) | This file |
| [`agent_instructions.md`](agent_instructions.md) | Seven hard rules + verification checklist |
| [`architecture.md`](architecture.md) | Layer boundaries and artifact tree |
| [`testing_philosophy.md`](testing_philosophy.md) | Fixture replay, coverage, no mocks |
| [`rendering_pipeline.md`](rendering_pipeline.md) | Stage 02 → variables → Stage 05 |
| [`style_guide.md`](style_guide.md) | Python conventions under `src/` |
| [`syntax_guide.md`](syntax_guide.md) | Manuscript `{{SIA_*}}` tokens |
| [`quickstart.md`](quickstart.md) | Minimal command sequence |
| [`output_conventions.md`](output_conventions.md) | `output/runs/` layout |
| [`troubleshooting.md`](troubleshooting.md) | Failure diagnostics |
| [`faq.md`](faq.md) | Scope and comparisons |
| [`forking_guide.md`](forking_guide.md) | Copy-and-adapt workflow |

## Reading order

1. [`agent_instructions.md`](agent_instructions.md)
2. [`architecture.md`](architecture.md)
3. [`testing_philosophy.md`](testing_philosophy.md)
4. [`syntax_guide.md`](syntax_guide.md) when touching manuscript or tasks
5. [`rendering_pipeline.md`](rendering_pipeline.md) before PDF work

## Verification commands

```bash
uv run python scripts/01_run_tests.py --project templates/template_sia --project-only
uv run python scripts/execute_pipeline.py --project templates/template_sia --core-only --skip-infra
grep -r "unittest.mock\|MagicMock\|@patch" projects/templates/template_sia/tests/ || echo "Clean"
```

## See also

- [`../AGENTS.md`](../AGENTS.md)
- [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md)
- [`../../../../infrastructure/sia/SKILL.md`](../../../../infrastructure/sia/SKILL.md)
