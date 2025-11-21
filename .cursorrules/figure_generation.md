# Figure Generation Patterns

## Thin Orchestrator for Figures

Figure generation scripts follow the thin orchestrator pattern strictly:

- **src/**: Contains plot functions, data analysis, visualization logic
- **scripts/**: Orchestrates figure creation, handles I/O, coordinates components

## Figure Script Structure

### ✅ Correct Pattern

```python
# scripts/generate_research_figures.py

import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

# Import from src/ - NOT implementation code
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from visualization import create_convergence_plot
from data_processing import load_and_process
from figure_manager import register_figure

def main():
    """Generate research figures using src/ modules."""
    
    # Use src/ functions for all logic
    data = load_and_process('input/data.csv')
    
    # Orchestrate figure creation
    print("Generating convergence plot...")
    fig = create_convergence_plot(data)
    
    # Save figure
    fig_path = Path('output/figures/convergence_plot.png')
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    # Register in figure registry
    register_figure(
        filename='convergence_plot.png',
        title='Convergence Analysis',
        description='Algorithm convergence over iterations',
        section='experimental_results'
    )
    
    print(f"✅ Saved: {fig_path}")

if __name__ == '__main__':
    main()
```

### ❌ Incorrect Pattern

```python
# scripts/generate_research_figures.py - BAD

import matplotlib.pyplot as plt

def main():
    """BAD: Algorithm in script, not reusable."""
    
    # Don't do this - algorithm in script!
    data = np.random.randn(100)
    convergence = []
    
    for i in range(100):
        # Algorithm here (should be in src/)
        value = compute_convergence_step(data[i])
        convergence.append(value)
    
    plt.plot(convergence)
    plt.savefig('output/figures/convergence.png')
```

## Figure Output Standards

### PNG Output
```python
# Save with consistent settings
plt.savefig(
    'output/figures/figure_name.png',
    dpi=300,           # High resolution
    bbox_inches='tight' # Remove whitespace
)

# Typical size: 10x6 inches at 100 DPI display resolution
fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
```

### PDF Output (Vector Format)
```python
# For embedding in LaTeX
plt.savefig(
    'output/figures/figure_name.pdf',
    format='pdf',
    bbox_inches='tight'
)
```

### Reproducibility
```python
# Always set random seed
np.random.seed(42)
random.seed(42)

# Deterministic matplotlib backend
import matplotlib
matplotlib.use('Agg')

# Reproducible output
plt.rcParams['figure.dpi'] = 100
plt.rcParams['savefig.dpi'] = 300
```

## Figure Registration

### Registration Pattern
```python
from figure_manager import register_figure

# Immediately after saving
fig.savefig('output/figures/my_plot.png', dpi=300)
register_figure(
    filename='my_plot.png',
    title='My Plot Title',
    description='Detailed description of what the plot shows',
    section='experimental_results'  # Which manuscript section
)
```

### Registry Data Structure
```json
{
  "figures": {
    "fig:my_plot": {
      "file": "my_plot.png",
      "title": "My Plot Title",
      "description": "Detailed description",
      "section": "experimental_results",
      "label": "fig:my_plot"
    }
  },
  "metadata": {
    "generated": "2025-11-21T09:08:51",
    "total_figures": 16
  }
}
```

## Data and Figure Pairing

Always generate both data and figure together:

```python
def generate_convergence_analysis():
    """Generate convergence figure and data."""
    
    # Compute data
    from src.analysis import compute_convergence
    convergence = compute_convergence(algorithm_params)
    
    # Save data
    np.savez(
        'output/data/convergence_data.npz',
        convergence=convergence
    )
    
    # Create and save figure
    from src.visualization import create_convergence_plot
    fig = create_convergence_plot(convergence)
    plt.savefig('output/figures/convergence_plot.png', dpi=300)
    plt.close()
    
    # Register both
    register_figure(
        filename='convergence_plot.png',
        title='Convergence Analysis',
        description='Algorithm convergence from analysis',
        section='experimental_results'
    )
    
    print("✅ Generated convergence_plot.png")
    print("✅ Generated convergence_data.npz")
```

## Styling and Formatting

### Consistent Style
```python
def setup_plot_style():
    """Configure consistent styling for all figures."""
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['figure.figsize'] = (10, 6)
    
    # Colorblind-friendly palette
    plt.rcParams['axes.prop_cycle'] = plt.cycler(
        color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    )

# Use in every figure script
setup_plot_style()
```

### Labeling
```python
def create_labeled_plot(data, title):
    """Create properly labeled plot."""
    fig, ax = plt.subplots()
    
    ax.plot(data, linewidth=2, label='Data')
    ax.set_xlabel('Iteration', fontsize=12)
    ax.set_ylabel('Value', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig
```

## Multiple Figure Generation

```python
def main():
    """Generate multiple figures."""
    
    from src.data_processing import load_dataset
    from src.visualization import (
        create_convergence_plot,
        create_comparison_plot,
        create_distribution_plot
    )
    
    # Load data once
    data = load_dataset('input/data.csv')
    
    # Generate figures
    figures = {
        'convergence_plot.png': create_convergence_plot(data),
        'comparison_plot.png': create_comparison_plot(data),
        'distribution_plot.png': create_distribution_plot(data),
    }
    
    # Save all
    for filename, fig in figures.items():
        path = Path('output/figures') / filename
        plt.savefig(path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Register
        register_figure(
            filename=filename,
            title=filename.replace('.png', '').replace('_', ' ').title(),
            description=f'Analysis: {filename}',
            section='experimental_results'
        )
        
        print(f"✅ {filename}")
```

## Error Handling

```python
def save_figure_safely(fig, filename, title):
    """Save figure with error handling."""
    try:
        path = Path('output/figures') / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        
        fig.savefig(path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        # Register
        register_figure(
            filename=filename,
            title=title,
            description=title,
            section='experimental_results'
        )
        
        print(f"✅ Saved: {path}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving {filename}: {e}")
        return False
```

## Testing Figure Scripts

Test through `src/` functions:

```python
# tests/test_visualization.py

def test_convergence_plot_creation():
    """Test that convergence plot creates valid figure."""
    from src.visualization import create_convergence_plot
    import numpy as np
    
    # Create test data
    convergence = np.array([1.0, 0.5, 0.1, 0.01, 0.001])
    
    # Create figure
    fig = create_convergence_plot(convergence)
    
    # Verify figure is valid
    assert fig is not None
    assert len(fig.axes) > 0
    assert len(fig.axes[0].lines) > 0
```

## Common Issues and Solutions

### Figures Blurry in PDF
```python
# Save with higher DPI
plt.savefig('output/figures/plot.pdf', dpi=600)
```

### Missing Fonts in LaTeX
```python
# Use standard fonts that work everywhere
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
```

### Unresolved References in PDF
```bash
# Ensure figure is registered
register_figure(filename='plot.png', ...)

# Check registry file exists
ls output/figures/figure_registry.json

# Recompile PDFs multiple times
xelatex document.tex  # 3+ times
```

## Checklist for Figure Generation

- [ ] Script imports from `src/` for all logic
- [ ] Figures saved with dpi=300 (high quality)
- [ ] Random seeds set for reproducibility
- [ ] Figures registered immediately after saving
- [ ] Data saved alongside figures
- [ ] Labels and title included on plots
- [ ] Output paths printed to stdout
- [ ] Error handling for missing files
- [ ] Tested through `src/` module tests
- [ ] Documentation includes figure examples

## See Also

- [thin_orchestrator.md](thin_orchestrator.md) - Script pattern details
- [source_code_standards.md](source_code_standards.md) - Code quality
- [../scripts/AGENTS.md](../scripts/AGENTS.md) - Scripts documentation
- [../src/figure_manager.py](../src/figure_manager.py) - Figure registry implementation

