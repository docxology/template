# scripts/ - Analysis Scripts

Thin orchestrators that coordinate Active Inference analysis workflows.

## Quick Start

```bash
# Run analysis pipeline
python3 scripts/analysis_pipeline.py

# Generate quadrant matrix visualizations
python3 scripts/generate_quadrant_matrix.py

# Generate Active Inference concept demonstrations
python3 scripts/generate_active_inference_concepts.py

# View generated outputs
ls -la ../output/figures/
```

## Key Features

- **analysis pipeline** (6-stage workflow)
- **Automated figure generation** (quadrant matrices, concept visualizations)
- **Statistical analysis** (validation and verification)
- **Manuscript integration** (figure registration and cross-referencing)

## Common Commands

### Run Analysis Pipeline
```bash
python3 analysis_pipeline.py
```
Executes 6-stage analysis workflow.

### Generate Specific Visualizations
```bash
python3 generate_quadrant_matrix.py          # 2×2 quadrant matrices
python3 generate_active_inference_concepts.py # Core AI concepts
python3 generate_fep_visualizations.py         # Free Energy Principle
python3 generate_quadrant_examples.py          # Quadrant demonstrations
```

### Insert Figures into Manuscript
```bash
python3 insert_all_figures.py
```
Registers and inserts all generated figures into manuscript sections.

## Architecture

```mermaid
graph TD
    A[analysis_pipeline.py] --> B[Stage 1: Theoretical Demos]
    A --> C[Stage 2: Visualizations]
    A --> D[Stage 3: Statistical Analysis]
    A --> E[Stage 4: Validation]
    A --> F[Stage 5: Reports]
    A --> G[Stage 6: Data Export]
    
    B --> H[src/active_inference.py]
    C --> I[src/visualization.py]
    D --> J[src/statistical_analysis.py]
    E --> K[src/validation.py]
    
    L[generate_quadrant_matrix.py] --> M[src/quadrant_framework.py]
    L --> N[src/visualization.py]
    
    O[insert_all_figures.py] --> P[utils/figure_manager.py]
```

## More Information

See [AGENTS.md](AGENTS.md) for technical documentation.
