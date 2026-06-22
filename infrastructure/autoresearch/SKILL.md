---
name: infrastructure-autoresearch
description: Skill for deterministic AutoResearch readiness planning. Use when adding, validating, or documenting opt-in autoresearch.yaml controls, stage-gate readiness, evidence-grounded claims, artifact readiness reports, or AutoResearchClaw-inspired workflow checks in template projects.
---

# AutoResearch Readiness

Use this module for deterministic planning and readiness validation. It adapts
reviewed AutoResearchClaw design ideas as file-backed template controls, not as
an autonomous research agent.

AutoResearch CLI-style measurement ideas are treated the same way: adopt exact
metric extraction, review-status vocabulary, baseline/noise/confidence
disclosure, and append-only evidence discipline; do not add lifecycle hooks,
git commit/revert ownership, or no-human autonomous loops by default.

## Commands

```bash
uv run python -m infrastructure.autoresearch.cli validate --project templates/template_code_project --fail-on-issues
```

## Public API

```python
from infrastructure.autoresearch import (
    AutoResearchConfig,
    AutoResearchIssue,
    AutoResearchPlan,
    AutoResearchReport,
    mad_confidence,
    metric_unit_from_name,
    build_autoresearch_plan,
    load_autoresearch_config,
    parse_metric_lines,
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

Use `parse_metric_lines()` only for output already produced by a trusted local
command. It accepts exact `METRIC name=value` lines and rejects ambiguous or
invalid metric evidence. Use `mad_confidence()` as a disclosure helper for
baseline/best/noise comparisons, not as an automatic publication decision.
