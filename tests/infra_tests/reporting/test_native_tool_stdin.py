"""Real native stdin descriptor/byte custody and ordinary DEVNULL regression."""

from __future__ import annotations

import os
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from infrastructure.reporting.native_tool_process import (
    SCHEMA,
    STDIN_SCHEMA,
    NativeLiveToolProcess,
    run_native_tool_process,
)


def _run(
    directory: Path,
    purpose: str,
    code: str,
    *,
    stdin: Path | None = None,
    while_live: Callable[[NativeLiveToolProcess], None] | None = None,
) -> dict[str, Any]:
    return run_native_tool_process(
        directory,
        sys.executable,
        ["-I", "-c", code],
        cwd=directory,
        env=dict(os.environ),
        deadline=time.monotonic() + 30.0,
        purpose=purpose,
        stdin_path=stdin,
        while_live=while_live,
    )


def test_actual_native_child_consumes_exact_confined_stdin(tmp_path: Path) -> None:
    stdin = tmp_path / "input.json"
    body = b'{"blocks":[],"meta":{},"pandoc-api-version":[1,23]}'
    stdin.write_bytes(body)
    result = _run(
        tmp_path,
        "stdin-original",
        "import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())",
        stdin=stdin,
    )
    assert result["accepted"] is True
    assert result["original_exit_code"] == 0
    assert result["schema_version"] == STDIN_SCHEMA
    assert result["stdin_input_before"] == result["stdin_input_after"]
    assert result["stdin_input_before"]["bytes"] == len(body)
    assert (tmp_path / "stdin-original.stdout.bin").read_bytes() == body


def test_ordinary_native_child_retains_devnull_schema(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        "devnull-original",
        "import sys; sys.stdout.write(str(len(sys.stdin.buffer.read())))",
    )
    assert result["accepted"] is True
    assert result["schema_version"] == SCHEMA
    assert "stdin_input_before" not in result
    assert "stdin_input_after" not in result
    assert (tmp_path / "devnull-original.stdout.bin").read_bytes() == b"0"


def test_stdin_symlink_refuses_before_actual_launch(tmp_path: Path) -> None:
    body = tmp_path / "body.json"
    body.write_bytes(b"{}")
    alias = tmp_path / "alias.json"
    alias.symlink_to(body)
    with pytest.raises(ValueError, match="exact owned private-directory"):
        _run(tmp_path, "symlink-refusal", "pass", stdin=alias)
    assert not (tmp_path / "symlink-refusal.native-process.json").exists()


def test_actual_live_input_mutation_refuses_custody(tmp_path: Path) -> None:
    stdin = tmp_path / "input.json"
    stdin.write_bytes(b"{}")

    def mutate(live: NativeLiveToolProcess) -> None:
        live.verify_live()
        with stdin.open("ab") as stream:
            stream.write(b" ")
        live.verify_live()

    result = _run(
        tmp_path,
        "changed-stdin",
        "import sys,time; time.sleep(.1); sys.stdin.buffer.read()",
        stdin=stdin,
        while_live=mutate,
    )
    assert result["accepted"] is False
    assert result["stdin_input_before"] != result["stdin_input_after"]
    assert any("stdin changed" in item for item in result["diagnostics"])
