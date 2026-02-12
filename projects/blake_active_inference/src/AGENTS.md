# Source Code - Blake Active Inference

## Purpose

Core visualization module for graphical abstract generation.

## Module: `visualization.py`

Generates 8 publication-quality figures illustrating Blake-Active Inference correspondences.

## Conventions

- Colorblind-safe IBM palette
- Minimum 16pt font size
- 300 DPI output resolution
- No unicode subscripts (LaTeX safe)

## Key Functions

- `generate_all_figures(output_dir)` - Batch generate all figures
- `create_thematic_atlas()` - Eight-theme overview
- Individual figure creators for each theme

## Entry Point

```python
from visualization import generate_all_figures
generate_all_figures(Path("output/figures"))
```
