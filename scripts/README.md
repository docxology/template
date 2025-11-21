# scripts/ - Quick Reference

Thin orchestrator scripts that coordinate src/ modules to generate figures, run analyses, and manage workflows.

## Overview

Scripts in this directory follow the **thin orchestrator pattern**:
- Import and use methods from `src/` for computation
- Handle I/O, visualization, and orchestration
- Demonstrate proper integration patterns
- Are fully testable through `src/` method mocking

## Available Scripts

| Script | Purpose |
|--------|---------|
| `analysis_pipeline.py` | End-to-end analysis orchestration |
| `example_figure.py` | Example figure generation |
| `generate_research_figures.py` | Generate publication-quality research figures |
| `generate_scientific_figures.py` | Generate scientific visualization outputs |
| `scientific_simulation.py` | Run scientific simulation workflows |

## Common Operations

### Running Individual Scripts
```bash
python3 scripts/generate_research_figures.py
python3 scripts/scientific_simulation.py
```

### Running All Scripts
```bash
# Via render_pdf pipeline
./repo_utilities/render_pdf.sh

# Manually (after tests pass)
python3 scripts/*.py
```

### Pattern: Thin Orchestrator Example
```python
# ✅ CORRECT - Thin orchestrator
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scientific.visualization import create_convergence_plot
from infrastructure.figure_manager import register_figure

def main():
    # Orchestrate using src/ functions
    plot = create_convergence_plot(data)
    register_figure('convergence_plot.png', 'Convergence', 'Algorithm convergence')

if __name__ == '__main__':
    main()
```

## Integration with Build Pipeline

Scripts execute in stage 3 of the PDF rendering pipeline:

1. ✅ Clean previous outputs
2. ✅ Run tests (100% coverage)
3. ▶️ **Execute scripts** (this stage)
4. Generate PDFs
5. Validate output

Scripts must:
- Pass all `src/` tests before execution
- Use only `src/` methods for computation
- Generate deterministic outputs
- Register figures with figure manager

## Key Principles

### Thin Orchestrator Pattern
- **Business logic**: All in `src/`
- **Coordination**: In scripts
- **Testing**: `src/` methods are 100% tested
- **Reusability**: Scripts demonstrate patterns, src/ methods are reused

### No Algorithm Duplication
- Don't duplicate algorithms from `src/`
- Don't implement new algorithms in scripts
- Extend `src/` first, then use in scripts

### Deterministic Outputs
- Use fixed random seeds
- Document output generation
- Register generated figures

## Testing Scripts

Scripts are tested through their integration with `src/` modules:

```bash
# Test via src/ method tests
python3 -m pytest tests/ --cov=src

# The coverage includes script behavior through src/ usage
```

## See Also

- [`AGENTS.md`](AGENTS.md) - Complete scripts documentation
- [`../src/README.md`](../src/README.md) - Source code guide
- [`../docs/THIN_ORCHESTRATOR_SUMMARY.md`](../docs/THIN_ORCHESTRATOR_SUMMARY.md) - Pattern details
- [`../.cursorrules/figure_generation.md`](../.cursorrules/figure_generation.md) - Figure generation

