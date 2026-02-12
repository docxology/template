# Scripts Documentation

## Purpose

This directory contains orchestration scripts for the Blake Active Inference project.

## Available Scripts

### `generate_figures.py`

Generates all 8 publication-quality graphical abstracts.

**Usage:**

```bash
# From repository root
uv run python projects/blake_active_inference/scripts/generate_figures.py [output_dir]
```

**Outputs (saved to `output/figures/`):**

| Figure | Description |
|--------|-------------|
| `fig0_thematic_atlas.png` | Overview of all eight thematic correspondences |
| `fig1_doors_of_perception.png` | Markov blanket as perceptual interface |
| `fig2_fourfold_vision.png` | Blake/Active Inference hierarchy mapping |
| `fig3_perception_action_cycle.png` | Circular inference diagram with Blake quotes |
| `fig4_newtons_sleep.png` | Prior dominance visualization |
| `fig5_four_zoas.png` | Factorized generative model |
| `fig6_temporal_horizons.png` | Temporal depth and prediction |
| `fig7_collective_jerusalem.png` | Multi-agent shared generative models |

## Running from Repository Root

```bash
# Generate figures
uv run python projects/blake_active_inference/scripts/generate_figures.py

# Run tests first to validate
uv run pytest projects/blake_active_inference/tests/test_visualization.py -v

# Full pipeline (includes figure generation)
./run.sh
```
