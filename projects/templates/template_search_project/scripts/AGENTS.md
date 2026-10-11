# template_search_project/scripts — Agent guide

## Purpose

Thin orchestrators selected in configured order by `scripts/pipeline/stage_02_analysis.py`. No business logic beyond CLI and paths.

## Execution order (default core analysis)

`analysis.scripts` in the manuscript config selects exactly these producers:

| Order | Script | Role |
|---|---|---|
| 1 | [`run_search_pipeline.py`](run_search_pipeline.py) | Local query, corpus, generated bibliography, search result |
| 2 | [`y_generate_search_figures.py`](y_generate_search_figures.py) | Coverage figures |
| 3 | [`z_generate_manuscript_variables.py`](z_generate_manuscript_variables.py) | Variables, hydrated manuscript, collision-checked extra citations |
| 4 | [`zz_generate_review_report.py`](zz_generate_review_report.py) | Review report |
| 5 | [`zzz_build_dashboard.py`](zzz_build_dashboard.py) | Dashboard and output invariants |

Deep search and composition are explicit opt-in commands outside this list.
Run `run_deep_search.py --enable` with configured sources first, then
`s_compose_literature_review.py`. Composition refuses missing or changed producer
receipts, config/source snapshots, and artifact bytes. Its default output is
`output/manuscript/S02_generated_literature_review.md`, which hydration preserves.
Only explicit direct `--output` can author another path. Curated manuscript
bibliographies remain inputs; generated databases live under `output/bibliography`.
The hydrator emits only new entries into `output/manuscript/generated_search.bib`,
so the actual renderer's bibliography union has one definition per citation key.

The deep producer's disk-source snapshot is a dependency record, separate from
fresh audited live-provider and installed-wheel acceptance.

## Review entrypoint

[`review`](review) (executable Python file) reads [`../review_config.yaml`](../review_config.yaml). Stages that pass `--repo-root` use `.` with `cwd` = project root (`projects/templates/template_search_project`).

From repository root:

```bash
uv run python projects/templates/template_search_project/scripts/review \
  --project-root "$(pwd)/projects/templates/template_search_project"
```

From project directory:

```bash
cd projects/templates/template_search_project && uv run python scripts/review
```

## Environment

- `ANALYSIS_SCRIPT_TIMEOUT_SEC` — per-script timeout (orchestrator default 7200s).

## See also

- [`../AGENTS.md`](../AGENTS.md)
- [`README.md`](README.md)
