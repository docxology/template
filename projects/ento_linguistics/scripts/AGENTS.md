# scripts/ - Thin Orchestrators

## Purpose

The `scripts/` directory contains **thin orchestrators** that integrate with `src/` modules. Scripts import and use tested methods from `src/` - they never implement business logic themselves.

## Current Scripts

### Active Scripts

#### 01_build_corpus.py

**Purpose**: Builds the literature corpus from entomological sources.

**What it does**:

- Collects entomological literature references
- Processes and normalizes source data
- Outputs corpus files for downstream analysis

#### 02_generate_figures.py

**Purpose**: Generates all manuscript figures for the six Ento-Linguistic domains.

**What it does**:

- Imports visualization and analysis modules from `src/`
- Generates domain-specific figures (term frequencies, ambiguity patterns, concept hierarchies)
- Produces cross-domain comparison figures
- Saves all figures to `output/figures/`

### Manually-Run Scripts (prefixed with `_`)

These scripts are **directly runnable** via `uv run python scripts/_<name>.py` but are **not auto-discovered by the pipeline orchestrator** (which only runs `01_build_corpus.py` and `02_generate_figures.py`). Run them manually for targeted analysis or debugging:

| Script | Purpose |
|--------|---------|
| `_analysis_pipeline.py` | Full analysis pipeline (all stages) |
| `_conceptual_mapping_script.py` | Concept mapping and network generation |
| `_convert_corpus.py` | Corpus format conversion |
| `_discourse_analysis_script.py` | Discourse pattern analysis |
| `_domain_analysis_script.py` | Domain-specific terminology analysis |
| `_example_figure.py` | Example figure generation |
| `_generate_domain_figures.py` | Per-domain frequency and ambiguity figures |
| `_generate_missing_figures.py` | Regenerate any missing figures |
| `_generate_scientific_figures.py` | Scientific simulation figures |
| `_literature_analysis_pipeline.py` | Full literature mining + analysis |
| `_manuscript_preflight.py` | Manuscript figure/reference validation |
| `_quality_report.py` | Readability and integrity metrics |
| `_register_manuscript_figures.py` | Figure registry updates |
| `_render_pdf_override.py` | Custom PDF rendering override |
| `_scientific_simulation.py` | Simulation workflows |

## Thin Orchestrator Pattern

**All business logic lives in `src/`, scripts handle orchestration only.**

### What Scripts Do

- Import methods from `src/` modules
- Orchestrate data flow and execution
- Generate visualizations and outputs
- Handle file I/O and directory management

### What Scripts Don't Do

- Implement mathematical algorithms (use `src/`)
- Duplicate business logic (import from `src/`)
- Contain complex computations (delegate to `src/`)

## See Also

- [`../src/AGENTS.md`](../src/AGENTS.md) - Available src/ modules
- [`../AGENTS.md`](../AGENTS.md) - Project documentation
