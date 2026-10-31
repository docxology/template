"""Actual functional child outcomes survive timeout cleanup without acceptance."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.core.testing.ci_infra import (
    AUTOMATIC_SHARD_MAX_MODULES,
    _run_functional_process,
    infrastructure_files,
    infrastructure_shards,
    validate_shards,
)
from tests.helpers.owned_process import assert_process_exited, owned_process_fixture


def _requested_process(root: Path, directory: Path, command: list[str], timeout: float) -> int:
    directory.mkdir()
    (directory / "request.json").write_text(
        json.dumps({"shard": 0, "nonce": "owned-original", "command": command, "timeout_seconds": timeout}),
        encoding="utf-8",
    )
    return _run_functional_process(
        root,
        command,
        dict(os.environ, PYTEST_ADDOPTS="", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"),
        directory,
        timeout_seconds=timeout,
        is_contract=False,
    )


@pytest.mark.parametrize("fails", [False, True])
def test_actual_pytest_exit_and_diagnostic_cannot_grant_execution_receipts(tmp_path: Path, fails: bool) -> None:
    case = tmp_path / "test_owned.py"
    case.write_text("def test_actual():\n    assert " + str(not fails) + "\n", encoding="utf-8")
    directory = tmp_path / "diagnostic"
    command = [sys.executable, "-m", "pytest", "-q", "--confcutdir=" + str(tmp_path), str(case)]
    code = _requested_process(tmp_path, directory, command, 30)

    row = json.loads((directory / "run-process.json").read_bytes())
    assert row["role"] == "diagnostic-process-only"
    assert row["original_returncode"] == row["returncode"] == row["cli_exit_code"] == code == int(fails)
    assert type(row["pid"]) is int and row["pid"] > 0
    assert not row["timed_out"] and not row["custody_refused"] and not row["command_error"]
    assert row["stream_mode"] == "inherited-not-captured"
    assert row["request_sha256"] == hashlib.sha256((directory / "request.json").read_bytes()).hexdigest()
    assert not (directory / "summary.json").exists()
    assert not (directory / "execution").exists()


def test_automatic_capacity_holds_for_real_skewed_module_sizes(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[3]
    baseline = infrastructure_files(root)
    changed = tuple(f"tests/infra_tests/skew/test_owned_{index:03d}.py" for index in range(61))
    for relative in (*baseline, *changed):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("def test_owned():\n    assert 1 + 1 == 2\n", encoding="utf-8")
    bins = (len(baseline) + len(changed) + AUTOMATIC_SHARD_MAX_MODULES - 1) // AUTOMATIC_SHARD_MAX_MODULES
    for relative in changed[: bins - 1]:
        with (tmp_path / relative).open("a") as stream:
            stream.write("#" + "large physical module " * 50000 + "\n")

    selected = infrastructure_files(tmp_path, changed)
    shards = infrastructure_shards(tmp_path, changed)

    validate_shards(shards, selected)
    assert all(1 <= len(shard) <= AUTOMATIC_SHARD_MAX_MODULES for shard in shards)
    assert max((tmp_path / name).stat().st_size for name in selected) > 1000000
    assert shards == infrastructure_shards(tmp_path, changed)


@pytest.mark.skipif(os.name != "posix", reason="detached POSIX sessions and native ps ownership")
@pytest.mark.timeout(120)
def test_actual_pytest_timeout_cleans_owned_detached_descendant_and_keeps_foreign_sibling(tmp_path: Path) -> None:
    owned_root = tmp_path / "owned"
    owned_root.mkdir()
    owned = owned_process_fixture(owned_root)
    case = tmp_path / "test_owned.py"
    case.write_text(
        f"import subprocess\ndef test_owned_tree():\n    subprocess.run({owned.command!r}, check=True, timeout=30)\n",
        encoding="utf-8",
    )
    foreign = subprocess.Popen([sys.executable, "-I", "-c", "import time; time.sleep(60)"], start_new_session=True)
    try:
        with owned:
            directory = tmp_path / "diagnostic"
            command = [sys.executable, "-m", "pytest", "-q", "--confcutdir=" + str(tmp_path), str(case)]
            code = _requested_process(tmp_path, directory, command, 10)
            row = json.loads((directory / "run-process.json").read_bytes())
            assert code == row["cli_exit_code"] == 124
            assert row["timed_out"] and type(row["original_returncode"]) is int
            assert row["original_returncode"] != 0 and row["returncode"] != 0
            assert type(row["pid"]) is int
            observed = owned.observed()
            assert observed["session_id"] == observed["pid"]
            owned.assert_cleaned()
            assert_process_exited(row["pid"])
            assert foreign.poll() is None
            assert not (directory / "summary.json").exists()
            assert not (directory / "execution").exists()
    finally:
        if foreign.poll() is None:
            foreign.terminate()
        foreign.wait(timeout=5)


def test_changed_request_is_refused_before_original_child_launch(tmp_path: Path) -> None:
    directory = tmp_path / "diagnostic"
    directory.mkdir()
    marker = tmp_path / "must-not-launch"
    command = [sys.executable, "-c", f"from pathlib import Path;Path({str(marker)!r}).touch()"]
    (directory / "request.json").write_text(
        json.dumps({"shard": 0, "nonce": "owned-original", "command": command, "timeout_seconds": 30}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="differs from its original request"):
        _run_functional_process(tmp_path, command, dict(os.environ), directory, timeout_seconds=5, is_contract=False)
    assert not marker.exists()
    assert not (directory / "run-process.json").exists()
    assert not (directory / "summary.json").exists()
