# Usage Documentation

## Overview

The `docs/usage/` directory contains practical usage examples, templates, and guides for effectively using the Research Project Template. These documents focus on real-world application and demonstrate best practices through concrete examples.

## Directory Structure

```
docs/usage/
├── AGENTS.md                       # This technical documentation
├── examples-showcase.md            # Real-world usage examples
├── examples.md                     # Usage examples and patterns
├── image-management.md             # Image handling and integration
├── manuscript-numbering-system.md  # Section numbering conventions
├── markdown-template-guide.md      # Markdown authoring guide
├── README.md                       # Quick reference for usage docs
├── template-description.md         # Template features overview
└── visualization-guide.md          # Data visualization techniques
```

## Key Documentation Files

### Examples Showcase (`examples-showcase.md`)

**Real-world research project examples:**

**Project Examples:**
- Machine learning research manuscript
- Statistical analysis publication
- Multi-author collaborative project
- Reproducible computational study

**Implementation Showcases:**
- Directory structure examples
- Configuration patterns
- Analysis workflow demonstrations
- Output generation examples

### Usage Examples (`examples.md`)

**Practical examples for common tasks:**

**Basic Usage Patterns:**
- Project initialization and setup
- Content creation and organization
- Analysis execution workflows
- Output generation procedures

**Advanced Patterns:**
- Custom analysis script development
- Multi-format output generation
- External tool integration
- Performance optimization examples

### Template Description (`template-description.md`)

**feature overview:**

**Core Capabilities:**
- Two-layer architecture benefits
- Thin orchestrator pattern advantages
- Multi-format output support
- Quality assurance features

**Advanced Features:**
- LLM integration capabilities
- Publishing platform support
- Validation and quality checks
- Performance optimization tools

### Markdown Template Guide (`markdown-template-guide.md`)

**Manuscript authoring best practices:**

**Structure and Organization:**
- Section hierarchy conventions
- Cross-reference techniques
- Figure and table integration
- Citation management

**Formatting Standards:**
- Markdown syntax guidelines
- LaTeX integration methods
- Mathematical notation
- Code block formatting

### Manuscript Numbering System (`manuscript-numbering-system.md`)

**Section numbering conventions and standards:**

**Numbering Hierarchy:**
- Main sections (1, 2, 3...)
- Subsections (1.1, 1.2, 2.1...)
- Sub-subsections (1.1.1, 1.1.2...)
- Appendix sections (A, B, C...)

**Cross-Reference System:**
- Internal reference formatting
- Figure and table numbering
- Equation references
- Citation linking

## Usage Documentation Standards

### Practical Example Focus

**Real Implementation Examples:**
```markdown
## Example: Research Workflow

### 1. Project Setup
```bash
# Create new research project
mkdir cardiovascular_study && cd cardiovascular_study
cp -r /path/to/template/* .

# Configure project
vim project/manuscript/config.yaml
```

### 2. Data Analysis Development
```python
# project/src/cardiovascular_analysis.py
import pandas as pd
import numpy as np
from scipy import stats

class CardiovascularAnalyzer:
    """Analyze cardiovascular health data."""

    def analyze_blood_pressure(self, data: pd.DataFrame) -> dict:
        """Analyze blood pressure measurements."""
        systolic = data['systolic_bp']
        diastolic = data['diastolic_bp']

        return {
            'mean_systolic': systolic.mean(),
            'mean_diastolic': diastolic.mean(),
            'hypertension_prevalence': (systolic >= 140).mean() * 100,
            'correlation': stats.pearsonr(systolic, diastolic)[0]
        }
```

### 3. Manuscript Content
```markdown
# Cardiovascular Health Study

## Abstract

This study analyzes blood pressure measurements from 1,000 participants...

## Methods

Data was collected using standardized protocols...
Statistical analysis performed using Python scientific stack...

## Results

```{python}
# project/scripts/generate_results.py
analyzer = CardiovascularAnalyzer()
results = analyzer.analyze_blood_pressure(bp_data)

print(f"Mean systolic BP: {results['mean_systolic']:.1f} mmHg")
print(f"Hypertension prevalence: {results['hypertension_prevalence']:.1f}%")
```
```

**Workflow Demonstrations:**
```bash
# Execute analysis pipeline
python3 scripts/02_run_analysis.py

# Generate manuscript with results
python3 scripts/03_render_pdf.py

# Validate all outputs
python3 scripts/04_validate_output.py

# Output: cardiovascular_study.pdf (manuscript)
```

### Template-Based Examples

**Reusable Project Templates:**
```python
# Template: Statistical Analysis Project
# File: project/src/statistical_model.py

from typing import Dict, List, Any
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error

class StatisticalModel:
    """Template for statistical analysis projects."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = None
        self.metrics = {}

    def load_data(self, filepath: str) -> pd.DataFrame:
        """Load and preprocess data."""
        data = pd.read_csv(filepath)

        # Handle missing values
        data = data.dropna()

        # Encode categorical variables if needed
        # data = pd.get_dummies(data, columns=['categorical_col'])

        return data

    def train_model(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train statistical model."""
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.model = LinearRegression()
        self.model.fit(X_train, y_train)

        # Calculate metrics
        y_pred = self.model.predict(X_test)
        self.metrics = {
            'r2_score': r2_score(y_test, y_pred),
            'mse': mean_squared_error(y_test, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred))
        }

    def generate_report(self) -> str:
        """Generate analysis report."""
        return f"""
Statistical Analysis Results
==========================

Model Performance:
- R² Score: {self.metrics['r2_score']:.3f}
- Mean Squared Error: {self.metrics['mse']:.3f}
- Root Mean Squared Error: {self.metrics['rmse']:.3f}

Model Coefficients:
{self._format_coefficients()}
"""

    def _format_coefficients(self) -> str:
        """Format model coefficients for display."""
        if self.model is None:
            return "Model not trained"

        coef_df = pd.DataFrame({
            'Feature': [f'X{i}' for i in range(len(self.model.coef_))],
            'Coefficient': self.model.coef_
        })
        return coef_df.to_string(index=False)
```

## Content Organization

### Progressive Complexity

**Beginner to Expert Examples:**

**Level 1-2 (Beginner):**
```bash
# Simple project setup
mkdir my_study && cd my_study
cp -r /path/to/template/* .

# Basic configuration
echo "paper:
  title: 'My First Study'
authors:
  - name: 'Dr. Researcher'" > project/manuscript/config.yaml

# Generate basic output
python3 scripts/03_render_pdf.py
```

**Level 3-4 (Intermediate):**
```python
# Custom analysis script
# project/scripts/data_analysis.py

from project.src.analysis import DataAnalyzer
from infrastructure.core import get_logger

def main():
    """Execute data analysis."""
    logger = get_logger(__name__)

    analyzer = DataAnalyzer()
    results = analyzer.analyze_data('data/dataset.csv')

    logger.info(f"Analysis: {len(results)} findings")

    # Generate plots
    analyzer.create_visualizations(results, 'output/figures/')

if __name__ == "__main__":
    main()
```

**Level 5-6 (Advanced):**
```python
# Advanced multi-method analysis
# project/src/advanced_analyzer.py

from typing import Protocol, List, Dict, Any
from abc import ABC, abstractmethod
import concurrent.futures
from project.src.base_analyzer import BaseAnalyzer

class AnalysisMethod(Protocol):
    """Protocol for analysis methods."""
    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        ...

class ComparativeAnalyzer(BaseAnalyzer):
    """Analyzer supporting multiple analysis methods."""

    def __init__(self, methods: List[AnalysisMethod]):
        super().__init__()
        self.methods = methods

    def run_comparative_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Run multiple analysis methods in parallel."""

        def run_method(method):
            return method.__class__.__name__, method.analyze(data)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(run_method, self.methods))

        return dict(results)

    def generate_comparison_report(self, results: Dict[str, Any]) -> str:
        """Generate comparative analysis report."""
        report_lines = ["Comparative Analysis Report", "=" * 30, ""]

        for method_name, method_results in results.items():
            report_lines.extend([
                f"{method_name}:",
                f"  Key Findings: {method_results.get('key_findings', 'N/A')}",
                f"  Confidence: {method_results.get('confidence', 'N/A')}",
                ""
            ])

        return "\n".join(report_lines)
```

### Category-Based Organization

**Research Domain Examples:**
- **Machine Learning**: Neural network analysis, model evaluation
- **Statistics**: Hypothesis testing, regression analysis, experimental design
- **Data Science**: ETL pipelines, visualization, feature engineering
- **Computational Biology**: Sequence analysis, pathway modeling
- **Physics**: Simulation workflows, data analysis, computational methods

**Project Scale Examples:**
- **Small Projects**: Single analysis, basic visualization
- **Medium Projects**: Multiple analyses, validation
- **Large Projects**: Distributed computing, complex workflows
- **Collaborative Projects**: Multi-author coordination, version control

## Quality Assurance

### Example Validation

**Automated Testing:**
```bash
# Test all usage examples
./validate_usage_examples.sh docs/usage/

# Check example code syntax
python3 -m py_compile docs/usage/examples/**/*.py

# Validate markdown examples
python3 validate_markdown_examples.py docs/usage/
```

**Example Completeness:**
- All code examples must be runnable
- All command sequences must work
- All file references must exist
- All configurations must be valid

### Content Accuracy

**Technical Validation:**
- Code examples tested in clean environments
- Command outputs verified for accuracy
- Configuration examples validated against schema
- File paths confirmed to exist

**Cross-Reference Verification:**
- Internal links must work
- External references must be current
- Related documentation must exist
- Version dependencies must be accurate

## Maintenance Procedures

### Content Updates

**Regular Maintenance:**
- Update examples with new template features
- Refresh outdated code patterns
- Validate all examples quarterly
- Update version-specific information

**Example Evolution:**
- Add examples for new use cases
- Update examples to use best practices
- Remove deprecated patterns
- Enhance existing examples based on user feedback

### User Feedback Integration

**Usage Analytics:**
- Track which examples are most viewed
- Monitor example completion rates
- Collect user feedback on examples
- Identify common usage patterns

**Content Improvement:**
```python
# Analyze usage patterns
def analyze_example_usage():
    """Analyze which examples are most effective."""
    usage_data = collect_usage_analytics()

    # Identify popular patterns
    popular_domains = find_popular_research_domains(usage_data)
    common_workflows = identify_common_workflows(usage_data)

    # Generate improvement recommendations
    recommendations = []

    for domain in popular_domains:
        if not has_domain_example(domain):
            recommendations.append(f"Add example for {domain} research")

    for workflow in common_workflows:
        if not has_workflow_example(workflow):
            recommendations.append(f"Create example for {workflow} workflow")

    return recommendations
```

## Special Content Types

### Template Collections

**Project Templates:**
```markdown
## Machine Learning Research Template

### Directory Structure
```
ml_research/
├── manuscript/
│   ├── 01_introduction.md
│   ├── 02_methodology.md
│   ├── 03_experiments.md
│   ├── 04_results.md
│   └── config.yaml
├── src/
│   ├── data_preprocessing.py
│   ├── model_training.py
│   ├── evaluation.py
│   └── visualization.py
└── scripts/
    ├── prepare_data.py
    ├── train_models.py
    └── generate_report.py
```

### Configuration Examples
```yaml
# ml_research/manuscript/config.yaml
paper:
  title: "Deep Learning for Image Classification"
  version: "1.0"

authors:
  - name: "Dr. ML Researcher"
    affiliation: "AI Research Lab"

keywords:
  - "deep learning"
  - "computer vision"
  - "image classification"
```

### Analysis Workflow
```python
# ml_research/scripts/train_models.py
from src.model_training import ModelTrainer
from src.evaluation import ModelEvaluator
from infrastructure.core import get_logger

def main():
    """Train and evaluate ML models."""
    logger = get_logger(__name__)

    # Prepare data
    trainer = ModelTrainer(config)
    trainer.prepare_data('data/images/')

    # Train models
    models = trainer.train_models(['cnn', 'transformer', 'ensemble'])

    # Evaluate performance
    evaluator = ModelEvaluator()
    results = evaluator.evaluate_models(models, 'data/test/')

    # Generate comparison report
    evaluator.generate_comparison_report(results, 'output/reports/')

    logger.info("Model training and evaluation")

if __name__ == "__main__":
    main()
```
```

### Implementation Showcase
```markdown
## Results

### Model Performance Comparison

| Model | Accuracy | F1-Score | Training Time |
|-------|----------|----------|---------------|
| CNN | 0.92 | 0.91 | 45 min |
| Transformer | 0.89 | 0.88 | 120 min |
| Ensemble | 0.94 | 0.93 | 180 min |

### Key Findings

- Ensemble model achieved highest accuracy (94%)
- CNN provided best performance/accuracy tradeoff
- Transformer model required significantly more training time

```{python}
# Generate performance visualization
from src.visualization import PerformanceVisualizer

visualizer = PerformanceVisualizer()
visualizer.create_performance_comparison(results, 'output/figures/model_comparison.png')
```
```

## Future Enhancements

### Examples

**Planned Improvements:**
- Video tutorials for complex workflows
- Interactive examples with live code execution
- Domain-specific example collections
- Template generator for common research types

**Content Expansion:**
- Multi-disciplinary research examples
- International collaboration examples
- Reproducibility-focused examples
- Performance optimization case studies

### Community Contributions

**Example Submission Process:**
1. **Identify Need**: Find research domain or workflow not covered
2. **Develop Example**: Create, working example
3. **Test Thoroughly**: Validate in multiple environments
4. **Document Clearly**: Provide documentation
5. **Submit for Review**: Get feedback from maintainers
6. **Publish**: Add to appropriate usage document

## See Also

**Usage Documentation:**
- [`examples.md`](examples.md) - General usage examples
- [`examples-showcase.md`](examples-showcase.md) - Real-world showcases
- [`template-description.md`](template-description.md) - Feature overview
- [`markdown-template-guide.md`](markdown-template-guide.md) - Authoring guide

**System Documentation:**
- [`../AGENTS.md`](../AGENTS.md) - system overview
- [`../documentation-index.md`](../documentation-index.md) - Documentation index
- [`../../AGENTS.md`](../../AGENTS.md) - Root system documentation