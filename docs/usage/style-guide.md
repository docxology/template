# ✍️ Manuscript Style Guide

> **How to format equations, figures, captions, and tables** in your research manuscript

**Quick Reference:** [Markdown Template Guide](markdown-template-guide.md) | [Image Management](image-management.md) | [Visualization Guide](visualization-guide.md)

This guide provides clear, example-driven formatting patterns for writing research content in `projects/{name}/manuscript/`. For exhaustive rules, see [`.cursorrules/manuscript_style.md`](../../.cursorrules/manuscript_style.md).

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

Use the `equation` environment for standalone, numbered equations. **Always include a label.**

```markdown
The optimization objective is:

\begin{equation}
\label{eq:objective}
f(x) = \sum_{i=1}^{n} w_i \phi_i(x) + \lambda R(x)
\end{equation}

where $\lambda$ controls regularization strength.
```

**Key rules:**

- ✅ Use `\begin{equation}` … `\end{equation}`
- ✅ Always add `\label{eq:descriptive_name}`
- ❌ **Never** use `$$ ... $$` — it produces unnumbered, unlabellable equations
- ❌ **Never** use `\[ ... \]` — same problem

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

Use `\eqref{}` (not `\ref{}`) to reference equations — it automatically adds parentheses:

```markdown
As shown in \eqref{eq:objective}, the regularization term controls...
Combining \eqref{eq:gradient_update} with the convergence bound...
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

Every figure follows this exact structure:

```markdown
\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/convergence_plot.png}
\caption{Algorithm convergence comparison showing exponential decay
with rate $\rho \approx 0.85$ across all benchmark datasets.}
\label{fig:convergence_plot}
\end{figure}
```

**Element-by-element breakdown:**

| Element                              | Purpose                              | Required? |
| ------------------------------------ | ------------------------------------ | --------- |
| `\begin{figure}[h]`                 | Float environment with placement hint | ✅        |
| `\centering`                        | Center the image horizontally        | ✅        |
| `\includegraphics[width=…]{path}`   | Insert the image file                | ✅        |
| `\caption{…}`                       | Descriptive sentence(s)              | ✅        |
| `\label{fig:…}`                     | Cross-reference target               | ✅        |
| `\end{figure}`                      | Close float environment              | ✅        |

### Placement Specifiers

| Specifier | Meaning                            | When to use                          |
| --------- | ---------------------------------- | ------------------------------------ |
| `[h]`     | Here (preferred position)          | **Default** — most figures           |
| `[t]`     | Top of page                        | Large figures that disrupt flow      |
| `[b]`     | Bottom of page                     | Secondary figures                    |
| `[H]`     | Force here (requires `float` pkg)  | Only when exact position is critical |
| `[!htbp]` | Try all positions                  | Last resort                          |

### Figure Sizing

```markdown
\includegraphics[width=0.5\textwidth]{...}   % Half page — side-by-side pairs
\includegraphics[width=0.8\textwidth]{...}   % 80% width — MOST COMMON
\includegraphics[width=0.9\textwidth]{...}   % 90% width — wide figures
\includegraphics[width=\textwidth]{...}      % Full width — panoramic/wide data
```

**Best practice:** Use `width=0.8\textwidth` unless you have a reason not to.

### Figure Paths

All paths are **relative to `projects/{name}/manuscript/`**:

```markdown
% ✅ Correct — relative path from manuscript/
\includegraphics{../output/figures/my_figure.png}

% ❌ Wrong — absolute path
\includegraphics{/Users/me/projects/{name}/output/figures/my_figure.png}

% ❌ Wrong — relative but missing ../
\includegraphics{output/figures/my_figure.png}
```

### Supported Image Formats

| Format  | Best for                         | Notes                             |
| ------- | -------------------------------- | --------------------------------- |
| **PNG** | Plots, diagrams, screenshots     | Recommended for most figures      |
| **PDF** | Vector graphics, line drawings   | Scales without artifacts          |
| **JPG** | Photographs                      | Lossy — avoid for plots           |

### Referencing Figures

```markdown
Figure \ref{fig:convergence_plot} shows the convergence behavior.
The results (Figure \ref{fig:results}) demonstrate improvement.
As illustrated in Figure \ref{fig:setup}, the pipeline includes...
```

**Capitalization:** "Figure" when starting a sentence, "figure" mid-sentence.

---

## Captions

Captions are the single most important piece of text for each figure and table. A reader should understand the key message from the caption alone.

### Caption Rules

1. **Write complete sentences** — start with a capital letter, end with a period
2. **Describe what the figure shows**, not just what it is
3. **Include key information** — method name, dataset, metric, key finding
4. **Include inline math** when it adds precision

### Good vs. Bad Captions

```markdown
% ✅ GOOD — descriptive, complete sentence, includes key details
\caption{Algorithm convergence comparison showing performance improvement
over baseline methods on the CIFAR-10 dataset.}

% ✅ GOOD — includes mathematical precision
\caption{Scalability analysis demonstrating $O(n \log n)$ computational
complexity for the proposed method across problem sizes $n = 10^2$ to $10^6$.}

% ✅ GOOD — describes the insight, not just the data
\caption{Ablation study results showing that removing the attention mechanism
reduces accuracy by 12.3\%, confirming its importance for feature extraction.}
```

```markdown
% ❌ BAD — too brief, not a sentence
\caption{convergence plot}

% ❌ BAD — vague, tells you nothing
\caption{Figure showing results}

% ❌ BAD — incomplete sentence
\caption{Results.}

% ❌ BAD — just names the type of chart
\caption{Bar chart of performance}
```

### Caption Template

When in doubt, use this pattern:

```text
\caption{[What is shown] [on what data/conditions] [highlighting what finding/result].}
```

Examples:

```markdown
\caption{Training loss curves for three model variants on ImageNet,
showing that Model C converges 2.1× faster than the baseline.}

\caption{Distribution of prediction errors across 500 test samples,
demonstrating a mean absolute error of $0.032 \pm 0.008$.}
```

---

## Tables

### Complete Table Block

```markdown
\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|}
\hline
\textbf{Method} & \textbf{Accuracy (\%)} & \textbf{Time (s)} \\
\hline
Baseline         & 85.2                   & 10.2              \\
Our Method       & 92.7                   & 8.5               \\
Our Method + Aug & \textbf{94.1}          & 9.1               \\
\hline
\end{tabular}
\caption{Performance comparison showing accuracy and execution time
for different optimization methods on the benchmark dataset.}
\label{tab:performance_comparison}
\end{table}
```

### Column Alignment

| Specifier | Alignment | Typical use                         |
| --------- | --------- | ----------------------------------- |
| `l`       | Left      | Text, method names                  |
| `c`       | Center    | Numbers, short values               |
| `r`       | Right     | Numeric data for decimal alignment  |
| `\|`     | Vertical border | Between columns (use sparingly) |

### Highlighting Best Results

Bold the best value in each column:

```markdown
Baseline         & 85.2              & 10.2 \\
Our Method       & \textbf{92.7}     & \textbf{8.5} \\
```

### Table Label Conventions

Same rules as equation and figure labels:

```markdown
\label{tab:performance_comparison}    % ✅ Descriptive
\label{tab:dataset_summary}           % ✅ Descriptive
\label{tab:1}                         % ❌ Generic
```

### Referencing Tables

```markdown
Table \ref{tab:performance_comparison} summarizes the results.
The hyperparameters (Table \ref{tab:hyperparameters}) were tuned via grid search.
```

---

## Cross-Referencing Quick Reference

| Element      | Label format          | Reference command    | In-text example                            |
| ------------ | --------------------- | -------------------- | ------------------------------------------ |
| **Equation** | `\label{eq:name}`    | `\eqref{eq:name}`   | "as shown in \eqref{eq:loss}"             |
| **Figure**   | `\label{fig:name}`   | `\ref{fig:name}`    | "Figure \ref{fig:setup} shows"            |
| **Table**    | `\label{tab:name}`   | `\ref{tab:name}`    | "Table \ref{tab:results} lists"           |
| **Section**  | `{#sec:name}`         | `\ref{sec:name}`    | "Section \ref{sec:method} describes"      |
| **Citation** | key in `.bib`         | `\cite{key}`        | "prior work \cite{smith2023}"             |

**All labels must be:**

- Lowercase with underscores: `eq:convergence_rate`
- Descriptive: `fig:ablation_study` not `fig:1`
- Unique across the entire manuscript

---

## Common Mistakes

| ❌ Mistake                           | ✅ Correct                                                             | Why                                          |
| ------------------------------------ | ---------------------------------------------------------------------- | -------------------------------------------- |
| `$$ f(x) = x^2 $$`                  | `\begin{equation}\label{eq:name} ... \end{equation}`                 | `$$` produces unnumbered equations           |
| `\includegraphics{figures/fig.png}` | `\includegraphics{../output/figures/fig.png}`                         | Paths are relative to `manuscript/`          |
| `\caption{results}`                 | `\caption{Comparison of model accuracy across three benchmarks.}`     | Captions must be complete sentences          |
| `\label{eq:1}`                      | `\label{eq:convergence_rate}`                                         | Labels must be descriptive                   |
| `\cite{Kingma2014}`                 | `\cite{kingma2014}`                                                   | Citation keys are case-sensitive             |
| Missing `\label{}` on equation      | Always add `\label{eq:name}`                                          | Every referenced equation needs a label      |
| Missing `\centering` in figure      | Always include `\centering`                                           | Figures should be horizontally centered      |

---

## Related Documentation

- **[Manuscript Style Reference](../../.cursorrules/manuscript_style.md)** — Exhaustive formatting rules (1000+ lines)
- **[Markdown Template Guide](markdown-template-guide.md)** — Cross-referencing system and build process
- **[Figures and Analysis Guide](../guides/figures-and-analysis.md)** — Creating figure scripts with the thin orchestrator pattern
- **[Image Management](image-management.md)** — Programmatic `ImageManager` and `FigureManager` APIs
- **[Visualization Guide](visualization-guide.md)** — `VisualizationEngine` for publication-quality figures
- **[Manuscript Numbering](manuscript-numbering-system.md)** — Section numbering conventions (01-09, S01-S0N, 98-99)
