# scripts/ — Analysis Scripts

## Overview

The `scripts/` directory contains **thin orchestrators**. A thin orchestrator
strictly coordinates without implementing analysis logic: all EDA computation
lives in the tested `src/eda/` library. Scripts import from `src/`, plot the
returned data with matplotlib, and write artifacts to `output/`.

## Key Concepts

- **Thin orchestrator pattern**: scripts are glue. They call tested functions
  and render their output; they never compute statistics or correlations
  themselves.
- **Headless plotting**: scripts set `MPLBACKEND=Agg` before importing pyplot so
  they run on CI and servers without a display.
- **Manifest output**: every written path is printed to stdout for collection.

## Directory Structure

```mermaid
flowchart LR
    SC[scripts/]
    SC --> EDA[eda_analysis.py<br/>EDA pipeline: figures + summary CSV]
    SC --> GEN[generate_measurements_data.py<br/>deterministic fixture regeneration]
    SC --> INIT[__init__.py<br/>package marker]
    SC --> DOCS[AGENTS.md · README.md · CONVENTIONS.md]

    classDef d fill:#0f172a,stroke:#0f172a,color:#fff
    classDef code fill:#1e3a8a,stroke:#0f172a,color:#fff
    classDef doc fill:#0f766e,stroke:#0f172a,color:#fff
    class SC d
    class EDA code
    class DOCS doc
```

## Usage

```bash
# From the project root
uv run python projects/templates/template_eda_notebook/scripts/eda_analysis.py
```

This script:

1. Loads the shipped dataset and drops incomplete rows (`load_dataset`,
   `clean_dataset`).
2. Prepares figure data via tested preparers (`histogram_data`,
   `correlation_heatmap_data`, `group_count_data`).
3. Plots three figures with matplotlib and writes them to `output/figures/`.
4. Writes a per-column summary CSV to `output/data/summary_statistics.csv`.
5. Writes `output/figures/figure_registry.json` from the immutable specs in
   `src/eda/figures.py`, after verifying all three PNGs exist.
6. Prints every output path for manifest collection.

### generate_measurements_data.py

Regenerates a deterministic **sibling** of the shipped dataset fixture
(`data/measurements.csv`) — same schema, 120 rows, same missingness pattern
(1 height / 2 weight / 1 resting), same group labels, and the same correlation
sign structure — from a fixed NumPy seed (`src/eda/generate.py::generate_measurements`).
The original fixture's random draw order is not recoverable, so the generator
reproduces the fixture's *family*, not a byte-exact clone. Writes
`output/data/measurements_generated.csv` and prints the path for manifest
collection. Because stage 02 discovers every non-underscore script, this
utility runs on each canonical pipeline run — the generated CSV is therefore a
deterministic, regenerable artifact, not a hand-maintained snapshot.

## API Reference

### eda_analysis.py

| Function | Role |
| --- | --- |
| `run_eda(project_root=None)` | Runs the full pipeline; returns three PNGs, the summary CSV, and the figure registry. Accepts an output-root override for tests. |
| `main()` | Calls `run_eda()` against the real project root and prints each path. |

### generate_measurements_data.py

| Function | Role |
| --- | --- |
| `generate_measurements_file(project_root=None)` | Writes `measurements_generated.csv` under `output/data/`. Accepts an output-root override for tests. |
| `main()` | Calls `generate_measurements_file()` against the real project root and prints the path. |

All analysis logic is in `src/eda/`; these scripts only orchestrate. Tested by
[`../tests/test_eda_analysis_script.py`](../tests/test_eda_analysis_script.py)
and [`../tests/test_generate_measurements_data.py`](../tests/test_generate_measurements_data.py),
which run the orchestrator functions against a temporary output root.

## Configuration

- **Histogram bins**: 10 (passed to `histogram_data`).
- **Output directories**: resolved via `src/project_paths.py::project_output_dirs`.
- **Plotting backend**: `Agg` (set before importing pyplot).

## Best Practices

- Use `pathlib.Path` for all file paths; never hardcode an absolute path.
- Verify generated files exist and have content (the script test asserts this).
- Keep all computation in `src/eda/` so the script stays trivially thin.

## See Also

- [README.md](README.md) — Quick reference.
- [CONVENTIONS.md](CONVENTIONS.md) — Thin-orchestrator rules and the headless
  plotting pattern.
- [../src/AGENTS.md](../src/AGENTS.md) — Library API the scripts call.
