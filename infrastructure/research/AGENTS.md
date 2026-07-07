# Research Module — Agent Notes

## Purpose

`infrastructure/research` provides a programmatic definition of the
seven-stage research workflow and the agent-facing prompt text used to
operate research-mode and literature-review sub-agents. It is the entry
point for any AI agent doing scientific research within the template/
research infrastructure.

## Public API

```python
from infrastructure.research import ResearchWorkflow, ResearchStage

workflow = ResearchWorkflow()

# Markdown rendering of the full workflow (for agent context)
md = workflow.describe()

# Access individual stages (implemented stage names: scope, survey,
# hypothesise, experiment, validate, review, write — see Note below)
stage = workflow.stage("survey")
print(stage.description)
```

> **Note (doc/code drift, tracked for follow-up):** the table below and the
> rest of this file describe a richer OpenScience-ported 7-stage design
> (SCOPE/LITERATURE/REASON/DESIGN/COMPUTE/SYNTHESIZE/WRITE with per-stage
> sub-agent fan-out counts and template commands). The implemented
> `ResearchWorkflow`/`ResearchStage` in `workflow.py` is a simpler 7-stage
> descriptive model (`scope, survey, hypothesise, experiment, validate,
> review, write` — no `parallel_subagents` or `template_commands` fields).
> Treat the table and provenance-integration examples below as design intent,
> not a verified API surface, until reconciled.

## Workflow Stages

| # | Stage | Required | Sub-agent | Key outputs |
|---|-------|----------|-----------|-------------|
| 1 | **SCOPE** | ✓ | — | `scope.md` |
| 2 | **LITERATURE** | ✓ (skip only if asked) | `literature-review` (×5 parallel) | `literature-review.md` |
| 3 | **REASON** | ✓ (skip only if asked) | — | `reasoning.md` |
| 4 | **DESIGN** | ✓ (skip only if asked) | — | `design.md` |
| 5 | **COMPUTE** | ✓ | — | `results.md`, `output/data/*` |
| 6 | **SYNTHESIZE** | ✓ | — | `synthesis.md` |
| 7 | **WRITE** | optional | `write` | `manuscript/*` |

## Prompt Files

| File | Purpose |
|------|---------|
| `prompts/research_workflow.md` | Full research-mode system prompt — load as agent context for primary research agents. |
| `prompts/literature_review.md` | PRISMA-adapted sub-agent prompt — load as context when spawning `literature-review` sub-agents. |

## Key Infrastructure Dependencies

| Capability | Module | Command |
|-----------|--------|---------|
| Literature search | `infrastructure.search.literature` | `uv run python -m infrastructure.search.literature search --query '...'` |
| BibTeX export | `infrastructure.search.literature.cli` | `... to-bibtex '...' --output projects/{name}/manuscript/references.bib` |
| Web/semantic search | `infrastructure.search.exa` | `uv run python -m infrastructure.search.exa search '...'` |
| Deep research | `infrastructure.search.deep_research` | `uv run python -m infrastructure.search.deep_research submit ...` |
| Pipeline execution | `scripts/runner/execute_pipeline.py` | `uv run python scripts/runner/execute_pipeline.py --project {name}` |
| Provenance DAG | `infrastructure.provenance` | `uv run python -m infrastructure.provenance record run ...` |
| Output validation | `scripts/pipeline/stage_04_validate.py` | `uv run python scripts/pipeline/stage_04_validate.py --project {name}` |

## Boundaries

- This module is **read-only infrastructure** — it defines workflows, it does
  not execute them. Execution happens via `scripts/runner/execute_pipeline.py` and
  the numbered `scripts/NN_*.py` orchestrators.
- No autonomous self-approval loops. Every paid compute step requires explicit
  user approval (see "Cost Approval" in `prompts/research_workflow.md`).
- No network calls at import time. `infrastructure.search.*` is opt-in.
- Stage outputs go to `output/data/` and `output/reports/` under the project
  directory, not into `infrastructure/research/` itself.

## Adding a New Stage

1. Add a `ResearchStage(...)` entry to `ResearchWorkflow.STAGES` in
   `workflow.py` with the correct `order` value.
2. Update `prompts/research_workflow.md` with the corresponding stage
   section.
3. Update the stage table in this `AGENTS.md` and in `README.md`.

## See Also

- [`README.md`](README.md) — quick reference
- [`prompts/research_workflow.md`](prompts/research_workflow.md) — full research prompt
- [`prompts/literature_review.md`](prompts/literature_review.md) — PRISMA sub-agent prompt
- [`infrastructure/search/AGENTS.md`](../search/AGENTS.md) — literature search module
- [`infrastructure/autoresearch/AGENTS.md`](../autoresearch/AGENTS.md) — deterministic readiness checks
- [`scripts/AGENTS.md`](../../scripts/AGENTS.md) — pipeline entry points
