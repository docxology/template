# Syntax Guide

This document defines the syntax conventions for documentation and manuscript content inside the `search_project` exemplar. Sections 1–5 are mandatory constraints; sections 6–8 are reference material for common operations.

The canonical, repo-wide manuscript-semantics reference is [`docs/guides/manuscript-semantics.md`](../../../docs/guides/manuscript-semantics.md). The project-local overlay is [`../manuscript/SYNTAX.md`](../manuscript/SYNTAX.md). This file ties them to agent-facing rules.

---

## 1. Markdown Links

Hyperlinks must be informative. Never use placeholder text.

- **BAD**: [this link](../src/pipeline.py) describes the pipeline.
- **GOOD**: See [`src/pipeline.py`](../src/pipeline.py) for the orchestrator.

For internal cross-references inside `manuscript/`, prefer relative paths to source files; the pre-render link checker (`infrastructure.validation.cli links`) walks them.

---

## 2. Pandoc-Crossref Cross-References

Inside `manuscript/` files, use Pandoc-crossref `[@label]` syntax for cross-references. **Never** use raw LaTeX `\ref{}` macros in Markdown source — they would render literally in the HTML output and bypass Pandoc-crossref's auto-numbering. Never hardcode figure or section numbers.

- **BAD**: `See Figure 2 or Section 3.`
- **BAD**: See Figure `\ref{fig:papers_per_source}`.
- **GOOD**: See [@fig:papers_per_source] or [@sec:methodology].

### Figure Label Registry

The three diagnostic figures are produced by `scripts/y_generate_search_figures.py` (which calls into `src/figures.py`) and embedded in `03_results.md`:

| Anchor (in `03_results.md`) | PNG Filename | Generator (in `src/figures.py`) |
|---|---|---|
| `{#fig:papers_per_source}` | `output/figures/papers_per_source.png` | `plot_papers_per_source` |
| `{#fig:year_histogram}` | `output/figures/year_histogram.png` | `plot_year_histogram` |
| `{#fig:score_distribution}` | `output/figures/score_distribution.png` | `plot_score_distribution` |

### Section Label Registry

| File | H1 | Label |
|---|---|---|
| `00_abstract.md` | Abstract | `{#sec:abstract}` |
| `01_introduction.md` | Introduction | `{#sec:introduction}` |
| `02_methodology.md` | Methodology | `{#sec:methodology}` |
| `03_results.md` | Results | `{#sec:results}` |
| `04_conclusion.md` | Conclusion | `{#sec:conclusion}` |
| `05_pipeline_internals.md` | Pipeline Internals | `{#sec:pipeline_internals}` |
| `06_reproducibility.md` | Reproducibility | `{#sec:reproducibility}` |
| `07_deep_search.md` | Deep Search | `{#sec:deep_search}` |
| `S01_literature_review.md` (auto-composed) | Supplemental S1 | `{#sec:supplemental_s1}` |
| `99_references.md` | References | `{#sec:references}` |

Always use **underscored** labels — Pandoc-crossref accepts dashes, but mixed conventions confuse downstream tooling.

---

## 3. Variable Injection (Madlibs)

When specifying numeric results in the manuscript, use the `{{TOKEN_NAME}}` syntax. Values are hydrated by `scripts/z_generate_manuscript_variables.py`, which calls into `src/manuscript_variables.py::compute_variables` and writes resolved markdown into `output/manuscript/`. Never hardcode a number that will change when configuration or corpus changes.

- **BAD**: The query returned 47 papers across 2 sources.
- **GOOD**: The query returned `{{RESULT_NUM_PAPERS}}` papers across `{{RESULT_NUM_SOURCES}}` sources.

### Complete `{{TOKEN}}` Registry

The live token list is defined by the fields of `ManuscriptVariables` in `src/manuscript_variables.py`. Tokens are uppercase versions of the field name wrapped in double curly braces.

**CONFIG_* — Derived from `manuscript/config.yaml`**

| Token | Source |
|---|---|
| `{{CONFIG_QUERY}}` | `config.search.query` |
| `{{CONFIG_MAX_RESULTS}}` | `config.search.max_results` |
| `{{CONFIG_SOURCES}}` | `config.search.sources`, joined with `, ` |

**RESULT_* — Derived from `output/search/results.json`**

| Token | Source |
|---|---|
| `{{RESULT_NUM_PAPERS}}` | `len(SearchResult.papers)` after dedup |
| `{{RESULT_NUM_SOURCES}}` | distinct backends in `per_source_counts` |
| `{{RESULT_PER_SOURCE}}` | `per_source_counts` rendered as `key=count, …` |
| `{{RESULT_ERRORS}}` | `SearchResult.errors` rendered as text |
| `{{RESULT_YEAR_MIN}}` | applied `year_min` filter (or `—`) |
| `{{RESULT_YEAR_MAX}}` | applied `year_max` filter (or `—`) |
| `{{RESULT_WITH_ABSTRACT}}` | papers carrying a non-empty `abstract` |
| `{{RESULT_WITH_DOI}}` | papers carrying a non-empty `doi` |

**DEEP_* — Derived from `config.deep_search` and `output/deep_search/aggregate.json`**

| Token | Source |
|---|---|
| `{{DEEP_MAX_RESULTS_PER_KEYWORD}}` | `config.deep_search.max_results_per_keyword` |
| `{{DEEP_KEYWORD_COUNT}}` | `len(config.deep_search.keywords)` |
| `{{DEEP_KEYWORDS_JOINED}}` | keywords joined with `; ` |
| `{{DEEP_SOURCES}}` | `config.deep_search.sources`, joined with `, ` |
| `{{DEEP_UNIQUE_PAPERS}}` | `len(aggregate.unique_papers)`, or the literal string `<deep-search not run>` when no aggregate exists |

The "not run" sentinel is intentional: a missing aggregate produces a discoverable string rather than a silent dash, so reviewers can `grep '<deep-search not run>'` to spot stale renders.

### Adding a New Variable

1. Add a field to `ManuscriptVariables` in `src/manuscript_variables.py`.
2. Populate it inside `compute_variables`.
3. Reference it in a manuscript `.md` file as `{{NEW_TOKEN}}` (the substitution lower-cases internally then uppercases the marker key, so the field name `new_token` becomes `{{NEW_TOKEN}}`).
4. Run `scripts/z_generate_manuscript_variables.py` and verify the JSON contains the key:
   ```bash
   uv run python projects/template_search_project/scripts/z_generate_manuscript_variables.py
   python -c "import json,sys; d=json.load(open(sys.argv[1])); print(d['new_token'])" \
       projects/template_search_project/output/data/manuscript_variables.json
   ```

### Detecting Unresolved Tokens

If a token remains unresolved, the literal `{{TOKEN_NAME}}` will appear in the rendered PDF. Detect before rendering:

```bash
grep -rn "{{[A-Z_]*}}" projects/template_search_project/output/manuscript/ \
  && echo "UNRESOLVED TOKENS FOUND" || echo "All tokens resolved"
```

The `variables_resolved` review stage (`scripts/review --stage variables_resolved`) automates this check; see `src/analysis.py::validate_variables_resolved`.

---

## 4. Code Blocks

Always tag code blocks with their language identifier. This is required for Pandoc syntax highlighting in the PDF.

```python
def example() -> bool:
    return True
```

For shell commands:
```bash
uv run pytest projects/template_search_project/tests/ -q
```

For YAML snippets:
```yaml
search:
  sources: [local]
```

For inline code referencing file paths, use single backticks: `projects/template_search_project/src/pipeline.py`.

---

## 5. Tables with Pandoc Captions

When writing tables in the manuscript, place the caption below the table using Pandoc syntax. The label goes inside the caption line:

```markdown
| Source   | Papers |
|----------|--------|
| arXiv    | 18     |
| Crossref | 25     |

: Per-source paper counts. {#tbl:per_source}
```

Do not use a `Table:` prefix — Pandoc infers the type from placement. Do not hardcode the table number in text; always use `[@tbl:per_source]`.

---

## 6. Adding a New Figure

To add a figure that appears in `03_results.md`:

1. Add a generator function in `src/figures.py` following the existing pattern (write a PNG to `output/figures/` with a fixed filename).
2. Register the generator in `scripts/y_generate_search_figures.py`.
3. Add the Pandoc image reference in `03_results.md`:
   ```markdown
   ![Caption text describing the figure.](../output/figures/new_figure.png){#fig:new_label}
   ```
4. Reference in prose using Pandoc-crossref: `See [@fig:new_label].`
5. Update [`../manuscript/SYNTAX.md`](../manuscript/SYNTAX.md) (figure label registry) and the matching table in this guide.
6. Re-run the full pipeline to verify the figure appears in the PDF.

---

## 7. LaTeX Math in Manuscript

Pandoc converts `$...$` and `$$...$$` to LaTeX automatically. The search exemplar uses math sparingly — most figures depict counts and distributions rather than analytical expressions — but the same Pandoc-crossref discipline applies when math does appear. Attach the anchor directly after the closing `$$`:

```markdown
$$
\mathrm{score}(p) = \frac{\#\text{matches}(p)}{\#\text{terms}}
$$ {#eq:score_definition}
```

Reference in text: `[@eq:score_definition]`. Never use a raw `\begin{equation}...\label{...}` block — Pandoc-crossref will not pick up the LaTeX label.

---

## 8. Two-Bibliography Citation Rule

Unlike `template_code_project` (single hand-curated `references.bib`), this project carries **two** auto-populated bibliographies that coexist in `manuscript/`:

| File | Generated by | Pipeline |
|---|---|---|
| `manuscript/references.bib` | `src/pipeline.py` (via `scripts/run_search_pipeline.py`) | Single-query workflow |
| `manuscript/references_deep.bib` | `src/deep_search.py` (via `scripts/run_deep_search.py`) | Multi-keyword fan-out |

`infrastructure.rendering.PDFRenderer.render_combined` runs Pandoc with `--natbib`; BibTeX is then invoked over `\bibliography{stem1,stem2,...}` constructed from every `manuscript/*.bib` (sorted). The pre-render citation gate (`infrastructure.validation.cli prerender`) unions the same files, so writing `[@key_only_in_deep]` resolves cleanly even though the key is absent from `references.bib`.

**Consequence**: do not hand-edit either `.bib` file. Both are regenerated. Add curated entries by editing `data/corpus.json` (for the standard pipeline) or by extending `config.deep_search.keywords` (for the deep pipeline).

Validate keys before render:

```bash
uv run python -m infrastructure.reference.citation.cli validate \
    projects/template_search_project/manuscript/references.bib --strict
uv run python -m infrastructure.reference.citation.cli validate \
    projects/template_search_project/manuscript/references_deep.bib --strict
```
