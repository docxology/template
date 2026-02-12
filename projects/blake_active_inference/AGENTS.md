# Blake Active Inference Project

## Purpose

Standalone academic research project synthesizing William Blake's visionary epistemology with Karl Friston's Active Inference framework.

## Capabilities

- Generate publication-quality manuscript connecting 18th-century Romantic philosophy with 21st-century computational neuroscience
- Produce 8 graphical abstracts visualizing Blake-Friston conceptual mappings
- Validate Blake quotation sources against scholarly editions
- Render mathematical Active Inference equations in manuscript

## Architecture

### Manuscript Layer (`manuscript/`)

Multi-section academic paper with modular structure:

- **Preamble** - Title page and Thematic Atlas
- **Abstract** - Synthesis thesis
- **Introduction** - Historical framing
- **Related Work** - Prior scholarship
- **Theoretical Foundations** - Active Inference mathematics
- **Synthesis** - Eight thematic correspondences (8 subfiles: `04a`–`04h`)
- **Implications** - Philosophy of mind
- **Conclusion** - Future directions

### Visualization Layer (`src/`)

- `visualization.py` - Graphical abstract generation using matplotlib
- Produces 8 key figures:
  - `fig0_thematic_atlas.png` - Overview of all correspondences
  - `fig1_doors_of_perception.png` - Markov blanket visualization
  - `fig2_fourfold_vision.png` - Hierarchical processing mapping
  - `fig3_perception_action_cycle.png` - Active Inference cycle
  - `fig4_newtons_sleep.png` - Prior dominance visualization
  - `fig5_four_zoas.png` - Factorized generative model
  - `fig6_temporal_horizons.png` - Temporal depth visualization
  - `fig7_collective_jerusalem.png` - Multi-agent coordination

### Testing Layer (`tests/`)

- `test_visualization.py` - Validates figure generation and quality
- `test_manuscript.py` - Validates manuscript structure and consistency

## Key Blake Sources

- *The Marriage of Heaven and Hell* (1790-1793)
- *Jerusalem: The Emanation of the Giant Albion* (1804-1820)
- *Milton: A Poem* (1804-1811)
- Letters to Thomas Butts (1800-1803)
- *A Vision of the Last Judgment* (1810)

## Key Active Inference Sources

- Friston, K. (2010). The free-energy principle: a unified brain theory?
- Parr, T., Pezzulo, G., & Friston, K. J. (2022). Active Inference
- Clark, A. (2016). Surfing Uncertainty

## Conventions

- All Blake quotations include plate/line numbers and scholarly source
- Mathematical equations use LaTeX notation
- Figures saved to `output/figures/` in PNG format
- Tests achieve 90%+ coverage on `src/` modules
- Eight thematic correspondences: Boundary, Vision, States, Imagination, Time, Space, Action, Collectives (including Zoas)

## Entry Points

- `scripts/generate_figures.py` - Generate all visual assets
- `tests/test_visualization.py` - Validate figure generation
- `tests/test_manuscript.py` - Validate manuscript consistency

## Dependencies

- matplotlib >= 3.5.0
- numpy >= 1.21.0
- pytest >= 7.0.0
