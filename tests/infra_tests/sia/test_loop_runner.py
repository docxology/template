"""Tests for SIA loop runner with fixture replay."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from infrastructure.core.exceptions import ValidationError
from infrastructure.sia.loop_runner import run_sia_loop
from infrastructure.sia.models import RunConfig
from infrastructure.sia.task_layout import validate_task_dir


def _write_task(task_dir: Path) -> None:
    public = task_dir / "data" / "public"
    private = task_dir / "data" / "private"
    reference = task_dir / "reference"
    public.mkdir(parents=True)
    private.mkdir(parents=True)
    reference.mkdir(parents=True)
    (public / "task.md").write_text("# Mini classify\n", encoding="utf-8")
    (public / "train.csv").write_text("feature_0,label\n1,a\n0,b\n", encoding="utf-8")
    (private / "labels.csv").write_text("id,label\n0,a\n1,b\n", encoding="utf-8")
    (reference / "reference_target_agent.py").write_text(
        "#!/usr/bin/env python3\nprint('ref')\n",
        encoding="utf-8",
    )
    (public / "evaluate.py").write_text(
        """#!/usr/bin/env python3
import argparse, json
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('--gen-dir', required=True)
args = p.parse_args()
Path(args.gen_dir).mkdir(parents=True, exist_ok=True)
(Path(args.gen_dir) / 'results.json').write_text(json.dumps({
    'metric_name': 'accuracy', 'metric_value': 0.5, 'n_samples': 2
}))
""",
        encoding="utf-8",
    )


def _write_fixtures(fixtures_dir: Path, generations: int = 3) -> None:
    for gen in range(1, generations + 1):
        root = fixtures_dir / f"gen_{gen}"
        root.mkdir(parents=True)
        (root / "target_agent.py").write_text(f"# gen {gen}\n", encoding="utf-8")
        (root / "agent_execution.json").write_text(
            json.dumps({"generation": gen, "returncode": 0}),
            encoding="utf-8",
        )
        (root / "results.json").write_text(
            json.dumps({"metric_name": "accuracy", "metric_value": 0.5 + gen * 0.1, "n_samples": 2}),
            encoding="utf-8",
        )
        if gen > 1:
            (root / "improvement.md").write_text(f"Improve gen {gen}\n", encoding="utf-8")


def test_run_sia_loop_fixture_replay(tmp_path: Path) -> None:
    task_dir = tmp_path / "tasks" / "mini"
    _write_task(task_dir)
    fixtures = tmp_path / "fixtures"
    _write_fixtures(fixtures)
    output = tmp_path / "output"
    config = RunConfig(
        task_dir=task_dir,
        output_dir=output,
        run_id=1,
        max_generations=3,
        live=False,
        fixtures_dir=fixtures,
    )
    artifacts = run_sia_loop(config)
    assert len(artifacts) == 3
    assert artifacts[-1].evaluation is not None
    assert artifacts[-1].evaluation.metric_value == pytest.approx(0.8)
    summary = output / "runs" / "run_1" / "run_summary.json"
    assert summary.is_file()
    context = output / "runs" / "run_1" / "context.md"
    context_text = context.read_text(encoding="utf-8")
    assert "Generation 3" in context_text
    assert context_text.count("## Generation 1") == 1
    assert context_text.count("## Generation 2") == 1
    assert context_text.count("## Generation 3") == 1


def test_run_sia_loop_missing_fixtures(tmp_path: Path) -> None:
    task_dir = tmp_path / "task"
    _write_task(task_dir)
    config = RunConfig(
        task_dir=task_dir,
        output_dir=tmp_path / "output",
        live=False,
        fixtures_dir=tmp_path / "missing",
    )
    with pytest.raises(ValidationError, match="Missing fixture"):
        run_sia_loop(config)
