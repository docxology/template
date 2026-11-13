# Template Meta-Project Documentation

Technical documentation for the `template` meta-project — the self-referential study that describes the `template/` architecture, built by the same pipeline it documents.

## Quick Links

| Document | Purpose |
|----------|---------|
| [AGENTS.md](AGENTS.md) | Directory index and AI agent instructions |
| [VERIFICATION.md](VERIFICATION.md) | Sub-minute verification routine |
| [architecture.md](architecture.md) | Project architecture and data flow |
| [testing_philosophy.md](testing_philosophy.md) | Zero-mock standard and test categories |
| [manuscript_guide.md](manuscript_guide.md) | 21-file manuscript structure and variable injection |
| [rendering_pipeline.md](rendering_pipeline.md) | Stage 02 → Stage 03 rendering flow |

## Getting Started

These qualified commands run from the **public monorepo root**, not the standalone
project root. For standalone SDK/DATA preparation and the own-suite command, see
[`../README.md`](../README.md#standalone-complete-source-data).

```bash
# Run tests
PYTHONPATH=. uv run pytest projects/templates/template_template/tests/ -v

# Generate figures + metrics + rendered manuscript
PYTHONPATH=. uv run python projects/templates/template_template/scripts/generate_architecture_viz.py
PYTHONPATH=. uv run python projects/templates/template_template/scripts/generate_manuscript_metrics.py

# Full pipeline
./run.sh --project templates/template_template --pipeline --mode core
```

## Key Concepts

- **Self-referential**: This project's manuscript describes the infrastructure it runs on
- **Variable injection**: `${variable}` tokens in manuscript are replaced with live metrics at build time
- **Zero-mock**: Every test runs against the real filesystem and real infrastructure; the collected total is in [monorepo `COUNTS.md`](https://github.com/docxology/template/blob/main/docs/_generated/COUNTS.md)
- **Four figures**: Architecture overview, pipeline stages, module inventory, comparative matrix — all auto-generated from live data
