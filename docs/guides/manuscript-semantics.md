# Manuscript Semantics & Syntax (Canonical)

This document is the **single source of truth** for manuscript Markdown semantics across the Research Project Template. The public template exemplars — `projects/template_active_inference/`, `projects/template_autoresearch_project/`, `projects/template_code_project/`, and `projects/template_prose_project/` — plus the local-only `projects_archive/template_search_project/` add-on conform to the conventions below. New projects should copy whichever exemplar most closely matches their shape and follow these rules verbatim.

The PDF rendering pipeline uses **two cooperating tools**:

| Tool | Role | Activated by |
|------|------|--------------|
| Pandoc with `--natbib` | Converts `[@key]` to `\cite{}`/`\citep{}`/`\citet{}` | [`infrastructure/rendering/_pdf_combined_renderer.py`](../../infrastructure/rendering/_pdf_combined_renderer.py) (line 225) |
| `pandoc-crossref` filter | Resolves `@fig:`, `@tbl:`, `@eq:`, `@sec:` cross-references | Same file (line 246) — auto-detected on `PATH` |

Because these tools cooperate, **all citations must use Pandoc bracket-cite syntax** and **all cross-references must use Pandoc-crossref syntax**. Raw `\cite{}` and `\ref{}` work in PDF but break HTML / EPUB rendering and clutter the source.

## 1. Citations

### Syntax — 1. Citations

```markdown
<!-- Parenthetical (renders as "(Knuth, 1997)" or "[1]" depending on style) -->
[@knuth1997]

<!-- Multiple citations, semicolon-separated -->
[@knuth1997; @cormen2009]

<!-- With locator (page, section, chapter) -->
[@knuth1997, pp. 42-45]

<!-- Narrative ("Knuth (1997) showed...") -->
@knuth1997 showed that...

<!-- Suppress author ("[1997]" only) -->
[-@knuth1997]
```

### Rules — 1. Citations

1. **Never use raw `\cite{key}`, `\citep{key}`, or `\citet{key}`** in Markdown — Pandoc emits the right LaTeX automatically under `--natbib`.
2. Every citation key must resolve in `manuscript/references.bib` (or `manuscript/references_deep.bib` in `template_search_project`). Undefined keys surface as `[?]` in the PDF and as warnings in the build log.
3. Citation keys are lowercase alphanumeric with optional underscores. The convention used by the auto-generators is `<surname><year><titleword>` — e.g. `boyd2004convex`, `nocedal2006numerical`, `peng2011reproducible`.
4. Bibliography files are **always** named `references.bib` (and `references_deep.bib` for the deep-search supplement). The Pandoc invocation merges every `manuscript/*.bib`, so projects with multiple bib files just drop them in.

## 2. Equations

### Syntax — 2. Equations

```markdown
<!-- Display equation with label -->
$$
\nabla f(x) = Ax - b
$$ {#eq:gradient}

<!-- LaTeX equation environment (also recognised by pandoc-crossref) -->
\begin{equation}
\label{eq:gradient_descent}
x_{k+1} = x_k - \alpha \nabla f(x_k)
\end{equation}

<!-- Cross-reference -->
[@eq:gradient] gives the gradient; iteration follows [@eq:gradient_descent].
```

### Rules — 2. Equations

1. Either form works — `$$ … $$ {#eq:label}` is the preferred pure-Pandoc form, and `\begin{equation}\label{eq:label}…\end{equation}` is an acceptable raw-LaTeX form that pandoc-crossref still picks up.
2. **Reference equations with `[@eq:label]`**, not `\ref{eq:label}`. The bracketed form renders as "eq. 1" and is portable; the raw form requires LaTeX-only output.
3. Inline math uses `$…$`, never raw `\(…\)`.

## 3. Figures

### Syntax — 3. Figures

```markdown
![Convergence plot showing objective value vs iteration. Reference line at $f(x^\ast)=0$.](../output/figures/convergence_plot.png){#fig:convergence width=80%}

<!-- Cross-reference -->
[@fig:convergence] shows that smaller step sizes converge slower.
```

### Rules — 3. Figures

1. Image paths are **relative to `manuscript/`** (Pandoc resolves them via `--resource-path`). Use `../output/figures/<name>.png` for figures the analysis pipeline writes.
2. Labels follow the pattern `{#fig:<lowercase_underscore_name>}`. Do not use dashes (`fig:per-source` is allowed; `fig:per-source-2` invites confusion with the autonumber).
3. Cross-reference with `[@fig:label]` for parenthetical ("see fig. 3") or `@fig:label` for narrative ("Figure 3 shows…").
4. Captions should be self-contained — they appear under the figure in the PDF and as alt text in the HTML / EPUB output. Avoid "see above"; describe what the figure conveys.
5. PNG only for archival stability; 300 dpi; colourblind-safe palette (Wong 2011).

## 4. Tables

### Syntax — 4. Tables

```markdown
| Step Size (α) | Iterations | Converged |
|---------------|------------|-----------|
| 0.1           | 412        | Yes       |
| 1.0           | 1          | Yes       |

: Gradient descent outcomes per step size, capped at $N_{\max} = 1000$. {#tbl:opt_results}

<!-- Cross-reference -->
[@tbl:opt_results] reports the per-step iteration counts.
```

### Rules — 4. Tables

1. Use Markdown pipe-tables; the caption attaches via `: <caption text> {#tbl:label}` placed **directly below the table** (no blank line).
2. Reference with `[@tbl:label]`, not `\ref{tab:label}` or `Table 1`.
3. For dynamic table bodies, use a `{{TOKEN}}` placeholder (substituted at render time) inside the table — see [`template_code_project/manuscript/03_results.md`](../../projects/template_code_project/manuscript/03_results.md) `RESULT_TABLE_ROWS` for an example.

## 5. Sections

### Syntax — 5. Sections

```markdown
# Methodology {#sec:methodology}

Cross-reference: see [@sec:methodology] for the full pipeline.
```

### Rules — 5. Sections

1. **Every top-level section heading carries a `{#sec:<short_name>}` label.** This enables `[@sec:methodology]` cross-references that are stable under section reordering.
2. Section files use a single H1; subsequent depth-2/3 headings use `## Heading` and `### Heading` (no manual numbering — Pandoc's `--number-sections` autonumbers).
3. **Never use manual numbering like `## 2.1 Search`** — write `## Search` and let `--number-sections` apply the prefix.
4. **Cross-section references** use `[@sec:label]`, not Markdown filename links

## 6. Bibliography Section (`99_references.md`)

Every project has a thin `99_references.md` that points Pandoc-citeproc at the BibTeX file:

```markdown
# References {#sec:references}

Bibliography lives in [`manuscript/references.bib`](references.bib) and is read by Pandoc with `--natbib` during PDF render.
```

The `99_` prefix ensures lexicographic-order assembly places it last. The Pandoc bibliography backend (natbib) replaces this section with the rendered citation list.

## 7. Manuscript-variable substitution (`{{TOKEN}}`)

Numeric values that come from analysis outputs **must** use `{{TOKEN_NAME}}` syntax — never hardcode numbers that change with `config.yaml` or analysis runs.

```markdown
The algorithm took {{RESULT_MAX_ITERATIONS}} iterations on the configured grid.
```

The pipeline (thin orchestrator pattern):

1. `scripts/z_generate_manuscript_variables.py` delegates to `src/manuscript_variables.py` to compute all token values (pure computation — no I/O).
2. The script writes `output/data/manuscript_variables.json` (the full `{TOKEN: value}` mapping).
3. `infrastructure.rendering.manuscript_injection.write_resolved_manuscript_tree()` writes substituted copies of `manuscript/*.md` to `output/manuscript/`. **Documentation-only files (`AGENTS.md`, `README.md`, `SYNTAX.md`) are excluded from the output tree** — their literal `{{TOKEN}}` examples remain unsubstituted in the source.
4. PDF renderer (stage 03) reads from `output/manuscript/` if present, falling back to `manuscript/`.

The live cross-reference test `test_all_manuscript_tokens_are_generated` in each project's test suite enforces that every `{{TOKEN}}` used in `manuscript/*.md` is produced by the variables module. This catches drift before it ever reaches a PDF.

To verify all tokens resolved before rendering:

```bash
grep -r "{{" projects/<your_project>/output/manuscript/ \
  && echo "UNRESOLVED — re-run z_generate_manuscript_variables.py" \
  || echo "All resolved"
```

## 8. Preamble (`preamble.md`)

LaTeX preamble lines live inside a fenced ` ```latex ` block in `preamble.md`. The renderer extracts that block and concatenates it into the Pandoc-LaTeX template via `infrastructure/rendering/latex_utils.py`. Required minimums for a project that uses figures, tables, equations, and citations:

```latex
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{geometry}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{hyperref}
\usepackage[capitalise,noabbrev]{cleveref}
\usepackage{natbib}
```

Do not duplicate packages already loaded by `infrastructure/rendering/pdf_renderer.py`. If you need an extra package (e.g. `algorithm2e`, `siunitx`), add it here and document it in the project AGENTS.md.

## 9. Common pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| `[?]` in PDF where citation should be | Citation key absent from `references.bib` | Add the entry or fix the typo |
| `Figure ??` in PDF | `pandoc-crossref` not on `PATH` | `brew install pandoc-crossref` (macOS) or [build from source](https://github.com/lierdakil/pandoc-crossref) |
| Section autonumbers like "2 2.1 Search" | Manual `## 2.1` heading prefix collides with `--number-sections` | Remove manual prefix; use plain `## Search` |
| Broken markdown link to `02_methodology.md` in PDF | Markdown filename links don't resolve in PDF | Replace with `[@sec:methodology]` |
| `{{TOKEN}}` literally in PDF | Substitution script not run, or token not defined in `src/manuscript_variables.py::generate_variables()` (code project) / `compute_variables()` (prose/search) | Run `z_generate_manuscript_variables.py`; add missing key to `src/manuscript_variables.py` |

## 10. Per-project checklist for new authors

Before committing a manuscript change:

- [ ] Every figure has `{#fig:label}` and is referenced with `[@fig:label]` somewhere in the prose.
- [ ] Every table has `{#tbl:label}` and is referenced with `[@tbl:label]`.
- [ ] Every numbered equation has `{#eq:label}` (or `\label{eq:label}` inside a `\begin{equation}` block) and is referenced with `[@eq:label]`.
- [ ] Every section H1 has `{#sec:label}`.
- [ ] Every `[@key]` citation resolves in `references.bib`.
- [ ] Cross-section references use `[@sec:label]`, not Markdown filename links.
- [ ] No raw `\cite{}` or `\ref{}` in Markdown source (LaTeX is fine inside math/equation environments).
- [ ] Numeric claims are `{{TOKEN}}`-driven, not hardcoded.

## See also

- [`projects/template_code_project/manuscript/SYNTAX.md`](../../projects/template_code_project/manuscript/SYNTAX.md) — code-exemplar-specific token table and figure registry.
- [`projects/template_prose_project/manuscript/SYNTAX.md`](../../projects/template_prose_project/manuscript/SYNTAX.md) — prose-exemplar-specific syntax notes.
- [`projects_archive/template_search_project/manuscript/SYNTAX.md`](../../projects_archive/template_search_project/manuscript/SYNTAX.md) — search-exemplar-specific BibTeX-automation notes.
- [`infrastructure/rendering/_pdf_combined_renderer.py`](../../infrastructure/rendering/_pdf_combined_renderer.py) — Pandoc invocation source.
