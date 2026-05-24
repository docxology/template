"""Shared fixtures for skill eval harness tests."""

from __future__ import annotations

import json
from pathlib import Path


def write_minimal_workspace(workspace: Path) -> None:
    benchmark = {
        "skill_name": "template-workflows",
        "run_dir": "latest",
        "configurations": [
            {
                "name": "with_skill",
                "evals": [{"eval_name": "analysis-fast-fail", "pass_rate": 1.0, "passed": 4, "total": 4}],
            },
            {
                "name": "without_skill",
                "evals": [{"eval_name": "analysis-fast-fail", "pass_rate": 0.75, "passed": 3, "total": 4}],
            },
        ],
        "summary": {
            "with_skill_mean_pass_rate": 1.0,
            "without_skill_mean_pass_rate": 0.75,
            "with_skill_positive_only_pass_rate": 1.0,
            "without_skill_positive_only_pass_rate": 0.75,
            "delta_pass_rate": 0.25,
            "delta_positive_only_pass_rate": 0.25,
            "positive_eval_count": 1,
            "negative_eval_count": 0,
        },
    }
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "benchmark.json").write_text(json.dumps(benchmark), encoding="utf-8")

    eval_dir = workspace / "analysis-fast-fail"
    eval_dir.mkdir()
    meta = {
        "eval_id": 1,
        "eval_name": "analysis-fast-fail",
        "prompt": "Fix analysis failure",
        "expectations": ["Mentions Project Analysis"],
        "negative": False,
    }
    (eval_dir / "eval_metadata.json").write_text(json.dumps(meta), encoding="utf-8")

    for mode, passed, total in (("with_skill", 4, 4), ("without_skill", 3, 4)):
        mode_dir = eval_dir / mode
        (mode_dir / "outputs").mkdir(parents=True)
        (mode_dir / "outputs" / "response.md").write_text("response", encoding="utf-8")
        grading = {
            "summary": {"passed": passed, "total": total, "pass_rate": passed / total},
            "expectations": [{"text": "Mentions Project Analysis", "passed": passed == total}],
        }
        (mode_dir / "grading.json").write_text(json.dumps(grading), encoding="utf-8")
