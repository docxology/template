"""Schema subcommand for the SIA CLI (no-mocks: in-process call + subprocess)."""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
from pathlib import Path

from infrastructure.sia.cli import main


def test_schema_subcommand_emits_valid_json() -> None:
    """``main(["schema"])`` returns 0 and prints a JSON parameter contract."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        rc = main(["schema"])
    assert rc == 0
    payload = json.loads(buffer.getvalue())
    assert "prog" in payload
    assert "subcommands" in payload
    # Existing subcommands are still present in the schema (no regression).
    assert "validate" in payload["subcommands"]
    assert "inspect-run" in payload["subcommands"]


def test_schema_via_python_m_invocation() -> None:
    """``python -m infrastructure.sia schema`` works and emits valid JSON."""
    repo = Path(__file__).resolve().parents[3]
    proc = subprocess.run(
        [sys.executable, "-m", "infrastructure.sia", "schema"],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["prog"]
    assert "validate" in payload["subcommands"]
