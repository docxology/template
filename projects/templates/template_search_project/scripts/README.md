# scripts/

The default core analysis list is declared in `manuscript/config.yaml`, in this order:

1. [run_search_pipeline.py](run_search_pipeline.py) — configured single-query local search, corpus and generated bibliography
2. [y_generate_search_figures.py](y_generate_search_figures.py) — numerical coverage figures
3. [z_generate_manuscript_variables.py](z_generate_manuscript_variables.py) — variables, hydrated manuscript, and extra-citation projection
4. [zz_generate_review_report.py](zz_generate_review_report.py) — review summary
5. [zzz_build_dashboard.py](zzz_build_dashboard.py) — dashboard and output invariants

[run_deep_search.py](run_deep_search.py) and [s_compose_literature_review.py](s_compose_literature_review.py)
are explicit opt-in commands. Composition requires a current producer dependency
record and writes `output/manuscript/S02_generated_literature_review.md`; authored
markdown and curated bibliography files remain unchanged. `--output` is an explicit
direct authoring command. Audited unpaid live acceptance uses the separate
`_run_unpaid_acceptance.py --mode live` entry point.

[review](review) reads `review_config.yaml`. Details: [AGENTS.md](AGENTS.md).
