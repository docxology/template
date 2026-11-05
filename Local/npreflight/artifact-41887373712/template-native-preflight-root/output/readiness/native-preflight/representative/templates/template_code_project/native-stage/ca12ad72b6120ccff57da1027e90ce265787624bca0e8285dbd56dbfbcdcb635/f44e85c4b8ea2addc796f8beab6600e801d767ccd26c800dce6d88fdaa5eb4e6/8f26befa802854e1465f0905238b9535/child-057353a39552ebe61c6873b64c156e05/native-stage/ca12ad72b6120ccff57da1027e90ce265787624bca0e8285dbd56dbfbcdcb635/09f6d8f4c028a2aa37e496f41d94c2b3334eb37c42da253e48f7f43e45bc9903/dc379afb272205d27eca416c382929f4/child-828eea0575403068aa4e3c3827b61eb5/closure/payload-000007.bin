"""Pure mathematical core and shared configuration for the code project.

This cluster keeps the infrastructure-independent mathematics and the
single experiment-configuration loader:

* :mod:`template_code_project.core.optimizer` — pure gradient-descent
  primitives (no I/O, no ``infrastructure.*`` imports).
* :mod:`template_code_project.core.invariants` — numerical invariant
  builders evaluated against real optimizer runs.
* :mod:`template_code_project.core.sweeps` — shared α-sweep and
  stability-matrix helpers for figures, dashboard, and invariants.
* :mod:`template_code_project.core.experiment_config` — single typed
  loader for ``manuscript/config.yaml`` → ``experiment:``.
* :mod:`template_code_project.core.project_paths` — project-root and
  output-directory resolution shared by analysis, figures, dashboard.
* :mod:`template_code_project.core.benchmark_support` — deterministic
  rubric demo for ``infrastructure.benchmark``.
* :mod:`template_code_project.core.manuscript_variables` — flat
  ``{{TOKEN}}`` substitution map for manuscript rendering.
* :mod:`template_code_project.core.documentation` — static API reference
  markdown for the exemplar.
"""

# NOTE: ``benchmark_support`` is intentionally NOT imported eagerly. It is a declared
# infrastructure adapter (see ``manuscript/layer_contract.yaml``) and hard-imports
# ``infrastructure.benchmark`` at module level; importing it here would make
# ``import template_code_project`` fail without the monorepo on ``sys.path``.
# Import it directly:
# ``from template_code_project.core.benchmark_support import run_quadratic_benchmark``.

from .documentation import (
    API_REFERENCE_TEMPLATE,
    build_api_reference_markdown,
)
from .experiment_config import ExperimentConfig, load_experiment_config
from .invariants import (
    InvariantResult,
    OptimizerSweepConfig,
    all_invariants,
    convergence_invariants,
    gradient_consistency_invariants,
    trajectory_invariants,
)
from .manuscript_variables import generate_variables, save_variables
from .optimizer import (
    OptimizationResult,
    compute_gradient,
    gradient_descent,
    make_quadratic_problem,
    quadratic_function,
    quadratic_optimum,
    simulate_trajectory,
)
from .project_paths import (
    project_output_dirs,
    project_root_context,
    resolve_project_root,
)
from .sweeps import (
    AlphaSweepConfig,
    AlphaSweepResult,
    DEFAULT_SENSITIVITY_ALPHAS,
    run_alpha_sweep,
    sensitivity_sweep,
    stability_error_matrix,
)

__all__ = [
    "AlphaSweepConfig",
    "AlphaSweepResult",
    "API_REFERENCE_TEMPLATE",
    "DEFAULT_SENSITIVITY_ALPHAS",
    "ExperimentConfig",
    "InvariantResult",
    "OptimizationResult",
    "OptimizerSweepConfig",
    "all_invariants",
    "build_api_reference_markdown",
    "compute_gradient",
    "convergence_invariants",
    "generate_variables",
    "gradient_consistency_invariants",
    "gradient_descent",
    "load_experiment_config",
    "make_quadratic_problem",
    "project_output_dirs",
    "project_root_context",
    "quadratic_function",
    "quadratic_optimum",
    "resolve_project_root",
    "run_alpha_sweep",
    "save_variables",
    "sensitivity_sweep",
    "simulate_trajectory",
    "stability_error_matrix",
    "trajectory_invariants",
]
