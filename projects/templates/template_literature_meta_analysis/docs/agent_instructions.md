# AI Agent Instructions - Literature Meta-Analysis Exemplar

Read this before modifying `template_literature_meta_analysis`.

## Rule 1: Config Owns Domain Policy

`manuscript/config.yaml` is the control surface for the review topic, query strings, enabled engines, relevance keywords, subfield taxonomy, and hypotheses. Retargeting from `modafinil` to another topic should primarily be a config and fixture-corpus change, not a source-code fork.

## Rule 2: Scripts Stay Thin

Scripts under `scripts/` orchestrate stage inputs, outputs, logging, and CLI flags. Retrieval, de-duplication, bibliometrics, embeddings, hypothesis scoring, figure generation, and token computation live under `src/`.

## Rule 3: No Mocks

Tests use real objects, real temporary files, and local HTTP servers through `pytest-httpserver`. Do not add `unittest.mock`, `MagicMock`, `mocker.patch`, or call-count assertions.

## Rule 4: Synthetic Fixture Honesty

The committed `data/fixtures/modafinil_corpus.jsonl` is a synthetic offline fixture. It demonstrates the pipeline; it is not evidence about modafinil. Real claims require a live retrieval run and regenerated artifacts.

## Rule 5: Output Is Disposable

Never hand-edit `output/`. To change generated manuscript text, edit source manuscript sections, config, or `src/manuscript/variables.py` and rerun `scripts/05_inject_variables.py`. To change figures or data, edit the relevant `src/` producer and rerun the stage.

## Rule 6: Use Generated Facts

Live counts and coverage snapshots belong in `../../../../docs/_generated/COUNTS.md`. Public exemplar membership belongs in `../../../../docs/_generated/active_projects.md` and `../../../../docs/_generated/exemplar_roster.md`.

## Rule 7: Verify The Touched Surface

```bash
uv run pytest projects/templates/template_literature_meta_analysis/tests/   --cov=projects/templates/template_literature_meta_analysis/src --cov-fail-under=90 -q
uv run python projects/templates/template_literature_meta_analysis/scripts/02_meta_analysis_pipeline.py
uv run python projects/templates/template_literature_meta_analysis/scripts/04_generate_figures.py --dpi 300
uv run python projects/templates/template_literature_meta_analysis/scripts/05_inject_variables.py
```

For docs/manifest changes, also run:

```bash
uv run python scripts/check_template_drift.py --strict --project templates/template_literature_meta_analysis
uv run python scripts/generate_exemplar_roster_doc.py --check
```
