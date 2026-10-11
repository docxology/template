"""Small genuine PID controls and literal request refusals; native paint is separate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.rendering._mermaid_v12 import request_bytes
from infrastructure.rendering.security import run_isolated_subprocess


@pytest.mark.parametrize("exit_code", [0, 7])
def test_actual_isolated_child_preserves_pid_exit_and_raw_streams(exit_code: int) -> None:
    code = f"import os,sys; print(os.getpid()); print('original-stderr',file=sys.stderr); raise SystemExit({exit_code})"
    command = [sys.executable, "-I", "-B", "-c", code]
    result = run_isolated_subprocess(command, timeout=3)
    assert isinstance(result, subprocess.CompletedProcess)
    assert result.args == command and result.returncode == exit_code
    assert type(result.pid) is int and result.pid > 0
    assert int(result.stdout.strip()) == result.pid
    assert result.stderr == "original-stderr\n"


@pytest.mark.parametrize("output_format", ["pdf", "md"])
def test_unadmitted_output_format_is_refused(output_format: str) -> None:
    with pytest.raises(ValueError, match="original SVG/PNG"):
        request_bytes(
            Path("/reader/package"),
            Path("/reader/original.mmd"),
            Path("/reader/output." + output_format),
            output_format,
            None,
        )


def test_relative_source_cannot_change_the_explicit_reader_origin() -> None:
    source = Path("reader/original.mmd")
    assert source != Path("/reader/original.mmd")
    with pytest.raises(ValueError, match="absolute"):
        request_bytes(Path("/reader/package"), source, Path("/reader/output.png"), "png", None)
