"""Load persisted harness run state from a workspace directory."""

from __future__ import annotations

import json
from pathlib import Path


def load_benchmark(workspace: Path) -> dict:
    """Read benchmark.json from a harness workspace."""
    benchmark_path = workspace / "benchmark.json"
    if not benchmark_path.is_file():
        msg = f"Missing benchmark.json in {workspace}. Run the harness first or pass --output-dir to an existing run."
        raise FileNotFoundError(msg)
    return json.loads(benchmark_path.read_text(encoding="utf-8"))


def load_gradings_by_eval(workspace: Path) -> dict[str, dict[str, dict]]:
    """Rebuild gradings_by_eval from per-eval grading.json files."""
    gradings: dict[str, dict[str, dict]] = {}

    for eval_dir in sorted(p for p in workspace.iterdir() if p.is_dir()):
        meta_path = eval_dir / "eval_metadata.json"
        if not meta_path.is_file():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        eval_name = meta["eval_name"]
        gradings.setdefault(eval_name, {})

        for mode in ("with_skill", "without_skill"):
            grading_path = eval_dir / mode / "grading.json"
            if not grading_path.is_file():
                continue
            grading = json.loads(grading_path.read_text(encoding="utf-8"))
            grading["negative"] = meta.get("negative", False)
            gradings[eval_name][mode] = grading

    return gradings


def load_workspace_state(workspace: Path) -> tuple[dict, dict[str, dict[str, dict]]]:
    """Load benchmark and gradings from a harness workspace."""
    return load_benchmark(workspace), load_gradings_by_eval(workspace)
