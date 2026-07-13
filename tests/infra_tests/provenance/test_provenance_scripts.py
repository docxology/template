"""Tests for scripts/pipeline/stage_09_provenance_record.py.

No mocks. Uses real subprocess calls and direct main() invocation.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "09_provenance_record.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run_script(*args: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    """Run the provenance record script with the given arguments."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# Structural tests
# ---------------------------------------------------------------------------


class TestScriptStructure:
    def test_script_exists(self) -> None:
        """The provenance record script file exists."""
        assert SCRIPT.exists(), f"Script not found at {SCRIPT}"

    def test_script_is_valid_python(self) -> None:
        """The script has no syntax errors."""
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr}"


# ---------------------------------------------------------------------------
# --help tests
# ---------------------------------------------------------------------------


class TestScriptHelp:
    def test_script_help_exits_zero(self) -> None:
        """--help returns exit code 0."""
        result = run_script("--help")
        assert result.returncode == 0, f"--help failed: {result.stderr}"

    def test_script_help_mentions_project(self) -> None:
        """--help output mentions --project."""
        result = run_script("--help")
        assert "--project" in result.stdout

    def test_script_help_mentions_stage(self) -> None:
        """--help output mentions --stage."""
        result = run_script("--help")
        assert "--stage" in result.stdout

    def test_script_help_mentions_store_path(self) -> None:
        """--help output mentions --store-path override."""
        result = run_script("--help")
        assert "--store-path" in result.stdout


# ---------------------------------------------------------------------------
# Missing required args tests
# ---------------------------------------------------------------------------


class TestScriptMissingArgs:
    def test_script_missing_stage_exits_error(self) -> None:
        """--project without --stage returns exit code 2 (argparse required arg)."""
        result = run_script("--project", "test")
        # argparse exits 2 when a required argument is missing
        assert result.returncode in (1, 2), (
            f"Expected non-zero for missing --stage, got {result.returncode}. stderr: {result.stderr}"
        )

    def test_script_missing_stage_mentions_stage(self) -> None:
        """Error output mentions '--stage' when it is missing."""
        result = run_script("--project", "test")
        assert "--stage" in result.stderr, f"Expected '--stage' in error output: {result.stderr!r}"

    def test_script_no_args_fails(self) -> None:
        """Running the script with no arguments is a non-zero exit."""
        result = run_script()
        assert result.returncode != 0


# ---------------------------------------------------------------------------
# Graceful skip tests
# ---------------------------------------------------------------------------


class TestScriptGracefulSkip:
    def test_script_missing_project_returns_two(self) -> None:
        """--project nonexistent with a valid --stage returns exit code 2."""
        result = run_script(
            "--project",
            "nonexistent_project_xyz_12345",
            "--stage",
            "Connector Search",
        )
        assert result.returncode == 2, (
            f"Expected exit 2 for missing project, got {result.returncode}. stderr: {result.stderr}"
        )

    def test_script_missing_project_warns(self) -> None:
        """--project nonexistent emits a warning."""
        result = run_script(
            "--project",
            "nonexistent_project_xyz_12345",
            "--stage",
            "Connector Search",
        )
        combined = result.stdout + result.stderr
        assert "not found" in combined.lower() or "skip" in combined.lower(), f"Expected skip message in: {combined!r}"
