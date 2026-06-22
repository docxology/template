"""Tests for the ``schema`` subcommand of infrastructure.prose.cli (no mocks)."""

from __future__ import annotations

import contextlib
import io
import json

from infrastructure.prose.cli import main


def test_schema_subcommand_emits_valid_json() -> None:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = main(["schema"])
    assert code == 0
    payload = json.loads(buffer.getvalue())
    assert payload["prog"]
    assert "subcommands" in payload
    # Existing subcommands remain in the contract (additive, no regression).
    for name in ("metrics", "outline", "quality", "report"):
        assert name in payload["subcommands"]
