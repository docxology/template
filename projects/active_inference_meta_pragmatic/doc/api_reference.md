# API Reference

This document provides a comprehensive reference for all public classes and methods in the Active Inference Meta-Pragmatic framework.

---

## Core Package

### ActiveInferenceFramework

**Module**: `src/core/active_inference.py`

Core Active Inference implementation with Expected Free Energy calculations, policy selection, and perception as inference.

**Constructor**:

```python
ActiveInferenceFramework(
    generative_model: Union[Dict[str, NDArray], GenerativeModel],
    precision: float = 1.0
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `generative_model` | `Dict[str, NDArray]` or `GenerativeModel` | Dictionary with A, B, C, D matrices or a `GenerativeModel` instance |
| `precision` | `float` | Precision parameter for EFE calculations (default: 1.0) |

**Attributes**: `n_states`, `n_observations`, `n_actions`, `generative_model`, `precision`

**Key Methods**:

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `calculate_expected_free_energy` | `posterior_beliefs: NDArray, policy: NDArray, observations: Optional[NDArray]` | `Tuple[float, Dict[str, float]]` | Compute EFE decomposed into epistemic and pragmatic components |
| `select_optimal_policy` | `candidate_policies: List[NDArray]` | `Tuple[NDArray, Dict]` | Select policy minimizing EFE across candidates |
| `perception_as_inference` | `observations: NDArray` | `NDArray` | Bayesian perception: update beliefs from observations |

**Usage**:

```python
from src.active_inference import ActiveInferenceFramework
import numpy as np

model = {"A": np.array([[0.8, 0.2], [0.2, 0.8]]),
         "B": np.array([[[0.9, 0.1], [0.1, 0.9]]]),
         "C": np.array([1.0, -1.0]),
         "D": np.array([0.5, 0.5])}
framework = ActiveInferenceFramework(model)
efe, components = framework.calculate_expected_free_energy(np.array([0.6, 0.4]), np.array([0]))
```

---

### FreeEnergyPrinciple

**Module**: `src/core/free_energy_principle.py`

Implementation of Free Energy Principle concepts including variational free energy, Markov blankets, and structure preservation dynamics.

**Constructor**:

```python
FreeEnergyPrinciple(
    system_states: Dict[str, NDArray],
    precision: float = 1.0
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `system_states` | `Dict[str, NDArray]` | Dictionary with keys `"internal"`, `"external"`, `"sensory"` mapping to state arrays |
| `precision` | `float` | Precision parameter for free energy calculations (default: 1.0) |

**Key Methods**:

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `calculate_free_energy` | `observations: NDArray, beliefs: NDArray` | `Tuple[float, Dict[str, float]]` | Compute variational free energy with energy, entropy, and surprise components |
| `define_system_boundary` | (none) | `Dict[str, NDArray]` | Define Markov blanket separating internal from external states |
| `demonstrate_structure_preservation` | `time_steps: int = 100` | `Dict[str, NDArray]` | Simulate structure preservation via free energy minimization over time |

**Usage**:

```python
from src.free_energy_principle import FreeEnergyPrinciple
import numpy as np

states = {"internal": np.array([0.5, 0.3, 0.2]),
          "external": np.array([0.1, 0.9]),
          "sensory": np.array([0.4, 0.6, 0.0])}
fep = FreeEnergyPrinciple(states)
fe, components = fep.calculate_free_energy(states["internal"], states["internal"])
```

---

### GenerativeModel

**Module**: `src/core/generative_models.py`

Probabilistic generative model implementation encoding the A, B, C, D matrices that define an agent's understanding of its world.

**Constructor**:

```python
GenerativeModel(
    A: NDArray,  # [n_observations x n_states]
    B: NDArray,  # [n_states x n_states x n_actions]
    C: NDArray,  # [n_observations]
    D: NDArray   # [n_states]
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `A` | `NDArray` | Observation likelihood matrix P(o\|s), shape `[n_observations, n_states]` |
| `B` | `NDArray` | Transition matrix P(s'\|s,a), shape `[n_states, n_states, n_actions]` |
| `C` | `NDArray` | Preference vector (log priors over observations), shape `[n_observations]` |
| `D` | `NDArray` | Prior beliefs P(s), shape `[n_states]`, must sum to 1.0 |

**Attributes**: `n_states`, `n_observations`, `n_actions`, `A`, `B`, `C`, `D`

**Key Methods**:

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `predict_observations` | `state: Union[int, NDArray]` | `NDArray` | Forward prediction P(o\|s) from hidden state index or distribution |
| `predict_state_transition` | `current_state: Union[int, NDArray], action: int` | `NDArray` | Predict next state distribution P(s'\|s,a) |
| `calculate_preference_likelihood` | `observation: Union[int, NDArray]` | `float` | Compute preference strength exp(C) for an observation |
| `perform_inference` | `observation: NDArray, prior_beliefs: Optional[NDArray]` | `NDArray` | Bayesian inference: posterior = likelihood * prior, normalized |
| `demonstrate_modeler_specifications` | (none) | `Dict` | Show how modeler specifies epistemic, pragmatic, and dynamic aspects |

**Factory Function**: `create_simple_generative_model() -> GenerativeModel` creates a 2-state, 2-observation, 2-action model for demonstrations.

**Usage**:

```python
from src.generative_models import create_simple_generative_model
model = create_simple_generative_model()
predicted_obs = model.predict_observations(0)
next_state = model.predict_state_transition(0, action=1)
```

---

## Framework Package

### QuadrantFramework

**Module**: `src/framework/quadrant_framework.py`

Implementation of the 2x2 quadrant framework organizing cognitive processing along Data/Meta-Data and Cognitive/Meta-Cognitive dimensions.

**Constructor**:

```python
QuadrantFramework()
```

No parameters. Initializes the four quadrant definitions internally.

**Key Methods**:

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `get_quadrant` | `quadrant_id: str` | `Dict` | Get details for a specific quadrant (e.g., `"Q1_data_cognitive"`) |
| `analyze_processing_level` | `data_type: str, cognitive_level: str` | `Dict` | Analyze processing for given data type (`"data"` or `"metadata"`) and level (`"cognitive"` or `"metacognitive"`) |
| `demonstrate_quadrant_transitions` | (none) | `Dict[str, List[Dict]]` | Show developmental, situational, and learning progressions across quadrants |
| `create_quadrant_matrix_visualization` | (none) | `Dict` | Generate data structure for rendering the 2x2 matrix figure |

**Quadrant IDs**: `Q1_data_cognitive`, `Q2_metadata_cognitive`, `Q3_data_metacognitive`, `Q4_metadata_metacognitive`

**Usage**:

```python
from src.quadrant_framework import QuadrantFramework
fw = QuadrantFramework()
analysis = fw.analyze_processing_level("metadata", "metacognitive")
```

---

### MetaCognitiveSystem

**Module**: `src/framework/meta_cognition.py`

Meta-cognitive monitoring and control system implementing confidence assessment, attention allocation, and strategy evaluation.

**Constructor**:

```python
MetaCognitiveSystem(
    confidence_threshold: float = 0.7,
    adaptation_rate: float = 0.1
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `confidence_threshold` | `float` | Threshold below which meta-cognitive intervention is triggered (default: 0.7) |
| `adaptation_rate` | `float` | Rate of meta-cognitive adaptation (default: 0.1) |

**Key Methods**:

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `assess_inference_confidence` | `posterior_beliefs: NDArray, observation_uncertainty: float` | `Dict[str, Union[float, str]]` | Composite confidence score from entropy, max belief, spread, and observation quality |
| `adjust_attention_allocation` | `confidence_assessment: Dict, available_resources: Dict[str, float]` | `Dict[str, float]` | Reallocate cognitive resources based on confidence level |
| `evaluate_strategy_effectiveness` | `strategy_name: str, performance_metrics: Dict[str, float]` | `Dict[str, Union[float, str]]` | Evaluate and rank a cognitive strategy by accuracy, efficiency, adaptability, robustness |
| `implement_meta_cognitive_control` | `current_state: Dict, meta_cognitive_assessment: Dict` | `Dict[str, Union[str, Dict]]` | Implement control actions (attention, strategy, monitoring intensity) based on assessment |

**Usage**:

```python
from src.meta_cognition import MetaCognitiveSystem
import numpy as np

mcs = MetaCognitiveSystem(confidence_threshold=0.7)
assessment = mcs.assess_inference_confidence(np.array([0.6, 0.3, 0.1]), 0.3)
```

---

### ModelerPerspective

**Module**: `src/framework/modeler_perspective.py`

Analysis of the modeler's dual role as architect (designing agent models) and subject (understanding their own cognition through Active Inference).

**Constructor**:

```python
ModelerPerspective()
```

No parameters.

**Key Methods**:

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `specify_epistemic_framework` | `framework_name: str, epistemic_boundaries: Dict[str, Union[str, List]]` | `Dict` | Define an epistemic framework specifying what agents can know |
| `specify_pragmatic_framework` | `framework_name: str, pragmatic_considerations: Dict[str, Union[str, List]]` | `Dict` | Define a pragmatic framework specifying agent goals and values |
| `demonstrate_meta_epistemic_modeling` | (none) | `Dict` | Show how A and D matrices define epistemic boundaries |
| `demonstrate_meta_pragmatic_modeling` | (none) | `Dict` | Show how C matrix defines pragmatic landscapes |
| `analyze_self_reflective_modeling` | (none) | `Dict` | Analyze recursive self-modeling aspects |
| `synthesize_meta_theoretical_perspective` | (none) | `Dict` | Produce complete meta-theoretical synthesis |

**Usage**:

```python
from src.modeler_perspective import ModelerPerspective
mp = ModelerPerspective()
framework = mp.specify_epistemic_framework("scientific",
    {"observation_model": ["sensors"], "prior_knowledge": ["domain_expertise"]})
```

---

### CognitiveSecurityAnalyzer

**Module**: `src/framework/cognitive_security.py`

Analysis of cognitive security implications within the Active Inference framework, including attack surface mapping, parameter drift detection, and framework integrity validation.

**Constructor**:

```python
CognitiveSecurityAnalyzer(
    generative_model: Dict[str, NDArray],
    meta_cognitive_system: Optional[MetaCognitiveSystem] = None
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `generative_model` | `Dict[str, NDArray]` | Generative model with A, B, C, D matrices |
| `meta_cognitive_system` | `MetaCognitiveSystem` or `None` | Optional meta-cognitive system for integrated analysis |

**Key Methods**:

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `analyze_attack_surface` | (none) | `Dict` | Map potential attack vectors across all four quadrants |
| `simulate_parameter_drift` | `matrix_name: str, drift_magnitude: float, n_steps: int` | `Dict` | Simulate gradual parameter corruption and measure impact |
| `detect_anomaly` | `observations: NDArray, expected_distribution: NDArray` | `Dict` | Detect anomalous observations using KL divergence |
| `validate_framework_integrity` | (none) | `Dict` | Comprehensive integrity check across all model components |

**Usage**:

```python
from src.cognitive_security import CognitiveSecurityAnalyzer
analyzer = CognitiveSecurityAnalyzer(model)
surface = analyzer.analyze_attack_surface()
```

---

## Analysis Package

### DataGenerator

**Module**: `src/analysis/data_generator.py`

Synthetic data generation for demonstrations, testing, and algorithm validation with reproducible seeding.

**Constructor**:

```python
DataGenerator(seed: Optional[int] = None)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `seed` | `int` or `None` | Random seed for reproducibility |

**Key Methods**:

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `generate_time_series` | `n_points: int, trend: str, noise_level: float, seasonality: bool, seed: Optional[int]` | `NDArray` | Synthetic time series with configurable trend (`"stationary"`, `"linear"`, `"exponential"`, `"sinusoidal"`) |
| `generate_categorical_observations` | `n_samples: int, n_categories: int, distribution: str` | `NDArray` | Categorical data with `"uniform"`, `"skewed"`, or `"bimodal"` distribution |
| `generate_state_sequences` | `n_sequences: int, sequence_length: int, n_states: int, transition_type: str` | `NDArray` | Hidden state sequences (`"markov"`, `"random"`, `"sticky"`) |
| `generate_observation_matrix` | `n_states: int, n_observations: int, noise_level: float` | `NDArray` | Observation likelihood matrix A |
| `generate_transition_matrix` | `n_states: int, n_actions: int, transition_type: str` | `NDArray` | Transition matrix B (`"controlled"`, `"random"`, `"deterministic"`) |
| `generate_preference_vector` | `n_observations: int, preference_type: str` | `NDArray` | Preference vector C (`"simple"`, `"complex"`, `"neutral"`) |
| `generate_synthetic_dataset` | `n_samples: int, n_features: int, n_classes: int, distribution: str` | `Tuple[NDArray, NDArray]` | Classification dataset with Gaussian clusters |

**Usage**:

```python
from src.data_generator import DataGenerator
gen = DataGenerator(seed=42)
ts = gen.generate_time_series(n_points=100, trend="sinusoidal")
A = gen.generate_observation_matrix(n_states=3, n_observations=4)
```

---

### StatisticalAnalyzer

**Module**: `src/analysis/statistical_analysis.py`

Statistical analysis toolkit for evaluating Active Inference algorithms with hypothesis testing, correlation analysis, and algorithm comparison.

**Constructor**:

```python
StatisticalAnalyzer(alpha: float = 0.05)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `alpha` | `float` | Significance level for hypothesis tests (default: 0.05) |

**Key Methods**:

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `calculate_descriptive_stats` | `data: NDArray` | `Dict[str, Union[float, int]]` | Mean, std, median, quartiles, skewness, kurtosis |
| `calculate_correlation` | `x: NDArray, y: NDArray, method: str` | `Dict` | Pearson, Spearman, or Kendall correlation with p-value |
| `calculate_confidence_interval` | `data: NDArray, confidence_level: float` | `Dict` | CI for mean using t-distribution |
| `perform_t_test` | `group1: NDArray, group2: NDArray, test_type: str` | `Dict` | Independent (Welch) or paired t-test with Cohen's d effect size |
| `anova_test` | `*groups: NDArray` | `Dict` | One-way ANOVA across two or more groups |
| `analyze_algorithm_performance` | `algorithm_results: Dict[str, List[float]]` | `Dict` | Comparative analysis with ANOVA and pairwise t-tests |

**Usage**:

```python
from src.statistical_analysis import StatisticalAnalyzer
import numpy as np

sa = StatisticalAnalyzer(alpha=0.05)
stats = sa.calculate_descriptive_stats(np.random.normal(0, 1, 100))
corr = sa.calculate_correlation(np.arange(50), np.arange(50) * 2 + 1)
```

---

### ValidationFramework

**Module**: `src/analysis/validation.py`

Comprehensive validation for Active Inference implementations covering probability distributions, generative models, theoretical correctness, and numerical stability.

**Constructor**:

```python
ValidationFramework(tolerance: float = 1e-6)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `tolerance` | `float` | Numerical tolerance for validation checks (default: 1e-6) |

**Key Methods**:

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `validate_probability_distribution` | `distribution: NDArray, name: str` | `Dict` | Check non-negativity, finiteness, and normalization (1D or 2D) |
| `validate_generative_model` | `model: Dict[str, NDArray]` | `Dict` | Validate A, B, C, D matrix shapes, compatibility, and probability properties |
| `validate_theoretical_correctness` | `algorithm_name: str, implementation_result: Dict, theoretical_expectation: Dict` | `Dict` | Check EFE decomposition, inference results, and numerical stability |
| `validate_algorithm_performance` | `performance_metrics: Dict, requirements: Dict` | `Dict` | Validate metrics against threshold or range requirements |
| `create_validation_report` | `validation_results: List[Dict]` | `Dict` | Aggregate multiple validations into a comprehensive report |

**Usage**:

```python
from src.validation import ValidationFramework
import numpy as np

vf = ValidationFramework()
result = vf.validate_probability_distribution(np.array([0.3, 0.7]), "prior")
model_check = vf.validate_generative_model({"A": A, "B": B, "C": C, "D": D})
```

---

## Visualization Package

### VisualizationEngine

**Module**: `src/visualization/visualization.py`

Publication-quality figure generation for Active Inference concepts including quadrant matrices, generative model diagrams, FEP visualizations, and meta-cognitive flow diagrams.

**Constructor**:

```python
VisualizationEngine(
    output_dir: Union[str, Path] = "output/figures",
    style: str = "publication"
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `output_dir` | `str` or `Path` | Directory for saving figures (created if missing) |
| `style` | `str` | Plot style: `"publication"` (serif, 300 DPI) or `"presentation"` (sans-serif, 150 DPI) |

**Key Methods**:

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `create_figure` | `figsize: Tuple[float, float]` | `Tuple[Figure, Axes]` | Create styled figure with grid and axis formatting |
| `apply_publication_style` | `ax, title, xlabel, ylabel, grid, legend` | `None` | Apply consistent publication formatting to axes |
| `save_figure` | `fig: Figure, filename: str, formats: List[str]` | `Dict[str, Path]` | Save in multiple formats (default: PNG + PDF) at 300 DPI |
| `create_quadrant_matrix_plot` | `matrix_data: Dict` | `Figure` | Render the 2x2 quadrant framework as a colored matrix |
| `create_generative_model_diagram` | `model_structure: Dict` | `Figure` | Render A, B, C, D matrix relationships as a flow diagram |
| `create_meta_cognitive_diagram` | `meta_cog_data: Dict` | `Figure` | Render meta-cognitive process flow with feedback loop |
| `create_fep_visualization` | `fep_data: Dict` | `Figure` | Render Free Energy Principle system boundaries and Markov blanket |
| `get_color` | `index: int` | `str` | Get hex color from a 10-color publication-ready palette |

**Usage**:

```python
from src.visualization import VisualizationEngine
from src.quadrant_framework import QuadrantFramework

engine = VisualizationEngine(output_dir="output/figures", style="publication")
fw = QuadrantFramework()
fig = engine.create_quadrant_matrix_plot(fw.create_quadrant_matrix_visualization())
engine.save_figure(fig, "quadrant_matrix", formats=["png", "pdf"])
```

---

## Utilities Package

### ValidationError

**Module**: `src/utils/exceptions.py`

Custom exception for validation failures with structured context and suggested fixes.

**Constructor**:

```python
ValidationError(
    message: str,
    context: dict = None,
    suggestions: list = None
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `message` | `str` | Error description |
| `context` | `dict` or `None` | Additional context information (default: `{}`) |
| `suggestions` | `list` or `None` | Suggested remediation actions (default: `[]`) |

**Attributes**: `message`, `context`, `suggestions`

**Usage**:

```python
from src.utils.exceptions import ValidationError

raise ValidationError(
    "Matrix A columns must sum to 1.0",
    context={"matrix": "A", "column_sums": [0.95, 1.0]},
    suggestions=["Normalize column 0"]
)
```

---

### get_logger

**Module**: `src/utils/logging.py`

Factory function returning a configured `logging.Logger` instance. Log level is controlled by the `LOG_LEVEL` environment variable (`0`=DEBUG, `1`=INFO, `2`=WARNING, `3`=ERROR; default: `1`).

**Signature**:

```python
get_logger(name: str) -> logging.Logger
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Logger name (conventionally `__name__`) |

**Usage**:

```python
from src.utils.logging import get_logger
logger = get_logger(__name__)
logger.info("Starting analysis pipeline")
```

---

### FigureManager

**Module**: `src/utils/figure_manager.py`

Manages a JSON registry of generated figures, tracking metadata (caption, label, section, generating script) for each figure.

**Constructor**:

```python
FigureManager(registry_file: Optional[str] = None)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `registry_file` | `str` or `None` | Path to registry JSON file. Defaults to `output/figures/figure_registry.json` relative to project root. |

**Key Methods**:

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `register_figure` | `filename: str, caption: str, label: Optional[str], section: Optional[str], generated_by: Optional[str], **kwargs` | `FigureMetadata` | Register a figure with metadata; auto-generates label from filename if not provided |

**FigureMetadata dataclass fields**: `filename`, `caption`, `label`, `section`, `generated_by`, `parameters`

**Usage**:

```python
from src.utils.figure_manager import FigureManager
fm = FigureManager()
meta = fm.register_figure(
    "quadrant_matrix.png",
    caption="2x2 quadrant framework",
    section="quadrant_model",
    generated_by="generate_figures.py"
)
```

---

### MarkdownIntegration

**Module**: `src/utils/markdown_integration.py`

Utilities for detecting sections in markdown manuscript files and programmatically inserting LaTeX figure blocks.

**Constructor**:

```python
MarkdownIntegration(manuscript_dir: Path)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `manuscript_dir` | `Path` | Path to manuscript directory containing `.md` files |

**Key Methods**:

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `detect_sections` | `markdown_file: Path` | `List[str]` | Extract all heading texts (levels 1-3) from a markdown file |
| `insert_figure_in_section` | `markdown_file: Path, figure_label: str, section: str, width: float, caption: str, filename: str` | `bool` | Insert a LaTeX `\begin{figure}` block after a specified section heading; skips if label already present |

**Usage**:

```python
from src.utils.markdown_integration import MarkdownIntegration
from pathlib import Path

mi = MarkdownIntegration(Path("manuscript"))
sections = mi.detect_sections(Path("manuscript/04_background.md"))
mi.insert_figure_in_section(
    Path("manuscript/04_background.md"),
    figure_label="fig:fep_visualization",
    section="The Free Energy Principle",
    caption="FEP system boundaries",
    filename="fep_system_boundaries.png"
)
```

---

## Convenience Functions

Several modules provide top-level convenience functions that instantiate default objects:

| Function | Module | Description |
|----------|--------|-------------|
| `create_simple_generative_model()` | `generative_models` | Create a 2-state demo model |
| `generate_time_series(*args, **kwargs)` | `data_generator` | Quick time series generation |
| `generate_synthetic_data(n_samples, n_features, distribution, seed)` | `data_generator` | Quick synthetic data |
| `calculate_descriptive_stats(data)` | `statistical_analysis` | Quick descriptive statistics |
| `calculate_correlation(x, y, method)` | `statistical_analysis` | Quick correlation analysis |
| `calculate_confidence_interval(data, confidence)` | `statistical_analysis` | Quick CI calculation |
| `anova_test(*groups)` | `statistical_analysis` | Quick ANOVA test |
| `demonstrate_*()` | All modules | Full concept demonstrations returning structured dictionaries |
