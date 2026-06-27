# 🚀 Research Project Template

<!-- Badges are qualitative; measured coverage and test counts drift — use `uv run pytest` and CI for ground truth. See docs/RUN_GUIDE.md. -->
[![Build](https://img.shields.io/badge/build-docs%20%26%20CI-blue)](docs/RUN_GUIDE.md)
[![Coverage](https://img.shields.io/badge/coverage-see%20RUN__GUIDE%20%26%20CI-blue)](docs/RUN_GUIDE.md)
[![Tests](https://img.shields.io/badge/tests-pytest%20%28infra%20%2B%20project%29-blue)](docs/RUN_GUIDE.md)
[![Documentation](https://img.shields.io/badge/docs-documentation--index-lightgrey)](docs/documentation-index.md)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19139090.svg)](https://doi.org/10.5281/zenodo.19139090)

> **📄 Published**: [*A template/ approach to Reproducible Generative Research: Architecture and Ergonomics from Configuration through Publication*](https://zenodo.org/records/19139090) — DOI: [10.5281/zenodo.19139090](https://doi.org/10.5281/zenodo.19139090)
>
> **Template Repository** - Click "Use this template" to create a research project with this structure

## Quickstart

Just cloned the repo? Do this:

1. `git clone <this-repo> && cd template`
2. `uv sync` (installs deps via uv)
3. `./run.sh` (interactive menu) **or** `./run.sh --pipeline --project templates/template_code_project --core-only` (non-interactive, no LLM)
4. PDFs land in `output/templates/<project>/pdf/`. Logs in `output/templates/<project>/logs/`.
5. Run `./run.sh --help` for all flags. Always-present exemplars are listed in [`docs/_generated/active_projects.md`](docs/_generated/active_projects.md): `template_active_inference`, `template_autoresearch_project`, `template_autoscientists`, `template_code_project`, `template_gold_refinement`, `template_literature_meta_analysis`, `template_madlib`, `template_newspaper`, `template_prose_project`, `template_sia`, `template_template`, `template_textbook`. The search exemplar is an optional add-on under `projects/archive/template_search_project/`.

For deeper guidance see [`docs/guides/getting-started.md`](docs/guides/getting-started.md) and [`docs/RUN_GUIDE.md`](docs/RUN_GUIDE.md).

**Thin-orchestrator gates:** `uv run python scripts/check_template_drift.py --strict`, `uv run python scripts/gates/module_line_count_check.py`, `uv run python -m infrastructure.core.health` — details in [`docs/architecture/thin-orchestrator-summary.md`](docs/architecture/thin-orchestrator-summary.md).

**Assistants and editors:** [`.cursorrules`](.cursorrules) summarizes architecture and tooling for Cursor; [`CLAUDE.md`](CLAUDE.md) is the command cheat sheet; [`AGENTS.md`](AGENTS.md) is the full system manual (pipeline, validation, configuration). For routable agent workflows, start at [`docs/prompts/SKILL.md`](docs/prompts/SKILL.md) and the generated skill index [`docs/_generated/skills_index.md`](docs/_generated/skills_index.md).

**Contributors and CI:** GitHub Actions, Dependabot, and PR/issue templates live under [`.github/README.md`](.github/README.md) ([agent entry point](.github/README.md#agent--automation-entry-point), doc map, CI inventory) and [`.github/AGENTS.md`](.github/AGENTS.md) (job names, thresholds, troubleshooting).

<a id="migration-from-quadmath"></a>

**Local hooks:** After `uv sync`, run `pre-commit install` and `pre-commit install --hook-type pre-push` to mirror Ruff, mypy, Bandit, and smoke tests locally (see [`.pre-commit-config.yaml`](.pre-commit-config.yaml)).

A system for research and development projects. This template provides a test-driven structure with automated PDF generation, professional documentation, and validated build pipelines.

## 🧭 Positioning (honest framing)

> This is primarily **Daniel Ari Friedman's research operating system**, made public and Apache 2.0-licensed so other researchers can fork it if helpful. It is not a one-size-fits-all template — it is opinionated, Python+pytest+LaTeX-flavored, and tuned to the kind of work Daniel does (Active Inference, computational biology, cognitive security). Honest framing ages better than wishful adoption metrics.
>
> If your workflow looks similar (TDD-on-research-code, Markdown→PDF, multi-project monorepo, optional local-LLM draft assistance, deterministic + watermarked outputs, Zenodo DOI publishing), the template will probably save you time. If it doesn't look similar, a lighter alternative (Quarto, MyST, Cookiecutter-data-science) may serve you better. See [`MAINTAINERS.md`](MAINTAINERS.md) for ownership and [`STATUS.md`](STATUS.md) for per-subsystem freshness so you can judge what's actively maintained vs dormant.
>
> Long-horizon viability guides — toolchain migration, regression testing, archival redundancy, local CI, and the design for a future executable-bundle stage — live in [`docs/maintenance/`](docs/maintenance/).

## 🎯 What This Template Provides

This is a **GitHub Template Repository** that gives you:

- ✅ **Multi-project support** - Run multiple projects in one repository
- ✅ **Project structure** with clear separation of concerns
- ✅ **Test-driven development** setup with coverage requirements
- ✅ **Automated PDF generation** from markdown sources
- ✅ **Thin orchestrator pattern** for maintainable code
- ✅ **Methods orchestration** linking pipeline contracts, methods prose, artifacts, and evidence
- ✅ **Ready-to-use utilities** for any research project
- ✅ **Professional documentation** structure (full inventory: [`docs/documentation-index.md`](docs/documentation-index.md))
- ✅ **Advanced quality analysis** and document metrics
- ✅ **Reproducibility tools** for scientific workflows
- ✅ **Integrity verification** and validation
- ✅ **Publishing tools** for academic dissemination
- ✅ **Scientific development** best practices
- ✅ **Reporting** with error aggregation and performance metrics
- ✅ **Local Ollama workflow** documented in `infrastructure/llm/README.md` and `docs/operational/troubleshooting/llm-review.md`

## 🗺️ Choose Your Path

Pick the entry point that matches your goal:

- **New users** (write docs, generate PDFs): start with [Quickstart](#quickstart),
  then [`docs/guides/getting-started.md`](docs/guides/getting-started.md) and
  [`docs/reference/quick-start-cheatsheet.md`](docs/reference/quick-start-cheatsheet.md).
- **Developers** (figures, data analysis, automation):
  [`docs/core/architecture.md`](docs/core/architecture.md),
  [`docs/architecture/thin-orchestrator-summary.md`](docs/architecture/thin-orchestrator-summary.md),
  [`docs/guides/methods-orchestration.md`](docs/guides/methods-orchestration.md),
  [`docs/core/workflow.md`](docs/core/workflow.md),
  [`docs/guides/figures-and-analysis.md`](docs/guides/figures-and-analysis.md).
- **Contributors** (improve the template):
  [`docs/development/contributing.md`](docs/development/contributing.md),
  [`docs/development/code-of-conduct.md`](docs/development/code-of-conduct.md),
  [`docs/development/roadmap.md`](docs/development/roadmap.md),
  [`docs/development/security.md`](docs/development/security.md).
- **Advanced** (system internals, modules, deep technical dive):
  [`AGENTS.md`](AGENTS.md), [`docs/RUN_GUIDE.md`](docs/RUN_GUIDE.md),
  [`docs/modules/modules-guide.md`](docs/modules/modules-guide.md),
  [`docs/documentation-index.md`](docs/documentation-index.md).

## 🧭 Documentation Hub

**📚 [Documentation Index](docs/documentation-index.md)** | **📖 [Documentation Guide](docs/AGENTS.md)** | **🔍 [Quick Reference](docs/README.md)**

The template ships with a large documentation corpus under `docs/`. The full
hierarchical map (with mermaid diagram) lives in
[`docs/AGENTS.md`](docs/AGENTS.md); the authoritative per-file index lives in
[`docs/documentation-index.md`](docs/documentation-index.md) (rely on that
index, not a hard-coded file count, which drifts). Top-level layout:

- `docs/core/` — essential reading: how-to-use, architecture, workflow
- `docs/guides/` — progressive walkthroughs by skill level (1–12)
- `docs/operational/` — build, configuration, troubleshooting, performance
- `docs/reference/` — FAQ, cheatsheet, common workflows, API reference
- `docs/architecture/` — two-layer architecture, thin orchestrator, decision tree
- `docs/usage/` — examples, showcase, markdown writing guide
- `docs/modules/` — module-by-module guides
- `docs/development/` — contributing, testing, roadmap

## 🤖 Agentic operation and SKILLS

Agents should load the smallest applicable workflow before editing. The routing
surface is first-class and generated from live `SKILL.md` discovery:

- **Workflow router:** [`docs/prompts/SKILL.md`](docs/prompts/SKILL.md)
  (`template-workflows`) routes broad requests such as full audits, pipeline
  debugging, code changes, tests, validation, manuscript work, and release
  checks to exactly one child workflow.
- **Agentic-use hardening:**
  [`docs/prompts/agentic-use/SKILL.md`](docs/prompts/agentic-use/SKILL.md)
  covers skill inventory, routing checks, `.cursor/skill_manifest.json`, and
  generated skill-index maintenance.
- **Infrastructure module skills:** [`infrastructure/SKILL.md`](infrastructure/SKILL.md)
  is the Layer-1 hub; pair the relevant `infrastructure/<module>/SKILL.md`
  with that module's `AGENTS.md` before editing code.
- **Human skill index:** [`docs/_generated/skills_index.md`](docs/_generated/skills_index.md)
  lists all discovered skills. Regenerate after skill changes with
  `uv run python -m infrastructure.skills write-index`; refresh the editor
  manifest with `uv run python -m infrastructure.skills write`; verify both
  with `uv run python -m infrastructure.skills check` and
  `uv run python -m infrastructure.skills check-contracts`.

## 🔀 Multi-Project Support

The repo can host multiple research projects in parallel. Each project owns its
own `src/`, `tests/`, `manuscript/`, `scripts/`, and `output/` directory under
`projects/<name>/`. Layer-1 infrastructure is shared.

**Permanent canonical exemplars — always present and tracked in git:**

| Exemplar | Shape | Tests | Coverage |
|---|---|---|---|
| [`projects/templates/template_active_inference/`](projects/templates/template_active_inference/) | Active Inference multi-track (analytical + pymdp + sheaf manuscript + Lean/GNN/ontology) | see canonical facts | see canonical facts |
| [`projects/templates/template_autoresearch_project/`](projects/templates/template_autoresearch_project/) | AutoResearch-centric (deterministic plan/evidence/claim/artifact/readiness loop) | see canonical facts | see canonical facts |
| [`projects/templates/template_autoscientists/`](projects/templates/template_autoscientists/) | Coordination-mechanism testbed (deterministic ablatable agent-team primitives, honest no-speedup framing) | see canonical facts | see canonical facts |
| [`projects/templates/template_code_project/`](projects/templates/template_code_project/) | Code-centric (optimization + dashboard) | see canonical facts | see canonical facts |
| [`projects/templates/template_gold_refinement/`](projects/templates/template_gold_refinement/) | Metallurgical gold-refining analogy for manuscript composition (ore → smelting → assaying → cupellation → nine-nines certification, mega-madlib token injection) | see canonical facts | see canonical facts |
| [`projects/templates/template_literature_meta_analysis/`](projects/templates/template_literature_meta_analysis/) | Generic literature meta-analysis (multi-engine retrieval + de-dup + full-text + embeddings + bibliometrics; default term `modafinil`) | see canonical facts | see canonical facts |
| [`projects/templates/template_madlib/`](projects/templates/template_madlib/) | Conditional token-injection manuscript generator (config-owned lexicon, QA probes, authoring contract, and IMRAD hydration) | see canonical facts | see canonical facts |
| [`projects/templates/template_newspaper/`](projects/templates/template_newspaper/) | Newspaper layout engine (data-driven 12-page broadsheet from YAML via ReportLab) | see canonical facts | see canonical facts |
| [`projects/templates/template_prose_project/`](projects/templates/template_prose_project/) | Prose-centric (editorial review + BibTeX validation) | see canonical facts | see canonical facts |
| [`projects/templates/template_sia/`](projects/templates/template_sia/) | SIA harness (meta → target → feedback loop, fixture replay) | see canonical facts | see canonical facts |
| [`projects/templates/template_template/`](projects/templates/template_template/) | Meta-template (introspects infrastructure and public exemplar roster) | see canonical facts | see canonical facts |
| [`projects/templates/template_textbook/`](projects/templates/template_textbook/) | Book-length manuscript scaffold (data-driven parts → chapters → labs/question banks, fillable stubs) | see canonical facts | see canonical facts |

*Test and coverage figures are representative; confirm against [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md) after substantive changes.*

**Choosing an exemplar:** every exemplar README opens with a `## When to use this template` section, and the generated differentiation map in [`docs/_generated/exemplar_roster.md`](docs/_generated/exemplar_roster.md) collects them into one "copy THIS when…" table (regenerate with `uv run python scripts/generate_exemplar_roster_doc.py`; sync is test-enforced).

The permanent exemplars share the same core layout and verification checklist. The code/prose exemplars also carry the 12-file project `docs/` hub (`agent_instructions.md`, `style_guide.md`, `syntax_guide.md`, `testing_philosophy.md`, `rendering_pipeline.md`, `faq.md`, `quickstart.md`, `output_conventions.md`, `troubleshooting.md`, `architecture.md`, `AGENTS.md`, `README.md`). New projects copy whichever exemplar is closest in shape and adjust from there. See [`projects/AGENTS.md`](projects/AGENTS.md#permanent-canonical-exemplars-and-optional-search-add-on) for the full comparison.

Publication metadata for every public exemplar is generated from project config and sidecars into [`docs/_generated/publication_records.md`](docs/_generated/publication_records.md), and the GitHub-facing table in [`.github/README.md`](.github/README.md#published-exemplars--pipeline-productivity-advanced-provenance-and-autopoiesis) is auto-injected from that same source.

### Public Exemplar Outputs And Mirrors

Every canonical exemplar under `projects/templates/` is tracked in this
monorepo, including its project-local `output/` tree. The copied release
artifacts under `output/templates/<name>/` are tracked as well, so a clone of
[`docxology/template`](https://github.com/docxology/template) contains both the
source and the latest rendered public artifacts. Public output files above
50 MB remain excluded by the generated-artifact guard; private or rotating
project outputs remain blocked.

Each exemplar also has a standalone `docxology/template_*` GitHub repository
linked to its Zenodo concept and latest version DOI. The current matrix is
[`docs/_generated/publication_records.md`](docs/_generated/publication_records.md).
To regenerate any exemplar from the monorepo:

```bash
git clone https://github.com/docxology/template
cd template
uv sync
./run.sh --project templates/template_code_project --pipeline --core-only
uv run python scripts/04_validate_output.py --project templates/template_code_project
uv run python scripts/05_copy_outputs.py --project templates/template_code_project
```

Replace `template_code_project` with any public exemplar name from the table
above. The standalone repositories are publication mirrors; use this monorepo
when you need the shared infrastructure, full render pipeline, or
cross-template validation.

The canonical exemplars also ship project-local composability overlays:
`domain_profile.yaml` declares review gates, source policy, artifact
expectations, and benchmark rubric preferences; `experiment_plan.yaml`
declares design-validation conditions, primary metric direction, expected
figures/tables, baselines, and ablations. These files are declarative inputs
for validation and benchmark tooling; they do not generate experiments or run
autonomous agents.

> **🔒 Confidentiality.** This is a **public** template repo. Only the
> canonical exemplars above (under `projects/templates/`) are git-tracked/pushed
> — `.gitignore` ignores `projects/*` and negates only `projects/templates/`. Any
> project you add under `projects/` (research, client, confidential, or the
> optional local-only `template_search_project` literature-search exemplar that
> rests in [`projects/archive/`](projects/archive/template_search_project/)) stays
> **local-only and is never committed**; `scripts/check_tracked_projects.py`
> blocks any accidental commit in the pre-push hook and CI. Copy
> `template_search_project` under `projects/active/` locally to exercise literature
> discovery, then never commit it.

**Private lifecycle projects.** In Daniel's working checkout, confidential
projects live outside this public repo at `$TEMPLATE_PRIVATE_PROJECTS_ROOT`.
The simplified sidecar uses `working/` and `archive/`; optional `ongoing/`
(long-lived projects with no publication target) plus legacy
`active/`, `published/`, and `other/` folders are still supported when present.
`run.sh` and `python -m infrastructure.orchestration` auto-sync existing folders
into matching typed subfolders under `projects/`: `working/*` into
`projects/working/*`, `ongoing/*` into `projects/ongoing/*`, `archive/*` into
`projects/archive/*`, and optional
`active/*` into `projects/active/*`. `templates/` and optional `active/` links
behave like native rendered entries; `working/`, `ongoing/`, and `archive/` links are visible
for explicit targeted work but are not default-rendered. Inspect without changing
the tree: `uv run python -m infrastructure.orchestration link-projects --dry-run`.
Override the sibling path with `TEMPLATE_PRIVATE_PROJECTS_ROOT` or
`.private_projects_root`; disable auto-sync with `TEMPLATE_SKIP_LINK_SYNC=1`.
The symlinked project keeps working outputs at `projects/<subfolder>/<name>/output/`
(the private target), while final deliverables still copy to
`output/<subfolder>/<name>/` in this template checkout.

Other entries rotate between `projects/working/` and `projects/archive/` as work
progresses. Never hard-code their paths in long-lived docs — consult
[`docs/_generated/active_projects.md`](docs/_generated/active_projects.md)
(authoritative public scope, regenerated from `infrastructure.project.public_scope`) and
[`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md)
instead.

**Common commands:**

```bash
./run.sh                                     # Interactive project selection
./run.sh --project templates/template_code_project --pipeline
./run.sh --all-projects --pipeline           # All discovered projects sequentially
./secure_run.sh --steganography-only --project templates/template_code_project  # Re-watermark PDFs
mkdir -p projects/my_research/{src,tests,manuscript,scripts}  # Scaffold new project
```

**Lifecycle:** rendered = `projects/templates/` plus optional `projects/active/`
(discovered, executed). The simplified private sidecar normally uses
`working/` and `archive/` (plus optional `ongoing/` for long-lived work with no
publication target); render sidecar projects explicitly with a qualified
name such as `working/{name}` or `ongoing/{name}`. See [`projects/PROJECTS_PARADIGM.md`](projects/PROJECTS_PARADIGM.md)
for lifecycle, slug rules, and discovery semantics.

## 🚀 Quick Start {#quick-start}

See the [Quickstart](#quickstart) at the top of this file for the canonical
clone-to-PDF flow. For headless cloud deployment use
[`docs/CLOUD_DEPLOY.md`](docs/CLOUD_DEPLOY.md) (uv is installed automatically
when you run `./run.sh --pipeline`). Beginner walkthrough:
[`docs/guides/getting-started.md`](docs/guides/getting-started.md). One-page
command reference:
[`docs/reference/quick-start-cheatsheet.md`](docs/reference/quick-start-cheatsheet.md).
Twelve-level usage guide: [`docs/core/how-to-use.md`](docs/core/how-to-use.md).

## System Status

Current state is captured in `docs/_generated/COUNTS.md` (updated from discovery, test runs, and CI configuration).

Key elements:
- Active projects listed via `discover_projects()`
- Coverage enforced at 60% (infrastructure) and 90% (projects)
- Tests run with real data and computations
- Commands standardized to `uv run`
- Outputs organized per project under `output/{name}/`

See `docs/_generated/COUNTS.md` and `docs/development/testing/testing-guide.md` for details.

## 🎓 Skill-Based Learning Paths

Twelve progressive levels — Document Creation (1–3), Figures & Automation (4–6),
Test-Driven Development (7–9), System Architecture (10–12) — are documented
end-to-end in [`docs/core/how-to-use.md`](docs/core/how-to-use.md). Per-band
walkthroughs: [`docs/guides/getting-started.md`](docs/guides/getting-started.md),
[`docs/guides/figures-and-analysis.md`](docs/guides/figures-and-analysis.md),
[`docs/guides/testing-and-reproducibility.md`](docs/guides/testing-and-reproducibility.md),
[`docs/guides/extending-and-automation.md`](docs/guides/extending-and-automation.md).

## 🏗️ Project Structure

Two-layer architecture:

- **Layer 1 — `infrastructure/`** (generic, reusable): build, validation,
  rendering, LLM, publishing, etc. Plus `scripts/` (entry-point orchestrators)
  and `tests/` (infrastructure tests, ≥60 % coverage).
- **Layer 2 — `projects/<name>/`** (project-specific, customizable): `src/`
  (algorithms, ≥90 % coverage), `tests/`, `scripts/` (thin orchestrators),
  `manuscript/` (markdown sections + `config.yaml`).
- **Output** lands under `output/<name>/{pdf,figures,data,reports}/`; all of
  `output/` is disposable and regeneratable.
- **Docs** live under `docs/` (full hierarchy in
  [`docs/AGENTS.md`](docs/AGENTS.md)); per-directory `AGENTS.md` files document
  every leaf.

### System Architecture Overview

A short summary lives here; full architecture diagrams (system overview,
module-dependency graph, per-stage data flow, configuration-system flow) are
maintained in [`AGENTS.md`](AGENTS.md#core-architecture) and
[`docs/core/architecture.md`](docs/core/architecture.md). In short:

- **Entry points:** `./run.sh` (interactive or `--pipeline`) and
  `uv run python scripts/execute_pipeline.py --project <name> [--core-only]`;
  numbered orchestrators under `scripts/` include `00_*.py` through `07_*.py` (setup → copy, LLM, executive report — see [`scripts/AGENTS.md`](scripts/AGENTS.md)).
- **Orchestration:** the pipeline runs Setup → Tests → Analysis → Render →
  Validate → Copy, with optional LLM Review and LLM Translations stages.
- **Core systems:** importable `infrastructure/` packages (Layer 1; live list
  in [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md))
  plus per-project `projects/{name}/src/` algorithms (Layer 2); see
  [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md) for
  the live module list.
- **Data flow:** project source + manuscript markdown + `config.yaml` flow
  through the pipeline into `output/<name>/{pdf,figures,data,reports}/`.
- **Quality assurance:** infra ≥60 % and project ≥90 % coverage gates,
  no-mocks policy, deterministic seeds, real PDF/markdown validation.
- **Configuration:** `projects/{name}/manuscript/config.yaml` plus environment
  overrides feed PDF metadata, LaTeX preamble, figure labels, and validation
  rules.

**Directory Overview with Documentation Links:**

| Directory | Purpose | Documentation |
| --- | --- | --- |
| **`infrastructure/`** | Generic build/validation tools (Layer 1) | [infrastructure/AGENTS.md](infrastructure/AGENTS.md) |
| **`scripts/`** | Entry point orchestrators | [scripts/AGENTS.md](scripts/AGENTS.md) |
| **`tests/`** | Infrastructure test suite | [tests/AGENTS.md](tests/AGENTS.md) |
| **`projects/{name}/src/`** | Project-specific scientific code (Layer 2) | Per-project `AGENTS.md` |
| **`projects/{name}/tests/`** | Project test suite | Per-project `AGENTS.md` |
| **`docs/`** | **Documentation hub** | **[docs/documentation-index.md](docs/documentation-index.md)** |
| **`projects/{name}/manuscript/`** | Research manuscript sections | Per-project `AGENTS.md` |
| **`output/`** | Generated outputs (disposable) | Regenerated by build pipeline |

**📚 Explore Documentation:** See **[docs/documentation-index.md](docs/documentation-index.md)** for documentation structure

## 🔑 Key Architectural Principles

The repository follows a **thin orchestrator pattern**: business logic lives
only in `infrastructure/` and `projects/{name}/src/`; scripts coordinate, never
implement. Tests use real data (no mocks), with strict coverage gates. Full
narrative + benefits:
[`docs/architecture/thin-orchestrator-summary.md`](docs/architecture/thin-orchestrator-summary.md),
[`docs/core/architecture.md`](docs/core/architecture.md).

## ✨ Key Features

- **Test-driven development** with ≥60 % infra and ≥90 % project coverage gates
  ([`docs/core/workflow.md`](docs/core/workflow.md)).
- **Automated script execution** via thin-orchestrator scripts under
  `projects/{name}/scripts/` ([`scripts/AGENTS.md`](scripts/AGENTS.md)).
- **Markdown-to-PDF pipeline** with cross-referenced manuscripts and figure
  integration ([`docs/usage/markdown-template-guide.md`](docs/usage/markdown-template-guide.md),
  [`docs/modules/pdf-validation.md`](docs/modules/pdf-validation.md)).
- **Validated build system** with 12 declared stages, a default 10-stage
  core+LLM path, an 8-stage `--core-only` path, and CI gates
  ([`docs/RUN_GUIDE.md`](docs/RUN_GUIDE.md)).
- **Generic + reusable** — drop the same `infrastructure/` into any project that
  follows the layout ([`docs/usage/template-description.md`](docs/usage/template-description.md)).

## 🔒 Security & Monitoring

LLM input sanitization (`infrastructure.llm.core.sanitization`), security
validators (`infrastructure.core.security`), runtime health checks
(`infrastructure.core.runtime.health_check`), rate limiting, and HTTP security
headers. Full surface and worked usage examples:
[`docs/development/security.md`](docs/development/security.md).

## 🛠️ Installation & Setup

Prerequisites: `pandoc` and a TeX distribution (`texlive-xetex` on Debian/Ubuntu,
MacTeX on macOS). Python deps install with `uv sync` (project interpreter is
`.venv/bin/python`; the template targets Python 3.10+ (`requires-python` in
[`pyproject.toml`](pyproject.toml)) and CI tests 3.10–3.12, with
[`.python-version`](.python-version) pinning 3.12 as the local default). Add per-project deps with
`uv run python scripts/maintenance/manage_workspace.py add <package> --project <name>`. To
generate a manuscript, follow the [Quickstart](#quickstart) at the top.

## 🐳 Docker Support

`docker-compose up` (or `docker build -t research-template . && docker run -it
research-template`) builds a reproducible image with pandoc, TeX, Ollama LLM
server support, persistent model/output volumes, and hot-reload. See
`Dockerfile` and `docker-compose.yml`.

## 🔧 Customization

### Project Metadata Configuration

Two configuration paths exist: edit `projects/{name}/manuscript/config.yaml`
(recommended) **or** export `AUTHOR_NAME` / `AUTHOR_ORCID` / `AUTHOR_EMAIL` /
`PROJECT_TITLE` / `DOI` environment variables (env vars override the YAML file).
The YAML schema (paper title, authors with ORCID, publication DOI, keywords,
optional LLM translations block) and a worked example are documented once in
[`CLAUDE.md`](CLAUDE.md#configuration) and
[`AGENTS.md`](AGENTS.md#configuration-system); both files also list every
available field. See `projects/{name}/manuscript/config.yaml.example` for the full
template. Applied configuration drives PDF metadata, LaTeX document properties
(see [`docs/reference/copypasta.md`](docs/reference/copypasta.md) for preamble
examples), generated file headers, and cross-reference systems.

### Adding Project-Specific Scripts

Place Python scripts under `projects/{name}/scripts/`. They must follow the
**thin orchestrator pattern**: import computation from `projects/{name}/src/`
or `infrastructure/`, handle only I/O / visualization / orchestration, print
output paths to stdout for manifest collection, and never implement algorithms
inline. Worked examples and the full pattern walkthrough live in
[`scripts/AGENTS.md`](scripts/AGENTS.md) and
[`docs/architecture/thin-orchestrator-summary.md`](docs/architecture/thin-orchestrator-summary.md).

### Manuscript Structure

Per-project manuscript files live in `projects/{name}/manuscript/`:
`config.yaml`, `preamble.md`, zero-padded numbered chapter files
(`00_abstract.md` onward), optional `S01_*.md` supplements, and
`99_references.md`. Exact chapter slugs vary per project — the canonical
exemplar is [`projects/templates/template_code_project/manuscript/`](projects/templates/template_code_project/manuscript/);
the numbering system and slug rules are authoritative in
[`docs/usage/manuscript-numbering-system.md`](docs/usage/manuscript-numbering-system.md).

## 📊 Testing

TDD with strict coverage gates: **infrastructure ≥ 60 %**, **projects ≥ 90 %**.
No mocks — tests use real data, real files, `pytest-httpserver` for HTTP. The
project pipeline runs a focused `pipeline-smoke` infrastructure contract plus
the selected project's full coverage suite, so ordinary renders do not rerun
the entire repository test matrix. Run the full infrastructure gate explicitly
with `uv run python scripts/01_run_tests.py --infra-only --infra-scope full`;
run a project suite with `uv run python scripts/01_run_tests.py --project-only
--project <name>`. Per-suite commands and coverage report flags are documented in
[`tests/AGENTS.md`](tests/AGENTS.md) and
[`docs/development/testing/testing-guide.md`](docs/development/testing/testing-guide.md);
live coverage / test counts live in
[`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md).

## Output

Working outputs: `projects/{name}/output/` (disposable). Final deliverables:
`output/{name}/{pdf,figures,data,reports}/`. Multi-project mode adds
`output/executive_summary/`. All of `output/` is regenerated by the pipeline.

## 🔍 How It Works

Two entry points — `./run.sh` (interactive or `--pipeline`) and
`uv run python scripts/execute_pipeline.py --project <name> [--core-only]`.

> **Pipeline (canonical phrasing — keep in sync with CLAUDE.md and AGENTS.md):** The default [`pipeline.yaml`](infrastructure/core/pipeline/pipeline.yaml) declares **12 named stages**: 8 core stages, 2 optional LLM stages, and 2 opt-in bundle/archival stages. Default full runs include the 10 core+LLM stages (`Clean Output Directories` plus nine numbered stages). `--core-only` runs **8 stages** by excluding the two LLM-tagged stages. Bundle and archival stages are declared for contracts but invoked separately when needed.

<!-- BEGIN:STAGE_TABLE -->
<!-- This block is generated from [`infrastructure/core/pipeline/pipeline.yaml`](infrastructure/core/pipeline/pipeline.yaml) by `scripts/generate_stage_table_doc.py`. Do not hand-edit. Stage indices are **0-based positions in the YAML** and intentionally do **not** match the `scripts/NN_*.py` numeric prefixes (for example, stage 9 runs `05_copy_outputs.py`). -->

| Stage | Script | Tags | Failure mode |
| ----- | ------ | ---- | ------------ |
| **0** Clean Output Directories | built-in `_run_clean_outputs` | `core`, `clean` | soft fail |
| **1** Environment Setup | `00_setup_environment.py` | `core` | hard fail |
| **2** Infrastructure Tests | `01_run_tests.py --infra-only --verbose --infra-scope pipeline-smoke` | `core`, `tests` | configurable tolerance |
| **3** Project Tests | `01_run_tests.py --project-only --verbose` | `core`, `tests` | configurable tolerance |
| **4** Project Analysis | `02_run_analysis.py` | `core` | hard fail |
| **5** PDF Rendering | `03_render_pdf.py` | `core` | hard fail |
| **6** Output Validation | `04_validate_output.py` | `core` | warning + report |
| **7** LLM Scientific Review | `06_llm_review.py --reviews-only` | `llm` | skipped if Ollama absent |
| **8** LLM Translations | `06_llm_review.py --translations-only` | `llm` | skipped if Ollama absent |
| **9** Copy Outputs | `05_copy_outputs.py` | `core` | soft fail |
| **10** Executable Bundle | `08_executable_bundle.py` | `bundle` | soft fail |
| **11** Archival Publication | `09_archive_publication.py` | `archival` | soft fail |
<!-- END:STAGE_TABLE -->

Full per-stage flowchart, failure/skip transitions, and the script-to-stage
mapping for `--core-only` live in [`AGENTS.md`](AGENTS.md#pipeline-stages) and
[`docs/RUN_GUIDE.md`](docs/RUN_GUIDE.md). Workflow narrative:
[`docs/core/workflow.md`](docs/core/workflow.md). Architecture narrative:
[`docs/core/architecture.md`](docs/core/architecture.md).

## 📚 Documentation Index

The full per-file documentation index lives in
[`docs/documentation-index.md`](docs/documentation-index.md) (authoritative;
counts drift, so it is not duplicated here). Top-level entry points:

- **System reference:** [`AGENTS.md`](AGENTS.md), [`CLAUDE.md`](CLAUDE.md), [`docs/AGENTS.md`](docs/AGENTS.md)
- **Walkthroughs:** [`docs/guides/getting-started.md`](docs/guides/getting-started.md),
  [`docs/core/how-to-use.md`](docs/core/how-to-use.md) (12 skill levels),
  [`docs/reference/quick-start-cheatsheet.md`](docs/reference/quick-start-cheatsheet.md)
- **Architecture:** [`docs/core/architecture.md`](docs/core/architecture.md),
  [`docs/architecture/thin-orchestrator-summary.md`](docs/architecture/thin-orchestrator-summary.md),
  [`docs/architecture/two-layer-architecture.md`](docs/architecture/two-layer-architecture.md)
- **Pipeline & build:** [`docs/RUN_GUIDE.md`](docs/RUN_GUIDE.md),
  [`docs/CLOUD_DEPLOY.md`](docs/CLOUD_DEPLOY.md)
- **Modules:** [`docs/modules/modules-guide.md`](docs/modules/modules-guide.md),
  [`infrastructure/AGENTS.md`](infrastructure/AGENTS.md)
- **Quality / testing:** [`tests/AGENTS.md`](tests/AGENTS.md),
  [`docs/development/testing/testing-guide.md`](docs/development/testing/testing-guide.md)
- **Agent code navigation:** [`docs/guides/codegraph-local.md`](docs/guides/codegraph-local.md),
  [`docs/guides/leann-local.md`](docs/guides/leann-local.md)
  (optional local indexes; never committed artifacts)
- **Best practices:** [`docs/best-practices/best-practices.md`](docs/best-practices/best-practices.md)
- **Live facts (auto-derived):** [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md),
  [`docs/_generated/active_projects.md`](docs/_generated/active_projects.md)
- **Per-directory `AGENTS.md`** files in `infrastructure/`, `scripts/`, `tests/`, `docs/`, and every `projects/{name}/{src,scripts,tests,manuscript}/`.

## 🤝 Contributing

**[contribution guide](docs/development/contributing.md)** | **[Code of conduct](docs/development/code-of-conduct.md)** | **[Roadmap](docs/development/roadmap.md)**

We welcome contributions! To contribute:

1. Ensure all tests pass with coverage requirements met - [Testing Guide](tests/AGENTS.md)
2. Follow the established project structure - [Architecture](docs/core/architecture.md)
3. Add tests for new functionality - [Workflow](docs/core/workflow.md)
4. Update documentation as needed - [Documentation Guide](docs/AGENTS.md)
5. **Maintain thin orchestrator pattern** - scripts use src/ methods - [Pattern Guide](docs/architecture/thin-orchestrator-summary.md)

**Recent Improvements:**

- Build system optimizations - [Performance Optimization](docs/operational/config/performance-optimization.md)
- Test suite enhancements
- Simplified directory structure with markdown/ elimination

## 📄 License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

## 📚 Citation

The machine-readable [`CITATION.cff`](CITATION.cff) is the single source of
truth (GitHub's "Cite this repository" widget reads it). If you use this
template in your research, please cite:

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19139090.svg)](https://doi.org/10.5281/zenodo.19139090)

Cite the current release. Earlier versions retain their own Zenodo DOIs;
the version-independent concept DOI always resolves to the latest.

**BibTeX:**

```bibtex
@software{friedman_template_2026,
  author    = {Daniel Ari Friedman},
  title     = {A template/ approach to Reproducible Generative Research:
               Architecture and Ergonomics from Configuration through Publication},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.19139090},
  url       = {https://doi.org/10.5281/zenodo.19139090}
}
```

**Plain text:**
Daniel Ari Friedman. (2026). *A template/ approach to Reproducible Generative
Research: Architecture and Ergonomics from Configuration through Publication.*
Zenodo. <https://doi.org/10.5281/zenodo.19139090>

## 🆘 Troubleshooting

Common issue catalog — failing tests, missing pandoc/xelatex, PDF quality, LLM
unavailability — lives in
[`docs/operational/troubleshooting/README.md`](docs/operational/troubleshooting/README.md)
and [`docs/reference/faq.md`](docs/reference/faq.md). Pipeline entry points and
flags: [`docs/RUN_GUIDE.md`](docs/RUN_GUIDE.md). PDF validator:
[`docs/modules/pdf-validation.md`](docs/modules/pdf-validation.md).

## 🔄 Migration from Other Projects

To adapt this template: copy `infrastructure/` and `scripts/`, mirror the
`projects/{name}/{src,tests,scripts,manuscript}/` layout, adopt
`config.yaml` (see [`AGENTS.md`](AGENTS.md#configuration-system)), and validate by
running the pipeline. Worked examples:
[`docs/usage/examples.md`](docs/usage/examples.md),
[`docs/best-practices/migration-guide.md`](docs/best-practices/migration-guide.md).

## 🏗️ Architecture Benefits

Thin orchestrator pattern delivers single-source-of-truth business logic,
high testability (≥90 % project coverage), reusability across projects,
and CI-gated quality. Full benefits + rationale:
[`docs/core/architecture.md`](docs/core/architecture.md).

---

## Quick Navigation by Task

| Task | Start here |
| --- | --- |
| **Assistants / Cursor** | [`.cursorrules`](.cursorrules), [`CLAUDE.md`](CLAUDE.md), [`AGENTS.md`](AGENTS.md#for-assistants-and-automation) |
| Write documents | [`docs/guides/getting-started.md`](docs/guides/getting-started.md), [`docs/usage/markdown-template-guide.md`](docs/usage/markdown-template-guide.md) |
| Add figures | [`docs/guides/figures-and-analysis.md`](docs/guides/figures-and-analysis.md), [`docs/usage/visualization-guide.md`](docs/usage/visualization-guide.md) |
| Fix issues | [`docs/operational/troubleshooting/README.md`](docs/operational/troubleshooting/README.md), [`docs/reference/faq.md`](docs/reference/faq.md) |
| Understand architecture | [`docs/core/architecture.md`](docs/core/architecture.md), [`docs/architecture/two-layer-architecture.md`](docs/architecture/two-layer-architecture.md) |
| Configure system | [`docs/operational/config/configuration.md`](docs/operational/config/configuration.md), [`AGENTS.md`](AGENTS.md) |
| Run pipeline | [`docs/RUN_GUIDE.md`](docs/RUN_GUIDE.md) |
| Contribute code | [`docs/development/contributing.md`](docs/development/contributing.md), [`docs/rules/AGENTS.md`](docs/rules/AGENTS.md) |
| Find all docs | [`docs/documentation-index.md`](docs/documentation-index.md) |

---

## 🎉 Get Started Now

**Ready to begin?** Choose your path:

1. **New User?** → Start with **[Quick Start](#quick-start)** or **[docs/guides/getting-started.md](docs/guides/getting-started.md)**
2. **Developer?** → Read **[docs/core/architecture.md](docs/core/architecture.md)** and **[docs/core/workflow.md](docs/core/workflow.md)**
3. **Need Help?** → Check **[docs/reference/faq.md](docs/reference/faq.md)** or **[docs/operational/troubleshooting/README.md](docs/operational/troubleshooting/README.md)**
4. **Explore All Docs?** → Browse **[docs/documentation-index.md](docs/documentation-index.md)**

**📚 Documentation Hub:** All documentation is organized in the **[docs/](docs/)** directory with guides for every aspect of the template.
