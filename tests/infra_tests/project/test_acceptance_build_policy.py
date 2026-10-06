"""Measured candidate clocks reach actual outside-checkout acceptance children."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.core.testing.project_test_matrix import ProjectTestTask, run_project_test_matrix
from infrastructure.project.installed_acceptance_worker import _environment
from infrastructure.project.public_acceptance_evidence import cell_environment

ROOT = Path(__file__).resolve().parents[3]
KEYS = ("SOURCE_DATE_EPOCH", "TEMPLATE_BUILD_EPOCH_SOURCE", "TEMPLATE_EXECUTION_MODE")


@pytest.mark.timeout(45)
@pytest.mark.parametrize("installed", [False, True])
def test_measured_candidate_epoch_is_transported_to_real_export_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, installed: bool
) -> None:
    # Remove the infrastructure-suite reference clock: this case measures the
    # nominated candidate and never presents the fixture epoch as Git evidence.
    for name in (*KEYS, "TEMPLATE_DETERMINISTIC"):
        monkeypatch.delenv(name, raising=False)
    environment = {name: value for name, value in os.environ.items() if not name.startswith("GIT_")}
    candidate = subprocess.run(
        ["git", "show", "-s", "--format=%H%n%ct", "HEAD"],
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout.splitlines()
    selected = Path(sys.executable)
    prepared = (
        _environment(selected, tmp_path, repo_root=ROOT)
        if installed
        else cell_environment(selected, tmp_path, repo_root=ROOT)
    )
    expected = dict(zip(KEYS, (candidate[1], "git:" + candidate[0], "core"), strict=True))
    assert {name: prepared[name] for name in KEYS} == expected
    exported = tmp_path / "exported"
    exported.mkdir()
    observed = run_project_test_matrix(
        [
            ProjectTestTask(
                0,
                "candidate-clock",
                (
                    sys.executable,
                    "-I",
                    "-c",
                    "import json,os;print(json.dumps({name:os.environ[name] for name in " + repr(KEYS) + "}))",
                ),
                exported,
                prepared,
                30,
                True,
            )
        ]
    )[0]
    assert not observed.timed_out and observed.returncode == 0, observed.output_tail
    assert json.loads(observed.output_tail) == expected


def test_export_environment_requires_explicit_candidate_epoch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (*KEYS, "TEMPLATE_DETERMINISTIC"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ValueError, match="set SOURCE_DATE_EPOCH explicitly"):
        _environment(Path(sys.executable), tmp_path, repo_root=tmp_path)
