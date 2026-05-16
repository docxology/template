# 🧠 PAI.md - Projects Context

## 📍 Purpose

This directory contains the **Layer 2** domain-specific research projects. Each subdirectory is a self-contained research environment operated upon by shared infrastructure.

## PAI v5 Project Framing

For substantial project work, use an ISA as the live statement of ideal state, verification criteria, decisions, and done condition. PRD references should be treated as archival wording unless a project explicitly preserves them as historical material.

## 📊 Active Projects

Always-present permanent exemplars under `projects/`:

| Project | Domain | Status |
|---|---|---|
| `template_code_project` | Optimization research exemplar | ✅ Permanent exemplar |
| `template_prose_project` | Prose-review exemplar | ✅ Permanent exemplar |

Rotating projects (e.g. `actinf_policy_entanglement_lean`, `crescent_city`) appear under `projects/` in some checkouts and under `projects_archive/` or `projects_in_progress/` in others. `fep_lean` and `act_inf_metaanalysis` are currently archived.

Authoritative active roster: [`docs/_generated/active_projects.md`](../docs/_generated/active_projects.md) (regenerated from `discover_projects()`).

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
- [template_code_project/AGENTS.md](template_code_project/AGENTS.md) — Canonical control-positive exemplar technical docs
