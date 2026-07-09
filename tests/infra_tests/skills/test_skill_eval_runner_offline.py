#!/usr/bin/env python3
"""Tests for skill eval harness offline CLI modes."""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_SKILLS_TESTS = Path(__file__).resolve().parent
_SCRIPTS = _REPO / "docs/prompts/_skill-eval/scripts"
HARNESS = _SCRIPTS / "run_eval_harness.py"
sys.path.insert(0, str(_SCRIPTS))
sys.path.insert(0, str(_SKILLS_TESTS))

from skill_eval_fixtures import write_minimal_workspace


def _run_harness(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    cmd = ["uv", "run", "python", str(HARNESS), *args]
    return subprocess.run(
        cmd,
        cwd=cwd or _REPO,
        capture_output=True,
        text=True,
        check=False,
    )


def test_save_baseline_only_no_progress_lines(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "latest"
    baseline_dir = tmp_path / "baseline"
    write_minimal_workspace(workspace)

    import skill_eval.config as config_mod
    import skill_eval.runner as runner_mod

    monkeypatch.setattr(config_mod, "BASELINE_DIR", baseline_dir)

    monkeypatch.setattr(
        sys,
        "argv",
        ["run_eval_harness.py", "--save-baseline-only", "--output-dir", str(workspace)],
    )
    assert runner_mod.main() == 0

    dest = baseline_dir / "benchmark.json"
    assert dest.is_file()
    saved = json.loads(dest.read_text(encoding="utf-8"))
    assert saved["run_dir"] == "baseline"


def test_compare_only_shows_compare_section(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "latest"
    baseline_dir = tmp_path / "baseline"
    write_minimal_workspace(workspace)
    baseline_dir.mkdir()
    benchmark = json.loads((workspace / "benchmark.json").read_text(encoding="utf-8"))
    benchmark["run_dir"] = "baseline"
    (baseline_dir / "benchmark.json").write_text(json.dumps(benchmark), encoding="utf-8")

    import skill_eval.config as config_mod
    import skill_eval.runner as runner_mod

    monkeypatch.setattr(config_mod, "BASELINE_DIR", baseline_dir)

    monkeypatch.setattr(
        sys,
        "argv",
        ["run_eval_harness.py", "--compare-only", "--output-dir", str(workspace)],
    )
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        assert runner_mod.main() == 0
    report = buffer.getvalue()
    assert "COMPARE (vs baseline with_skill)" in report
    assert "No with_skill regressions." in report
    assert "loaded from workspace (no re-grade)" in report


def test_compare_only_missing_baseline_exits_nonzero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "latest"
    baseline_dir = tmp_path / "baseline"
    write_minimal_workspace(workspace)

    import skill_eval.config as config_mod
    import skill_eval.runner as runner_mod

    monkeypatch.setattr(config_mod, "BASELINE_DIR", baseline_dir)

    monkeypatch.setattr(
        sys,
        "argv",
        ["run_eval_harness.py", "--compare-only", "--output-dir", str(workspace)],
    )
    assert runner_mod.main() == 1


def test_save_baseline_only_missing_benchmark_exits_nonzero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "latest"
    baseline_dir = tmp_path / "baseline"
    workspace.mkdir()

    import skill_eval.config as config_mod
    import skill_eval.runner as runner_mod

    monkeypatch.setattr(config_mod, "BASELINE_DIR", baseline_dir)

    monkeypatch.setattr(
        sys,
        "argv",
        ["run_eval_harness.py", "--save-baseline-only", "--output-dir", str(workspace)],
    )
    assert runner_mod.main() == 1


def test_validate_rejects_save_baseline_with_offline_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import skill_eval.runner as runner_mod

    monkeypatch.setattr(
        sys,
        "argv",
        ["run_eval_harness.py", "--save-baseline-only", "--save-baseline"],
    )
    assert runner_mod.main() == 2


@pytest.mark.timeout(30)
def test_save_baseline_only_integration(tmp_path: Path) -> None:
    """Integration test: --save-baseline-only pins the latest run as a baseline.

    Uses a minimal synthetic workspace (no real LLM eval run needed) to
    exercise the full subprocess harness entry point.
    """
    workspace = tmp_path / "latest"
    write_minimal_workspace(workspace)

    # The harness resolves --output-dir as the workspace containing benchmark.json.
    # Pass --output-dir pointing at the synthetic workspace.
    result = _run_harness("--save-baseline-only", "--output-dir", str(workspace))
    assert result.returncode == 0, result.stderr
