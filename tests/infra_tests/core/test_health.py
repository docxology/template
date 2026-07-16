"""Real-data tests for ``infrastructure.core.health``.

The unified health command is itself a thin subprocess orchestrator, so
the tests exercise it the same way: real ``subprocess.run`` calls, a
real repo root, and assertions against actual gate outputs. No mocks.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import is_dataclass
from pathlib import Path

import pytest

from infrastructure.core.health import (
    GATE_NAMES,
    GateResult,
    HealthReport,
    build_gate_specs,
    format_report_table,
    run_health_checks,
)
from infrastructure.core.health import _stage_table_passed

REPO_ROOT = Path(__file__).resolve().parents[3]


def _run_module_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Invoke ``python -m infrastructure.core.health`` against the live repo."""

    cmd = [
        sys.executable,
        "-m",
        "infrastructure.core.health",
        "--repo-root",
        str(REPO_ROOT),
        *args,
    ]
    return subprocess.run(  # noqa: S603 — argv list, no shell.
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


class TestPublicSurface:
    """The public dataclasses and registry stay stable."""

    def test_gate_result_is_frozen_dataclass(self) -> None:
        assert is_dataclass(GateResult)
        assert is_dataclass(HealthReport)

    def test_gate_names_are_unique_and_non_empty(self) -> None:
        assert len(GATE_NAMES) == len(set(GATE_NAMES))
        assert all(name and name.islower() for name in GATE_NAMES)

    def test_build_gate_specs_returns_argv_lists(self) -> None:
        specs = build_gate_specs(REPO_ROOT)
        assert {name for name, _ in specs} == set(GATE_NAMES)
        for _, argv in specs:
            assert isinstance(argv, list)
            assert all(isinstance(arg, str) for arg in argv)
            assert len(argv) >= 1

    def test_build_gate_specs_uses_public_project_scope(self, tmp_path: Path) -> None:
        """Lint/type gates must not follow local rotating project symlinks."""
        (tmp_path / "projects" / "templates" / "template_code_project" / "src").mkdir(parents=True)
        (tmp_path / "projects" / "private_research_project" / "src").mkdir(parents=True)

        specs = dict(build_gate_specs(tmp_path))

        for gate in ("mypy", "ruff", "ruff-format"):
            argv = specs[gate]
            assert "projects/templates/template_code_project/src" in argv
            assert "projects/private_research_project/src" not in argv

        assert "projects/" not in specs["bandit"]
        assert "projects/templates/template_code_project/" in specs["bandit"]
        assert all("projects/private_research_project" not in arg for arg in specs["bandit"])
        for gate in (
            "confidentiality",
            "generated-artifacts",
            "template-drift",
            "counts",
            "skills-manifest",
            "semantic-standins",
            "operations-manifest",
            "skill-reachability",
        ):
            assert gate in specs

        assert specs["semantic-standins"][-3:] == [
            "--inventory",
            "--max-dependency-replacements",
            "0",
        ]
        assert specs["operations-manifest"][-1] == "operations-check"
        assert specs["skill-reachability"][-1] == "scripts/gates/skill_reachability_check.py"

    def test_ci_security_and_platform_oracles_fail_closed(self) -> None:
        workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        assert "continue-on-error: ${{ runner.os == 'macOS' }}" not in workflow
        assert "uv export --all-groups --all-extras --frozen" in workflow
        assert 'pip-audit --requirement "$LOCK_REQUIREMENTS"' in workflow
        assert "--no-deps --disable-pip" in workflow
        assert 'targets+=("projects/$project")' in workflow


class TestSyntheticGate:
    """A trivial echo gate must parse correctly into a ``GateResult``."""

    def test_synthetic_gate_runs_via_register_then_subprocess(
        self,
        tmp_path: Path,
    ) -> None:
        # Hand-roll a minimal gate by calling the underlying private helper
        # via the module's own subprocess — keeps the test mock-free while
        # exercising the parsing path that real gates use.
        from infrastructure.core.health import _run_single_gate  # noqa: PLC0415

        result = _run_single_gate(
            "synthetic-echo",
            [sys.executable, "-c", "print('hello health'); raise SystemExit(0)"],
            tmp_path,
        )
        assert isinstance(result, GateResult)
        assert result.name == "synthetic-echo"
        assert result.passed is True
        assert result.elapsed_ms >= 0.0
        assert "hello health" in result.output

    def test_synthetic_failing_gate_reports_failure(self, tmp_path: Path) -> None:
        from infrastructure.core.health import _run_single_gate  # noqa: PLC0415

        result = _run_single_gate(
            "synthetic-fail",
            [sys.executable, "-c", "import sys; sys.stderr.write('boom'); sys.exit(7)"],
            tmp_path,
        )
        assert result.passed is False
        assert "boom" in result.output

    def test_synthetic_gate_timeout_fails_closed(self, tmp_path: Path) -> None:
        from infrastructure.core.health import _run_single_gate  # noqa: PLC0415

        result = _run_single_gate(
            "synthetic-timeout",
            [sys.executable, "-c", "import time; time.sleep(1)"],
            tmp_path,
            timeout_seconds=0.01,
        )
        assert result.passed is False
        assert "timed out" in result.output


class TestSubsetSelection:
    """``gates=[...]`` must run only the requested gates."""

    def test_subset_runs_only_named_gates(self) -> None:
        report = run_health_checks(REPO_ROOT, gates=["no-mocks"])
        assert isinstance(report, HealthReport)
        assert [r.name for r in report.results] == ["no-mocks"]

    def test_unknown_gate_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown gate"):
            run_health_checks(REPO_ROOT, gates=["does-not-exist"])

    def test_empty_list_fails_closed(self) -> None:
        with pytest.raises(ValueError, match="at least one gate"):
            run_health_checks(REPO_ROOT, gates=[])

    def test_stage_table_requires_complete_zero_drift_summary(self) -> None:
        assert _stage_table_passed(0, "Would update 0; up-to-date 7") is True
        assert _stage_table_passed(0, "") is False
        assert _stage_table_passed(0, "stage table completed") is False
        assert _stage_table_passed(0, "Would update 0; up-to-date 0") is False
        assert _stage_table_passed(0, "Would update 1; up-to-date 6") is False


class TestRealGate:
    """Run a real gate against the live tree and assert it passes."""

    def test_no_mocks_gate_passes_on_clean_tree(self) -> None:
        report = run_health_checks(REPO_ROOT, gates=["no-mocks"])
        assert report.passed is True, f"verify_no_mocks failed unexpectedly:\n{report.results[0].output}"
        assert report.results[0].name == "no-mocks"
        assert report.results[0].elapsed_ms > 0


class TestRendering:
    """``format_report_table`` produces sensible plain and coloured output."""

    def test_plain_table_contains_gate_names_and_overall(self) -> None:
        report = run_health_checks(REPO_ROOT, gates=["no-mocks"])
        text = format_report_table(report, color=False)
        assert "no-mocks" in text
        assert "PASS" in text
        assert "Overall" in text
        # No ANSI escape when colour is disabled.
        assert "\033[" not in text

    def test_colored_table_contains_ansi(self) -> None:
        report = run_health_checks(REPO_ROOT, gates=["no-mocks"])
        text = format_report_table(report, color=True)
        assert "\033[" in text


class TestCLI:
    """The ``python -m infrastructure.core.health`` entry point."""

    def test_json_output_is_parseable(self) -> None:
        proc = _run_module_cli("--json", "--gates=no-mocks", "--quiet")
        assert proc.returncode == 0, proc.stderr
        payload = json.loads(proc.stdout)
        assert payload["passed"] is True
        assert isinstance(payload["results"], list)
        assert payload["results"][0]["name"] == "no-mocks"
        assert "elapsed_ms" in payload["results"][0]
        assert isinstance(payload["total_elapsed_ms"], (int, float))

    def test_unknown_gate_exits_non_zero(self) -> None:
        proc = _run_module_cli("--gates=not-a-gate")
        assert proc.returncode != 0
        assert "unknown gate" in proc.stderr.lower()

    def test_empty_gate_expression_exits_non_zero(self) -> None:
        proc = _run_module_cli("--gates=,")
        assert proc.returncode != 0
        assert "at least one gate" in proc.stderr.lower()

    def test_help_lists_all_gates(self) -> None:
        # argparse wraps help text to ``COLUMNS``; widen so the choices
        # list is rendered intact and we can assert each gate appears.
        cmd = [
            sys.executable,
            "-m",
            "infrastructure.core.health",
            "--repo-root",
            str(REPO_ROOT),
            "--help",
        ]
        proc = subprocess.run(  # noqa: S603 — argv list, no shell.
            cmd,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
            env={**__import__("os").environ, "COLUMNS": "1000"},
        )
        assert proc.returncode == 0
        for name in GATE_NAMES:
            assert name in proc.stdout, f"missing gate {name!r} in help"
