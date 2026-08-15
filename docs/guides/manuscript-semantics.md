# Manuscript Semantics & Syntax (Canonical)

This document is the **single source of truth** for manuscript Markdown semantics across the Research Project Template. The public template exemplars under `projects/templates/` conform to the conventions below. The authoritative, always-current roster lives in [`docs/_generated/active_projects.md`](../_generated/active_projects.md). New projects should copy whichever exemplar most closely matches their shape and follow these rules verbatim.

The PDF rendering pipeline uses **three cooperating tools**:

| Tool | Role | Activated by |
|------|------|--------------|
| `formalism.lua` filter | Numbers Definition/Proposition/Theorem blocks and resolves `@def:`, `@prop:`, `@thm:` references | [`infrastructure/rendering/_pandoc_filters.py`](../../infrastructure/rendering/_pandoc_filters.py) — ships with the repo, applied **first** |
| `pandoc-crossref` filter | Resolves `@fig:`, `@tbl:`, `@eq:`, `@sec:` cross-references | [`infrastructure/rendering/_pdf_combined_pandoc.py`](../../infrastructure/rendering/_pdf_combined_pandoc.py) (`build_pandoc_tex_command`) — auto-detected on `PATH` |
| Pandoc citation backend | Resolves the remaining `[@key]`; the PDF path uses `--natbib`, while HTML/DOCX/EPUB/Beamer/Reveal.js use `--citeproc` | Format-specific renderer |

Order matters. `[@def:x]` and `[@knuth1997]` are both Pandoc *citations*; the formalism filter runs first so it can claim the formalism labels before the citation machinery would emit them as undefined citations. The renderers request the same formalism/cross-reference filter order and the same deterministic bibliography union; citation backends still differ (`natbib` for PDF, citeproc for HTML/DOCX/EPUB/slides). `pandoc-crossref` is also an optional external executable. Verify numbering and citations in every enabled edition rather than inferring parity from one render.

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
2. Every citation key must resolve in the bibliography set actually consumed by
   each enabled format. Undefined keys surface as `[?]` or renderer warnings;
   inspect every edition.
3. Citation keys are lowercase alphanumeric with optional underscores. The convention used by the auto-generators is `<surname><year><titleword>` — e.g. `boyd2004convex`, `nocedal2006numerical`, `peng2011reproducible`.
4. Prefer one curated `references.bib`, but supplemental top-level `.bib`
   databases are supported. Combined PDF, HTML, DOCX, EPUB, and the opt-in
   ebook stage all consume the same filename-sorted `manuscript/*.bib` union.
   Repeated or symlinked paths are included once, and duplicate citation keys,
   including case-only variants within or across databases, fail before
   rendering because BibTeX and citeproc otherwise have different winner
   rules. See the
   [cross-format bibliography contract](../usage/output-formats.md#cross-format-bibliography-contract).
5. Syntax and metadata validation do not establish that a source supports the
   adjacent claim. Before submission, validate the BibTeX, resolve identifiers
   against scholarly indexes, and inspect the primary source for claim support:

   ```bash
   uv run python -m infrastructure.reference.citation.cli validate \
     projects/<qualified-name>/manuscript/references.bib --strict
   uv run python -m infrastructure.reference.verification verify \
     projects/<qualified-name>/manuscript/references.bib \
     --live --as-of-year <manuscript-year>
   ```

   `unchecked` and `unverifiable` are honest incomplete outcomes, not passes.
   The resolver checks existence and metadata; it does not prove proposition
   support, assess study quality, or replace checks for corrections,
   expressions of concern, and retractions.

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
2. Labels follow the pattern `{#fig:<lowercase_underscore_name>}`. Use stable,
   descriptive lowercase names with underscores; do not encode a displayed
   figure number in the label.
3. Cross-reference with `[@fig:label]` for parenthetical ("see fig. 3") or `@fig:label` for narrative ("Figure 3 shows…").
4. Captions must be self-contained, but a caption is not a substitute for all
   accessibility text. The current HTML post-processor derives a concise image
   `alt` value from the first caption sentence; the full caption remains
   visible. Make that first sentence a useful identification of the visual,
   then put interpretation, methods, denominators, and uncertainty in the
   remaining caption. Inspect the rendered HTML rather than assuming the
   conversion is semantically adequate.
5. Register every generated figure in
   `output/figures/figure_registry.json`, including a stable label, filename,
   generator, caption, and explicit `metadata.alt_text`. The accessibility
   validator checks that the field is present; human review must still check
   that it conveys the figure's purpose and does not merely repeat its title.
   Provide a nearby prose or appendix description when the relationships in a
   complex figure cannot be conveyed concisely.
6. Do not encode meaning by colour alone. Use a colour-accessible palette plus
   redundant shapes, line styles, direct labels, or patterns; check contrast,
   grayscale legibility, type size, clipping, and panel order in the final
   render.
7. Prefer vector output for line art when every target format supports it.
   Otherwise publish a raster at sufficient resolution for its final physical
   size (300 ppi is a common print target, not a universal guarantee). Use JPEG
   for photographs and lossless formats for plots or diagrams.
8. A statistical caption identifies the analysis population, what `n` counts,
   units, transformations, summary statistic, uncertainty interval or error
   bar, and any test or multiplicity correction needed to interpret the
   visual. Dynamic caption values and annotations come from the same analysis
   outputs as the plotted data; never copy them by hand.

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
3. For dynamic table bodies, use a `{{TOKEN}}` placeholder (substituted at render time) inside the table — see [`template_code_project/manuscript/03_results.md`](../../projects/templates/template_code_project/manuscript/03_results.md) `RESULT_TABLE_ROWS` for an example. Generate the body from typed analysis records, and bind its population, units, rounding, and missing-value policy to those same records.

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

## 6. Formalism blocks (Definitions, Propositions, Theorems)

`pandoc-crossref` numbers figures, equations, tables, listings and sections, but it has **no custom-environment support**. Numbered Definitions and Propositions are therefore handled by a repo-shipped Lua filter, [`infrastructure/rendering/formalism.lua`](../../infrastructure/rendering/formalism.lua), which numbers the blocks and resolves references to them. Write the label; never write the number.

### Syntax — 6. Formalism blocks

```markdown
<!-- Numbered block with a label and an optional title -->
::: {.definition #def:aspiration title="Aspiration"}
An aspiration is a six-tuple.
:::

<!-- Title is optional -->
::: {.proposition #prop:monotone}
Dropping oversight never softens a verdict.
:::

<!-- .unnumbered renders the kind name alone and consumes no number -->
::: {.remark .unnumbered}
Numbering is not a claim about importance.
:::

<!-- Reference by label, exactly like every other cross-reference -->
By [@def:aspiration] the registry is well formed, which [@prop:monotone] extends.
```

renders as:

```text
Definition 1 (Aspiration). An aspiration is a six-tuple.
Proposition 1. Dropping oversight never softens a verdict.
Remark. Numbering is not a claim about importance.

By Definition 1 the registry is well formed, which Proposition 1 extends.
```

Recognised classes: `definition`, `proposition`, `theorem`, `lemma`, `corollary`, `remark`, `axiom`, `claim`, `example`.

### Rules — 6. Formalism blocks

1. **Never write the number.** `**Definition 3.**` typed by hand goes stale the moment a block is inserted above it, and the prose referring to it keeps pointing at the old number. That silent drift is the entire reason this filter exists.
2. **Reference with `[@def:label]`**, the same bracket syntax used for figures, tables and equations. The filter consumes these before the citation machinery sees them, so a formalism label must **not** appear in `references.bib`.
3. Counters are **per kind** and run in document order: Definitions and Propositions each have their own sequence.
4. A label is required for any block you intend to reference; an unlabelled block still gets a number.
5. A reference to a label that was never declared is **left exactly as written** and reported on stderr, so a broken cross-reference stays visible in the output instead of silently vanishing. Watch the build log.
6. Duplicate labels are reported on stderr; the last block declaring a label wins.

### Metadata — 6. Formalism blocks

Set in `manuscript/config.yaml` or a section's YAML block:

| Key | Effect |
|-----|--------|
| `formalism_reset_level` | Restart every counter at each header of this level or above. `0` (default) never resets. A collected volume reproducing several works sets `1`; a standalone paper leaves it unset, because there a level-1 header is a section. |
| `formalism_kinds` | Map of class name to displayed title, merged over the defaults. Adds a kind without editing the filter. |

### Relationship to raw-LaTeX theorem environments

Authors may instead write `\begin{theorem}…\end{theorem}` raw LaTeX, which the manuscript preamble's `\newtheorem` definitions number in the PDF and which `web_renderer.py` rewrites **web-only** into `.theorem-box` Divs. That path predates this filter and still works, but it numbers PDF and web independently and offers no `[@label]` resolution. **Prefer the portable `::: {.definition #def:x}` Div form** — it is the cross-format path designed to keep numbering aligned. Inspect each rendered format because missing optional filters or format-specific conversion can still break parity.

## 7. Bibliography Section (`99_references.md`)

Every project has a thin `99_references.md` that points Pandoc-citeproc at the BibTeX file:

```markdown
# References {#sec:references}

Bibliography lives in [`manuscript/references.bib`](references.bib) and is read by Pandoc with `--natbib` during PDF render.
```

The `99_` prefix ensures lexicographic-order assembly places it last. The PDF
path uses natbib; HTML/DOCX/EPUB use citeproc with the format-specific
bibliography selection described above.

## 8. Manuscript-variable substitution (`{{TOKEN}}`)

Every **dynamic manuscript value** must have a source-bound producer. Dynamic
means any fact that can change with data, configuration, code, environment, or
release identity: counts, sample sizes, exclusions, denominators, estimates,
intervals, p-values, thresholds, parameters, versions, dates, artifact counts,
table cells, and statistics in prose, captions, alt text, or annotations.
Stable prose and mathematical constants need not be tokenized. Never hardcode a
second copy of a generated fact.

```markdown
The algorithm took {{RESULT_MAX_ITERATIONS}} iterations on the configured grid.
```

The canonical code-exemplar pipeline is:

1. Importable project code in `src/manuscript_variables.py` reads canonical
   configuration and analysis outputs, validates them, and computes the token
   mapping. The project script remains a thin I/O orchestrator; the source
   module need not be I/O-free.
2. `scripts/z_generate_manuscript_variables.py` writes
   `output/data/manuscript_variables.json` (the full `{TOKEN: value}` mapping).
3. `infrastructure.rendering.manuscript_injection.write_resolved_manuscript_tree()` writes substituted copies of `manuscript/*.md` to `output/manuscript/`. **Documentation-only files (`AGENTS.md`, `README.md`, `SYNTAX.md`) are excluded from the output tree** — their literal `{{TOKEN}}` examples remain unsubstituted in the source.
4. Stage 03 runs `z_generate_manuscript_variables.py` when the project provides
   it, then reads from `output/manuscript/` when hydrated Markdown exists,
   falling back to the source manuscript otherwise.

`write_resolved_manuscript_tree()` deliberately logs and preserves an unknown
token; it does **not** fail by itself. Projects that inject values must add a
completeness test equivalent to the code exemplar's
`test_all_manuscript_tokens_are_generated`, reject empty/non-finite or
wrong-type scientific values in the producer, and run strict pre-render and
publication gates. Draft-only sentinels such as `N/A` must never enter a release
candidate.

Keep raw scientific values typed in canonical analysis outputs. Apply units and
presentation precision once at the manuscript-variable boundary. Record, in
code or a project-owned registry, each token's definition, source field, unit,
format, missing-value rule, and consumers. Values drawn inside figure pixels
cannot be hydrated after plotting; their generator must read the same canonical
records and publish a figure registry that identifies that generator.

Regenerate in dependency order:

```text
canonical inputs + config
→ analysis outputs
→ variables + tables + figures + figure registry
→ hydrated manuscript
→ PDF/HTML/DOCX/EPUB
→ validation, provenance, and release receipts
```

Do not hand-edit `manuscript_variables.json`, generated tables, figures,
`output/manuscript/`, rendered documents, or receipts. Fix the producer and
regenerate all downstream consumers from the same source revision.

To verify all tokens resolved before rendering:

```bash
uv run python projects/<qualified-name>/scripts/z_generate_manuscript_variables.py
if rg -n '\{\{[A-Z][A-Z0-9_]*\}\}' \
  projects/<qualified-name>/output/manuscript; then
  echo "Unresolved manuscript token(s)" >&2
  exit 1
fi
uv run python -m infrastructure.validation.cli prerender \
  projects/<qualified-name>/manuscript --repo-root .
```

## 9. Preamble (`preamble.md`)

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

## 10. Common pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| `[?]` in PDF where citation should be | Citation key absent from `references.bib` | Add the entry or fix the typo |
| `Figure ??` in PDF | `pandoc-crossref` not on `PATH` | `brew install pandoc-crossref` (macOS) or [build from source](https://github.com/lierdakil/pandoc-crossref) |
| Section autonumbers like "2 2.1 Search" | Manual `## 2.1` heading prefix collides with `--number-sections` | Remove manual prefix; use plain `## Search` |
| Broken markdown link to `02_methodology.md` in PDF | Markdown filename links don't resolve in PDF | Replace with `[@sec:methodology]` |
| `{{TOKEN}}` literally in PDF | Substitution script not run, or token not defined in `src/manuscript_variables.py::generate_variables()` (code project) / `compute_variables()` (prose/search) | Run `z_generate_manuscript_variables.py`; add missing key to `src/manuscript_variables.py` |
| `[@def:x]` left verbatim in the output, `reference to undeclared formalism` on stderr | No block declares `#def:x` — usually a typo or a deleted block | Fix the label, or restore the block. The reference stays visible on purpose |
| Definition numbers disagree between the PDF and the EPUB | A hand-typed `**Definition 3.**` literal instead of a `::: {.definition}` block | Convert to the Div form and let the filter number it |
| Render aborts with `formalism.lua is missing` | Broken or partial install of `infrastructure/rendering/` | Preserve local work, then restore the file from the reviewed source revision or reinstall the package. The render refuses rather than shipping unnumbered output. |

## 11. Statistics, evidence, and claim limits

- Define the research question, estimand, target population, sampling or
  experimental unit, unit of analysis, comparator, and analysis population.
- Report attempted, completed, analyzable, included, excluded, failed,
  unavailable, and non-converged cases separately. Define what every `n`
  counts; do not turn missing or unavailable observations into zero.
- Report an effect estimate and uncertainty appropriate to the design. State
  the interval type and level, test statistic, sidedness, degrees of freedom,
  multiplicity correction, and software implementation when applicable.
- Preserve pairing, clustering, repeated measures, and the correct resampling
  unit in bootstrap, permutation, and cross-validation procedures. Disclose
  stopping, exclusion, missingness, preprocessing, and model-selection rules.
- Do not interpret non-significance as equivalence without a justified margin
  and equivalence analysis. Separate confirmatory, exploratory, post hoc,
  synthetic, historical, and current empirical evidence.
- Use precision justified by measurement and uncertainty. Derive rounded prose,
  tables, captions, and annotations from one raw value rather than independently
  rounding copied literals.
- Map each substantive claim to current analysis evidence or a verified source.
  Narrow novelty, causal, comparative, and generalization language to the
  study design and available evidence; report null and adverse outcomes.

The repository can validate registrations, paths, hashes, and selected claim
records, but automated green checks do not establish study validity or source
support. Use the evidence gate where the project provides a claim ledger:

```bash
uv run python -m infrastructure.validation.cli evidence \
  projects/<qualified-name> --fail-on-issues
uv run python -m infrastructure.validation.cli publication-audit \
  --project <qualified-name> --rendered --strict \
  --require-figure-accessibility --format markdown
```

## 12. Per-project checklist for new authors

Before committing a manuscript change:

- [ ] Every figure has `{#fig:label}` and is referenced with `[@fig:label]` somewhere in the prose.
- [ ] Every generated figure is in `output/figures/figure_registry.json` with
      its generator, self-contained caption, and meaningful explicit alt text;
      complex figures also have a long description, data table, or equivalent.
- [ ] Every table has `{#tbl:label}` and is referenced with `[@tbl:label]`.
- [ ] Every numbered equation has `{#eq:label}` (or `\label{eq:label}` inside a `\begin{equation}` block) and is referenced with `[@eq:label]`.
- [ ] Every section H1 has `{#sec:label}`.
- [ ] Every Definition/Proposition/Theorem is a `::: {.definition #def:label}` block — **no hand-typed numbers** — and is referenced with `[@def:label]`.
- [ ] The build log shows no `formalism.lua: reference to undeclared formalism` or `duplicate label` lines.
- [ ] Every `[@key]` citation resolves in `references.bib`.
- [ ] Each citation supports the adjacent proposition; metadata/existence,
      correction, and retraction checks have explicit outcomes.
- [ ] Cross-section references use `[@sec:label]`, not Markdown filename links.
- [ ] No raw `\cite{}` or `\ref{}` in Markdown source (LaTeX is fine inside math/equation environments).
- [ ] All dynamic values, including caption/table statistics and denominators,
      are source-generated and `{{TOKEN}}`-driven where they appear in
      manuscript text; no generated fact has a hand-copied duplicate.
- [ ] Statistical populations, units, transformations, effect sizes,
      uncertainty, exclusions, and multiplicity treatment agree across prose,
      tables, figures, captions, and alt descriptions.
- [ ] Analysis, hydration, render, provenance, and validation artifacts come
      from one source/configuration lineage, with no hand-edited output.

## See also

- [`projects/templates/template_code_project/manuscript/SYNTAX.md`](../../projects/templates/template_code_project/manuscript/SYNTAX.md) — code-exemplar-specific token table and figure registry.
- [`projects/templates/template_prose_project/manuscript/SYNTAX.md`](../../projects/templates/template_prose_project/manuscript/SYNTAX.md) — prose-exemplar-specific syntax notes.
- [`projects/templates/template_search_project/manuscript/SYNTAX.md`](../../projects/templates/template_search_project/manuscript/SYNTAX.md) — search-exemplar-specific BibTeX-automation notes.
- [`infrastructure/rendering/_pdf_combined_pandoc.py`](../../infrastructure/rendering/_pdf_combined_pandoc.py) — Pandoc `--natbib` invocation (`build_pandoc_tex_command`); [`_pdf_combined_renderer.py`](../../infrastructure/rendering/_pdf_combined_renderer.py) is the backward-compatible re-export facade.
