# Analysis Scripts Documentation

## Overview

This directory contains thin orchestrator scripts that implement the analysis pipeline for the Active Inference meta-pragmatic framework. Following the thin orchestrator pattern, these scripts contain **no business logic** - all computational work is performed by modules in the `src/` directory.

## Thin Orchestrator Pattern

### Core Principle
**CRITICAL**: All business logic resides in `src/` modules. Scripts are **thin orchestrators** that:

- Import computation methods from `src/` modules
- Handle I/O operations (file reading/writing, data loading/saving)
- Coordinate workflow execution
- Manage configuration and parameters
- Provide user interface and progress reporting

### Implementation Standard
```python
# CORRECT: Thin orchestrator pattern
from src.active_inference import ActiveInferenceFramework
from src.generative_models import create_simple_generative_model

def main():
    # Setup
    model = create_simple_generative_model()  # Business logic in src/
    framework = ActiveInferenceFramework(model)  # Business logic in src/

    # Orchestration
    results = framework.calculate_expected_free_energy(data)  # Computation in src/

    # I/O
    save_results(results, output_file)  # I/O in script

# INCORRECT: Business logic in script
def main():
    # Never implement algorithms in scripts
    efe = calculate_efe_here(data)  # Wrong!
```

## Pipeline Architecture

### Analysis Pipeline (`analysis_pipeline.py`)

**Purpose**: Orchestrates the analysis workflow with 6 stages

**Stages**:
1. **Theoretical Demonstrations**: Generate concept demonstrations using `src/` modules
2. **Visualization Generation**: Create figures using `VisualizationEngine`
3. **Statistical Analysis**: Perform analysis using `StatisticalAnalyzer`
4. **Validation & Verification**: Validate results using `ValidationFramework`
5. **Report Generation**: Create reports using local utilities
6. **Data Export**: Export results in various formats

**Key Features**:
- Modular stage execution
- Progress tracking and error handling
- logging
- Output organization
- Cross-stage data flow

### Visualization Scripts

#### `generate_quadrant_matrix.py`
**Purpose**: Create 2×2 quadrant matrix visualizations
**Imports**:
- `QuadrantFramework` from `src/`
- `VisualizationEngine` from `src/`
- `FigureManager` from utils

**Outputs**:
- `quadrant_matrix.png/pdf`: Basic matrix diagram
- `quadrant_matrix_enhanced.png/pdf`: Detailed quadrant descriptions

#### `generate_active_inference_concepts.py`
**Purpose**: Visualize core Active Inference concepts
**Imports**:
- `active_inference` and `generative_models` from `src/`
- `VisualizationEngine` from `src/`

**Outputs**:
- `efe_decomposition.png/pdf`: EFE component breakdown
- `perception_action_loop.png/pdf`: AI cycle
- `generative_model_structure.png/pdf`: A, B, C, D matrix relationships
- `meta_level_concepts.png/pdf`: Meta-epistemic/pragmatic concepts

#### `generate_fep_visualizations.py`
**Purpose**: Create Free Energy Principle visualizations
**Imports**:
- `FreeEnergyPrinciple` from `src/`
- `VisualizationEngine` from `src/`

**Outputs**:
- `fep_system_boundaries.png/pdf`: Markov blanket visualization
- `free_energy_dynamics.png/pdf`: Minimization trajectories
- `structure_preservation.png/pdf`: System organization maintenance
- `physics_cognition_bridge.png/pdf`: Domain integration

#### `generate_quadrant_examples.py`
**Purpose**: Demonstrate specific quadrant examples
**Imports**:
- Multiple modules from `src/` (AI, meta-cognition, etc.)
- `VisualizationEngine` from `src/`

**Outputs**:
- `quadrant_1_data_cognitive.png/pdf`: Basic EFE processing
- `quadrant_2_metadata_cognitive.png/pdf`: Meta-data processing
- `quadrant_3_data_metacognitive.png/pdf`: Self-reflective processing
- `quadrant_4_metadata_metacognitive.png/pdf`: Higher-order reasoning

## Script Structure Standards

### Standard Script Template
```python
#!/usr/bin/env python3
"""Script description."""

import sys
from pathlib import Path

# Path setup
project_root = Path(__file__).parent.parent
repo_root = project_root.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(repo_root))

# Local imports
from src.utils.logging import get_logger
from src.utils.figure_manager import FigureManager

# Domain imports from src/
from src.module import ClassName

logger = get_logger(__name__)

def main() -> None:
    """Main execution function."""
    logger.info("Starting script execution...")

    # Setup output directories
    output_dir = project_root / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize components
    domain_object = ClassName()
    viz_engine = VisualizationEngine(output_dir=str(output_dir))
    figure_manager = FigureManager()

    # Execute analysis (business logic in src/)
    results = domain_object.analyze_data(data)

    # Create visualizations
    fig = viz_engine.create_visualization(results)
    saved = viz_engine.save_figure(fig, "output_name")

    # Register for cross-referencing
    figure_manager.register_figure(
        filename="output_name.png",
        caption="Figure description for manuscript",
        section="manuscript_section",
        generated_by="script_name.py"
    )

    logger.info("Script execution completed")

if __name__ == "__main__":
    main()
```

## Configuration and Parameters

### Path Management
```python
# Standard path setup
project_root = Path(__file__).parent.parent  # scripts/ -> project/
repo_root = project_root.parent             # project/ -> repository root
src_path = project_root / "src"
infrastructure_path = repo_root

sys.path.insert(0, str(src_path))
sys.path.insert(0, str(infrastructure_path))
```

### Output Organization
```python
# Standard output structure
output_base = project_root / "output"
figures_dir = output_base / "figures"
data_dir = output_base / "data"
reports_dir = output_base / "reports"

# Create directories
for dir_path in [figures_dir, data_dir, reports_dir]:
    dir_path.mkdir(parents=True, exist_ok=True)
```

## Error Handling and Logging

### Logging Integration
```python
logger = get_logger(__name__)

def main():
    try:
        logger.info("Starting execution...")
        # Execution logic
        logger.info("Execution completed successfully")
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        raise
```

### Progress Reporting
```python
from infrastructure.core.logging_utils import log_substep

def multi_step_process():
    log_substep("Step 1: Data preparation")
    # Step 1 logic

    log_substep("Step 2: Analysis execution")
    # Step 2 logic

    log_substep("Step 3: Result visualization")
    # Step 3 logic
```

## Figure Management Integration

### Figure Registration
```python
# Register figures for manuscript cross-referencing
fig_meta = figure_manager.register_figure(
    filename="figure_name.png",
    caption="figure caption for manuscript",
    section="methodology",  # or "experimental_results", etc.
    generated_by="script_name.py",
    parameters={"key": "value"}  # Optional metadata
)

logger.info(f"Registered figure: {fig_meta.label}")
```

### Cross-Reference Labels
Figures are automatically assigned labels like `fig:figure_name` for use in manuscript:
```latex
\\ref{fig:quadrant_matrix}
```

## Testing Integration

### Script Testing Strategy
Since scripts follow thin orchestrator pattern, testing focuses on:
- Correct import and initialization
- Proper data flow coordination
- Error handling and logging
- Output file generation
- Figure registration

### Test Example
```python
def test_script_execution():
    """Test script executes without errors."""
    # Setup test environment
    # Run script
    # Validate outputs exist
    # Check figures registered
    # Verify log messages
```

## Performance and Scalability

### Execution Time Monitoring
```python
from infrastructure.core.performance import PerformanceMonitor

perf_monitor = PerformanceMonitor()

def main():
    perf_monitor.start_stage("script_execution")

    # Execution logic

    perf_monitor.end_stage("script_execution")
    logger.info(f"Performance: {perf_monitor.get_summary()}")
```

### Memory Management
- Process large datasets in chunks
- Clean up intermediate results
- Use efficient data structures
- Monitor memory usage for large models

## Maintenance Guidelines

### Adding New Scripts
1. Follow thin orchestrator pattern strictly
2. Use established path setup and imports
3. Include logging and error handling
4. Register all generated figures
5. Add appropriate tests
6. Update this documentation

### Modifying Existing Scripts
1. Preserve thin orchestrator pattern
2. Maintain backward compatibility
3. Update logging and error messages
4. Verify figure registration still works
5. Update dependent tests

### Script Quality Standards
- **No Business Logic**: All algorithms in `src/` modules
- **Logging**: Progress and error reporting
- **Error Handling**: Graceful failure with informative messages
- **Documentation**: Clear docstrings and comments
- **Testing**: Integration tests for orchestration logic

## Execution Methods

### Direct Execution
```bash
# From template root (recommended)
python projects/active_inference_meta_pragmatic/scripts/script_name.py

# From project directory
cd projects/active_inference_meta_pragmatic
python scripts/script_name.py
```

### Pipeline Integration
```bash
# Run specific stages
python projects/active_inference_meta_pragmatic/scripts/analysis_pipeline.py --stages 2

# Run pipeline
python projects/active_inference_meta_pragmatic/scripts/analysis_pipeline.py
```

### IDE Integration
Scripts can be executed directly from IDEs with proper working directory setup pointing to the template root.

This scripts directory provides a clean separation between orchestration (scripts) and computation (src/), enabling modular development, testing, and maintenance of the Active Inference meta-pragmatic framework analysis pipeline.