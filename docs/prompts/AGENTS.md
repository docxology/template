# AI Prompt Templates

## Overview

Technical guide for `docs/prompts/` — prompt templates aligned with Research Project Template standards.

## Files

| File | Purpose |
|------|---------|
| `manuscript_creation.md` | Manuscript creation from research description |
| `code_development.md` | Standards-compliant code development |
| `test_creation.md` | Test creation (no mocks policy) |
| `feature_addition.md` | Feature development with architecture compliance |
| `refactoring.md` | Clean-break code refactoring |
| `documentation_creation.md` | AGENTS.md and README.md creation |
| `infrastructure_module.md` | Generic infrastructure module development |
| `validation_quality.md` | Quality assurance and validation |
| `comprehensive_assessment.md` | Comprehensive assessment and review |

## Key Conventions

- **Exemplar tree**: point concrete paths at [`projects/code_project/`](../../projects/code_project/); active names → [_generated/active_projects.md](../_generated/active_projects.md).
- Each prompt includes context injection, explicit constraints, and verification steps
- All prompts enforce the thin orchestrator pattern and no-mocks testing policy
- Prompts reference `../rules/` standards for consistency
- Copy-paste ready — each prompt is self-contained

## See Also

- [README.md](README.md) — Prompt overview and usage guide
- [Contributing](../development/contributing.md) — Development standards
