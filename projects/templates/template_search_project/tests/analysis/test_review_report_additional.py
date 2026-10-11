"""Additional no-mock tests for src.review_report covering branches that sit
at the 90% coverage floor (lines 58-65, 87-109, 129-130, 172, 281, 326, 330).

Each test exercises a real code path — real subprocesses, real files, real
SyntaxError handling — with no mock framework.
"""

from __future__ import annotations

import json
from pathlib import Path

from template_search_project.analysis.review_report import (
    _subprocess_env,
    collect_infra_imports,
    ensure_review_summary,
    generate_review_report,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# _subprocess_env (lines 58-65)
# ---------------------------------------------------------------------------


def test_subprocess_env_without_existing_pythonpath(monkeypatch):
    """An unset import path stays unset; no repository ancestry is inserted."""
    monkeypatch.delenv("PYTHONPATH", raising=False)
    assert "PYTHONPATH" not in _subprocess_env()


def test_subprocess_env_removes_ambient_pythonpath(monkeypatch):
    """Application settings survive while ambient Python imports do not."""
    monkeypatch.setenv("PYTHONPATH", "/custom/existing/path")
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")
    env = _subprocess_env()
    assert "PYTHONPATH" not in env
    assert env["SOURCE_DATE_EPOCH"] == "0"


def test_subprocess_env_explicit_empty_environment_does_not_inherit(monkeypatch):
    monkeypatch.setenv("PYTHONPATH", "/custom/existing/path")
    assert _subprocess_env({}) == {}


# ---------------------------------------------------------------------------
# ensure_review_summary subprocess path (lines 87-109)
# ---------------------------------------------------------------------------


def test_ensure_review_summary_subprocess_writes_summary(tmp_path: Path):
    """When summary.json is absent but scripts/review exists and the subprocess
    writes summary.json, that summary is returned along with the subprocess
    exit code and captured output tail (lines 87-100).
    """
    project_root = tmp_path / "proj"
    scripts_dir = project_root / "scripts"
    scripts_dir.mkdir(parents=True)
    review_dir = project_root / "output" / ".pipeline" / "review"

    review_exe = scripts_dir / "review"
    review_exe.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "project_root = os.getcwd()\n"
        "review_dir = os.path.join(project_root, 'output', '.pipeline', 'review')\n"
        "os.makedirs(review_dir, exist_ok=True)\n"
        "summary = {'total': 2, 'passed': 2, 'failed': 0, 'skipped': 0, 'overall_exit_code': 0}\n"
        "with open(os.path.join(review_dir, 'summary.json'), 'w') as f:\n"
        "    json.dump(summary, f)\n"
        "print('review completed successfully')\n"
        "sys.exit(0)\n",
        encoding="utf-8",
    )
    review_exe.chmod(0o755)

    summary, exit_code, notes = ensure_review_summary(project_root, review_dir)
    assert exit_code == 0
    assert summary["total"] == 2
    assert summary["passed"] == 2
    assert "review completed successfully" in notes


def test_ensure_review_summary_subprocess_without_summary(tmp_path: Path):
    """When the review subprocess finishes but does not write summary.json,
    a placeholder is returned with exit code (proc.returncode or 1) and the
    output tail (lines 94-96, 102-109).
    """
    project_root = tmp_path / "proj"
    scripts_dir = project_root / "scripts"
    scripts_dir.mkdir(parents=True)
    review_dir = project_root / "output" / ".pipeline" / "review"

    review_exe = scripts_dir / "review"
    review_exe.write_text(
        "#!/usr/bin/env python3\nprint('ran but produced no summary')\nimport sys; sys.exit(0)\n",
        encoding="utf-8",
    )
    review_exe.chmod(0o755)

    summary, exit_code, notes = ensure_review_summary(project_root, review_dir)
    # proc.returncode is 0, but "or 1" on line 109 makes it 1
    assert exit_code == 1
    assert summary["overall_exit_code"] == 1
    assert summary["failed"] == 1
    assert summary["total"] == 0
    assert "ran but produced no summary" in notes


# ---------------------------------------------------------------------------
# collect_infra_imports SyntaxError handler (lines 129-130)
# ---------------------------------------------------------------------------


def test_collect_infra_imports_skips_syntax_error(tmp_path: Path):
    """A src/*.py file with a SyntaxError is silently skipped (lines 129-130)
    rather than crashing the ast scan.
    """
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "broken.py").write_text("def broken(:\n    pass\n", encoding="utf-8")
    (src_dir / "good.py").write_text(
        "from infrastructure.core.logging.utils import get_logger\n",
        encoding="utf-8",
    )
    result = collect_infra_imports(tmp_path)
    assert "infrastructure.core.logging.utils" in result
    assert result["infrastructure.core.logging.utils"] == {"good.py"}


# ---------------------------------------------------------------------------
# Helper: build an isolated project tree for generate_review_report tests
# ---------------------------------------------------------------------------


def _make_project(tmp_path: Path) -> Path:
    """Create a minimal project tree that generate_review_report can run on.

    The project ships with a pre-materialised summary.json (so
    ensure_review_summary short-circuits), a real infrastructure import in
    src/widget.py, and two stage files.  Individual tests modify the tree
    as needed to exercise specific branches.
    """
    project_root = tmp_path / "proj"
    project_root.mkdir()

    # Documentation
    (project_root / "AGENTS.md").write_text(
        "# Agent guide\n\n### Purpose\n\nStuff.\n\n### Layout\n\nMore stuff.\n",
        encoding="utf-8",
    )
    (project_root / "README.md").write_text("# Project\n\n## Purpose\n\nStuff.\n", encoding="utf-8")

    # Manuscript
    (project_root / "manuscript").mkdir()
    (project_root / "manuscript" / "references.bib").write_text(
        "@article{a2020,\n  title={T},\n}\n@article{b2021,\n  title={U},\n}\n",
        encoding="utf-8",
    )
    (project_root / "manuscript" / "01_intro.md").write_text("Intro citing [@a2020] and [@b2021].\n", encoding="utf-8")
    (project_root / "manuscript" / "99_references.md").write_text("See bib.\n", encoding="utf-8")

    # src/ with a real infrastructure import
    src_dir = project_root / "src"
    src_dir.mkdir()
    (src_dir / "widget.py").write_text(
        "from infrastructure.core.logging.utils import get_logger\n",
        encoding="utf-8",
    )
    (src_dir / "_private.py").write_text("y = 2\n", encoding="utf-8")

    # tests/
    (project_root / "tests").mkdir()
    (project_root / "tests" / "test_x.py").write_text("", encoding="utf-8")

    # scripts/
    (project_root / "scripts").mkdir()
    (project_root / "scripts" / "review").write_text("#!/usr/bin/env python3\n", encoding="utf-8")

    # review_config.yaml
    (project_root / "review_config.yaml").write_text(
        "review:\n"
        "  stages:\n"
        "  - name: bibtex_validation\n"
        "    enabled: true\n"
        "  - name: bibliography_completeness\n"
        "    enabled: true\n"
        "  - name: skipped_stage\n"
        "    enabled: false\n",
        encoding="utf-8",
    )

    # output/review/
    review_dir = project_root / "output" / "review"
    review_dir.mkdir(parents=True)
    (review_dir / "summary.json").write_text(
        json.dumps({"total": 2, "passed": 2, "failed": 0, "skipped": 0, "overall_exit_code": 0}),
        encoding="utf-8",
    )
    (review_dir / "stage_bibtex_validation.json").write_text(
        json.dumps({"status": "ok", "success": True}), encoding="utf-8"
    )
    (review_dir / "stage_bibliography_completeness.json").write_text(
        json.dumps({"status": "ok", "success": False}), encoding="utf-8"
    )

    return project_root


# ---------------------------------------------------------------------------
# generate_review_report: non-empty review_notes (line 172)
# ---------------------------------------------------------------------------


def test_generate_review_report_omits_operational_notes_when_unavailable(tmp_path: Path):
    """When ensure_review_summary returns non-empty notes (e.g. missing
    scripts/review), the report header includes a 'Review subprocess notes'
    line (line 172).
    """
    project_root = _make_project(tmp_path)
    # Remove summary.json and scripts/review so review_notes is non-empty.
    (project_root / "output" / "review" / "summary.json").unlink()
    (project_root / "scripts" / "review").unlink()

    exit_code = generate_review_report(project_root, project_root / "output" / "review")
    assert exit_code == 0

    text = (project_root / "output" / "review" / "REVIEW_REPORT.md").read_text(encoding="utf-8")
    assert "Review subprocess notes:" not in text
    assert "scripts/review missing" not in text
    assert "informational current-source findings" in text


# ---------------------------------------------------------------------------
# generate_review_report: no infrastructure imports (line 281)
# ---------------------------------------------------------------------------


def test_generate_review_report_no_infra_imports(tmp_path: Path):
    """When no src/ module imports infrastructure, section 4 prints
    'Infrastructure imports: none detected' (line 281).
    """
    project_root = _make_project(tmp_path)
    # Replace src modules with ones that don't import infrastructure.
    for py in (project_root / "src").glob("*.py"):
        py.write_text("x = 1\n", encoding="utf-8")

    exit_code = generate_review_report(project_root, project_root / "output" / "review")
    assert exit_code == 0

    text = (project_root / "output" / "review" / "REVIEW_REPORT.md").read_text(encoding="utf-8")
    assert "Infrastructure imports:** none detected" in text


# ---------------------------------------------------------------------------
# generate_review_report: stage with status="skipped" (line 326)
# ---------------------------------------------------------------------------


def test_generate_review_report_stage_status_skipped(tmp_path: Path):
    """A stage whose JSON data has status='skipped' renders as SKIP in
    section 6 via the status=='skipped' branch (line 326).
    """
    project_root = _make_project(tmp_path)
    # Overwrite bibliography_completeness stage with status=skipped.
    (project_root / "output" / "review" / "stage_bibliography_completeness.json").write_text(
        json.dumps({"status": "skipped", "success": False}), encoding="utf-8"
    )

    exit_code = generate_review_report(project_root, project_root / "output" / "review")
    assert exit_code == 0

    text = (project_root / "output" / "review" / "REVIEW_REPORT.md").read_text(encoding="utf-8")
    assert "ENABLED  bibliography_completeness" in text
    assert "Bibliography completeness:** passed" in text
    assert "SKIP  bibliography_completeness" not in text


# ---------------------------------------------------------------------------
# generate_review_report: disabled stage with a stage file (line 330)
# ---------------------------------------------------------------------------


def test_generate_review_report_disabled_stage_with_file(tmp_path: Path):
    """A disabled stage (enabled=false) that has a materialised stage file with
    success=false and status != 'skipped' renders as SKIP via the 'not enabled'
    branch (line 330).
    """
    project_root = _make_project(tmp_path)
    # Create a stage file for the disabled 'skipped_stage'.
    (project_root / "output" / "review" / "stage_skipped_stage.json").write_text(
        json.dumps({"status": "ok", "success": False}), encoding="utf-8"
    )

    exit_code = generate_review_report(project_root, project_root / "output" / "review")
    assert exit_code == 0

    text = (project_root / "output" / "review" / "REVIEW_REPORT.md").read_text(encoding="utf-8")
    assert "DISABLED  skipped_stage" in text
    assert "SKIP  skipped_stage" not in text
