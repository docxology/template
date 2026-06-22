"""Tests for the validation CLI ``schema`` subcommand (no mocks)."""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys

import pytest

from infrastructure.validation.cli import main as cli


class TestSchemaSubcommand:
    def test_schema_returns_zero_and_emits_json(self):
        """`main(["schema"])` returns 0 and prints a JSON parameter contract."""
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cli.main(["schema"])
        assert rc == 0
        payload = json.loads(buf.getvalue())
        assert payload["prog"]
        assert "subcommands" in payload
        # The schema subcommand itself plus existing subcommands are present.
        assert "schema" in payload["subcommands"]
        assert "pdf" in payload["subcommands"]
        assert "markdown" in payload["subcommands"]

    def test_existing_subcommand_still_parses(self, tmp_path):
        """An existing subcommand still dispatches and exits with its own code."""
        missing = tmp_path / "nope.pdf"
        with pytest.raises(SystemExit) as exc:
            cli.main(["pdf", str(missing)])
        assert exc.value.code == 1

    def test_help_still_exits_zero(self):
        """`--help` remains unchanged (no regression)."""
        with pytest.raises(SystemExit) as exc:
            cli.main(["--help"])
        assert exc.value.code == 0

    def test_module_invocation_emits_schema(self):
        """`python -m infrastructure.validation.cli schema` prints JSON, exits 0."""
        proc = subprocess.run(
            [sys.executable, "-m", "infrastructure.validation.cli", "schema"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0
        payload = json.loads(proc.stdout)
        assert payload["prog"]
