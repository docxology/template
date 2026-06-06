---
name: infrastructure-autoresearch
description: Skill for deterministic AutoResearch readiness planning. Use when adding, validating, or documenting opt-in autoresearch.yaml controls, stage-gate readiness, evidence-grounded claims, artifact readiness reports, or AutoResearchClaw-inspired workflow checks in template projects.
---

# AutoResearch Readiness

Use this module for deterministic planning and readiness validation. It adapts
reviewed AutoResearchClaw design ideas as file-backed template controls, not as
an autonomous research agent.

## Commands

```bash
uv run python -m infrastructure.autoresearch.cli validate --project template_code_project --fail-on-issues
```

## Public API

```python
from infrastructure.autoresearch import (
    AutoResearchConfig,
    AutoResearchIssue,
    AutoResearchPlan,
    AutoResearchReport,
    build_autoresearch_plan,
    load_autoresearch_config,
    parse_string_sequence,
    validate_autoresearch_plan,
    write_autoresearch_report,
)
```

`validate_autoresearch_plan(..., phase="intrinsic"|"extrinsic"|"all")` splits
pre-write structure checks from post-write artifact checks.

## Configuration

Project-local `autoresearch.yaml` supports:

- `enabled`
- `strict`
- `topic`
- `quality_checks`
- `stage_gates`
- `required_artifacts`
- `security_profile` (mapping: `enabled`, `mode`, `integrity_algorithm`,
  `network_policy`, `external_signing`, `threat_model_frameworks`)
- `source_manifests` (list of source-manifest artifact paths)

`stage_gates` must use exact stage names from `pipeline.yaml`. The full
accepted key set is defined by `_CONFIG_KEYS` in
`infrastructure/autoresearch/config.py`.

## Guardrails

Keep v1 deterministic: do not add network calls, LLM calls, generated-code
execution, or autonomous loops here. Delegate execution and validation to the
existing pipeline, project, validation, and reporting modules.
