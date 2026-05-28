# 🧠 PAI.md - Projects Context

## 📍 Purpose

This directory contains the **Layer 2** domain-specific research projects. Each subdirectory is a self-contained research environment operated upon by shared infrastructure.

## PAI v5 Project Framing

For substantial project work, use an ISA as the live statement of ideal state, verification criteria, decisions, and done condition. PRD references should be treated as archival wording unless a project explicitly preserves them as historical material.

## 📊 Active Projects

Always-present permanent exemplars under `projects/`:

| Project | Domain | Status |
|---|---|---|
| `template_active_inference` | Active Inference multi-track exemplar | ✅ Permanent exemplar |
| `template_autoresearch_project` | AutoResearch exemplar | ✅ Permanent exemplar |
| `template_code_project` | Optimization research exemplar | ✅ Permanent exemplar |
| `template_prose_project` | Prose-review exemplar | ✅ Permanent exemplar |
| `template_template` | Meta-template exemplar | ✅ Permanent exemplar |

Rotating projects appear under `projects/active/` in some checkouts and under `projects/archive/`, `projects/working/`, `projects/published/`, or `projects/other/` in others; specific names rotate, so consult the generated roster rather than hard-coding them.

Authoritative public active roster: [`docs/_generated/active_projects.md`](../docs/_generated/active_projects.md) (regenerated from `infrastructure.project.public_scope`; runtime `discover_projects()` may include local private symlinks).

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
- **Creation**: To create a new project, copy an exemplar from `projects/templates/` into `projects/active/`.
- **In-Progress**: Projects in `projects/working/` are not yet discovered by the pipeline until moved under `projects/active/`.
- **Archived**: Projects in `projects/archive/` are preserved but not discovered.

## 🔗 Key References

- [AGENTS.md](AGENTS.md) — Technical documentation for the projects directory
- [README.md](README.md) — Quick reference and getting started
- [PROJECTS_PARADIGM.md](PROJECTS_PARADIGM.md) — Standalone project paradigm philosophy
- [templates/template_code_project/AGENTS.md](templates/template_code_project/AGENTS.md) — Canonical control-positive exemplar technical docs
