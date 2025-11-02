# manuscript/ - Research Manuscript

Research manuscript sections in markdown format, converted to PDFs.

## Quick Start

### Edit Manuscript
```bash
vim manuscript/02_introduction.md
```

### Build PDFs
```bash
# Clean and build everything
./repo_utilities/clean_output.sh
./repo_utilities/render_pdf.sh

# View output
open output/pdf/project_combined.pdf
```

## Structure

### Manuscript Sections (Generate PDFs)
- `01_abstract.md` - Research overview
- `02_introduction.md` - Project structure
- `03_methodology.md` - Mathematical framework
- `04_experimental_results.md` - Performance evaluation
- `05_discussion.md` - Theoretical implications
- `06_conclusion.md` - Summary and future work
- `07_references.md` - Bibliography
- `10_symbols_glossary.md` - Auto-generated API reference

### Supporting Files
- `preamble.md` - LaTeX configuration (no PDF)
- `references.bib` - BibTeX bibliography

## Cross-Referencing

### Sections
```markdown
## Introduction {#sec:intro}
See \ref{sec:intro} for details.
```

### Equations
```markdown
\begin{equation}
\label{eq:myeq}
f(x) = x^2
\end{equation}
Using \eqref{eq:myeq}...
```

### Figures
```markdown
\begin{figure}[h]
\includegraphics[width=0.8\textwidth]{../output/figures/example.png}
\caption{Example figure.}
\label{fig:example}
\end{figure}
See \ref{fig:example}...
```

## Configuration

```bash
export AUTHOR_NAME="Dr. Jane Smith"
export PROJECT_TITLE="My Research"
export AUTHOR_EMAIL="jane@example.edu"
./repo_utilities/render_pdf.sh
```

## Validation

```bash
# Check markdown
python3 repo_utilities/validate_markdown.py

# Check PDF
python3 repo_utilities/validate_pdf_output.py
```

## See Also

- [`AGENTS.md`](AGENTS.md) - Detailed documentation
- [`preamble.md`](preamble.md) - LaTeX configuration
- [`../docs/MARKDOWN_TEMPLATE_GUIDE.md`](../docs/MARKDOWN_TEMPLATE_GUIDE.md) - Full guide

