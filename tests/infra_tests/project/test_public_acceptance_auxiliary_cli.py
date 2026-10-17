"""The actual auxiliary CLI rejects invalid workers before Source or I/O."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize("workers", ("0", "4", "-1", "many"))
def test_actual_auxiliary_cli_refuses_invalid_worker_count_without_outputs(tmp_path: Path, workers: str) -> None:
    _assert_invalid_worker_count(tmp_path, workers, "--installed-workers")


@pytest.mark.parametrize("workers", ("0", "4", "-1", "many"))
def test_actual_auxiliary_cli_refuses_invalid_auxiliary_workers_without_outputs(tmp_path: Path, workers: str) -> None:
    _assert_invalid_worker_count(tmp_path, workers, "--auxiliary-workers")


def _assert_invalid_worker_count(tmp_path: Path, workers: str, flag: str) -> None:
    root = Path(__file__).resolve().parents[3]
    evidence = tmp_path / "never-created"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "infrastructure.project.public_acceptance_auxiliary_cli",
            "--repo-root",
            str(tmp_path / "absent-source"),
            "--installed",
            flag,
            workers,
            "--evidence-dir",
            str(evidence),
        ],
        cwd=root,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 2
    assert flag in result.stderr
    assert "invalid choice" in result.stderr or "invalid int value" in result.stderr
    assert not tuple(tmp_path.iterdir())


def test_public_pipeline_export_preserves_direct_script_permissions_and_source_bytes(tmp_path: Path) -> None:
    from infrastructure.project.public_acceptance_auxiliary_pipeline_environment import copy_public_pipeline_source
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

    root = tmp_path.resolve() / "root"
    (root / "infrastructure/vendor").mkdir(parents=True)
    script = root / "run.sh"
    script.write_text("#!/bin/sh\nexit 0\n")
    script.chmod(0o755)
    source = root / "infrastructure" / "model.py"
    source.write_text("VALUE = 7\n")
    source.chmod(0o644)
    (root / "infrastructure/vendor/.git").write_text("local submodule metadata")
    copied = tmp_path.resolve() / "export"
    reader = SnapshotReader(root)
    files = copy_public_pipeline_source(root, copied, reader)
    assert {row["path"] for row in files} == {"run.sh", "infrastructure/model.py"}
    assert (copied / "run.sh").stat().st_mode & 0o777 == 0o755
    assert (copied / "infrastructure/model.py").stat().st_mode & 0o777 == 0o644
    assert (copied / "run.sh").read_bytes() == script.read_bytes()
    assert not (copied / "infrastructure/vendor/.git").exists()
    result = subprocess.run([str(copied / "run.sh")], capture_output=True, check=False, timeout=10)
    assert result.returncode == 0
    source.write_text("VALUE = 8\n")
    with pytest.raises(ValueError, match="changed during confined export"):
        copy_public_pipeline_source(root, tmp_path.resolve() / "changed-export", reader)


def test_expired_logical_reader_never_renews_the_enclosing_deadline(tmp_path: Path) -> None:
    import time
    from infrastructure.project.public_acceptance_auxiliary_pipeline_environment import _read_logical_plan

    with pytest.raises(TimeoutError, match="original auxiliary deadline"):
        _read_logical_plan(tmp_path, "templates/template_madlib", 1800, "1760000000", deadline=time.monotonic() - 1)
    assert not tuple(tmp_path.iterdir())


@pytest.mark.timeout(90)
def test_real_auxiliary_deadline_retains_a_complete_failed_selection() -> None:
    import json
    import shutil
    from uuid import uuid4
    from infrastructure.project.public_acceptance_auxiliary import run_auxiliary_acceptance

    root = Path(__file__).resolve().parents[3]
    directory = root / "output/readiness" / ("deadline-retention-" + uuid4().hex)
    selected = ("root:roster", "root:methods", "templates/template_madlib:pipeline")
    try:
        result = run_auxiliary_acceptance(
            root,
            gates=selected,
            timeout_seconds=1,
            workers=3,
            evidence_dir=directory,
        )
        retained = json.loads((directory / "receipt.json").read_text())
        assert retained["exit_code"] == result["exit_code"] == 1
        assert retained["deadline_exhausted"] is True
        assert set(retained["gates"]) == set(selected)
        for entry in retained["gates"].values():
            assert entry["status"] != "pass"
            artifact = json.loads((root / entry["artifact"]).read_text())
            assert artifact["status"] == entry["status"]
    finally:
        if directory.exists():
            shutil.rmtree(directory)
