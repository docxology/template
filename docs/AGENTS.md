# docs/ — Documentation Hub

## Overview

Technical guide for the `docs/` directory — the central documentation hub for the Research Project Template.

## Directory Structure

| Directory | Purpose |
|-----------|---------|
| `core/` | Essential docs: usage guide, architecture overview, workflow |
| `guides/` | Skill-level guides (Levels 1-12) |
| `architecture/` | System design, two-layer architecture, thin orchestrator |
| `usage/` | Content authoring, formatting, visualization patterns |
| `operational/` | Build, config, logging, troubleshooting, reporting |
| `reference/` | API reference, glossary, FAQ, cheatsheet, workflows |
| `modules/` | Infrastructure module guides (9 modules) |
| `development/` | Contributing, testing, security, roadmap |
| `best-practices/` | Best practices, version control, migration |
| `prompts/` | AI prompt templates (9 expert prompts) |
| `audit/` | Audit reports and findings |

## Key Conventions

- Each sub-directory has a `README.md` (user-facing index) and `AGENTS.md` (technical guide)
- `documentation-index.md` is the comprehensive flat index of all files
- Cross-references use relative paths with descriptive link text
- All documentation is evergreen (no time-sensitive dates)

## Entry Points

| Audience | Start Here |
|----------|------------|
| New user | `core/how-to-use.md` → `guides/getting-started.md` |
| Developer | `core/architecture.md` → `architecture/two-layer-architecture.md` |
| Contributor | `development/contributing.md` → `development/testing/` |
| Troubleshooter | `operational/troubleshooting/` → `reference/faq.md` |

## See Also

- [README.md](README.md) — Quick navigation with Mermaid diagram
- [documentation-index.md](documentation-index.md) — Comprehensive file index
- [Root AGENTS.md](../AGENTS.md) — System-level documentation
