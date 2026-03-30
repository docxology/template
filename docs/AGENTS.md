# docs/ — Documentation Hub

## Overview

Technical guide for the `docs/` directory — the central documentation hub for the Research Project Template.

## Directory Structure

| Directory | Purpose |
| ---------- | ------- |
| `core/` | Essential docs: usage guide, architecture overview, workflow |
| `guides/` | Skill-level guides (Levels 1-12) + new project setup checklist |
| `architecture/` | System design, two-layer architecture, thin orchestrator |
| `usage/` | Content authoring, formatting, visualization patterns |
| `operational/` | Build, config, logging, troubleshooting, reporting |
| `reference/` | API reference, glossary, FAQ, cheatsheet, workflows |
| `modules/` | Infrastructure module guides (13 modules) |
| `development/` | Contributing, testing, security, roadmap |
| `best-practices/` | Best practices, version control, migration |
| `prompts/` | AI prompt templates (9 expert prompts) |
| `audit/` | Audit reports and findings |
| `security/` | Security documentation and policies |
| `rules/` | Development standards and guidelines (formerly .cursorrules) |
| `streams/` | Timestamped notes for livestreams and recorded talks |
| `_generated/` | Machine-generated snippets; authoritative active `projects/` names in `active_projects.md` — link there instead of duplicating rosters in guides |

## Key Conventions

- Each sub-directory has a `README.md` (user-facing index) and `AGENTS.md` (technical guide)
- `documentation-index.md` is the comprehensive flat index of all files
- Cross-references use relative paths with descriptive link text
- Documentation is intended to be evergreen; when behaviour changes, we may include dated notes so it’s clear which guidance is newer.

## Entry Points

| Audience | Start Here |
| -------- | ---------- |
| New user | `core/how-to-use.md` → `guides/getting-started.md` |
| Developer | `core/architecture.md` → `architecture/two-layer-architecture.md` |
| **New project** | **`guides/new-project-setup.md`** → **`guides/new-project-one-shot-prompt.md`** (optional LLM scaffold) → `architecture/thin-orchestrator-summary.md` |
| Contributor | `development/contributing.md` → `development/testing/` |
| AI Agent | `rules/AGENTS.md` → `rules/README.md` |
| Troubleshooter | `operational/troubleshooting/` → `reference/faq.md` |

## Learnings & Known Issues

Key discoveries from multi-project development are documented in:

- **[guides/new-project-setup.md](guides/new-project-setup.md)** — Comprehensive setup checklist with all pitfalls
- **[operational/troubleshooting/common-errors.md](operational/troubleshooting/common-errors.md)** — Pipeline-specific error patterns

### ⚠️ Critical Rule: Root Venv Must Include All Project Dependencies

If a project in `projects/<name>/` has its own `pyproject.toml` but **no `.venv/` directory**, every package listed in that `pyproject.toml#dependencies` must also appear in the **root** `pyproject.toml`. Analysis scripts (`02_run_analysis.py`) run under the root venv in this case.

**Symptom when violated:** `❌ <project>: 4 stages, 7.7s` — Stage 4 (Analysis) fails silently in < 1s. No import error surfaces in the console.

**Fix:** Add missing packages to root `pyproject.toml`, then `uv sync`.

**Root venv vs project `pyproject.toml`:**

| Scope | Notes |
| --- | --- |
| [`projects/code_project/`](../projects/code_project/) | Stable exemplar; often uses a local `projects/code_project/.venv/`. |
| Any other `projects/{name}/` | Listed in [_generated/active_projects.md](_generated/active_projects.md). If that project has **no** `.venv/`, every package in its `pyproject.toml` must also appear in the **root** `pyproject.toml`. |
| Plotting | `matplotlib` must be in root `[project.dependencies]` (not only optional groups) when analysis needs it under the root interpreter. |

### ⚠️ Critical Rule: `matplotlib` Must be in Core Dependencies

`matplotlib` must be in `[project.dependencies]`, not `[project.optional-dependencies]`. `uv sync` without flags does not install optional groups.

### Idempotency Contract for Analysis Scripts

Network-dependent analysis scripts (e.g., literature search, LLM extraction) must detect existing output files and skip re-processing:

```python
if corpus_path.exists() and corpus_path.stat().st_size > 0:
    logger.info("Corpus already populated — skipping network searches.")
    # load and return existing data
else:
    # perform actual network operation
```

This ensures the pipeline remains reproducible and does not make expensive network calls when the output clean step preserves data files.

## See Also

- [README.md](README.md) — Quick navigation with Mermaid diagram
- [documentation-index.md](documentation-index.md) — Comprehensive file index
- [Root AGENTS.md](../AGENTS.md) — System-level documentation

## 3-Directory Project Lifecycle

Projects are tracked across three sibling directories:

| Directory | Purpose | Discovered by `./run.sh`? |
| ---------- | ------- | ------------------------ |
| `projects/` | **Active** projects for the current pipeline run | ✅ Yes |
| `projects_in_progress/` | Work-in-progress projects not yet ready for rendering | ❌ No |
| `projects_archive/` | Completed or paused projects kept for reference | ❌ No |

**Movement rules:**

- Only projects under `projects/` are discovered and rendered by `./run.sh`.
- Move a project **into** `projects/` when it is ready for a full pipeline run.
- Move a project **out** to `projects_in_progress/` or `projects_archive/` when it is not the current focus, to keep pipeline output clean and fast.
- Projects in archive/in-progress directories retain their structure so they can be moved back at any time without modification.

**Configuring the active directory (advanced):**

To run the pipeline against a non-default directory (e.g., for smoke-testing an in-progress project without moving it):

```python
from infrastructure.core.pipeline.types import PipelineConfig
from infrastructure.core.pipeline.pipeline import PipelineExecutor

config = PipelineConfig(
    project_name="my_wip_project",
    repo_root=Path("."),
    projects_dir="projects_in_progress",  # override the default "projects"
)
executor = PipelineExecutor(config)
executor.execute_core_pipeline()
```

The `projects_dir` field on `PipelineConfig` defaults to `"projects"`, preserving the standard `./run.sh` behaviour. The resolved project root path is the read-only property `project_dir` (`repo_root / projects_dir / project_name`). Call sites and helpers that accept an explicit directory typically take a `projects_dir` string (or derive paths from `PipelineConfig`).
