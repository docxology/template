# Manuscript Style and Formatting Standards

## Overview

This guide provides comprehensive formatting standards for writing research manuscripts in the `project/manuscript/` directory. All manuscript content must follow these standards to ensure consistency, proper rendering, and correct cross-referencing.

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

### Lists in LaTeX vs Markdown

- **Markdown lists** are converted to LaTeX `itemize` or `enumerate` environments during PDF rendering
- **LaTeX lists** can be used directly in markdown for more control:
  ```latex
  \begin{itemize}
  \item First item
  \item Second item
  \end{itemize}
  ```

**Best Practice:** Use Markdown lists for simplicity; use LaTeX lists only when specific formatting is required.

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

Use the `equation` environment for standalone equations that should be centered and numbered.

**Syntax:**
```markdown
\begin{equation}
\label{eq:objective}
f(x) = \sum_{i=1}^{n} w_i \phi_i(x) + \lambda R(x)
\end{equation}
```

**When to Use:**
- Important equations that are referenced
- Complex mathematical expressions
- Equations that need numbering
- Key results or definitions

**Example:**
```markdown
The optimization problem we solve is:

\begin{equation}
\label{eq:optimization}
\min_{x \in \mathcal{X}} f(x) \quad \text{subject to} \quad g_i(x) \leq 0, \quad i = 1, \ldots, m
\end{equation}

where $\mathcal{X}$ is the feasible set.
```

### Equation Labels

All important equations must have descriptive labels.

**Naming Convention:**
- Prefix: `eq:`
- Format: `eq:descriptive_name`
- Use lowercase with underscores
- Be descriptive, not generic

**Good Examples:**
```markdown
\label{eq:objective}
\label{eq:convergence_rate}
\label{eq:update_rule}
\label{eq:adaptive_step_size}
```

**Bad Examples:**
```markdown
\label{eq:1}           # Too generic
\label{eq:eq1}         # Redundant prefix
\label{eq:MyEquation}  # Inconsistent case
```

### Equation References

Reference equations using `\eqref{}` command.

**Syntax:**
```markdown
As shown in \eqref{eq:objective}, the objective function...
The convergence rate \eqref{eq:convergence} demonstrates...
```

**Placement:**
- Before punctuation: "Equation \eqref{eq:name} shows..."
- In parentheses: "The result (see \eqref{eq:name}) indicates..."
- As part of sentence: "Using \eqref{eq:name}, we derive..."

### Multi-Line Equations

For equations spanning multiple lines, use `align` or `split` environments.

**Align Environment (multiple equations):**
```markdown
\begin{align}
\label{eq:system}
x_{k+1} &= x_k - \alpha_k \nabla f(x_k) \\
y_{k+1} &= y_k + \beta_k (x_k - x_{k-1})
\end{align}
```

**Split Environment (single equation, multiple lines):**
```markdown
\begin{equation}
\begin{split}
\label{eq:complex}
f(x) &= \sum_{i=1}^{n} w_i \phi_i(x) \\
     &\quad + \lambda \sum_{j=1}^{m} |x_j| \\
     &\quad + \gamma \|x\|^2
\end{split}
\end{equation}
```

### Numbering Conventions

- Equations are automatically numbered by LaTeX
- Numbering is sequential throughout the document
- Supplemental sections use separate numbering (S1, S2, etc.)

### DO NOT Use

**Never use these for display math:**
```markdown
$$ f(x) = x^2 $$           # ❌ BAD: Double dollar signs
\[ f(x) = x^2 \]          # ❌ BAD: Backslash square brackets
```

**Always use:**
```markdown
\begin{equation}
\label{eq:name}
f(x) = x^2
\end{equation}
```

## Figures

### Figure Placement

Use placement specifiers to control figure location.

**Options:**
- `[h]` - Here (current position, if possible)
- `[t]` - Top of page
- `[b]` - Bottom of page
- `[H]` - Here (force current position, requires `float` package)
- `[!htbp]` - Try here, then top, then bottom, then separate page

**Syntax:**
```markdown
\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/figure_name.png}
\caption{Descriptive caption explaining the figure.}
\label{fig:figure_name}
\end{figure}
```

**Best Practice:** Use `[h]` for most figures; use `[t]` or `[b]` if figure is large.

### Figure Sizing

Control figure size using `width` or `height` parameters.

**Common Sizes:**
```markdown
width=0.5\textwidth   # Half page width
width=0.8\textwidth   # 80% page width (most common)
width=0.9\textwidth   # 90% page width
width=\textwidth      # Full page width
```

**Syntax:**
```markdown
\includegraphics[width=0.8\textwidth]{../output/figures/figure.png}
```

**Best Practice:** Use `0.8\textwidth` for most figures to leave margins.

### Figure Paths

All figures must use relative paths from the manuscript directory.

**Path Format:**
```markdown
../output/figures/figure_name.png
```

**Requirements:**
- Paths are relative to `project/manuscript/`
- Figures are stored in `project/output/figures/`
- Use forward slashes (`/`) even on Windows
- Include file extension (`.png`, `.pdf`, `.jpg`)

**Example:**
```markdown
\includegraphics[width=0.9\textwidth]{../output/figures/convergence_plot.png}
```

### Figure Captions

Captions must be descriptive and complete sentences.

**Format:**
- Start with capital letter
- End with period
- Describe what the figure shows
- Include key information (method, dataset, result)

**Good Examples:**
```markdown
\caption{Algorithm convergence comparison showing performance improvement over baseline methods.}
\caption{Experimental setup diagram illustrating the complete data processing pipeline.}
\caption{Scalability analysis demonstrating $O(n \log n)$ computational complexity.}
```

**Bad Examples:**
```markdown
\caption{convergence plot}                    # Too brief, not a sentence
\caption{Figure showing results}              # Vague, doesn't describe content
\caption{Results.}                            # Incomplete sentence
```

### Figure Labels

All figures must have descriptive labels.

**Naming Convention:**
- Prefix: `fig:`
- Format: `fig:descriptive_name`
- Use lowercase with underscores
- Match filename when possible

**Good Examples:**
```markdown
\label{fig:convergence_plot}
\label{fig:experimental_setup}
\label{fig:scalability_analysis}
\label{fig:ablation_study}
```

**Bad Examples:**
```markdown
\label{fig:1}              # Too generic
\label{fig:figure1}        # Redundant prefix
\label{fig:MyFigure}       # Inconsistent case
```

### Figure References

Reference figures using `\ref{}` command.

**Syntax:**
```markdown
As shown in Figure \ref{fig:convergence_plot}, the algorithm...
The experimental setup (Figure \ref{fig:experimental_setup}) includes...
```

**Placement:**
- Capitalize "Figure" when starting a sentence
- Use lowercase "figure" in the middle of a sentence
- Place reference before the figure when possible

**Examples:**
```markdown
Figure \ref{fig:convergence_plot} shows the convergence behavior.
The results, shown in figure \ref{fig:results}, demonstrate...
As illustrated in \ref{fig:setup}, the system includes...
```

### Figure Formatting

**Centering:**
```markdown
\begin{figure}[h]
\centering
% ... includegraphics ...
\end{figure}
```

**Supported Formats:**
- PNG (recommended for plots)
- PDF (recommended for vector graphics)
- JPG/JPEG (for photographs)

**Best Practice:** Use PNG for plots and diagrams; use PDF for vector graphics.

## Tables

### Table Environment

Use the `table` environment for all tables.

**Basic Syntax:**
```markdown
\begin{table}[h]
\centering
\begin{tabular}{|l|c|r|}
\hline
\textbf{Column 1} & \textbf{Column 2} & \textbf{Column 3} \\
\hline
Row 1, Col 1 & Row 1, Col 2 & Row 1, Col 3 \\
Row 2, Col 1 & Row 2, Col 2 & Row 2, Col 3 \\
\hline
\end{tabular}
\caption{Descriptive caption explaining the table.}
\label{tab:table_name}
\end{table}
```

### Tabular Formatting

**Column Alignment:**
- `l` - Left-aligned
- `c` - Center-aligned
- `r` - Right-aligned
- `|` - Vertical border

**Examples:**
```markdown
\begin{tabular}{lcr}           % Left, center, right (no borders)
\begin{tabular}{|l|c|r|}        % With vertical borders
\begin{tabular}{ll}             % Two left-aligned columns
\begin{tabular}{|c|c|c|c|}      % Four centered columns with borders
```

### Table Borders

**Horizontal Borders:**
- `\hline` - Full-width horizontal line
- Place before first row and after last row
- Use between header and data rows

**Vertical Borders:**
- `|` in column specification
- Use sparingly for clarity

**Example:**
```markdown
\begin{tabular}{|l|c|c|}
\hline
\textbf{Method} & \textbf{Accuracy} & \textbf{Time (s)} \\
\hline
Baseline & 0.85 & 10.2 \\
Our Method & 0.92 & 8.5 \\
\hline
\end{tabular}
```

### Table Captions

Follow the same caption guidelines as figures.

**Format:**
- Descriptive and complete sentences
- Start with capital letter
- End with period
- Place above table (before `\label`)

**Example:**
```markdown
\caption{Performance comparison showing accuracy and execution time for different methods.}
```

### Table Labels

All tables must have descriptive labels.

**Naming Convention:**
- Prefix: `tab:`
- Format: `tab:descriptive_name`
- Use lowercase with underscores

**Good Examples:**
```markdown
\label{tab:performance_comparison}
\label{tab:dataset_summary}
\label{tab:hyperparameter_settings}
```

### Table References

Reference tables using `\ref{}` command.

**Syntax:**
```markdown
Table \ref{tab:performance_comparison} shows...
The results (see Table \ref{tab:results}) indicate...
```

**Placement:**
- Capitalize "Table" when starting a sentence
- Use lowercase "table" in the middle of a sentence

### Markdown Tables vs LaTeX Tables

**Markdown Tables:**
- Simple tables with basic formatting
- Converted to LaTeX during rendering
- Limited formatting options

**LaTeX Tables:**
- Full control over formatting
- Support for complex layouts
- Required for multirow/multicolumn

**Best Practice:** Use LaTeX tables for publication-quality formatting; use Markdown tables only for simple data.

### Complex Tables

For tables with merged cells, use `multirow` and `multicolumn` packages.

**Example:**
```markdown
\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|}
\hline
\multirow{2}{*}{\textbf{Method}} & \multicolumn{2}{c|}{\textbf{Performance}} \\
\cline{2-3}
& Accuracy & Time (s) \\
\hline
Baseline & 0.85 & 10.2 \\
Our Method & 0.92 & 8.5 \\
\hline
\end{tabular}
\caption{Complex table with merged cells.}
\label{tab:complex}
\end{table}
```

## Citations

### Citation Format

Use `\cite{}` command for citations.

**Basic Syntax:**
```markdown
According to recent research \cite{author2023}, this method...
The algorithm \cite{kingma2014} demonstrates...
```

### Multiple Citations

Cite multiple sources using comma-separated keys.

**Syntax:**
```markdown
\cite{key1,key2,key3}
```

**Example:**
```markdown
Previous work \cite{boyd2004, nesterov2018, kingma2014} has shown...
```

### Citation Placement

Place citations before punctuation marks.

**Correct:**
```markdown
The method works well \cite{author2023}.
Previous research \cite{key1,key2} has demonstrated this.
```

**Incorrect:**
```markdown
The method works well.\cite{author2023}  # ❌ After punctuation
```

### Citation Keys

Citation keys are case-sensitive and must match entries in `references.bib`.

**Requirements:**
- Keys are defined in `project/manuscript/references.bib`
- Use exact key spelling (case-sensitive)
- Keys typically follow pattern: `authorYYYY` or `authorYYYYkeyword`

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
The Adam optimizer \cite{kingma2014} provides...
```

### Bibliography Style

The system uses `plainnat` style, which produces numbered citations `[1]`, `[2]`, etc.

**Output Format:**
- Citations appear as `[1]`, `[2]`, `[3]` in text
- Bibliography is numbered and sorted
- Multiple citations: `[1,2,3]` or `[1-3]`

## Section Headings

### Heading Hierarchy

Use consistent heading levels to maintain document structure.

**Levels:**
- `#` - Main section (e.g., "Introduction", "Methodology")
- `##` - Subsection (e.g., "Experimental Setup", "Results")
- `###` - Subsubsection (e.g., "Convergence Analysis", "Ablation Studies")
- `####` - Paragraph-level heading (use sparingly)

**Example:**
```markdown
# Methodology {#sec:methodology}

## Mathematical Framework

### Optimization Problem

#### Convex Case
```

### Section Labels

All main sections and important subsections should have labels.

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

Reference sections using `\ref{}` command.

**Syntax:**
```markdown
As described in Section \ref{sec:methodology}...
The results (see \ref{sec:results}) show...
```

**Placement:**
- Capitalize "Section" when starting a sentence
- Use lowercase "section" in the middle of a sentence

### Numbering

Section numbering is automatic in LaTeX.

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

**Markdown:**
```markdown
The *optimization variable* $x$ represents...
```

**LaTeX:**
```markdown
The \textit{optimization variable} $x$ represents...
```

### Bold

Use for strong emphasis or key terms.

**Markdown:**
```markdown
The **key contribution** of this work is...
```

**LaTeX:**
```markdown
The \textbf{key contribution} of this work is...
```

### Code

Use for code, function names, or technical terms.

**Markdown:**
```markdown
The function `calculate_average()` computes...
```

**LaTeX:**
```markdown
The function \texttt{calculate\_average()} computes...
```

### Inline Code in Equations

Code can appear in equations when appropriate.

**Example:**
```markdown
The function $f(\texttt{x})$ where $\texttt{x}$ is a vector...
```

### Special Characters

Escape special LaTeX characters when needed.

**Common Escaping:**
- `%` → `\%`
- `&` → `\&`
- `$` → `\$`
- `#` → `\#`
- `_` → `\_` (in text, not in math mode)
- `{` → `\{`
- `}` → `\}`

## Cross-Referencing Patterns

### Section → Section

Reference other sections using `\ref{sec:name}`.

**Examples:**
```markdown
As discussed in Section \ref{sec:methodology}...
The experimental setup (Section \ref{sec:experimental_setup}) includes...
See \ref{sec:results} for detailed analysis.
```

### Section → Equation

Reference equations using `\eqref{eq:name}`.

**Examples:**
```markdown
The objective function \eqref{eq:objective} defines...
Using \eqref{eq:convergence}, we can show...
As shown in equation \eqref{eq:update}, the algorithm...
```

### Section → Figure

Reference figures using `\ref{fig:name}`.

**Examples:**
```markdown
Figure \ref{fig:convergence_plot} shows...
The results (see Figure \ref{fig:results}) demonstrate...
As illustrated in \ref{fig:setup}, the system...
```

### Section → Table

Reference tables using `\ref{tab:name}`.

**Examples:**
```markdown
Table \ref{tab:performance_comparison} summarizes...
The data (Table \ref{tab:dataset}) shows...
See \ref{tab:results} for complete statistics.
```

### Multiple References

Combine multiple references in a single sentence.

**Examples:**
```markdown
The methodology (Section \ref{sec:methodology}) and results
(Section \ref{sec:results}) demonstrate...

Equations \eqref{eq:objective} and \eqref{eq:optimization} define...

Figures \ref{fig:convergence} and \ref{fig:scalability} show...
```

### Reference Placement in Sentences

Place references naturally within sentences.

**Good Examples:**
```markdown
The algorithm described in Section \ref{sec:methodology} achieves
the convergence rate shown in \eqref{eq:convergence}.

As shown in Figure \ref{fig:results}, the method outperforms
baselines (see Table \ref{tab:comparison}).
```

**Bad Examples:**
```markdown
The algorithm. See Section \ref{sec:methodology}.  # ❌ Fragmented
Figure \ref{fig:results}. Shows results.         # ❌ Fragmented
```

## Best Practices

### Label Naming Conventions

**Guidelines:**
- Use descriptive names, not numbers
- Be consistent across document
- Use lowercase with underscores
- Match content purpose (eq:, fig:, tab:, sec:)

**Good:**
```markdown
\label{eq:convergence_rate}
\label{fig:experimental_setup}
\label{tab:performance_comparison}
\label{sec:methodology}
```

**Bad:**
```markdown
\label{eq:1}
\label{fig:figure1}
\label{tab:table}
\label{sec:sec1}
```

### Reference Validation

**Before Building:**
- Verify all `\ref{}` and `\eqref{}` targets exist
- Check label spelling matches exactly
- Ensure all figures/tables/equations have labels
- Run validation: `python3 -m infrastructure.validation.cli markdown manuscript/`

### Figure/Table Placement Guidelines

**Placement Strategy:**
- Place figures/tables near first reference
- Use `[h]` for most cases
- Use `[t]` or `[b]` for large figures
- Avoid `[H]` unless necessary (can cause layout issues)

### Equation Numbering Strategy

**Numbering Guidelines:**
- Number all equations that are referenced
- Number key results and definitions
- Don't number trivial or obvious equations
- Use consistent labeling across sections

### Citation Management

**Best Practices:**
- Add all citations to `references.bib` first
- Use consistent key naming (authorYYYY)
- Verify keys match exactly (case-sensitive)
- Keep bibliography file organized

## Common Mistakes to Avoid

### Using `$$` for Display Math

**Never:**
```markdown
$$ f(x) = x^2 $$
```

**Always:**
```markdown
\begin{equation}
\label{eq:name}
f(x) = x^2
\end{equation}
```

### Missing Labels

**Never:**
```markdown
\begin{equation}
f(x) = x^2
\end{equation}
```

**Always:**
```markdown
\begin{equation}
\label{eq:name}
f(x) = x^2
\end{equation}
```

### Incorrect Path References

**Never:**
```markdown
\includegraphics{figures/figure.png}           # ❌ Wrong path
\includegraphics{output/figures/figure.png}   # ❌ Wrong path
```

**Always:**
```markdown
\includegraphics{../output/figures/figure.png}  # ✅ Correct relative path
```

### Case-Sensitive Citation Keys

**Never:**
```markdown
\cite{Kingma2014}  # ❌ Wrong case
\cite{kingma2014}  # ✅ Correct case
```

**Always:** Match exact case from `references.bib`.

### Inconsistent Label Naming

**Never:**
```markdown
\label{eq:Objective}      # ❌ Inconsistent case
\label{eq:objective_func} # ❌ Inconsistent style
\label{eq:obj}           # ❌ Too abbreviated
```

**Always:**
```markdown
\label{eq:objective}      # ✅ Consistent, descriptive
```

## Examples

### Complete Figure Example

```markdown
\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/convergence_plot.png}
\caption{Algorithm convergence comparison showing performance improvement
over baseline methods. The plot demonstrates exponential convergence
with rate $\rho \approx 0.85$.}
\label{fig:convergence_plot}
\end{figure}

As shown in Figure \ref{fig:convergence_plot}, our method achieves
faster convergence than existing approaches.
```

### Complete Table Example

```markdown
\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|}
\hline
\textbf{Method} & \textbf{Accuracy} & \textbf{Time (s)} \\
\hline
Baseline & 0.85 & 10.2 \\
Our Method & 0.92 & 8.5 \\
\hline
\end{tabular}
\caption{Performance comparison showing accuracy and execution time
for different optimization methods.}
\label{tab:performance_comparison}
\end{table}

Table \ref{tab:performance_comparison} demonstrates that our method
achieves higher accuracy with reduced computation time.
```

### Complete Equation Example

```markdown
The optimization problem we solve is:

\begin{equation}
\label{eq:optimization}
\min_{x \in \mathcal{X}} f(x) \quad \text{subject to} \quad g_i(x) \leq 0, \quad i = 1, \ldots, m
\end{equation}

where $\mathcal{X}$ is the feasible set and $g_i(x)$ are constraint
functions. The solution to \eqref{eq:optimization} is obtained using
the iterative algorithm described in Section \ref{sec:algorithm}.
```

## See Also

- [project/manuscript/AGENTS.md](../projects/project/manuscript/AGENTS.md) - Complete manuscript documentation
- [project/manuscript/README.md](../projects/project/manuscript/README.md) - Quick reference for manuscript
- [docs/MARKDOWN_TEMPLATE_GUIDE.md](../docs/usage/MARKDOWN_TEMPLATE_GUIDE.md) - Markdown and cross-referencing guide
- [docs/MANUSCRIPT_NUMBERING_SYSTEM.md](../docs/usage/MANUSCRIPT_NUMBERING_SYSTEM.md) - Section numbering system
- [code_style.md](code_style.md) - Code formatting standards
- [documentation_standards.md](documentation_standards.md) - Documentation writing guide

