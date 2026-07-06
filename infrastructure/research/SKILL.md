---
name: research-workflow
description: >
  Seven-stage research workflow (SCOPE→LITERATURE→REASON→DESIGN→COMPUTE→SYNTHESIZE→WRITE).
  Use for: structuring an AI agent's research process, generating literature
  review prompts, scoping methodology.
  Usage: from infrastructure.research import ResearchWorkflow; ResearchWorkflow.describe()
  Config: set stage overrides in projects/{name}/manuscript/config.yaml `research_workflow:` block.
---

# Research Workflow

Seven-stage research workflow scaffolding for AI-assisted research processes.
Each stage produces structured prompts and acceptance criteria for agent loops.

## Stages

| # | Stage | Purpose |
| --- | --- | --- |
| 1 | **SCOPE** | Define research question, scope, and success criteria |
| 2 | **LITERATURE** | Survey prior work; produce annotated bibliography |
| 3 | **REASON** | Identify gaps, contradictions, and open questions |
| 4 | **DESIGN** | Formulate methodology and experimental plan |
| 5 | **COMPUTE** | Execute analysis; collect and validate results |
| 6 | **SYNTHESIZE** | Interpret results relative to prior work |
| 7 | **WRITE** | Draft manuscript sections and iterative revision |

## Quick Start

```python
from infrastructure.research import ResearchWorkflow

# Print all stage descriptions
ResearchWorkflow.describe()

# Get a structured prompt for a specific stage
prompt = ResearchWorkflow.prompt("SCOPE", question="What drives protein misfolding?")
print(prompt)

# Iterate stages in order
for stage in ResearchWorkflow.stages():
    print(f"{stage.index}. {stage.name}: {stage.description}")
```

## Pipeline Orchestrator

```bash
# Run research workflow scaffolding for a named project
uv run python scripts/10_research_workflow.py --project my_project

# Run only specific stages
uv run python scripts/10_research_workflow.py --project my_project --stages SCOPE,LITERATURE

# Generate stage prompts without executing
uv run python scripts/10_research_workflow.py --project my_project --dry-run
```

## Config Integration

Set stage overrides in `projects/{name}/manuscript/config.yaml`:

```yaml
research_workflow:
  question: "How do transformer attention patterns relate to syntactic structure?"
  stages:
    SCOPE:
      depth: detailed
    LITERATURE:
      max_papers: 50
      sources:
        - arxiv
        - semantic_scholar
    WRITE:
      target_venue: NeurIPS
```

## Key Types

```python
from infrastructure.research import (
    ResearchWorkflow,   # Main class — describe / prompt / stages
    ResearchStage,      # Stage descriptor: index, name, description, prompt_template
    WorkflowConfig,     # Parsed config.yaml `research_workflow:` block
)
```

## Stage Prompt Generation

```python
from infrastructure.research import ResearchWorkflow

# Generate LITERATURE stage prompt for a specific project
prompt = ResearchWorkflow.prompt(
    "LITERATURE",
    question="Neural scaling laws",
    context={"prior_papers": 12, "target_venue": "ICML"},
)
```

## Agent Loop Integration

```python
from infrastructure.research import ResearchWorkflow

# Use in an agent loop
for stage in ResearchWorkflow.stages():
    prompt = stage.render(project_context)
    response = llm_call(prompt)
    stage.record_output(response, output_dir="output/research/")
```

## Testing

```bash
uv run pytest tests/infra_tests/research/ -v
```

## See Also

- [`AGENTS.md`](AGENTS.md) — operating contract and architecture
- [`../search/SKILL.md`](../search/SKILL.md) — literature search integration
- [`../llm/SKILL.md`](../llm/SKILL.md) — LLM review integration
