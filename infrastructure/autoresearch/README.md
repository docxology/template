# AutoResearch Readiness

Deterministic planning and readiness validation for research projects.

This module adapts design ideas reviewed from
[aiming-lab/AutoResearchClaw](https://github.com/aiming-lab/AutoResearchClaw)
at commit `b5804c5fa0acecc01f56bdf52995e11bb74474cc`: explicit research
plans, stage/gate contracts, human-review policy, evidence-grounded claims,
artifact readiness reports, and run lessons. It does not implement an
autonomous idea-to-paper runner.

## Public API

```python
from infrastructure.autoresearch import (
    build_autoresearch_plan,
    load_autoresearch_config,
    parse_string_sequence,
    validate_autoresearch_plan,
    write_autoresearch_report,
)
```

`validate_autoresearch_plan(plan, project_root, phase="all")` accepts
`phase="intrinsic"` or `phase="extrinsic"` to validate pre-write structure or
post-write artifact surfaces separately.

The module composes existing template surfaces:

- `domain_profile.yaml`
- `experiment_plan.yaml`
- `pipeline.yaml`
- `output/reports/evidence_registry.json`
- `output/reports/artifact_manifest.json`
- thin-orchestrator drift checks

## Configuration

Projects may add `autoresearch.yaml`:

```yaml
enabled: true
strict: true
topic: "Deterministic readiness"
quality_checks:
  - domain_profile
  - experiment_plan
  - pipeline_contracts
  - evidence_registry
  - artifact_manifest
  - thin_orchestrators
stage_gates:
  - Project Analysis
  - Output Validation
required_artifacts:
  - output/data/result.csv
```

`stage_gates` entries must exactly match stage names in `pipeline.yaml`.
Unknown quality checks fail validation. In non-strict mode, readiness defects
that are not configuration errors are warnings.

## CLI

```bash
uv run python -m infrastructure.autoresearch.cli validate --project template_code_project --fail-on-issues
```

Reports are written to:

- `projects/{project}/output/reports/autoresearch_readiness.json`
- `projects/{project}/output/reports/autoresearch_readiness.md`
