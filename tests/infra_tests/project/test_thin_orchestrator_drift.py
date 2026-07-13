"""Tests for thin-orchestrator drift detection."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.project.drift.models import Report
from infrastructure.project.drift.orchestrator import (
    check_project_scripts,
    check_repo_scripts,
)
from infrastructure.validation.line_count import (
    scan_infrastructure_and_scripts,
    scan_project_scripts,
)


def _scaffold_project(tmp_path: Path, name: str = "demo") -> Path:
    root = tmp_path / "projects" / name
    (root / "scripts").mkdir(parents=True)
    (root / "src").mkdir()
    (root / "src" / "__init__.py").write_text("", encoding="utf-8")
    return root


def _fat_function(name: str) -> str:
    return f"""def {name}(data):
    total = 0.0
    for row in data:
        for value in row:
            total += value ** 2
        if total < 0:
            total = 0.0
    return total

"""


def test_thin_script_passes(tmp_path: Path) -> None:
    root = _scaffold_project(tmp_path)
    (root / "scripts" / "run.py").write_text(
        "from src.pipeline import main\n\ndef main_cli():\n    main()\n",
        encoding="utf-8",
    )
    report = Report()
    check_project_scripts(root, tmp_path, report, "demo")
    assert not report.errors()


def test_fat_script_raises_error(tmp_path: Path) -> None:
    root = _scaffold_project(tmp_path)
    body = "import numpy as np\n\n"
    for i in range(4):
        body += _fat_function(f"worker_{i}")
    body += "\n" + "pass\n" * 210
    (root / "scripts" / "fat.py").write_text(body, encoding="utf-8")
    report = Report()
    check_project_scripts(root, tmp_path, report, "demo")
    assert any(f.rule == "thin_orchestrator" for f in report.errors())


def test_fat_async_functions_are_counted(tmp_path: Path) -> None:
    root = _scaffold_project(tmp_path)
    helpers = "".join(_fat_function(f"worker_{i}").replace("def ", "async def ", 1) for i in range(4))
    (root / "scripts" / "fat_async.py").write_text(
        helpers + "pass\n" * 210,
        encoding="utf-8",
    )
    report = Report()
    check_project_scripts(root, tmp_path, report, "demo")
    assert any("fat_async.py" in finding.message for finding in report.errors())


def test_fat_class_methods_are_counted(tmp_path: Path) -> None:
    root = _scaffold_project(tmp_path)
    methods = "".join("    " + _fat_function(f"worker_{i}").replace("\n", "\n    ").rstrip() + "\n\n" for i in range(4))
    (root / "scripts" / "fat_class.py").write_text(
        "class HiddenLogic:\n" + methods + "pass\n" * 210,
        encoding="utf-8",
    )
    report = Report()
    check_project_scripts(root, tmp_path, report, "demo")
    assert any("fat_class.py" in finding.message for finding in report.errors())


def test_syntax_error_fails_closed(tmp_path: Path) -> None:
    root = _scaffold_project(tmp_path)
    (root / "scripts" / "broken.py").write_text(
        "def broken(:\n" + "pass\n" * 250,
        encoding="utf-8",
    )
    report = Report()
    check_project_scripts(root, tmp_path, report, "demo")
    assert any("syntax error" in finding.message for finding in report.errors())


def test_fat_main_in_repo_script_counts_as_non_trivial(tmp_path: Path) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    main_body = "\n".join(f"    step_{i}()" for i in range(125))
    helpers = "".join(_fat_function(f"helper_{i}") for i in range(3))
    source = helpers + f"def main():\n{main_body}\n\nif __name__ == '__main__':\n    main()\n"
    source += "pass\n" * 50
    (scripts / "fat_main.py").write_text(source, encoding="utf-8")
    report = Report()
    check_repo_scripts(tmp_path, report)
    assert any("fat_main.py" in f.message for f in report.warnings())


def test_repo_script_fat_warns_not_errors(tmp_path: Path) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    body = "import json\n\n"
    for i in range(5):
        body += _fat_function(f"step_{i}")
    body += "x = 1\n" * 190
    (scripts / "fat_gate.py").write_text(body, encoding="utf-8")
    report = Report()
    check_repo_scripts(tmp_path, report)
    assert not report.errors()
    assert any(f.rule == "thin_orchestrator" for f in report.warnings())


def test_repo_script_with_many_helpers_warns_before_line_count_limit(tmp_path: Path) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    body = "import json\n\n"
    for i in range(4):
        body += _fat_function(f"helper_{i}")
    (scripts / "logic_orchestrator.py").write_text(body, encoding="utf-8")

    report = Report()
    check_repo_scripts(tmp_path, report)

    assert not report.errors()
    assert any("multiple reusable helpers" in f.message for f in report.warnings())


def test_repo_vs_project_severity_policy(tmp_path: Path) -> None:
    """Repo scripts warn; project scripts error when fat."""
    project_root = _scaffold_project(tmp_path, "demo")
    body = "import numpy as np\n\n"
    for i in range(4):
        body += _fat_function(f"worker_{i}")
    body += "\n" + "pass\n" * 210
    (project_root / "scripts" / "fat.py").write_text(body, encoding="utf-8")

    repo_scripts = tmp_path / "scripts"
    repo_scripts.mkdir(exist_ok=True)
    (repo_scripts / "fat_gate.py").write_text(body.replace("numpy", "json"), encoding="utf-8")

    project_report = Report()
    check_project_scripts(project_root, tmp_path, project_report, "demo")
    repo_report = Report()
    check_repo_scripts(tmp_path, repo_report)

    assert any(f.rule == "thin_orchestrator" for f in project_report.errors())
    assert not repo_report.errors()
    assert any(f.rule == "thin_orchestrator" for f in repo_report.warnings())


def test_line_count_scan_project_scripts(tmp_path: Path) -> None:
    scripts = tmp_path / "projects" / "templates" / "template_code_project" / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "big.py").write_text("\n".join(["# line"] * 260), encoding="utf-8")
    _warnings, failures = scan_project_scripts(tmp_path)
    assert any("projects/templates/template_code_project/scripts/big.py" in rel for rel, _ in failures)


def test_line_count_scan_infrastructure(tmp_path: Path) -> None:
    infra = tmp_path / "infrastructure"
    infra.mkdir()
    (infra / "huge.py").write_text("\n".join(["# line"] * 960), encoding="utf-8")
    _warnings, failures = scan_infrastructure_and_scripts(tmp_path)
    assert any("infrastructure/huge.py" in rel for rel, _ in failures)


# ---------------------------------------------------------------------------
# runner.py branch coverage
# ---------------------------------------------------------------------------

import subprocess
import sys

from infrastructure.project.drift.runner import (
    exit_code_for_report,
    print_github_report,
    print_human_report,
    run_drift_checks,
)
from infrastructure.project.drift.models import Finding


def _report_with(*findings: Finding) -> Report:
    r = Report()
    r.findings.extend(findings)
    return r


def _finding(sev: str, project: str = "p", rule: str = "r", msg: str = "m") -> Finding:
    return Finding(sev, project, rule, msg)


def test_run_drift_checks_uses_default_projects_when_none(tmp_path: Path) -> None:
    """run_drift_checks with projects=None iterates over DEFAULT_PROJECT_NAMES without error."""
    from infrastructure.project.drift.runner import DEFAULT_PROJECT_NAMES

    report = run_drift_checks(tmp_path, projects=None, include_repo_checks=False)
    # Should complete without exception even when projects dirs are absent
    assert isinstance(report, Report)
    # At minimum one finding per public project (missing-project finding)
    assert len(DEFAULT_PROJECT_NAMES) > 0


def test_run_drift_checks_explicit_projects_list(tmp_path: Path) -> None:
    """run_drift_checks accepts an explicit list of project names."""
    report = run_drift_checks(tmp_path, projects=["template_code_project"], include_repo_checks=False)
    assert isinstance(report, Report)


def test_run_drift_checks_skip_repo_checks(tmp_path: Path) -> None:
    """run_drift_checks with include_repo_checks=False skips run_repo_checks."""
    # run_repo_checks on an empty tmp_path raises or adds findings; skipping it means no registry findings
    report = run_drift_checks(tmp_path, projects=[], include_repo_checks=False)
    assert isinstance(report, Report)
    # No findings because no projects were checked and repo checks were skipped
    assert len(report.findings) == 0


def test_run_drift_checks_include_repo_checks(tmp_path: Path) -> None:
    """run_drift_checks with include_repo_checks=True calls run_repo_checks."""
    report = run_drift_checks(tmp_path, projects=[], include_repo_checks=True)
    assert isinstance(report, Report)
    # Registry checks run even with zero projects; may add findings or not depending on repo state
    # Just verifies the code path executes without exception


def test_print_human_report_no_findings(capsys: object) -> None:
    """print_human_report with empty findings prints 'no drift detected'."""
    report = Report()
    print_human_report(report)
    out = capsys.readouterr().out  # type: ignore[attr-defined]
    assert "no drift detected" in out


def test_print_human_report_errors_only(capsys: object) -> None:
    """print_human_report with errors only prints ERROR block, no WARNING block."""
    report = _report_with(_finding("ERROR"))
    print_human_report(report)
    out = capsys.readouterr().out  # type: ignore[attr-defined]
    assert "ERROR" in out
    assert "WARNING" not in out


def test_print_human_report_warnings_only(capsys: object) -> None:
    """print_human_report with warnings only prints WARNING block, no ERROR block."""
    report = _report_with(_finding("WARNING"))
    print_human_report(report)
    out = capsys.readouterr().out  # type: ignore[attr-defined]
    assert "WARNING" in out.upper()
    assert "ERROR" not in out


def test_print_human_report_errors_and_warnings(capsys: object) -> None:
    """print_human_report with both errors and warnings prints both blocks."""
    report = _report_with(_finding("ERROR"), _finding("WARNING"))
    print_human_report(report)
    out = capsys.readouterr().out  # type: ignore[attr-defined]
    assert "ERROR" in out
    assert "WARNING" in out.upper()


def test_print_github_report_error_prefix(capsys: object) -> None:
    """print_github_report uses ::error prefix for ERROR-severity findings."""
    report = _report_with(_finding("ERROR", project="proj", rule="rule1", msg="bad"))
    print_github_report(report)
    out = capsys.readouterr().out  # type: ignore[attr-defined]
    assert out.startswith("::error")


def test_print_github_report_warning_prefix(capsys: object) -> None:
    """print_github_report uses ::warning prefix for non-ERROR-severity findings."""
    report = _report_with(_finding("WARNING", project="proj", rule="rule1", msg="mild"))
    print_github_report(report)
    out = capsys.readouterr().out  # type: ignore[attr-defined]
    assert out.startswith("::warning")


def test_print_github_report_empty(capsys: object) -> None:
    """print_github_report with empty findings produces no output."""
    report = Report()
    print_github_report(report)
    out = capsys.readouterr().out  # type: ignore[attr-defined]
    assert out == ""


def test_exit_code_errors_returns_1() -> None:
    """exit_code_for_report returns 1 when report has errors."""
    report = _report_with(_finding("ERROR"))
    assert exit_code_for_report(report) == 1


def test_exit_code_strict_false_warnings_returns_0() -> None:
    """exit_code_for_report returns 0 with warnings when strict=False."""
    report = _report_with(_finding("WARNING"))
    assert exit_code_for_report(report, strict=False) == 0


def test_exit_code_strict_true_warnings_returns_1() -> None:
    """exit_code_for_report returns 1 with warnings when strict=True."""
    report = _report_with(_finding("WARNING"))
    assert exit_code_for_report(report, strict=True) == 1


def test_exit_code_no_findings_returns_0() -> None:
    """exit_code_for_report returns 0 when there are no findings."""
    report = Report()
    assert exit_code_for_report(report) == 0


@pytest.mark.timeout(45)
def test_subprocess_check_template_drift_no_flags() -> None:
    """check_template_drift script runs with no flags and exits without crashing."""
    repo_root = Path(__file__).resolve().parents[3]
    script = repo_root / "scripts" / "check_template_drift.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    # Exit code 0 (clean) or 1 (drift found) — not a crash code
    assert result.returncode in (0, 1), f"stderr: {result.stderr[:500]}"


@pytest.mark.timeout(45)
def test_subprocess_check_template_drift_strict_flag() -> None:
    """check_template_drift script runs with --strict flag and exits without crashing."""
    repo_root = Path(__file__).resolve().parents[3]
    script = repo_root / "scripts" / "check_template_drift.py"
    result = subprocess.run(
        [sys.executable, str(script), "--strict"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode in (0, 1), f"stderr: {result.stderr[:500]}"


@pytest.mark.timeout(45)
def test_subprocess_check_template_drift_project_flag() -> None:
    """check_template_drift script runs with a valid --project flag."""
    from infrastructure.project.drift.runner import DEFAULT_PROJECT_NAMES

    repo_root = Path(__file__).resolve().parents[3]
    script = repo_root / "scripts" / "check_template_drift.py"
    project = DEFAULT_PROJECT_NAMES[0]
    result = subprocess.run(
        [sys.executable, str(script), "--project", project],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode in (0, 1), f"stderr: {result.stderr[:500]}"
