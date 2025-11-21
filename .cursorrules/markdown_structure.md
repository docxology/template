# Markdown Structure for Manuscripts

## Manuscript Organization

Markdown files are numbered for ordering and organized by section type:

### Main Sections (01-09)
- `01_abstract.md` - Research summary
- `02_introduction.md` - Overview
- `03_methodology.md` - Methods
- `04_experimental_results.md` - Results
- `05_discussion.md` - Analysis
- `06_conclusion.md` - Summary
- `08_acknowledgments.md` - Credits
- `09_appendix.md` - Extra material

### Supplemental (S01-S99)
- `S01_supplemental_methods.md`
- `S02_supplemental_results.md`
- `S03_supplemental_analysis.md`
- `S04_supplemental_applications.md`

### References and Index (98-99)
- `98_symbols_glossary.md` - Auto-generated API reference
- `99_references.md` - Bibliography

## Cross-Reference Format

### Sections
```latex
See Section \ref{sec:methodology} for details.
```

### Equations
```latex
From Equation \eqref{eq:convergence}, we obtain...

\begin{equation}
x_{n+1} = x_n - \alpha \nabla f(x_n)
\label{eq:convergence}
\end{equation}
```

### Figures
```latex
As shown in Figure \ref{fig:convergence_plot}:

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/convergence_plot.png}
\caption{Convergence of the optimization algorithm}
\label{fig:convergence_plot}
\end{figure}
```

### Tables
```latex
\ref{tab:results} presents the results:

| Metric | Value |
|--------|-------|
| Accuracy | 0.95 |
\label{tab:results}
```

### Citations
```latex
Recent work \cite{Smith2023} shows...
Multiple sources \cite{Smith2023, Jones2022} indicate...
```

## Equation Labeling

### Format
```latex
\label{eq:descriptive_name}
```

### Examples
```latex
\label{eq:gradient_descent}
\label{eq:convergence_rate}
\label{eq:loss_function}
```

### Rules
- Use snake_case for label names
- Use descriptive names (not `eq1`, `eq2`)
- Must be unique across manuscript
- Referenced with `\eqref{eq:name}`

## Figure Integration

### Required Elements
1. Caption
2. Label
3. Width specification
4. File path (relative to manuscript/)
5. Referenced in text

### Example
```markdown
## Results

Figure \ref{fig:convergence_plot} shows the convergence behavior.

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/convergence_plot.png}
\caption{Convergence of the optimization algorithm over iterations}
\label{fig:convergence_plot}
\end{figure}

The figure demonstrates that the algorithm achieves convergence in approximately 50 iterations.
```

## Citation Management

### Bibliography File
```bibtex
# manuscript/references.bib

@article{Smith2023,
  author = {Smith, John and Doe, Jane},
  title = {Novel Optimization Approaches},
  journal = {Journal of Algorithms},
  year = {2023},
  volume = {15},
  pages = {123--145}
}

@book{Johnson2022,
  author = {Johnson, Michael},
  title = {Advanced Mathematics},
  publisher = {Academic Press},
  year = {2022}
}
```

### In Manuscript
```markdown
Recent developments \cite{Smith2023} and comprehensive reviews \cite{Johnson2022} indicate...

\nocite{*}
\bibliography{references}
```

## Markdown Features

### Code Blocks
```python
# Code with language specification
def analyze_data(data):
    return np.mean(data)
```

### Lists
```markdown
1. First step
2. Second step
3. Third step

- Bullet point
- Another point
  - Nested point
  - More nesting
```

### Tables
```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Data 1   | Data 2   | Data 3   |
```

### Emphasis
```markdown
*Italic text* or _italic_
**Bold text** or __bold__
***Bold italic***
```

### Headers
```markdown
# Level 1 (Section)
## Level 2 (Subsection)
### Level 3 (Subsubsection)
#### Level 4 (Paragraph)
```

## Preamble Configuration

### LaTeX Settings
Defined in `manuscript/preamble.md`:

```latex
\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{hyperref}
\usepackage{amsmath}
\usepackage{graphicx}

\geometry{margin=1.5cm}
\setmainfont{Times New Roman}
\hypersetup{colorlinks=true, linkcolor=blue}
```

## Validation Checks

### Automatic Validation
During build, checks ensure:
- All figure files exist
- All labels are unique
- All cross-references valid
- All equations have labels
- No bare URLs
- No undefined citations

### Manual Check
```bash
python3 repo_utilities/validate_markdown.py manuscript/
```

## Best Practices

### Organization
- Each markdown file covers one topic
- Sections within files use consistent heading levels
- Logical flow through sections
- Cross-references between sections

### Content
- Clear writing for technical audience
- Explain methodology thoroughly
- Show results with figures
- Discuss implications
- Provide comprehensive references

### Formatting
- Use LaTeX for math (not plain text)
- Inline math with `$...$`
- Display math with `\begin{equation}...\end{equation}`
- Always include figure captions
- Always label figures and equations

## Examples

### Well-Structured Introduction
```markdown
# Introduction

## Overview
This work addresses...

## Background
Previous approaches...

## Motivation
Our contribution...

## Contributions
We present...
```

### Results with Figures
```markdown
## Experimental Results

### Convergence Analysis
Figure \ref{fig:convergence} demonstrates...

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/convergence_plot.png}
\caption{Convergence behavior for different learning rates}
\label{fig:convergence}
\end{figure}

The convergence rate improves with...
```

## Comprehensive Documentation

For complete manuscript and markdown guidance, see:

- [`docs/MARKDOWN_TEMPLATE_GUIDE.md`](../docs/MARKDOWN_TEMPLATE_GUIDE.md) - Comprehensive markdown writing guide
- [`docs/MANUSCRIPT_NUMBERING_SYSTEM.md`](../docs/MANUSCRIPT_NUMBERING_SYSTEM.md) - Section numbering and organization
- [`docs/IMAGE_MANAGEMENT.md`](../docs/IMAGE_MANAGEMENT.md) - Image insertion and cross-referencing
- [`docs/PDF_VALIDATION.md`](../docs/PDF_VALIDATION.md) - PDF output validation

## See Also

- [core_architecture.md](core_architecture.md) - System design
- [../manuscript/](../manuscript/) - Manuscript sources
- [../repo_utilities/validate_markdown.py](../repo_utilities/validate_markdown.py) - Validation tool

