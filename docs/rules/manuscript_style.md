# Manuscript Style and Formatting Standards

## Overview

This guide provides formatting standards for writing research manuscripts in the `projects/{name}/manuscript/` directory. All manuscript content must follow these standards to ensure consistency, proper rendering, and correct cross-referencing.

**Canonical syntax reference:** [`docs/guides/manuscript-semantics.md`](../guides/manuscript-semantics.md) is the single source of truth for manuscript Markdown semantics. The PDF pipeline runs Pandoc with `--natbib` (converts `[@key]` to natbib citation commands) plus the `pandoc-crossref` filter (resolves `@fig:`, `@tbl:`, `@eq:`, `@sec:` cross-references). Raw `\cite{}` and `\ref{}` work in PDF-only output but **break HTML / EPUB rendering** and are never used in any real exemplar manuscript — this guide teaches the Pandoc-native syntax throughout.

## Lists

### Ordered Lists (Numbered)

Use ordered lists for sequential steps, ranked items, or hierarchical information.

**Markdown Syntax:**

```markdown
1. First item
2. Second item
3. Third item
```

**When to Use:**

- Sequential procedures or steps
- Ranked results or priorities
- Numbered examples or cases
- Hierarchical information with natural ordering

**Example:**

```markdown
The experimental evaluation follows three main steps:

1. **Data Preprocessing**: Normalize and clean input data
2. **Algorithm Execution**: Run optimization with specified parameters
3. **Performance Evaluation**: Compute metrics and generate visualizations
```

### Unordered Lists (Bullets)

Use unordered lists for non-sequential items, features, or options.

**Markdown Syntax:**

```markdown
- First item
- Second item
- Third item
```

**When to Use:**

- Features or characteristics
- Non-sequential items
- Options or alternatives
- General itemization

**Example:**

```markdown
The framework provides several key features:

- Automated test execution with coverage requirements
- Reproducible figure generation from scripts
- Cross-referenced manuscript sections
- Multi-format output (PDF, HTML, LaTeX)
```

### Nested Lists

Nested lists require proper indentation (2 spaces per level).

**Markdown Syntax:**

```markdown
1. Main item
   - Sub-item
   - Another sub-item
2. Second main item
   - Sub-item
     - Sub-sub-item
```

**Example:**

```markdown
The system includes:

1. **Infrastructure Layer**
   - Build verification tools
   - Validation systems
   - Documentation generators
2. **Project Layer**
   - Research algorithms
   - Analysis scripts
   - Manuscript content
```

### List Items with Multiple Paragraphs

For list items with multiple paragraphs, indent subsequent paragraphs.

**Markdown Syntax:**

```markdown
1. First item with multiple paragraphs.

   This is the second paragraph of the first item.
   It should be indented to align with the item content.

2. Second item.
```

### Always Use Markdown Lists

Pandoc converts Markdown `-`/`1.` lists to the correct output-format construct automatically (LaTeX `itemize`/`enumerate` for PDF, `<ul>`/`<ol>` for HTML/EPUB). **Do not write raw `\begin{itemize}`/`\begin{enumerate}` in manuscript Markdown** — it renders correctly in PDF but produces broken or literal output in HTML/EPUB, the same portability problem raw `\cite{}`/`\ref{}` cause. There is no legitimate case in this pipeline for a hand-written LaTeX list environment inside `manuscript/*.md`.

## Equations

### Inline Equations

Use inline equations for mathematical expressions within sentences.

**Syntax:**

```markdown
The variable $x$ represents the optimization parameter.
The function $f(x) = x^2 + 1$ is quadratic.
```

**When to Use:**

- Short mathematical expressions in text
- Variables, parameters, or simple formulas
- Mathematical notation within sentences

**Example:**

```markdown
The algorithm updates the solution $x_k$ according to the gradient
$\nabla f(x_k)$, where $k$ is the iteration index.
```

### Display Equations

Use a standalone, numbered block for equations that should be centered, numbered, and cross-referenced.

**Preferred syntax — pure Pandoc:**

```markdown
$$
f(x) = \sum_{i=1}^{n} w_i \phi_i(x) + \lambda R(x)
$$ {#eq:objective}
```

**Also acceptable — raw-LaTeX `equation` environment (pandoc-crossref still resolves the label):**

```markdown
\begin{equation}
\label{eq:objective}
f(x) = \sum_{i=1}^{n} w_i \phi_i(x) + \lambda R(x)
\end{equation}
```

Both forms number correctly and both labels resolve via `[@eq:objective]`. Prefer the `$$ … $$ {#eq:label}` form for new content — it's shorter and doesn't imply a LaTeX-only dependency.

**When to Use:**

- Important equations that are referenced
- Complex mathematical expressions
- Equations that need numbering
- Key results or definitions

**Example:**

```markdown
The optimization problem we solve is:

$$
\min_{x \in \mathcal{X}} f(x) \quad \text{subject to} \quad g_i(x) \leq 0, \quad i = 1, \ldots, m
$$ {#eq:optimization}

where $\mathcal{X}$ is the feasible set.
```

### Equation Labels

All important equations must have descriptive labels.

**Naming Convention:**

- Prefix: `eq:`
- Format: `{#eq:descriptive_name}` (or `\label{eq:descriptive_name}` inside a raw `equation` environment)
- Use lowercase with underscores
- Be descriptive, not generic

**Good Examples:**

```markdown
{#eq:objective}
{#eq:convergence_rate}
{#eq:update_rule}
{#eq:adaptive_step_size}
```

**Bad Examples:**

```markdown
{#eq:1}           # Too generic
{#eq:eq1}         # Redundant prefix
{#eq:MyEquation}  # Inconsistent case
```

### Equation References

**Reference equations with `[@eq:label]`, never `\eqref{}` or `\ref{}`.** The bracketed cross-reference form renders as "eq. 1" (or "Equation 1" with `cleveref`) in every output format; `\eqref{}` requires LaTeX-only output and breaks HTML/EPUB.

**Syntax:**

```markdown
As shown in [@eq:objective], the objective function...
The convergence rate [@eq:convergence] demonstrates...
```

**Placement:**

- Before punctuation: "Equation [@eq:name] shows..."
- In parentheses: "The result (see [@eq:name]) indicates..."
- As part of sentence: "Using [@eq:name], we derive..."
- Narrative form: "@eq:name shows that..." (no brackets — reads as "Equation 1 shows that...")

### Multi-Line Equations

For equations spanning multiple lines, use `align` or `split` environments — pandoc-crossref resolves labels on these the same way as a plain `equation` block.

**Align Environment (multiple equations):**

```markdown
\begin{align}
x_{k+1} &= x_k - \alpha_k \nabla f(x_k) \\
y_{k+1} &= y_k + \beta_k (x_k - x_{k-1})
\end{align} {#eq:system}
```

**Split Environment (single equation, multiple lines):**

```markdown
$$
\begin{split}
f(x) &= \sum_{i=1}^{n} w_i \phi_i(x) \\
     &\quad + \lambda \sum_{j=1}^{m} |x_j| \\
     &\quad + \gamma \|x\|^2
\end{split}
$$ {#eq:complex}
```

### Numbering Conventions

- Equations are automatically numbered by `pandoc-crossref`
- Numbering is sequential throughout the document
- Supplemental sections use separate numbering (S1, S2, etc.) if the project configures a supplement prefix

### DO NOT Use

**Never place a display-math delimiter inline in the middle of a running prose sentence:**

```markdown
Prose $$ f(x) = x^2 $$ continues here.     # ❌ BAD: breaks paragraph flow
```

**Always give a display equation its own block, with a label:**

```markdown
$$
f(x) = x^2
$$ {#eq:name}
```

## Figures

Manuscript figures use standard Pandoc image syntax — never a raw `\begin{figure}...\end{figure}`/`\includegraphics{}` block. Pandoc converts a labeled image to a numbered, captioned figure in every output format (PDF, HTML, EPUB); a hand-written LaTeX figure environment only works in PDF.

### Figure Syntax

```markdown
![Descriptive caption explaining the figure.](../output/figures/figure_name.png){#fig:figure_name width=80%}
```

- The bracketed text `[...]` is the caption.
- The parenthesized path `(...)` is the image path.
- The brace attributes `{#fig:label width=...}` carry the cross-reference label and sizing.

### Figure Sizing

Control figure size with the `width` (or `height`) attribute — a fraction of the text width, not a raw `\includegraphics[width=...\textwidth]` command.

**Common Sizes:**

```markdown
{#fig:name width=50%}   # Half page width
{#fig:name width=80%}   # 80% page width (most common)
{#fig:name width=90%}   # 90% page width
{#fig:name width=100%}  # Full page width
```

**Best Practice:** Use `width=80%` for most figures to leave margins.

### Figure Paths

All figures must use relative paths from the manuscript directory.

**Path Format:**

```markdown
../output/figures/figure_name.png
```

**Requirements:**

- Paths are relative to `projects/{name}/manuscript/` (Pandoc resolves them via `--resource-path`)
- Figures are stored in `projects/{name}/output/figures/`
- Use forward slashes (`/`) even on Windows
- Include file extension (`.png` preferred for archival stability)

**Example:**

```markdown
![Convergence plot showing objective value vs iteration.](../output/figures/convergence_plot.png){#fig:convergence width=90%}
```

### Figure Captions

Captions must be descriptive and complete sentences. They appear under the figure in the PDF **and as alt text in HTML/EPUB output**, so they must be self-contained — never "see above" or content that depends on the figure being visible.

**Format:**

- Start with capital letter
- End with period
- Describe what the figure shows
- Include key information (method, dataset, result)

**Good Examples:**

```markdown
![Algorithm convergence comparison showing performance improvement over baseline methods.](../output/figures/convergence.png){#fig:convergence}
![Experimental setup diagram illustrating the data processing pipeline.](../output/figures/setup.png){#fig:setup}
![Scalability analysis demonstrating $O(n \log n)$ computational complexity.](../output/figures/scalability.png){#fig:scalability}
```

**Bad Examples:**

```markdown
![convergence plot](../output/figures/convergence.png){#fig:convergence}      # Too brief, not a sentence
![Figure showing results](../output/figures/results.png){#fig:results}       # Vague, doesn't describe content
![Results.](../output/figures/results.png){#fig:results}                     # Incomplete sentence
```

### Figure Labels

All figures must have descriptive labels.

**Naming Convention:**

- Prefix: `fig:`
- Format: `{#fig:descriptive_name}`
- Use lowercase with underscores
- Match filename when possible

**Good Examples:**

```markdown
{#fig:convergence_plot}
{#fig:experimental_setup}
{#fig:scalability_analysis}
{#fig:ablation_study}
```

**Bad Examples:**

```markdown
{#fig:1}              # Too generic
{#fig:figure1}        # Redundant prefix
{#fig:MyFigure}       # Inconsistent case
```

### Figure References

**Reference figures using `[@fig:label]`, never `\ref{}`.**

**Syntax:**

```markdown
As shown in [@fig:convergence_plot], the algorithm...
The experimental setup ([@fig:experimental_setup]) includes...
```

**Placement:**

- Capitalize "Figure" when starting a sentence (with `cleveref`/`--number-sections`, `[@fig:name]` renders as "Fig. 3" or "Figure 3" depending on style; write prose so capitalization reads naturally either way)
- Place reference before or after the figure as the narrative requires

**Examples:**

```markdown
[@fig:convergence_plot] shows the convergence behavior.
The results, shown in [@fig:results], demonstrate...
As illustrated in [@fig:setup], the system includes...
```

### Supported Formats

- PNG (recommended for plots — archival stability, 300 dpi, colourblind-safe palette)
- PDF (recommended for vector graphics)
- JPG/JPEG (for photographs)

## Tables

Manuscript tables use Pandoc pipe-tables with a caption line — never a raw `\begin{table}...\begin{tabular}...\end{table}` block. Pipe-tables render correctly in PDF, HTML, and EPUB; a hand-written LaTeX table only works in PDF.

### Table Syntax

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Row 1, Col 1 | Row 1, Col 2 | Row 1, Col 3 |
| Row 2, Col 1 | Row 2, Col 2 | Row 2, Col 3 |

: Descriptive caption explaining the table. {#tbl:table_name}
```

The caption line (`: <caption text> {#tbl:label}`) goes **directly below the table, no blank line in between** — that's what attaches it to the table for numbering.

### Column Alignment

Pipe-table alignment is set with colons in the header separator row, not a LaTeX `l`/`c`/`r`/`|` column-spec string.

**Examples:**

```markdown
| Left | Center | Right |
|:-----|:------:|------:|
```

### Table Captions

Follow the same caption guidelines as figures.

**Format:**

- Descriptive and complete sentences
- Start with capital letter
- End with period
- Place directly below the table body, as the `: caption {#tbl:label}` line

**Example:**

```markdown
: Performance comparison showing accuracy and execution time for different methods. {#tbl:performance_comparison}
```

### Table Labels

All tables must have descriptive labels.

**Naming Convention:**

- Prefix: `tbl:`
- Format: `{#tbl:descriptive_name}`
- Use lowercase with underscores

**Good Examples:**

```markdown
{#tbl:performance_comparison}
{#tbl:dataset_summary}
{#tbl:hyperparameter_settings}
```

### Table References

**Reference tables using `[@tbl:label]`, never `\ref{tab:name}` or a hardcoded "Table 1".**

**Syntax:**

```markdown
[@tbl:performance_comparison] shows...
The results (see [@tbl:results]) indicate...
```

### Dynamic Table Bodies

For table rows generated from analysis output rather than hand-typed, use a `{{TOKEN}}` placeholder inside the table body — see [`template_code_project/manuscript/03_results.md`](../../projects/templates/template_code_project/manuscript/03_results.md) (`RESULT_TABLE_ROWS`) for a real example. Never hardcode a number that changes with `config.yaml` or an analysis re-run.

### Complex Tables (merged cells)

Pandoc pipe-tables cannot express merged cells (`multirow`/`multicolumn`). No current public exemplar needs this; if a project genuinely requires it, a raw LaTeX `table`/`tabular` block is a PDF-only escape hatch — document the HTML/EPUB degradation explicitly in the project's own manuscript `AGENTS.md` if you use it, and prefer restructuring the table (e.g., a second small pipe-table, or splitting one wide column) over reaching for `multirow` first.

## Citations

### Citation Format

**Use Pandoc bracket-cite syntax, never `\cite{}`, `\citep{}`, or `\citet{}`.** Pandoc emits the correct LaTeX citation command automatically under `--natbib` at render time; hand-writing `\cite{}` in the Markdown source works in PDF only and breaks HTML/EPUB.

**Basic Syntax:**

```markdown
According to recent research [@author2023], this method...
The algorithm [@kingma2014] demonstrates...
```

**Narrative form** (author name reads as part of the sentence):

```markdown
@kingma2014 demonstrated that...
```

**Suppressed-author form** (year/number only, e.g. after the author was just named):

```markdown
Kingma and Ba [-@kingma2014] later extended this to...
```

### Multiple Citations

Cite multiple sources semicolon-separated inside one bracket pair.

**Syntax:**

```markdown
[@key1; @key2; @key3]
```

**Example:**

```markdown
Previous work [@boyd2004; @nesterov2018; @kingma2014] has shown...
```

### Citations With a Locator

```markdown
[@knuth1997, pp. 42-45]
```

### Citation Placement

Place citations before punctuation marks.

**Correct:**

```markdown
The method works well [@author2023].
Previous research [@key1; @key2] has demonstrated this.
```

**Incorrect:**

```markdown
The method works well.[@author2023]  # ❌ After punctuation
```

### Citation Keys

Citation keys are case-sensitive and must match entries in `references.bib`.

**Requirements:**

- Keys are defined in `projects/{name}/manuscript/references.bib` (Pandoc merges every `manuscript/*.bib`, so a project with a supplemental bib file like `references_deep.bib` just drops it alongside)
- Use exact key spelling (case-sensitive)
- Keys typically follow the auto-generator convention `<surname><year><titleword>` — e.g. `boyd2004convex`, `kingma2014adam`

**Example:**

```bibtex
@article{kingma2014,
  title={Adam: A Method for Stochastic Optimization},
  author={Kingma, Diederik P and Ba, Jimmy},
  journal={arXiv preprint arXiv:1412.6980},
  year={2014}
}
```

**Usage:**

```markdown
The Adam optimizer [@kingma2014] provides...
```

An undefined key surfaces as `[?]` in the rendered PDF and as a warning in the build log — this is the fastest way to spot a typo'd or missing citation.

## Section Headings

### Heading Hierarchy

Use consistent heading levels to maintain document structure.

**Levels:**

- `#` - Main section (e.g., "Introduction", "Methodology")
- `##` - Subsection (e.g., "Experimental Setup", "Results")
- `###` - Subsubsection (e.g., "Convergence Analysis", "Ablation Studies")
- `####` - Paragraph-level heading (use sparingly)

**Never manually number a heading** (e.g. `## 2.1 Search`) — write the plain heading text and let Pandoc's `--number-sections` apply the prefix automatically; a manual prefix collides with autonumbering and produces "2 2.1 Search" in the rendered output.

**Example:**

```markdown
# Methodology {#sec:methodology}

## Mathematical Framework

### Optimization Problem

#### Convex Case
```

### Section Labels

**Every top-level section heading carries a `{#sec:<short_name>}` label.** This enables `[@sec:methodology]` cross-references that stay stable under section reordering.

**Naming Convention:**

- Prefix: `sec:`
- Format: `{#sec:descriptive_name}`
- Use lowercase with underscores
- Place in heading: `# Section Title {#sec:section_name}`

**Example:**

```markdown
# Introduction {#sec:introduction}

## Experimental Setup {#sec:experimental_setup}
```

### Section References

**Reference sections using `[@sec:label]`, never `\ref{}` and never a Markdown filename link** (`[see methodology](02_methodology.md)` resolves in an editor but not in the rendered PDF).

**Syntax:**

```markdown
As described in [@sec:methodology]...
The results (see [@sec:results]) show...
```

### Numbering

Section numbering is automatic via Pandoc's `--number-sections`.

- Main sections: 1, 2, 3, ...
- Subsections: 1.1, 1.2, 2.1, ...
- Subsubsections: 1.1.1, 1.1.2, ...

### Consistent Heading Structure

Maintain consistent heading structure across all manuscript files.

**Recommended Structure:**

```markdown
# Main Section {#sec:name}

## Subsection

### Subsubsection

## Another Subsection
```

## Text Formatting

### Emphasis (Italic)

Use for emphasis, technical terms, or variable names in text.

```markdown
The *optimization variable* $x$ represents...
```

### Bold

Use for strong emphasis or key terms.

```markdown
The **key contribution** of this work is...
```

### Code

Use for code, function names, or technical terms.

```markdown
The function `calculate_average()` computes...
```

Prefer Markdown backtick-code over raw `\texttt{}` — Pandoc converts backtick spans to the correct monospace construct in every output format. Raw `\texttt{}` does appear inside math-mode expressions in a couple of exemplars (e.g. a piecewise-definition table cell), which is fine — that's LaTeX math syntax, not a manuscript-formatting escape hatch.

### Inline Code in Equations

Code can appear in equations when appropriate.

**Example:**

```markdown
The function $f(\texttt{x})$ where $\texttt{x}$ is a vector...
```

### Special Characters

Escape special LaTeX characters when they appear in ordinary prose text (not inside `$...$` math mode, where most of these are meaningful operators).

**Common Escaping:**

- `%` → `\%`
- `&` → `\&`
- `$` → `\$`
- `#` → `\#`
- `_` → `\_` (in text, not in math mode)
- `{` → `\{`
- `}` → `\}`

## Cross-Referencing Patterns

All cross-references use Pandoc-crossref bracket syntax — `[@sec:]`, `[@eq:]`, `[@fig:]`, `[@tbl:]` — never `\ref{}` or `\eqref{}`.

### Section → Section

```markdown
As discussed in [@sec:methodology]...
The experimental setup ([@sec:experimental_setup]) includes...
See [@sec:results] for detailed analysis.
```

### Section → Equation

```markdown
The objective function [@eq:objective] defines...
Using [@eq:convergence], we can show...
As shown in [@eq:update], the algorithm...
```

### Section → Figure

```markdown
[@fig:convergence_plot] shows...
The results (see [@fig:results]) demonstrate...
As illustrated in [@fig:setup], the system...
```

### Section → Table

```markdown
[@tbl:performance_comparison] summarizes...
The data ([@tbl:dataset]) shows...
See [@tbl:results] for statistics.
```

### Multiple References

Combine multiple references in a single sentence — each gets its own bracket pair.

```markdown
The methodology ([@sec:methodology]) and results
([@sec:results]) demonstrate...

Equations [@eq:objective] and [@eq:optimization] define...

Figures [@fig:convergence] and [@fig:scalability] show...
```

### Reference Placement in Sentences

Place references naturally within sentences.

**Good Examples:**

```markdown
The algorithm described in [@sec:methodology] achieves
the convergence rate shown in [@eq:convergence].

As shown in [@fig:results], the method outperforms
baselines (see [@tbl:comparison]).
```

**Bad Examples:**

```markdown
The algorithm. See [@sec:methodology].  # ❌ Fragmented
[@fig:results]. Shows results.          # ❌ Fragmented
```

## Best Practices

### Label Naming Conventions

**Guidelines:**

- Use descriptive names, not numbers
- Be consistent across document
- Use lowercase with underscores
- Match content purpose (`eq:`, `fig:`, `tbl:`, `sec:`)

**Good:**

```markdown
{#eq:convergence_rate}
{#fig:experimental_setup}
{#tbl:performance_comparison}
{#sec:methodology}
```

**Bad:**

```markdown
{#eq:1}
{#fig:figure1}
{#tbl:table}
{#sec:sec1}
```

### Reference Validation

**Before Building:**

- Verify every `[@eq:]`, `[@fig:]`, `[@tbl:]`, `[@sec:]` target has a matching label somewhere in the manuscript
- Check label spelling matches exactly
- Ensure all figures/tables/equations have labels
- Run validation: `uv run python -m infrastructure.validation.cli markdown manuscript/`

### Figure/Table Placement Guidelines

Pandoc places figures and tables at their position in the source flow (float behavior is controlled by the renderer's LaTeX template, not by a per-figure placement specifier in the Markdown). Place the figure/table Markdown block near its first reference in the prose.

### Equation Numbering Strategy

**Numbering Guidelines:**

- Give a label (`{#eq:label}`) to every equation that's referenced
- Number key results and definitions
- Don't label trivial or obvious inline equations
- Use consistent labeling across sections

### Citation Management

**Best Practices:**

- Add all citations to `references.bib` first
- Use consistent key naming (`authorYYYY` or `authorYYYYkeyword`)
- Verify keys match exactly (case-sensitive)
- Keep bibliography file organized

## Common Mistakes to Avoid

### Using Inline `$$` for Display Math

**Never place display delimiters inline in prose:**

```markdown
Prose $$ f(x) = x^2 $$ continues here.
```

**Always give it its own labeled block:**

```markdown
$$
f(x) = x^2
$$ {#eq:name}
```

### Missing Labels

**Never:**

```markdown
$$
f(x) = x^2
$$
```

**Always:**

```markdown
$$
f(x) = x^2
$$ {#eq:name}
```

### Incorrect Path References

**Never:**

```markdown
![caption](figures/figure.png){#fig:name}           # ❌ Wrong path — missing ../output
![caption](output/figures/figure.png){#fig:name}     # ❌ Wrong path — missing ../
```

**Always:**

```markdown
![caption](../output/figures/figure.png){#fig:name}  # ✅ Correct relative path
```

### Case-Sensitive Citation Keys

**Never:**

```markdown
[@Kingma2014]  # ❌ Wrong case
```

**Always:**

```markdown
[@kingma2014]  # ✅ Correct case, matches references.bib exactly
```

### Inconsistent Label Naming

**Never:**

```markdown
{#eq:Objective}      # ❌ Inconsistent case
{#eq:objective_func} # ❌ Inconsistent style
{#eq:obj}             # ❌ Too abbreviated
```

**Always:**

```markdown
{#eq:objective}      # ✅ Consistent, descriptive
```

### Raw LaTeX Cross-References

**Never** use `\ref{}`, `\eqref{}`, or `\cite{}` in manuscript Markdown — they render in PDF-only output and break HTML/EPUB.

```markdown
As shown in Figure \ref{fig:convergence}...   # ❌ PDF-only, breaks HTML/EPUB
```

**Always use the bracket cross-reference form:**

```markdown
As shown in [@fig:convergence]...             # ✅ Works in every output format
```

## Examples

### Figure Example

```markdown
![Algorithm convergence comparison showing performance improvement
over baseline methods. The plot demonstrates exponential convergence
with rate $\rho \approx 0.85$.](../output/figures/convergence_plot.png){#fig:convergence_plot width=90%}

As shown in [@fig:convergence_plot], our method achieves
faster convergence than existing approaches.
```

### Table Example

```markdown
| Method | Accuracy | Time (s) |
|--------|:--------:|:--------:|
| Baseline | 0.85 | 10.2 |
| Our Method | 0.92 | 8.5 |

: Performance comparison showing accuracy and execution time
for different optimization methods. {#tbl:performance_comparison}

[@tbl:performance_comparison] demonstrates that our method
achieves higher accuracy with reduced computation time.
```

### Equation Example

```markdown
The optimization problem we solve is:

$$
\min_{x \in \mathcal{X}} f(x) \quad \text{subject to} \quad g_i(x) \leq 0, \quad i = 1, \ldots, m
$$ {#eq:optimization}

where $\mathcal{X}$ is the feasible set and $g_i(x)$ are constraint
functions. The solution to [@eq:optimization] is obtained using
the iterative algorithm described in [@sec:algorithm].
```

## See Also

- [docs/guides/manuscript-semantics.md](../guides/manuscript-semantics.md) - Canonical single source of truth for manuscript syntax
- [docs/usage/style-guide.md](../usage/style-guide.md) - User-facing manuscript style guide (equations, figures, captions, tables)
- [projects/templates/template_code_project/manuscript/](../../projects/templates/template_code_project/manuscript/) - Example manuscript (active project)
- [docs/usage/markdown-template-guide.md](../usage/markdown-template-guide.md) - Markdown and cross-referencing guide
- [docs/usage/manuscript-numbering-system.md](../usage/manuscript-numbering-system.md) - Section numbering system
- [code_style.md](code_style.md) - Code formatting standards
- [documentation_standards.md](documentation_standards.md) - Documentation writing guide
