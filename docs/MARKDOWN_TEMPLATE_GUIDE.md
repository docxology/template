# Markdown Template Guide

This document explains the comprehensive markdown template structure and cross-referencing system implemented in this project. For related information, see **[`docs/HOW_TO_USE.md`](HOW_TO_USE.md)** for complete usage guidance, **[`docs/ARCHITECTURE.md`](ARCHITECTURE.md)**, **[`docs/WORKFLOW.md`](WORKFLOW.md)**, and **[`README.md`](README.md)**.

## Template Structure

The template demonstrates a complete academic paper structure with the following markdown files:

### Core Sections

1. **`manuscript/preamble.md`** - LaTeX preamble with enhanced styling and packages
2. **`manuscript/01_abstract.md`** - Research overview and key contributions
3. **`manuscript/02_introduction.md`** - Introduction with section references and overview
4. **`manuscript/03_methodology.md`** - Mathematical framework with numbered equations
5. **`manuscript/04_experimental_results.md`** - Results with figure and equation references
6. **`manuscript/05_discussion.md`** - Discussion with cross-references to previous sections
7. **`manuscript/06_conclusion.md`** - Conclusion summarizing all contributions
8. **`manuscript/10_symbols_glossary.md`** - Auto-generated API reference from `src/`

## Cross-Referencing System

### Section References

Use `\ref{sec:section_name}` to reference sections:

```markdown
# Introduction {#sec:introduction}

The methodology described in Section \ref{sec:methodology} shows...
```

**Available section labels:**
- `{#sec:introduction}` - Introduction
- `{#sec:methodology}` - Methodology  
- `{#sec:experimental_results}` - Experimental Results
- `{#sec:discussion}` - Discussion
- `{#sec:conclusion}` - Conclusion

### Equation References

Use `\eqref{eq:equation_name}` to reference equations:

```markdown
\begin{equation}\label{eq:convergence}
\|x_k - x^*\| \leq C \rho^k
\end{equation}

The convergence rate \eqref{eq:convergence} shows...
```

**Key equations in the template:**
- `eq:objective` - Main objective function
- `eq:optimization` - Optimization problem
- `eq:update` - Algorithm update rule
- `eq:convergence` - Convergence bound
- `eq:adaptive_step` - Adaptive step size
- `eq:memory` - Memory scaling
- `eq:accuracy` - Accuracy metric
- `eq:advantage_metric` - Performance advantage
- `eq:robustness_metric` - Robustness measure
- `eq:complexity_bound` - Complexity bound
- `eq:final_improvement` - Overall improvement

### Figure References

Use `\ref{fig:figure_name}` to reference figures:

```markdown
\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/experimental_setup.png}
\caption{Experimental setup diagram}
\label{fig:experimental_setup}
\end{figure}

Figure \ref{fig:experimental_setup} shows the pipeline...
```

**Available figures:**
- `fig:example_figure` - Basic example function plot
- `fig:convergence_plot` - Algorithm convergence comparison
- `fig:experimental_setup` - Experimental pipeline diagram
- `fig:scalability_analysis` - Performance scaling analysis
- `fig:ablation_study` - Component ablation results
- `fig:hyperparameter_sensitivity` - Parameter sensitivity surface

### Table References

Use `\ref{tab:table_name}` to reference tables:

```markdown
| Metric | Value | Unit |
|--------|-------|------|
| Performance | 23.7% | improvement |

Table \ref{tab:performance_summary} shows...
```

## LaTeX Features Demonstrated

### Equation Environments

The template shows proper use of LaTeX equation environments:

```markdown
\begin{equation}\label{eq:example}
f(x) = \sum_{i=1}^{n} w_i \phi_i(x)
\end{equation}
```

### Mathematical Notation

Examples of mathematical notation used:

- **Greek letters**: $\alpha$, $\beta$, $\lambda$, $\rho$, $\epsilon$
- **Mathematical operators**: $\min$, $\max$, $\sum$, $\prod$
- **Special symbols**: $\mathbb{R}$, $\mathcal{X}$, $\nabla$
- **Subscripts/superscripts**: $x_k$, $x^*$, $w_i$

### Cross-References in Text

Demonstrates various cross-reference patterns:

```markdown
- Section references: Section \ref{sec:methodology}
- Equation references: \eqref{eq:convergence}
- Figure references: Figure \ref{fig:convergence_plot}
- Multiple references: equations \eqref{eq:objective} through \eqref{eq:convergence}
```

## Figure Generation

### Scripts

The template includes two figure generation scripts that demonstrate the **thin orchestrator pattern**:

1. **`example_figure.py`** - Basic example figure using `src/` methods
2. **`generate_research_figures.py`** - Comprehensive research figures using `src/` methods

### Thin Orchestrator Pattern

Scripts in the `scripts/` directory are **thin orchestrators** that:

- **Import** mathematical functions from `src/` modules
- **Use** tested methods for all computation (never implement algorithms)
- **Handle** visualization, I/O, and orchestration
- **Generate** figures and data outputs
- **Validate** that `src/` integration works correctly

**Example integration:**
```python
# Import src/ methods for computation
from example import add_numbers, calculate_average

def generate_figure():
    # Use src/ methods for all computation
    data = [1, 2, 3, 4, 5]
    avg = calculate_average(data)  # From src/example.py
    
    # Script handles visualization and output
    fig, ax = plt.subplots()
    ax.plot(data)
    ax.set_title(f"Average: {avg}")
    return fig
```

### Output Structure

Figures are automatically saved to:
- `output/figures/` - PNG files
- `output/data/` - NPZ and CSV data files

### Integration

Figures are referenced in markdown using relative paths:
```markdown
\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/figure_name.png}
\caption{Figure caption}
\label{fig:figure_name}
\end{figure}
```

## Validation System

### Manuscript Validation

The `validate_markdown.py` script checks:
- Image file existence
- Equation label uniqueness
- Cross-reference validity
- No bare URLs

### Glossary Generation

The `generate_glossary.py` script:
- Scans `src/` for public APIs
- Generates markdown table
- Updates `10_symbols_glossary.md` automatically

## Build Process

### Complete Pipeline

The pipeline orchestrator (`scripts/run_all.py`):

1. **Runs tests** with coverage requirements (70% project, 49% infra)
2. **Executes scripts** to generate figures and data (validating src/ integration)
3. **Validates manuscript** for references and images
4. **Generates glossary** from source code
5. **Builds individual PDFs** for each manuscript file
6. **Creates combined PDF** with all sections
7. **Exports LaTeX** source files

### Output Files

Generated outputs include:
- Individual PDFs for each section
- Combined PDF with all sections
- LaTeX source files
- Figures and data files
- Coverage reports

## Best Practices

### Writing New Sections

1. **Add section label**: `# Section Title {#sec:section_name}`
2. **Use descriptive equation labels**: `\label{eq:descriptive_name}`
3. **Reference previous content**: Use `\ref{}` and `\eqref{}`
4. **Include figures**: Reference generated figures with `\ref{fig:name}`

### Adding Equations

1. **Use equation environment**: `\begin{equation}\label{eq:name}...\end{equation}`
2. **Choose descriptive labels**: Avoid generic names like `eq:1`
3. **Reference consistently**: Use `\eqref{eq:name}` throughout

### Creating Figures

1. **Generate with scripts**: Use scripts in `scripts/` directory
2. **Use src/ methods**: Import and use tested methods from `src/` modules
3. **Save to output**: Place in `output/figures/`
4. **Reference properly**: Use `\ref{fig:name}` in markdown
5. **Include data**: Save both figures and data files

## Customization

### Adding New Sections

1. Create new markdown file in `manuscript/`
2. Add section label: `{#sec:new_section}`
3. Include cross-references to existing content
4. Add to the build pipeline (automatic)

### Modifying Equations

1. Update equation content and labels
2. Update all references using `\eqref{}`
3. Ensure label uniqueness across document

### Extending Figures

1. **Add new figure generation functions** to existing scripts or create new ones
2. **Import from src/**: Ensure scripts use `src/` methods for computation
3. **Update scripts** to generate new figures
4. **Add figure references** in markdown
5. **Ensure proper file paths** and naming

### Adding New Source Code

1. **Create new modules** in `src/` directory
2. **Add comprehensive tests** in `tests/` directory (coverage requirements apply)
3. **Update scripts** to import and use new `src/` methods
4. **Validate integration** through the build pipeline

## Troubleshooting

### Common Issues

1. **Missing references**: Check that labels exist and are spelled correctly
2. **Figure not found**: Verify figure file exists in `output/figures/`
3. **Equation numbering**: Ensure unique labels across all files
4. **Build failures**: Check markdown validation output
5. **Script import errors**: Ensure `src/` modules exist and are properly tested

### Validation Errors

The validation system will report:
- Missing image files
- Unresolved cross-references
- Duplicate equation labels
- Bare URLs or non-informative links

### Fixing Issues

1. **Missing figures**: Run appropriate generation scripts
2. **Broken references**: Check label spelling and existence
3. **Validation errors**: Address each reported issue
4. **Build failures**: Fix all validation issues before rebuilding
5. **Import errors**: Ensure `src/` modules meet coverage requirements

## Architecture Compliance

### Thin Orchestrator Pattern

This template enforces the **thin orchestrator pattern** where:

- **`src/`** contains ALL business logic, algorithms, and mathematical implementations
- **`scripts/`** are lightweight wrappers that import and use `src/` methods
- **`tests/`** ensures comprehensive coverage of `src/` functionality
- **`scripts/run_all.py`** orchestrates the entire 6-stage pipeline

### Script Requirements

Scripts in `scripts/` MUST:
- Import methods from `@src/` modules
- Use `src/` methods for all computation
- Handle only I/O, visualization, and orchestration
- Include proper error handling for imports
- Print output paths for render system
- Set `MPLBACKEND=Agg` for headless operation

Scripts MUST NOT:
- Implement mathematical algorithms
- Duplicate business logic from `@src/`
- Contain complex computations
- Define new data structures

## Summary

This template provides a complete framework for academic writing with:

- **Structured organization** of content into logical sections
- **Comprehensive cross-referencing** system for equations, figures, and sections
- **Automated figure generation** with proper integration using `src/` methods
- **Validation system** ensuring document integrity
- **Build pipeline** generating both individual and combined PDFs
- **LaTeX export** for further customization
- **Thin orchestrator pattern** ensuring maintainability and testability

The system demonstrates best practices for academic writing while maintaining the flexibility to adapt to different research domains and writing styles, all while enforcing the architectural principles of the generic project template.

For more details on architecture and workflow, see **[`ARCHITECTURE.md`](ARCHITECTURE.md)** and **[`WORKFLOW.md`](WORKFLOW.md)**.
