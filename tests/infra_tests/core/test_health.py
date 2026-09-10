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
        assert specs["public-capabilities"][-1] == "scripts/gates/public_capabilities.py"
        assert all("stage_01_test.py" not in argument for argument in specs["public-capabilities"])

    def test_ci_security_and_platform_oracles_fail_closed(self) -> None:
        workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        assert "continue-on-error: ${{ runner.os == 'macOS' }}" not in workflow
        assert "uv export --all-groups --all-extras --frozen" in workflow
        assert 'audit_requirements "$LOCK_REQUIREMENTS"' in workflow
        assert 'uv run pip-audit --requirement "$requirement_file"' in workflow
        assert 'uv export --project "projects/$project" --all-extras --frozen' in workflow
        assert "--no-deps --disable-pip" in workflow
        assert 'targets+=("projects/$project")' in workflow


class TestSyntheticGate:
    """A trivial stub gate script must parse correctly into a ``GateResult``."""

    @staticmethod
    def _stub_gate_repo(tmp_path: Path, script_body: str) -> Path:
        repo = tmp_path / "stub-repo"
        (repo / "scripts" / "audit").mkdir(parents=True)
        (repo / "scripts" / "audit" / "verify_no_mocks.py").write_text(script_body, encoding="utf-8")
        return repo

    def test_stub_gate_runs_via_registry_then_subprocess(
        self,
        tmp_path: Path,
    ) -> None:
        # The gate executes through the public registry path (run_health_checks
        # → real subprocess), exercising the output-parsing behavior real gates
        # rely on — no mocks, no private seams.
        report = run_health_checks(self._stub_gate_repo(tmp_path, "print('hello health')\n"), gates=["no-mocks"])

        result = report.results[0]
        assert isinstance(result, GateResult)
        assert result.name == "no-mocks"
        assert result.passed is True
        assert result.elapsed_ms >= 0.0
        assert "hello health" in result.output

    def test_stub_gate_failure_reports_stderr_tail(self, tmp_path: Path) -> None:
        repo = self._stub_gate_repo(tmp_path, "import sys; sys.stderr.write('boom'); raise SystemExit(7)\n")

        result = run_health_checks(repo, gates=["no-mocks"]).results[0]

        assert result.passed is False
        assert "boom" in result.output

    def test_stub_gate_timeout_fails_closed(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TEMPLATE_HEALTH_GATE_TIMEOUT", "0.01")
        repo = self._stub_gate_repo(tmp_path, "import time; time.sleep(1)\n")

        result = run_health_checks(repo, gates=["no-mocks"]).results[0]

        assert result.passed is False
        assert "timed out" in result.output


class TestGateTimeoutResolution:
    """The environment knob overrides gate timeouts and fails closed on bad values."""

    def test_env_override_forces_a_real_gate_timeout(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TEMPLATE_HEALTH_GATE_TIMEOUT", "0.01")
        repo = tmp_path / "timeout-repo"
        (repo / "scripts" / "audit").mkdir(parents=True)
        (repo / "scripts" / "audit" / "verify_no_mocks.py").write_text("import time; time.sleep(1)\n", encoding="utf-8")

        result = run_health_checks(repo, gates=["no-mocks"]).results[0]

        assert result.passed is False
        # The resolved override surfaces in the diagnostic tail.
        assert "gate timed out after 0.01s" in result.output

    def test_env_override_rejects_nonpositive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TEMPLATE_HEALTH_GATE_TIMEOUT", "0")
        with pytest.raises(ValueError, match="positive"):
            run_health_checks(REPO_ROOT, gates=["no-mocks"])

    def test_env_override_rejects_non_numeric(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TEMPLATE_HEALTH_GATE_TIMEOUT", "soon")
        with pytest.raises(ValueError, match="Invalid TEMPLATE_HEALTH_GATE_TIMEOUT"):
            run_health_checks(REPO_ROOT, gates=["no-mocks"])


class TestSubsetSelection:
    """``gates=[...]`` must run only the requested gates."""

    def test_subset_runs_only_named_gates(self) -> None:
        report = run_health_checks(REPO_ROOT, gates=["no-mocks"])
        assert isinstance(report, HealthReport)
        assert [r.name for r in report.results] == ["no-mocks"]

    def test_parallel_subset_preserves_requested_order(self) -> None:
        report = run_health_checks(
            REPO_ROOT,
            gates=["semantic-standins", "no-mocks"],
            workers=2,
        )
        assert report.passed is True
        assert [result.name for result in report.results] == ["semantic-standins", "no-mocks"]
        assert report.wall_elapsed_ms > 0

    def test_workers_must_be_positive(self) -> None:
        with pytest.raises(ValueError, match="workers must be at least 1"):
            run_health_checks(REPO_ROOT, gates=["no-mocks"], workers=0)

    def test_unknown_gate_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown gate"):
            run_health_checks(REPO_ROOT, gates=["does-not-exist"])

    def test_empty_list_fails_closed(self) -> None:
        with pytest.raises(ValueError, match="at least one gate"):
            run_health_checks(REPO_ROOT, gates=[])

    @pytest.mark.parametrize(
        ("script_body", "expected_pass"),
        [
            ("print('Would update 0; up-to-date 7')\n", True),  # idempotent success summary
            ("print('')\n", False),  # empty / crashed-before-work output is not proof
            ("print('stage table completed')\n", False),  # arbitrary exit-zero output
            ("print('Would update 0; up-to-date 0')\n", False),  # no up-to-date evidence
            ("print('Would update 1; up-to-date 6')\n", False),  # pending drift
            ("import sys; print('Would update 0; up-to-date 7'); sys.exit(3)\n", False),  # nonzero exit
            ("print('Would update 0; up-to-date 7'); print('Updating stale.md')\n", False),  # mutation marker
        ],
    )
    def test_stage_table_requires_complete_zero_drift_summary(
        self, tmp_path: Path, script_body: str, expected_pass: bool
    ) -> None:
        """The stage-table pass decision, exercised through the real gate registry."""
        repo = tmp_path / "stage-table-repo"
        (repo / "scripts" / "docgen").mkdir(parents=True)
        (repo / "scripts" / "docgen" / "stage_table.py").write_text(script_body, encoding="utf-8")

        report = run_health_checks(repo, gates=["stage-table"])

        assert report.results[0].passed is expected_pass


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
        assert isinstance(payload["wall_elapsed_ms"], (int, float))
        assert payload["schema_version"] == 1
        assert payload["workers"] == 1
        assert payload["repo_commit"]
        assert isinstance(payload["clean_checkout"], bool)
        assert len(payload["gate_spec_sha256"]) == 64

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


class TestRepositoryState:
    """Health reports degrade to unknown repository state when git is unavailable."""

    def test_unresolvable_git_executable_reports_unknown_state(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Real environmental fault, no mocks: a PATH with no git binary makes
        # the actual subprocess call raise FileNotFoundError.
        monkeypatch.setenv("PATH", str(tmp_path))

        report = run_health_checks(REPO_ROOT, gates=["no-mocks"])

        assert report.repo_commit is None
        assert report.clean_checkout is False


class TestFailureDiagnosticsReachStderr:
    """A failing health run must be legible from any bounded output tail.

    The 2026-09-08 hosted rehearsal ran ``health --json --quiet``; a
    docs-lint failure surfaced only as a bare exit 1 because the verdict
    and failing-gate detail lived mid-JSON on stdout. The verdict line and
    failing-gate dumps now always reach stderr (stdout stays pure JSON).
    """

    def test_failing_quiet_run_writes_verdict_only(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """--quiet suppresses the per-gate dumps, never the verdict line."""
        monkeypatch.setenv("TEMPLATE_HEALTH_GATE_TIMEOUT", "0.001")
        proc = _run_module_cli("--json", "--quiet", "--gates", "ruff")

        assert proc.returncode == 1
        assert "health verdict: passed=false failed_gates=['ruff']" in proc.stderr
        # The failing gate's captured tail is suppressed in quiet mode.
        assert "── ruff ──" not in proc.stderr
        assert "gate timed out" not in proc.stderr

    def test_failing_non_quiet_run_dumps_failing_gate_tail(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Without --quiet, the failing gate's captured tail follows the verdict."""
        monkeypatch.setenv("TEMPLATE_HEALTH_GATE_TIMEOUT", "0.001")
        proc = _run_module_cli("--gates", "ruff")

        assert proc.returncode == 1
        assert "── ruff ──" in proc.stderr
        assert "gate timed out" in proc.stderr

    def test_module_cli_wiring_keeps_stdout_pure_json_with_stderr_verdict(
        self,
    ) -> None:
        """End-to-end wiring: the real CLI emits the verdict line on stderr."""
        completed = _run_module_cli("--json", "--quiet", "--gates", "ruff")

        assert completed.returncode == 0
        payload = json.loads(completed.stdout)
        assert payload["passed"] is True
        assert "health verdict: passed=true failed_gates=[]" in completed.stderr

    def test_module_cli_timed_out_gate_reports_failure_verdict(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Real failing run: the timeout env knob forces a genuine gate failure."""
        monkeypatch.setenv("TEMPLATE_HEALTH_GATE_TIMEOUT", "0.001")
        completed = _run_module_cli("--json", "--quiet", "--gates", "ruff")

        assert completed.returncode == 1
        payload = json.loads(completed.stdout)
        assert payload["passed"] is False
        assert "health verdict: passed=false failed_gates=['ruff']" in completed.stderr
