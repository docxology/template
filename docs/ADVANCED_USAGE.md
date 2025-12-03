# 🧪 Advanced Usage Guide

> **Master test-driven development** and complex workflows

**Previous**: [Intermediate Usage](INTERMEDIATE_USAGE.md) (Levels 4-6) | **Next**: [Expert Usage](EXPERT_USAGE.md) (Levels 10-12)

This guide covers **Levels 7-9** of the Research Project Template. Perfect for developers ready to embrace test-driven development, complex mathematical workflows, and reproducible research.

## 📚 What You'll Learn

By the end of this guide, you'll be able to:

- ✅ Practice test-driven development (TDD)
- ✅ Achieve and maintain comprehensive test coverage
- ✅ Build complex mathematical workflows
- ✅ Implement comprehensive testing strategies
- ✅ Ensure reproducible research results
- ✅ Manage data versioning and environment control

**Estimated Time:** 1-2 weeks

## 🎯 Prerequisites

- Completed [Intermediate Usage Guide](INTERMEDIATE_USAGE.md)
- Strong Python programming skills
- Understanding of software testing concepts
- Familiarity with pytest framework

**Development Standards:** See [Testing Standards](../.cursorrules/testing_standards.md) and [Type Hints Standards](../.cursorrules/type_hints_standards.md) for TDD and type safety guidelines.

## 📖 Table of Contents

- [Level 7: Test-Driven Development](#level-7-test-driven-development)
- [Level 8: Complex Mathematical Workflows](#level-8-complex-mathematical-workflows)
- [Level 9: Reproducible Research](#level-9-reproducible-research)
- [What to Read Next](#what-to-read-next)

---

## Level 7: Test-Driven Development

**Goal**: Master TDD methodology and maintain comprehensive coverage

**Time**: 3-5 days

### The TDD Cycle

```
1. Write Test (RED)
   ↓
2. Run Test (FAILS)
   ↓
3. Write Minimum Code (GREEN)
   ↓
4. Run Test (PASSES)
   ↓
5. Refactor (IMPROVE)
   ↓
6. Run Test (STILL PASSES)
   ↓
7. Repeat
```

### Example TDD Workflow

**Scenario**: Implement optimization algorithm

**Step 1: Write Test First** (RED)

```python
# tests/test_optimization.py
import pytest
from optimization import gradient_descent

def test_gradient_descent_converges():
    """Test that gradient descent converges for quadratic function."""
    
    def objective(x):
        return x[0]**2 + x[1]**2
    
    def gradient(x):
        return [2*x[0], 2*x[1]]
    
    result = gradient_descent(objective, gradient, [1.0, 1.0])
    
    # Test convergence
    assert result.converged == True
    assert result.iterations < 100
    assert abs(result.f_x) < 1e-6
    assert all(abs(xi) < 1e-3 for xi in result.x)
```

**Step 2: Run Test** (FAILS)

```bash
pytest tests/test_optimization.py
# ImportError: No module named 'optimization'
```

**Step 3: Write Minimum Code** (GREEN)

```python
# src/optimization.py
class OptimizationResult:
    """Container for optimization results."""
    def __init__(self, x, f_x, converged, iterations):
        self.x = x
        self.f_x = f_x
        self.converged = converged
        self.iterations = iterations

def gradient_descent(objective_fn, gradient_fn, initial_x,
                    learning_rate=0.01, max_iter=1000, tolerance=1e-6):
    """Gradient descent optimization."""
    x = list(initial_x)
    
    for iteration in range(max_iter):
        grad = gradient_fn(x)
        x_new = [x[i] - learning_rate * grad[i] for i in range(len(x))]
        
        # Check convergence
        if all(abs(x_new[i] - x[i]) < tolerance for i in range(len(x))):
            f_x = objective_fn(x_new)
            return OptimizationResult(x_new, f_x, True, iteration + 1)
        
        x = x_new
    
    # Max iterations reached
    f_x = objective_fn(x)
    return OptimizationResult(x, f_x, False, max_iter)
```

**Step 4: Run Test** (PASSES)

```bash
pytest tests/test_optimization.py
# ✓ test_gradient_descent_converges PASSED
```

**Step 5: Add More Tests**

```python
def test_gradient_descent_different_learning_rates():
    """Test with different learning rates."""
    def objective(x):
        return x[0]**2 + x[1]**2
    def gradient(x):
        return [2*x[0], 2*x[1]]
    
    for lr in [0.001, 0.01, 0.1]:
        result = gradient_descent(objective, gradient, [1.0, 1.0], learning_rate=lr)
        assert result.converged

def test_gradient_descent_max_iterations():
    """Test max iterations limit."""
    def objective(x):
        return x[0]**2
    def gradient(x):
        return [2*x[0]]
    
    result = gradient_descent(objective, gradient, [1.0], max_iter=5, learning_rate=0.001)
    assert result.iterations == 5
    assert result.converged == False

def test_gradient_descent_tolerance():
    """Test convergence with different tolerances."""
    def objective(x):
        return x[0]**2
    def gradient(x):
        return [2*x[0]]
    
    result = gradient_descent(objective, gradient, [1.0], tolerance=1e-8)
    assert result.converged
    assert abs(result.x[0]) < 1e-8
```

**Step 6: Check Coverage**

```bash
pytest tests/test_optimization.py --cov=src.optimization --cov-report=term-missing
```

Expected: Coverage requirements met (70% project, 49% infra)

### Ensuring 100% Coverage

**Check for missing lines**:

```bash
pytest tests/ --cov=src --cov-report=term-missing

# Output shows:
# Name                     Stmts   Miss  Cover   Missing
# ------------------------------------------------------
# src/optimization.py         25      2    92%   45-46
```

**Lines 45-46 are not covered** - add test:

```python
def test_edge_case_that_hits_lines_45_46():
    # Implement test that exercises those lines
    pass
```

**Generate HTML report** for visual inspection:

```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

### Coverage Requirements

This template enforces:

- ✅ **Statement coverage**: 100% of code lines
- ✅ **Branch coverage**: 100% of conditionals  
- ✅ **No mocks**: Real data only
- ✅ **Deterministic**: Fixed seeds for reproducibility

**See [TEST_IMPROVEMENTS_SUMMARY.md](TEST_IMPROVEMENTS_SUMMARY.md) for details.**

---

## Level 8: Complex Mathematical Workflows

**Goal**: Build sophisticated analysis pipelines

**Time**: 1 week

### Advanced Source Modules

**Example: Optimization with multiple algorithms**

```python
# src/optimizers.py
from typing import Callable, List, Tuple
from dataclasses import dataclass

@dataclass
class OptimizerConfig:
    """Configuration for optimization algorithms."""
    learning_rate: float = 0.01
    max_iterations: int = 1000
    tolerance: float = 1e-6
    momentum: float = 0.9  # For momentum-based methods

@dataclass
class OptimizationResult:
    """Results from optimization."""
    x: List[float]
    f_x: float
    converged: bool
    iterations: int
    history: List[Tuple[List[float], float]]  # Track progress

def gradient_descent_with_momentum(
    objective_fn: Callable,
    gradient_fn: Callable,
    initial_x: List[float],
    config: OptimizerConfig
) -> OptimizationResult:
    """Gradient descent with momentum."""
    x = list(initial_x)
    velocity = [0.0] * len(x)
    history = []
    
    for iteration in range(config.max_iterations):
        grad = gradient_fn(x)
        f_x = objective_fn(x)
        history.append((list(x), f_x))
        
        # Update velocity and position
        velocity = [
            config.momentum * v - config.learning_rate * g
            for v, g in zip(velocity, grad)
        ]
        x_new = [xi + vi for xi, vi in zip(x, velocity)]
        
        # Check convergence
        if all(abs(x_new[i] - x[i]) < config.tolerance for i in range(len(x))):
            f_x_new = objective_fn(x_new)
            history.append((x_new, f_x_new))
            return OptimizationResult(x_new, f_x_new, True, iteration + 1, history)
        
        x = x_new
    
    f_x = objective_fn(x)
    return OptimizationResult(x, f_x, False, config.max_iterations, history)

def adam_optimizer(
    objective_fn: Callable,
    gradient_fn: Callable,
    initial_x: List[float],
    config: OptimizerConfig,
    beta1: float = 0.9,
    beta2: float = 0.999,
    epsilon: float = 1e-8
) -> OptimizationResult:
    """Adam optimization algorithm."""
    x = list(initial_x)
    m = [0.0] * len(x)  # First moment
    v = [0.0] * len(x)  # Second moment
    history = []
    
    for t in range(1, config.max_iterations + 1):
        grad = gradient_fn(x)
        f_x = objective_fn(x)
        history.append((list(x), f_x))
        
        # Update biased moments
        m = [beta1 * mi + (1 - beta1) * gi for mi, gi in zip(m, grad)]
        v = [beta2 * vi + (1 - beta2) * gi**2 for vi, gi in zip(v, grad)]
        
        # Bias correction
        m_hat = [mi / (1 - beta1**t) for mi in m]
        v_hat = [vi / (1 - beta2**t) for vi in v]
        
        # Update parameters
        x_new = [
            xi - config.learning_rate * mh / (vh**0.5 + epsilon)
            for xi, mh, vh in zip(x, m_hat, v_hat)
        ]
        
        # Check convergence
        if all(abs(x_new[i] - x[i]) < config.tolerance for i in range(len(x))):
            f_x_new = objective_fn(x_new)
            history.append((x_new, f_x_new))
            return OptimizationResult(x_new, f_x_new, True, t, history)
        
        x = x_new
    
    f_x = objective_fn(x)
    return OptimizationResult(x, f_x, False, config.max_iterations, history)
```

### Comprehensive Testing

```python
# tests/test_optimizers.py
import pytest
import numpy as np
from optimizers import (
    gradient_descent_with_momentum,
    adam_optimizer,
    OptimizerConfig
)

class TestObjectiveFunctions:
    """Test functions for optimization."""
    
    @staticmethod
    def quadratic(x):
        return sum(xi**2 for xi in x)
    
    @staticmethod
    def quadratic_gradient(x):
        return [2*xi for xi in x]
    
    @staticmethod
    def rosenbrock(x):
        return sum(100*(x[i+1] - x[i]**2)**2 + (1 - x[i])**2 
                  for i in range(len(x)-1))
    
    @staticmethod
    def rosenbrock_gradient(x):
        grad = [0.0] * len(x)
        for i in range(len(x)-1):
            grad[i] += -400*x[i]*(x[i+1] - x[i]**2) - 2*(1 - x[i])
            grad[i+1] += 200*(x[i+1] - x[i]**2)
        return grad

def test_momentum_quadratic():
    """Test momentum on simple quadratic."""
    config = OptimizerConfig(learning_rate=0.01, max_iterations=1000)
    result = gradient_descent_with_momentum(
        TestObjectiveFunctions.quadratic,
        TestObjectiveFunctions.quadratic_gradient,
        [1.0, 1.0],
        config
    )
    assert result.converged
    assert result.f_x < 1e-10

def test_adam_rosenbrock():
    """Test Adam on Rosenbrock function."""
    config = OptimizerConfig(learning_rate=0.01, max_iterations=5000)
    result = adam_optimizer(
        TestObjectiveFunctions.rosenbrock,
        TestObjectiveFunctions.rosenbrock_gradient,
        [0.0, 0.0],
        config
    )
    # Rosenbrock minimum at [1, 1]
    assert all(abs(xi - 1.0) < 0.1 for xi in result.x)

def test_optimizer_history():
    """Test that history is tracked."""
    config = OptimizerConfig(learning_rate=0.1, max_iterations=100)
    result = gradient_descent_with_momentum(
        TestObjectiveFunctions.quadratic,
        TestObjectiveFunctions.quadratic_gradient,
        [1.0, 1.0],
        config
    )
    assert len(result.history) > 0
    # Check convergence in history
    final_f_x = result.history[-1][1]
    assert final_f_x < 1e-6
```

### Advanced Scripts

```python
# scripts/optimizer_comparison.py
#!/usr/bin/env python3
"""Compare multiple optimization algorithms."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from optimizers import (
    gradient_descent_with_momentum,
    adam_optimizer,
    OptimizerConfig
)

def rosenbrock(x):
    return sum(100*(x[i+1] - x[i]**2)**2 + (1 - x[i])**2 
              for i in range(len(x)-1))

def rosenbrock_gradient(x):
    grad = [0.0] * len(x)
    for i in range(len(x)-1):
        grad[i] += -400*x[i]*(x[i+1] - x[i]**2) - 2*(1 - x[i])
        grad[i+1] += 200*(x[i+1] - x[i]**2)
    return grad

def main():
    initial_x = [0.0, 0.0]
    config = OptimizerConfig(learning_rate=0.001, max_iterations=2000)
    
    # Use src/ methods for computation
    result_momentum = gradient_descent_with_momentum(
        rosenbrock, rosenbrock_gradient, initial_x, config
    )
    
    result_adam = adam_optimizer(
        rosenbrock, rosenbrock_gradient, initial_x, config
    )
    
    # Script handles visualization only
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot convergence
    momentum_history = [f_x for _, f_x in result_momentum.history]
    adam_history = [f_x for _, f_x in result_adam.history]
    
    ax1.semilogy(momentum_history, label='Momentum')
    ax1.semilogy(adam_history, label='Adam')
    ax1.set_xlabel('Iteration')
    ax1.set_ylabel('Objective Value')
    ax1.set_title('Convergence Comparison')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot trajectory
    momentum_x = [x[0] for x, _ in result_momentum.history]
    momentum_y = [x[1] for x, _ in result_momentum.history]
    adam_x = [x[0] for x, _ in result_adam.history]
    adam_y = [x[1] for x, _ in result_adam.history]
    
    ax2.plot(momentum_x, momentum_y, 'o-', label='Momentum', alpha=0.5)
    ax2.plot(adam_x, adam_y, 's-', label='Adam', alpha=0.5)
    ax2.plot(1, 1, 'r*', markersize=20, label='Optimum')
    ax2.set_xlabel('x[0]')
    ax2.set_ylabel('x[1]')
    ax2.set_title('Optimization Trajectory')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save
    output_path = 'output/figures/optimizer_comparison.png'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    # Print for manifest
    print(output_path)

if __name__ == '__main__':
    main()
```

---

## Level 9: Reproducible Research

**Goal**: Ensure complete reproducibility

**Time**: 2-3 days

### Deterministic Results

**Always set random seeds**:

```python
import numpy as np
import random

# At start of script
np.random.seed(42)
random.seed(42)

# In functions that use randomness
def monte_carlo_simulation(n_samples, seed=42):
    np.random.seed(seed)
    samples = np.random.normal(0, 1, n_samples)
    return samples
```

### Data Versioning

**Save metadata with data**:

```python
import json
import hashlib
from datetime import datetime

def save_with_metadata(data, filename, description=""):
    """Save data with comprehensive metadata."""
    import numpy as np
    import sys
    import platform
    
    # Save data
    np.savez(filename, data=data)
    
    # Calculate hash for integrity
    with open(filename, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    
    # Create metadata
    metadata = {
        'filename': filename,
        'description': description,
        'timestamp': datetime.now().isoformat(),
        'sha256': file_hash,
        'shape': data.shape if hasattr(data, 'shape') else len(data),
        'python_version': sys.version,
        'numpy_version': np.__version__,
        'platform': platform.platform(),
    }
    
    # Save metadata
    meta_file = filename.replace('.npz', '_metadata.json')
    with open(meta_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(filename)
    print(meta_file)
    
    return metadata
```

### Environment Management

**Lock dependencies**:

```bash
# Using uv (recommended)
uv lock --frozen

# Or pip
pip freeze > requirements.txt
```

**Document environment**:

```python
# scripts/capture_environment.py
import sys
import platform
import json

env_info = {
    'python_version': sys.version,
    'platform': platform.platform(),
    'machine': platform.machine(),
    'processor': platform.processor(),
}

# Add package versions
import numpy, matplotlib, pytest
env_info['packages'] = {
    'numpy': numpy.__version__,
    'matplotlib': matplotlib.__version__,
    'pytest': pytest.__version__,
}

with open('output/environment.json', 'w') as f:
    json.dump(env_info, f, indent=2)
```

**See [infrastructure/build/reproducibility.py](../infrastructure/build/reproducibility.py) for advanced tools.**

---

## What to Read Next

### If you're ready to...

**Build custom architectures**
→ Read **[Expert Usage Guide](EXPERT_USAGE.md)** (Levels 10-12)

**Understand complete architecture**
→ Read **[Architecture Guide](ARCHITECTURE.md)**

**See build system details**
→ Read **[Build System](BUILD_SYSTEM.md)**

**Review testing standards**
→ Read **[Test Improvements Summary](TEST_IMPROVEMENTS_SUMMARY.md)**

### Related Documentation

- **[Quick Start Cheatsheet](QUICK_START_CHEATSHEET.md)** - Essential commands
- **[Common Workflows](COMMON_WORKFLOWS.md)** - Step-by-step recipes
- **[Workflow Guide](WORKFLOW.md)** - Complete development process
- **[Glossary](GLOSSARY.md)** - Terms and definitions
- **[Documentation Index](DOCUMENTATION_INDEX.md)** - Complete reference

---

## Success Checklist

After completing this guide, you should be able to:

- [x] Practice test-driven development effectively
- [x] Achieve and maintain comprehensive test coverage
- [x] Build complex mathematical workflows
- [x] Implement comprehensive testing strategies  
- [x] Ensure reproducible research results
- [x] Manage data versioning and environments

**Congratulations!** You've mastered advanced usage. Ready for expert-level customization? Check out **[Expert Usage](EXPERT_USAGE.md)**.

---

**Need help?** Check the **[FAQ](FAQ.md)** or **[Common Workflows](COMMON_WORKFLOWS.md)**

**Quick Reference**: [Cheatsheet](QUICK_START_CHEATSHEET.md) | [Glossary](GLOSSARY.md)


