# Manuscript Style Guide

This guide documents all manuscript style features used in the project, with examples extracted from actual manuscript files. This complements the standards defined in [`.cursorrules/manuscript_style.md`](../../../.cursorrules/manuscript_style.md) by showing real-world implementation examples.

## Overview

This guide documents the style features actually used in the manuscript, including:
- Section numbering and structure
- Cross-referencing patterns
- Citation styles
- Equation formatting
- Figure and table integration
- Configuration and metadata
- Bibliography management

## Section Numbering System

### Main Sections (01-09)

Main sections use numbered prefixes (01-09) and descriptive names:

**Examples from manuscript:**
- `01_abstract.md` - Research overview and key contributions
- `02_introduction.md` - Project structure and motivation
- `03_methodology.md` - Mathematical framework and algorithms
- `04_experimental_results.md` - Performance evaluation and validation
- `05_discussion.md` - Theoretical implications and comparisons
- `06_conclusion.md` - Summary and future directions
- `08_acknowledgments.md` - Funding, collaborators, and acknowledgments
- `09_appendix.md` - Technical details, proofs, and derivations

### Supplemental Sections (S01-S0N)

Supplemental sections use "S" prefix with numbering:

**Examples from manuscript:**
- `S01_supplemental_methods.md` - Extended methodological details
- `S02_supplemental_results.md` - Additional experimental results
- `S03_supplemental_analysis.md` - Extended theoretical analysis and complexity
- `S04_supplemental_applications.md` - Additional application examples

### Reference Sections (98-99)

Reference sections use higher numbers:
- `98_symbols_glossary.md` - Auto-generated API reference from `src/`
- `99_references.md` - Bibliography and cited works (always last)

## Cross-Referencing Patterns

### Section References

**Pattern:** `\ref{sec:name}` with `{#sec:name}` labels

**Examples from manuscript:**
```markdown
# Introduction {#sec:introduction}

As discussed in Section \ref{sec:methodology}.
The experimental setup (Section \ref{sec:experimental_setup}) includes...
```

From `02_introduction.md`:
```markdown
1. **Abstract** (Section \ref{sec:abstract}): Research overview and key contributions
2. **Introduction** (Section \ref{sec:introduction}): Overview and project structure
3. **Methodology** (Section \ref{sec:methodology}): Mathematical framework and algorithms
```

### Equation References

**Pattern:** `\eqref{eq:name}` with `\label{eq:name}` labels

**Examples from manuscript:**
```markdown
\begin{equation}\label{eq:objective}
f(x) = \sum_{i=1}^{n} w_i \phi_i(x) + \lambda R(x)
\end{equation}

The objective function \eqref{eq:objective} defines...
```

From `03_methodology.md`:
```markdown
The core algorithm can be expressed as follows:

\begin{equation}\label{eq:objective_example2}
f(x) = \sum_{i=1}^{n} w_i \phi_i(x) + \lambda R(x)
\end{equation}
```

### Figure References

**Pattern:** `\ref{fig:name}` with `\label{fig:name}` labels

**Examples from manuscript:**
```markdown
\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/example_figure.png}
\caption{Example figure demonstrating data analysis with src/ functions.}
\label{fig:example_figure}
\end{figure}

As shown in Figure \ref{fig:example_figure}...
```

From `02_introduction.md`:
```markdown
\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/example_figure.png}
\caption{Example project figure showing a mathematical function}
\label{fig:example_figure}
\end{figure}

This demonstrates how figures are automatically integrated into the manuscript with proper cross-referencing capabilities.
```

### Table References

**Pattern:** `\ref{tab:name}` with `\label{tab:name}` labels

**Examples from manuscript:**
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
\caption{Performance comparison with state-of-the-art methods}
\label{tab:performance_comparison}
\end{table}

Table \ref{tab:performance_comparison} demonstrates...
```

From `04_experimental_results.md`:
```markdown
\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|c|}
\hline
\textbf{Method} & \textbf{Convergence Rate} & \textbf{Memory Usage} & \textbf{Success Rate (\%)} \\
\hline
Our Method & 0.85 & $O(n)$ & 94.3 \\
Gradient Descent & 0.9 & $O(n^2)$ & 85.0 \\
Adam & 0.9 & $O(n^2)$ & 85.0 \\
L-BFGS & 0.9 & $O(n^2)$ & 85.0 \\
\hline
\end{tabular}
\caption{Performance comparison with state-of-the-art methods}
\label{tab:performance_comparison}
\end{table}
```

### Multiple References

**Pattern:** Combine multiple references in single sentences

**Examples from manuscript:**
```markdown
The methodology (Section \ref{sec:methodology}) and results (Section \ref{sec:results}) demonstrate...

The equation \eqref{eq:objective_methodology} defines the objective function...
```

## Citation Styles

### Single Citations

**Pattern:** `\cite{key}` before punctuation

**Examples from manuscript:**
```markdown
According to recent research \cite{boyd2004}, the method...
The algorithm \cite{kingma2014} demonstrates...
Previous work \cite{nesterov2018} has shown this.
```

From `01_abstract.md`:
```markdown
This research presents a novel optimization framework... building on foundational work in convex optimization \cite{boyd2004, nesterov2018} and recent advances in adaptive optimization \cite{kingma2014, duchi2011}.
```

### Multiple Citations

**Pattern:** `\cite{key1,key2,key3}` for multiple sources

**Examples from manuscript:**
```markdown
Our work makes several significant contributions... combining regularization, adaptive step sizes, and momentum techniques... validated through extensive experimentation. Our experimental evaluation demonstrates... across multiple problem domains. The framework has broad applications across machine learning \cite{kingma2014}, signal processing \cite{beck2009}, computational biology, and climate modeling \cite{polak1997}.
```

From `03_methodology.md`:
```markdown
Our approach is based on a novel optimization framework that combines multiple mathematical techniques, extending classical convex optimization methods \cite{boyd2004, nesterov2018} with modern adaptive strategies \cite{kingma2014, duchi2011}.
```

### Citation Keys

**Pattern:** Case-sensitive keys matching `references.bib` entries

**Examples from `references.bib`:**
```bibtex
@article{boyd2004,
  title={Convex Optimization},
  author={Boyd, Stephen and Vandenberghe, Lieven},
  year={2004},
  publisher={Cambridge University Press}
}

@inproceedings{kingma2014,
  title={Adam: A Method for Stochastic Optimization},
  author={Kingma, Diederik P. and Ba, Jimmy},
  booktitle={Proceedings of the 3rd International Conference on Learning Representations},
  year={2015},
  url={[arXiv:1412.6980](https://arxiv.org/abs/1412.6980)}
}
```

## Equation Formatting

### Inline Equations

**Pattern:** `$expression$` for inline math

**Examples from manuscript:**
```markdown
The variable $x \in \mathbb{R}^d$ is the optimization parameter.
The function $f(x) = x^2 + 1$ is quadratic.
The algorithm converges with rate $\rho \in (0,1)$.
```

From `03_methodology.md`:
```markdown
where $x \in \mathbb{R}^d$ is the optimization variable, $w_i$ are learned weights, $\phi_i$ are basis functions, and $R(x)$ is a regularization term with strength $\lambda$.
```

### Display Equations

**Pattern:** `\begin{equation}...\end{equation}` with labels

**Examples from `03_methodology.md`:**
```markdown
The core algorithm can be expressed as follows:

\begin{equation}\label{eq:objective_example1}
f(x) = \sum_{i=1}^{n} w_i \phi_i(x) + \lambda R(x)
\end{equation}

where $x \in \mathbb{R}^d$ is the optimization variable, $w_i$ are learned weights, $\phi_i$ are basis functions, and $R(x)$ is a regularization term with strength $\lambda$.

The optimization problem we solve is:

\begin{equation}\label{eq:optimization_example1}
\min_{x \in \mathcal{X}} f(x) \quad \text{subject to} \quad g_i(x) \leq 0, \quad i = 1, \ldots, m
\end{equation}

where $\mathcal{X}$ is the feasible set and $g_i(x)$ are constraint functions.
```

### Multi-Line Equations

**Pattern:** `align` or `split` environments for complex equations

**Examples from manuscript:**
```markdown
\begin{align}
\label{eq:system}
x_{k+1} &= x_k - \alpha_k \nabla f(x_k) \\
y_{k+1} &= y_k + \beta_k (x_k - x_{k-1})
\end{align}
```

From `S01_supplemental_methods.md`:
```markdown
\begin{equation}\label{eq:iterations_bound}
\|x_k - x^*\| \leq C \rho^k \leq \epsilon \Rightarrow k \geq \frac{\log(C/\epsilon)}{\log(1/\rho)} = O(\kappa \log(1/\epsilon))
\end{equation}
```

## Figure Integration

### Figure Placement

**Pattern:** `[h]` placement specifier

**Examples from manuscript:**
```markdown
\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/experimental_setup.png}
\caption{Experimental pipeline showing the complete workflow}
\label{fig:experimental_setup}
\end{figure}
```

### Figure Sizing

**Pattern:** `width=0.8\textwidth` or `width=0.9\textwidth`

**Examples from manuscript:**
```markdown
\includegraphics[width=0.8\textwidth]{../output/figures/example_figure.png}
\includegraphics[width=0.9\textwidth]{../output/figures/convergence_plot.png}
```

### Figure Paths

**Pattern:** `../output/figures/filename.png` relative paths

**Examples from manuscript:**
```markdown
\includegraphics[width=0.8\textwidth]{../output/figures/example_figure.png}
\includegraphics[width=0.9\textwidth]{../output/figures/experimental_setup.png}
\includegraphics[width=0.9\textwidth]{../output/figures/convergence_plot.png}
```

### Figure Captions

**Pattern:** Descriptive sentences ending with periods

**Examples from manuscript:**
```markdown
\caption{Example project figure showing a mathematical function}
\caption{Experimental pipeline showing the complete workflow}
\caption{Algorithm convergence comparison showing performance improvement}
\caption{Detailed analysis of adaptive step size behavior}
```

### Figure Labels

**Pattern:** `fig:` prefix with descriptive names

**Examples from manuscript:**
```markdown
\label{fig:example_figure}
\label{fig:experimental_setup}
\label{fig:convergence_plot}
\label{fig:step_size_analysis}
```

## Table Formatting

### Table Structure

**Pattern:** `table` environment with `tabular`

**Examples from manuscript:**
```markdown
\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|c|}
\hline
\textbf{Method} & \textbf{Convergence Rate} & \textbf{Memory Usage} & \textbf{Success Rate (\%)} \\
\hline
Our Method & 0.85 & $O(n)$ & 94.3 \\
Gradient Descent & 0.9 & $O(n^2)$ & 85.0 \\
Adam & 0.9 & $O(n^2)$ & 85.0 \\
L-BFGS & 0.9 & $O(n^2)$ & 85.0 \\
\hline
\end{tabular}
\caption{Performance comparison with state-of-the-art methods}
\label{tab:performance_comparison}
\end{table}
```

### Table Borders

**Pattern:** `|` for vertical borders, `\hline` for horizontal lines

**Examples from manuscript:**
```markdown
\begin{tabular}{|l|c|c|c|}
\hline
\textbf{Method} & \textbf{Convergence Rate} & \textbf{Memory Usage} & \textbf{Success Rate (\%)} \\
\hline
Our Method & 0.85 & $O(n)$ & 94.3 \\
Gradient Descent & 0.9 & $O(n^2)$ & 85.0 \\
\hline
\end{tabular}
```

### Table Captions

**Pattern:** Descriptive captions ending with periods

**Examples from manuscript:**
```markdown
\caption{Performance comparison with state-of-the-art methods}
\caption{Dataset characteristics and problem sizes used in experiments}
```

### Table Labels

**Pattern:** `tab:` prefix with descriptive names

**Examples from manuscript:**
```markdown
\label{tab:performance_comparison}
\label{tab:dataset_summary}
```

## Section Headings

### Heading Hierarchy

**Pattern:** `#` for main sections, `##` for subsections, `###` for subsubsections

**Examples from manuscript:**
```markdown
# Methodology {#sec:methodology}

## Mathematical Framework

### Optimization Problem

## Algorithm Description

### Implementation Details
```

### Section Labels

**Pattern:** `{#sec:name}` at end of heading line

**Examples from manuscript:**
```markdown
# Methodology {#sec:methodology}
# Experimental Results {#sec:experimental_results}
# Supplemental Methods {#sec:supplemental_methods}
```

## Configuration and Metadata

### Config File Structure

**Pattern:** YAML format with hierarchical structure

**Examples from `config.yaml.example`:**
```yaml
paper:
  title: "Novel Optimization Framework for Machine Learning"
  subtitle: "A Comprehensive Approach to Large-Scale Problems"
  version: "1.0"

authors:
  - name: "Dr. Jane Smith"
    orcid: "0000-0000-0000-1234"
    email: "jane.smith@university.edu"
    affiliation: "Department of Computer Science, University of Example"
    corresponding: true

publication:
  doi: ""
  journal: "Journal of Example Research"
  volume: "42"
  pages: ""
  year: ""

keywords:
  - "optimization"
  - "machine learning"
  - "convex optimization"
```

### Multiple Authors

**Pattern:** Array of author objects with affiliations

**Examples from config:**
```yaml
authors:
  - name: "Dr. Jane Smith"
    orcid: "0000-0000-0000-1234"
    email: "jane.smith@university.edu"
    affiliation: "Department of Computer Science, University of Example"
    corresponding: true
  - name: "Dr. John Doe"
    orcid: "0000-0000-0000-5678"
    email: "john.doe@university.edu"
    affiliation: "Department of Mathematics, Another University"
    corresponding: false
```

### LLM Settings

**Pattern:** Configuration for LLM review features

**Examples from config:**
```yaml
llm:
  translations:
    enabled: true
    languages:
      - zh  # Chinese (Simplified)
      - hi  # Hindi
      - ru  # Russian
```

## Bibliography Management

### BibTeX Entries

**Pattern:** Various entry types with complete metadata

**Examples from `references.bib`:**
```bibtex
@article{boyd2004,
  title={Convex Optimization},
  author={Boyd, Stephen and Vandenberghe, Lieven},
  year={2004},
  publisher={Cambridge University Press},
  address={Cambridge, UK},
  isbn={978-0-521-83378-3}
}

@inproceedings{kingma2014,
  title={Adam: A Method for Stochastic Optimization},
  author={Kingma, Diederik P. and Ba, Jimmy},
  booktitle={Proceedings of the 3rd International Conference on Learning Representations},
  year={2015},
  url={[arXiv:1412.6980](https://arxiv.org/abs/1412.6980)}
}

@article{nesterov2018,
  title={Lectures on Convex Optimization},
  author={Nesterov, Yurii},
  journal={Springer Optimization and Its Applications},
  volume={137},
  year={2018},
  publisher={Springer},
  doi={10.1007/978-3-319-91578-4}
}
```

### Bibliography Processing

**Pattern:** `\nocite{*}` and `\bibliography{references}` in `99_references.md`

**Examples from manuscript:**
```markdown
# References {#sec:references}

\nocite{*}
\bibliography{references}
```

## LaTeX Preamble

### Package Usage

**Pattern:** LaTeX packages wrapped in markdown code blocks

**Examples from `preamble.md`:**
```latex
% Mathematical typesetting (required for equations and symbols)
\usepackage{amsmath,amssymb}          % Mathematical symbols and environments
\usepackage{amsfonts}                 % Additional math fonts
\usepackage{amsthm}                   % Theorem environments

% Graphics and page layout (required for figures and formatting)
\usepackage{graphicx}                 % Include graphics (REQUIRED for figures)
\usepackage[margin=1in]{geometry}     % Page margins
\usepackage{float}                    % Better float placement

% Tables (required for table formatting)
\usepackage{booktabs}                 % Professional tables
\usepackage{longtable}                % Long tables spanning pages
\usepackage{array}                    % Advanced table formatting

% PDF features (required for cross-references and metadata)
\usepackage{url}                      % URL formatting
\usepackage{hyperref}                 % Hyperlinks and cross-references
\usepackage{natbib}                   % Bibliography support (REQUIRED)
```

## Glossary Generation

### Auto-Generation Markers

**Pattern:** HTML comments marking auto-generated content

**Examples from `98_symbols_glossary.md`:**
```markdown
# API Symbols Glossary {#sec:glossary}

This glossary is auto-generated from the public API in `src/`.

<!-- BEGIN: AUTO-API-GLOSSARY -->
| Module | Name | Kind | Summary |
|---|---|---|---|
| `data_generator` | `generate_classification_dataset` | function | Generate classification dataset. |
| `data_generator` | `generate_correlated_data` | function | Generate correlated multivariate data. |
<!-- END: AUTO-API-GLOSSARY -->
```

## Best Practices from Examples

### Consistent Patterns

**Cross-referencing:**
- Always place references before punctuation
- Use descriptive labels (`sec:`, `eq:`, `fig:`, `tab:` prefixes)
- Reference sections/equations/figures/tables near their first mention

**Equation formatting:**
- Use `equation` environment for all display math
- Always include `\label{}` with descriptive names
- Use `\eqref{}` for equation references

**Figure integration:**
- Use `../output/figures/` relative paths
- Consistent `width=0.8\textwidth` or `width=0.9\textwidth`
- Descriptive captions ending with periods
- Labels matching filename when possible

### Common Mistakes to Avoid

**Based on validation results:**
- Never use `$$` for display math (use `equation` environment)
- Never use `\[...\]` for display math (use `equation` environment)
- Always include labels for equations, figures, tables
- Always place citations before punctuation
- Use consistent relative paths for figures

### Supplemental Material

**Cross-referencing to supplemental:**
- Reference supplemental sections from main text: `Section \ref{sec:supplemental_methods}`
- Supplemental equations/figures/tables use same numbering as main sections
- Clear distinction between main and supplemental content

## See Also

**Standards:**
- [`.cursorrules/manuscript_style.md`](../../../.cursorrules/manuscript_style.md) - Complete manuscript formatting standards
- [`.cursorrules/documentation_standards.md`](../../../.cursorrules/documentation_standards.md) - Documentation writing guidelines

**Manuscript Structure:**
- [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) - Complete manuscript documentation
- [`../manuscript/README.md`](../manuscript/README.md) - Quick manuscript reference
- [`../../docs/MARKDOWN_TEMPLATE_GUIDE.md`](../../docs/MARKDOWN_TEMPLATE_GUIDE.md) - Markdown and cross-referencing guide

**Validation:**
- [`validation_guide.md`](validation_guide.md) - Quality assurance procedures
- [`../../docs/operational/TROUBLESHOOTING_GUIDE.md`](../../docs/operational/TROUBLESHOOTING_GUIDE.md) - Error handling guide