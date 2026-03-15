# API Reference — Project Modules

> **API documentation** for project-specific scientific modules (`projects/{name}/src/`)

**Quick Reference:** [Infrastructure API](api-reference.md) | [Modules Guide](../modules/modules-guide.md) | [Getting Started](../guides/getting-started.md)

This document provides API reference for public functions and classes in `projects/{name}/src/`. These are project-specific (Layer 2) modules — for infrastructure modules, see [api-reference.md](api-reference.md).

---

## Module: example

### Functions

#### `add_numbers(a: float, b: float) -> float`

Add two numbers together.

**Parameters:**

- `a` (float): First number
- `b` (float): Second number

**Returns:** `float` — Sum of a and b

**Example:**

```python
from example import add_numbers
result = add_numbers(3.5, 2.5)  # Returns 6.0
```

---

#### `multiply_numbers(a: float, b: float) -> float`

Multiply two numbers together.

**Parameters:**

- `a` (float): First number
- `b` (float): Second number

**Returns:** `float` — Product of a and b

**Example:**

```python
from example import multiply_numbers
result = multiply_numbers(3.0, 4.0)  # Returns 12.0
```

---

#### `calculate_average(numbers: List[float]) -> Optional[float]`

Calculate the average of a list of numbers.

**Parameters:**

- `numbers` (List[float]): List of numbers to average

**Returns:** `Optional[float]` — Average of the numbers, or None if list is empty

**Example:**

```python
from example import calculate_average
result = calculate_average([1.0, 2.0, 3.0, 4.0])  # Returns 2.5
result = calculate_average([])  # Returns None
```

---

#### `find_maximum(numbers: List[float]) -> Optional[float]`

Find the maximum value in a list of numbers.

**Parameters:**

- `numbers` (List[float]): List of numbers to search

**Returns:** `Optional[float]` — Maximum value, or None if list is empty

---

#### `find_minimum(numbers: List[float]) -> Optional[float]`

Find the minimum value in a list of numbers.

**Parameters:**

- `numbers` (List[float]): List of numbers to search

**Returns:** `Optional[float]` — Minimum value, or None if list is empty

---

#### `is_even(number: int) -> bool`

Check if a number is even.

**Returns:** `bool` — True if number is even, False otherwise

---

#### `is_odd(number: int) -> bool`

Check if a number is odd.

**Returns:** `bool` — True if number is odd, False otherwise

---

## Module: data_generator

Synthetic data generation with configurable distributions.

### Functions

#### `generate_synthetic_data(n_samples: int, n_features: int = 1, distribution: str = "normal", seed: Optional[int] = None, **kwargs) -> np.ndarray`

Generate synthetic data with specified distribution.

**Parameters:**

- `n_samples` (int): Number of samples
- `n_features` (int): Number of features (default: 1)
- `distribution` (str): Distribution type (normal, uniform, exponential, poisson, beta)
- `seed` (Optional[int]): Random seed
- `**kwargs`: Distribution-specific parameters

**Returns:** `np.ndarray` — Array of generated data

**Example:**

```python
from data_generator import generate_synthetic_data
data = generate_synthetic_data(100, n_features=2, distribution="normal", mean=0.0, std=1.0)
```

---

## Module: statistics

Statistical analysis including descriptive statistics, hypothesis testing, and correlation analysis.

### Functions

#### `calculate_descriptive_stats(data: np.ndarray) -> DescriptiveStats`

Calculate descriptive statistics for a dataset.

**Returns:** `DescriptiveStats` — Object with mean, std, median, min, max, quartiles, count

**Example:**

```python
from statistics import calculate_descriptive_stats
stats = calculate_descriptive_stats(data)
print(f"Mean: {stats.mean}, Std: {stats.std}")
```

---

## Module: visualization

Publication-quality figure generation with consistent styling.

### Classes

#### `VisualizationEngine`

Engine for generating publication-quality figures.

**Methods:**

- `create_figure(nrows, ncols, figsize, **kwargs)` - Create figure with subplots
- `save_figure(figure, filename, formats, dpi)` - Save figure in multiple formats
- `apply_publication_style(ax, title, xlabel, ylabel, grid, legend)` - Apply styling

**Example:**

```python
from visualization import VisualizationEngine
engine = VisualizationEngine(style="publication", output_dir="output/figures")
fig, ax = engine.create_figure()
engine.save_figure(fig, "my_figure", formats=["png", "pdf"])
```

---

## Module: figure_manager

Automatic figure numbering, caption generation, and cross-referencing.

### Classes

#### `FigureManager`

Manages figures with automatic numbering and cross-referencing.

**Methods:**

- `register_figure(filename, caption, label, section, ...)` - Register a new figure
- `get_figure(label)` - Get figure metadata by label
- `generate_latex_figure_block(label)` - Generate LaTeX figure block
- `generate_reference(label)` - Generate LaTeX reference

**Example:**

```python
from infrastructure.documentation import FigureManager
manager = FigureManager()
fig_meta = manager.register_figure("convergence.png", "Convergence analysis", "fig:convergence")
latex_block = manager.generate_latex_figure_block("fig:convergence")
```

---

## Additional Modules

For full per-module details, see:

- **[Infrastructure Documentation](../../infrastructure/AGENTS.md)** — Infrastructure module descriptions
- **[Project Source Documentation](../../projects/code_project/src/AGENTS.md)** — Project-specific module descriptions
- **[Scientific Simulation Guide](../modules/scientific-simulation-guide.md)** — Simulation and analysis modules
- **[Visualization Guide](../usage/visualization-guide.md)** — Visualization and figure management

**Key project modules (`projects/{name}/src/`):**

| Module | Purpose |
|--------|---------|
| `data_processing.py` | Data cleaning, normalization, outlier detection |
| `metrics.py` | Performance metrics, convergence metrics, quality metrics |
| `validation.py` | Result validation framework |
| `simulation.py` | Core simulation framework |
| `parameters.py` | Parameter management and sweeps |
| `performance.py` | Convergence and scalability analysis |
| `reporting.py` | Automated report generation |
| `plots.py` | Plot type implementations |

---

**Related Documentation:**

- [Infrastructure API Reference](api-reference.md) — Infrastructure module API docs
- [Modules Guide](../modules/modules-guide.md) — Usage examples
- [Best Practices](../best-practices/best-practices.md) — Usage recommendations
