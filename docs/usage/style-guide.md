# ✍️ Manuscript Style Guide

> **How to format equations, figures, captions, and tables** in your research manuscript

**Quick Reference:** [Markdown Template Guide](markdown-template-guide.md) | [Image Management](image-management.md) | [Visualization Guide](visualization-guide.md)

This guide provides clear, example-driven formatting patterns for writing research content in `projects/{name}/manuscript/`. For exhaustive rules, see [`docs/rules/manuscript_style.md`](../rules/manuscript_style.md).

## 📖 Table of Contents

- [Equations](#equations)
- [Figures](#figures)
- [Captions](#captions)
- [Tables](#tables)
- [Cross-Referencing Quick Reference](#cross-referencing-quick-reference)
- [Common Mistakes](#common-mistakes)

---

## Equations

### Inline Equations

Use single dollar signs for math within a sentence:

```markdown
The variable $x$ represents the optimization parameter.
The loss is defined as $\mathcal{L}(\theta) = -\log p(y \mid x; \theta)$.
```

**When to use:** variable names, simple expressions, mathematical notation woven into prose.

### Display Equations

Use a labelled display block for standalone, numbered equations. **Always include a label.**

```markdown
The optimization objective is:

$$
f(x) = \sum_{i=1}^{n} w_i \phi_i(x) + \lambda R(x)
$$ {#eq:objective}

where $\lambda$ controls regularization strength.
```

The `\begin{equation}\label{eq:objective}…\end{equation}` raw-LaTeX form also
works (pandoc-crossref still picks up `\label{}`), but the `$$ … $$ {#eq:name}`
form above is the pure-Pandoc, PDF/HTML/EPUB-portable default — see
[Manuscript Semantics](../guides/manuscript-semantics.md).

**Key rules:**

- ✅ Use isolated Pandoc display math blocks: `$$ ... $$` on their own line(s)
- ✅ For numbered equations, use the project's registry/crossref syntax or a labelled `equation` environment when the target is PDF-only
- ❌ **Never** use inline `$$ ... $$` inside prose
- ❌ **Never** use `\[ ... \]` — Pandoc emits literal brackets in HTML

### Multi-Line Equations

**Multiple related equations** — use `align`:

```markdown
\begin{align}
\label{eq:gradient_update}
x_{k+1} &= x_k - \alpha_k \nabla f(x_k) \\
y_{k+1} &= y_k + \beta_k (x_k - x_{k-1})
\end{align}
```

**Single equation broken across lines** — use `split` inside `equation`:

```markdown
\begin{equation}
\label{eq:loss_expanded}
\begin{split}
\mathcal{L}(\theta) &= \frac{1}{N} \sum_{i=1}^{N} \ell(y_i, \hat{y}_i) \\
    &\quad + \lambda_1 \|\theta\|_1 \\
    &\quad + \lambda_2 \|\theta\|_2^2
\end{split}
\end{equation}
```

### Referencing Equations

Use `[@eq:label]` (never raw `\eqref{}` or `\ref{}`) to reference equations — this is the one form that renders correctly in PDF, HTML, and EPUB alike:

```markdown
As shown in [@eq:objective], the regularization term controls...
Combining [@eq:gradient_update] with the convergence bound...
```

### Equation Label Conventions

| Convention  | Example               | Notes                                          |
| ----------- | --------------------- | ---------------------------------------------- |
| Prefix      | `eq:`                 | Always required                                |
| Case        | lowercase             | `eq:convergence_rate` not `eq:Convergence_Rate` |
| Separator   | underscore            | `eq:step_size` not `eq:step-size`              |
| Descriptive | required              | `eq:convergence_rate` not `eq:1`               |

---

## Figures

### Complete Figure Block

Every figure follows this exact structure — Pandoc image syntax with a
`{#fig:name}` attribute, **not** a raw LaTeX `figure` environment (see
[Manuscript Semantics](../guides/manuscript-semantics.md)):

```markdown
![Algorithm convergence comparison showing exponential decay
with rate $\rho \approx 0.85$ across all benchmark datasets.](../output/figures/convergence_plot.png){#fig:convergence_plot width=80%}
```

**Element-by-element breakdown:**

| Element                | Purpose                              | Required? |
| ----------------------- | ------------------------------------ | --------- |
| `![caption](path)`      | Pandoc image syntax                  | ✅        |
| Caption text            | Descriptive sentence(s)              | ✅        |
| `{#fig:name}`           | Cross-reference target               | ✅        |
| `width=…`               | Sizing attribute                     | ✅        |

### Placement

Pandoc/pandoc-crossref places each figure inline at the point in the
Markdown source where it appears; there is no LaTeX-style placement
specifier (`[h]`/`[t]`/`[b]`) to choose. Position figures in the prose flow
where they are first discussed.

### Figure Sizing

```markdown
![...](path){#fig:name width=50%}    % Half page — side-by-side pairs
![...](path){#fig:name width=80%}    % 80% width — MOST COMMON
![...](path){#fig:name width=90%}    % 90% width — wide figures
![...](path){#fig:name width=100%}   % Full width — panoramic/wide data
```

**Best practice:** Use `width=80%` unless you have a reason not to.

### Figure Paths

All paths are **relative to `projects/{name}/manuscript/`**:

```markdown
% ✅ Correct — relative path from manuscript/
![...](../output/figures/my_figure.png){#fig:my_figure}

% ❌ Wrong — absolute path
![...](/Users/me/projects/{name}/output/figures/my_figure.png){#fig:my_figure}

% ❌ Wrong — relative but missing ../
![...](output/figures/my_figure.png){#fig:my_figure}
```

### Supported Image Formats

| Format  | Best for                         | Notes                             |
| ------- | -------------------------------- | --------------------------------- |
| **PNG** | Plots, diagrams, screenshots     | Recommended for most figures      |
| **PDF** | Vector graphics, line drawings   | Scales without artifacts          |
| **JPG** | Photographs                      | Lossy — avoid for plots           |

### Referencing Figures

Use `[@fig:name]` (never raw `\ref{}`):

```markdown
[@fig:convergence_plot] shows the convergence behavior.
The results ([@fig:results]) demonstrate improvement.
As illustrated in [@fig:setup], the pipeline includes...
```

`[@fig:name]` renders as "Figure 3" (parenthetical) or use bare `@fig:name`
for a narrative reference ("Figure 3 shows…").

---

## Captions

Captions are the single most important piece of text for each figure and table. A reader should understand the key message from the caption alone.

### Caption Rules

1. **Write complete sentences** — start with a capital letter, end with a period
2. **Describe what the figure shows**, not just what it is
3. **Include key information** — method name, dataset, metric, key finding
4. **Include inline math** when it adds precision

### Good vs. Bad Captions

The caption text is the bracketed part of the Pandoc image syntax
`![caption text](path){#fig:name}`:

```markdown
% ✅ GOOD — descriptive, complete sentence, includes key details
Algorithm convergence comparison showing performance improvement
over baseline methods on the CIFAR-10 dataset.

% ✅ GOOD — includes mathematical precision
Scalability analysis demonstrating $O(n \log n)$ computational
complexity for the proposed method across problem sizes $n = 10^2$ to $10^6$.

% ✅ GOOD — describes the insight, not just the data
Ablation study results showing that removing the attention mechanism
reduces accuracy by 12.3\%, confirming its importance for feature extraction.
```

```markdown
% ❌ BAD — too brief, not a sentence
convergence plot

% ❌ BAD — vague, tells you nothing
Figure showing results

% ❌ BAD — incomplete sentence
Results.

% ❌ BAD — just names the type of chart
Bar chart of performance
```

### Caption Template

When in doubt, use this pattern:

```text
[What is shown] [on what data/conditions] [highlighting what finding/result].
```

Examples:

```markdown
![Training loss curves for three model variants on ImageNet,
showing that Model C converges 2.1× faster than the baseline.](../output/figures/loss_curves.png){#fig:loss_curves}

![Distribution of prediction errors across 500 test samples,
demonstrating a mean absolute error of $0.032 \pm 0.008$.](../output/figures/error_distribution.png){#fig:error_distribution}
```

---

## Tables

### Complete Table Block

Use a Markdown pipe-table with the caption attached via `: <caption> {#tbl:name}`
placed **directly below the table** (no blank line) — not a raw LaTeX `table`
environment (see [Manuscript Semantics](../guides/manuscript-semantics.md)):

```markdown
| Method           | Accuracy (%) | Time (s) |
|------------------|--------------|----------|
| Baseline         | 85.2         | 10.2     |
| Our Method       | 92.7         | 8.5      |
| Our Method + Aug | **94.1**     | 9.1      |

: Performance comparison showing accuracy and execution time
for different optimization methods on the benchmark dataset. {#tbl:performance_comparison}
```

### Column Alignment

Pipe-table alignment is controlled by colon placement in the separator row:

| Specifier | Alignment | Typical use                         |
| --------- | --------- | ----------------------------------- |
| `---`     | Left (default) | Text, method names              |
| `:---:`   | Center    | Numbers, short values               |
| `---:`    | Right     | Numeric data for decimal alignment  |

### Highlighting Best Results

Bold the best value in each column with Markdown `**bold**`:

```markdown
| Baseline   | 85.2         | 10.2     |
| Our Method | **92.7**     | **8.5**  |
```

### Table Label Conventions

Same rules as equation and figure labels:

```markdown
{#tbl:performance_comparison}    % ✅ Descriptive
{#tbl:dataset_summary}           % ✅ Descriptive
{#tbl:1}                         % ❌ Generic
```

### Referencing Tables

Use `[@tbl:name]` (never raw `\ref{}`):

```markdown
[@tbl:performance_comparison] summarizes the results.
The hyperparameters ([@tbl:hyperparameters]) were tuned via grid search.
```

---

## Cross-Referencing Quick Reference

| Element      | Label format          | Reference syntax    | In-text example                            |
| ------------ | --------------------- | -------------------- | ------------------------------------------ |
| **Equation** | `{#eq:name}` (or `\label{eq:name}` inside `equation`) | `[@eq:name]` | "as shown in [@eq:loss]"       |
| **Figure**   | `{#fig:name}`          | `[@fig:name]`         | "[@fig:setup] shows"                       |
| **Table**    | `{#tbl:name}`          | `[@tbl:name]`         | "[@tbl:results] lists"                     |
| **Section**  | `{#sec:name}`          | `[@sec:name]`         | "[@sec:method] describes"                  |
| **Citation** | key in `.bib`          | `[@key]`              | "prior work [@smith2023]"                  |

Never use raw `\ref{}`, `\eqref{}`, or `\cite{}` — Pandoc bracket-cite/crossref
syntax is the one form that renders correctly in PDF, HTML, and EPUB alike
(see [Manuscript Semantics](../guides/manuscript-semantics.md)).

**All labels must be:**

- Lowercase with underscores: `eq:convergence_rate`
- Descriptive: `fig:ablation_study` not `fig:1`
- Unique across the entire manuscript

---

## Common Mistakes

| ❌ Mistake                           | ✅ Correct                                                             | Why                                          |
| ------------------------------------ | ---------------------------------------------------------------------- | -------------------------------------------- |
| `Prose $$ f(x)=x^2 $$`              | `$$ f(x)=x^2 $$` on its own line or registered equation syntax       | Inline `$$` is fragile across render targets |
| `![...](figures/fig.png){#fig:x}`   | `![...](../output/figures/fig.png){#fig:x}`                            | Paths are relative to `manuscript/`          |
| Caption "results" (too brief)       | "Comparison of model accuracy across three benchmarks."                | Captions must be complete sentences         |
| `{#eq:1}`                            | `{#eq:convergence_rate}`                                               | Labels must be descriptive                   |
| `[@Kingma2014]`                      | `[@kingma2014]`                                                        | Citation keys are case-sensitive             |
| Missing `{#eq:name}` on equation    | Always add `{#eq:name}`                                                | Every referenced equation needs a label      |
| Raw `\ref{}`/`\eqref{}`/`\cite{}`   | `[@fig:name]` / `[@eq:name]` / `[@key]`                                | Raw LaTeX cross-refs break HTML/EPUB         |

---

## Related Documentation

- **[Manuscript Style Reference](../rules/manuscript_style.md)** — Exhaustive formatting rules (1000+ lines)
- **[Markdown Template Guide](markdown-template-guide.md)** — Cross-referencing system and build process
- **[Figures and Analysis Guide](../guides/figures-and-analysis.md)** — Creating figure scripts with the thin orchestrator pattern
- **[Image Management](image-management.md)** — Programmatic `ImageManager` and `FigureManager` APIs
- **[Visualization Guide](visualization-guide.md)** — `VisualizationEngine` for publication-quality figures
- **[Manuscript Numbering](manuscript-numbering-system.md)** — Section numbering conventions (01-09, S01-S0N, 98-99)
