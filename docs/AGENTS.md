# docs/ — Documentation Hub

## Overview

Technical guide for the `docs/` directory — the central documentation hub for the Research Project Template.

## Agents: Start Here

If you are an AI agent picking up work in this repo, orient through these four doors before touching code or docs:

1. **Discover every skill.** Read [`_generated/skills_index.md`](_generated/skills_index.md) — the generated catalog of every `SKILL.md` found under `infrastructure/`, `projects/`, `docs/prompts/`, and `.cursor/skills/`. It is the single inventory of what this repo can do.
2. **Find the agent-invocable CLI operations.** The machine-readable catalog of CLI operations (module, invocation, subcommands, exports) lives in [`../.cursor/operations_manifest.json`](../.cursor/operations_manifest.json). Regenerate or verify it with `uv run python -m infrastructure.skills operations-write` (write) and `uv run python -m infrastructure.skills operations-check` (verify against live discovery).
3. **Route workflow intents.** Send any research/manuscript/pipeline intent through the hub router [`prompts/SKILL.md`](prompts/SKILL.md), then follow the handoffs declared in [`prompts/MODE_REGISTRY.md`](prompts/MODE_REGISTRY.md). One intent → one child skill.
4. **THE TWO-TREE ROUTING RULE.** To **EDIT/extend an infrastructure module**, use that module's `infrastructure/<module>/SKILL.md`. To **RUN a research workflow**, use `docs/prompts/<skill>/SKILL.md`. Infrastructure skills are for changing the machinery; prompt skills are for operating it.

To compose a **custom** subset of pipeline stages rather than running the whole `--pipeline`, follow the **Workflow Composition Map**: [`prompts/COMPOSITION.md`](prompts/COMPOSITION.md).

## Directory Structure

| Directory | Purpose |
| ---------- | ------- |
| `core/` | Essential docs: usage guide, architecture overview, workflow |
| `guides/` | Skill-level guides (Levels 1-12) + new project setup checklist |
| `architecture/` | System design, two-layer architecture, thin orchestrator |
| `usage/` | Content authoring, formatting, visualization patterns |
| `operational/` | Runbooks, maintenance, configuration, Docker, logging, troubleshooting |
| `plans/` | Strategic plans and architecture decision records |
| `reference/` | API reference, glossary, FAQ, cheatsheet, workflows |
| `modules/` | Infrastructure module guides (see [modules/modules-guide.md](modules/modules-guide.md); package count drifts — re-derive from `infrastructure/` discovery) |
| `maintenance/` | Long-horizon maintenance: private-projects, ci-local, regression, archival, bundle |
| `development/` | Contributing, testing, security, roadmap |
| `best-practices/` | Best practices, version control, migration |
| `prompts/` | Agent workflow skills — hub [`prompts/SKILL.md`](prompts/SKILL.md); see [prompts/AGENTS.md](prompts/AGENTS.md) |
| `security/` | Security documentation and policies |
| `rules/` | Contributor norms — expanded standards; repo-root [`.cursorrules`](../.cursorrules) is the Cursor-facing summary |
| `audit/` | Generated, point-in-time audit snapshots; never hand-edit producer output |
| `images/` | Small public assets used by repository documentation, not manuscript figures |
| `streams/` | Timestamped notes for livestreams and recorded talks |
| `_generated/` | Machine-generated snippets; authoritative active `projects/` names in `active_projects.md` — link there instead of duplicating rosters in guides |

## Key Conventions

- **Public exemplars are generated scope:** tracked canonical templates are listed
  in [`_generated/active_projects.md`](_generated/active_projects.md). Use
  [`projects/templates/template_code_project/`](../projects/templates/template_code_project/)
  as the default concrete walkthrough; private lifecycle mirrors rotate locally.
- **CodeGraph is local-only:** `.codegraph/` is generated agent-navigation state; see [`guides/codegraph-local.md`](guides/codegraph-local.md) before documenting or initializing it.
- Each sub-directory has a `README.md` (user-facing index) and `AGENTS.md` (technical guide)
- `documentation-index.md` is a curated flat map of long-lived documentation;
  generated inventories and source-owned directory guides remain authoritative
  for their own scopes
- Cross-references use relative paths with descriptive link text
- Documentation is intended to be evergreen; when behaviour changes, we may include dated notes so it’s clear which guidance is newer.

## Review and evidence contract

Deep documentation review must follow the fact to its producer and verifier.
Do not resolve a contradiction by changing prose to match an accidental runtime
behavior when the code's docstring, public contract, and tests indicate the
opposite intent; record the discrepancy and repair the owning source or narrow
the claim.

| Surface | Producer / authority | Required review |
| --- | --- | --- |
| Commands, flags, defaults, precedence | CLI parser, config schema, implementation, focused tests | Execute or probe the exact path, including conflicting inputs and failure cases. |
| Generated repo facts | Producer named by [`_generated/AGENTS.md`](_generated/AGENTS.md) | Regenerate with the producer; never edit generated output directly. |
| Manuscript variables and statistics | Project analysis code and source artifacts, serialized to `output/data/manuscript_variables.json` | Trace every variable to inputs, estimand, sample size, uncertainty, units, rounding, and freshness. Source manuscript prose uses `{{TOKEN}}`; hydrated output is generated. |
| Figures and tables | Analysis code, figure/artifact registry, source data | Check data lineage, scales, labels, legends, uncertainty, palettes, resolution, panel ordering, and agreement among plot, caption, prose, and registry. |
| Captions and alt text | Manuscript source plus the rendered artifact | A caption interprets the display and states statistical context; alt text conveys the visual structure without pretending the caption alone is accessible text. |
| Scholarship and citations | Primary literature and bibliography records | Verify citation identity and support, qualify claim strength, disclose limitations and alternative explanations, and avoid citation laundering through secondary summaries. |
| Gates and release claims | Gate implementation, negative controls, fresh receipts, hosted CI, remote SHA | Name the verifier and a known-wrong test/fixture when claiming enforcement. Report local validation, hosted CI, approval, merge, publication, and archival state separately. |

When a value can change between runs, inject or generate it. When a statement is
interpretive, cite evidence and state its boundary. When a check is advisory,
do not describe it as a blocking gate.

### Documentation validation sequence

Run the smallest focused checks while editing, then the complete documentation
surface before handoff:

```bash
uv run python scripts/audit/lint_docs.py --json --repo-root .
uv run python scripts/audit/audit_documentation.py --format markdown
uv run python scripts/audit/check_template_drift.py --strict
uv run python scripts/docgen/counts.py --check
uv run python scripts/docgen/exemplar_roster.py --check
uv run python scripts/docgen/status_evidence.py --check
uv run python scripts/docgen/api_reference.py --check
uv run python -m infrastructure.skills check
uv run python -m infrastructure.skills check-contracts
```

The RedTeam audit is intentionally broad and advisory; triage its findings
rather than treating the number of heuristic matches as a quality score. The
other commands above fail on concrete drift. Changes to generated sources,
public behavior, or release contracts also require their focused tests and the
repository's normal pre-commit/pre-push checks.

## Entry Points

| Audience | Start Here |
| -------- | ---------- |
| New user | `core/how-to-use.md` → `guides/getting-started.md` |
| Developer | `core/architecture.md` → `architecture/two-layer-architecture.md` |
| **New project** | **`guides/new-project-setup.md`** → **`guides/new-project-one-shot-prompt.md`** (optional LLM scaffold) → `architecture/thin-orchestrator-summary.md` |
| Publication | `guides/publication-runbook.md` → `guides/publishing-guide.md` → `modules/guides/publishing-module.md` |
| Contributor | `development/contributing.md` → `development/testing/` |
| AI Agent | `prompts/SKILL.md` → `prompts/agentic-use/SKILL.md` → `rules/AGENTS.md` |
| Troubleshooter | `operational/troubleshooting/` → `reference/faq.md` |

## Learnings & Known Issues

Key discoveries from multi-project development are documented in:

- **[guides/new-project-setup.md](guides/new-project-setup.md)** — Comprehensive setup checklist with all pitfalls
- **[guides/manuscript-semantics.md](guides/manuscript-semantics.md)** — Canonical manuscript syntax (citations, cross-references, sections, `{{TOKEN}}` substitution) shared by public template exemplars; project-specific overlays live in `projects/templates/template_*/manuscript/SYNTAX.md`
- **[operational/troubleshooting/common-errors.md](operational/troubleshooting/common-errors.md)** — Pipeline-specific error patterns

### ⚠️ Critical Rule: Root Venv Must Include All Project Dependencies

If a project in `projects/<name>/` has its own `pyproject.toml` but **no `.venv/` directory**, every package listed in that `pyproject.toml#dependencies` must also appear in the **root** `pyproject.toml`. Project-local analysis scripts run under the root venv through `scripts/pipeline/stage_02_analysis.py` in this case.

**Symptom when violated:** `❌ <project>: 4 stages, 7.7s` — Stage 4 (Analysis) fails silently in < 1s. No import error surfaces in the console.

**Fix:** Add missing packages to root `pyproject.toml`, then `uv sync`.

**Root venv vs project `pyproject.toml`:**

| Scope | Notes |
| --- | --- |
| [`projects/templates/template_code_project/`](../projects/templates/template_code_project/) | Stable exemplar; often uses a local `projects/templates/template_code_project/.venv/`. |
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
- [documentation-index.md](documentation-index.md) — Curated documentation map
- [Root AGENTS.md](../AGENTS.md) — System-level documentation

## Typed-Subfolder Project Lifecycle

Project lifecycle state is expressed as **typed subfolders under `projects/`**. Public exemplars are always discovered/rendered; optional `active/` entries are discovered/rendered when present; simplified sidecar `working/` and `archive/` mirrors are non-rendered by default. Authoritative public roster: [`docs/_generated/active_projects.md`](_generated/active_projects.md).

| Subfolder | Purpose | Discovered + rendered? |
| ---------- | ------- | ------------------------ |
| `projects/templates/` | The git-tracked public exemplars (this repo) | ✅ Yes |
| `projects/active/` | Optional hot-seat render set — symlinks to deliberately reintroduced private `active/` | ✅ Yes when present |
| `projects/working/` | Simplified sidecar working set — symlinks, explicit targeted renders only | ❌ No |
| `projects/archive/` | Simplified sidecar archive — symlinks, historical/reference | ❌ No |

**Movement rules:**

- Only `projects/templates/*` and optional `projects/active/*` are discovered and rendered (qualified names `templates/<name>` and `active/<name>`).
- Private lifecycle projects live in the sibling `docxology/projects` repo. Its default folders are `working/` and `archive/`, symlinked into matching typed subfolders on every `./run.sh` (or `uv run python -m infrastructure.orchestration link-projects`). Render a working project explicitly with a lifecycle-qualified name such as `working/<name>`.
- The git-tracked public exemplars under `projects/templates/` never move — they are owned by this repo. Every other path under `projects/` is local-only and never committed (enforced by `scripts/audit/check_tracked_all.py`).

**Configuring the active directory (advanced):**

To run the pipeline against a non-default directory (e.g., for smoke-testing an in-progress project without moving it):

```python
from pathlib import Path

from infrastructure.core.pipeline import PipelineConfig, PipelineExecutor

config = PipelineConfig(
    project_name="my_wip_project",
    repo_root=Path("."),
    projects_dir="projects/working",  # override the default "projects"
)
executor = PipelineExecutor(config)
executor.execute_core_pipeline()
```

The `projects_dir` field on `PipelineConfig` defaults to `"projects"`, preserving the standard `./run.sh` behaviour. The resolved project root path is the read-only property `project_dir` (`repo_root / projects_dir / project_name`). Call sites and helpers that accept an explicit directory typically take a `projects_dir` string (or derive paths from `PipelineConfig`).
