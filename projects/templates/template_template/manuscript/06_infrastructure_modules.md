# Infrastructure Module Reference

This section inventories every Layer‑1 subdirectory returned by `${module_count}` `discover_infrastructure_modules(repo_root)`. File totals use `${total_infra_python_files}` Python sources across infra + `${infra_test_count_approx}` infra tests guarding them. Documentation Duality = paired `README.md` + `AGENTS.md`; optional `SKILL.md` manifests feed `python -m infrastructure.skills`.

${module_inventory_table}

## Alphabetical summaries

Below, `${module_*_python_file_count}` placeholders expand per subdirectory at render-time.

### `infrastructure.autoresearch` (${module_autoresearch_python_file_count} files)

Readiness planner, validation CLI, and report models for AutoResearch-style project promotion (`infrastructure/autoresearch/`).

### `infrastructure.benchmark` (${module_benchmark_python_file_count} files)

Template harness scoring and comparative gate helpers exercised in CI smoke paths.

### `infrastructure/config` (non-package subdirectory)

Repository-wide YAML templates and secure manifests (`.env.template`, hardened defaults referenced by Docker + CLI). `config/` carries no `__init__.py`, so it is a configuration subdirectory rather than an importable package.

### `infrastructure.core` (${module_core_python_file_count} files)

Checkpointing, logging, pipeline YAML parsing, telemetry bridges, filesystem helpers, hardened exceptions. Everything else imports logging + error taxonomy from here first.

### `infrastructure.doctor` (${module_doctor_python_file_count} files)

Checkout diagnose/fix/undo repairs for broken local workspace states.

### `infrastructure.docker` (${module_docker_python_file_count} files)

Pinned images / compose scaffolding for reproducible CI + remote builds.

### `infrastructure.documentation` (${module_documentation_python_file_count} files)

Figure registries plus glossary tooling feeding manuscript automation.

### `infrastructure.fonds` (${module_fonds_python_file_count} files)

Resource pool management for curated fonds (tracked reference datasets, bibliographic collections, and evidence corpora). Fonds mirror `projects/templates/` with git-tracked `templates/*` exemplars and sidecar-linked private lifecycle folders.

### `infrastructure.llm` (${module_llm_python_file_count} files)

Ollama integrations, sanitization adapters, templated reviewer flows. **Literature ingestion now lives primarily in `search/literature` + citation helpers in `reference/`.**

### `infrastructure.methods` (${module_methods_python_file_count} files)

Deterministic methods-orchestration contracts (`MethodStage`, `MethodsOrchestrationPlan`, `MethodsIssue`): builds and validates an ordered methods plan for a research project so the manuscript's "Methods" track stays bound to executable stages.

### `infrastructure.orchestration` (${module_orchestration_python_file_count} files)

`python -m infrastructure.orchestration` exposes interactive menus, subprocess wiring for thin shell wrappers (`run.sh`, `secure_run.sh`), and stubs used in CI for menu parsing tests.

### `infrastructure.project` (${module_project_python_file_count} files)

Canonical discovery (`discover_projects`) enforcing `src/` + `tests/`, slug validation, nested WIP namespaces.

### `infrastructure.prose` (${module_prose_python_file_count} files)

Readability metrics + Markdown tooling for prose-centric manuscripts / CI gates.

### `infrastructure.provenance` (${module_provenance_python_file_count} files)

Content-addressed provenance DAG. Records artifact lineage (which run produced which file, from which inputs) as a verifiable graph of artifact/run/source/claim nodes connected by produced/consumed/derived-from/supports/refutes edges. Includes a structured Review system with severity (blocking/major/minor/info) and verdict (refutes/supports). Features a CLI and pipeline integration hooks for automatic lineage recording after every stage.

### `infrastructure.publishing` (${module_publishing_python_file_count} files)

Metadata models, APA/BibTeX/MLA formatters, optional Zenodo clients.

### `infrastructure.reference` (${module_reference_python_file_count} files)

Citation/BibTeX parsing + conversion utilities leveraged by manuscripts and retrieval scripts.

### `infrastructure.rendering` (${module_rendering_python_file_count} files)

Pandoc shim, Unicode/XeLaTeX postprocessors, combined PDF/HTML/slide exporters.

### `infrastructure.reporting` (${module_reporting_python_file_count} files)

Parses pytest + coverage artefacts for dashboards; pairs with Stage 01 summaries and downstream executive exports.

### `infrastructure.research` (${module_research_python_file_count} files)

Seven-stage research workflow (SCOPE→LITERATURE→REASON→DESIGN→COMPUTE→SYNTHESIZE→WRITE) defined as typed ResearchStage data classes with explicit outputs, skills, and template commands per stage. Includes a full PRISMA-adapted literature review prompt and a research workflow prompt referencing template/ infrastructure commands.

### `infrastructure.rules` (${module_rules_python_file_count} files)

Governance rules layer for validating project lifecycle transitions, sidecar sync policies, and pipeline gate orchestration. Rules mirror `projects/templates/` with git-tracked `templates/*` exemplars.

### `infrastructure.scientific` (${module_scientific_python_file_count} files)

Stability probing, benchmarking hooks—consumed heavily by optimization exemplars (`template_code_project` scripts).

### `infrastructure.search` (${module_search_python_file_count} files)

Two-tier search architecture: the `literature/` client stack (client.py, backends, caches) powers literature search with arXiv, Crossref, local, and Paperclip backends. `connectors/` exposes the built-in scientific database adapters through a uniform `ConnectorRegistry`; OpenAlex, UniProt, PDB, Semantic Scholar, European PMC, bioRxiv, and other registered adapters share list/search CLI commands with HTTP timeout, retry, and TTL caching. The live registry, not this prose, is authoritative for connector count.

### `infrastructure.sia` (${module_sia_python_file_count} files)

Generic Self-Improving-AI loop utilities: task-layout validation, execution harness, and metric capture reused by `template_sia` (fixture-replay by default).

### `infrastructure.skills` (${module_skills_python_file_count} files)

Discovers `SKILL.md` frontmatter → `.cursor/skill_manifest.json`.

### `infrastructure.steganography` (${module_steganography_python_file_count} files)

Watermark overlays, hashing companions triggered by secure pipeline path.

### `infrastructure.tools` (${module_tools_python_file_count} files)

Invocable tool definitions registered by resource-pool governance; tools mirror `projects/templates/` with git-tracked `templates/*` exemplars.

### `infrastructure.validation` (${module_validation_python_file_count} files)

Markdown + PDF + integrity CLIs underpinning Stage 04 diagnostics.

### `infrastructure/logrotate.d` (${module_logrotate_d_python_file_count} files)

Operational templates for deployments (documentation-first; intentionally minimal Python footprint).

---

**Documentation maturity:** Coverage statements in Results pull from introspection—not hand-maintained denominators—so newly promoted modules automatically flow into manuscripts after `generate_manuscript_metrics.py`.

**FAIR+RSE linkage:** MCP-ready `SKILL.md` artefacts align with evaluator heuristics (executability + metadata richness) emphasized by FAIRsoft guidance [@garijo2024fairsoft].
