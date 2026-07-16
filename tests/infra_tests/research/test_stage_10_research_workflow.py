"""Tests for scripts/pipeline/stage_10_research_workflow.py.

No mocks. Uses real subprocess calls against the actual script.

Regression coverage for a confirmed drift bug: the script imported a
``WORKFLOW_STAGES`` symbol and called ``ResearchWorkflow.describe()`` /
``ResearchWorkflow.stage()`` as classmethods — none of which exist on the
current ``infrastructure.research`` API — so every invocation, including
``--help``, raised ``ImportError`` at module load time. This file existing
before that fix would have caught it immediately.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "pipeline" / "stage_10_research_workflow.py"


def run_script(*args: str, cwd: Path | None = None, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(cwd) if cwd else str(REPO_ROOT),
    )


class TestScriptStructure:
    def test_script_exists(self) -> None:
        assert SCRIPT.exists(), f"Script not found at {SCRIPT}"

    def test_script_is_valid_python(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr}"


class TestScriptImportsResolve:
    def test_module_imports_without_error(self) -> None:
        """Module-level imports must resolve — regression for the WORKFLOW_STAGES ImportError."""
        result = subprocess.run(
            [sys.executable, "-c", f"import runpy; runpy.run_path({str(SCRIPT)!r}, run_name='not_main')"],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, f"Module-level import failed: {result.stderr}"
        assert "ImportError" not in result.stderr


class TestScriptDescribe:
    def test_describe_exits_zero(self) -> None:
        result = run_script("--describe")
        assert result.returncode == 0, f"--describe failed: {result.stderr}"

    def test_describe_lists_real_stage_names(self) -> None:
        result = run_script("--describe")
        for name in ("scope", "survey", "hypothesise", "experiment", "validate", "review", "write"):
            assert name in result.stdout.lower(), f"Expected stage '{name}' in --describe output"


class TestScriptStageLookup(object):
    def _enabled_project(self, tmp_path: Path) -> Path:
        project = tmp_path / "projects" / "rw_test_project"
        (project / "manuscript").mkdir(parents=True)
        (project / "manuscript" / "config.yaml").write_text("research_workflow:\n  enabled: true\n")
        return tmp_path

    def test_stage_survey_resolves(self, tmp_path: Path) -> None:
        root = self._enabled_project(tmp_path)
        result = run_script("--project", "rw_test_project", "--stage", "survey", cwd=root)
        assert result.returncode == 0, f"stage lookup failed: {result.stderr}"
        assert "survey" in result.stdout.lower()

    def test_unknown_stage_flagged(self, tmp_path: Path) -> None:
        root = self._enabled_project(tmp_path)
        result = run_script("--project", "rw_test_project", "--stage", "nonsense", cwd=root)
        assert result.returncode == 1
        assert "unknown stage" in (result.stdout + result.stderr).lower()


class TestScriptGracefulSkip:
    def test_disabled_project_returns_two(self, tmp_path: Path) -> None:
        result = run_script("--project", "nonexistent_project_xyz", "--stage", "survey", cwd=tmp_path)
        assert result.returncode == 2

    def test_malformed_yaml_returns_two_without_traceback(self, tmp_path: Path) -> None:
        project = tmp_path / "projects" / "malformed_project" / "manuscript"
        project.mkdir(parents=True)
        (project / "config.yaml").write_text("research_workflow: [\n", encoding="utf-8")

        result = run_script("--project", "malformed_project", "--stage", "survey", cwd=tmp_path)

        assert result.returncode == 2
        assert "traceback" not in result.stderr.lower()
