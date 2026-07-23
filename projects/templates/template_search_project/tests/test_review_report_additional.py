"""Additional tests for src/review_report.py — uncovered branches.

Targets lines 58-65 (_subprocess_env), 87-109 (ensure_review_summary
subprocess path), 129-130 (SyntaxError in collect_infra_imports),
172 (_bs), 281 (no infra imports), 326/330 (stage status edge cases).
All tests use real files and real subprocess calls — no mocks.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.review_report import (
    _bs,
    _subprocess_env,
    collect_infra_imports,
    ensure_review_summary,
    generate_review_report,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parents[2]


def test_subprocess_env_includes_template_root() -> None:
    """_subprocess_env must set PYTHONPATH to include the template root."""
    env = _subprocess_env()
    template_root = str(Path(__file__).resolve().parents[4])
    assert template_root in env["PYTHONPATH"]


def test_subprocess_env_preserves_existing_pythonpath(monkeypatch) -> None:
    """Existing PYTHONPATH entries are preserved, not overwritten."""
    monkeypatch.setenv("PYTHONPATH", "/existing/path")
    env = _subprocess_env()
    assert "/existing/path" in env["PYTHONPATH"]


def test_subprocess_env_without_pythonpath(monkeypatch) -> None:
    """When PYTHONPATH is unset, only the template root is set."""
    monkeypatch.delenv("PYTHONPATH", raising=False)
    env = _subprocess_env()
    template_root = str(Path(__file__).resolve().parents[4])
    assert env["PYTHONPATH"] == template_root


def test_collect_infra_imports_skips_syntax_error(tmp_path: Path) -> None:
    """A file with a SyntaxError should be silently skipped."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "broken.py").write_text(
        "from infrastructure.core.logging.utils import get_logger\n"
        "def (:  # syntax error\n",
        encoding="utf-8",
    )
    result = collect_infra_imports(tmp_path, REPO_ROOT)
    # broken.py was skipped — no entries
    assert len(result) == 0


def test_bs_counts_directory_contents(tmp_path: Path) -> None:
    """_bs returns the number of entries in a directory."""
    (tmp_path / "testdir").mkdir()
    (tmp_path / "testdir" / "a.txt").write_text("", encoding="utf-8")
    (tmp_path / "testdir" / "b.txt").write_text("", encoding="utf-8")
    assert _bs(tmp_path, "testdir") == 2


def test_ensure_review_summary_runs_subprocess_when_no_summary(tmp_path: Path) -> None:
    """When summary.json is missing, the review subprocess is invoked."""
    project_root = tmp_path / "proj"
    project_root.mkdir()
    (project_root / "scripts").mkdir(parents=True)
    # Create a review script that writes a summary.json
    review_script = project_root / "scripts" / "review"
    review_script.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        "from pathlib import Path\n"
        "project_root = Path(sys.argv[sys.argv.index('--project-root') + 1])\n"
        "review_dir = project_root / 'output' / 'review'\n"
        "review_dir.mkdir(parents=True, exist_ok=True)\n"
        "(review_dir / 'summary.json').write_text(\n"
        "    json.dumps({'total': 1, 'passed': 1, 'failed': 0, 'skipped': 0, 'overall_exit_code': 0})\n"
        ")\n",
        encoding="utf-8",
    )
    review_script.chmod(0o755)

    review_dir = project_root / "output" / "review"
    summary, exit_code, notes = ensure_review_summary(project_root, review_dir)
    assert exit_code == 0
    assert summary["total"] == 1


def test_ensure_review_summary_subprocess_no_summary_output(tmp_path: Path) -> None:
    """When the review subprocess runs but doesn't write summary.json,
    a placeholder is returned with exit code 1."""
    project_root = tmp_path / "proj"
    project_root.mkdir()
    (project_root / "scripts").mkdir(parents=True)
    # Create a review script that exits 0 but doesn't write summary.json
    review_script = project_root / "scripts" / "review"
    review_script.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "print('done')\n",
        encoding="utf-8",
    )
    review_script.chmod(0o755)

    review_dir = project_root / "output" / "review"
    summary, exit_code, notes = ensure_review_summary(project_root, review_dir)
    assert exit_code == 1
    assert summary["overall_exit_code"] == 1
    assert summary["failed"] == 1


def test_generate_review_report_no_infra_imports(tmp_path: Path) -> None:
    """When no src/ modules import infrastructure, section 4 reports 'none detected'."""
    project_root = tmp_path / "proj"
    project_root.mkdir()
    (project_root / "AGENTS.md").write_text("# Agent guide\n\n### Purpose\n\nStuff.\n\n### Layout\n\nMore stuff.\n", encoding="utf-8")
    (project_root / "README.md").write_text("# Project\n\n## Purpose\n\nStuff.\n", encoding="utf-8")
    (project_root / "manuscript").mkdir()
    (project_root / "manuscript" / "references.bib").write_text("@article{a2020,\n  title={T},\n}\n", encoding="utf-8")
    (project_root / "manuscript" / "01_intro.md").write_text("Intro citing [@a2020].\n", encoding="utf-8")
    (project_root / "manuscript" / "99_references.md").write_text("See bib.\n", encoding="utf-8")
    (project_root / "src").mkdir()
    (project_root / "src" / "no_infra.py").write_text("x = 1\n", encoding="utf-8")
    (project_root / "tests").mkdir()
    (project_root / "tests" / "test_x.py").write_text("", encoding="utf-8")
    (project_root / "scripts").mkdir()

    review_dir = project_root / "output" / "review"
    review_dir.mkdir(parents=True)
    (review_dir / "summary.json").write_text(
        json.dumps({"total": 0, "passed": 0, "failed": 0, "skipped": 0, "overall_exit_code": 0}),
        encoding="utf-8",
    )

    (project_root / "review_config.yaml").write_text(
        "review:\n  stages:\n  - name: bibtex_validation\n    enabled: true\n",
        encoding="utf-8",
    )

    exit_code = generate_review_report(project_root, REPO_ROOT, review_dir)
    assert exit_code == 0
    text = (review_dir / "REVIEW_REPORT.md").read_text(encoding="utf-8")
    assert "none detected" in text


def test_generate_review_report_stage_skipped_status(tmp_path: Path) -> None:
    """A stage with status='skipped' in its JSON should show SKIP."""
    project_root = tmp_path / "proj"
    project_root.mkdir()
    (project_root / "AGENTS.md").write_text("# Agent guide\n\n### Purpose\n\nStuff.\n\n### Layout\n\nMore stuff.\n", encoding="utf-8")
    (project_root / "README.md").write_text("# Project\n\n## Purpose\n\nStuff.\n", encoding="utf-8")
    (project_root / "manuscript").mkdir()
    (project_root / "manuscript" / "references.bib").write_text("@article{a2020,\n  title={T},\n}\n", encoding="utf-8")
    (project_root / "manuscript" / "01_intro.md").write_text("Intro citing [@a2020].\n", encoding="utf-8")
    (project_root / "manuscript" / "99_references.md").write_text("See bib.\n", encoding="utf-8")
    (project_root / "src").mkdir()
    (project_root / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    (project_root / "tests").mkdir()
    (project_root / "tests" / "test_x.py").write_text("", encoding="utf-8")
    (project_root / "scripts").mkdir()

    review_dir = project_root / "output" / "review"
    review_dir.mkdir(parents=True)
    (review_dir / "summary.json").write_text(
        json.dumps({"total": 1, "passed": 0, "failed": 1, "skipped": 0, "overall_exit_code": 1}),
        encoding="utf-8",
    )
    (review_dir / "stage_skipped_stage.json").write_text(
        json.dumps({"status": "skipped", "success": False}),
        encoding="utf-8",
    )
    (review_dir / "stage_disabled_stage.json").write_text(
        json.dumps({"status": "ok", "success": False}),
        encoding="utf-8",
    )

    (project_root / "review_config.yaml").write_text(
        "review:\n  stages:\n  - name: skipped_stage\n    enabled: true\n"
        "  - name: disabled_stage\n    enabled: false\n",
        encoding="utf-8",
    )

    exit_code = generate_review_report(project_root, REPO_ROOT, review_dir)
    assert exit_code == 0
    text = (review_dir / "REVIEW_REPORT.md").read_text(encoding="utf-8")
    assert "SKIP  skipped_stage" in text
    assert "SKIP  disabled_stage" in text


def test_generate_review_report_stage_not_materialised(tmp_path: Path) -> None:
    """A configured stage with no stage_*.json file should show SKIP (not materialised)."""
    project_root = tmp_path / "proj"
    project_root.mkdir()
    (project_root / "AGENTS.md").write_text("# Agent guide\n\n### Purpose\n\nStuff.\n\n### Layout\n\nMore stuff.\n", encoding="utf-8")
    (project_root / "README.md").write_text("# Project\n\n## Purpose\n\nStuff.\n", encoding="utf-8")
    (project_root / "manuscript").mkdir()
    (project_root / "manuscript" / "references.bib").write_text("@article{a2020,\n  title={T},\n}\n", encoding="utf-8")
    (project_root / "manuscript" / "01_intro.md").write_text("Intro.\n", encoding="utf-8")
    (project_root / "manuscript" / "99_references.md").write_text("See bib.\n", encoding="utf-8")
    (project_root / "src").mkdir()
    (project_root / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    (project_root / "tests").mkdir()
    (project_root / "tests" / "test_x.py").write_text("", encoding="utf-8")
    (project_root / "scripts").mkdir()

    review_dir = project_root / "output" / "review"
    review_dir.mkdir(parents=True)
    (review_dir / "summary.json").write_text(
        json.dumps({"total": 0, "passed": 0, "failed": 0, "skipped": 0, "overall_exit_code": 0}),
        encoding="utf-8",
    )

    (project_root / "review_config.yaml").write_text(
        "review:\n  stages:\n  - name: bibtex_validation\n    enabled: true\n"
        "  - name: unmaterialised_stage\n    enabled: true\n",
        encoding="utf-8",
    )

    exit_code = generate_review_report(project_root, REPO_ROOT, review_dir)
    assert exit_code == 0
    text = (review_dir / "REVIEW_REPORT.md").read_text(encoding="utf-8")
    assert "SKIP (disabled or not materialised)  unmaterialised_stage" in text
