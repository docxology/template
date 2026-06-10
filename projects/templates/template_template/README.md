# Template: Meta-Research Project

A self-referential research study that programmatically analyzes and documents the Docxology Template repository's own architecture, pipeline, and security layer.

**Location:** git-tracked public exemplar at `projects/templates/template_template/` in the public template checkout.

## When to use this template

Use this template when your research subject is **the repository itself** —
programmatic introspection of architecture, pipeline DAGs, module inventories,
and security layers, rendered as a manuscript whose every metric is computed
live (autopoietic: the paper regenerates itself from the code it describes).
It is the reference for binding `${var}` metric tokens to introspection code.

If you are studying an external subject rather than the repo, start from
[`template_code_project`](../template_code_project/) (computational research)
or [`template_prose_project`](../template_prose_project/) (editorial
pipeline). Full roster:
[`projects/AGENTS.md`](../../AGENTS.md#permanent-canonical-exemplars-and-optional-search-add-on).

## Overview

- **Repository introspection:** `src/template_template/introspection.py` loads the YAML pipeline DAG, discovers modules/projects, and aggregates file counts.
- **Metrics injection:** `src/template_template/metrics.py` computes manuscript variables; `inject_metrics.py` renders `${var}` tokens into `output/manuscript/`.
- **Figures:** `scripts/generate_architecture_viz.py` produces four PNGs from live introspection data.

## Quick Start

From the public template repo root:

```bash
uv run pytest projects/templates/template_template/tests/ \
  --cov=projects/templates/template_template/src/template_template --cov-fail-under=90 -v

uv run python projects/templates/template_template/scripts/generate_architecture_viz.py
uv run python projects/templates/template_template/scripts/generate_manuscript_metrics.py

./run.sh --project templates/template_template --pipeline
```

## Directory Structure

| Folder | Contents |
|--------|----------|
| `manuscript/` | 21 Markdown chapters + `config.yaml` (+ `config.yaml.example` copy-and-customize starting point) + `references.bib` |
| `scripts/` | Two thin orchestrators (figures, metrics) |
| `src/template_template/` | Introspection, metrics, injection, visualization |
| `tests/` | full suite, 90%+ coverage on `src/template_template/` |
| `output/` | PDF, figures, metrics JSON, rendered manuscript |

## Pipeline Outputs

| Artifact | Path |
|----------|------|
| Rendered PDF | `output/pdf/template_template_combined.pdf` |
| Metrics JSON | `output/data/metrics.json` |
| Rendered chapters | `output/manuscript/*.md` |
| Figures | `output/figures/*.png` |

See [`docs/VERIFICATION.md`](docs/VERIFICATION.md) for the full gate checklist.
