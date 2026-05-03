# template_search_project/scripts — Agent guide

## Purpose

Thin orchestrators executed in **lexicographic order** by `scripts/02_run_analysis.py`. No business logic beyond CLI and paths.

## Execution order (analysis stage)

| Order | Script | Role |
|-------|--------|------|
| 1 | [`run_deep_search.py`](run_deep_search.py) | Multi-keyword fan-out → unified `references_deep.bib` and `output/deep_search/aggregate.json` |
| 2 | [`run_search_pipeline.py`](run_search_pipeline.py) | Single-query search → enrich → `references.bib` → `output/search/results.json` |
| 3 | [`s_compose_literature_review.py`](s_compose_literature_review.py) | Auto-composes `manuscript/S01_literature_review.md` from the deep-search outputs (must run before the manuscript resolver below) |
| 4 | [`y_generate_search_figures.py`](y_generate_search_figures.py) | Figures under `output/figures/` |
| 5 | [`z_generate_manuscript_variables.py`](z_generate_manuscript_variables.py) | `output/data/manuscript_variables.json` and resolved `output/manuscript/` (the PDF-rendering stage prefers this tree when present) |
| 6 | [`zz_generate_review_report.py`](zz_generate_review_report.py) | Runs `review` if needed; writes `output/review/REVIEW_REPORT.md` |

> Lexicographic ordering matters. The composer is named `s_*` (between
> `run_*` and `y_*`/`z_*`) so `S01_literature_review.md` is fully written
> *before* `z_generate_manuscript_variables.py` resolves the manuscript
> tree into `output/manuscript/`.

## Review entrypoint

[`review`](review) (executable Python file) reads [`../review_config.yaml`](../review_config.yaml). Stages that pass `--repo-root` use `.` with `cwd` = project root (`projects/template_search_project`).

From repository root:

```bash
uv run python projects/template_search_project/scripts/review \
  --project-root "$(pwd)/projects/template_search_project"
```

From project directory:

```bash
cd projects/template_search_project && uv run python scripts/review
```

## Environment

- `ANALYSIS_SCRIPT_TIMEOUT_SEC` — per-script timeout (orchestrator default 7200s).

## See also

- [`../AGENTS.md`](../AGENTS.md)
- [`README.md`](README.md)
