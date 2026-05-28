# AutoResearch Module

> **Deterministic readiness planning for research workflows.**

**Location:** `infrastructure/autoresearch/`
**Quick Reference:** [Modules Guide](../modules-guide.md) | [AutoResearch Exemplar](../../../projects/templates/template_autoresearch_project/README.md) | [Code Review Checklist](../../development/code-review-checklist.md)

---

## Key Features

- **Readiness plan** - `build_autoresearch_plan()` composes project profile, experiment plan, pipeline contract, evidence, artifacts, and script-drift checks.
- **Phase validation** - `validate_autoresearch_plan(..., phase="intrinsic"|"extrinsic"|"all")` separates pre-write structure checks from post-write artifact checks.
- **File-backed configuration** - project-local `autoresearch.yaml` declares enabled checks, strictness, exact stage gates, and required artifacts.
- **Reports** - `write_autoresearch_report()` writes JSON and Markdown readiness reports under the project `output/reports/` tree.
- **Bounded scope** - no network calls, no LLM calls, no generated-code execution, and no autonomous self-approval loops.

---

## CLI

```bash
uv run python -m infrastructure.autoresearch.cli validate \
  --project template_autoresearch_project \
  --fail-on-issues
```

---

## Public API

```python
from infrastructure.autoresearch import (
    AutoResearchConfig,
    AutoResearchIssue,
    AutoResearchPlan,
    AutoResearchReport,
    AutoResearchStage,
    build_autoresearch_plan,
    load_autoresearch_config,
    validate_autoresearch_plan,
    write_autoresearch_report,
)
```

See `infrastructure/autoresearch/__init__.py` for the authoritative export list.

---

## Review Criteria Mapping

The AutoResearch module is reviewed primarily against criteria 2 (Composability - reuse pipeline, project, validation, and reporting modules), 5 (Validation - deterministic readiness defects are explicit), and 8 (Reproducibility - reports are file-backed and inspectable). See [Code Review Checklist](../../development/code-review-checklist.md).
