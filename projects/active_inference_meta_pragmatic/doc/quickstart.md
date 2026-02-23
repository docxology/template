# Quickstart Guide

Get started with the Active Inference Meta-Pragmatic framework in five minutes.

## Prerequisites

- Python 3.10 or later
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Installation

```bash
# Navigate to the project
cd projects_archive/active_inference_meta_pragmatic

# Install dependencies with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

## Running Tests

```bash
# Run the full test suite
uv run pytest tests/ -v

# Run with coverage reporting
uv run pytest tests/ --cov=src --cov-report=term

# Run a specific test file
uv run pytest tests/test_active_inference.py -v

# Run a single test function
uv run pytest tests/test_quadrant_framework.py::test_quadrant_definitions -v
```

Coverage target is 95%+. All tests use real data and computations (no mocks).

## Generating Figures

```bash
# Generate the 2x2 quadrant matrix visualization
python scripts/generate_quadrant_matrix.py

# Generate Active Inference concept figures (EFE, perception-action loop)
python scripts/generate_active_inference_concepts.py

# Generate Free Energy Principle diagrams
python scripts/generate_fep_visualizations.py

# Generate quadrant-specific examples
python scripts/generate_quadrant_examples.py

# Insert figures into manuscript
python scripts/insert_all_figures.py
```

Generated figures are saved to `output/figures/`.

## Running the Full Pipeline

From the repository root:

```bash
# Core pipeline (tests, analysis, rendering, validation)
python3 scripts/execute_pipeline.py --project active_inference_meta_pragmatic --core-only

# Interactive menu
./run.sh
```

## Basic Usage

```python
from src.active_inference import ActiveInferenceFramework
from src.generative_models import create_simple_generative_model
import numpy as np

# Create a simple 2-state generative model
model = create_simple_generative_model()

# Initialize the Active Inference framework
framework = ActiveInferenceFramework(model)

# Perform perception as inference
observation = np.array([1.0, 0.0])  # Observed state 0
posterior = framework.perception_as_inference(observation)
print(f"Posterior beliefs: {posterior}")

# Calculate Expected Free Energy for a policy
efe, components = framework.calculate_expected_free_energy(
    posterior_beliefs=posterior,
    policy=np.array([0])  # Single action
)
print(f"EFE: {efe:.4f} (epistemic: {components['epistemic']:.4f}, pragmatic: {components['pragmatic']:.4f})")
```

## Key Concepts

For an accessible introduction to the theoretical foundations (Active Inference, Free Energy Principle, generative models, the 2x2 framework), see [doc/theoretical_primer.md](theoretical_primer.md).

## Project Structure

```
active_inference_meta_pragmatic/
├── src/                    # Source modules (11 files in 4 subpackages + utils)
│   ├── core/               # active_inference, free_energy_principle, generative_models
│   ├── framework/          # quadrant_framework, meta_cognition, modeler_perspective, cognitive_security
│   ├── analysis/           # data_generator, statistical_analysis, validation
│   └── visualization/      # visualization engine
├── tests/                  # Test suite (~17 test files, 95%+ coverage)
├── scripts/                # Analysis workflows (thin orchestrators)
├── manuscript/             # Research manuscript sections
├── doc/                    # Documentation
│   ├── architecture.md     # System architecture and design decisions
│   ├── api_reference.md    # Comprehensive API reference
│   ├── theoretical_primer.md  # Accessible theoretical introduction
│   └── quickstart.md       # This file
├── output/                 # Generated outputs (figures, data, reports)
├── utils/                  # Shared utilities (logging, exceptions, figure_manager)
├── pyproject.toml          # Project configuration
├── README.md               # Project overview
├── AGENTS.md               # Technical documentation
└── PAI.md                  # PAI integration context
```

## Next Steps

- Read the [API Reference](api_reference.md) for detailed class and method documentation
- Explore the [Architecture Guide](architecture.md) for design decisions and data flow
- Review the manuscript in `manuscript/` for the full theoretical treatment
- Run `python scripts/analysis_pipeline.py` for the complete analysis workflow
