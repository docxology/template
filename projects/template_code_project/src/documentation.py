"""API documentation generation for template_code_project."""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.documentation.glossary_gen import build_api_index, generate_markdown_table

logger = get_logger(__name__)

API_REFERENCE_TEMPLATE = """# Code Project API Reference

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

### compute_gradient(x, A=None, b=None)

Compute analytical gradient of quadratic function ∇f(x) = A x - b.

### gradient_descent(initial_point, objective_func, gradient_func, ...)

Perform gradient descent optimization with fixed step size.
"""


def build_api_reference_markdown() -> str:
    """Return markdown API reference for the optimization exemplar."""
    return API_REFERENCE_TEMPLATE


def run_api_doc_generation(project_root: Path) -> dict[str, str | None] | None:
    """Generate glossary-style API index and static API reference markdown."""
    output_dir = project_root / "output" / "docs"
    output_dir.mkdir(parents=True, exist_ok=True)

    glossary_path = None
    try:
        src_dir = project_root / "src"
        entries = build_api_index(str(src_dir))
        glossary_path = output_dir / "api_glossary.md"
        glossary_path.write_text(generate_markdown_table(entries), encoding="utf-8")
    except (OSError, ImportError, ValueError, SyntaxError) as exc:
        logger.warning("API index generation failed: %s", exc)

    api_ref_path = output_dir / "api_reference.md"
    api_ref_path.write_text(build_api_reference_markdown(), encoding="utf-8")

    return {
        "api_reference": str(api_ref_path),
        "glossary": str(glossary_path) if glossary_path and glossary_path.exists() else None,
    }
