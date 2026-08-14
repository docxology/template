# Visualization Guide

## Overview

This guide covers the supported pattern for producing source-bound,
publication figures. Plotting code is project-owned; there is no generic
`VisualizationEngine` or `plot_line` API in the canonical exemplar.

## Canonical pattern

1. Compute values in tested `projects/<qualified-name>/src/` functions.
2. Use a thin analysis script to draw and save the figure under the project's
   `output/figures/` directory.
3. Declare the label, filename, visible caption, generator, and concise alt
   text in a project-owned figure specification.
4. Publish a fail-closed `figure_registry.json` with
   `publish_generated_figures()` or `write_generated_figure_registry()`.
5. Reference the figure in manuscript source with Pandoc image syntax and
   `[@fig:label]`.

```python
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from infrastructure.documentation import write_generated_figure_registry


@dataclass(frozen=True)
class FigureSpec:
    label: str
    filename: str
    caption: str
    generated_by: str
    alt_text: str


output_dir = Path("projects/templates/template_code_project/output/figures")
output_dir.mkdir(parents=True, exist_ok=True)
figure_path = output_dir / "convergence.png"

# `iterations` and `objective_values` must come from tested project analysis.
fig, ax = plt.subplots()
ax.plot(iterations, objective_values, marker="o", label="Objective")
ax.set(xlabel="Iteration", ylabel="Objective value")
ax.legend()
fig.savefig(figure_path, dpi=300, bbox_inches="tight")
plt.close(fig)

spec = FigureSpec(
    label="fig:convergence",
    filename=figure_path.name,
    caption="Objective value by optimization iteration.",
    generated_by="scripts.optimization_analysis:main",
    alt_text="Line plot in which the objective decreases across iterations.",
)
write_generated_figure_registry(
    output_dir / "figure_registry.json",
    [spec],
    [figure_path],
    schema_version="1.0",
)
```

Use the same analysis outputs to inject any changing statistics into the
caption or nearby prose. Do not copy numbers from a plot into manuscript text.

## Legacy figure management

`FigureManager` is a real infrastructure utility, but it emits raw LaTeX and
is not wired into the default Pandoc manuscript workflow. Retain it only for a
legacy integration that explicitly requires those outputs.

### Registering figures

```python
from infrastructure.documentation import FigureManager

manager = FigureManager()
fig_meta = manager.register_figure(
    filename="convergence.png",
    caption="Convergence analysis showing exponential decay",
    section="experimental_results",
    generated_by="my_script.py"
)
```

### Generating LaTeX blocks

```python
latex_block = manager.generate_latex_figure_block("fig:convergence")
```

### Cross-references

```python
ref = manager.generate_reference("fig:convergence")
# Returns: \ref{fig:convergence}
```

**Caveat:** `FigureManager.generate_reference()` and `generate_latex_figure_block()`
emit raw LaTeX (`\ref{}`, `\begin{figure}`), not the Pandoc bracket-cite
syntax (`[@fig:name]`, `![caption](path){#fig:name}`) that the actual render
pipeline and every exemplar manuscript use (see
[Manuscript Semantics](../guides/manuscript-semantics.md)). This utility is
not wired into the default pipeline — do not use its output directly in
manuscript source; write `[@fig:name]` and `![...](path){#fig:name}` by hand
instead.

## Scientific and accessibility checks

- State the population, denominator, units, uncertainty definition, and
  statistical comparison represented by the plot.
- Bind plotted values, annotations, captions, and manuscript statistics to the
  same canonical analysis output.
- Use colorblind-considerate palettes and redundant encodings such as marker
  shape, line style, or direct labels; verify grayscale and contrast.
- Keep the visible caption and concise alt text distinct. For a complex figure,
  add a nearby prose or appendix description of relationships that concise alt
  text cannot convey.
- Inspect fonts, clipping, panel labels, legends, and uncertainty displays at
  final render size in every enabled output format.
- Record the generating function and publish the figure registry only after all
  declared files exist.

See [Manuscript Semantics](../guides/manuscript-semantics.md) for the canonical
authoring and accessibility contract.
