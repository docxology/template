# 🚀 HOW TO USE: Research Project Template

> **Complete Usage Guide** - From basic usage to advanced test-driven development

This comprehensive guide shows you how to use the Research Project Template at different levels of complexity. Whether you're just getting started or building advanced research workflows, this guide has you covered.

## 📚 **Quick Navigation**

- **[🚀 Quick Start](#-quick-start)** - Get up and running in minutes
- **[📝 Basic Usage](#-basic-usage)** - Simple document creation without coding
- **[🔧 Intermediate Usage](#-intermediate-usage)** - Add figures and basic automation
- **[🧪 Advanced Usage](#-advanced-usage)** - Test-driven development and complex workflows
- **[🏗️ Expert Usage](#️-expert-usage)** - Custom architectures and advanced features
- **[🆘 Troubleshooting](#-troubleshooting)** - Common issues and solutions

## 🚀 **Quick Start**

### **For Everyone: Use This Template**

1. **Click "Use this template"** on the [GitHub repository](https://github.com/docxology/template)
2. **Clone your new repository**
3. **Install dependencies**: `uv sync`
4. **Generate your first document**: `./repo_utilities/render_pdf.sh`

That's it! You now have a complete research project structure.

### **What You Get Immediately**

- ✅ **Complete project structure** with clear organization
- ✅ **Professional PDF generation** from markdown
- ✅ **Cross-referencing system** for equations and figures
- ✅ **Automated testing** framework
- ✅ **Build pipeline** that validates everything

## 📝 **Basic Usage**

### **Level 1: Just Write Documents**

If you want to focus purely on writing without any programming:

#### **1. Edit Manuscript Files**
Navigate to `manuscript/` and edit the existing files:
- `manuscript/01_introduction.md` - Your project introduction
- `manuscript/02_methodology.md` - Your methods and approach
- `manuscript/03_experimental_results.md` - Your results and findings
- `manuscript/04_discussion.md` - Your analysis and discussion
- `manuscript/05_conclusion.md` - Your conclusions

#### **2. Add Your Content**
Replace the template content with your research:

```markdown
# Introduction {#sec:introduction}

Your research introduction goes here. This template automatically handles:

- **Professional formatting** with LaTeX
- **Cross-referencing** between sections
- **Equation numbering** and references
- **Figure integration** and captions
- **Table of contents** generation
```

#### **3. Generate PDFs**
```bash
# Clean any previous outputs
./repo_utilities/clean_output.sh

# Generate everything
./repo_utilities/render_pdf.sh
```

**Result**: Professional PDFs with proper academic formatting, automatically numbered sections, and cross-references.

### **Level 2: Add Equations and References**

#### **Adding Mathematical Equations**
```markdown
\begin{equation}\label{eq:objective}
f(x) = \sum_{i=1}^{n} w_i \phi_i(x)
\end{equation}

The objective function \eqref{eq:objective} represents our optimization problem.
```

#### **Cross-Referencing Sections**
```markdown
# Methodology {#sec:methodology}

As described in Section \ref{sec:introduction}, our approach...

# Results {#sec:results}

Following the methodology in Section \ref{sec:methodology}, we found...
```

#### **Adding Figures**
```markdown
\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/your_figure.png}
\caption{Your figure caption}
\label{fig:your_figure}
\end{figure}

Figure \ref{fig:your_figure} shows the results of our analysis.
```

### **Level 3: Basic Customization**

#### **Project Metadata**
Edit `.project_config` to customize your project:
```bash
PROJECT_NAME="your-research-project"
PROJECT_DESCRIPTION="Your project description"
AUTHOR_NAME="Your Name"
AUTHOR_EMAIL="your.email@university.edu"
```

#### **Custom Styling**
Modify `manuscript/preamble.md` for custom LaTeX styling:
```latex
% Custom colors
\definecolor{myblue}{RGB}{0,114,178}
\definecolor{mygreen}{RGB}{0,158,115}

% Custom commands
\newcommand{\highlight}[1]{\textcolor{myblue}{#1}}
```

## 🔧 **Intermediate Usage**

### **Level 4: Add Basic Figures**

#### **Using Existing Figure Scripts**
The template includes example scripts that generate figures:

```bash
# Generate basic example figures
uv run python scripts/example_figure.py

# Generate research-quality figures
uv run python scripts/generate_research_figures.py
```

These scripts demonstrate the **thin orchestrator pattern** - they import mathematical functions from `src/` modules and use them to generate figures.

#### **Understanding the Pattern**
```python
# Scripts import from src/ modules
from example import add_numbers, calculate_average

# Use src/ methods for computation
data = [1, 2, 3, 4, 5]
avg = calculate_average(data)  # From src/example.py

# Script handles visualization and output
fig, ax = plt.subplots()
ax.plot(data)
ax.set_title(f"Average: {avg}")
```

#### **Adding Your Own Figures**
1. **Create a new script** in `scripts/` directory
2. **Import functions** from `src/` modules
3. **Use src/ methods** for all computation
4. **Handle visualization** and file output
5. **Print output paths** for the build system

### **Level 5: Basic Data Analysis**

#### **Extending Source Code**
Add new mathematical functions to `src/`:

```python
# src/analysis.py
def calculate_correlation(x: list[float], y: list[float]) -> float:
    """Calculate Pearson correlation coefficient."""
    # Implementation here
    pass

def perform_t_test(group1: list[float], group2: list[float]) -> tuple[float, float]:
    """Perform t-test between two groups."""
    # Implementation here
    pass
```

#### **Adding Tests**
Create tests in `tests/` directory:

```python
# tests/test_analysis.py
def test_calculate_correlation():
    x = [1, 2, 3, 4, 5]
    y = [2, 4, 6, 8, 10]
    corr = calculate_correlation(x, y)
    assert abs(corr - 1.0) < 1e-10

def test_perform_t_test():
    group1 = [1, 2, 3, 4, 5]
    group2 = [6, 7, 8, 9, 10]
    t_stat, p_value = perform_t_test(group1, group2)
    assert p_value < 0.05  # Significant difference
```

#### **Using in Scripts**
```python
# scripts/analysis_figures.py
from analysis import calculate_correlation, perform_t_test

def generate_correlation_plot():
    # Use src/ methods for computation
    x = [1, 2, 3, 4, 5]
    y = [2, 4, 6, 8, 10]
    corr = calculate_correlation(x, y)
    
    # Script handles visualization
    fig, ax = plt.subplots()
    ax.scatter(x, y)
    ax.set_title(f"Correlation: {corr:.3f}")
    return fig
```

### **Level 6: Automated Workflows**

#### **Running the Complete Pipeline**
```bash
# This single command does everything:
./repo_utilities/render_pdf.sh
```

**What happens automatically:**
1. ✅ **Runs all tests** (ensures 100% coverage)
2. ✅ **Executes all scripts** (generates figures and data)
3. ✅ **Validates markdown** (checks references and images)
4. ✅ **Generates glossary** (from source code API)
5. ✅ **Builds PDFs** (individual and combined)
6. ✅ **Exports LaTeX** (for further processing)

#### **Understanding the Output Structure**
```
output/
├── figures/          # PNG files from your scripts
├── data/             # CSV/NPZ data files
├── pdf/              # Individual and combined PDFs
└── tex/              # LaTeX source files
```

## 🧪 **Advanced Usage**

### **Level 7: Test-Driven Development**

#### **TDD Workflow**
1. **Write tests first** - Define expected behavior
2. **Run tests** - They should fail (no implementation yet)
3. **Implement functionality** - Write code to pass tests
4. **Refactor** - Clean up and optimize
5. **Repeat** - Add new features following the same pattern

#### **Example TDD Cycle**
```python
# 1. Write test first
def test_optimization_algorithm():
    """Test our optimization algorithm converges."""
    initial_guess = [1.0, 1.0]
    result = optimize_function(initial_guess, max_iter=100)
    assert result.converged
    assert result.iterations < 100
    assert abs(result.value - expected_minimum) < 1e-6

# 2. Run test (fails - no implementation)
# 3. Implement the algorithm
# 4. Run test again (passes)
# 5. Refactor and repeat
```

#### **Ensuring 100% Coverage**
```bash
# Check coverage
uv run pytest tests/ --cov=src --cov-report=term-missing

# Generate HTML coverage report
uv run pytest tests/ --cov=src --cov-report=html
```

**Coverage requirements:**
- **Statement coverage**: 100% of all code lines executed
- **Branch coverage**: 100% of all conditional branches taken
- **No mocks**: All tests use real numerical examples

### **Level 8: Complex Mathematical Workflows**

#### **Advanced Source Modules**
```python
# src/optimization.py
class OptimizationResult:
    def __init__(self, x: list[float], f_x: float, converged: bool, iterations: int):
        self.x = x
        self.f_x = f_x
        self.converged = converged
        self.iterations = iterations

def gradient_descent(objective_fn, gradient_fn, initial_x: list[float], 
                    learning_rate: float = 0.01, max_iter: int = 1000,
                    tolerance: float = 1e-6) -> OptimizationResult:
    """Gradient descent optimization algorithm."""
    x = initial_x.copy()
    
    for iteration in range(max_iter):
        grad = gradient_fn(x)
        x_new = [x[i] - learning_rate * grad[i] for i in range(len(x))]
        
        if all(abs(x_new[i] - x[i]) < tolerance for i in range(len(x))):
            return OptimizationResult(x_new, objective_fn(x_new), True, iteration + 1)
        
        x = x_new
    
    return OptimizationResult(x, objective_fn(x), False, max_iter)
```

#### **Comprehensive Testing**
```python
# tests/test_optimization.py
import pytest
import numpy as np

def test_gradient_descent_convergence():
    """Test gradient descent converges for simple quadratic function."""
    def objective(x):
        return x[0]**2 + x[1]**2
    
    def gradient(x):
        return [2*x[0], 2*x[1]]
    
    result = gradient_descent(objective, gradient, [1.0, 1.0])
    
    assert result.converged
    assert result.iterations < 100
    assert abs(result.f_x) < 1e-6
    assert all(abs(x) < 1e-3 for x in result.x)

def test_gradient_descent_parameters():
    """Test gradient descent with different parameters."""
    def objective(x):
        return x[0]**2 + x[1]**2
    
    def gradient(x):
        return [2*x[0], 2*x[1]]
    
    # Test different learning rates
    for lr in [0.001, 0.01, 0.1]:
        result = gradient_descent(objective, gradient, [1.0, 1.0], learning_rate=lr)
        assert result.converged
    
    # Test different tolerances
    for tol in [1e-4, 1e-6, 1e-8]:
        result = gradient_descent(objective, gradient, [1.0, 1.0], tolerance=tol)
        assert result.converged
```

#### **Advanced Scripts**
```python
# scripts/optimization_analysis.py
from optimization import gradient_descent
import matplotlib.pyplot as plt
import numpy as np

def generate_convergence_analysis():
    """Generate comprehensive convergence analysis."""
    
    # Test functions
    test_cases = [
        ("Quadratic", lambda x: x[0]**2 + x[1]**2, lambda x: [2*x[0], 2*x[1]]),
        ("Rosenbrock", lambda x: (1-x[0])**2 + 100*(x[1]-x[0]**2)**2, 
         lambda x: [-2*(1-x[0]) - 400*x[0]*(x[1]-x[0]**2), 200*(x[1]-x[0]**2)])
    ]
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    for i, (name, obj_fn, grad_fn) in enumerate(test_cases):
        # Use src/ methods for computation
        results = []
        for lr in [0.001, 0.01, 0.1]:
            result = gradient_descent(obj_fn, grad_fn, [1.0, 1.0], learning_rate=lr)
            results.append(result)
        
        # Script handles visualization
        axes[i].plot([r.iterations for r in results], [r.f_x for r in results], 'o-')
        axes[i].set_title(f"{name} Function")
        axes[i].set_xlabel("Iterations")
        axes[i].set_ylabel("Objective Value")
        axes[i].legend([f"LR={lr}" for lr in [0.001, 0.01, 0.1]])
        axes[i].set_yscale('log')
    
    plt.tight_layout()
    return fig
```

### **Level 9: Reproducible Research**

#### **Deterministic Results**
```python
# Set random seeds for reproducibility
import numpy as np
np.random.seed(42)

# Use deterministic algorithms
def deterministic_optimization():
    # Implementation that always produces same results
    pass
```

#### **Data Versioning**
```python
# scripts/data_generation.py
import hashlib
import json

def save_data_with_metadata(data, filename: str, metadata: dict):
    """Save data with metadata for reproducibility."""
    
    # Save data
    np.savez(filename, data=data)
    
    # Save metadata
    metadata_file = filename.replace('.npz', '_metadata.json')
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Print paths for build system
    print(f"../output/data/{filename}")
    print(f"../output/data/{metadata_file}")
```

#### **Environment Management**
```bash
# Create reproducible environment
uv lock --frozen

# Or with pip
pip freeze > requirements.txt
```

## 🏗️ **Expert Usage**

### **Level 10: Custom Architectures**

#### **Extending the Template**
Create new project types by extending the base structure:

```bash
# Create new project type
mkdir -p project_types/machine_learning
cp -r src tests scripts markdown project_types/machine_learning/
```

#### **Custom Build Pipelines**
```bash
# Create custom build script
#!/bin/bash
# custom_build.sh

# Run ML-specific tests
uv run pytest tests/ --cov=src --cov-report=html

# Generate ML-specific figures
uv run python scripts/ml_visualizations.py

# Build ML-specific documentation
pandoc manuscript/*.md -o output/ml_report.pdf --pdf-engine=xelatex
```

#### **Integration with External Tools**
```python
# scripts/external_integration.py
import subprocess
import json

def run_external_simulation():
    """Run external simulation tool and process results."""
    
    # Run external tool
    result = subprocess.run(['external_tool', '--config', 'config.json'], 
                          capture_output=True, text=True)
    
    # Process results using src/ methods
    from analysis import process_simulation_data
    processed_data = process_simulation_data(result.stdout)
    
    # Generate visualization
    fig = create_visualization(processed_data)
    return fig
```

### **Level 11: Advanced Automation**

#### **Continuous Integration**
```yaml
# .github/workflows/build.yml
name: Build and Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    - run: |
        pip install -r requirements.txt
        pytest tests/ --cov=src --cov-report=xml
    - uses: codecov/codecov-action@v1
```

#### **Automated Documentation**
```python
# scripts/auto_documentation.py
import ast
import inspect

def generate_api_documentation():
    """Automatically generate API documentation from source code."""
    
    api_docs = {}
    
    for module_name in ['example', 'analysis', 'optimization']:
        module = __import__(module_name)
        api_docs[module_name] = {}
        
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj) and not name.startswith('_'):
                api_docs[module_name][name] = {
                    'docstring': obj.__doc__,
                    'signature': str(inspect.signature(obj))
                }
    
    return api_docs
```

### **Level 12: Research Workflow Integration**

#### **Literature Review Integration**
```python
# scripts/literature_analysis.py
import requests
from src.analysis import text_analysis

def analyze_research_trends():
    """Analyze research trends from literature."""
    
    # Fetch recent papers
    papers = fetch_recent_papers("machine learning optimization")
    
    # Use src/ methods for analysis
    trends = text_analysis.extract_trends([p['abstract'] for p in papers])
    
    # Generate trend visualization
    fig = create_trend_plot(trends)
    return fig
```

#### **Collaborative Research**
```bash
# Set up collaborative workflow
git checkout -b feature/new-algorithm
# Make changes
git add .
git commit -m "Add new optimization algorithm"
git push origin feature/new-algorithm
# Create pull request
```

## 🆘 **Troubleshooting**

### **Common Issues and Solutions**

#### **Tests Failing**
```bash
# Check what's failing
uv run pytest tests/ -v

# Check coverage gaps
uv run pytest tests/ --cov=src --cov-report=term-missing

# Fix coverage issues
# Add tests for uncovered code paths
```

#### **Script Import Errors**
```bash
# Ensure src/ is on Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Or use the built-in path management
python scripts/your_script.py
```

#### **PDF Generation Issues**
```bash
# Check pandoc installation
pandoc --version

# Check LaTeX installation
xelatex --version

   # Verify manuscript syntax
   uv run python repo_utilities/validate_markdown.py
```

#### **Figure Generation Problems**
```bash
# Check matplotlib backend
export MPLBACKEND=Agg

# Run figure generation scripts
uv run python scripts/example_figure.py

# Check output directories exist
ls -la output/figures/
```

### **Getting Help**

1. **Check the documentation**:
   - **[`README.md`](docs/README.md)** - Project overview
   - **[`ARCHITECTURE.md`](docs/ARCHITECTURE.md)** - System design
   - **[`WORKFLOW.md`](docs/WORKFLOW.md)** - Development process

2. **Review error messages** - Most issues have clear error descriptions

3. **Check the build pipeline** - Run `./repo_utilities/render_pdf.sh` and review output

4. **Validate components individually**:
   ```bash
   # Test source code
   uv run pytest tests/
   
   # Test scripts
   uv run python scripts/example_figure.py
   
   # Validate markdown
   uv run python repo_utilities/validate_markdown.py
   ```

## 🎯 **Usage Patterns by Experience Level**

### **Beginner (Levels 1-3)**
- **Focus**: Document creation and basic formatting
- **Tools**: Markdown editor, basic LaTeX knowledge
- **Output**: Professional PDFs with equations and references
- **Time**: 1-2 hours to get started

### **Intermediate (Levels 4-6)**
- **Focus**: Figure generation and basic automation
- **Tools**: Python basics, matplotlib, basic testing
- **Output**: Automated figure generation and data analysis
- **Time**: 1-2 days to implement basic workflows

### **Advanced (Levels 7-9)**
- **Focus**: Test-driven development and reproducible research
- **Tools**: Python expertise, testing frameworks, CI/CD
- **Output**: Fully tested, reproducible research workflows
- **Time**: 1-2 weeks to implement comprehensive systems

### **Expert (Levels 10-12)**
- **Focus**: Custom architectures and advanced automation
- **Tools**: System design, advanced Python, DevOps
- **Output**: Custom research platforms and automated workflows
- **Time**: 1-2 months to build custom systems

## 🚀 **Next Steps**

### **Choose Your Path**

1. **Start Simple**: Begin with basic document creation (Levels 1-3)
2. **Add Automation**: Gradually add figures and scripts (Levels 4-6)
3. **Embrace Testing**: Implement test-driven development (Levels 7-9)
4. **Build Systems**: Create custom architectures (Levels 10-12)

### **Resources for Each Level**

- **Levels 1-3**: **[`README.md`](docs/README.md)**, **[`docs/MARKDOWN_TEMPLATE_GUIDE.md`](docs/MARKDOWN_TEMPLATE_GUIDE.md)**
- **Levels 4-6**: **[`EXAMPLES.md`](docs/EXAMPLES.md)**, **[`EXAMPLES_SHOWCASE.md`](docs/EXAMPLES_SHOWCASE.md)**
- **Levels 7-9**: **[`WORKFLOW.md`](docs/WORKFLOW.md)**, **[`THIN_ORCHESTRATOR_SUMMARY.md`](docs/THIN_ORCHESTRATOR_SUMMARY.md)**
- **Levels 10-12**: **[`ARCHITECTURE.md`](docs/ARCHITECTURE.md)**, **[`ROADMAP.md`](docs/ROADMAP.md)**

### **Community Support**

- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and share experiences
- **Contributing**: Help improve the template for everyone

---

**Ready to transform your research workflow? Start at your comfort level and gradually advance through the levels. The template grows with you! 🚀**

For detailed implementation guidance, see **[`ARCHITECTURE.md`](docs/ARCHITECTURE.md)** and **[`WORKFLOW.md`](docs/WORKFLOW.md)**.
