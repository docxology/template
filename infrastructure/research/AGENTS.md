# Research Module — Agent Notes

`infrastructure.research` provides descriptive research-stage and configuration
APIs. Its immutable stage descriptors are planning data. Status values and gate
text do not prove that research was executed or reviewed.

## Read order

Read [`README.md`](README.md), then [`workflow.py`](workflow.py) and
[`config.py`](config.py) before changing descriptors or configuration.
Repository pipeline execution is governed by
[`core/pipeline/pipeline.yaml`](../core/pipeline/pipeline.yaml).

## Implemented API

```python
from infrastructure.research import ResearchWorkflow, ResearchStage, StageStatus

workflow = ResearchWorkflow()
stage = workflow.stage("survey")
print(stage.description, stage.gate)
print(workflow.describe())
serialized = workflow.to_dict()
ordered_stages = workflow.all_stages()
```

Built-in names, in order, are `scope`, `survey`, `hypothesise`, `experiment`,
`validate`, `review` and `write`. `ResearchStage` contains `name`, `label`,
`description`, `inputs`, `outputs`, `gate`, `status` and `order`.
`StageStatus` values are `pending`, `in_progress`, `complete`, `skipped` and
`blocked`. There is no automatic status transition or gate evaluator here.

Callers can construct their own descriptor list and pass
`ResearchWorkflow(stages=descriptors)`. Changes to the built-in vocabulary
must update `_STAGE_DEFS`, `ResearchWorkflow.STAGE_NAMES` and the validated
configuration stage names together, with tests of actual descriptor behavior.

## Configuration boundaries

`load_research_workflow_config(project_dir)` reads optional
`project_dir/research_workflow.yaml`, with `enabled`, `active_stage`,
`skip_stages` and `strict` keys. Unknown keys and invalid names fail.
The dataclass's tracking defaults are returned when the file is absent.

`scripts/pipeline/stage_10_research_workflow.py` is an inspection CLI. Its
separate `manuscript/config.yaml` switch is `research_workflow.enabled`.
`--describe` prints the full plan; `--stage survey` prints one descriptor when
the inspection switch is enabled. Neither command dispatches research workers.

Actual computations belong in domain source and the canonical execution DAG.
Generic search, model, provenance and publication services retain their own
explicit configuration, evidence and execution boundaries.

## Optional prose guidance

[`prompts/research_workflow.md`](prompts/research_workflow.md) and
[`prompts/literature_review.md`](prompts/literature_review.md) are agent-context
references. They do not implement Python prompt generation or execution APIs,
and do not authorize external communications or paid provider calls.

## Verification

Run `uv run pytest tests/infra_tests/research/ --no-cov -q` after changes.
Descriptor serialization and configuration errors have real tests; preserve
source-owned gate wording and the distinction between plans and execution.

See [`SKILL.md`](SKILL.md), [`search/AGENTS.md`](../search/AGENTS.md),
[`autoresearch/AGENTS.md`](../autoresearch/AGENTS.md) and
[`scripts/AGENTS.md`](../../scripts/AGENTS.md).
