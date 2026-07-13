"""Tests for evaluation runner."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.core.exceptions import BuildError, ValidationError
from infrastructure.sia.evaluation_runner import read_results_json, run_evaluation, write_results_json
from infrastructure.sia.models import EvaluationResult


def test_read_and_write_results_json(tmp_path: Path) -> None:
    path = tmp_path / "results.json"
    result = EvaluationResult(metric_name="accuracy", metric_value=0.75, n_samples=20)
    write_results_json(path, result)
    loaded = read_results_json(path)
    assert loaded.metric_name == "accuracy"
    assert loaded.metric_value == 0.75
    assert loaded.n_samples == 20


def test_run_evaluation_subprocess(tmp_path: Path) -> None:
    task_dir = tmp_path / "task"
    public = task_dir / "data" / "public"
    public.mkdir(parents=True)
    (task_dir / "data" / "private").mkdir(parents=True)
    evaluate = public / "evaluate.py"
    evaluate.write_text(
        """#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--gen-dir", required=True)
args = parser.parse_args()
gen = Path(args.gen_dir)
gen.mkdir(parents=True, exist_ok=True)
payload = {"metric_name": "accuracy", "metric_value": 0.9, "n_samples": 5}
(gen / "results.json").write_text(json.dumps(payload))
""",
        encoding="utf-8",
    )
    gen_dir = tmp_path / "gen_1"
    result = run_evaluation(evaluate, gen_dir=gen_dir, task_dir=task_dir)
    assert result.metric_value == 0.9


def test_run_evaluation_failure(tmp_path: Path) -> None:
    task_dir = tmp_path / "task"
    public = task_dir / "data" / "public"
    public.mkdir(parents=True)
    evaluate = public / "evaluate.py"
    evaluate.write_text("import sys\nsys.exit(2)\n", encoding="utf-8")
    with pytest.raises(BuildError, match="evaluate.py failed"):
        run_evaluation(evaluate, gen_dir=tmp_path / "gen", task_dir=task_dir)


def test_read_results_missing_keys(tmp_path: Path) -> None:
    path = tmp_path / "results.json"
    path.write_text(json.dumps({"metric_name": "acc"}), encoding="utf-8")
    with pytest.raises(ValidationError, match="missing keys"):
        read_results_json(path)


def test_to_dict_preserves_canonical_keys_over_extra() -> None:
    result = EvaluationResult(
        metric_name="accuracy",
        metric_value=0.5,
        n_samples=10,
        extra={"metric_name": "spoof", "metric_value": 0.0, "custom": "ok"},
    )
    payload = result.to_dict()
    assert payload["metric_name"] == "accuracy"
    assert payload["metric_value"] == 0.5
    assert payload["n_samples"] == 10
    assert payload["custom"] == "ok"
