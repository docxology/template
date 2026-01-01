#!/usr/bin/env python3
"""API documentation generation script for code project.

This script demonstrates the documentation infrastructure capabilities by:
1. Generating API documentation from source code
2. Creating documentation artifacts
3. Registering documentation with the figure manager
"""

import sys
from pathlib import Path

# Add project src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Add infrastructure imports (with graceful fallback)
try:
    # Ensure repo root is on path for infrastructure imports
    repo_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(repo_root))

    try:
        from infrastructure.documentation import (
            generate_glossary,
        )
        from infrastructure.core import (
            get_logger,
            log_operation,
            log_success,
            ProgressBar,
        )
    except ImportError:
        # Fallback when infrastructure is not available
        generate_glossary = None
        get_logger = lambda x: None
        log_operation = lambda *args, **kwargs: nullcontext()
        log_success = lambda *args, **kwargs: None
        ProgressBar = lambda *args, **kwargs: nullcontext()

        class nullcontext:
            def __enter__(self): return self
            def __exit__(self, *args): pass
    INFRASTRUCTURE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Infrastructure modules not available: {e}")
    INFRASTRUCTURE_AVAILABLE = False


def generate_api_documentation():
    """Generate comprehensive API documentation for the code project."""
    print("Generating API documentation...")

    try:
        # Output directory for documentation
        output_dir = project_root / "output" / "docs"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate glossary if available
        glossary_path = None
        if generate_glossary:
            print("Generating API glossary...")
            try:
                glossary_path = generate_glossary(
                    source_dirs=[project_root / "src"],
                    output_dir=output_dir,
                    min_frequency=2
                )
            except Exception as e:
                print(f"⚠️  Glossary generation failed: {e}")

        # Create a simple API reference manually
        print("Creating API reference...")
        api_ref_path = output_dir / "api_reference.md"

        # Get functions from optimizer module
        from optimizer import (
            quadratic_function,
            compute_gradient,
            gradient_descent,
            OptimizationResult,
        )

        api_content = """# Code Project API Reference

This document provides API reference for the code project's optimization algorithms.

## Classes

### OptimizationResult

Container for optimization algorithm results.

**Attributes:**
- `solution`: Final solution point as numpy array
- `objective_value`: Objective function value at the solution
- `iterations`: Number of iterations performed
- `converged`: True if gradient norm fell below tolerance
- `gradient_norm`: Final L2 norm of the gradient vector
- `objective_history`: List of objective function values during optimization

## Functions

### quadratic_function(x, A=None, b=None)

Evaluate quadratic objective function f(x) = (1/2) x^T A x - b^T x.

**Parameters:**
- `x`: Input point as numpy array (n-dimensional vector)
- `A`: Symmetric positive definite matrix (n x n). Defaults to identity.
- `b`: Linear coefficient vector (n-dimensional). Defaults to vector of ones.

**Returns:** Function value as float

### compute_gradient(x, A=None, b=None)

Compute analytical gradient of quadratic function ∇f(x) = A x - b.

**Parameters:**
- `x`: Input point as numpy array (n-dimensional vector)
- `A`: Symmetric positive definite matrix (n x n). Defaults to identity.
- `b`: Linear coefficient vector (n-dimensional). Defaults to vector of ones.

**Returns:** Gradient vector as numpy array

### gradient_descent(initial_point, objective_func, gradient_func, ...)

Perform gradient descent optimization with fixed step size.

**Parameters:**
- `initial_point`: Starting point for optimization as numpy array
- `objective_func`: Callable that takes x and returns f(x)
- `gradient_func`: Callable that takes x and returns ∇f(x)
- `max_iterations`: Maximum number of iterations (default: 1000)
- `tolerance`: Convergence tolerance for gradient norm (default: 1e-6)
- `step_size`: Fixed step size α > 0 (default: 0.01)
- `verbose`: If True, print progress (default: False)

**Returns:** OptimizationResult containing solution and convergence diagnostics

## Examples

```python
import numpy as np
from optimizer import gradient_descent, quadratic_function, compute_gradient

# Define optimization problem
def obj_func(x):
    return quadratic_function(x, np.eye(len(x)), np.ones(len(x)))

def grad_func(x):
    return compute_gradient(x, np.eye(len(x)), np.ones(len(x)))

# Run optimization
initial_point = np.array([0.0, 0.0])
result = gradient_descent(initial_point, obj_func, grad_func, step_size=0.1)

if result.converged:
    print(f"Converged in {{result.iterations}} iterations")
    print(f"Solution: {{result.solution}}")
    print(f"Objective: {{result.objective_value:.6f}}")
else:
    print(f"Did not converge within {{result.iterations}} iterations")
```
"""

        with open(api_ref_path, 'w') as f:
            f.write(api_content)

        documentation_files = {
            'api_reference': str(api_ref_path),
            'glossary': str(glossary_path) if glossary_path else None,
        }

        print("✅ API documentation generation completed")
        return documentation_files

    except Exception as e:
        print(f"⚠️  API documentation generation failed: {e}")
        return None


def generate_code_quality_report():
    """Generate code quality and documentation completeness report."""
    if not INFRASTRUCTURE_AVAILABLE:
        return None

    print("Generating code quality report...")

    try:
        from infrastructure.documentation import analyze_code_quality

        src_dirs = [project_root / "src"]
        output_dir = project_root / "output" / "reports"

        quality_report = analyze_code_quality(
            source_dirs=src_dirs,
            output_dir=output_dir,
            include_metrics=True,
            include_coverage=True
        )

        print("✅ Code quality analysis completed")
        return quality_report

    except Exception as e:
        print(f"⚠️  Code quality analysis failed: {e}")
        return None


def main():
    """Main API documentation generation function."""
    print("Starting API documentation generation...")

    try:
        # Generate API documentation
        docs_files = generate_api_documentation()

        # Summary
        print("\nAPI Documentation Generation Complete!")
        if docs_files:
            print("Generated documentation files:")
            for doc_type, file_path in docs_files.items():
                if file_path:
                    print(f"  - {doc_type}: {file_path}")
            print("✅ API documentation generation completed successfully!")
        else:
            print("❌ API documentation generation failed - check error messages above")
            return 1  # Exit with error code

    except Exception as e:
        error_msg = f"API documentation generation failed: {e}"
        print(f"\n❌ {error_msg}")
        raise


if __name__ == "__main__":
    main()