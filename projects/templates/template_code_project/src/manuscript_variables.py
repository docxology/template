"""Manuscript variable generation for the template_code_project exemplar.

Reads:
- ``manuscript/config.yaml``          — experiment parameters and paper metadata
- ``output/data/optimization_results.csv``  — per-step-size convergence data
- ``output/reports/stability_analysis.json``
- ``output/reports/performance_benchmark.json``

Returns a flat ``dict[str, str]`` of UPPERCASE_KEY → value for
``{{TOKEN}}`` substitution via
:func:`infrastructure.rendering.manuscript_injection.write_resolved_manuscript_tree`.

Called exclusively by ``scripts/z_generate_manuscript_variables.py``
(thin orchestrator).
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import yaml

try:
    from .experiment_config import load_experiment_config
    from .optimizer import quadratic_optimum
except ImportError:  # pragma: no cover
    from experiment_config import load_experiment_config  # type: ignore[no-redef]
    from optimizer import quadratic_optimum  # type: ignore[no-redef]

from ._runtime import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# I/O helpers — thin readers, no business logic
# ---------------------------------------------------------------------------


def _load_config(project_root: Path) -> dict[str, Any]:
    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.exists():
        logger.warning("Config file not found: %s", config_path)
        return {}
    with config_path.open("r") as f:
        return yaml.safe_load(f) or {}


def _load_optimization_results(project_root: Path) -> list[dict[str, str]]:
    csv_path = project_root / "output" / "data" / "optimization_results.csv"
    if not csv_path.exists():
        logger.warning("Optimization results not found: %s", csv_path)
        return []
    with csv_path.open("r") as f:
        return list(csv.DictReader(f))


def _load_json_report(project_root: Path, name: str) -> dict[str, Any]:
    report_path = project_root / "output" / "reports" / name
    if not report_path.exists():
        logger.warning("Report not found: %s", report_path)
        return {}
    with report_path.open("r") as f:
        result: dict[str, Any] = json.load(f)
        return result


def _compute_config_hash(project_root: Path) -> str:
    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.exists():
        return "N/A"
    return hashlib.sha256(config_path.read_bytes()).hexdigest()[:16]


def _count_output_artifacts(project_root: Path) -> dict[str, int]:
    """Count generated artifacts by category (publication-quality only)."""
    _SUFFIXES: dict[str, set[str]] = {
        "figures": {".png", ".pdf", ".svg", ".jpg", ".jpeg"},
        "data": {".csv", ".npz", ".json", ".parquet"},
        "reports": {".json", ".md", ".html", ".txt"},
    }
    counts: dict[str, int] = {}
    output_dir = project_root / "output"
    for subdir, suffixes in _SUFFIXES.items():
        dir_path = output_dir / subdir
        if dir_path.exists():
            counts[subdir] = sum(1 for f in dir_path.iterdir() if f.is_file() and f.suffix.lower() in suffixes)
        else:
            counts[subdir] = 0
    return counts


# ---------------------------------------------------------------------------
# Pure computation helpers
# ---------------------------------------------------------------------------


def _format_sci(value: float) -> str:
    """Format a small float as LaTeX scientific notation, e.g. ``1e-6`` → ``10^{-6}``."""
    if value == 0:
        return "0"
    exp = int(np.floor(np.log10(abs(value))))
    coeff = value / (10**exp)
    if abs(coeff - 1.0) < 1e-9:
        return f"10^{{{exp}}}"
    return f"{coeff:.1f} \\times 10^{{{exp}}}"


def _step_agency_label(alpha: float) -> str:
    if alpha < 0.3:
        return "conservative"
    if alpha <= 1.0:
        return "near-optimal"
    if alpha < 2.0:
        return "aggressive"
    return "divergent (expected unstable for H = I)"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_variables(project_root: Path, *, require_analysis_outputs: bool = False) -> dict[str, str]:
    """Generate all manuscript variables from config and analysis outputs.

    Reads ``manuscript/config.yaml`` and analysis outputs from ``output/``.
    Returns a flat mapping of UPPERCASE_KEY → string value for ``{{TOKEN}}``
    substitution.  When data files are absent and *require_analysis_outputs*
    is False (draft mode), fallback sentinel values (``"N/A"``) are used so the
    manuscript renders without crashing.  Pipeline callers should pass
    ``require_analysis_outputs=True`` so missing analysis outputs fail before
    render.

    Args:
        project_root: Root directory of the code project (the directory
            containing ``manuscript/`` and ``output/``).
        require_analysis_outputs: When True, raise if
            ``output/data/optimization_results.csv`` is missing or empty.

    Returns:
        ``dict[str, str]`` with plain UPPERCASE_KEY keys (no surrounding
        braces), ready for
        :func:`infrastructure.rendering.manuscript_injection.write_resolved_manuscript_tree`.
    """
    config = _load_config(project_root)
    exp_cfg = load_experiment_config(project_root)
    results = _load_optimization_results(project_root)
    if require_analysis_outputs and not results:
        csv_path = project_root / "output" / "data" / "optimization_results.csv"
        raise FileNotFoundError(
            f"Analysis outputs required but missing or empty: {csv_path}. "
            "Run projects/templates/template_code_project/scripts/optimization_analysis.py first."
        )
    stability = _load_json_report(project_root, "stability_analysis.json")
    benchmark = _load_json_report(project_root, "performance_benchmark.json")
    artifact_counts = _count_output_artifacts(project_root)

    variables: dict[str, str] = {}

    # ---- Configuration-derived ----
    paper = config.get("paper", {})
    variables["CONFIG_VERSION"] = paper.get("version", "1.0")

    step_sizes = list(exp_cfg.step_sizes)
    variables["CONFIG_NUM_STEP_SIZES"] = str(len(step_sizes))
    variables["CONFIG_STEP_SIZES_CSV"] = ", ".join(str(s) for s in step_sizes)
    variables["CONFIG_MIN_STEP_SIZE"] = str(min(step_sizes))
    variables["CONFIG_MAX_STEP_SIZE"] = str(max(step_sizes))

    bullets = [f"- $\\alpha = {float(s)}$ ({_step_agency_label(float(s))})" for s in step_sizes]
    variables["CONFIG_STEP_SIZES_BULLETS"] = "\n".join(bullets)

    variables["CONFIG_INITIAL_POINT"] = str(exp_cfg.initial_point)
    variables["CONFIG_MAX_ITERATIONS"] = str(exp_cfg.max_iterations)
    variables["CONFIG_TOLERANCE"] = _format_sci(float(exp_cfg.tolerance))
    variables["CONFIG_CONVERGENCE_TOL"] = _format_sci(float(exp_cfg.convergence_tolerance))

    variables["CONFIG_QUADRATIC_A"] = str(list(exp_cfg.quadratic_A))
    variables["CONFIG_QUADRATIC_B"] = str(list(exp_cfg.quadratic_b))

    stability_starts = list(exp_cfg.stability_starting_points)
    stability_steps = list(exp_cfg.stability_step_sizes)
    variables["CONFIG_NUM_STABILITY_STARTS"] = str(len(stability_starts))
    variables["CONFIG_NUM_STABILITY_STEPS"] = str(len(stability_steps))
    variables["CONFIG_STABILITY_CELLS"] = str(len(stability_starts) * len(stability_steps))
    variables["CONFIG_STABILITY_MIN_STEP"] = str(min(stability_steps))
    variables["CONFIG_STABILITY_MAX_STEP"] = str(max(stability_steps))

    dims = list(exp_cfg.benchmark_dimensions)
    variables["CONFIG_BENCHMARK_DIMS"] = ", ".join(str(d) for d in dims)
    variables["CONFIG_BENCHMARK_MIN_DIM"] = str(min(dims)) if dims else "1"
    variables["CONFIG_BENCHMARK_MAX_DIM"] = str(max(dims)) if dims else "50"

    # ---- Results-derived ----
    if results:
        x_star, f_star = quadratic_optimum(exp_cfg.A_array(), exp_cfg.b_array())
        variables["RESULT_OPTIMUM_X"] = f"{x_star[0]:.1f}"
        variables["RESULT_OPTIMUM_F"] = f"{f_star:.1f}"

        iterations_list = [int(r["iterations"]) for r in results]
        converged_list = [r["converged"] for r in results]

        variables["RESULT_MIN_ITERATIONS"] = str(min(iterations_list))
        variables["RESULT_MAX_ITERATIONS"] = str(max(iterations_list))
        variables["RESULT_AVG_ITERATIONS"] = f"{np.mean(iterations_list):.0f}"
        variables["RESULT_ALL_CONVERGED"] = "Yes" if all(c == "True" for c in converged_list) else "No"

        n_converged = sum(1 for c in converged_list if c == "True")
        variables["RESULT_NUM_CONVERGED"] = str(n_converged)
        variables["RESULT_CONVERGED_STEP_SIZES"] = ", ".join(
            r["step_size"] for r in results if r["converged"] == "True"
        )
        variables["RESULT_DIVERGED_STEP_SIZES"] = ", ".join(r["step_size"] for r in results if r["converged"] != "True")

        table_rows = []
        for r in results:
            sol = float(r["solution"])
            obj = float(r["objective_value"])
            iters = int(r["iterations"])
            conv = "Yes" if r["converged"] == "True" else "No"
            table_rows.append(
                f"| {float(r['step_size']):.2f}          "
                f"| {sol:.4f}         "
                f"| {obj:.4f}          "
                f"| {iters:<10} "
                f"| {conv:<9} |"
            )
        variables["RESULT_TABLE_ROWS"] = "\n".join(table_rows)

        factor_bullets = []
        for r in results:
            alpha = float(r["step_size"])
            rho = abs(1 - alpha)
            if 0 < rho < 1:
                iters_for_eps = int(np.ceil(np.log(1e-6) / np.log(rho)))
                status = f"requiring ~{iters_for_eps} iterations for $\\epsilon = 10^{{-6}}$"
            elif rho >= 1:
                status = "**divergent**"
            else:
                status = "converges in one step ($\\rho = 0$)"
            factor_bullets.append(f"- $\\alpha = {alpha}$: $\\rho \\approx {rho:.2f}$, {status}")
        variables["RESULT_CONVERGENCE_FACTORS"] = "\n".join(factor_bullets)

        best_idx = iterations_list.index(min(iterations_list))
        worst_idx = iterations_list.index(max(iterations_list))
        variables["RESULT_BEST_STEP_SIZE"] = str(float(results[best_idx]["step_size"]))
        variables["RESULT_WORST_STEP_SIZE"] = str(float(results[worst_idx]["step_size"]))
    else:
        logger.warning("No optimization results available — using fallback sentinel values")
        for key in (
            "RESULT_OPTIMUM_X",
            "RESULT_OPTIMUM_F",
            "RESULT_MIN_ITERATIONS",
            "RESULT_MAX_ITERATIONS",
            "RESULT_AVG_ITERATIONS",
            "RESULT_ALL_CONVERGED",
            "RESULT_NUM_CONVERGED",
            "RESULT_CONVERGED_STEP_SIZES",
            "RESULT_DIVERGED_STEP_SIZES",
            "RESULT_BEST_STEP_SIZE",
            "RESULT_WORST_STEP_SIZE",
        ):
            variables[key] = "N/A"
        variables["RESULT_TABLE_ROWS"] = "| N/A | N/A | N/A | N/A | N/A |"
        variables["RESULT_CONVERGENCE_FACTORS"] = "- No data available"

    # ---- Stability-derived ----
    variables["STABILITY_SCORE"] = f"{float(stability.get('stability_score', 0.0)):.2f}"
    variables["STABILITY_FUNCTION"] = str(stability.get("function_name", "N/A"))

    # ---- Benchmark-derived ----
    exec_time = benchmark.get("execution_time")
    variables["BENCHMARK_AVG_TIME"] = f"{float(exec_time) * 1e6:.1f}" if exec_time else "N/A"

    # ---- Artifact counts ----
    variables["ARTIFACT_FIGURES"] = str(artifact_counts.get("figures", 0))
    variables["ARTIFACT_DATA_FILES"] = str(artifact_counts.get("data", 0))
    variables["ARTIFACT_REPORTS"] = str(artifact_counts.get("reports", 0))
    variables["ARTIFACT_TOTAL"] = str(sum(artifact_counts.values()))

    # ---- Provenance ----
    variables["CONFIG_HASH"] = _compute_config_hash(project_root)
    variables["GENERATION_TIMESTAMP"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    variables["PYTHON_VERSION"] = platform.python_version()
    variables["NUMPY_VERSION"] = np.__version__
    variables["PLATFORM"] = f"{platform.system()} {platform.machine()}"

    # ---- Author / keyword metadata ----
    authors = config.get("authors", [])
    variables["CONFIG_FIRST_AUTHOR"] = authors[0].get("name", "Unknown") if authors else "Unknown"
    variables["CONFIG_KEYWORDS"] = ", ".join(config.get("keywords", []))

    logger.info("Generated %d manuscript variables", len(variables))
    return variables


def save_variables(variables: dict[str, str], output_path: Path) -> Path:
    """Persist *variables* as JSON for downstream rendering and debugging.

    Args:
        variables: The flat UPPERCASE_KEY → value mapping from
            :func:`generate_variables`.
        output_path: Destination ``.json`` file (parent is created if absent).

    Returns:
        Resolved path to the written file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(variables, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Saved %d variables to %s", len(variables), output_path)
    return output_path
