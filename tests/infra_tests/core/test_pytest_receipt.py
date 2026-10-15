"""Original real pytest subprocess reports, never invented executed success."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.core.testing.pytest_observations import DIRECTORY_ENV, NONCE_ENV, ROOT_ENV, read_execution_receipts

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("workers", [0, 2])
@pytest.mark.parametrize("fault", ["none", "failed", "nonce", "skip"])
def test_original_pytest_observation_requires_real_complete_success(tmp_path: Path, fault: str, workers: int) -> None:
    tests = tmp_path / "test_owned.py"
    tests.write_text("def test_owned():\n    assert " + ("False" if fault == "failed" else "True") + "\n")
    if fault == "skip":
        with tests.open("a") as stream:
            stream.write("\ndef test_expected_skip():\n    import pytest\n    pytest.skip('explicit existing skip')\n")
    directory = tmp_path / "observations"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--no-cov",
            "-n",
            str(workers),
            "-p",
            "infrastructure.core.testing.pytest_receipt",
            str(tests),
        ],
        cwd=tmp_path,
        env={
            **os.environ,
            "PYTHONPATH": str(ROOT),
            "PYTEST_ADDOPTS": "",
            DIRECTORY_ENV: str(directory),
            NONCE_ENV: "owned",
            ROOT_ENV: str(tmp_path),
        },
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == (1 if fault == "failed" else 0)
    if fault in {"none", "skip"}:
        selected, outcomes = read_execution_receipts(directory, "owned")
        assert "test_owned.py::test_owned" in selected
        assert len(outcomes) == len(selected) == (2 if fault == "skip" else 1)
        assert any("skipped" in row for row in outcomes) is (fault == "skip")
    else:
        with pytest.raises(ValueError):
            read_execution_receipts(directory, "wrong" if fault == "nonce" else "owned")


def test_separate_project_controllers_qualify_equal_local_nodeids(tmp_path: Path) -> None:
    directory = tmp_path / "observations"
    for name in ("one", "two"):
        project = tmp_path / "projects" / name
        project.mkdir(parents=True)
        (project / "pytest.ini").write_text("[pytest]\n")
        (project / "test_owned.py").write_text("def test_owned():\n    assert True\n")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--no-cov", "-p", "infrastructure.core.testing.pytest_receipt"],
            cwd=project,
            env={
                **os.environ,
                "PYTHONPATH": str(ROOT),
                "PYTEST_ADDOPTS": "",
                DIRECTORY_ENV: str(directory),
                NONCE_ENV: "owned",
                ROOT_ENV: str(tmp_path),
            },
            capture_output=True,
            check=False,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
    selected, _ = read_execution_receipts(directory, "owned")
    assert selected == ("projects/one/test_owned.py::test_owned", "projects/two/test_owned.py::test_owned")


def test_pytest_spawned_by_test_cannot_add_another_controller_observation(tmp_path: Path) -> None:
    child = tmp_path / "child"
    child.mkdir()
    (child / "test_inner.py").write_text("def test_inner():\n    assert True\n")
    (tmp_path / "test_owned.py").write_text(
        "def test_owned():\n"
        "    import subprocess, sys\n"
        "    from pathlib import Path\n"
        "    result = subprocess.run([sys.executable, '-m', 'pytest', '-q', '--no-cov',\n"
        "        '-p', 'infrastructure.core.testing.pytest_receipt'], cwd=Path(__file__).parent/'child')\n"
        "    assert result.returncode == 0\n"
    )
    directory = tmp_path / "observations"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--no-cov",
            "-p",
            "infrastructure.core.testing.pytest_receipt",
            "test_owned.py",
        ],
        cwd=tmp_path,
        env={
            **os.environ,
            "PYTHONPATH": str(ROOT),
            "PYTEST_ADDOPTS": "",
            DIRECTORY_ENV: str(directory),
            NONCE_ENV: "owned",
            ROOT_ENV: str(tmp_path),
        },
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    selected, _ = read_execution_receipts(directory, "owned")
    assert selected == ("test_owned.py::test_owned",)
    assert len(tuple(directory.glob("execution-*.json"))) == 1
