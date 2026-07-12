#!/usr/bin/env python3
"""Thin orchestrator: run the infra-backed benchmark and write artifacts.

Demonstrates ``infrastructure.benchmark`` from inside the code exemplar. All
computation lives in ``src/benchmark_support.py``; this script only handles
I/O — writing a canonical JSON report and a deterministic objective-value
figure, then printing artifact paths for manifest collection.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
for _path in (PROJECT_ROOT, PROJECT_ROOT / "src", PROJECT_ROOT.parents[2]):
    path_text = str(_path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

from src.benchmark_support import (  # noqa: E402
    benchmark_payload,
    run_quadratic_benchmark,
    write_benchmark_report,
)
from src.project_paths import project_output_dirs  # noqa: E402


def main() -> int:
    """Run the benchmark stage and emit a report (+ optional figure)."""
    output_dirs = project_output_dirs(PROJECT_ROOT)
    report_path = output_dirs["reports"] / "benchmark_report.json"
    figure_path = output_dirs["figures"] / "benchmark_timings.png"

    run = run_quadratic_benchmark()
    write_benchmark_report(run, report_path)
    print(str(report_path))

    payload = benchmark_payload(run)
    sizes = [m["input_size"] for m in payload["measurements"]]
    objectives = [m["objective_value"] for m in payload["measurements"]]

    try:
        import matplotlib.pyplot as plt

        figure_path.parent.mkdir(parents=True, exist_ok=True)
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.plot(sizes, objectives, marker="o")
        ax.set_xlabel("input size")
        ax.set_ylabel("objective value")
        ax.set_title("quadratic_function deterministic outputs")
        fig.tight_layout()
        fig.savefig(figure_path, dpi=120)
        plt.close(fig)
        print(str(figure_path))
    except Exception as exc:  # pragma: no cover - figure is optional
        print(f"benchmark figure skipped: {exc}", file=sys.stderr)

    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
