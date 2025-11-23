# manuscript/ - Research Manuscript

## Purpose

The `manuscript/` directory contains research manuscript sections in markdown format. These files are processed by `render_pdf.sh` to generate individual section PDFs and a combined manuscript document.

## File Structure

### Manuscript Sections (Generate PDFs)

| File | Purpose | Generates PDF |
|------|---------|---------------|
| `01_abstract.md` | Research overview and key contributions | ✅ |
| `02_introduction.md` | Project structure and motivation | ✅ |
| `03_methodology.md` | Mathematical framework and algorithms | ✅ |
| `04_experimental_results.md` | Performance evaluation and validation | ✅ |
| `05_discussion.md` | Theoretical implications and comparisons | ✅ |
| `06_conclusion.md` | Summary and future directions | ✅ |
| `08_acknowledgments.md` | Funding, collaborators, and acknowledgments | ✅ |
| `09_appendix.md` | Technical details, proofs, and derivations | ✅ |
| **Supplemental Sections** | | |
| `S01_supplemental_methods.md` | Extended methodological details | ✅ |
| `S02_supplemental_results.md` | Additional experimental results | ✅ |
| `S03_supplemental_analysis.md` | Extended theoretical analysis and complexity | ✅ |
| `S04_supplemental_applications.md` | Additional application examples | ✅ |
| **Reference Sections** | | |
| `98_symbols_glossary.md` | Auto-generated API reference from `src/` | ✅ |
| `99_references.md` | Bibliography and cited works (always last) | ✅ |

### Supporting Files (No PDF Generation)

| File | Purpose |
|------|---------|
| `preamble.md` | LaTeX preamble and document styling |
| `references.bib` | BibTeX bibliography database |
| `config.yaml` | Paper metadata configuration (title, authors, DOI, etc.) |
| `config.yaml.example` | Configuration template with all options documented |

## Numbering Convention

Files are numbered to control document ordering:

### Main Sections (01-09)
- `01-06`: Core manuscript sections (Abstract → Conclusion)
- `08`: Acknowledgments
- `09`: Appendix

### Supplemental Sections (S01-S0N)
- `S01-S99`: Supplemental material (methods, results, etc.)
- Prefix `S` identifies supplemental content
- Numbered sequentially: `S01`, `S02`, `S03`, etc.

### Reference Sections (98-99)
- `98`: Auto-generated API glossary
- `99`: Bibliography (always last section)

**Ordering guarantees:**
1. Main sections (01-09) appear first
2. Supplemental sections (S01-S0N) appear after main content
3. References (99) always appears last
4. Glossary (98) appears just before references

**Adding new sections:**
- Main sections: Use next available number (e.g., `07_`, `10_`)
- Supplemental sections: Use next `S##` number (e.g., `S03_`, `S04_`)
- References: Always keep as `99_references.md`
- Glossary: Always keep as `98_symbols_glossary.md`

## preamble.md - LaTeX Styling

The `preamble.md` file contains LaTeX configuration wrapped in markdown code blocks:

```markdown
# LaTeX Preamble

```latex
\usepackage{amsmath}
\usepackage{graphicx}
% ... additional LaTeX commands ...
```
```

**Key features:**
- Custom LaTeX packages
- Document styling
- Mathematical notation setup
- Figure and table formatting
- Cross-reference configuration

**Note:** Does NOT generate a separate PDF - content is extracted and injected into document preambles.

## references.bib - Bibliography

BibTeX format bibliography file:

```bibtex
@article{author2023,
  title={Title},
  author={Author, Name},
  journal={Journal},
  year={2023},
  volume={1},
  pages={1-10}
}
```

Citations in markdown:
```markdown
According to \cite{author2023}, the method...
```

### Bibliography Processing Workflow

The citation system uses **BibTeX with plainnat style** for robust bibliography management:

**Processing Flow:**
1. Manuscript markdown files contain `\cite{key}` commands
2. During PDF rendering, Pandoc preserves these LaTeX citation commands (no `--citeproc`)
3. The `references.bib` file is **copied into the build directory** to satisfy BibTeX security constraints
4. XeLaTeX generates `.aux` file listing all citations
5. BibTeX processes the `.aux` file and generates `.bbl` (bibliography list) file
6. XeLaTeX performs multiple compilation passes to resolve all citations and cross-references

**Key Points:**
- Citation keys are **case-sensitive** (use exact keys from `references.bib`)
- All cited entries must exist in `references.bib`
- The References section uses `\bibliography{references}` and `\nocite{*}` commands in `99_references.md`
- Bibliography style is set to `plainnat` for numbered citations like `[1]`, `[2]`

**Bibliography Security:**
- BibTeX operates in "paranoid" security mode by default
- It restricts file access across directories
- Solution: Copy `references.bib` into the compilation directory before running BibTeX
- This ensures all files are local to the execution context

## Cross-Referencing

### Section References
```markdown
## Introduction {#sec:introduction}

As discussed in \ref{sec:introduction}...

Supplemental methods in \ref{sec:supplemental_methods}...
```

### Equation References
```markdown
\begin{equation}
\label{eq:myequation}
f(x) = x^2
\end{equation}

Using \eqref{eq:myequation}, we derive...
```

### Figure References
```markdown
\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/example_figure.png}
\caption{Example figure demonstrating the concept.}
\label{fig:example}
\end{figure}

As shown in \ref{fig:example}...
```

### Figure Insertion and Path Resolution

**Figure Storage:**
- All figures are generated to or placed in `project/output/figures/`
- Supported formats: PNG, PDF, JPG, JPEG

**Path References:**
- Use relative paths from the `project/` directory: `../output/figures/filename.png`
- Paths are resolved relative to the manuscript compilation directory
- The rendering system handles path resolution automatically

**Figure Generation Workflow:**
1. Scripts in `project/scripts/` generate figures to `project/output/figures/`
2. Markdown files reference figures using `\includegraphics[width=...]{../output/figures/filename.png}`
3. Figure labels use LaTeX `\label{fig:label_name}` for cross-referencing
4. References to figures use `\ref{fig:label_name}` or embedded in figure captions

**Figure Registry:**
- `project/output/figures/figure_registry.json` maintains a record of all generated figures
- Includes metadata for each figure (path, label, description)
- Used by validation systems to verify all figure references

### Table References
```markdown
\begin{table}[h]
\centering
\begin{tabular}{ll}
Item & Value \\
\hline
A & 1 \\
B & 2 \\
\end{tabular}
\caption{Example table.}
\label{tab:example}
\end{table}

Table \ref{tab:example} shows...
```

## LaTeX Integration

### Mathematical Notation

**Inline math:**
```markdown
The variable $x$ represents...
```

**Display equations:**
```markdown
\begin{equation}
\label{eq:name}
f(x) = \int_0^x t^2 dt
\end{equation}
```

**Do NOT use:**
- Double dollar signs (e.g., `$$ ... $$`) for display math—use equation environment instead
- Backslash square brackets (e.g., `\[ ... \]`) for display math—use equation environment instead

### Figure Integration

Figures must reference files in `output/figures/`:

```markdown
\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/convergence_plot.png}
\caption{Convergence behavior over iterations.}
\label{fig:convergence}
\end{figure}
```

**Requirements:**
- Path: `../output/figures/` (relative to manuscript/)
- Generated by scripts in `scripts/`
- PNG format recommended
- Descriptive labels (e.g., `fig:convergence`)

## 98_symbols_glossary.md - Auto-Generation

This file is **automatically generated** from `src/` module APIs:

```markdown
# API Symbols Glossary

This glossary is auto-generated from the public API in `src/`.

<!-- BEGIN: AUTO-API-GLOSSARY -->
| Module | Name | Kind | Summary |
|---|---|---|---|
| `example` | `add_numbers` | function | Add two numbers together. |
| `example` | `calculate_average` | function | Calculate the average of a list... |
<!-- END: AUTO-API-GLOSSARY -->
```

**Generation process:**
1. `scripts/03_render_pdf.py` scans `project/src/`
2. Extracts public functions and classes
3. Builds markdown table
4. Writes directly to `manuscript/98_symbols_glossary.md`

**Do NOT edit** the auto-generated content between markers.

## Building PDFs

### Individual Section PDFs

```bash
# Builds all individual section PDFs
python3 scripts/03_render_pdf.py
```

Output: `project/output/pdf/01_abstract.pdf`, `02_introduction.pdf`, `S01_supplemental_methods.pdf`, etc.

### Combined Manuscript PDF

```bash
# Builds combined manuscript
python3 scripts/03_render_pdf.py
```

Output: `output/pdf/project_combined.pdf`

**Combined PDF includes:**
- Custom title page
- Abstract (before TOC)
- Table of contents
- All numbered main sections (01-09)
- All supplemental sections (S01-S0N)
- API glossary (98)
- Bibliography (99, always last)

## Editing Workflow

### 1. Edit Markdown Files
Edit any `*.md` file in `manuscript/` directory:
```bash
vim manuscript/02_introduction.md
vim manuscript/S01_supplemental_methods.md
```

### 2. Generate Figures (if needed)
If adding new figures, create script in `scripts/`:
```python
# scripts/my_figure.py
from example import calculate_average
# ... generate figure ...
plt.savefig("output/figures/my_figure.png")
```

### 3. Reference Figure in Markdown
```markdown
\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/my_figure.png}
\caption{My new figure.}
\label{fig:myfigure}
\end{figure}
```

### 4. Validate and Build
```bash
# Clean previous outputs  
python3 scripts/run_all.py --clean

# Build everything (recommended)
python3 scripts/run_all.py

# Or run individual stages
python3 scripts/03_render_pdf.py
```

### 5. Review Output
```bash
# Open combined PDF
open output/pdf/project_combined.pdf

# Or HTML version (better for IDEs)
open output/project_combined.html
```

## Adding New Sections

### Adding Main Sections

1. Create new file with next available number:
   ```bash
   vim manuscript/07_new_section.md
   ```

2. Include section header with label:
   ```markdown
   # New Section {#sec:newsection}
   
   Content here...
   ```

3. Build and verify ordering:
   ```bash
   python3 scripts/03_render_pdf.py
   ```

### Adding Supplemental Sections

1. Create new file with `S##` prefix:
   ```bash
   vim manuscript/S03_supplemental_figures.md
   ```

2. Include section header with label:
   ```markdown
   # Supplemental Figures {#sec:supplemental_figures}
   
   Extended figures and visualizations...
   ```

3. Reference from main text:
   ```markdown
   Additional results in \ref{sec:supplemental_figures}...
   ```

4. Build and verify:
   ```bash
   python3 scripts/03_render_pdf.py
   ```

## Configuration

### Configuration File (Recommended)

The manuscript configuration is managed through `manuscript/config.yaml`, which provides a centralized, version-controllable way to manage all paper metadata.

**Location**: `manuscript/config.yaml`

**Template**: `manuscript/config.yaml.example` (copy and customize)

**Example configuration**:
```yaml
paper:
  title: "Advanced Research Framework"
  subtitle: ""  # Optional
  version: "1.0"

authors:
  - name: "Dr. Jane Smith"
    orcid: "0000-0000-0000-1234"
    email: "jane.smith@university.edu"
    affiliation: "University of Example"
    corresponding: true

publication:
  doi: "10.5281/zenodo.12345678"  # Optional
  journal: ""  # Optional
  volume: ""  # Optional
  pages: ""  # Optional

keywords:
  - "optimization"
  - "machine learning"

metadata:
  license: "Apache-2.0"
  language: "en"
```

**Benefits**:
- ✅ Version controllable (can be committed to git)
- ✅ Single file for all metadata
- ✅ Supports multiple authors
- ✅ Structured format (YAML)
- ✅ Easy to edit and maintain

### Environment Variables (Backward Compatible)

For backward compatibility, environment variables still work and take precedence over config file values:

```bash
export AUTHOR_NAME="Dr. Jane Smith"
export AUTHOR_ORCID="0000-0000-0000-1234"
export AUTHOR_EMAIL="jane.smith@university.edu"
export PROJECT_TITLE="Advanced Research Framework"
export DOI="10.5281/zenodo.12345678"  # Optional

./repo_utilities/render_pdf.sh
```

**Priority order**:
1. Environment variables (highest priority)
2. Config file (`manuscript/config.yaml`)
3. Default values (lowest priority)

### Multiple Authors

The config file supports multiple authors:

```yaml
authors:
  - name: "Dr. Jane Smith"
    orcid: "0000-0000-0000-1234"
    email: "jane.smith@university.edu"
    affiliation: "University of Example"
    corresponding: true
  - name: "Dr. John Doe"
    orcid: "0000-0000-0000-5678"
    email: "john.doe@university.edu"
    affiliation: "Another University"
    corresponding: false
```

The first author (or the one marked `corresponding: true`) is used for PDF metadata.

## Validation

### Markdown Validation
```bash
# Check for issues
python3 -m infrastructure.validation.cli markdown manuscript/

# Strict mode (fail on any issues)
python3 -m infrastructure.validation.cli markdown manuscript/ --strict
```

**Validates:**
- Image references exist
- Cross-references are valid
- Equation labels are unique
- No bare URLs
- LaTeX equation syntax

### PDF Validation
```bash
# Check rendered PDF
python3 -m infrastructure.validation.cli pdf project/output/pdf/

# Specific section
python3 -m infrastructure.validation.cli pdf project/output/pdf/01_abstract.pdf
```

**Detects:**
- Unresolved references (??)
- Missing citations ([?])
- LaTeX warnings
- Rendering issues

## Best Practices

### Markdown Writing
- Use descriptive cross-reference labels
- Always label equations, figures, and tables
- Keep section structure hierarchical
- Use consistent heading levels

### Figure Integration
- Generate figures from scripts (reproducible)
- Save to `output/figures/`
- Use descriptive filenames
- Include captions and labels

### Cross-References
- Use `\ref{}` for sections, figures, tables
- Use `\eqref{}` for equations
- Use `\cite{}` for bibliography
- Ensure all references have labels

### LaTeX Math
- Use equation environment for display math
- Label all important equations
- Use `\eqref{}` to reference equations
- Avoid double dollar signs or backslash square brackets for display math

### Supplemental Material
- Use for extended methods, additional results
- Reference from main text appropriately
- Maintain consistent formatting with main text
- Number supplemental figures/tables distinctly (e.g., S1, S2)

## Output Formats

### Standard PDF (`project_combined.pdf`)
- Professional printing quality
- Full LaTeX rendering
- Complete cross-references
- Publication-ready

### IDE-Friendly PDF (`project_combined_ide_friendly.pdf`)
- Optimized for text editor viewing
- Better font rendering
- Simplified layout

### HTML Version (`project_combined.html`)
- Web browser compatible
- IDE integration
- Interactive features
- Faster loading

## Troubleshooting

### Missing Figures
```bash
# Ensure scripts generated figures
ls project/output/figures/

# Check figure path in markdown
grep "includegraphics" project/manuscript/*.md
```

### Unresolved References
```bash
# Validate all references
python3 -m infrastructure.validation.cli markdown project/manuscript/

# Check for ?? in PDF
python3 -m infrastructure.validation.cli pdf project/output/pdf/
```

### LaTeX Errors
```bash
# Check compilation log
cat project/output/pdf/project_combined_compile.log
```

### Section Ordering Issues
```bash
# List sections in order
ls -1 project/manuscript/*.md | grep -E '^[0-9]|^S[0-9]'

# Verify order matches:
# 01-09: Main sections
# S01-S0N: Supplemental sections
# 98: Glossary
# 99: References
```

## See Also

- [`preamble.md`](preamble.md) - LaTeX configuration
- [`references.bib`](references.bib) - Bibliography
- [`../docs/MARKDOWN_TEMPLATE_GUIDE.md`](../docs/MARKDOWN_TEMPLATE_GUIDE.md) - Markdown guide
- [`../scripts/README.md`](../scripts/README.md) - Entry point orchestrators
- [`../AGENTS.md`](../AGENTS.md) - Complete system documentation
