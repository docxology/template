# Doctor Module

> **Diagnose and safely repair repository state — detectors, fixers, safety journal, scorecard.**

**Location:** `infrastructure/doctor/`
**Quick Reference:** [Modules Guide](../modules-guide.md) | [API Reference](../../reference/api-reference.md) | [Code Review Checklist](../../development/code-review-checklist.md)

---

## Key Features

- **Read-only detectors** — produce `Finding` objects without mutating the tree.
- **Fixers** — translate findings into `FixPlan` objects (declarative, not executed by themselves).
- **Safety boundary** — `safety.mutate()` is the only entry point that touches the filesystem; every change is snapshotted into `.doctor/backups/<action_id>/` and journaled in `.doctor/actions.jsonl` so `safety.undo()` can replay in reverse.
- **Scorecard** — numeric summary across diagnostic dimensions.
- **Reporter** — text + JSON output with stable exit codes by severity.

---

## CLI

```bash
uv run python -m infrastructure.doctor                  # diagnose
uv run python -m infrastructure.doctor fix --plan       # dry-run plan
uv run python -m infrastructure.doctor fix --apply      # apply safe fixes
uv run python -m infrastructure.doctor fix --apply --aggressive
uv run python -m infrastructure.doctor undo --last
uv run python -m infrastructure.doctor history
uv run python -m infrastructure.doctor capabilities
```

---

## Public API (selected)

```python
from infrastructure.doctor import (
    DETECTORS, run_detectors,
    FIXER_REGISTRY, build_plans_for_findings,
    DoctorReport, Finding, FixPlan, MutateRecord,
    RepairLevel, Severity,
    compute_scorecard,
)
```

See `infrastructure/doctor/__init__.py` for the complete authoritative docstring and the full export list.

---

## Review Criteria Mapping

The doctor module is reviewed primarily against criteria 3 (Functionality / SSOT — diagnosis logic lives here, not in scripts), 5 (Validation — filesystem mutations must go through `safety.mutate`), and 8 (Reproducibility — journalled actions). See [Code Review Checklist](../../development/code-review-checklist.md).
