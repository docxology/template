"""Offline metadata/archive controls; these do not claim remote transfer."""

from __future__ import annotations

import hashlib
import io
import os
import stat
import sys
import zipfile
from copy import deepcopy
from pathlib import Path

import pytest

from infrastructure.core.execution_boundary import run_bounded_subprocess
from infrastructure.project.public_hosted_origin import ARTIFACTS, WORKFLOW, _metadata, _process, _zip_members

SHA = "a" * 40
REPOSITORY = "example/public-template"


def metadata() -> tuple[dict, dict]:
    run = {
        "id": 91,
        "head_sha": SHA,
        "path": WORKFLOW,
        "repository": {"id": 8, "full_name": REPOSITORY},
        "head_repository": {"id": 8, "full_name": REPOSITORY},
    }
    rows = [
        {
            "id": index,
            "name": name,
            "expired": False,
            "digest": "sha256:" + "b" * 64,
            "workflow_run": {"id": 91, "head_sha": SHA, "repository_id": 8, "head_repository_id": 8},
        }
        for index, name in enumerate(ARTIFACTS, 1)
    ]
    return run, {"total_count": 4, "artifacts": rows}


def archive(entries: list[tuple[str, bytes | zipfile.ZipInfo]]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as stream:
        for name, value in entries:
            if isinstance(value, zipfile.ZipInfo):
                stream.writestr(value, b"target")
            else:
                stream.writestr(name, value)
    return output.getvalue()


def test_exact_six_original_metadata_and_foreign_stale_duplicate_controls() -> None:
    run, listing = metadata()
    assert len(_metadata(run, listing, REPOSITORY, 91, SHA)) == 4
    for key, value in (("head_sha", "c" * 40), ("id", 92), ("path", ".github/workflows/foreign.yml")):
        with pytest.raises(ValueError):
            _metadata({**run, key: value}, listing, REPOSITORY, 91, SHA)
    for key, value in (("expired", True), ("digest", None), ("id", 2)):
        changed = deepcopy(listing)
        changed["artifacts"][0][key] = value
        with pytest.raises(ValueError):
            _metadata(run, changed, REPOSITORY, 91, SHA)
    for key, value in (("head_sha", "c" * 40), ("id", 92), ("repository_id", 9), ("head_repository_id", 9)):
        changed = deepcopy(listing)
        changed["artifacts"][0]["workflow_run"][key] = value
        with pytest.raises(ValueError):
            _metadata(run, changed, REPOSITORY, 91, SHA)
    changed = deepcopy(listing)
    changed["artifacts"][0]["name"] = changed["artifacts"][1]["name"]
    with pytest.raises(ValueError):
        _metadata(run, changed, REPOSITORY, 91, SHA)


def test_actual_zip_complete_bytes_and_unsafe_member_controls() -> None:
    name = "required-source-root-Linux-3.14"
    receipt = ("root-linux-3.14/receipt.json", b'{"original_exit_code":1}')
    raw = archive([receipt, ("root-linux-3.14/log.txt", b"actual failure remains visible")])
    admitted = _zip_members(raw, name)
    assert admitted == {
        "output/readiness/" + receipt[0]: receipt[1],
        "output/readiness/root-linux-3.14/log.txt": b"actual failure remains visible",
    }
    mutant = archive([receipt, ("root-linux-3.14/log.txt", b"changed")])
    assert hashlib.sha256(raw).digest() != hashlib.sha256(mutant).digest()
    assert _zip_members(mutant, name) != admitted
    for bad in (
        "../escape",
        "/root-linux-3.14/absolute",
        "root-linux-3.14/../escape",
        "root-macos-3.14/foreign",
        "root-linux-3.14\\ambiguous",
    ):
        with pytest.raises(ValueError):
            _zip_members(archive([receipt, (bad, b"bad")]), name)
    link = zipfile.ZipInfo("root-linux-3.14/link")
    link.create_system = 3
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    with pytest.raises(ValueError):
        _zip_members(archive([receipt, (link.filename, link)]), name)
    with pytest.warns(UserWarning), pytest.raises(ValueError):
        _zip_members(archive([receipt, receipt]), name)
    with pytest.raises(ValueError):
        _zip_members(archive([("root-linux-3.14/log.txt", b"no receipt")]), name)


def test_genuine_bounded_process_original_outcome_is_required(tmp_path: Path) -> None:
    # An independent actual Python process exercises custody validation; it is
    # never labeled a gh API call or evidence of a hosted transfer.
    command = [sys.executable, "-I", "-c", "print('observed original output')"]
    result = run_bounded_subprocess(command, cwd=tmp_path, env=os.environ.copy(), timeout=15)
    raw = {
        "command": command,
        "exit_code": result.returncode,
        "original_exit_code": result.original_returncode,
        "timed_out": result.timed_out,
        "custody_refused": result.custody_refused,
        "diagnostic": result.command_error,
    }
    _process(raw, command)
    assert result.stdout.strip() == "observed original output"
    for key, value in (
        ("original_exit_code", 1),
        ("timed_out", True),
        ("custody_refused", True),
        ("diagnostic", "lost custody"),
        ("exit_code", True),
    ):
        with pytest.raises(ValueError):
            _process({**raw, key: value}, command)
    with pytest.raises(ValueError):
        _process({"status": "passed"}, command)
    with pytest.raises(ValueError):
        _process(raw, [*command, "changed"])


def test_real_archive_stream_retains_nested_original_exit(tmp_path: Path) -> None:
    import json

    from infrastructure.project.public_hosted_origin import DOWNLOAD_SCRIPT

    content = archive([("root-linux-3.14/receipt.json", b'{"original_exit_code":1}')])
    for exit_code in (0, 1):
        target = tmp_path / f"observed-{exit_code}.zip"
        source = f"import sys;sys.stdout.buffer.write({content!r});sys.exit({exit_code})"
        command = [sys.executable, "-I", "-c", DOWNLOAD_SCRIPT, str(target), sys.executable, "-I", "-c", source]
        result = run_bounded_subprocess(command, cwd=tmp_path, env=os.environ.copy(), timeout=15)
        assert result.returncode == result.original_returncode == exit_code
        assert not result.timed_out and not result.custody_refused
        assert target.read_bytes() == content
        assert json.loads(result.stdout) == {
            "original_exit_code": exit_code,
            "archive_sha256": hashlib.sha256(content).hexdigest(),
        }
