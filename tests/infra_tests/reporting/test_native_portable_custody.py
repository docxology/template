"""Genuine bounded execution survives relocation; tampering stays refused."""

from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

import pytest

from infrastructure.core.execution_boundary import run_bounded_subprocess
from infrastructure.project.public_acceptance_evidence import bootstrap_command, runtime_identity, write_json
from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
from infrastructure.reporting.native_format_acceptance_evidence import _tool
from infrastructure.reporting.native_format_portable_custody import (
    producer_custody,
    producer_bootstrap,
    producer_path,
    validate_producer_custody,
)
from infrastructure.reporting.native_projection_contracts import ProjectionSourceUnsupported
from infrastructure.reporting.native_tool_replay import validate_native_tool_data
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.reporting.required_acceptance_aggregate import _evidence_closure

REPO = Path(__file__).absolute().parents[3]
# Portable admission of a retained native tool receipt needs the externally
# admitted Source and original launch custodian; receipt DATA never holds them.
UNADMITTED = "externally admitted source and original launch custody"


def test_original_bootstrap_reconstruction_preserves_root_and_hook(tmp_path: Path) -> None:
    producer = tmp_path / "producer"
    producer.mkdir()
    (producer / "root_source.py").write_text("value = 1\n")
    runtime = runtime_identity()
    custody = producer_custody(producer, runtime, "a" * 64)
    assert validate_producer_custody(custody, runtime, "a" * 64) == custody
    original = bootstrap_command(Path(sys.executable), producer, "example", "--root", str(producer))
    reader = tmp_path / "reader"
    shutil.copytree(producer, reader)
    shutil.rmtree(producer)
    assert producer_bootstrap(custody, reader, runtime, "example", "--root", custody["root"]) == list(original)
    assert producer_path(custody, reader, reader / "output/test") == producer / "output/test"
    for change in ({"runtime_digest": "b" * 64}, {"source_digest": "b" * 64}, {"root": "/original/../escape"}):
        with pytest.raises(ValueError):
            validate_producer_custody({**custody, **change}, runtime, "a" * 64)


def test_actual_tool_receipt_relocated_reader_and_tamper(tmp_path: Path) -> None:
    """Relocated receipt DATA stays checkable but never self-authorizes.

    Admission of an original tool receipt requires the externally held
    original launch custodian. A bare relocated reader, in this or another
    interpreter, must refuse; tampered DATA is refused by its own checks.
    """
    producer = tmp_path / "producer"
    producer.mkdir()
    executable = producer / "producer-python"
    executable.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n')
    executable.chmod(0o700)
    args = ["-I", "-c", "print('original actual execution')"]
    directory = producer / "output/readiness/tool"
    create_private_native_directory(producer, directory)
    deadline = time.monotonic() + 30
    record = native_tool_record(
        producer,
        directory,
        str(executable),
        args,
        env={"PATH": str(Path(sys.executable).parent)},
        deadline=deadline,
        run_id="a" * 32,
        purpose="portable-actual",
    )
    completed = time.monotonic()
    assert record["exit_code"] == 0
    reader = tmp_path / "reader"
    shutil.copytree(producer, reader)
    shutil.rmtree(producer)
    raw = SnapshotReader(reader).read(record["artifact"]["path"]).json_object()
    assert raw["stdout"].strip() == "original actual execution"
    closure_reader = SnapshotReader(reader)
    closure = _evidence_closure(closure_reader, record["artifact"]["path"])
    assert set(closure) == {
        record["artifact"]["path"],
        raw["native_process_artifact"]["path"],
        raw["raw_stdout"]["path"],
        raw["raw_stderr"]["path"],
    }
    assert closure[raw["raw_stdout"]["path"]].decode().strip() == "original actual execution"
    assert closure[raw["raw_stderr"]["path"]] == b""
    assert set(closure_reader.snapshots) == {reader / relative for relative in closure}
    assert closure_reader.unchanged()
    # The relocated original PID/OS/stream/guardian DATA remains consistent
    # under the clock this caller actually held for the original launch.
    validate_native_tool_data(raw, SnapshotReader(reader), original_deadline=deadline, original_completion=completed)
    native_path = reader / raw["native_process_artifact"]["path"]
    original_native = native_path.read_bytes()
    try:
        for channel in ("stdout", "stderr"):
            for fault in ("legacy", "schema", "hash", "bytes", "name", "extra"):
                changed_native = json.loads(original_native)
                stream = changed_native[f"raw_{channel}"]
                if fault == "legacy":
                    stream.pop("schema_version")
                elif fault == "schema":
                    stream["schema_version"] = "unrecognized-stream-observation"
                elif fault == "hash":
                    stream["sha256"] = "0" * 64
                elif fault == "bytes":
                    stream["bytes"] += 1
                elif fault == "name":
                    stream["path"] += ".changed"
                else:
                    stream["extra"] = True
                # Rebind the changed process so refusal must inspect stream DATA,
                # not merely notice an obsolete enclosing artifact hash.
                changed_raw = {
                    **raw,
                    "native_process_artifact": write_json(reader, native_path, changed_native),
                }
                with pytest.raises(ValueError):
                    validate_native_tool_data(
                        changed_raw,
                        SnapshotReader(reader),
                        original_deadline=deadline,
                        original_completion=completed,
                    )
    finally:
        native_path.write_bytes(original_native)
    with pytest.raises(ProjectionSourceUnsupported, match=UNADMITTED):
        _tool(record["artifact"], SnapshotReader(reader), "a" * 32, str(executable), "portable-actual", args)
    # Another actual interpreter loading the same source cannot mint custody either.
    alternate = Path(sys.base_prefix) / "bin/python3"
    if alternate.exists():
        script = (
            "import sys;sys.path[:0]=[sys.argv[1],sys.argv[6]];"
            "from pathlib import Path;import json;"
            "from infrastructure.reporting.native_format_acceptance_evidence import _tool;"
            "from infrastructure.reporting.release_readiness_snapshot import SnapshotReader;"
            "_tool(json.loads(sys.argv[3]),SnapshotReader(Path(sys.argv[2])), '"
            + "a" * 32
            + "',sys.argv[4],'portable-actual',json.loads(sys.argv[5]))"
        )
        result = run_bounded_subprocess(
            [
                str(alternate),
                "-I",
                "-c",
                script,
                str(REPO),
                str(reader),
                json.dumps(record["artifact"]),
                str(executable),
                json.dumps(args),
                str(Path(__import__("pypdf").__file__).parent.parent),
            ],
            cwd=REPO,
            env={"PATH": "/usr/bin:/bin"},
            timeout=30,
            capture_output=True,
        )
        assert result.returncode != 0 and not result.timed_out
        assert "ProjectionSourceUnsupported" in result.stderr and UNADMITTED in result.stderr, result.stderr
    path = reader / record["artifact"]["path"]
    payload = json.loads(path.read_text())
    for changed in (
        {"run_id": "b" * 32},
        {"command": ["/changed", *args]},
        {"original_exit_code": 7},
        {"executable_observation_after": {}},
    ):
        binding = write_json(reader, path, {**payload, **changed})
        with pytest.raises(ValueError) as refused:
            _tool(binding, SnapshotReader(reader), "a" * 32, str(executable), "portable-actual", args)
        # The tampered DATA itself is refused before custody is even consulted.
        assert not isinstance(refused.value, ProjectionSourceUnsupported)
    path.write_text("{}")
    with pytest.raises(ValueError, match="bytes differ"):
        _tool(record["artifact"], SnapshotReader(reader), "a" * 32, str(executable), "portable-actual", args)
