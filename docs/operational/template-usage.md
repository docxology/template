# Using This Repository for New Research Projects

This repository combines **Layer 1** (`infrastructure/`)—generic build, validation, rendering, and pipeline tooling—with **Layer 2** (`projects/{name}/`), where research code, manuscripts, and tests live. Nothing here is published as a standalone Layer 1 pip package; infrastructure is meant to stay in-tree with your projects.

## Overview

Typical layout you keep or extend:

- `infrastructure/`: reusable modules (tests required for changes; coverage gate applies).
- `projects/{name}/`: `src/`, `tests/`, `scripts/`, `manuscript/`, `output/` per project.
- `scripts/`: thin orchestrators invoked by the pipeline.

When starting from this repo as a boilerplate:

1. Copy or fork the repository.
2. Keep `infrastructure/` as-is unless you intend to fork it—then prune optional areas deliberately (see below).
3. Add or rename projects under `projects/` (see [`guides/new-project-setup.md`](../guides/new-project-setup.md)).
4. Adjust root [`pyproject.toml`](../../pyproject.toml) optional dependency groups only if you remove features that need those extras.

## Step 1: Copy the Repository

```bash
git clone <your-remote> my-research-project
cd my-research-project
```

Commit the baseline, then customize `projects/` and manuscripts.

## Step 2: Add or Customize a Project

Use the stable exemplar [`projects/templates/template_code_project/`](../../projects/templates/template_code_project/) as a structural reference: `src/` for logic, `tests/` with coverage targets per [`CLAUDE.md`](../../CLAUDE.md), `scripts/` as thin wrappers calling `src/`, and `manuscript/` for Markdown sources.

Authoritative discovered names (after you add folders) are listed in [`docs/_generated/active_projects.md`](../_generated/active_projects.md).

## Step 3: Optional Pruning

Reduce scope by **not installing** optional dependency groups (`uv sync` defaults are documented in [`CLAUDE.md`](../../CLAUDE.md)), or by deleting unused infrastructure subsystems **only after** you remove pipeline references (grep `scripts/` and `infrastructure/core/pipeline/`).

Examples of optional infrastructure areas projects sometimes drop:

| Area | Notes |
|------|--------|
| `infrastructure/steganography/` | Used when invoking secure PDF hardening (`secure_run.sh`). |
| `infrastructure/publishing/` | Zenodo/arXiv helpers—omit if you do not wire publishing scripts. |
| `infrastructure/llm/` | Omit LLM stages when running `--core-only` or without Ollama. |

Do not delete arbitrary folders without reconciling imports and tests.

## Step 4: Extracting Patterns Elsewhere

If you reuse pieces of `infrastructure/` in another repo:

- **Vendor copy**: Copy `infrastructure/` wholesale; simplest, but merges from upstream are manual.
- **Partial extract**: Expect to fix imports and path assumptions (`projects/`, `output/`, repo root discovery).

Many modules assume paths resolved from the repository root via [`infrastructure/project/discovery.py`](../../infrastructure/project/discovery.py).

## Further Reading

- [Two-layer architecture](../architecture/two-layer-architecture.md)
- [New project setup checklist](../guides/new-project-setup.md)
- [Operations: Docker](docker.md)
- [Operational: Troubleshooting](../operational/troubleshooting/)
- [Operational: Build System](../operational/build/)
- [`infrastructure/AGENTS.md`](../../infrastructure/AGENTS.md)
