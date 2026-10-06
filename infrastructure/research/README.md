# Research Workflow Module

`ResearchWorkflow` describes a research plan. Its stage descriptors record
expected inputs, outputs, gates, order and status. Creating or displaying a
plan performs no research computation and does not establish that any gate passed.

## Public API

```python
from infrastructure.research import ResearchWorkflow, load_research_workflow_config

workflow = ResearchWorkflow()
print(workflow.describe())
print(workflow.stage("survey").gate)
for stage in workflow.all_stages():
    print(stage.name, stage.inputs, stage.outputs)
serialized = workflow.to_dict()
config = load_research_workflow_config("projects/templates/template_code_project")
```

The package exports `ResearchWorkflow`, `ResearchStage`, `StageStatus`,
`ResearchWorkflowConfig` and `load_research_workflow_config`.
`ResearchStage.to_dict()` and `ResearchWorkflow.to_dict()` serialize descriptors;
callers supply actual execution and evidence separately.

## Built-in stages

| Order | Name | Described work |
|---|---|---|
| 0 | `scope` | Research question, success criteria, domain profile and experiment plan |
| 1 | `survey` | Literature collection and normalization |
| 2 | `hypothesise` | Testable hypotheses and idea ledger |
| 3 | `experiment` | Experiments, run ledger and provenance |
| 4 | `validate` | Evidence registry and validation report |
| 5 | `review` | Review decisions and required approvals |
| 6 | `write` | Manuscript and research artifacts |

Exact descriptor fields and gate text come from [`workflow.py`](workflow.py).

## Configuration and inspection

The library loader reads optional `research_workflow.yaml` at the **project root**.
Its supported keys are `enabled`, `active_stage`, `skip_stages` and `strict`;
[`config.py`](config.py) validates booleans, known keys and stage names.
Absent files return the dataclass defaults. These settings describe tracking
preferences; loading them executes no stages.

```yaml
# projects/<qualified-project>/research_workflow.yaml
enabled: true
active_stage: survey
skip_stages: []
strict: true
```

The repository inspection script has a separate enable switch in
`manuscript/config.yaml`: `research_workflow.enabled`. It reports descriptors:

```bash
uv run python scripts/pipeline/stage_10_research_workflow.py \
  --project templates/template_code_project --describe
# With the inspection switch enabled in manuscript/config.yaml:
uv run python scripts/pipeline/stage_10_research_workflow.py \
  --project templates/template_code_project --stage survey
```

`--describe` prints the plan even without that switch. `--stage` prints one
stage's details; it launches no model, search or experiment.
Actual project execution uses the canonical pipeline and its source-owned
contracts in [`pipeline.yaml`](../core/pipeline/pipeline.yaml).

## Agent guidance

[`prompts/research_workflow.md`](prompts/research_workflow.md) and
[`prompts/literature_review.md`](prompts/literature_review.md) are optional
agent-context documents adapted from OpenScience. They are prose guidance,
independent of the Python descriptor API.

## Verification and navigation

```bash
uv run pytest tests/infra_tests/research/ --no-cov -q
```

See [`AGENTS.md`](AGENTS.md), [`SKILL.md`](SKILL.md),
[`search/README.md`](../search/README.md) and
[`autoresearch/README.md`](../autoresearch/README.md).
