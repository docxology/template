# Syntax Guide

This document defines the syntax conventions for documentation and manuscript
content inside the `template_prose_project` exemplar. Sections 1–5 are
mandatory constraints; sections 6–7 are reference material.

The canonical, repository-wide manuscript-syntax reference is
[`docs/guides/manuscript-semantics.md`](../../../docs/guides/manuscript-semantics.md).
Read that first; this document records prose-project-specific overlays.

---

## 1. Markdown Links

Hyperlinks must be informative. Never use placeholder text.

- **BAD**: [this link](https://github.com/docxology/template) to see the template.
- **GOOD**: See the [Research Project Template](https://github.com/docxology/template).

For internal cross-references, prefer relative paths to files inside the
repository:

- **BAD**: See `https://github.com/docxology/template/blob/main/projects/template_prose_project/src/pipeline.py`
- **GOOD**: See [`projects/template_prose_project/src/pipeline.py`](../src/pipeline.py).

---

## 2. Pandoc-Crossref Cross-References

Inside `manuscript/` files, use Pandoc-crossref `[@sec:label]` syntax for
cross-section references. **Never** use raw LaTeX `\ref{}` macros in
Markdown source — they would render literally in the HTML and slide outputs
and bypass Pandoc-crossref's auto-numbering.

- **BAD**: See Section 2 or §3.
- **BAD**: See Section `\ref{sec:methodology}`.
- **GOOD**: See [@sec:methodology] or [@sec:results].

### What this project does **not** use

This exemplar deliberately omits two categories of label that the code
exemplar uses:

| Label kind | Used here? | Why |
|---|---|---|
| `[@sec:label]` for sections | Yes | Standard cross-section reference |
| `[@fig:label]` for figures | **No** | The three diagnostic figures (`output/figures/*.png`) live in the review report, not in the manuscript body. See [`architecture.md`](architecture.md). |
| `[@eq:label]` for equations | **No** | The manuscript contains no equations; LaTeX math is permitted but unused. |
| `[@tbl:label]` for tables | Rare | Tables appear in the review report, not the manuscript body. The Pandoc-crossref filter is loaded so the syntax remains available if a future revision needs a table. |

### Section Label Registry

All eight section files use the labels enumerated in
[`manuscript/SYNTAX.md`](../manuscript/SYNTAX.md):

| File | Section H1 | Label |
|---|---|---|
| `00_abstract.md` | Abstract | `{#sec:abstract}` |
| `01_introduction.md` | Introduction | `{#sec:introduction}` |
| `02_methodology.md` | Methodology | `{#sec:methodology}` |
| `03_results.md` | Results | `{#sec:results}` |
| `04_conclusion.md` | Conclusion | `{#sec:conclusion}` |
| `05_pipeline_internals.md` | Pipeline Internals | `{#sec:pipeline_internals}` |
| `06_reproducibility.md` | Reproducibility | `{#sec:reproducibility}` |
| `99_references.md` | References | `{#sec:references}` |

Cross-section references in prose use `[@sec:methodology]`, never markdown
filename links.

---

## 3. Variable Injection (Madlibs)

When the manuscript needs a numeric or string value derived from a run, use
the `{{TOKEN_NAME}}` syntax. Values are hydrated by
`scripts/z_generate_manuscript_variables.py`, which delegates to
`src/manuscript_variables.py::compute_variables`. Never hardcode a number
that will change when the manuscript or the configuration changes.

- **BAD**: The manuscript contains 12,345 words.
- **GOOD**: The manuscript contains `{{TOTAL_WORDS}}` words.

### Complete `{{TOKEN}}` Reference

All tokens defined in `src/manuscript_variables.py::ManuscriptVariables`:

| Token | Source |
|---|---|
| `{{CONFIG_TITLE}}` | `paper.title` from `manuscript/config.yaml` |
| `{{TOTAL_WORDS}}` | sum of `metrics.word_count` across all manuscript files |
| `{{TOTAL_SENTENCES}}` | sum of `metrics.sentence_count` |
| `{{TOTAL_PARAGRAPHS}}` | sum of `metrics.paragraph_count` |
| `{{AVG_GRADE_LEVEL}}` | weighted-average Flesch-Kincaid Grade Level |
| `{{AVG_READING_EASE}}` | weighted-average Flesch Reading Ease |
| `{{AVG_GUNNING_FOG}}` | weighted-average Gunning Fog Index |
| `{{CITATION_COUNT}}` | count of unique cited keys |
| `{{FILES_ANALYSED}}` | count of files in `manuscript_report.files` |
| `{{LONGEST_SECTION_WORDS}}` | maximum per-file word count |
| `{{SHORTEST_SECTION_WORDS}}` | minimum per-file word count |

### Adding a New Token

1. Add a field to the `ManuscriptVariables` dataclass in
   `projects/template_prose_project/src/manuscript_variables.py`.
2. Populate the new field inside `compute_variables(report)` from the
   `ManuscriptReport` it receives.
3. Add a test in `projects/template_prose_project/tests/test_manuscript_variables.py`
   asserting the new field's value on a known fixture.
4. Reference the token in the appropriate `manuscript/*.md` file as
   `{{NEW_TOKEN}}`.
5. Re-run the pipeline (`run_prose_pipeline.py` then
   `z_generate_manuscript_variables.py`) and confirm
   `output/data/manuscript_variables.json` now contains the key.

### Detecting Unresolved Tokens

If a token remains unresolved, the literal `{{TOKEN_NAME}}` will appear in
the rendered PDF. Detect before rendering:

```bash
grep -r "{{" projects/template_prose_project/output/manuscript/ 2>/dev/null \
  | grep -v ".json" \
  && echo "UNRESOLVED TOKENS FOUND" || echo "All tokens resolved"
```

---

## 4. Code Blocks

Always tag code blocks with their language identifier. This is required for
Pandoc syntax highlighting in the PDF.

````markdown
```python
def example() -> bool:
    return True
```
````

For shell commands:

````markdown
```bash
uv run pytest projects/template_prose_project/tests/ -v
```
````

For inline code referencing file paths, use single backticks:
`projects/template_prose_project/src/pipeline.py`.

---

## 5. Tables (Pandoc)

When writing tables in the manuscript, place the caption below the table
using Pandoc syntax. Tables are rare in this exemplar but the convention
matches the code-project style:

```markdown
| Check | Threshold | Source |
|---|---|---|
| `grade_level_in_band` | 10.0 ≤ FKGL ≤ 18.0 | `prose.target_grade_level_*` |
| `every_file_has_h1` | true | `prose.require_h1_per_section` |
| `bibliography_consistency` | true | `bibliography.fail_on_missing` |

: Configurable checks evaluated by `src/pipeline.py`. {#tbl:checks}
```

Do not use `Table:` prefix — Pandoc infers the type from placement. Do not
hardcode the table number in text; reference with `[@tbl:checks]`.

---

## 6. No Embedded Figures (by design)

The three figures generated by `scripts/y_generate_prose_figures.py`
— `output/figures/section_word_counts.png`,
`output/figures/readability_metrics.png`,
`output/figures/citation_density.png` — are **diagnostic outputs of the
review pipeline**, not part of the manuscript narrative. They are surfaced
in the human-readable review (`output/review_report.md`) for the editor,
not embedded in `manuscript/*.md`.

This contrasts with [`template_code_project`](../../template_code_project/),
where figures are first-class citizens of the results section. The
prose-project pipeline produces no scientific data of its own; therefore it
publishes no figures into the manuscript body. See
[`architecture.md`](architecture.md) for the full justification.

If a future revision needs to embed a figure, follow the code-project
convention: write the PNG via `src/figures.py`, reference it as a Pandoc
image with the relative path `../output/figures/new_figure.png` and the
anchor `{#fig:new_label}`, and document the new label here.

---

## 7. LaTeX Math (allowed but unused)

The Pandoc preamble loads the standard math environment, so `$...$` for
inline math and `$$...$$` for display equations would render correctly.
The current manuscript contains no equations; the editorial-review pipeline
is intentionally an algorithm-free exemplar.

If math is added later, follow the code-project convention: attach a
Pandoc-crossref anchor with `{#eq:label}` directly after the closing `$$`,
and reference with `[@eq:label]`. **Never** use a raw
`\begin{equation}...\label{...}` block inside Markdown — Pandoc-crossref
will not pick up the LaTeX label.
