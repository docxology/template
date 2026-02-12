# Scripts - Blake Active Inference

## Purpose

Pipeline orchestration scripts for figure generation.

## Available Scripts

### `generate_figures.py`

Generates all 8 publication-quality figures.

**Usage:**

```bash
uv run python projects/blake_active_inference/scripts/generate_figures.py [output_dir]
```

**Outputs:**

- `fig0_thematic_atlas.png` - Eight-theme overview
- `fig1_doors_of_perception.png` - Markov blanket
- `fig2_fourfold_vision.png` - Hierarchical processing
- `fig3_perception_action_cycle.png` - Active Inference cycle
- `fig4_newtons_sleep.png` - Prior dominance
- `fig5_four_zoas.png` - Factorized model
- `fig6_temporal_horizons.png` - Temporal prediction
- `fig7_collective_jerusalem.png` - Multi-agent coordination

## Entry Point

```bash
uv run python scripts/execute_pipeline.py --project blake_active_inference
```
