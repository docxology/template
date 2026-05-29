"""Tests for individual detectors and run_detectors()."""

from pathlib import Path


from infrastructure.doctor.detectors import (
    detect_doctor_state_writable,
    detect_pycache_clutter,
    detect_run_sh_executable,
    detect_stale_coverage_files,
    run_detectors,
)
from infrastructure.doctor.models import Severity


def _make_min_repo(root: Path) -> None:
    """Minimal repo skeleton sufficient for detectors to run."""
    (root / "projects").mkdir()
    (root / "pyproject.toml").write_text("[project]\nname='x'\nversion='0'\n")
    (root / "uv.lock").write_text("# empty")
    # Touch run.sh as executable.
    run_sh = root / "run.sh"
    run_sh.write_text("#!/bin/sh\necho hi\n")
    run_sh.chmod(0o755)


# ---------------------------------------------------------------------------
# Individual detectors
# ---------------------------------------------------------------------------


def test_run_sh_executable_detected(tmp_path: Path):
    _make_min_repo(tmp_path)
    findings = detect_run_sh_executable(tmp_path)
    assert len(findings) == 1
    assert findings[0].code == "DOC103"
    assert findings[0].healthy is True


def test_run_sh_missing_executable_bit(tmp_path: Path):
    _make_min_repo(tmp_path)
    (tmp_path / "run.sh").chmod(0o644)
    findings = detect_run_sh_executable(tmp_path)
    assert findings[0].healthy is False
    assert findings[0].severity == Severity.WARN
    fix_ids = [rl.fix_id for rl in findings[0].repair_levels]
    assert "fix_make_run_sh_executable" in fix_ids


def test_pycache_clutter_finds_dirs(tmp_path: Path):
    _make_min_repo(tmp_path)
    (tmp_path / "infrastructure" / "core" / "__pycache__").mkdir(parents=True)
    (tmp_path / "infrastructure" / "core" / "__pycache__" / "x.pyc").write_text("compiled")
    findings = detect_pycache_clutter(tmp_path)
    assert findings[0].healthy is False
    assert findings[0].evidence["count"] == 1


def test_pycache_skips_venv_anywhere(tmp_path: Path):
    """A nested .venv anywhere in the path filters out caches inside it."""
    _make_min_repo(tmp_path)
    (tmp_path / "tools" / ".venv" / "lib" / "__pycache__").mkdir(parents=True)
    (tmp_path / "tools" / ".venv" / "lib" / "__pycache__" / "x.pyc").write_text("compiled")
    findings = detect_pycache_clutter(tmp_path)
    assert findings[0].healthy is True


def test_pycache_skips_dormant_project_subdirs(tmp_path: Path):
    _make_min_repo(tmp_path)
    (tmp_path / "projects" / "archive" / "old" / "__pycache__").mkdir(parents=True)
    (tmp_path / "projects" / "working" / "wip" / "__pycache__").mkdir(parents=True)
    findings = detect_pycache_clutter(tmp_path)
    assert findings[0].healthy is True


def test_stale_coverage_files(tmp_path: Path):
    _make_min_repo(tmp_path)
    (tmp_path / ".coverage").write_text("data")
    (tmp_path / ".coverage.infra").write_text("data")
    (tmp_path / "coverage_project.json").write_text("{}")
    findings = detect_stale_coverage_files(tmp_path)
    assert findings[0].healthy is False
    assert findings[0].evidence["files"]
    # Fix id surfaced
    assert any(rl.fix_id == "fix_clean_coverage_files" for rl in findings[0].repair_levels)


def test_doctor_state_not_writable_reports_warn(tmp_path: Path) -> None:
    doctor_dir = tmp_path / ".doctor"
    doctor_dir.mkdir()
    doctor_dir.chmod(0o444)
    try:
        findings = detect_doctor_state_writable(tmp_path)
        assert findings[0].healthy is False
        assert findings[0].severity == Severity.CRITICAL
    finally:
        doctor_dir.chmod(0o755)


def test_doctor_state_writable_does_not_create_directory(tmp_path: Path):
    findings = detect_doctor_state_writable(tmp_path)
    assert findings[0].healthy is True
    assert not (tmp_path / ".doctor").exists()
    assert not (tmp_path / ".doctor" / ".write_probe").exists()


# ---------------------------------------------------------------------------
# run_detectors orchestration
# ---------------------------------------------------------------------------


def test_run_detectors_returns_sorted_findings(tmp_path: Path):
    _make_min_repo(tmp_path)
    findings = run_detectors(tmp_path)
    codes = [f.code for f in findings]
    assert codes == sorted(codes)


def test_run_detectors_isolates_crashes(tmp_path: Path):
    _make_min_repo(tmp_path)

    def boom(_root):
        raise RuntimeError("kaboom")

    findings = run_detectors(tmp_path, selected=(boom,))
    assert any(f.severity == Severity.CRITICAL for f in findings)
    assert any("kaboom" in f.description for f in findings)


def test_run_detectors_idempotent(tmp_path: Path):
    """Same inputs → byte-identical findings (modulo evidence ordering)."""
    _make_min_repo(tmp_path)
    first = run_detectors(tmp_path)
    second = run_detectors(tmp_path)
    assert [f.code for f in first] == [f.code for f in second]
    assert [f.healthy for f in first] == [f.healthy for f in second]


def test_run_detectors_selected_subset(tmp_path: Path):
    """``selected=`` runs only the requested detectors."""
    _make_min_repo(tmp_path)
    (tmp_path / ".coverage").write_text("data")
    findings = run_detectors(tmp_path, selected=(detect_stale_coverage_files,))
    assert len(findings) == 1
    assert findings[0].code == "DOC302"


def test_orphan_output_dirs_surfaces_fix_id(tmp_path: Path):
    from infrastructure.doctor.detectors import detect_orphan_output_dirs

    _make_min_repo(tmp_path)
    orphan = tmp_path / "output" / "ghost_project"
    orphan.mkdir(parents=True)
    (orphan / "pdf").mkdir()
    findings = detect_orphan_output_dirs(tmp_path)
    assert findings
    assert findings[0].healthy is False
    fix_ids = {rl.fix_id for rl in findings[0].repair_levels}
    assert "fix_remove_orphan_output_dirs" in fix_ids
