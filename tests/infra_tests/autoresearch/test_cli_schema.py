"""Tests for the AutoResearch CLI ``schema`` subcommand (no mocks)."""

from __future__ import annotations

import contextlib
import io
import json

from infrastructure.autoresearch.cli import main


def test_schema_subcommand_emits_valid_json() -> None:
    """``schema`` returns 0 and prints a JSON parameter contract."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        exit_code = main(["schema"])
    assert exit_code == 0
    payload = json.loads(buffer.getvalue())
    assert "prog" in payload
    assert "subcommands" in payload
    # Existing subcommands remain present in the contract (no regression).
    for name in ("plan", "validate", "review-packet", "summarize", "benchmark"):
        assert name in payload["subcommands"]
