#!/usr/bin/env python3
"""Thin orchestrator: compile the example methods, validate, export, and figure.

Follows the thin-orchestrator contract: all computation lives in
``src.methods_dsl``; this script only calls the tested library, writes
deterministic export/report artifacts, draws one figure with a headless
matplotlib backend, and prints every output path for manifest collection.

Run from the monorepo root::

    uv run python projects/templates/template_methods_paper/scripts/methods_analysis.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Headless backend MUST be set before importing pyplot.
os.environ.setdefault("MPLBACKEND", "Agg")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
for _path in (PROJECT_ROOT, PROJECT_ROOT / "src", PROJECT_ROOT.parents[2]):
    text = str(_path)
    if text not in sys.path:
        sys.path.insert(0, text)

import matplotlib.pyplot as plt  # noqa: E402

from infrastructure.documentation.generated_figure_registry import (  # noqa: E402
    write_generated_figure_registry,
)
from src.figure_specs import FIGURE_REGISTRY_SCHEMA, METHODS_FIGURE_SPECS  # noqa: E402
from src.methods_dsl import (  # noqa: E402
    all_example_methods,
    compile_method,
    demo_chain_report,
    run_all_gates,
    write_all_exports,
    write_json_report,
)
from src.project_paths import project_output_dirs  # noqa: E402


def run_methods_analysis(project_root: Path | None = None) -> list[Path]:
    """Compile every example method, export artifacts, and return written paths.

    Args:
        project_root: Optional project root override (used by tests with a
            temporary directory). Defaults to the real project root.

    Returns:
        Paths to every artifact written (exports + figure + reports).
    """
    dirs = project_output_dirs(project_root)
    figures_dir, data_dir, reports_dir = dirs["figures"], dirs["data"], dirs["reports"]

    written: list[Path] = []
    compiled_plans: list[dict[str, object]] = []
    gate_counts = {"total_gates_run": 0, "total_gates_passed": 0}
    step_counts: list[tuple[str, int]] = []

    for method in all_example_methods():
        gate_results = run_all_gates(method)
        gate_counts["total_gates_run"] += len(gate_results)
        gate_counts["total_gates_passed"] += sum(1 for g in gate_results if g.passed)

        plan = compile_method(method)
        step_counts.append((method.name, len(plan.steps)))
        compiled_plans.append(
            {
                "method_name": plan.method_name,
                "method_version": plan.method_version,
                "target": plan.target,
                "plan_hash": plan.plan_hash,
                "step_count": len(plan.steps),
            }
        )
        written.extend(write_all_exports(plan, data_dir))

    written.append(write_json_report(compiled_plans, data_dir / "compiled_plans.json"))
    written.append(write_json_report(gate_counts, reports_dir / "gate_report.json"))
    written.append(write_json_report(demo_chain_report(), reports_dir / "trust_chain_report.json"))

    figures_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots()
    ax.bar([name for name, _ in step_counts], [count for _, count in step_counts])
    ax.set_title("Steps per example method")
    ax.set_ylabel("step count")
    fig_path = figures_dir / METHODS_FIGURE_SPECS[0].filename
    fig.savefig(fig_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    written.append(fig_path)

    registry_path = write_generated_figure_registry(
        figures_dir / "figure_registry.json",
        METHODS_FIGURE_SPECS,
        [fig_path],
        schema_version=FIGURE_REGISTRY_SCHEMA,
    )
    written.append(registry_path)

    return written


def main() -> None:
    """CLI entry point."""
    for path in run_methods_analysis():
        print(path)


if __name__ == "__main__":
    main()
