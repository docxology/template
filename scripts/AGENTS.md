# scripts/ - Thin Orchestrator Scripts

## Purpose

This directory contains **thin orchestrator scripts** that coordinate `src/` modules to generate figures, run analyses, and manage workflows. Scripts handle orchestration, I/O, and visualization - all computation logic resides in `src/` modules for testing and reusability.

## Architectural Role

Scripts follow the **thin orchestrator pattern**:
- Import and use methods from `src/` for ALL computation
- Handle I/O, file management, and visualization
- Coordinate between components
- Demonstrate proper integration patterns
- Are testable through `src/` method usage (no mocks)

## Script Organization

### Core Analysis Scripts

| Script | Purpose | Uses |
|--------|---------|------|
| `analysis_pipeline.py` | End-to-end analysis orchestration | src/scientific modules |
| `example_figure.py` | Basic figure generation example | src/scientific.visualization |
| `generate_research_figures.py` | Publication-quality figure generation | src/scientific, infrastructure |
| `generate_scientific_figures.py` | Scientific output generation | src/scientific modules |
| `scientific_simulation.py` | Scientific simulation workflows | src/scientific.simulation |

## Pattern: Thin Orchestrator

### ✅ CORRECT Pattern

```python
# scripts/generate_research_figures.py
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

# Import from src/ - NOT implementation
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from scientific.visualization import create_convergence_plot
from infrastructure.figure_manager import register_figure

def main():
    """Generate research figures using src/ modules."""
    
    # Use src/ functions for ALL computation
    plot = create_convergence_plot(data)
    
    # Handle I/O and visualization
    fig_path = Path('output/figures/convergence.png')
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    # Register in figure registry
    register_figure(
        filename='convergence.png',
        title='Convergence Analysis',
        description='Algorithm convergence over iterations'
    )
    
    print(f"✅ Generated: {fig_path}")

if __name__ == '__main__':
    main()
```

### ❌ INCORRECT Pattern (Violates Architecture)

```python
# scripts/bad_example.py - DON'T DO THIS
import matplotlib.pyplot as plt
import numpy as np

def main():
    """BAD: Algorithm in script, not reusable, not tested."""
    
    # ❌ Algorithm in script - should be in src/
    data = np.random.randn(100)
    mean = np.sum(data) / len(data)  # ❌ Duplicates src/ logic
    
    # ❌ No coordination with src/ modules
    # ❌ Not testable separately
    # ❌ Not reusable
    
    plt.plot(data)
    plt.savefig('output/convergence.png')

if __name__ == '__main__':
    main()
```

## Integration with Build Pipeline

Scripts execute as **Stage 3** in the PDF rendering pipeline (`repo_utilities/render_pdf.sh`):

```
Stage 1: Clean previous outputs
Stage 2: Run tests (100% coverage required)
▶️ Stage 3: Execute scripts (this stage)
   - scripts/analysis_pipeline.py
   - scripts/generate_research_figures.py
   - scripts/generate_scientific_figures.py
   - scripts/scientific_simulation.py
Stage 4: Generate PDFs from Markdown
Stage 5: Validate all outputs
```

### Pipeline Requirements

Scripts must:
1. ✅ Pass all `src/` tests (100% coverage)
2. ✅ Use ONLY `src/` modules for computation
3. ✅ Generate deterministic outputs (use fixed seeds)
4. ✅ Register generated figures with `infrastructure.figure_manager`
5. ✅ Handle errors gracefully
6. ✅ Provide clear logging/output

## Key Script Implementations

### analysis_pipeline.py

**Purpose:** End-to-end analysis orchestration

```python
# Orchestrates complete analysis workflow
# - Load data via src/ methods
# - Process data
# - Run analysis
# - Generate reports
# - Save results
```

### generate_research_figures.py

**Purpose:** Publication-quality figure generation

```python
# Generates figures for research paper
# - Calls src/visualization modules
# - Registers with infrastructure.figure_manager
# - Ensures deterministic output
# - Optimizes for publication quality
```

### generate_scientific_figures.py

**Purpose:** Scientific output generation

```python
# Generates scientific analysis figures
# - Creates plots and visualizations
# - Saves data files
# - Generates supplementary materials
# - Validates output quality
```

### scientific_simulation.py

**Purpose:** Scientific simulation workflows

```python
# Runs scientific simulations
# - Initializes parameters via src/
# - Runs simulation
# - Collects results
# - Analyzes convergence
```

## Testing

Scripts are tested through integration with `src/` modules:

### Unit Testing `src/` Modules
```bash
# All computation is tested via src/ tests
python3 -m pytest tests/ --cov=src --cov-report=term-missing

# Achieves 100% coverage of src/ code
# Scripts are verified through src/ usage coverage
```

### Integration Testing
```bash
# Test script execution (Stage 3 of pipeline)
./repo_utilities/render_pdf.sh

# Tests that verify:
# - Scripts can import src/ modules
# - Scripts generate expected outputs
# - Figure registration works
# - Output quality meets standards
```

## Best Practices

### 1. Import Organization

```python
import sys
from pathlib import Path

# Standard library imports
import numpy as np
import matplotlib.pyplot as plt

# Add src/ to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import from src/ - ONLY place for computation
from scientific.visualization import create_plot
from infrastructure.figure_manager import register_figure
```

### 2. Error Handling

```python
def main():
    try:
        # Generate output
        result = src_function(data)
        
        # Save result
        save_result(result)
        
        print(f"✅ Success: {output_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
```

### 3. Reproducibility

```python
def main():
    # Set fixed seeds for reproducibility
    np.random.seed(42)
    random.seed(42)
    
    # Generate deterministic output
    result = generate_with_src_functions()
    
    # Document generation parameters
    log_generation_info()
    
    # Save with metadata
    save_with_metadata(result)
```

### 4. Figure Registration

```python
from infrastructure.figure_manager import register_figure

# After saving figure
register_figure(
    filename='convergence_plot.png',
    title='Algorithm Convergence',
    description='Convergence analysis comparing methods',
    section='experimental_results',
    figure_type='convergence'
)
```

## Troubleshooting

### Import Errors

**Problem:** `ImportError: No module named 'scientific'`

**Solution:** Ensure script has:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
```

### Figure Not Registered

**Problem:** Generated figure not included in final PDF

**Solution:** Call `register_figure()` after saving:
```python
from infrastructure.figure_manager import register_figure
register_figure(filename='myplot.png', title='My Plot', ...)
```

### Non-Deterministic Output

**Problem:** Running script twice produces different results

**Solution:** Set fixed random seeds:
```python
import random
np.random.seed(42)
random.seed(42)
```

## Development Workflow

### Adding a New Script

1. **Create file** in `scripts/`
2. **Import from `src/`** - don't implement algorithms
3. **Use thin orchestrator pattern** - handle I/O only
4. **Test via `src/` coverage** - script validated through src/
5. **Register figures** if generating outputs
6. **Document script** - add docstrings and comments
7. **Add to pipeline** - `render_pdf.sh` executes all scripts

### Extending Scripts

```python
# Step 1: Create src/ function first
# src/scientific/analysis.py
def new_analysis(data):
    # Implement computation here
    return result

# Step 2: Use in script
# scripts/myscript.py
from scientific.analysis import new_analysis

def main():
    result = new_analysis(data)  # Use src/ function
    save_result(result)
```

## References

- [`AGENTS.md`](./AGENTS.md) - This file
- [`README.md`](./README.md) - Quick reference
- [`../src/AGENTS.md`](../src/AGENTS.md) - Source code architecture
- [`../docs/THIN_ORCHESTRATOR_SUMMARY.md`](../docs/THIN_ORCHESTRATOR_SUMMARY.md) - Pattern explanation
- [`../.cursorrules/thin_orchestrator.md`](../.cursorrules/thin_orchestrator.md) - Rules and standards
- [`../.cursorrules/figure_generation.md`](../.cursorrules/figure_generation.md) - Figure generation patterns

## Key Takeaway

**Scripts are thin orchestrators:**
- ✅ Import and use `src/` methods
- ✅ Handle I/O and visualization
- ✅ Coordinate components
- ❌ Never implement algorithms
- ❌ Never duplicate business logic

This architecture ensures code is testable, reusable, and maintainable.
