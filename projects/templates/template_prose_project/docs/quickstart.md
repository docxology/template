# Quickstart


## 1. Prepare the selected environment

For an independent project, follow the genuine SDK-wheel recipe in
[STANDALONE.md](../STANDALONE.md#standalone-environment). For a canonical monorepo
checkout, prepare Root and the project's own development environment through the
[shared run surface](https://github.com/docxology/template/blob/main/projects/README.md#run-surface),
then enter `projects/templates/template_prose_project/`.

Sections 2, 3, 5 and 6 run from that prepared project root with
`.venv/bin/python`. Initial dependency installation may need network access;
fixture-backed editorial checks are distinct from live review and publication.

## 2. Run the orchestrator

```bash
.venv/bin/python scripts/run_prose_pipeline.py
```

Reads `manuscript/config.yaml`, runs prose analysis on
`manuscript/*.md`, validates `manuscript/references.bib`, and writes:

* `output/manuscript_report.json`
* `output/checks.json`
* `output/review_report.md`
* `output/run_summary.json`

## 3. Generate figures + variables

```bash
.venv/bin/python scripts/y_generate_prose_figures.py
.venv/bin/python scripts/z_generate_manuscript_variables.py
```

Outputs:

* `output/figures/section_word_counts.png`
* `output/figures/readability_metrics.png`
* `output/figures/citation_density.png`
* `output/data/manuscript_variables.json`

## 4. Run under the full pipeline

This is a separate monorepo operation, not a standalone script. Return to the
prepared monorepo root and follow the
[dispatch contract](https://github.com/docxology/template/blob/main/docs/RUN_GUIDE.md).

```bash
./run.sh --project templates/template_prose_project --pipeline --mode core
```

The selected core DAG includes tests, discovered analysis, rendering, validation
and copying. Rendering has its own prepared system-tool requirements; a local
editorial report is not PDF, scientific, native or publication acceptance.
Canonical public outputs can be tracked evidence: preserve retained snapshots
and immutable receipts rather than treating every `output/` tree as disposable.

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
.venv/bin/python scripts/run_prose_pipeline.py --strict
```

The script exits nonzero if a configured check fails; inspect the actual report.

## 6. Complete own test suite

From the prepared project root:

```bash
.venv/bin/python -I -m pytest tests/ --cov=src --cov-fail-under=90
```

The suite uses offline fixtures after dependency preparation. No fixed duration
or passing outcome is promised; inspect collection, failures and coverage.
