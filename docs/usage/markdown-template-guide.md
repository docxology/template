# Markdown Template Guide

This document explains the markdown template structure and cross-referencing system implemented in this project. For related information, see **[`../core/how-to-use.md`](../core/how-to-use.md)** for usage guidance, **[`../core/architecture.md`](../core/architecture.md)**, **[`../core/workflow.md`](../core/workflow.md)**, and **[`../README.md`](../README.md)**.

## Template Structure

The template demonstrates an academic paper structure organized as numbered markdown sections.

> **Note:** The section file names, section labels (`{#sec:...}`), and the `eq:`/`fig:` labels listed throughout this guide are *illustrative naming patterns*, not the literal contents of any one exemplar. The canonical `template_code_project` ships `00_abstract.md`, `01_introduction.md`, `02_methodology.md`, `03_results.md`, `04_conclusion.md`, `05_experimental_setup.md`, `06_reproducibility.md`, `07_scope_and_related_work.md`, and `99_references.md` (plus `preamble.md`). List the real files for your checkout with `ls projects/templates/template_code_project/manuscript/`.

### Core Sections (illustrative)

1. **`manuscript/preamble.md`** - LaTeX preamble with styling and packages
2. **`manuscript/00_abstract.md`** - Research overview and key contributions
3. **`manuscript/01_introduction.md`** - Introduction with section references and overview
4. **`manuscript/02_methodology.md`** - Mathematical framework with numbered equations
5. **`manuscript/03_results.md`** - Results with figure and equation references
6. **`manuscript/04_conclusion.md`** - Conclusion summarizing all contributions
7. **`manuscript/05_experimental_setup.md`** - Experimental setup and methodology details
8. **`manuscript/06_reproducibility.md`** - Reproducibility and code availability
9. **`manuscript/07_scope_and_related_work.md`** - Scope and related work
10. **`manuscript/99_references.md`** - Bibliography and references

## Cross-Referencing System

### Section References

Use `[@sec:section_name]` to reference sections — never raw `\ref{}` or a
Markdown filename link (see [Manuscript Semantics](../guides/manuscript-semantics.md)):

```markdown
# Introduction {#sec:introduction}

The methodology described in [@sec:methodology] shows...
```

Labels are project-owned. Discover the current set instead of copying this
guide's examples:

```bash
rg -n '\{#sec:' projects/templates/template_code_project/manuscript/
```

### Equation References

Use `[@eq:equation_name]` to reference equations — never raw `\eqref{}`:

```markdown
$$
\|x_k - x^*\| \leq C \rho^k
$$ {#eq:convergence}

The convergence rate [@eq:convergence] shows...
```

Equation labels are likewise project-owned. Inspect them with
`rg -n '\{#eq:|\\label\{eq:' projects/<qualified-name>/manuscript/`.

### Figure References

Use `[@fig:figure_name]` to reference figures — never raw `\ref{}`:

```markdown
![Experimental setup diagram.](../output/figures/experimental_setup.png){#fig:experimental_setup width=80%}

[@fig:experimental_setup] shows the pipeline...
```

Figure labels are declared by each manuscript and its generated figure
registry. Inspect both before adding a reference; do not assume an illustrative
label exists.

### Table References

Use `[@tbl:table_name]` to reference tables — never raw `\ref{}`:

```markdown
| Metric | Value | Unit |
|--------|-------|------|
| Performance | {{PERFORMANCE_VALUE}} | {{PERFORMANCE_UNIT}} |

: Performance summary. {#tbl:performance_summary}

[@tbl:performance_summary] shows...
```

## Equations and Cross-References

### Equation Forms

The template supports two equivalent forms for a labelled display equation —
the pure-Pandoc form is preferred; the raw-LaTeX `equation` environment also
works because pandoc-crossref picks up `\label{}`:

```markdown
$$
f(x) = \sum_{i=1}^{n} w_i \phi_i(x)
$$ {#eq:example}
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
- Section references: [@sec:methodology]
- Equation references: [@eq:convergence]
- Figure references: [@fig:convergence_plot]
- Multiple references: [@eq:objective] through [@eq:convergence]
```

## Figure Generation

### Scripts

The template includes two figure generation scripts that demonstrate the **thin orchestrator pattern**:

1. **`projects/{name}/scripts/<analysis>.py`** - Thin orchestrator (code exemplar: `optimization_analysis.py`) using `projects/{name}/src/` methods
2. **`projects/{name}/scripts/y_generate_*`** - Optional ordered figure/analysis scripts (prose exemplar pattern)

### Thin Orchestrator Pattern

Scripts in the `scripts/` directory are **thin orchestrators** that:

- **Import** mathematical functions from `projects/{name}/src/` modules
- **Use** tested methods for all computation (never implement algorithms)
- **Handle** visualization, I/O, and orchestration
- **Generate** figures and data outputs
- **Validate** that `projects/{name}/src/` integration works correctly

**Example integration:**

```python
# When the script adds its project root to sys.path, import the project package.
from src.optimizer import compute_gradient, quadratic_function

def generate_figure():
    # Use projects/{name}/src/ methods for all computation
    data = [-2.0, -1.0, 0.0, 1.0, 2.0]
    gradients = [compute_gradient([value])[0] for value in data]
    objectives = [quadratic_function([value]) for value in data]

    # Script handles visualization and output
    fig, ax = plt.subplots()
    ax.plot(data, objectives, label="Objective")
    ax.plot(data, gradients, label="Gradient")
    ax.legend()
    return fig
```

### Output Structure

Project analysis scripts save outputs to:

- `projects/<qualified-name>/output/figures/` - figure files and registry
- `projects/<qualified-name>/output/data/` - data, manifests, and manuscript variables

### Integration

Figures are referenced in markdown using relative paths, Pandoc image syntax,
and a `{#fig:name}` attribute:

```markdown
![Figure caption.](../output/figures/figure_name.png){#fig:figure_name width=80%}
```

## Source-injected manuscript variables

Any value that can change when data, configuration, code, or analysis changes
must be a `{{TOKEN}}` in source manuscript files. This includes statistics in
prose, tables, visible captions, annotations, and accessibility descriptions.
The canonical flow is:

```text
tested project src + config + analysis outputs
  -> project manuscript-variable producer
  -> output/data/manuscript_variables.json
  -> write_resolved_manuscript_tree(...)
  -> output/manuscript/*.md
  -> enabled renderers
```

The pipeline normally hydrates this render tree before rendering. The
control-positive exemplar's producer is
`projects/templates/template_code_project/scripts/z_generate_manuscript_variables.py`;
its default mode fails if required analysis outputs are missing. Use its
`--allow-draft` option only for an intentional early draft.

Do not hand-edit `manuscript_variables.json` or hydrated files under
`output/manuscript/`. Extend the project-owned producer, regenerate, and fail
validation if a required token is unresolved. Keep visible captions distinct
from concise registry alt text, with longer descriptions in nearby prose when
the visualization is complex. See
[Manuscript Semantics](../guides/manuscript-semantics.md).

## Validation System

### Manuscript Validation

Markdown validation is performed via the infrastructure validation module:

```bash
uv run python -m infrastructure.validation.cli markdown \
  projects/templates/template_code_project/manuscript/
```

This checks:

- Image file existence
- Equation label uniqueness
- Cross-reference validity
- No bare URLs

### Glossary Generation

Glossary generation is **not** a fixed numbered pipeline stage in the root `scripts/` DAG; run it **manually** when needed (see [modules guide](../modules/modules-guide.md#documentation-generation)):

```bash
uv run python -m infrastructure.documentation.generate_glossary_cli \
  projects/templates/template_code_project/src/ projects/templates/template_code_project/manuscript/98_symbols_glossary.md
```

This:

- Scans the given `src/` tree for public APIs
- Generates a markdown table
- Injects it into the target manuscript file (created if missing)

## Build Process

### Pipeline

The pipeline orchestrator (`./run.sh pipeline` or the compatibility entry point
`scripts/runner/execute_pipeline.py`):

1. **Runs tests** with coverage requirements (90% project, 60% infra)
2. **Executes scripts** to generate figures and data (validating projects/{name}/src/ integration)
3. **Hydrates manuscript variables** into the output render tree
4. **Validates manuscript** for references and images
5. **Builds enabled formats** from the hydrated sources
6. **Validates and copies** deliverables and evidence

### Output Files

Generated outputs include:

- Enabled PDF, HTML, slide, DOCX, and EPUB artifacts (see
  [Output formats](output-formats.md))
- Intermediate LaTeX and combined markdown used by renderers
- Figures and data files
- Coverage reports

## Best Practices

### Writing New Sections

1. **Add section label**: `# Section Title {#sec:section_name}`
2. **Use descriptive equation labels**: `{#eq:descriptive_name}`
3. **Reference previous content**: Use `[@sec:name]` and `[@eq:name]` — never raw `\ref{}`/`\eqref{}`
4. **Include figures**: Reference generated figures with `[@fig:name]`

### Adding Equations

1. **Use a labelled display block**: `$$ ... $$ {#eq:name}` (or `\begin{equation}\label{eq:name}...\end{equation}`)
2. **Choose descriptive labels**: Avoid generic names like `eq:1`
3. **Reference consistently**: Use `[@eq:name]` throughout — never `\eqref{}`

### Creating Figures

1. **Generate with scripts**: Use scripts in the selected project's `scripts/` directory
2. **Use project `src/` methods**: Import and use tested methods from the selected project's `src/` modules
3. **Save to project output**: Place in the selected project's `output/figures/`
4. **Reference properly**: Use `[@fig:name]` in markdown — never `\ref{}`
5. **Include data**: Save both figures and data files

## Customization

### Adding New Sections

1. Create new markdown file in `manuscript/`
2. Add section label: `{#sec:new_section}`
3. Include cross-references to existing content
4. Add to the build pipeline (automatic)

### Modifying Equations

1. Update equation content and labels
2. Update all references using `[@eq:name]`
3. Ensure label uniqueness across document

### Extending Figures

1. **Add new figure generation functions** to existing scripts or create new ones
2. **Import from projects/{name}/src/**: Ensure scripts use `projects/{name}/src/` methods for computation
3. **Update scripts** to generate new figures
4. **Add figure references** in markdown
5. **Ensure proper file paths** and naming

### Adding New Source Code

1. **Create modules** in `projects/{name}/src/` directory
2. **Add tests** in `projects/{name}/tests/` directory (coverage requirements apply)
3. **Update scripts** to import and use new `projects/{name}/src/` methods
4. **Validate integration** through the build pipeline

## Troubleshooting

### Common Issues

1. **Missing references**: Check that labels exist and are spelled correctly
2. **Figure not found**: Verify the figure and registry exist in the selected
   project's `output/figures/`
3. **Equation numbering**: Ensure unique labels across all files
4. **Build failures**: Check markdown validation output
5. **Script import errors**: Ensure `projects/{name}/src/` modules exist and are properly tested

### Reference Shows ??

**Symptom**: `[@sec:label]` shows `??` in PDF

**Solution**: Check label exists - search for `{#sec:label_name}` in manuscript files

### Figure Path Error

**Symptom**: Figure renders but wrong location

**Solution**: Use relative path `../output/figures/name.png` not absolute paths

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
5. **Import errors**: Ensure `projects/{name}/src/` modules meet coverage requirements

## Architecture Compliance

### Thin Orchestrator Pattern — File Structure

This template enforces the **thin orchestrator pattern** where:

- **`projects/{name}/src/`** contains ALL business logic, algorithms, and mathematical implementations
- **`projects/{name}/scripts/`** are lightweight wrappers that import and use `projects/{name}/src/` methods
- **`projects/{name}/tests/`** ensures coverage of `projects/{name}/src/` functionality
- **`scripts/runner/execute_pipeline.py`** orchestrates the declared DAG pipeline

### Script Requirements

Scripts in `projects/{name}/scripts/` MUST:

- Import methods from `projects/{name}/src/` modules
- Use `projects/{name}/src/` methods for all computation
- Handle only I/O, visualization, and orchestration
- Include proper error handling for imports
- Print output paths for render system
- Set `MPLBACKEND=Agg` for headless operation

Scripts MUST NOT:

- Implement mathematical algorithms
- Duplicate business logic from `projects/{name}/src/`
- Contain complex computations
- Define new data structures

## Summary

This template provides a framework for academic writing with:

- **Structured organization** of content into logical sections
- **cross-referencing** system for equations, figures, and sections
- **Automated figure generation** with proper integration using `projects/{name}/src/` methods
- **Validation system** ensuring document integrity
- **Build pipeline** generating both individual and combined PDFs
- **LaTeX export** for further customization
- **Thin orchestrator pattern** ensuring maintainability and testability

The system demonstrates best practices for academic writing while maintaining the flexibility to adapt to different research domains and writing styles, all while enforcing the architectural principles of the generic project template.

For more details on architecture and workflow, see:

- **[`../core/architecture.md`](../core/architecture.md)** - System design overview
- **[`../architecture/two-layer-architecture.md`](../architecture/two-layer-architecture.md)** - two-layer architecture guide
- **[`../core/workflow.md`](../core/workflow.md)** - Development workflow

For manuscript formatting standards, see:

- **[`docs/rules/manuscript_style.md`](../rules/manuscript_style.md)** - manuscript formatting and style guide (equations, figures, tables, citations, lists, cross-references)
