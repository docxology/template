# Blake Active Inference Project

This project provides comprehensive documentation and analysis for the academic paper:
**"The Doors of Perception are the Threshold of Prediction: Active Inference and William Blake's Theory of Seeing"**

## Project Purpose

This standalone research project synthesizes William Blake's visionary theory of perception (c. 1790-1827) with Karl Friston's Active Inference framework (2006-present), demonstrating that Blake's poetic epistemology prefigures contemporary predictive processing models of cognition.

## Quick Start

```bash
# From repository root
cd template

# Run tests
uv run pytest projects/blake_active_inference/tests/ -v

# Generate figures only
uv run python projects/blake_active_inference/scripts/generate_figures.py

# Run full pipeline (tests, analysis, PDF)
./run.sh
# or for this project only:
uv run python scripts/execute_pipeline.py --project blake_active_inference
```

## Project Structure

```
blake_active_inference/
├── manuscript/          # Academic paper sections (22 files)
│   ├── config.yaml      # Paper metadata and settings
│   ├── preamble.md      # LaTeX preamble packages
│   ├── references.bib   # Bibliography
│   └── *.md             # Manuscript sections
├── src/                 # Source code for analysis
│   └── visualization.py # 8 graphical abstract generators
├── tests/               # Test suite (53 tests)
│   ├── test_manuscript.py    # Manuscript consistency tests
│   └── test_visualization.py # Figure generation tests
├── scripts/             # Pipeline orchestration
│   └── generate_figures.py
└── output/              # Generated figures and outputs
    └── figures/         # 8 PNG figures

## Configuration

The manuscript metadata is controlled by `manuscript/config.yaml`:
- **Date**: Set `paper.date` (e.g., "February 12, 2026").
- **DOI**: Set `publication.doi`.

**Note on Preamble**: The file `manuscript/preamble.md` contains custom LaTeX setup. If `\date{}` is defined there, it will **override** the date in `config.yaml`. Ensure these are synchronized.
```

## Key Concepts

### Blake's Theory of Vision

- **Doors of Perception**: The interface between finite perception and infinite reality
- **Fourfold Vision**: Hierarchy from sensory input to imaginative integration
- **Newton's Sleep**: Critique of reductive materialism limiting perception

### Active Inference Framework

- **Free Energy Principle**: Organisms minimize prediction error to persist
- **Markov Blankets**: Statistical boundaries defining self/world distinction
- **Generative Models**: Internal models predicting sensory observations

### Eight Thematic Correspondences

1. **Boundary** — Doors of Perception = Markov Blanket
2. **Vision** — Fourfold Vision = Hierarchical Processing
3. **States** — Newton's Sleep = Prior Dominance
4. **Imagination** — Human Existence = Generative Model
5. **Time** — Eternity in Hour = Temporal Horizons
6. **Space** — World in Grain = Spatial Inference
7. **Action** — Cleansing = Free Energy Minimization
8. **Collectives** — Building Jerusalem & Four Zoas = Shared & Factorized Models

## Key Quotations

> "If the doors of perception were cleansed every thing would appear to man as it is, Infinite."
> — William Blake, *The Marriage of Heaven and Hell*, Plate 14

> "May God us keep / From Single vision & Newton's sleep!"
> — William Blake, Letter to Thomas Butts, 1802
