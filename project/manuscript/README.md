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
# Recommended: Enhanced from-scratch build (includes cleanup and validation)
./generate_pdf_from_scratch.sh

# With options
./generate_pdf_from_scratch.sh --verbose --log-file build.log

# Alternative: Manual steps
./repo_utilities/clean_output.sh
./repo_utilities/render_pdf.sh

# View output
open output/pdf/project_combined.pdf
# Or use the open script
./repo_utilities/open_manuscript.sh
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
- `S03_supplemental_analysis.md` - Extended theoretical analysis and complexity
- `S04_supplemental_applications.md` - Additional application examples

### Reference Sections (98-99)
- `98_symbols_glossary.md` - Auto-generated API reference
- `99_references.md` - Bibliography (always last)

### Supporting Files
- `preamble.md` - LaTeX configuration (no PDF)
- `references.bib` - BibTeX bibliography
- `config.yaml` - Paper metadata configuration (version-controllable)
- `config.yaml.example` - Configuration template

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

### Method 1: Configuration File (Recommended)

Edit `config.yaml` in the `manuscript/` directory:

```yaml
paper:
  title: "My Research Paper"

authors:
  - name: "Dr. Jane Smith"
    orcid: "0000-0000-0000-1234"
    email: "jane@example.edu"
    affiliation: "University of Example"
    corresponding: true

publication:
  doi: "10.5281/zenodo.12345678"  # Optional
```

See `config.yaml.example` for all available options.

### Method 2: Environment Variables (Backward Compatible)

```bash
export AUTHOR_NAME="Dr. Jane Smith"
export PROJECT_TITLE="My Research"
export AUTHOR_EMAIL="jane@example.edu"
./repo_utilities/render_pdf.sh
```

**Priority**: Environment variables override config file values.

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
