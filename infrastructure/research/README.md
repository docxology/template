# Research Workflow Module

Programmatic definition of the seven-stage research workflow and agent-facing
prompt text for the template/ research infrastructure. Ported and adapted from
[OpenScience](https://github.com/synthetic-sciences/openscience).

## Overview

```python
from infrastructure.research import ResearchWorkflow

workflow = ResearchWorkflow()

# Print a markdown rendering of all seven stages
print(workflow.describe())

# Access a specific stage (implemented names: scope, survey, hypothesise,
# experiment, validate, review, write — see the drift note under "Public API")
stage = workflow.stage("survey")
print(stage.description)
```

## Seven-Stage Workflow

| # | Stage | Required | Sub-agent | Outputs |
|---|-------|----------|-----------|---------|
| 1 | SCOPE | ✓ | — | `scope.md` |
| 2 | LITERATURE | ✓ | `literature-review` (×5) | `literature-review.md` |
| 3 | REASON | ✓ | — | `reasoning.md` |
| 4 | DESIGN | ✓ | — | `design.md` |
| 5 | COMPUTE | ✓ | — | `results.md`, `output/data/*` |
| 6 | SYNTHESIZE | ✓ | — | `synthesis.md` |
| 7 | WRITE | optional | `write` | `manuscript/*` |

## Agent Prompts

| File | Use |
|------|-----|
| [`prompts/research_workflow.md`](prompts/research_workflow.md) | Load as system context for the primary research agent. |
| [`prompts/literature_review.md`](prompts/literature_review.md) | Load as context when spawning `literature-review` sub-agents. |

## Key Commands

```bash
# Literature search (multi-backend: arXiv + Crossref)
uv run python -m infrastructure.search.literature search \
    --query 'your query' --max-results 50

# Export as BibTeX into a project's manuscript
uv run python -m infrastructure.search.literature.cli to-bibtex \
    'your query' --source arxiv,crossref \
    --output projects/{name}/manuscript/references.bib

# Exa semantic / grounded-answer search
uv run python -m infrastructure.search.exa answer 'your query'

# Run the full project pipeline
uv run python scripts/runner/execute_pipeline.py --project {name}

# Run only the analysis stage
uv run python scripts/pipeline/stage_02_analysis.py --project {name}

# Record a provenance node
uv run python -m infrastructure.provenance record run \
    --tool synthesize --label 'synthesis complete' --project {name}
```

## Public API

```python
from infrastructure.research import (
    ResearchStage,          # dataclass: one workflow stage (name/label/description/inputs/outputs/gate/status/order)
    ResearchWorkflow,       # instance API: workflow.stage(name), workflow.all_stages(), workflow.describe()
    StageStatus,            # enum: pending/in_progress/complete status per stage
    ResearchWorkflowConfig, # parsed config.yaml `research_workflow:` block
)
```

> **Doc/code drift (tracked for follow-up):** there is no module-level
> `WORKFLOW_STAGES` export — use `ResearchWorkflow().all_stages()` instead.
> The "Seven-Stage Workflow" table above (SCOPE/LITERATURE/REASON/DESIGN/
> COMPUTE/SYNTHESIZE/WRITE, with per-stage sub-agent fan-out) describes an
> OpenScience-ported design richer than what `ResearchStage` actually
> implements (`scope, survey, hypothesise, experiment, validate, review,
> write` — no `parallel_subagents`/`template_commands` fields). Treat the
> table and the "Provenance Integration" `record run`/`evidence add` CLI
> examples below as design intent, not a verified API surface.

## Provenance Integration

The SYNTHESIZE stage uses `infrastructure.provenance` to record durable
research state. If the module is unavailable, skip silently — it is additive.

```bash
uv run python -m infrastructure.provenance record run \
    --tool synthesize --label '{description}' --project {name}

uv run python -m infrastructure.provenance evidence add \
    --target {node_id} --artifact output/data/{artifact} --project {name}
```

## Source Attribution

The research workflow and literature-review prompt structures are adapted from
OpenScience (`synthetic-sciences/openscience`) by Synthetic Sciences AI.
Adapted for the template/ research infrastructure: OpenScience CLI commands
replaced with `uv run python -m infrastructure.*` invocations; Atlas
persistence replaced with `infrastructure.provenance`; cloud-GPU directives
replaced with the template/ pipeline scripts.

## See Also

- [`AGENTS.md`](AGENTS.md) — agent operating contract
- [`infrastructure/search/README.md`](../search/README.md) — literature search module
- [`infrastructure/autoresearch/README.md`](../autoresearch/README.md) — deterministic readiness checks
- [`scripts/AGENTS.md`](../../scripts/AGENTS.md) — pipeline entry points
- [`infrastructure/core/pipeline/pipeline.yaml`](../core/pipeline/pipeline.yaml) — 14-stage pipeline definition
