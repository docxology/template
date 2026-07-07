# Pools, Rules, and Tools: A Template-Integrated Resource Architecture

**A Meta-Project Demonstrating Fonds, Rules, and Tools Integration in Research Software**

---

| Field | Value |
|---|---|
| **Authors** | Research Template Author¹, Template Collaborator¹ |
| **Affiliation** | ¹ Active Inference Institute |
| **Correspondence** | author@research-template.org |
| **Version** | 1.0.0 |
| **Date** | 2026-07-05 |
| **License** | CC-BY-4.0 |
| **Repository** | [docxology/template](https://github.com/docxology/template) |
| **DOI** | 10.5281/zenodo.template_pools_rules_tools |
| **Keywords** | research software engineering, monorepo architecture, reproducibility, fonds, governance rules, tool discovery, graceful degradation |

---

## Author Contributions

**Research Template Author**: Conceptualisation, architecture design, module implementation (`fonds_reader`, `rules_applier`, `tools_invoker`, `integration`), manuscript writing (all sections), validation.

**Template Collaborator**: Manuscript review, test suite design, exemplar resource authoring (fonds, rules, tools).

## Acknowledgements

The authors thank the Active Inference Institute for hosting the public template repository and providing the infrastructure within which this exemplar was developed. The design of the three-layer resource architecture draws inspiration from the Unix philosophy [@Raymond2003art] and the enterprise application patterns documented by [@Fowler2002patterns].

## Data Availability

All source code, configuration files, and exemplar resources described in this paper are available in the public template repository at <https://github.com/docxology/template> under the `projects/templates/template_pools_rules_tools/` path. The integration pipeline is fully reproducible from source using `uv run python projects/templates/template_pools_rules_tools/scripts/02_run_integration.py` from the repository root. Generated manuscript variables are stored in `output/data/manuscript_variables.json` and injected at render time.

## Competing Interests

The authors declare no competing interests.



```{=latex}
\newpage
```


# Abstract

Research software repositories in monorepo configurations accumulate three categories of shared resources that individual projects must consume without re-implementing discovery logic: **data pools** (bibliographies, contacts, datasets), **governance rules** (style guides, coverage thresholds, citation schemas), and **executable tools** (code executors, validators, skill invocations). Without a canonical integration pattern, projects either duplicate discovery logic or silently ignore resources that fail to load — both outcomes degrade reproducibility and collaborative cohesion [@Wilson2014best; @Taschuk2017ten].

This paper presents `template_pools_rules_tools`, a meta-project exemplar that demonstrates how a single project can programmatically discover, validate, and exercise all three resource categories with zero tight coupling to any specific resource instance. The exemplar comprises four Python modules — `fonds_reader`, `rules_applier`, `tools_invoker`, and `integration` — plus three thin orchestration scripts and a fully token-injected manuscript pipeline.

The architecture (@fig:architecture) separates *resource ownership* from *resource consumption*. Resources live in top-level `fonds/`, `rules/`, and `tools/` directories and are never modified by consumers. Each resource exposes a typed manifest (`fonds.yaml`, `rules.yaml`, `tools.yaml`) that the corresponding reader module uses for discovery and validation. All readers implement graceful fallbacks: they return `None` or empty collections when a resource is absent, log a warning via the standard library `logging` module, and allow the integration pipeline to continue.

In a representative pipeline run, the integration demo loaded {{integration.fonds_loaded}} fonds, validated {{integration.rules_sets_ok}} rule sets, discovered {{integration.tools_discovered}} tools, and processed {{integration.bib_entries}} bibliography entries — all reported as structured JSON that populates manuscript variable tokens at render time. Tests covering the four `src/` modules achieve ≥90% line coverage and use real file paths rather than mocks, ensuring that reported counts are genuine.

The `template_pools_rules_tools` exemplar provides a reference implementation that any project in the template repository can consult when designing its own resource-consumption layer.

**Keywords:** research software engineering, monorepo architecture, reproducibility, fonds, governance rules, tool discovery, graceful degradation



```{=latex}
\newpage
```


# Introduction

## Motivation

Modern research software repositories increasingly adopt monorepo designs in which multiple projects share a common set of curated resources. A monorepo consolidates source code, documentation, datasets, and governance artefacts under one version-controlled root, enabling atomic cross-project changes and a single source of truth for shared data [@Fowler2002patterns]. The practical benefit is significant: a bibliography updated once in `fonds/templates/template_bibliography/` is immediately available to every project that discovers it at runtime, without any per-project copy.

Three categories of shared resource appear consistently across research template repositories:

1. **Data pools (fonds)**: curated reference sets — bibliographies, contact registries, dataset catalogues — that projects query but must never mutate.
2. **Governance rules**: machine-readable constraint schemas and human-readable style guidelines that projects load to validate their own outputs.
3. **Executable tools**: script-based entry points that projects invoke to run computations, validate artefacts, or call external agents.

Without a canonical integration pattern for consuming these resources, projects face a dilemma: they can hard-code discovery paths (creating fragile, repo-root-sensitive logic) or skip resource consumption entirely (forfeiting the monorepo's collaborative benefits). Neither outcome is acceptable in a public, forkable template repository intended to demonstrate best practices [@Wilson2014best].

## Contribution

This paper introduces `template_pools_rules_tools`, a **meta-project exemplar** that resolves this dilemma with a four-module architecture (@fig:architecture). Each module handles one resource category plus a fourth orchestration module:

| Module | Resource category | Key function |
|---|---|---|
| `src/fonds_reader.py` | Data pools | `read_all_fonds()` |
| `src/rules_applier.py` | Governance rules | `validate_against_rules()` |
| `src/tools_invoker.py` | Executable tools | `discover_tools()` |
| `src/integration.py` | All three | `run_integration_demo()` |

The architecture obeys three design invariants:

- **Read-only resource access**: no module writes to `fonds/`, `rules/`, or `tools/`. The Layer Contract in `AGENTS.md` enforces this at code-review time.
- **Repo-root-relative discovery**: all path resolution uses `pathlib.Path(__file__).resolve().parents[N]` so that scripts work from any working directory.
- **Graceful degradation**: every reader catches `FileNotFoundError` and `yaml.YAMLError`, logs a warning, and returns a safe empty value. The pipeline never raises on a missing resource.

## Paper Organisation

The remainder of this paper is structured as follows. @sec:pools describes the fond layer and the `fonds_reader` module. @sec:rules describes the rules layer and the `rules_applier` module. @sec:tools describes the tool layer and the `tools_invoker` module. @sec:integration presents the unified integration pipeline, the manuscript variable token system, and a discussion of resilience design. @sec:conclusion summarises key findings and future directions.

The architecture overview in @fig:architecture provides a visual map of these relationships. Runtime statistics collected during integration are visualised in @fig:counts.



```{=latex}
\newpage
```


# Pools: Fonds as Passive Data Resources {#sec:pools}

## What Is a Fond?

A **fond** is a versioned, read-only data pool that any project in the repository can consume without modifying. The term evokes the culinary concept of a concentrated stock — a stable base that enriches whatever is built on top of it. Fonds live under the top-level `fonds/<scope>/<name>/` directory, each containing a manifest file (`fonds.yaml`), a `data/` subdirectory, and optional documentation. This architecture separates *data ownership* from *data usage*: research projects in `projects/` are consumers, not producers, of fond data. The separation prevents the accretion of project-specific mutations in shared resources — a recurring source of reproducibility failures in collaborative research software [@Wilson2014best].

The three-layer taxonomy (bibliography, contacts, datasets) maps to the three most common categories of curated research data: citable literature, human collaboration networks, and input/output datasets. Each category carries its own schema enforced by `rules/templates/template_manuscript_rules`.

## The Three Template Fonds

### `template_bibliography`

The `template_bibliography` fond is a curated reference library stored in two formats: a BibTeX file (`data/references.bib`) as source of truth, and a flat CSV export (`data/references.csv`) for programmatic querying. Deduplication is enforced on the cite key (the primary CSV column). The collection spans foundational machine-learning works — the transformer architecture [@Vaswani2017attention], early convolutional network research [@LeCun1998gradient], and large-scale language model pre-training [@Brown2020gpt3] — alongside software-engineering references on best practices [@Wilson2014best] and robust software design [@Taschuk2017ten]. In the current integration run, the fond contains **{{integration.bib_entries}} entries**.

The bibliography fond illustrates the *registry pattern* [@Fowler2002patterns]: a single authoritative list is maintained centrally, and all projects reference it rather than keeping private copies. This guarantees citation consistency across all exemplar manuscripts.

### `template_contacts`

The `template_contacts` fond holds a registry of research collaborators, advisors, and reviewers. Each entry is a YAML object with required fields `id` (a unique slug), `name`, and `email`, plus optional fields `affiliation`, `role`, `orcid`, `website`, and `notes`. The YAML file (`data/contacts.yaml`) is the source of truth; a JSON mirror (`data/contacts.json`) supports consumers that prefer JSON deserialization. Deduplication is enforced on the `id` field at validation time.

### `template_datasets`

The `template_datasets` fond catalogs dataset metadata: provenance, licensing, format, size, access URLs, and research tasks. It intentionally stores *metadata only* — no actual data binaries are committed to the repository. This design aligns with the principle that version control systems should track configuration and metadata rather than large binary artefacts [@Kluyver2016jupyter]. Dataset entries require `id`, `name`, `version`, and `license` fields. Exemplar entries reference classic benchmarks such as MNIST (introduced in [@LeCun1998gradient]) and large-scale corpora used in language-model research [@Brown2020gpt3].

## The `fonds.yaml` Manifest

Every fond root must contain a `fonds.yaml` manifest with at minimum three fields:

```yaml
type: bibliography   # bibliography | contacts | datasets
description: "Human-readable description of the fond"
version: "1.0"
tags: [curated, exemplar]
```

The `type` field governs which reader function is appropriate and what schema the `data/` directory is expected to follow. The `version` field is incremented whenever the schema changes, enabling consumers to detect and handle schema drift without silent failures.

## The `fonds_reader` Module

The `src/fonds_reader.py` module provides three reader functions — one per fond type — plus a convenience aggregator:

```python
from src.fonds_reader import (
    read_bibliography_fond,
    read_contacts_fond,
    read_datasets_fond,
    read_all_fonds,
)

bib      = read_bibliography_fond()   # dict | None
contacts = read_contacts_fond()       # dict | None
datasets = read_datasets_fond()       # dict | None
all_fonds = read_all_fonds()          # {"bibliography": ..., "contacts": ..., "datasets": ...}
```

Each reader resolves the repository root from `pathlib.Path(__file__).resolve().parents[4]` and uses a `try/except` block that catches both `FileNotFoundError` and `yaml.YAMLError`. Returning `None` on failure rather than raising ensures that the integration pipeline degrades gracefully when a fond has not yet been populated by a parallel agent [@Taschuk2017ten]. In the current run, {{integration.fonds_loaded}} of 3 expected fonds were successfully loaded (see @fig:counts).

## Resilience by Design

The fond layer enforces resilience at two levels. At the **structural** level, readers tolerate missing fonds entirely. At the **schema** level, the manifest version field allows consumers to check compatibility before processing data. This two-level approach means a fond can evolve its schema without breaking existing consumers that have not yet been updated: the consumer detects the version mismatch and either adapts or skips, rather than crashing silently on malformed data.



```{=latex}
\newpage
```


# Rules: Soft and Strong Governance {#sec:rules}

## The Role of Governance Rules

Research software projects make dozens of implicit governance decisions: what test-coverage threshold is acceptable, how manuscript sections should be ordered, which citation fields are mandatory. Left implicit, these decisions drift silently across projects in a monorepo, eroding the consistency that makes the repository valuable as a public exemplar. The rules layer makes governance explicit, versioned, and machine-enforceable.

A **rule set** in the template repository is a directory under `rules/<scope>/<name>/` containing a typed manifest (`rules.yaml`) and two subdirectories of rule files:

```
<name>/
├── rules.yaml       — manifest (type, scope, version, rule_kinds)
├── soft/            — Markdown guideline files (human-readable, prompt-like)
└── strong/          — YAML constraint schemas (machine-enforceable)
```

This two-tier architecture reflects the distinction between *guidance* (which humans follow approximately) and *constraints* (which pipelines enforce precisely) — a distinction also recognised in enterprise application architecture [@Fowler2002patterns].

## Soft Rules: Style and Process Guidelines

Soft rules are Markdown files in `soft/`. They encode preferences and conventions that cannot easily be expressed as boolean constraints but that human reviewers and AI agents can apply contextually. Examples include:

- **Style preferences**: "Prefer active voice in manuscript sections." "Use `\module{}` macros for all code identifiers."
- **Process guidelines**: "Tag pull requests with a review-stage label before requesting review." "Update `TODO.md` before closing an issue."
- **Citation conventions**: "Cite primary sources rather than textbooks where possible."

Soft rules are treated as guidance: deviations surface as suggestions in code review and manuscript audit reports, not as pipeline blockers. This makes the soft layer suitable for evolving preferences that should not break automated checks.

## Strong Rules: Hard Constraints

Strong rules are YAML files in `strong/`. Each file defines one named constraint:

```yaml
rule:
  name: coverage-gate
  kind: strong
  description: "Minimum test coverage threshold for src/ modules."
  applies_to: "projects/*/src/"
  enforcement: fail_on_violation
  constraints:
    minimum_line_coverage: 90
    minimum_branch_coverage: 80
```

The `enforcement: fail_on_violation` field signals that a pipeline must halt and report when this rule is violated. Strong rules are suitable for invariants that, if broken, indicate a genuine defect rather than a style preference: coverage below 90% means tests are missing; a manuscript section without an abstract means the document is incomplete.

## The Two Template Rule Sets

### `template_project_rules`

This rule set governs software projects throughout the template repository. Its strong rules currently comprise:

| File | Constraint |
|---|---|
| `strong/coverage-gate.yaml` | Minimum line coverage 90%, branch coverage 80% for `src/` |
| `strong/module-structure.yaml` | Required directory layout: `src/`, `tests/`, `scripts/`, `manuscript/` |

Its soft rules provide guidance on code style, commit message conventions, and pull-request labelling.

### `template_manuscript_rules`

This rule set governs research manuscripts. Its strong rules comprise:

| File | Constraint |
|---|---|
| `strong/reference-schema.yaml` | Required BibTeX fields and cite-key format constraints |
| `strong/section-schema.yaml` | Required manuscript sections, ordering, and minimum word counts |

In the current pipeline run, **{{integration.rules_sets_ok}} of 2 rule sets** validated successfully (@fig:counts).

## The `rules_applier` Module

The `src/rules_applier.py` module exposes three functions:

```python
from src.rules_applier import (
    load_soft_rules,
    load_strong_rules,
    validate_against_rules,
)

soft   = load_soft_rules("template_project_rules")    # list[dict]
strong = load_strong_rules("template_project_rules")  # list[dict]
result = validate_against_rules("template_project_rules")
# → {"status": "ok" | "partial" | "missing", "soft_count": N, "strong_count": N}
```

`validate_against_rules()` performs two checks: (1) the `rules.yaml` manifest is parseable YAML; (2) every rule file in `soft/` and `strong/` is parseable YAML. It returns a status of `"ok"` when both checks pass, `"partial"` when the manifest exists but some rule files are missing or malformed, and `"missing"` when the rule set directory is absent entirely. This graduated status enables the integration pipeline to distinguish between a rule set that has not yet been created (acceptable during active development) and one that is present but broken (actionable defect).

## Rules and Manuscript Variables

Strong rule validation counts are injected into the manuscript through the token system. The token `{{integration.rules_sets_ok}}` expands to the count of rule sets that returned `status="ok"` during the integration run. This creates a verifiable link between the pipeline's actual behaviour and the manuscript's claims — the manuscript cannot assert successful validation without the pipeline having actually succeeded.



```{=latex}
\newpage
```


# Tools: Executable Entry Points {#sec:tools}

## What Is a Tool?

A **tool** in the template repository is a directory under `tools/<scope>/<name>/` that packages one or more executable scripts behind a typed manifest (`tools.yaml`). Tools provide the third layer of the resource architecture: where fonds supply static data and rules supply governance constraints, tools supply *behaviour* — computations, validation runs, and agent skill invocations that projects can trigger without re-implementing the underlying logic.

The tools layer deliberately mirrors the Unix philosophy of small, composable utilities that communicate through standard interfaces [@Raymond2003art]. Each tool declares its entrypoints (shell scripts), its invocation contract (stdin/stdout/exit-code semantics), and its capabilities (type, version, tags) in a single manifest file. Consumers invoke tools through the `tools_invoker` module without needing to understand the tool's implementation details — a textbook application of the Facade pattern [@Gamma1994design].

## The `tools.yaml` Manifest

Every tool root must contain a `tools.yaml` manifest with the following fields:

```yaml
type: code_executor | validator | skill | agent | renderer
description: "Human-readable description of the tool"
version: "1.0.0"
tags: [curated, exemplar, production, experimental]
creator: "org/repo"
license: "Apache-2.0"
entrypoints:
  - scripts/run.sh
  - scripts/validate.sh
```

The `type` field determines the invocation contract the consumer should expect. The `entrypoints` list names the scripts that must exist on disk; the `tools_invoker` module validates their presence at discovery time rather than at invocation time, making failures visible early in the pipeline rather than at runtime.

## The Three Template Tools

### `template_code_executor`

A generic code execution tool that accepts a JSON payload on standard input and returns execution results as JSON. The invocation contract is:

| Entrypoint | stdin | stdout | exit code |
|---|---|---|---|
| `scripts/run.sh` | `{"code": str, "language": str}` | `{"exit_code": int, "stdout": str, "stderr": str}` | 0 = success |
| `scripts/validate.sh` | — | Human-readable validation report | 0 = valid |

The code executor exemplifies tools that wrap a computational capability. The JSON-in/JSON-out contract makes it easily composable with pipeline orchestrators and agent frameworks.

### `template_validator`

A JSON Schema validation tool. It reads a target document and a schema from disk and reports validation results in human-readable form. The entrypoint `scripts/validate.sh` exits 0 when the document is valid and non-zero with a detailed error message otherwise. The validator tool is used in the project pipeline to validate `manuscript_variables.json` against its expected schema before manuscript rendering.

### `template_skill`

An agent skill invocation tool that wraps a Hermes-compatible skill definition. The entrypoint `scripts/invoke.sh` accepts a prompt string on standard input and returns the agent response as text. This tool type bridges the repository's tool architecture with external agent frameworks, demonstrating that the same manifest-and-entrypoint pattern applies equally to computational tools and AI agents.

## The `tools_invoker` Module

The `src/tools_invoker.py` module provides three public functions:

```python
from src.tools_invoker import (
    discover_tools,
    get_tool_entrypoints,
    validate_tool_scripts_exist,
)

tools = discover_tools()
# → [{"name": "template_code_executor", "manifest": {...}}, ...]

eps = get_tool_entrypoints("template_code_executor")
# → ["scripts/run.sh", "scripts/validate.sh"]

result = validate_tool_scripts_exist("template_code_executor")
# → {"status": "ok" | "partial" | "missing", "missing_scripts": [...]}
```

`discover_tools()` scans `tools/templates/` for subdirectories containing a parseable `tools.yaml` and returns a list of discovery records. It silently skips directories without a manifest rather than raising, ensuring that partially-completed tool directories do not block the pipeline.

`validate_tool_scripts_exist()` iterates over the manifest's `entrypoints` list and checks each path against the filesystem. It returns a structured result distinguishing between tools that are fully ready (`"ok"`), partially configured (`"partial"` — some scripts missing), and entirely absent (`"missing"`). In the current integration run, **{{integration.tools_discovered}} tools** were discovered (@fig:counts), all with valid manifests.

## Tool Discovery and Reproducibility

The tools layer contributes to reproducibility by making the *availability* of computational capabilities explicit and checkable. A project that hard-codes a path to a tool script becomes brittle when the repository is reorganised. By contrast, a project that calls `discover_tools()` and checks `validate_tool_scripts_exist()` will detect missing entrypoints at pipeline initialisation time and report them clearly, rather than failing silently at execution time [@Stodden2016enhancing]. This shift from implicit to explicit dependency declaration is a key design principle of the template architecture (see @fig:architecture).



```{=latex}
\newpage
```


# Integration: Unified Pipeline and Token Injection {#sec:integration}

## Architecture Overview

The three resource layers described in @sec:pools, @sec:rules, and @sec:tools are orchestrated by a single function in `src/integration.py`. The `run_integration_demo()` function calls all three subsystems in a defined order, collects their results into a structured dictionary, and writes summary counts to `output/data/manuscript_variables.json` for injection into this manuscript at render time. @fig:architecture illustrates the complete architecture.

```
run_integration_demo()
  ├── read_bibliography_fond()       → {"manifest": ..., "bibtex": ..., "csv_rows": [...]}
  ├── read_contacts_fond()           → {"manifest": ..., "contacts": [...]}
  ├── read_datasets_fond()           → {"manifest": ..., "datasets": [...]}
  ├── validate_against_rules("template_project_rules")    → {"status": "ok", ...}
  ├── validate_against_rules("template_manuscript_rules") → {"status": "ok", ...}
  ├── discover_tools()               → [{"name": ..., "manifest": ...}, ...]
  └── validate_tool_scripts_exist(<each tool>)            → {"status": "ok", ...}
```

The function returns a top-level dict with keys `fonds`, `rules`, `tools`, and `summary`. The `summary` sub-dict provides the counts that populate manuscript tokens.

## Manuscript Variable Tokens

The token injection system bridges the integration pipeline and the manuscript prose. Tokens use double-brace syntax: `{{integration.fonds_loaded}}` expands to the integer count of fonds successfully loaded during the most recent integration run. Tokens are resolved by `scripts/03_generate_manuscript.py`, which reads `output/data/manuscript_variables.json` and substitutes each token before the manuscript is passed to the rendering engine.

The current `manuscript_variables.json` contains the following summary values (see @fig:counts for a visual representation):

| Token | Value |
|---|---|
| `{{integration.fonds_loaded}}` | {{integration.fonds_loaded}} |
| `{{integration.rules_sets_ok}}` | {{integration.rules_sets_ok}} |
| `{{integration.tools_discovered}}` | {{integration.tools_discovered}} |
| `{{integration.bib_entries}}` | {{integration.bib_entries}} |

This table is itself token-injected: the values shown are those produced by the pipeline, not hard-coded by the manuscript author. If the pipeline results change — for example, because a new fond is added — re-running `scripts/03_generate_manuscript.py` updates the manuscript automatically, without manual editing. This property is central to reproducibility: the manuscript's quantitative claims are always consistent with the code that generated them [@Stodden2016enhancing].

## Methods: The Script Pipeline

Three thin orchestration scripts govern the integration workflow (@fig:pipeline):

| Script | Purpose | Key output |
|---|---|---|
| `scripts/01_validate_sources.py` | Validate presence and well-formedness of all resources | Console report |
| `scripts/02_run_integration.py` | Run `run_integration_demo()` and print JSON summary | Console JSON |
| `scripts/03_generate_manuscript.py` | Write `output/data/manuscript_variables.json` | JSON file |

Each script is ≤ 50 lines, imports all business logic from `src/`, and uses `argparse` for optional flags. This thin-orchestrator pattern [@Wilson2014best] ensures that all testable logic is in `src/` at ≥ 90% coverage, while the scripts themselves remain readable without a test suite.

## Resilience Design

The integration layer enforces resilience at three levels, corresponding to the three failure modes a monorepo integration pipeline encounters:

1. **Resource absence**: A fond, rule set, or tool directory may not yet exist if the resource was created by a parallel agent that has not yet completed. All three reader modules return `None` or empty collections in this case, and `run_integration_demo()` reports the missing resource in the `summary` dict without raising.

2. **Schema malformation**: A manifest may be present but contain invalid YAML or missing required fields. Readers catch `yaml.YAMLError` and return a degraded result (`status="partial"` in rule validation; `None` in fond reading) rather than propagating the parse error.

3. **Script absence**: A tool may declare entrypoints in its manifest that have not yet been created. `validate_tool_scripts_exist()` detects this at discovery time and returns `status="partial"` with a list of missing script paths, so the pipeline can report the defect without attempting to invoke a non-existent script.

This three-level resilience design reflects the principle that shared-resource pipelines should fail *informatively* rather than *catastrophically* — surfacing the cause of incompleteness in structured output that downstream consumers can act on [@Taschuk2017ten].

## Test Coverage

The four `src/` modules are covered by 38 tests across four test files in `tests/`. Tests use real file paths, real YAML files, and real BibTeX content rather than mocks, ensuring that coverage numbers reflect genuine code paths through the resource-discovery logic. The current coverage report shows ≥ 90% line coverage for all four modules. The `tests/test_integration.py` suite includes an end-to-end test that calls `run_integration_demo()` and asserts that the `summary` dict contains the expected keys with non-negative integer values — a contract test that verifies the token injection pipeline's data source.



```{=latex}
\newpage
```


# Conclusion {#sec:conclusion}

## Summary

This paper has presented `template_pools_rules_tools`, a meta-project exemplar demonstrating how research software projects embedded in a monorepo can integrate three categories of shared resources — data pools (fonds), governance rules, and executable tools — without tight coupling to any specific resource instance. The key contributions are:

1. **A four-module architecture** (`fonds_reader`, `rules_applier`, `tools_invoker`, `integration`) that provides a canonical pattern for resource-aware project code in the template repository. Each module is independently testable and independently deployable.

2. **A typed manifest convention** (`fonds.yaml`, `rules.yaml`, `tools.yaml`) that makes resource capabilities explicit and checkable at pipeline initialisation time, shifting failure detection from runtime to startup — a significant improvement for reproducibility [@Wilson2014best].

3. **A token injection pipeline** that links manuscript prose to integration runtime statistics through `{{integration.*}}` tokens, ensuring that quantitative claims in the manuscript are always generated by the pipeline rather than authored manually. In the current run this covered {{integration.fonds_loaded}} fonds, {{integration.rules_sets_ok}} rule sets, {{integration.tools_discovered}} tools, and {{integration.bib_entries}} bibliography entries.

4. **A three-level resilience design** — resource absence, schema malformation, and script absence — that allows the pipeline to degrade gracefully and report failures informatively rather than crashing, consistent with best practices for robust research software [@Taschuk2017ten].

## Design Decisions Revisited

Several design decisions deserve emphasis as lessons for future exemplar authors:

**Repo-root-relative discovery** is non-negotiable in a forkable monorepo. Any hard-coded absolute path or working-directory assumption will fail when the repository is cloned to a different location. The `pathlib.Path(__file__).resolve().parents[N]` idiom used throughout `src/` ensures that discovery works from any working directory.

**Graceful fallbacks over exceptions** is the correct trade-off for a resource-consumption layer. The alternative — raising `FileNotFoundError` when a fond is missing — would make the integration pipeline fragile to the ordering of parallel agent writes. Returning `None` and logging a warning allows the pipeline to produce a complete, if partial, result dict that downstream consumers can reason about.

**Real-file tests over mocks** is required for a template exemplar. Mocks can pass tests while the real discovery logic is silently broken. Tests that use real file paths exercise the full path-resolution chain and catch regressions that mocks would miss.

**Thin orchestration scripts** keep the scripts directory readable and focus all testable logic in `src/`. A script that does more than parse arguments, call a `src/` function, and write output is accumulating business logic that belongs elsewhere.

## Future Directions

The three-layer architecture described here is deliberately extensible. The most natural extension is a fourth resource category: **models** (`models/<scope>/<name>/`) for pre-trained machine learning models and their inference scripts. The pattern would follow exactly the same manifest-and-reader design, with `models.yaml` declaring type, version, and entrypoints, and a `models_loader` module providing `discover_models()` and `validate_model_files_exist()`. Adding this layer to `template_pools_rules_tools` would require only a new reader module and a new section in the integration orchestrator — the existing architecture places no constraints on the number of resource categories.

A second direction is **cross-fond validation**: checking that cite keys used in a project's `manuscript/references.bib` are a subset of those available in `fonds/templates/template_bibliography/`. This would require a small cross-reference function in the integration module and would strengthen the reproducibility guarantee by ensuring that manuscript citations always trace back to curated, shared sources.

The exemplar is ready to fork. A project team wishing to adopt this architecture need only copy the four `src/` modules, update the resource directory paths in each reader, and replace the exemplar fond/rules/tool names with their own.
