# Troubleshooting

## Phase Filtering Removes Almost Everything

A phase's `deterministic_filters` (`min_year`, `max_year`,
`min_citation_count`) are applied independently per phase — a narrow
`min_year`/`max_year` window on a young phase (e.g. `phase_2_jwst`'s
`min_year: 2020`) can legitimately yield a small corpus. Check
`output/data/phase_metadata.json` → `phases.<phase_id>.papers_final` against
`project_config.phase_integration.quality_gates.<phase_id>.min_papers` before
assuming a bug. Widen the phase's `queries` or `deterministic_filters` in
`manuscript/config.yaml`, then rerun `scripts/01_multi_phase_search.py`.

## Cross-Phase Validation Conflicts

`phase_integration.citation_validation` expects later-phase papers to cite
≥ `min_cross_phase_citations` earlier-phase papers (per `depends_on`). If
`CROSS_PHASE_CITATION_RATE` reads low or zero:

1. Confirm the dependent phase's `depends_on` list is correct in `config.yaml`.
2. Confirm the earlier phase actually produced papers (see above) — a phase
   with zero papers cannot be cited by anything.
3. Re-run `scripts/01_multi_phase_search.py` so citation metadata is
   recomputed against the current corpus, not a stale snapshot.

This is a known open validator gap — see `TODO.md` → `ARL-CROSS-PHASE-1` and
`ARL-PHASE-VALIDATION-1`: negative controls for boundary/conflict cases are
tracked follow-up work, not yet a hard gate.

## Literal `{{TOKEN}}` Appears

Run token hydration and inspect the resolved manuscript tree:

```bash
uv run python projects/templates/template_advanced_literature_review/scripts/05_inject_variables.py
rg "\{\{" projects/templates/template_advanced_literature_review/output/manuscript
```

If a token remains, add it to `src/manuscript/variables/compute.py` or the
relevant `extractors/` module (see `syntax_guide.md` for the phase-aware
families) and cover it with a test.

## Missing Per-Phase Corpus or `phase_metadata.json`

For an offline demonstration, use the tracked snapshot already committed
under `output/data/`. For a live refresh:

```bash
uv run python projects/templates/template_advanced_literature_review/scripts/01_multi_phase_search.py
```

## Engine Returns `skipped`

Expected when a network, API key, or optional provider condition is absent
for a given phase's `engines` selection. Check
`manuscript/config.yaml` → `project_config.search_phases.<phase>.engines`
and the provider-specific client logs before treating it as a failure.

## Hypothesis Scores Or Assertion Tokens Read `pending`

Stage 03 (knowledge graph) hasn't run, or no Ollama server is reachable at
`project_config.llm_extraction.base_url`. Run it (optionally scoped):

```bash
uv run python projects/templates/template_advanced_literature_review/scripts/03_build_knowledge_graph.py --max-papers 0
```

## Figures Are Missing Or Low Resolution

```bash
uv run python projects/templates/template_advanced_literature_review/scripts/04_generate_figures.py --dpi 300
ls projects/templates/template_advanced_literature_review/output/figures/
```

## Coverage Gate Fails

```bash
uv run pytest projects/templates/template_advanced_literature_review/tests/ \
  --cov=projects/templates/template_advanced_literature_review/src --cov-report=term-missing -v
```

Add real-data tests for uncovered branches — including uncovered phases or
filter-boundary cases; do not remove tests or introduce mocks.

## A Symlinked Module Seems Broken

`src/analysis/`, `src/knowledge_graph/`, `src/reproducibility/`,
`src/visualization/`, and `src/config_loader.py` are symlinks into
`template_literature_meta_analysis/src/` (see `architecture.md`). If one of
these misbehaves, the fix belongs in the sibling project, not here — confirm
with `readlink` before debugging in place:

```bash
readlink projects/templates/template_advanced_literature_review/src/analysis
```

## YAML Parse Error

```bash
uv run python -c "import yaml; yaml.safe_load(open('projects/templates/template_advanced_literature_review/manuscript/config.yaml'))"
```

Tabs, unclosed quotes, and JSON-style trailing commas are the usual causes —
watch especially the multi-line `prompt:` blocks under `llm_filters`.

## PDF Render Fails On Mermaid Or Chrome

```bash
npx --yes puppeteer browsers install chrome-headless-shell
uv run python scripts/pipeline/stage_03_render.py --project templates/template_advanced_literature_review
```

## Tests Collect Zero Files

Run the project suite directly from the repo root:

```bash
uv run pytest projects/templates/template_advanced_literature_review/tests/ \
  --cov=projects/templates/template_advanced_literature_review/src --cov-fail-under=90
```

A green exit from a wrapper with zero collected tests is not evidence of
project readiness.
