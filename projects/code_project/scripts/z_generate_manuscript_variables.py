#!/usr/bin/env python3
"""Generate manuscript variables from config and computed results.

This script reads experimental configuration from config.yaml and computed results
from the analysis pipeline outputs, then produces a consolidated JSON file
(manuscript_variables.json) containing every quantitative value referenced
in the manuscript via {{PLACEHOLDER}} syntax.

It also performs variable substitution: reading manuscript/*.md template files,
replacing {{VARIABLE}} tokens with computed values, and writing the substituted
copies to output/manuscript/ for rendering.

This is the core of the "madlib" pattern — the manuscript files are templates,
and this script fills them in from real data.
"""

import csv
import hashlib
import json
import platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

# Project root: projects/code_project/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANUSCRIPT_DIR = PROJECT_ROOT / "manuscript"
OUTPUT_DIR = PROJECT_ROOT / "output"


def load_config() -> dict[str, Any]:
    """Load and return the project config.yaml."""
    config_path = MANUSCRIPT_DIR / "config.yaml"
    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}")
        return {}
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def load_optimization_results() -> list[dict[str, str]]:
    """Load optimization_results.csv into a list of row dicts."""
    csv_path = OUTPUT_DIR / "data" / "optimization_results.csv"
    if not csv_path.exists():
        logger.warning(f"Optimization results not found: {csv_path}")
        return []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_json_report(name: str) -> dict[str, Any]:
    """Load a JSON report from output/reports/."""
    report_path = OUTPUT_DIR / "reports" / name
    if not report_path.exists():
        logger.warning(f"Report not found: {report_path}")
        return {}
    with open(report_path, "r") as f:
        return json.load(f)


def compute_config_hash() -> str:
    """Compute SHA-256 hash of config.yaml for provenance tracking."""
    config_path = MANUSCRIPT_DIR / "config.yaml"
    if not config_path.exists():
        return "N/A"
    content = config_path.read_bytes()
    return hashlib.sha256(content).hexdigest()[:16]


def count_output_artifacts() -> dict[str, int]:
    """Count generated artifacts by category."""
    counts = {}
    for subdir in ["figures", "data", "reports"]:
        dir_path = OUTPUT_DIR / subdir
        if dir_path.exists():
            counts[subdir] = sum(1 for f in dir_path.iterdir() if f.is_file())
        else:
            counts[subdir] = 0
    return counts


def generate_variables() -> dict[str, str]:
    """Generate all manuscript variables from config and results.

    Returns:
        Dictionary mapping variable names to string values suitable for
        direct substitution into manuscript markdown.
    """
    config = load_config()
    results = load_optimization_results()
    stability = load_json_report("stability_analysis.json")
    benchmark = load_json_report("performance_benchmark.json")
    artifact_counts = count_output_artifacts()

    variables: dict[str, str] = {}

    # ---- Configuration-derived variables ----
    paper = config.get("paper", {})
    variables["CONFIG_TITLE"] = paper.get("title", "Untitled")
    variables["CONFIG_SUBTITLE"] = paper.get("subtitle", "")
    variables["CONFIG_VERSION"] = paper.get("version", "1.0")

    experiment = config.get("experiment", {})
    step_sizes = experiment.get("step_sizes", [0.01, 0.1, 0.5, 1.0, 1.5, 2.5])
    variables["CONFIG_NUM_STEP_SIZES"] = str(len(step_sizes))
    variables["CONFIG_STEP_SIZES_CSV"] = ", ".join(str(s) for s in step_sizes)
    variables["CONFIG_STEP_SIZES_MATH"] = ", ".join(
        f"\\\\alpha = {s}" for s in step_sizes
    )
    variables["CONFIG_MIN_STEP_SIZE"] = str(min(step_sizes))
    variables["CONFIG_MAX_STEP_SIZE"] = str(max(step_sizes))

    # Bullet list for methodology section (labels match optimization_analysis._agency_category)
    def _step_agency_label(alpha: float) -> str:
        if alpha < 0.3:
            return "conservative"
        if alpha <= 1.0:
            return "near-optimal"
        if alpha < 2.0:
            return "aggressive"
        return "divergent (expected unstable for H = I)"

    bullets = []
    for s in step_sizes:
        a = float(s)
        lbl = _step_agency_label(a)
        bullets.append(f"- $\\\\alpha = {a}$ ({lbl})")
    variables["CONFIG_STEP_SIZES_BULLETS"] = "\n".join(bullets)

    variables["CONFIG_INITIAL_POINT"] = str(experiment.get("initial_point", 0.0))
    variables["CONFIG_MAX_ITERATIONS"] = str(experiment.get("max_iterations", 100))
    variables["CONFIG_TOLERANCE"] = _format_sci(experiment.get("tolerance", 1e-6))
    variables["CONFIG_CONVERGENCE_TOL"] = _format_sci(
        experiment.get("convergence_tolerance", 1e-8)
    )

    # Quadratic problem parameters
    A = experiment.get("quadratic_A", [[1.0]])
    b = experiment.get("quadratic_b", [1.0])
    variables["CONFIG_QUADRATIC_A"] = str(A)
    variables["CONFIG_QUADRATIC_B"] = str(b)

    # Stability grid
    stability_starts = experiment.get(
        "stability_starting_points", [-50, -10, -5, 0, 0.1, 5, 10, 50]
    )
    stability_steps = experiment.get(
        "stability_step_sizes", [0.01, 0.05, 0.1, 0.2, 0.5, 0.9]
    )
    variables["CONFIG_NUM_STABILITY_STARTS"] = str(len(stability_starts))
    variables["CONFIG_NUM_STABILITY_STEPS"] = str(len(stability_steps))
    variables["CONFIG_STABILITY_CELLS"] = str(
        len(stability_starts) * len(stability_steps)
    )
    variables["CONFIG_STABILITY_MIN_STEP"] = str(min(stability_steps))
    variables["CONFIG_STABILITY_MAX_STEP"] = str(max(stability_steps))

    # Benchmark dimensions
    dims = experiment.get("benchmark_dimensions", [1, 2, 5, 10, 20, 50])
    variables["CONFIG_BENCHMARK_DIMS"] = ", ".join(str(d) for d in dims)
    variables["CONFIG_BENCHMARK_MIN_DIM"] = str(min(dims)) if dims else "1"
    variables["CONFIG_BENCHMARK_MAX_DIM"] = str(max(dims)) if dims else "50"

    # ---- Results-derived variables ----
    if results:
        # Compute analytical optimum from A and b
        A_np = np.array(A, dtype=float)
        b_np = np.array(b, dtype=float)
        x_star = np.linalg.solve(A_np, b_np)
        f_star = float(0.5 * x_star.T @ A_np @ x_star - b_np.T @ x_star)
        variables["RESULT_OPTIMUM_X"] = f"{x_star[0]:.1f}"
        variables["RESULT_OPTIMUM_F"] = f"{f_star:.1f}"

        # Parse CSV rows
        iterations_list = [int(r["iterations"]) for r in results]
        converged_list = [r["converged"] for r in results]

        variables["RESULT_MIN_ITERATIONS"] = str(min(iterations_list))
        variables["RESULT_MAX_ITERATIONS"] = str(max(iterations_list))
        variables["RESULT_AVG_ITERATIONS"] = f"{np.mean(iterations_list):.0f}"
        variables["RESULT_ALL_CONVERGED"] = (
            "Yes" if all(c == "True" for c in converged_list) else "No"
        )

        # Count converged vs total
        n_converged = sum(1 for c in converged_list if c == "True")
        variables["RESULT_NUM_CONVERGED"] = str(n_converged)
        variables["RESULT_CONVERGED_STEP_SIZES"] = ", ".join(
            r["step_size"] for r in results if r["converged"] == "True"
        )
        variables["RESULT_DIVERGED_STEP_SIZES"] = ", ".join(
            r["step_size"] for r in results if r["converged"] != "True"
        )

        # Build the results table rows
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

        # Convergence factors: for H=I quadratic, ρ = |1 - α|
        factor_bullets = []
        for r in results:
            alpha = float(r["step_size"])
            rho = abs(1 - alpha)
            if rho < 1 and rho > 0:
                iters_for_eps = int(np.ceil(np.log(1e-6) / np.log(rho)))
            else:
                iters_for_eps = 0
            if rho >= 1:
                status = "**divergent**"
            else:
                status = f"requiring ~{iters_for_eps} iterations for $\\\\epsilon = 10^{{-6}}$"
            factor_bullets.append(
                f"- $\\\\alpha = {alpha}$: "
                f"$\\\\rho \\\\approx {rho:.2f}$, "
                f"{status}"
            )
        variables["RESULT_CONVERGENCE_FACTORS"] = "\n".join(factor_bullets)

        # Best/worst step sizes
        best_idx = iterations_list.index(min(iterations_list))
        worst_idx = iterations_list.index(max(iterations_list))
        variables["RESULT_BEST_STEP_SIZE"] = str(
            float(results[best_idx]["step_size"])
        )
        variables["RESULT_WORST_STEP_SIZE"] = str(
            float(results[worst_idx]["step_size"])
        )
    else:
        logger.warning("No optimization results available — using fallback values")
        variables["RESULT_OPTIMUM_X"] = "N/A"
        variables["RESULT_OPTIMUM_F"] = "N/A"
        variables["RESULT_MIN_ITERATIONS"] = "N/A"
        variables["RESULT_MAX_ITERATIONS"] = "N/A"
        variables["RESULT_AVG_ITERATIONS"] = "N/A"
        variables["RESULT_ALL_CONVERGED"] = "N/A"
        variables["RESULT_TABLE_ROWS"] = "| N/A | N/A | N/A | N/A | N/A |"
        variables["RESULT_CONVERGENCE_FACTORS"] = "- No data available"
        variables["RESULT_BEST_STEP_SIZE"] = "N/A"
        variables["RESULT_WORST_STEP_SIZE"] = "N/A"
        variables["RESULT_NUM_CONVERGED"] = "N/A"
        variables["RESULT_CONVERGED_STEP_SIZES"] = "N/A"
        variables["RESULT_DIVERGED_STEP_SIZES"] = "N/A"

    # ---- Stability-derived variables ----
    variables["STABILITY_SCORE"] = f"{stability.get('stability_score', 0.0):.2f}"
    variables["STABILITY_FUNCTION"] = stability.get("function_name", "N/A")

    # ---- Benchmark-derived variables ----
    variables["BENCHMARK_AVG_TIME"] = (
        f"{benchmark.get('execution_time', 0.0) * 1e6:.1f}"
        if benchmark.get("execution_time")
        else "N/A"
    )

    # ---- Artifact counts ----
    variables["ARTIFACT_FIGURES"] = str(artifact_counts.get("figures", 0))
    variables["ARTIFACT_DATA_FILES"] = str(artifact_counts.get("data", 0))
    variables["ARTIFACT_REPORTS"] = str(artifact_counts.get("reports", 0))
    variables["ARTIFACT_TOTAL"] = str(sum(artifact_counts.values()))

    # ---- Provenance ----
    variables["CONFIG_HASH"] = compute_config_hash()
    variables["GENERATION_TIMESTAMP"] = datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    variables["PYTHON_VERSION"] = platform.python_version()
    variables["NUMPY_VERSION"] = np.__version__
    variables["PLATFORM"] = f"{platform.system()} {platform.machine()}"

    # ---- Author info from config ----
    authors = config.get("authors", [])
    if authors:
        variables["CONFIG_FIRST_AUTHOR"] = authors[0].get("name", "Unknown")
        variables["CONFIG_AUTHOR_COUNT"] = str(len(authors))
    else:
        variables["CONFIG_FIRST_AUTHOR"] = "Unknown"
        variables["CONFIG_AUTHOR_COUNT"] = "0"

    # ---- Keywords ----
    keywords = config.get("keywords", [])
    variables["CONFIG_KEYWORDS"] = ", ".join(keywords)

    logger.info(f"Generated {len(variables)} manuscript variables")
    return variables


def _format_sci(value: float) -> str:
    """Format a small float as LaTeX scientific notation, e.g. 1e-6 → 10^{-6}."""
    if value == 0:
        return "0"
    exp = int(np.floor(np.log10(abs(value))))
    coeff = value / (10 ** exp)
    if abs(coeff - 1.0) < 1e-9:
        return f"10^{{{exp}}}"
    return f"{coeff:.1f} \\\\times 10^{{{exp}}}"


def substitute_manuscript_files(variables: dict[str, str]) -> Path:
    """Read manuscript/*.md templates, substitute {{VARIABLES}}, write to output/manuscript/.

    Args:
        variables: Dict mapping variable names to replacement strings.

    Returns:
        Path to the output/manuscript/ directory containing substituted files.
    """
    output_manuscript_dir = OUTPUT_DIR / "manuscript"
    output_manuscript_dir.mkdir(parents=True, exist_ok=True)

    # Find all .md files in manuscript/ that are numbered sections or preamble
    md_files = sorted(MANUSCRIPT_DIR.glob("*.md"))

    substitution_count = 0
    unresolved_count = 0

    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        original = content

        # Replace all {{VARIABLE}} patterns
        def replacer(match: re.Match) -> str:
            var_name = match.group(1)
            if var_name in variables:
                return variables[var_name]
            logger.warning(
                f"Unresolved variable {{{{{var_name}}}}} in {md_file.name}"
            )
            return match.group(0)  # Leave unresolved

        content = re.sub(r"\{\{(\w+)\}\}", replacer, content)

        # Count substitutions
        subs = len(re.findall(r"\{\{(\w+)\}\}", original)) - len(
            re.findall(r"\{\{(\w+)\}\}", content)
        )
        substitution_count += subs
        unresolved_count += len(re.findall(r"\{\{(\w+)\}\}", content))

        # Write substituted version
        out_path = output_manuscript_dir / md_file.name
        out_path.write_text(content, encoding="utf-8")

    logger.info(
        f"Substituted {substitution_count} variables across {len(md_files)} files"
    )
    if unresolved_count > 0:
        logger.warning(f"{unresolved_count} unresolved {{{{VARIABLE}}}} placeholder(s) remain")

    # Copy auxiliary files needed for compilation (e.g., config for title page, bibliography)
    import shutil
    for aux_file in ["config.yaml", "references.bib"]:
        aux_path = MANUSCRIPT_DIR / aux_file
        if aux_path.exists():
            shutil.copy2(aux_path, output_manuscript_dir / aux_file)
            logger.debug(f"Copied {aux_file} to {output_manuscript_dir.name}/")

    return output_manuscript_dir


def save_variables(variables: dict[str, str]) -> Path:
    """Save manuscript variables to JSON."""
    output_path = OUTPUT_DIR / "data" / "manuscript_variables.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(variables, f, indent=2, sort_keys=True)
    logger.info(f"Saved {len(variables)} variables to {output_path}")
    return output_path


def main():
    """Generate variables, save JSON, and substitute into manuscript copies."""
    logger.info("Generating manuscript variables...")
    variables = generate_variables()
    save_variables(variables)
    output_dir = substitute_manuscript_files(variables)
    logger.info(f"Substituted manuscript files written to: {output_dir}")
    return variables


if __name__ == "__main__":
    main()
