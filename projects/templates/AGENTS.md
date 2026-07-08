# Public Template Exemplars Knowledge Base

## Overview

`projects/templates/` contains the eighteen public canonical exemplar projects for
the template repository. This directory is public and tracked; private,
rotating, archived, active, or search-only project work belongs outside this
subtree and is guarded by `.gitignore`, `scripts/audit/check_tracked_projects.py`, and
`infrastructure.project.public_scope`.

Nearest child `AGENTS.md` files are authoritative for template-specific rules.
Use this file for shared exemplar parity, command selection, and escalation.

## Structure

```text
projects/templates/
├── template_active_inference/        # analytical + pymdp + sheaf + Lean/GNN
├── template_autopoiesis/             # combinatoric grammar generating whole runnable projects
├── template_autoresearch_project/    # deterministic AutoResearch loop
├── template_autoscientists/          # coordination-mechanism testbed
├── template_code_project/            # code-first numerical exemplar
├── template_eda_notebook/            # exploratory data analysis on tabular data
├── template_gold_refinement/         # metallurgical gold-refining analogy (ore → nine-nines)
├── template_literature_meta_analysis/ # reproducible literature meta-analysis (multi-engine retrieval)
├── template_madlib/                  # conditional token-injection manuscript
├── template_methods_paper/           # methods-paper exemplar: tested methodology DSL
├── template_newspaper/               # ReportLab newspaper layout engine
├── template_pools_rules_tools/       # fonds/rules/tools resource-pool integration (autopoietic)
├── template_prose_project/           # prose/references validation exemplar
├── template_search_project/          # literature search → BibTeX → LLM synthesis pipeline
├── template_sia/                     # fixture-backed SIA harness
├── template_storybook/               # full-page illustrated storybook PDF
├── template_template/                # meta-template introspection exemplar
└── template_textbook/                # modular textbook scaffold
```

Every exemplar also carries these agent-facing surfaces:

- `.agents/AGENTS.md` — per-template agent contract catalog
- `.agents/skills/<name>/SKILL.md` — Hermes/agentskills.io-compatible skill definition
- `.agents/skills/<name>/AGENTS.md` + `README.md` — skill folder contract

## Where To Look

| Task | Location | Notes |
| --- | --- | --- |
| Public roster | `../../infrastructure/project/public_scope.py` | Update generated docs after roster changes. |
| Exemplar selection | `../../docs/_generated/exemplar_roster.md` | Generated from README `## When to use this template`. |
| Shared project rules | `../AGENTS.md` | Confidentiality and lifecycle rules live there. |
| Shared design/browser QA | `DESIGN.md` | Applies to generated manuscript, web, and PDF outputs across all public templates. |
| Template-specific rules | `<template>/AGENTS.md` | Read this before editing that exemplar. |
| Agent skill definition | `<template>/.agents/skills/<name>/SKILL.md` | Hermes-compatible YAML frontmatter skill; load when working inside that exemplar. |
| Manuscript rules | `<template>/manuscript/AGENTS.md` | Token, figure, bibliography, and config rules. |
| Script ordering | `<template>/scripts/AGENTS.md` | Project scripts stay thin and may be order-sensitive. |
| Open work | `<template>/TODO.md` | Forward-only integrity/template-status ladder. |
| Fork config | `<template>/manuscript/config.yaml.example` | Copy-and-customize template with placeholder-safe values. |
| Output evidence | `<template>/output/` and repo `output/` | Disposable generated evidence; never hand-edit to pass gates. |

## Code Map

| Surface | Role |
| --- | --- |
| `template_active_inference/src/roadmap_tracks/` | Largest hotspot; promotion artifacts and validation coupling. |
| `template_active_inference/src/manuscript/sheaf/` | Dense sheaf manuscript semantics and track binding. |
| `template_autoresearch_project/src/` | Plan/evidence/claim/readiness loop with ML, diagnostics, security, and writers. |
| `template_code_project/src/__init__.py` | Centralized public API for the code exemplar. |
| `template_gold_refinement/src/` | Refinery pipeline (ore → nine-nines), karat grading, mega-madlib token composition. |
| `template_madlib/src/__init__.py` | Public authoring/evaluation API; large config/composition modules. |
| `template_newspaper/src/newspaper/` | Layout geometry, typography, components, and rendered page figures. |
| `template_textbook/src/` | Textbook paths, scaffold generation, visualization, and Mermaid helpers. |

## Conventions

- Run commands from the repository root (`../..` from here) unless a child
  `AGENTS.md` explicitly gives a project-local form.
- Generated manuscript, web, and PDF surfaces inherit the shared visual and
  browser-QA contract in `DESIGN.md` unless a child `AGENTS.md` states a
  narrower project-specific rule.
- All public templates must carry the canonical forkable surface:
  `README.md`, `AGENTS.md`, `TODO.md`, `pyproject.toml`, `.gitignore`,
  `.agents/` (skill catalog), `scripts/`, `src/`, `tests/`, `manuscript/config.yaml`,
  `manuscript/config.yaml.example`, `manuscript/references.bib`, and
  `manuscript/preamble.md`.
- `TODO.md` is future-only: current validation evidence first, then integrity
  gaps, configurable-surface gaps, documentation/signpost gaps,
  test/validator gaps, and an ordered improvement ladder.
- `manuscript/config.yaml` is the live source of truth for manuscript metadata,
  thresholds, paths, structural toggles, and project-specific controls.
- `manuscript/config.yaml.example` is the fork template. Keep it
  placeholder-safe and shape-specific; do not dump unrelated knobs into every
  exemplar.
- Scripts are thin orchestrators. Business logic belongs in `src/` or shared
  `infrastructure/`, not in `projects/templates/*/scripts/`.
- Measured counts, project rosters, and stage facts belong in generated docs,
  especially `docs/_generated/COUNTS.md` and
  `docs/_generated/active_projects.md`.
- Tests must use real files, real subprocesses, real generated artifacts, or
  deterministic fixtures when the child project says no mocks.
- Gate-like validators need negative controls where practical; they should fail
  on stale, missing, malformed, or unsupported evidence, not only accept the
  happy path.
- Registries, manifests, ledgers, configs, and generated variables are stronger
  evidence than prose lists. Update the source-of-truth artifact first, then
  regenerate downstream docs or manuscript outputs.
- Generated outputs, coverage HTML, local `.venv/`, `.codegraph/`, and render
  artifacts are not source of truth and must not be tracked.

## Anti-Patterns

- Do not add private, rotating, archived, or active work under this directory.
- Do not hard-code the public roster in prose when a generated doc or
  `PUBLIC_PROJECT_NAMES` can be referenced.
- Do not patch `output/` or `rendered/` to make validation pass; fix the source
  producer, config, or test oracle.
- Do not run all project test directories in one pytest process. Per-project
  `tests/conftest.py` package names collide; run one template per invocation.
- Do not treat optional live paths as default gates. Examples: Hermes/Ollama
  for `template_autoscientists`, optional sheaf tracks or Lean for
  `template_active_inference`.
- Do not infer `template_newspaper` layout success from source tests alone
  after layout/content changes; inspect rendered pages or generated artifacts.

## Commands

Run from the repository root:

```bash
uv run pytest projects/templates/<name>/tests --cov=projects/templates/<name>/src --cov-fail-under=90
uv run python -m infrastructure.validation.cli prerender projects/templates/<name>/manuscript --repo-root .
uv run python scripts/runner/execute_pipeline.py --project templates/<name> --core-only
uv run python scripts/pipeline/stage_02_analysis.py --project templates/<name>
uv run python scripts/pipeline/stage_03_render.py --project templates/<name>
uv run python scripts/pipeline/stage_04_validate.py --project templates/<name>
uv run python scripts/pipeline/stage_05_copy.py --project templates/<name>
uv run python scripts/pipeline/stage_01_test.py --project-only --all-projects --public-projects
uv run python scripts/audit/check_template_drift.py --strict
uv run python scripts/audit/check_tracked_projects.py
uv run python scripts/docgen/exemplar_roster.py --check
uv run python scripts/docgen/counts.py --check
uv run python -m infrastructure.skills check
```

For style/type checks, derive public CI source paths first:

```bash
uv run python -m infrastructure.project.public_scope source-paths
```

Then pass those paths to Ruff and mypy rather than inventing a stale allowlist.

## Notes

- `template_madlib` is in the public template scope even when its tree is newly
  added or locally untracked.
- `template_active_inference` and `template_textbook` have the deepest child
  AGENTS hierarchies. Read the nearest nested file before editing their
  manuscript, validation, Lean/GNN, roadmap, lab, question, or asset areas.
- Stage ordering comes from `infrastructure/core/pipeline/pipeline.yaml`, not
  only from numeric script prefixes.
- Keep dirty worktree discipline: preserve unrelated user changes and stage
  only the intended template/public-scope files when committing.
