# Template: Meta-Research Project

A self-referential research study that programmatically analyzes and documents the Docxology Template repository's own architecture, pipeline, and security layer.

## Overview

The Template Project serves as a live demonstration of the pipeline's capabilities:

- **Repository Introspection**: `src/template/introspection.py` discovers infrastructure modules, projects, pipeline stages, and test configurations from the live filesystem.
- **Publication-Quality Visualization**: `scripts/generate_architecture_viz.py` generates 3 architecture figures using real introspection data.
- **Comprehensive Manuscript**: 8 chapters (~7,500 words) documenting the Two-Layer Architecture, 8-stage pipeline, 10 infrastructure modules, and steganographic provenance layer.
- **Zero-Mock Test Suite**: 36 tests validating all introspection functions against the real repository.

## Quick Start

```bash
# Run tests
uv run pytest projects/template/tests/ -v

# Generate figures
uv run python projects/template/scripts/generate_architecture_viz.py

# Full pipeline
./run.sh  # Select template, then option 9 (full pipeline)

# With steganography
./secure_run.sh --project template
```

## Directory Structure

| Folder | Contents |
|--------|----------|
| `manuscript/` | 8 Markdown chapters + `config.yaml` |
| `scripts/` | Thin orchestrator for figure generation |
| `src/template/` | Introspection module (5 functions, 5 dataclasses) |
| `tests/` | 36 tests across 5 test classes |
| `output/` | Generated PDF, figures, reports, logs |

## Pipeline Outputs

| Artifact | Path |
|----------|------|
| Rendered PDF | `output/template.pdf` |
| Architecture diagram | `output/figures/architecture_overview.png` |
| Pipeline flow | `output/figures/pipeline_stages.png` |
| Module inventory | `output/figures/module_inventory.png` |
| Test results | `output/reports/test_results.json` |
| Executive report | `output/reports/executive_report.md` |

## Dependencies

- Python ≥ 3.12
- matplotlib ≥ 3.10.0
- numpy ≥ 2.0.0
- pyyaml ≥ 6.0
- Infrastructure layer (via `PYTHONPATH`)
