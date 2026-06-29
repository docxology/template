# Syntax Guide

This document defines the syntax conventions for documentation and manuscript
content inside the `template_eda_notebook` exemplar.

---

## 1. Markdown Links

Hyperlinks must be informative. Never use placeholder text.

- **BAD**: [this link](https://github.com/docxology/template) to see the template.
- **GOOD**: See the [Research Project Template](https://github.com/docxology/template).

For internal cross-references inside `manuscript/`, prefer relative paths.

---

## 2. Pandoc-Crossref Cross-References

Inside `manuscript/` files, use Pandoc-crossref `[@label]` syntax. **Never** use
raw LaTeX `\ref{}` macros — they render literally in HTML/slide outputs and
bypass auto-numbering. Never hardcode figure or table numbers.

- **BAD**: See Table 1 or Figure 2.
- **GOOD**: See [@tbl:summary_statistics] or [@fig:correlation_heatmap].

### Figure Label Registry

The three figures the analysis script produces from `src/eda/figures.py`:

| Anchor (in `03_results.md`) | PNG Filename | Figure-data preparer |
|---|---|---|
| `{#fig:height_histogram}` | `output/figures/height_histogram.png` | `histogram_data()` |
| `{#fig:correlation_heatmap}` | `output/figures/correlation_heatmap.png` | `correlation_heatmap_data()` |
| `{#fig:group_counts}` | `output/figures/group_counts.png` | `group_count_data()` |

The table anchor used in `03_results.md`: `{#tbl:summary_statistics}`.

---

## 3. Numbers in Prose (no token injection)

This exemplar does **not** use `{{VARIABLE}}` token injection. Concrete numbers
are reproduced by running `scripts/eda_analysis.py`; numeric claims that appear
in prose are registered in [`../data/claim_ledger.yaml`](../data/claim_ledger.yaml)
for evidence validation.

- **Prefer**: describing structure and provenance ("height and weight are
  strongly positively correlated; the dominant pair from `strongest_pairs()`").
- **Avoid**: transcribing a volatile value that would drift when the dataset
  changes.

If you do state a fixed number that comes from the shipped dataset or a default
parameter, add a row to `data/claim_ledger.yaml` recording its source.

---

## 4. Code Blocks

Always tag code blocks with their language identifier for Pandoc syntax
highlighting.

```python
def example() -> bool:
    return True
```

```bash
uv run pytest projects/templates/template_eda_notebook/tests -v
```

For inline code referencing file paths, use single backticks:
`projects/templates/template_eda_notebook/src/eda/dataset.py`.

---

## 5. Table Captions (Pandoc)

Place the caption below the table; the `{#tbl:label}` goes on the caption line:

```markdown
| Column | Reported statistics |
|---|---|
| height_cm | count, mean, std, min, median, max |

: Summary-statistics table written by the analysis script. {#tbl:summary_statistics}
```

Do not use a `Table:` prefix and do not hardcode the table number — use
`[@tbl:summary_statistics]`.

---

## 6. Adding a New Figure

1. Add a figure-data preparer to `src/eda/figures.py` with a test in
   `tests/test_figures.py`.
2. Plot it in `scripts/eda_analysis.py` and write the PNG to `output/figures/`.
3. Add the Pandoc image reference in `03_results.md`:
   ```markdown
   ![Caption text describing the figure.](../output/figures/my_figure.png){#fig:my_label}
   ```
4. Reference it: `See [@fig:my_label].`
5. Update `manuscript/AGENTS.md` and this registry, then re-run the pipeline.

---

## 7. LaTeX Math in Manuscript

Use `$...$` for inline math and `$$...$$` for display equations. For numbered,
referable equations, attach a Pandoc-crossref anchor with `{#eq:label}` after
the closing `$$` and reference with `[@eq:label]`. (This exemplar's prose is
largely equation-free; the convention is documented for forks that need it.)
