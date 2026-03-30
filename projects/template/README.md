# Template: Meta-Research Project

A self-referential research study that programmatically analyzes and documents the Docxology Template repository's own architecture, pipeline, and security layer.

## Overview

The Template Project serves as a live demonstration of the pipeline's capabilities:

- **Repository Introspection**: `src/template/introspection.py` discovers infrastructure modules, projects, pipeline stages, and test configurations from the live filesystem.
- **Metrics Injection**: `src/template/metrics.py` computes ~40 manuscript variables; `inject_metrics.py` renders them via `${var}` substitution into output chapters.
- **Publication-Quality Visualization**: `scripts/generate_architecture_viz.py` generates 4 architecture figures using real introspection data with a 16 pt font floor.

### Key Features Demonstrated

- **Comprehensive Manuscript**: 21 modular chapters (~13,500 words) documenting the Two-Layer Architecture, ten-stage DAG pipeline, 13 infrastructure modules, and steganographic provenance layer.
- **Dynamic Introspection**: Architecture visualizations (Figure 1-4) are generated at render-time by scanning the live `template/` repository infrastructure.

## Quick Start

```bash
# Run tests (from repo root)
uv run pytest projects/template/tests/ -v

# Generate figures
uv run python projects/template/scripts/generate_architecture_viz.py

# Generate metrics + rendered manuscript
uv run python projects/template/scripts/generate_manuscript_metrics.py

# Full pipeline
./run.sh  # Select template from menu, then full pipeline

# With steganography
./secure_run.sh --project template
```

## Directory Structure

| Folder | Contents |
|--------|----------|
| `manuscript/` | 21 Markdown chapters + `config.yaml` + `references.bib` |
| `scripts/` | 2 thin orchestrator scripts (figures, metrics) |
| `src/template/` | 5 source modules (introspection, metrics, injection, viz, init) |
| `tests/` | 65 tests across 3 files and 6 test classes |
| `output/` | Generated PDF, figures, reports, manuscripts, logs |

## Pipeline Outputs

| Artifact | Path |
|----------|------|
| Rendered PDF | `output/pdf/template_combined.pdf` |
| Architecture diagram | `output/figures/architecture_overview.png` |
| Pipeline flow | `output/figures/pipeline_stages.png` |
| Module inventory | `output/figures/module_inventory.png` |
| Feature matrix | `output/figures/comparative_feature_matrix.png` |
| Metrics JSON | `output/data/metrics.json` |
| Rendered chapters | `output/manuscript/*.md` |
| Test results | `output/reports/test_results.json` |

## Dependencies

- Python ≥ 3.12
- matplotlib ≥ 3.10.0
- numpy ≥ 2.0.0
- pyyaml ≥ 6.0
- Infrastructure layer (via `PYTHONPATH`)
