# scripts/

Pipeline-facing entry points for this project. Order matters: discovery sorts `*.py` by name, so `run_*` … `s_*` … `y_*` … `z_*` … `zz_*` … `zzz_*`.

- [run_deep_search.py](run_deep_search.py) — multi-keyword deep search (max 100 papers per keyword, see `manuscript/config.yaml`; full enrichment, optional per-paper LLM deep summary). See [the *Deep Search* manuscript section](../manuscript/07_deep_search.md).
- [run_search_pipeline.py](run_search_pipeline.py) — main (single-query) search pipeline
- [s_compose_literature_review.py](s_compose_literature_review.py) — composes `S01_literature_review.md` from the deep-search outputs (runs before the manuscript resolver)
- [y_generate_search_figures.py](y_generate_search_figures.py) — plots
- [z_generate_manuscript_variables.py](z_generate_manuscript_variables.py) — variables JSON + resolved `output/manuscript/`
- [zz_generate_review_report.py](zz_generate_review_report.py) — review summary markdown
- [zzz_build_dashboard.py](zzz_build_dashboard.py) — interactive search-coverage dashboard + plaintext invariants; runs last, writes `output/web/dashboard.html`, `output/data/dashboard_payload.json`, `output/reports/dashboard_*.txt`
- [review](review) — configurable quality gate (`review_config.yaml`)

Full table and review notes: [AGENTS.md](AGENTS.md).
