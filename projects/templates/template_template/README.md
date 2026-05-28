# Template: Meta-Research Project

A self-referential research study that programmatically analyzes and documents the Docxology Template repository's own architecture, pipeline, and security layer.

**Location:** git-tracked public exemplar at `projects/templates/template_template/` in the public template checkout.

## Overview

- **Repository introspection:** `src/template/introspection.py` loads the YAML pipeline DAG, discovers modules/projects, and aggregates file counts.
- **Metrics injection:** `src/template/metrics.py` computes manuscript variables; `inject_metrics.py` renders `${var}` tokens into `output/manuscript/`.
- **Figures:** `scripts/generate_architecture_viz.py` produces four PNGs from live introspection data.

## Quick Start

From the public template repo root:

```bash
uv run pytest projects/templates/template_template/tests/ \
  --cov=projects/templates/template_template/src/template_template --cov-fail-under=90 -v

uv run python projects/templates/template_template/scripts/generate_architecture_viz.py
uv run python projects/templates/template_template/scripts/generate_manuscript_metrics.py

./run.sh --project template_template --pipeline
```

## Directory Structure

| Folder | Contents |
|--------|----------|
| `manuscript/` | 21 Markdown chapters + `config.yaml` + `references.bib` |
| `scripts/` | Two thin orchestrators (figures, metrics) |
| `src/template/` | Introspection, metrics, injection, visualization |
| `tests/` | 75 tests, 90%+ coverage on `src/template/` |
| `output/` | PDF, figures, metrics JSON, rendered manuscript |

## Pipeline Outputs

| Artifact | Path |
|----------|------|
| Rendered PDF | `output/pdf/template_combined.pdf` |
| Metrics JSON | `output/data/metrics.json` |
| Rendered chapters | `output/manuscript/*.md` |
| Figures | `output/figures/*.png` |

See [`docs/VERIFICATION.md`](docs/VERIFICATION.md) for the full gate checklist.
