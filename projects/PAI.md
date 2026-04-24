# 🧠 PAI.md - Projects Context

## 📍 Purpose

This directory contains the **Layer 2** domain-specific research projects. Each subdirectory is a self-contained research environment operated upon by shared infrastructure.

## 📊 Active Projects

| Project           | Domain                          | Status |
|-------------------|---------------------------------|--------|
| `code_project`         | Optimization research exemplar  | ✅ Active |
| `fep_lean`             | FEP / Lean4 formalization       | ✅ Active |
| `act_inf_metaanalysis` | Active Inference meta-analysis  | ✅ Active |

Authoritative slugs: [`docs/_generated/active_projects.md`](../docs/_generated/active_projects.md) (regenerated from `discover_projects()`).

## 📂 Structure Per Project

- `src/`: Pure scientific logic and self-contained execution.
- `tests/`: Zero-Mock test suite guaranteeing 90%+ coverage.
- `scripts/`: Thin Orchestrators handling side-effects and coordination.
- `manuscript/`: Markdown source and configuration.
- `docs/`: Modular documentation hub.
- `output/`: Working directory for generated artifacts.

## 🤖 Agent Guidelines

- **Isolation**: Projects should not import from each other.
- **Infrastructure Usage**: Projects can and should import from `infrastructure/`.
- **Creation**: To create a new project, copy an existing project under `projects/` as a template.
- **In-Progress**: Projects in `projects_in_progress/` are not yet discovered by the pipeline until moved under `projects/`.
- **Archived**: Projects in `projects_archive/` are preserved but not discovered.

## 🔗 Key References

- [AGENTS.md](AGENTS.md) — Technical documentation for the projects directory
- [README.md](README.md) — Quick reference and getting started
- [PROJECTS_PARADIGM.md](PROJECTS_PARADIGM.md) — Standalone project paradigm philosophy
- [code_project/AGENTS.md](code_project/AGENTS.md) — Canonical control-positive exemplar technical docs
