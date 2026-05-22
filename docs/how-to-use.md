# How to Use the Research Template

This guide covers end-to-end usage of the template/ research pipeline.

## Quick Start

```bash
# Clone and setup
git clone <your-template-fork>
cd template
uv sync

# Run full pipeline on a single project
./run.sh

# Run on all active projects
./run.sh --all-projects

# Run specific project only
uv run python scripts/03_render_pdf.py --project template_code_project
```

## Pipeline Overview

Stage numbers below are script-prefix keys (0 = `00_setup_environment.py`). The canonical DAG has 10 named stages — Clean (stage 0) plus nine numbered stages — see [`docs/RUN_GUIDE.md`](RUN_GUIDE.md) for the authoritative table.

| Key | Script | Purpose |
|-----|--------|---------|
| 0 | `00_setup_environment.py` | Dependency & environment checks |
| 1 | `01_run_tests.py` | Infrastructure + project tests |
| 2 | `02_run_analysis.py` | Data analysis, figures |
| 3 | `03_render_pdf.py` | Build combined PDF manuscript |
| 4 | `04_validate_output.py` | Output integrity checks |
| 5 | `05_copy_outputs.py` | Copy to `output/`  directory |
| 6 | `06_llm_review.py` | LLM scientific/translation review |
| 7 | `07_generate_executive_report.py` | Executive summary (multi-project) |

## Project Layout

- `infrastructure/` — Reusable generic tooling (17 packages)
- `projects/{name}/` — Self-contained research project
  - `src/` — Domain algorithms
  - `tests/` — Test suite
  - `scripts/` — Project-specific orchestration
  - `manuscript/` — Markdown source
  - `output/` — Working outputs

## Common Tasks

### Add a new project
```bash
# Copy scaffold
cp -r projects/template_code_project projects/my_project
# Edit manifest, rename identifiers
# Add to projects/ directory (must have src/ + tests/)
uv run python scripts/generate_active_projects_doc.py
```

### Preflight validate before render
```bash
uv run python -m infrastructure.validation.cli prerender projects/my_project/manuscript --repo-root .
```

### Debug failing tests
```bash
cd projects/my_project
uv run pytest tests/ -v --tb=short
```

## Troubleshooting

See `docs/core/workflow.md` for detailed troubleshooting guide.

## Related

- `docs/core/architecture.md` — System design deep-dive
- `AGENTS.md` — Full system documentation
- `CLAUDE.md` — Claude Code integration guide
