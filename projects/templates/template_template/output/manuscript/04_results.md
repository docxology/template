# Results

This section reports repository facts produced by the meta-project's live introspection pass. Test counts, module inventories, pipeline-stage counts, and figure data are injected from generated artifacts. Runtime and achieved-coverage claims are intentionally omitted when no versioned benchmark or coverage artifact backs them.

## Multi-Project Pipeline Execution

The `./run.sh` interactive orchestrator can execute the public roster through the shared DAG. The table below is a structural snapshot, not a timing benchmark: counts come from repository introspection, and the coverage column states each exemplar's declared policy floor rather than an unversioned observed percentage.

| Project | Effective core stages¹ | Discovered tests | Declared project floor |
|---------|-----------------------|-----------------:|-----------------------:|
| `template_code_project` | 8 | 258 | 90% |
| `template_prose_project` | 8 | 165 | 90% |
| `template_autoresearch_project` | 8 | 318 | 90% |

¹“Core-only” excludes LLM-tagged and other opt-in stages according to the YAML stage tags. A fresh run must be used to establish completion status or wall-clock performance for a particular machine and dependency set.

## Infrastructure Test Suite

| Metric | Value |
|--------|-------|
| Test files | 949+ |
| Total tests | ~12,552 |
| Infrastructure coverage gate | ≥60% configured floor |
| Prohibited mock-framework imports | Checked by the static no-mocks gate |

Exercises Pandoc/XeLaTeX paths, steganography hashing, telemetry, YAML-driven pipeline DAG resolution, HTTPS-bound optional suites (`pytest-httpserver`), and local Ollama-gated subsets.

## Infrastructure Module Inventory

The introspection module (`template_template.core.introspection`) emits the authoritative table below—every row reflects `discover_infrastructure_modules(REPO_ROOT)`.

| Module | Python Files | Has AGENTS.md | Has README.md | Key Exports |
|--------|:-----------:|:-------------:|:-------------:|-------------|
| `autoresearch` | 11 | ✓ | ✓ | `build_autoresearch_plan`, readiness validation CLI |
| `benchmark` | 4 | ✓ | ✓ | Template harness scoring + comparative gates |
| `config` | 0 | ✓ | ✓ | Repository defaults + hardened templates |
| `core` | 201 | ✓ | ✓ | `get_logger`, `load_config`, `TemplateError` |
| `docker` | 0 | ✓ | ✓ | Containerisation scaffolding |
| `doctor` | 14 | ✓ | ✓ | Checkout diagnose/fix/undo repairs |
| `documentation` | 23 | ✓ | ✓ | `FigureManager`, `build_api_index`, `generate_markdown_table` |
| `fonds` | 6 | ✓ | ✓ | — |
| `formal_contracts` | 5 | ✓ | ✓ | — |
| `llm` | 57 | ✓ | ✓ | Ollama helpers, sanitization, review + translation pipelines |
| `logrotate.d` | 0 | ✓ | ✓ | Rotation snippets (documentation-first) |
| `metadata` | 3 | ✓ | ✓ | `normalized_repository_url`, `generate_metadata_package` |
| `methods` | 10 | ✓ | ✓ | `build_methods_orchestration_plan`, methods-stage contracts + validation |
| `orchestration` | 14 | ✓ | ✓ | `PipelineRunner`, entry point for `./run.sh` |
| `project` | 116 | ✓ | ✓ | `discover_projects`, workspace management |
| `prose` | 9 | ✓ | ✓ | Markdown readability + prose tooling |
| `provenance` | 9 | ✓ | ✓ | — |
| `publishing` | 85 | ✓ | ✓ | Zenodo, executable bundle, archival targets |
| `reference` | 16 | ✓ | ✓ | BibTeX models, parsers, converters |
| `rendering` | 120 | ✓ | ✓ | PDF/HTML/slide rendering, Pandoc filters |
| `reporting` | 411 | ✓ | ✓ | Coverage parsers, dashboards, executive artefacts |
| `research` | 3 | ✓ | ✓ | — |
| `rules` | 6 | ✓ | ✓ | — |
| `scientific` | 4 | ✓ | ✓ | `check_numerical_stability`, `benchmark_function` |
| `search` | 77 | ✓ | ✓ | `infrastructure.search.literature` clients + cache |
| `sia` | 10 | ✓ | ✓ | Self-Improving-AI loop: task validation, harness, metric capture |
| `skills` | 8 | ✓ | ✓ | `discover_skills`, SKILL manifest regeneration |
| `steganography` | 13 | ✓ | ✓ | Watermark overlays + hash manifests |
| `tools` | 6 | ✓ | ✓ | — |
| `transmission` | 6 | ✓ | ✓ | — |
| `validation` | 87 | ✓ | ✓ | PDF + Markdown + integrity CLIs |

All 31 enumerated subdirectories carry Tier‑1/`README.md` and Tier‑2/`AGENTS.md` coverage wherever the Documentation Duality standard applies; subsets ship Tier‑3 `SKILL.md` descriptors for MCP routing (`infrastructure/skills` manifest generation).

## Agentic Skill Documentation Coverage

| Layer | Role |
|-------|------|
| Shared agent guidance | Root `AGENTS.md`, `.agents/` skills, roles, and workflows |
| Structural | `AGENTS.md` directories |
| Skills | Optional `SKILL.md` manifests + generated `.agents/skill_manifest.json` |
| PAI capsule | Repository level `PAI.md` narratives |

`380+` Markdown shards under `docs/` capture operational knowledge without duplicating auto-generated inventories.

## DAG Reference (Declarative Executor)

The table summarizes the 10 default full-run stages (core plus live LLM nodes) from 17 YAML declarations; core mode selects 8. Separately tagged opt-in extensions are omitted here. Entries follow dependency order rather than numeric script filenames.

| Name | Typical script / method | Responsibility | Failure semantics |
|--------------|------------------------|----------------|------------------|
| Clean Output Directories | `_run_clean_outputs` | Deletes stale `output/` trees | Blocking |
| Environment Setup | `scripts/pipeline/stage_00_setup.py` | Validates tooling, PYTHONPATH scaffolding | Blocking |
| Infrastructure Tests | `scripts/pipeline/stage_01_test.py` `--infra-only` `--infra-scope` `pipeline-smoke` | Focused infrastructure smoke contracts | Required tests must pass |
| Project Tests | `scripts/pipeline/stage_01_test.py` `--project-only` | Project-local tests + coverage gates | Required tests and coverage must pass |
| Project Analysis | `scripts/pipeline/stage_02_analysis.py` | Executes `projects/<name>/scripts/*.py` | Blocking |
| PDF Rendering | `scripts/pipeline/stage_03_render.py` | Pandoc → XeLaTeX manuscripts | Blocking |
| Output Validation | `scripts/pipeline/stage_04_validate.py` | Structural PDF/markdown probes | Blocking / warnings |
| LLM Manuscript Review | `scripts/pipeline/stage_06_llm_review.py` `--reviews-only` | Local Ollama reviews | Fresh policy-bound skip; required live acceptance remains blocking |
| LLM Translations | `scripts/pipeline/stage_06_llm_review.py` `--translations-only` | Optional translations | Fresh policy-bound skip |
| Copy Outputs | `scripts/pipeline/stage_05_copy.py` | Mirrors deliverables → `output/<project>/` | Blocking |

`scripts/pipeline/stage_07_executive_report.py` provides separate **multi-project executive reporting**, not an additional single-project DAG node (`execute_pipeline.py`). The multi-project executor writes its aggregate summary after project execution.

## Steganographic Performance Boundary

The steganography path exposes metadata injection, SHA-256 hashing, overlay generation, and optional QR-code insertion as separately testable operations. This revision makes no latency claim because the project does not currently generate a versioned benchmark artifact recording hardware, input PDF, warm-up policy, repetitions, and dispersion. A future performance table should be compiled from such an artifact rather than copied from an ad-hoc workstation run.

## Self-Referential Analysis

Rendered via `projects/templates/template_template` (`generate_manuscript_metrics.py` → injected tokens such as `31`). Architecture figures stem from [`template_template.figures.architecture_viz`](../src/template_template/figures/architecture_viz.py)—font sizes constrained by §QA.

![Live rendering of the Two-Layer Architecture from repository introspection: the infrastructure layer (top) holds the `31` enumerated infrastructure directories, each annotated with its Python file count and a four-slot documentation badge—`A` AGENTS.md, `R` README.md, `S` SKILL.md, `P` PAI.md, with `·` marking an absent file—so a fully documented module reads `[ARSP]`. A YAML DAG arrow connects it to the project layer (bottom) of public exemplars labelled with chapter and test-file counts. The takeaway: documentation-duality coverage is near-uniform across the infrastructure, and every box was placed from the same live data the prose cites.](../output/figures/architecture_overview.png){#fig:template-architecture data-slide-manifest="../output/figures/architecture_overview.panels.json"}

![Declared-stage reference with all 17 YAML stages in reading order, showing complete names and tags (core, LLM, ebook, docxplus, metadata, bundle, archival). Panel order documents declarations; it does not imply a linear dependency chain.](../output/figures/pipeline_stages.png){#fig:template-pipeline-flow data-slide-manifest="../output/figures/pipeline_stages.panels.json"}

![Horizontal file-count histogram of every infrastructure subdirectory, sorted largest-first.](../output/figures/module_inventory.png){#fig:template-module-inventory data-slide-manifest="../output/figures/module_inventory.panels.json" height="210mm" style="height: auto !important;"}

The long tail of small, single-purpose packages beside a handful of larger ones (`core`, `validation`, `publishing`) is the visual signature of the Unix-philosophy modularity the architecture section argues for—capability concentrated where it compounds, not spread evenly by fiat.

## Comparative Feature Analysis

The comparative feature matrix below summarizes the Appendix F capability matrix.


![14 × 10 heatmap annotated in appendix text—green **✓** full native capability, yellow partial / plugin-hosted, red **—** unavailable. Rows group *Core Pipeline*, *Quality & Security*, then *Ecosystem*.](../output/figures/comparative_feature_matrix.png){#fig:template-comparative-matrix data-slide-manifest="../output/figures/comparative_feature_matrix.panels.json"}

¹ Nextflow lineage records exist at workflow scope, not per rendered PDF citation graph.

² DVC: content-addressed artifacts without native prose rendering.

³ DVC: remote object stores (S3, GCS, Azure) without turnkey CI manuscript gates.

## Test Quality Metrics

- **Zero mocks:** repository policy bans `unittest.mock` / patching frameworks in tests.


- **Filesystem + subprocess realism:** ephemeral directories + actual CLI binaries.


- **HTTP realism:** infra suites favour `pytest-httpserver`; literature tests hit recorded fixtures.


- **`template_code_project`** focuses on numerical reproducibility assertions.


- **`template_autoresearch_project`** exercises the AutoResearch readiness planner (`infrastructure/autoresearch/`). **`template_search_project`** exercises literature-search workflows.
