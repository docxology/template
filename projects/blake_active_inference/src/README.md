# Source Code - Blake Active Inference

## Purpose

Core visualization module for generating publication-quality graphical abstracts that illustrate the Blake-Active Inference correspondences.

## Modules

### `visualization.py`

Main visualization module containing figure generation functions for all 8 graphical abstracts.

**Key Functions:**

| Function | Output | Description |
|----------|--------|-------------|
| `create_thematic_atlas()` | `fig0_thematic_atlas.png` | Overview of all eight correspondences |
| `create_doors_of_perception()` | `fig1_doors_of_perception.png` | Markov blanket boundary visualization |
| `create_fourfold_vision()` | `fig2_fourfold_vision.png` | Hierarchical processing levels |
| `create_perception_action_cycle()` | `fig3_perception_action_cycle.png` | Active Inference cycle |
| `create_newtons_sleep()` | `fig4_newtons_sleep.png` | Prior dominance illustration |
| `create_four_zoas()` | `fig5_four_zoas.png` | Factorized model structure |
| `create_temporal_horizons()` | `fig6_temporal_horizons.png` | Temporal prediction depth |
| `create_collective_jerusalem()` | `fig7_collective_jerusalem.png` | Multi-agent coordination |
| `generate_all_figures()` | All 8 figures | Convenience function for batch generation |

**Design Principles:**

- Colorblind-safe palette (IBM Design)
- Minimum 16pt font size for accessibility
- 300 DPI resolution for publication
- No unicode subscripts (LaTeX compatibility)

## Dependencies

- matplotlib >= 3.5.0
- numpy >= 1.21.0

## Usage

```python
from visualization import generate_all_figures
from pathlib import Path

output_dir = Path("output/figures")
figures = generate_all_figures(output_dir)
```
