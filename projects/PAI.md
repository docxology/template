# 🧠 PAI.md - Projects Context

## 📍 Purpose

This directory contains the **Layer 2** domain-specific research projects. Each subdirectory is a self-contained research environment operated upon by shared infrastructure.

## 📊 Active Projects

| Project        | Domain                    | Tests | Coverage | Status |
|----------------|---------------------------|-------|----------|--------|
| `code_project` | Optimization research     | 45    | 100%     | ✅ Active |
| `template`     | Meta-documentation        | 65    | 94.4%    | ✅ Active |
| `cognitive_case_diagrams` | Case / diagrams    | large | ≥90% `src/` | ✅ Active |
| `fep_lean`     | FEP / Lean catalogue      | ~180  | ≥89% `src/` | ✅ Active |

Authoritative slugs: [`docs/_generated/active_projects.md`](../docs/_generated/active_projects.md).

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
- [code_project/AGENTS.md](code_project/AGENTS.md) — Master exemplar technical docs
- [template/AGENTS.md](template/AGENTS.md) — Meta-documentation project docs
