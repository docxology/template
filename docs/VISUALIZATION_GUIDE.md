# Visualization Guide

## Overview

This guide covers the visualization system for generating publication-quality figures with automatic management and integration.

## Visualization Engine

The `VisualizationEngine` class provides consistent styling and export capabilities:

```python
from visualization import VisualizationEngine

engine = VisualizationEngine(
    style="publication",
    color_palette="default",
    output_dir="output/figures"
)
```

### Style Presets

- **publication**: High-quality figures for papers
- **presentation**: Optimized for slides
- **draft**: Quick previews

### Color Palettes

- **default**: Standard matplotlib colors
- **colorblind**: Colorblind-friendly palette
- **grayscale**: Grayscale for printing

## Plot Types

### Line Plots

```python
from plots import plot_line

ax = plot_line(x, y, label="Data", color="#1f77b4")
```

### Scatter Plots

```python
from plots import plot_scatter

ax = plot_scatter(x, y, alpha=0.6, size=50)
```

### Bar Charts

```python
from plots import plot_bar

ax = plot_bar(categories, values, color="#2ca02c")
```

### Convergence Plots

```python
from plots import plot_convergence

ax = plot_convergence(iterations, values, target=0.0)
```

## Figure Management

### Registering Figures

```python
from figure_manager import FigureManager

manager = FigureManager()
fig_meta = manager.register_figure(
    filename="convergence.png",
    caption="Convergence analysis showing exponential decay",
    section="experimental_results",
    generated_by="my_script.py"
)
```

### Generating LaTeX Blocks

```python
latex_block = manager.generate_latex_figure_block("fig:convergence")
```

### Cross-References

```python
ref = manager.generate_reference("fig:convergence")
# Returns: \ref{fig:convergence}
```

## Best Practices

1. **Use consistent styling** - Apply publication style to all figures
2. **Register all figures** - Use FigureManager for tracking
3. **Generate captions** - Provide descriptive captions
4. **Use appropriate formats** - PNG for manuscripts, PDF for presentations
5. **Validate figures** - Check file existence and paths

