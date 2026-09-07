"""Thin gate-script test for scripts/gates/status_freshness.py.

The gate is an opt-in CLI that wires ``--repo-root`` / ``--as-of`` /
``--max-age-days`` to :func:`infrastructure.validation.status_freshness.validate_status_file`.
These tests exercise the thin CLI (exit codes + output) against a real temporary
``STATUS.md``; the parsing/findings logic itself is covered by
``tests/infra_tests/validation/test_status_freshness.py``.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

_GOOD = """# Subsystem Status

**Last updated:** 2026-08-08

| ID | Subsystem | Last verified | Verified by | Verification scope | Command | Receipt | Mode | Health |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| STATUS-PIPELINE-1 | Pipeline | 2026-08-07 | Maintainer | real run | `uv run pytest tests -q` | docs/_generated/status_evidence.json | automated | healthy |
"""


def _run_gate(status_dir: Path, *, as_of: str) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts/gates/status_freshness.py"),
            "--repo-root",
            str(status_dir),
            "--as-of",
            as_of,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_gate_exits_zero_for_fresh_ledger(tmp_path: Path) -> None:
    (tmp_path / "STATUS.md").write_text(_GOOD, encoding="utf-8")
    result = _run_gate(tmp_path, as_of="2026-08-08")
    assert result.returncode == 0
    assert "OK" in result.stdout


def test_gate_exits_nonzero_for_stale_ledger(tmp_path: Path) -> None:
    (tmp_path / "STATUS.md").write_text(_GOOD.replace("2026-08-07", "2025-12-01"), encoding="utf-8")
    result = _run_gate(tmp_path, as_of="2026-08-08")
    assert result.returncode != 0
    assert "FAIL" in result.stdout


def test_gate_reports_cannot_read_missing_file(tmp_path: Path) -> None:
    result = _run_gate(tmp_path, as_of="2026-08-08")
    assert result.returncode != 0
    assert "cannot read" in result.stdout
