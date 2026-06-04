# Quickstart

```mermaid
flowchart TB
    S1[Step 1<br/>uv run pytest projects/templates/template_prose_project/tests/]
    S2[Step 2<br/>scripts/run_prose_pipeline.py]
    S3[Step 3<br/>scripts/y_generate_prose_figures.py<br/>scripts/z_generate_manuscript_variables.py]
    S4[Step 4<br/>./run.sh --project template_prose_project --pipeline]
    S5[Step 5<br/>tighten thresholds in config.yaml]

    S1 --> S2 --> S3 --> S4 --> S5

    classDef step fill:#1e3a8a,stroke:#0f172a,color:#fff
    class S1,S2,S3,S4,S5 step
```

## 1. Smoke-test in 5 seconds

```bash
uv run pytest projects/templates/template_prose_project/tests/ -q
```

All tests should pass without an internet connection.

## 2. Run the orchestrator

```bash
uv run python projects/templates/template_prose_project/scripts/run_prose_pipeline.py
```

Reads `manuscript/config.yaml`, runs prose analysis on
`manuscript/*.md`, validates `manuscript/references.bib`, and writes:

* `output/manuscript_report.json`
* `output/checks.json`
* `output/review_report.md`
* `output/run_summary.json`

## 3. Generate figures + variables

```bash
uv run python projects/templates/template_prose_project/scripts/y_generate_prose_figures.py
uv run python projects/templates/template_prose_project/scripts/z_generate_manuscript_variables.py
```

Outputs:

* `output/figures/section_word_counts.png`
* `output/figures/readability_metrics.png`
* `output/figures/citation_density.png`
* `output/data/manuscript_variables.json`

## 4. Run under the full pipeline

```bash
./run.sh --project template_prose_project --pipeline
```

The infrastructure pipeline runner cleans `output/`, runs tests,
executes every `scripts/*.py` (alphabetical: `run_prose_pipeline.py`,
`y_generate_prose_figures.py`, `z_generate_manuscript_variables.py`),
renders the PDF with Pandoc, and validates outputs.

## 5. Tighten thresholds

To enforce a stricter grade-level band:

```yaml
prose:
  target_grade_level_min: 12.0
  target_grade_level_max: 16.0
  citation_density_min_per_1000: 8.0
```

Then run with `--strict`:

```bash
uv run python projects/templates/template_prose_project/scripts/run_prose_pipeline.py --strict
```

The script exits non-zero if any check fails — perfect for CI.
