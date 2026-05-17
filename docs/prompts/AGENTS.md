# AI Prompt Templates

## Overview

Technical guide for `docs/prompts/` — copy-paste prompt templates aligned with Research Project Template standards.

## Files

| File | Purpose |
|------|---------|
| `manuscript_creation.md` | Manuscript scaffold from a research description |
| `manuscript_cross_references.md` | Registry/token manuscripts (`labels.yaml`, `[[FIG:]]`, …) and cross-ref audits |
| `manuscript_claim_verification.md` | Triple-check every manuscript claim against code/data/refs/renderer; improve text; keep AGENTS/README complete |
| `code_development.md` | Standards-compliant code development |
| `test_creation.md` | Tests under the no-mocks policy |
| `feature_addition.md` | Feature work with architecture compliance |
| `refactoring.md` | Clean-break refactoring |
| `documentation_creation.md` | AGENTS.md and README.md authoring |
| `infrastructure_module.md` | Generic `infrastructure/` module development |
| `validation_quality.md` | Validation and QA workflows |
| `comprehensive_assessment.md` | Full-repo or multi-area assessment (metrics measured, not assumed) |
| `reproducibility_audit.md` | Determinism, regenerate-from-clean, double-run diff before release/Zenodo |
| `pipeline_debugging.md` | Systematic DAG-stage failure triage (reproduce → isolate → classify → fix) |
| `literature_synthesis.md` | LLM prompt blocks for literature search synthesis |

## Key conventions

- **Exemplar paths**: default to [`projects/template_code_project/`](../../projects/template_code_project/); active `projects/` names → [`_generated/active_projects.md`](../_generated/active_projects.md).
- **Manuscript semantics**: most exemplars use Pandoc + `pandoc-crossref` + `[@citekey]` — see [`../guides/manuscript-semantics.md`](../guides/manuscript-semantics.md). Some projects use a **YAML registry + `[[…]]` tokens**; use `manuscript_cross_references.md` for those.
- Each prompt should name **constraints**, **verification commands**, and **layer** (infrastructure vs project) where relevant.
- Enforce the thin orchestrator pattern and the no-mocks testing policy unless a task explicitly documents an exception.
- Point to [`../rules/`](../rules/) for normative detail; avoid duplicating long rule text inside prompts.

## See also

- [README.md](README.md) — overview and navigation
- [Contributing](../development/contributing.md) — contribution workflow
