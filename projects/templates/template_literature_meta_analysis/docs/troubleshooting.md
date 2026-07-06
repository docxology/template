# Troubleshooting

## Literal `{{TOKEN}}` Appears

Run token hydration and inspect the resolved manuscript tree:

```bash
uv run python projects/templates/template_literature_meta_analysis/scripts/05_inject_variables.py
rg "\{\{" projects/templates/template_literature_meta_analysis/output/manuscript
```

If a token remains, add it to `src/manuscript/variables.py` and cover it in `tests/test_variables.py`.

## Missing `corpus.jsonl`

For offline demonstration, regenerate the fixture corpus and run analysis:

```bash
uv run python projects/templates/template_literature_meta_analysis/scripts/generate_fixture_corpus.py
uv run python projects/templates/template_literature_meta_analysis/scripts/02_meta_analysis_pipeline.py
```

For a live run, use:

```bash
uv run python projects/templates/template_literature_meta_analysis/scripts/01_literature_search.py
```

## Engine Returns `skipped`

This is expected when a network, API key, or optional provider condition is absent. Check `manuscript/config.yaml` engine toggles and the provider-specific client logs before treating it as a failure.

## LLM Extraction Is Unavailable

The knowledge-graph stage is optional. To score existing nanopublications without new extraction:

```bash
uv run python projects/templates/template_literature_meta_analysis/scripts/03_build_knowledge_graph.py --max-papers 0
```

For live extraction, run Ollama at the configured `base_url` and pull the configured model.

## Figures Are Missing Or Low Resolution

```bash
uv run python projects/templates/template_literature_meta_analysis/scripts/04_generate_figures.py --dpi 300
ls projects/templates/template_literature_meta_analysis/output/figures/
```

The CLI `--dpi` value updates `VIZ_CONFIG["dpi"]` before figures are saved.

## Coverage Gate Fails

```bash
uv run pytest projects/templates/template_literature_meta_analysis/tests/   --cov=projects/templates/template_literature_meta_analysis/src --cov-report=term-missing -v
```

Add real-data tests for uncovered branches; do not remove tests or introduce mocks.

## YAML Parse Error

```bash
uv run python -c "import yaml; yaml.safe_load(open('projects/templates/template_literature_meta_analysis/manuscript/config.yaml'))"
```

Tabs, unclosed quotes, and JSON-style trailing commas are the usual causes.

## PDF Render Fails On Mermaid Or Chrome

Install the headless Chrome dependency used by Mermaid rendering, then rerun:

```bash
npx --yes puppeteer browsers install chrome-headless-shell
uv run python scripts/pipeline/stage_03_render.py --project templates/template_literature_meta_analysis
```

## Tests Collect Zero Files

Run the project suite directly from the repo root:

```bash
uv run pytest projects/templates/template_literature_meta_analysis/tests/   --cov=projects/templates/template_literature_meta_analysis/src --cov-fail-under=90
```

A green exit from a wrapper with zero collected tests is not evidence of project readiness.
