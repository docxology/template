# Infrastructure Module Reference

This section inventories every Layer‑1 subdirectory returned by `28` `discover_infrastructure_modules(repo_root)`. File totals use `662` Python sources across infra + `8,583` infra tests guarding them. Documentation Duality = paired `README.md` + `AGENTS.md`; optional `SKILL.md` manifests feed `python -m infrastructure.skills`.

| Module | Python Files | Has AGENTS.md | Has README.md | Key Exports |
|--------|:-----------:|:-------------:|:-------------:|-------------|
| `autoresearch` | 10 | ✓ | ✓ | `build_autoresearch_plan`, readiness validation CLI |
| `benchmark` | 3 | ✓ | ✓ | Template harness scoring + comparative gates |
| `config` | 0 | ✓ | ✓ | Repository defaults + hardened templates |
| `core` | 112 | ✓ | ✓ | `get_logger`, `load_config`, `TemplateError` |
| `docker` | 0 | ✓ | ✓ | Containerisation scaffolding |
| `doctor` | 14 | ✓ | ✓ | Checkout diagnose/fix/undo repairs |
| `documentation` | 13 | ✓ | ✓ | `FigureManager`, `generate_glossary` |
| `fonds` | 6 | ✓ | ✓ | — |
| `llm` | 54 | ✓ | ✓ | Ollama helpers, sanitization, review + translation pipelines |
| `logrotate.d` | 0 | ✓ | ✓ | Rotation snippets (documentation-first) |
| `methods` | 5 | ✓ | ✓ | `build_methods_orchestration_plan`, methods-stage contracts + validation |
| `orchestration` | 9 | ✓ | ✓ | `PipelineRunner`, entry point for `./run.sh` |
| `project` | 27 | ✓ | ✓ | `discover_projects`, workspace management |
| `prose` | 9 | ✓ | ✓ | Markdown readability + prose tooling |
| `provenance` | 7 | ✓ | ✓ | — |
| `publishing` | 74 | ✓ | ✓ | Zenodo, executable bundle, archival targets |
| `reference` | 16 | ✓ | ✓ | BibTeX models, parsers, converters |
| `rendering` | 60 | ✓ | ✓ | PDF/HTML/slide rendering, Pandoc filters |
| `reporting` | 57 | ✓ | ✓ | Coverage parsers, dashboards, executive artefacts |
| `research` | 3 | ✓ | ✓ | — |
| `rules` | 6 | ✓ | ✓ | — |
| `scientific` | 4 | ✓ | ✓ | `check_numerical_stability`, `benchmark_function` |
| `search` | 62 | ✓ | ✓ | `infrastructure.search.literature` clients + cache |
| `sia` | 10 | ✓ | ✓ | Self-Improving-AI loop: task validation, harness, metric capture |
| `skills` | 7 | ✓ | ✓ | `discover_skills`, SKILL manifest regeneration |
| `steganography` | 13 | ✓ | ✓ | Watermark overlays + hash manifests |
| `tools` | 6 | ✓ | ✓ | — |
| `validation` | 75 | ✓ | ✓ | PDF + Markdown + integrity CLIs |

## Alphabetical summaries

Below, `${module_*_python_file_count}` placeholders expand per subdirectory at render-time.

### `infrastructure.autoresearch` (10 files)

Readiness planner, validation CLI, and report models for AutoResearch-style project promotion (`infrastructure/autoresearch/`).

### `infrastructure.benchmark` (3 files)

Template harness scoring and comparative gate helpers exercised in CI smoke paths.

### `infrastructure/config` (non-package subdirectory)

Repository-wide YAML templates and secure manifests (`.env.template`, hardened defaults referenced by Docker + CLI). `config/` carries no `__init__.py`, so it is a configuration subdirectory rather than an importable package.

### `infrastructure.core` (112 files)

Checkpointing, logging, pipeline YAML parsing, telemetry bridges, filesystem helpers, hardened exceptions. Everything else imports logging + error taxonomy from here first.

### `infrastructure.doctor` (14 files)

Checkout diagnose/fix/undo repairs for broken local workspace states.

### `infrastructure.docker` (0 files)

Pinned images / compose scaffolding for reproducible CI + remote builds.

### `infrastructure.documentation` (13 files)

Figure registries plus glossary tooling feeding manuscript automation.

### `infrastructure.fonds` (6 files)

Resource pool management for curated fonds (tracked reference datasets, bibliographic collections, and evidence corpora). Fonds mirror `projects/templates/` with git-tracked `templates/*` exemplars and sidecar-linked private lifecycle folders.

### `infrastructure.llm` (54 files)

Ollama integrations, sanitization adapters, templated reviewer flows. **Literature ingestion now lives primarily in `search/literature` + citation helpers in `reference/`.**

### `infrastructure.methods` (5 files)

Deterministic methods-orchestration contracts (`MethodStage`, `MethodsOrchestrationPlan`, `MethodsIssue`): builds and validates an ordered methods plan for a research project so the manuscript's "Methods" track stays bound to executable stages.

### `infrastructure.orchestration` (9 files)

`python -m infrastructure.orchestration` exposes interactive menus, subprocess wiring for thin shell wrappers (`run.sh`, `secure_run.sh`), and stubs used in CI for menu parsing tests.

### `infrastructure.project` (27 files)

Canonical discovery (`discover_projects`) enforcing `src/` + `tests/`, slug validation, nested WIP namespaces.

### `infrastructure.prose` (9 files)

Readability metrics + Markdown tooling for prose-centric manuscripts / CI gates.

### `infrastructure.provenance` (7 files)

Content-addressed provenance DAG. Records artifact lineage (which run produced which file, from which inputs) as a verifiable graph of artifact/run/source/claim nodes connected by produced/consumed/derived-from/supports/refutes edges. Includes a structured Review system with severity (blocking/major/minor/info) and verdict (refutes/supports). Features a CLI and pipeline integration hooks for automatic lineage recording after every stage.

### `infrastructure.publishing` (74 files)

Metadata models, APA/BibTeX/MLA formatters, optional Zenodo clients.

### `infrastructure.reference` (16 files)

Citation/BibTeX parsing + conversion utilities leveraged by manuscripts and retrieval scripts.

### `infrastructure.rendering` (60 files)

Pandoc shim, Unicode/XeLaTeX postprocessors, combined PDF/HTML/slide exporters.

### `infrastructure.reporting` (57 files)

Parses pytest + coverage artefacts for dashboards; pairs with Stage 01 summaries and downstream executive exports.

### `infrastructure.research` (3 files)

Seven-stage research workflow (SCOPE→LITERATURE→REASON→DESIGN→COMPUTE→SYNTHESIZE→WRITE) defined as typed ResearchStage data classes with explicit outputs, skills, and template commands per stage. Includes a full PRISMA-adapted literature review prompt and a research workflow prompt referencing template/ infrastructure commands.

### `infrastructure.rules` (6 files)

Governance rules layer for validating project lifecycle transitions, sidecar sync policies, and pipeline gate orchestration. Rules mirror `projects/templates/` with git-tracked `templates/*` exemplars.

### `infrastructure.scientific` (4 files)

Stability probing, benchmarking hooks—consumed heavily by optimization exemplars (`template_code_project` scripts).

### `infrastructure.search` (62 files)

Two-tier search architecture: the `literature/` client stack (client.py, backends, caches) powers literature search with arXiv, Crossref, local, and Paperclip backends. `connectors/` exposes the built-in scientific database adapters through a uniform `ConnectorRegistry`; OpenAlex, UniProt, PDB, Semantic Scholar, European PMC, bioRxiv, and other registered adapters share list/search CLI commands with HTTP timeout, retry, and TTL caching. The live registry, not this prose, is authoritative for connector count.

### `infrastructure.sia` (10 files)

Generic Self-Improving-AI loop utilities: task-layout validation, execution harness, and metric capture reused by `template_sia` (fixture-replay by default).

### `infrastructure.skills` (7 files)

Discovers `SKILL.md` frontmatter → `.cursor/skill_manifest.json`.

### `infrastructure.steganography` (13 files)

Watermark overlays, hashing companions triggered by secure pipeline path.

### `infrastructure.tools` (6 files)

Invocable tool definitions registered by resource-pool governance; tools mirror `projects/templates/` with git-tracked `templates/*` exemplars.

### `infrastructure.validation` (75 files)

Markdown + PDF + integrity CLIs underpinning Stage 04 diagnostics.

### `infrastructure/logrotate.d` (0 files)

Operational templates for deployments (documentation-first; intentionally minimal Python footprint).

--- 

**Documentation maturity:** Coverage statements in Results pull from introspection—not hand-maintained denominators—so newly promoted modules automatically flow into manuscripts after `generate_manuscript_metrics.py`.

**FAIR+RSE linkage:** MCP-ready `SKILL.md` artefacts align with evaluator heuristics (executability + metadata richness) emphasized by FAIRsoft guidance [@garijo2024fairsoft].
