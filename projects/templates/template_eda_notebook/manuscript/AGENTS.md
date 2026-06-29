---
title: "Manuscript directory: template_eda_notebook"
type: "manuscript_guide"
version: "1.0.0"
---

# Manuscript (`projects/templates/template_eda_notebook/manuscript/`)

Repository-wide agent rules for this exemplar live in
[`../docs/agent_instructions.md`](../docs/agent_instructions.md). This file
covers **manuscript-specific** editing: file roles, figure protocol, and the
section modification workflow.

This exemplar keeps the manuscript deliberately simple: it describes the EDA
workflow in prose and references the figures the analysis script produces. It
does **not** use the `{{VARIABLE}}` token-injection pipeline — every numeric
claim is either reproduced by the reader running `scripts/eda_analysis.py` or
registered in [`../data/claim_ledger.yaml`](../data/claim_ledger.yaml). The
`config.yaml` block remains the configuration source of truth for paper
metadata.

## File Inventory

| File / Pattern | Role |
|---|---|
| `00_abstract.md` | Abstract; what the EDA exemplar demonstrates and the headline finding |
| `01_introduction.md` | Why EDA / computational notebooks; the notebook -> tested src extraction idea |
| `02_methodology.md` | The dataset, cleaning, statistics, correlation, and figure-data methods |
| `03_results.md` | The EDA figures and the summary-statistics table |
| `04_conclusion.md` | What the workflow guarantees; how to fork it |
| `05_experimental_setup.md` | Dataset schema, software environment, reproduction commands |
| `06_reproducibility.md` | Artifact inventory and how to regenerate everything |
| `07_scope_and_related_work.md` | Scope limits and related EDA literature |
| `config.yaml` | Paper metadata + publication block — the configuration source of truth |
| `config.yaml.example` | Reference copy with the same top-level sections |
| `preamble.md` | LaTeX injections shared by PDF output |
| `references.bib` | BibTeX bibliography |
| `SYNTAX.md` | Citation, figure, and cross-reference syntax reference |
| `README.md` | Human quick-reference for this directory |
| `AGENTS.md` | This file — agent technical directives |

## Figure Protocol

Figures are referenced via Pandoc-crossref `[@fig:label]`, never with hardcoded
numbers. Each figure is produced by the thin analysis script from a tested
figure-data preparer in `src/eda/figures.py`:

| Label | PNG Filename | Figure-data preparer (`src/eda/figures.py`) |
|---|---|---|
| `{#fig:height_histogram}` | `output/figures/height_histogram.png` | `histogram_data()` |
| `{#fig:correlation_heatmap}` | `output/figures/correlation_heatmap.png` | `correlation_heatmap_data()` |
| `{#fig:group_counts}` | `output/figures/group_counts.png` | `group_count_data()` |

**To add a new figure**:

1. Add a figure-data preparer to `src/eda/figures.py` (returns a dataclass of
   numbers; no matplotlib) and a test in `tests/test_figures.py`.
2. Plot it in [`../scripts/eda_analysis.py`](../scripts/eda_analysis.py) and
   write the PNG under `output/figures/`.
3. Reference it in a manuscript section with a Pandoc image line and `{#fig:…}`.

## Section Modification Protocol

1. **Update the prose** in `02_methodology.md` / `03_results.md` to match the
   code.
2. **Add or extend tests** in the matching `tests/test_*.py`.
3. **Regenerate analysis outputs**:
   ```bash
   uv run python projects/templates/template_eda_notebook/scripts/eda_analysis.py
   ```
4. **Render PDF** from the repository root:
   ```bash
   uv run python scripts/03_render_pdf.py --project templates/template_eda_notebook
   ```
5. **Verify figures and the summary table appear** in the rendered PDF.

## Conventions

1. Avoid boilerplate closers such as "In summary" / "In conclusion" unless the
   section genuinely needs them.
2. Figures and numbers in `03_results.md` must match what
   `scripts/eda_analysis.py` writes under `output/`.
3. When referencing template code, prefer concrete paths
   (e.g. `src/eda/correlation.py::strongest_pairs()`).

## See also

- [`README.md`](README.md) — Quick orientation.
- [`SYNTAX.md`](SYNTAX.md) — Pandoc syntax reference for this manuscript.
- [`../docs/rendering_pipeline.md`](../docs/rendering_pipeline.md) — Manuscript → PDF flow.
- [`../src/eda/figures.py`](../src/eda/figures.py) — Figure-data preparers.
- [`../scripts/eda_analysis.py`](../scripts/eda_analysis.py) — Thin orchestrator that writes the figures.
