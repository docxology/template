"""Original real pytest subprocess reports, never invented executed success."""

from __future__ import annotations

import os
import json
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.core.testing.pytest_observations import DIRECTORY_ENV, NONCE_ENV, ROOT_ENV, read_execution_receipts

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize(
    "fault",
    (
        "none",
        "missing-collected",
        "missing-deselected",
        "overlap",
        "unobserved-file",
        "profile",
        "arguments",
        "ambient-keyword",
        "ambient-deselect",
        "argv-deselect",
        "argv-plugin",
        "argv-ini",
    ),
)
def test_original_collection_accounts_for_wholly_deselected_files_and_refuses_omissions(
    tmp_path: Path, fault: str
) -> None:
    from infrastructure.core.testing.ci_infra import _shard_collection, verify_shard_receipts
    from infrastructure.core.testing.pytest_observations import member_digest, read_execution_collection

    (tmp_path / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\naddopts = "-m \'not slow\'"\nmarkers = ["slow: explicitly excluded"]\n'
    )
    (tmp_path / "test_owned.py").write_text("def test_owned():\n    assert 2 + 2 == 4\n")
    (tmp_path / "test_slow.py").write_text(
        "import pytest\n@pytest.mark.slow\ndef test_explicitly_deselected():\n"
        "    raise AssertionError('the original quick profile must exclude this case')\n"
    )
    bypass = fault in {"ambient-keyword", "ambient-deselect", "argv-deselect"}
    if bypass:
        with (tmp_path / "test_slow.py").open("a") as stream:
            stream.write("\ndef test_normal_failure():\n    assert False, 'must never be silently deselected'\n")
    files = ["test_owned.py", "test_slow.py"]
    shard = tmp_path / "receipts/shard-0"
    directory = shard / "execution"
    command = [
        sys.executable,
        "-m",
        "pytest",
        *files,
        "--no-cov",
        "-q",
        "--benchmark-disable",
        "-p",
        "infrastructure.core.testing.pytest_receipt",
        "--junitxml=" + str(shard / "junit.xml"),
        "--timeout=60",
    ]
    if fault == "argv-deselect":
        command.extend(["--deselect", "test_slow.py::test_normal_failure"])
    elif fault == "argv-plugin":
        command.extend(["-p", "no:cacheprovider"])
    elif fault == "argv-ini":
        command.extend(["-o", "addopts=-m 'not slow'"])
    result = subprocess.run(
        command,
        cwd=tmp_path,
        env={
            **os.environ,
            "PYTHONPATH": str(ROOT),
            "PYTEST_ADDOPTS": "-k test_owned"
            if fault == "ambient-keyword"
            else "--deselect=test_slow.py::test_normal_failure"
            if fault == "ambient-deselect"
            else "",
            DIRECTORY_ENV: str(directory),
            NONCE_ENV: "owned-collection",
            ROOT_ENV: str(tmp_path),
        },
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    selected, outcomes = read_execution_receipts(directory, "owned-collection")
    collected, deselected, profile = read_execution_collection(directory, "owned-collection")
    assert selected == ("test_owned.py::test_owned",)
    assert "test_slow.py::test_explicitly_deselected" in deselected
    assert len(deselected) == (2 if bypass else 1)
    assert set(collected) == set(selected) | set(deselected)
    assert profile["arguments"][:2] == files
    assert profile["marker_expression"] == "not slow"
    if fault in {"ambient-keyword", "ambient-deselect", "argv-deselect", "argv-plugin", "argv-ini"}:
        with pytest.raises(ValueError, match="invocation/profile"):
            _shard_collection(directory, "owned-collection", files, tmp_path)
        return
    row = {
        "shard": 0,
        "nonce": "owned-collection",
        "files": files,
        "selected": selected,
        "outcomes": outcomes,
        "member_sha256": member_digest(selected),
        "outcome_sha256": member_digest(outcomes),
        **_shard_collection(directory, "owned-collection", files, tmp_path),
    }
    original = next(directory.glob("execution-*.json"))
    raw = json.loads(original.read_bytes())
    if fault == "missing-collected":
        raw["collected"] = list(selected)
    elif fault == "missing-deselected":
        raw.pop("deselected")
    elif fault == "overlap":
        raw["deselected"].extend(selected)
    elif fault == "unobserved-file":
        raw["collected"] = list(selected)
        raw["deselected"] = []
    elif fault == "arguments":
        raw["selection_profile"]["arguments"].remove("test_slow.py")
    elif fault == "profile":
        row["selection_profile"] = {**profile, "marker_expression": ""}
    original.write_text(json.dumps(raw))
    (shard / "summary.json").write_text(json.dumps(row))
    if fault == "none":
        assert verify_shard_receipts({"infra_shards": [files]}, tmp_path / "receipts", root=tmp_path)["members"] == 1
    else:
        with pytest.raises(ValueError):
            verify_shard_receipts({"infra_shards": [files]}, tmp_path / "receipts", root=tmp_path)


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
