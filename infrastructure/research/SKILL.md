---
name: research-workflow
description: >
  Descriptive research planning API: scope, survey, hypothesise, experiment,
  validate, review and write. Use for inspecting ordered stage descriptors,
  expected artifacts, gates and tracking configuration. Instantiate
  ResearchWorkflow; query stage(name), all_stages(), describe() or to_dict().
  The library reads optional project-root research_workflow.yaml.
---

# Research Workflow

Use this module when a caller needs an inspectable research plan or tracking
configuration. Execution and evidence are supplied by the caller's actual
project pipeline.

## Quick reference

```python
from infrastructure.research import ResearchWorkflow, load_research_workflow_config

workflow = ResearchWorkflow()
print(workflow.describe())
for stage in workflow.all_stages():
    print(stage.order, stage.name, stage.gate)
record = workflow.stage("survey").to_dict()
plan = workflow.to_dict()
settings = load_research_workflow_config("projects/templates/template_code_project")
```

Stage names are `scope`, `survey`, `hypothesise`, `experiment`, `validate`,
`review` and `write`. Descriptors contain name, label, description, inputs,
outputs, gate, status and order; no computation happens when they are displayed.

## Configuration

The library reads optional `projects/<qualified-project>/research_workflow.yaml`:

```yaml
enabled: true
active_stage: survey
skip_stages: []
strict: true
```

Unknown keys and invalid stage names fail. Missing files return tracking defaults.
The separate repository inspection CLI reads `research_workflow.enabled` from
`manuscript/config.yaml` and supports these actual arguments:

```bash
uv run python scripts/pipeline/stage_10_research_workflow.py \
  --project templates/template_code_project --describe
uv run python scripts/pipeline/stage_10_research_workflow.py \
  --project templates/template_code_project --stage survey
```

`--describe` works without enabling the inspection switch. `--stage` reports
a descriptor with the switch enabled. These are inspection commands;
actual computations use the canonical execution DAG and domain producers.

## Boundaries and verification

The optional documents under [`prompts/`](prompts/) provide agent-context prose.
They are separate from the Python planning API. Every execution or acceptance
claim needs actual source-bound producer evidence.

```bash
uv run pytest tests/infra_tests/research/ --no-cov -q
```

See [`README.md`](README.md), [`AGENTS.md`](AGENTS.md),
[`search/SKILL.md`](../search/SKILL.md) and [`llm/SKILL.md`](../llm/SKILL.md).
