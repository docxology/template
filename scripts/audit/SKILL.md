---
name: template-audit
version: 1.0.0
description: >
  Audit and quality-gate scripts for the template research framework.
  Covers documentation linting, filepath audits, mock-usage checking,
  template drift, and confidentiality / git-guard checks.
tags:
  - audit
  - quality
  - lint
  - drift
  - template
trigger: "audit|lint docs|template drift|check tracked|verify no mocks|git guard|confidentiality"
---

# template-audit

Audit and quality-gate scripts in `scripts/audit/`.

## When to use

Load this skill when you need to:
- Run documentation or filepath audits
- Check for template drift in exemplar projects
- Enforce confidentiality (no private project commits)
- Verify prohibited mock-framework syntax is absent and inventory semantic stand-ins

## Key scripts

| Script | Exit 0 means |
|--------|-------------|
| `lint_docs.py` | All doc lints pass |
| `check_tracked_projects.py` | No private projects staged/committed |
| `check_template_drift.py` | Exemplars are up-to-date |
| `verify_no_mocks.py` | No prohibited mock-framework imports/calls detected |

## Bootstrap note

All scripts use `parents[2]` from `scripts/audit/` — three levels to repo root.

## Pitfalls

- `check_tracked_projects.py` runs in pre-push hook — keep it fast.
- `audit_documentation.py` is advisory; non-zero exit is a warning, not a gate.
- `copy_exemplar.py` modifies tracked files — review diff before committing.
- `verify_no_mocks.py --inventory` is advisory while dependency-replacement
  debt is non-zero. Do not interpret the default lexical pass as proof that all
  integration points are real.
