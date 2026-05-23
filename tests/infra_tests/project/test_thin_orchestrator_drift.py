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
        body += f"def worker_{i}(x):\n    return np.sum(x ** {i})\n\n"
    body += "\n" + "pass\n" * 180
    (root / "scripts" / "fat.py").write_text(body, encoding="utf-8")
    report = Report()
    check_project_scripts(root, tmp_path, report, "demo")
    assert any(f.rule == "thin_orchestrator" for f in report.errors())


def test_repo_script_fat_raises(tmp_path: Path) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    body = "import json\n\n"
    for i in range(5):
        body += f"def step_{i}(data):\n    return data.get({i!r}, 0)\n\n"
    body += "x = 1\n" * 190
    (scripts / "fat_gate.py").write_text(body, encoding="utf-8")
    report = Report()
    check_repo_scripts(tmp_path, report)
    assert any(f.rule == "thin_orchestrator" for f in report.errors())


def test_line_count_scan_project_scripts(tmp_path: Path) -> None:
    scripts = tmp_path / "projects" / "p" / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "big.py").write_text("\n".join(["# line"] * 260), encoding="utf-8")
    _warnings, failures = scan_project_scripts(tmp_path)
    assert any("projects/p/scripts/big.py" in rel for rel, _ in failures)


def test_line_count_scan_infrastructure(tmp_path: Path) -> None:
    infra = tmp_path / "infrastructure"
    infra.mkdir()
    (infra / "huge.py").write_text("\n".join(["# line"] * 960), encoding="utf-8")
    _warnings, failures = scan_infrastructure_and_scripts(tmp_path)
    assert any("infrastructure/huge.py" in rel for rel, _ in failures)
