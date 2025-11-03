# manuscript/ - Research Manuscript

Research manuscript sections in markdown format, converted to PDFs.

## Quick Start

### Edit Manuscript
```bash
vim manuscript/02_introduction.md
vim manuscript/S01_supplemental_methods.md
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

### Main Sections (01-09)
- `01_abstract.md` - Research overview
- `02_introduction.md` - Project structure
- `03_methodology.md` - Mathematical framework
- `04_experimental_results.md` - Performance evaluation
- `05_discussion.md` - Theoretical implications
- `06_conclusion.md` - Summary and future work
- `08_acknowledgments.md` - Funding and acknowledgments
- `09_appendix.md` - Technical details and proofs

### Supplemental Sections (S01-S0N)
- `S01_supplemental_methods.md` - Extended methodological details
- `S02_supplemental_results.md` - Additional experimental results

### Reference Sections (98-99)
- `98_symbols_glossary.md` - Auto-generated API reference
- `99_references.md` - Bibliography (always last)

### Supporting Files
- `preamble.md` - LaTeX configuration (no PDF)
- `references.bib` - BibTeX bibliography

## Numbering Convention

**Main sections:** 01-09 (core manuscript)
**Supplemental sections:** S01-S0N (additional material)
**Reference sections:** 98 (glossary), 99 (bibliography - always last)

**Adding new sections:**
- Main: Use next number (e.g., `07_new_section.md`)
- Supplemental: Use next S## (e.g., `S03_new_supplement.md`)
- Keep references as `99_references.md`
- Keep glossary as `98_symbols_glossary.md`

## Cross-Referencing

### Sections
```markdown
## Introduction {#sec:intro}
See \ref{sec:intro} for details.
See \ref{sec:supplemental_methods} for extended methods.
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

## Section Ordering

The build system automatically orders sections:
1. **Main sections** (01-09) - Core manuscript
2. **Supplemental sections** (S01-S0N) - Additional material
3. **Glossary** (98) - Auto-generated API reference
4. **References** (99) - Bibliography (always last)

This ensures proper document flow with supplemental material clearly separated from main content.

## See Also

- [`AGENTS.md`](AGENTS.md) - Detailed documentation
- [`preamble.md`](preamble.md) - LaTeX configuration
- [`../docs/MARKDOWN_TEMPLATE_GUIDE.md`](../docs/MARKDOWN_TEMPLATE_GUIDE.md) - Full guide
