#!/usr/bin/env python3
"""API documentation generation script for code project.

This script demonstrates the documentation infrastructure capabilities by:
1. Generating API documentation from source code
2. Creating documentation artifacts
3. Registering documentation with the figure manager
"""

import sys
from contextlib import nullcontext
from pathlib import Path
from typing import Any

# Add project src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Add infrastructure imports (with graceful null-object fallback)
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

try:
    from infrastructure.core import ProgressBar, get_logger, log_operation, log_success
    from infrastructure.documentation import generate_glossary
except ImportError:
    generate_glossary = None

    def get_logger(x):  # type: ignore[misc]
        return None

    def log_operation(*args, **kwargs):  # type: ignore[misc]
        return nullcontext()

    def log_success(*args, **kwargs):  # type: ignore[misc]
        return None

    def ProgressBar(*args, **kwargs):  # type: ignore[misc]
        return nullcontext()


def generate_api_documentation() -> dict[str, Any] | None:
    """Generate comprehensive API documentation for the code project."""
    logger = get_logger(__name__)

    if logger:
        logger.info("Generating API documentation...")

    try:
        # Output directory for documentation
        output_dir = project_root / "output" / "docs"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate glossary if available
        glossary_path = None
        if generate_glossary:
            if logger:
                logger.info("Generating API glossary...")
            try:
                glossary_path = generate_glossary(
                    source_dirs=[project_root / "src"],
                    output_dir=output_dir,
                    min_frequency=2,
                )
            except Exception as e:
                if logger:
                    logger.warning(f"Glossary generation failed: {e}")

        # Create a simple API reference manually
        if logger:
            logger.info("Creating API reference...")
        api_ref_path = output_dir / "api_reference.md"

        # Get functions from optimizer module (imported for API introspection)
        from optimizer import (compute_gradient,  # noqa: F401
                               gradient_descent, quadratic_function)  # noqa: F401

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
    if logger:
        logger.debug(f"Converged in {result.iterations} iterations")
        logger.debug(f"Solution: {result.solution}")
        logger.debug(f"Objective: {result.objective_value:.6f}")
else:
    if logger:
        logger.warning(f"Did not converge within {result.iterations} iterations")
```
"""

        with open(api_ref_path, "w") as f:
            f.write(api_content)

        documentation_files = {
            "api_reference": str(api_ref_path),
            "glossary": str(glossary_path) if glossary_path else None,
        }

        if logger:
            logger.info("API documentation generation completed")
        return documentation_files

    except (OSError, ImportError, ValueError) as e:
        if logger:
            logger.warning(f"API documentation generation failed: {e}")
        return None


def generate_code_quality_report() -> Any:
    """Generate code quality and documentation completeness report."""
    logger = get_logger(__name__)

    if logger:
        logger.info("Generating code quality report...")

    try:
        from infrastructure.documentation import analyze_code_quality

        src_dirs = [project_root / "src"]
        output_dir = project_root / "output" / "reports"

        quality_report = analyze_code_quality(
            source_dirs=src_dirs,
            output_dir=output_dir,
            include_metrics=True,
            include_coverage=True,
        )

        if logger:
            logger.info("Code quality analysis completed")
        return quality_report

    except (OSError, ImportError, ValueError) as e:
        if logger:
            logger.warning(f"Code quality analysis failed: {e}")
        return None


def main() -> int | None:
    """Main API documentation generation function."""
    logger = get_logger(__name__)

    if logger:
        logger.info("Starting API documentation generation...")

    try:
        # Generate API documentation
        docs_files = generate_api_documentation()

        # Summary
        if logger:
            logger.info("API Documentation Generation Complete!")
        if docs_files:
            if logger:
                logger.info("Generated documentation files:")
                for doc_type, file_path in docs_files.items():
                    if file_path:
                        logger.info(f"  - {doc_type}: {file_path}")
                logger.info("API documentation generation completed successfully!")
        else:
            if logger:
                logger.error(
                    "API documentation generation failed - check error messages above"
                )
            return 1  # Exit with error code

    except (OSError, ImportError, ValueError) as e:
        error_msg = f"API documentation generation failed: {e}"
        if logger:
            logger.error(error_msg)
        raise


if __name__ == "__main__":
    main()
