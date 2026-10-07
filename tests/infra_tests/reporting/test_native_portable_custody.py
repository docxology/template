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
from infrastructure.reporting.native_format_acceptance_validation import _tool
from infrastructure.reporting.native_format_portable_custody import (
    producer_custody,
    producer_bootstrap,
    producer_path,
    validate_producer_custody,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

REPO = Path(__file__).absolute().parents[3]


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
    producer = tmp_path / "producer"
    producer.mkdir()
    executable = producer / "producer-python"
    executable.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n')
    executable.chmod(0o700)
    args = ["-I", "-c", "print('original actual execution')"]
    record = native_tool_record(
        producer,
        producer / "output/readiness/tool",
        str(executable),
        args,
        env={"PATH": str(Path(sys.executable).parent)},
        deadline=time.monotonic() + 30,
        run_id="a" * 32,
        purpose="portable-actual",
    )
    assert record["exit_code"] == 0
    reader = tmp_path / "reader"
    shutil.copytree(producer, reader)
    shutil.rmtree(producer)
    assert (
        _tool(record["artifact"], SnapshotReader(reader), "a" * 32, str(executable), "portable-actual", args)[
            "stdout"
        ].strip()
        == "original actual execution"
    )
    # Use another actual interpreter for admission, with source loaded explicitly.
    alternate = Path(sys.base_prefix) / "bin/python3"
    if alternate.exists():
        script = (
            "import sys;sys.path[:0]=[sys.argv[1],sys.argv[6]];"
            "from pathlib import Path;import json;"
            "from infrastructure.reporting.native_format_acceptance_validation import _tool;"
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
        assert result.returncode == 0, result.stderr
    path = reader / record["artifact"]["path"]
    payload = json.loads(path.read_text())
    for changed in (
        {"run_id": "b" * 32},
        {"command": ["/changed", *args]},
        {"original_exit_code": 7},
        {"executable_observation_after": {}},
    ):
        binding = write_json(reader, path, {**payload, **changed})
        with pytest.raises(ValueError):
            _tool(binding, SnapshotReader(reader), "a" * 32, str(executable), "portable-actual", args)
    path.write_text("{}")
    with pytest.raises(ValueError, match="bytes differ"):
        _tool(record["artifact"], SnapshotReader(reader), "a" * 32, str(executable), "portable-actual", args)
