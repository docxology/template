"""Tests for thin-orchestrator drift detection."""

from __future__ import annotations

from pathlib import Path

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
    scripts = tmp_path / "projects" / "template_code_project" / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "big.py").write_text("\n".join(["# line"] * 260), encoding="utf-8")
    _warnings, failures = scan_project_scripts(tmp_path)
    assert any("projects/template_code_project/scripts/big.py" in rel for rel, _ in failures)


def test_line_count_scan_infrastructure(tmp_path: Path) -> None:
    infra = tmp_path / "infrastructure"
    infra.mkdir()
    (infra / "huge.py").write_text("\n".join(["# line"] * 960), encoding="utf-8")
    _warnings, failures = scan_infrastructure_and_scripts(tmp_path)
    assert any("infrastructure/huge.py" in rel for rel, _ in failures)
