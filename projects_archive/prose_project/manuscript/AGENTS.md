# manuscript/ - Research Manuscript

## Overview

The `manuscript/` directory contains academic prose demonstrating the template's manuscript rendering capabilities. This project emphasizes mathematical notation, structured argumentation, and professional academic writing with LaTeX-style equations.

## Key Concepts

- **Mathematical exposition**: Clear presentation of mathematical concepts
- **Academic prose**: Formal scholarly writing conventions
- **Equation formatting**: LaTeX mathematical notation and derivations
- **Structured content**: Logical flow from introduction to conclusion

## Directory Structure

```
manuscript/
├── 00_abstract.md             # Research abstract and summary
├── 01_introduction.md         # Project motivation and context
├── 02_methodology.md          # Mathematical framework and methods
├── 03_results.md               # Analysis and findings
├── 04_conclusion.md            # Summary and implications
├── references.bib              # Academic bibliography
├── AGENTS.md                  # This technical documentation
└── README.md                  # Quick reference
```

## Installation/Setup

Manuscript uses standard markdown with LaTeX math extensions. Processed by the template's pandoc and LaTeX pipeline for professional PDF generation.

## Usage Examples

### Edit Manuscript Content

```bash
# Edit individual sections
vim 01_introduction.md
vim 02_methodology.md

# Generate complete manuscript PDF
python3 ../../scripts/03_render_pdf.py

# View rendered document
open ../../output/pdf/project_combined.pdf
```

### Mathematical Content

The manuscript demonstrates proper mathematical notation:

```latex
% Fundamental Theorem of Calculus
\frac{d}{dx} \int_a^x f(t) \, dt = f(x)

% Matrix operations
\mathbf{A} = \begin{pmatrix}
a_{11} & a_{12} \\
a_{21} & a_{22}
\end{pmatrix}
```

## Configuration

Manuscript sections follow academic paper structure with proper cross-referencing and citation formatting.

## Testing

Manuscript quality validated through template's validation system:

```bash
# Validate markdown structure
python3 -m infrastructure.validation.cli markdown .

# Check mathematical notation
python3 ../../scripts/04_validate_output.py
```

## API Reference

### Manuscript Sections

#### 00_abstract.md
Research abstract providing a concise summary of the mathematical framework, methodology, key results, and contributions.

**Content Structure:**
- Research focus and scope
- Key theoretical contributions
- Brief methodology overview
- Main findings and implications

#### 01_introduction.md
Project introduction with research context and motivation.

**Content Structure:**
- Research domain overview
- Problem statement
- Key contributions
- Document organization

#### 02_methodology.md
Mathematical methodology and theoretical framework.

**Key Elements:**
- Mathematical formulations
- Equation derivations
- Methodological approach
- Theoretical foundations

#### 03_results.md
Results and analysis section.

**Content:**
- Findings presentation
- Data interpretation
- Result validation
- Comparative analysis

#### 04_conclusion.md
Conclusion with summary and future directions.

**Structure:**
- Key findings recap
- Contribution summary
- Limitations discussion
- Future work suggestions

#### references.bib
Bibliography in BibTeX format for academic citations.

## Troubleshooting

### Common Issues

- **LaTeX compilation errors**: Check mathematical notation syntax
- **Cross-reference issues**: Verify equation and section labels
- **Figure references**: Ensure figures are properly labeled

### Debug Tips

Render individual sections for debugging:
```bash
# Test single section rendering
python3 ../../scripts/03_render_pdf.py --section 02_methodology
```

Validate mathematical expressions:
```bash
# Check LaTeX syntax
pandoc 02_methodology.md -t latex | head -50
```

## Best Practices

- **Mathematical accuracy**: Ensure all equations are mathematically correct
- **Consistent notation**: Use consistent symbols and formatting throughout
- **Clear exposition**: Explain complex concepts with clear prose
- **Proper citations**: Reference sources appropriately
- **Academic tone**: Maintain formal scholarly writing style

## See Also

- [README.md](README.md) - Quick reference
- [PDF generation script](../../../scripts/03_render_pdf.py) - PDF generation
- [Validation module](../../../infrastructure/validation/AGENTS.md) - Content validation