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


# ---------------------------------------------------------------------------
# Layout detector — detect_project_structure
# ---------------------------------------------------------------------------


def _make_valid_project(parent: Path, name: str) -> Path:
    """Create a minimal valid project directory (src + tests + a Python file)."""
    proj = parent / name
    src = proj / "src"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text("")
    (proj / "tests").mkdir()
    return proj


def test_detect_project_structure_missing_projects_dir(tmp_path: Path):
    """Returns a DOC201 ERROR Finding when the projects/ directory does not exist."""
    from infrastructure.doctor.detectors.layout import detect_project_structure

    # Do NOT create a projects/ directory
    findings = detect_project_structure(tmp_path)
    assert len(findings) == 1
    f = findings[0]
    assert f.code == "DOC201"
    assert f.healthy is False
    assert f.severity == Severity.ERROR
    assert "projects/" in f.title or "missing" in f.title


def test_detect_project_structure_happy_path(tmp_path: Path):
    """Returns a healthy DOC201 INFO Finding when projects are discovered."""
    from infrastructure.doctor.detectors.layout import detect_project_structure

    projects_dir = tmp_path / "projects" / "templates"
    projects_dir.mkdir(parents=True)
    _make_valid_project(projects_dir, "my_project")

    findings = detect_project_structure(tmp_path)
    # First finding should be the discovery summary — healthy INFO
    discovery = findings[0]
    assert discovery.code == "DOC201"
    assert discovery.healthy is True
    assert discovery.severity == Severity.INFO


def test_detect_project_structure_pyproject_missing_emits_warn(tmp_path: Path):
    """Emits a DOC202 WARN Finding for each project missing a pyproject.toml."""
    from infrastructure.doctor.detectors.layout import detect_project_structure

    projects_dir = tmp_path / "projects" / "templates"
    projects_dir.mkdir(parents=True)
    _make_valid_project(projects_dir, "no_pyproject")
    # Deliberately no pyproject.toml inside the project directory

    findings = detect_project_structure(tmp_path)
    codes = [f.code for f in findings]
    # At least one finding must contain DOC202
    doc202 = [f for f in findings if f.code.startswith("DOC202")]
    assert doc202, f"Expected a DOC202 finding; got codes: {codes}"
    assert doc202[0].healthy is False
    assert doc202[0].severity == Severity.WARN


def test_detect_project_structure_with_pyproject_no_doc202(tmp_path: Path):
    """No DOC202 warnings when every project has a pyproject.toml."""
    from infrastructure.doctor.detectors.layout import detect_project_structure

    projects_dir = tmp_path / "projects" / "templates"
    projects_dir.mkdir(parents=True)
    proj = _make_valid_project(projects_dir, "complete_project")
    (proj / "pyproject.toml").write_text("[project]\nname='complete_project'\nversion='0'\n")

    findings = detect_project_structure(tmp_path)
    doc202 = [f for f in findings if f.code.startswith("DOC202")]
    assert not doc202, f"Unexpected DOC202 findings: {doc202}"


# ---------------------------------------------------------------------------
# Layout detector — detect_manuscript_config
# ---------------------------------------------------------------------------


def _make_project_with_manuscript(parent: Path, name: str) -> Path:
    """Create a project that has a manuscript/ directory (triggers config checks)."""
    proj = _make_valid_project(parent, name)
    (proj / "manuscript").mkdir()
    return proj


def test_detect_manuscript_config_missing_config_file(tmp_path: Path):
    """Emits a DOC203 WARN Finding when manuscript/config.yaml is absent."""
    from infrastructure.doctor.detectors.layout import detect_manuscript_config

    projects_dir = tmp_path / "projects" / "templates"
    projects_dir.mkdir(parents=True)
    _make_project_with_manuscript(projects_dir, "no_config")

    findings = detect_manuscript_config(tmp_path)
    assert findings, "Expected at least one finding"
    doc203 = [f for f in findings if "DOC203" in f.code]
    assert doc203
    assert doc203[0].healthy is False
    assert doc203[0].severity == Severity.WARN


def test_detect_manuscript_config_yaml_parse_error(tmp_path: Path):
    """Emits a DOC203 ERROR Finding when config.yaml is not valid YAML."""
    from infrastructure.doctor.detectors.layout import detect_manuscript_config

    projects_dir = tmp_path / "projects" / "templates"
    projects_dir.mkdir(parents=True)
    proj = _make_project_with_manuscript(projects_dir, "bad_yaml")
    cfg = proj / "manuscript" / "config.yaml"
    # Deliberately malformed YAML
    cfg.write_text("key: [\nbad yaml: {unclosed\n")

    findings = detect_manuscript_config(tmp_path)
    doc203 = [f for f in findings if "DOC203" in f.code]
    assert doc203
    error_findings = [f for f in doc203 if f.severity == Severity.ERROR]
    assert error_findings, f"Expected ERROR severity; got: {[f.severity for f in doc203]}"
    assert error_findings[0].healthy is False


def test_detect_manuscript_config_title_missing_warn(tmp_path: Path):
    """Emits a DOC203 WARN Finding when config.yaml exists but paper.title is empty."""
    from infrastructure.doctor.detectors.layout import detect_manuscript_config

    projects_dir = tmp_path / "projects" / "templates"
    projects_dir.mkdir(parents=True)
    proj = _make_project_with_manuscript(projects_dir, "empty_title")
    cfg = proj / "manuscript" / "config.yaml"
    cfg.write_text("paper:\n  title: ''\n")

    findings = detect_manuscript_config(tmp_path)
    doc203 = [f for f in findings if "DOC203" in f.code]
    assert doc203
    warn_findings = [f for f in doc203 if f.severity == Severity.WARN]
    assert warn_findings
    assert any("title" in f.title.lower() or "title" in f.description.lower() for f in warn_findings)


def test_detect_manuscript_config_paper_title_ok(tmp_path: Path):
    """Emits a healthy DOC203 INFO Finding when paper.title is present and non-empty."""
    from infrastructure.doctor.detectors.layout import detect_manuscript_config

    projects_dir = tmp_path / "projects" / "templates"
    projects_dir.mkdir(parents=True)
    proj = _make_project_with_manuscript(projects_dir, "good_paper")
    cfg = proj / "manuscript" / "config.yaml"
    cfg.write_text("paper:\n  title: 'My Research Paper'\n")

    findings = detect_manuscript_config(tmp_path)
    doc203 = [f for f in findings if "DOC203" in f.code]
    assert doc203
    assert doc203[0].healthy is True
    assert doc203[0].severity == Severity.INFO


def test_detect_manuscript_config_book_title_fallback(tmp_path: Path):
    """Healthy DOC203 INFO when book.title is present and paper key is absent."""
    from infrastructure.doctor.detectors.layout import detect_manuscript_config

    projects_dir = tmp_path / "projects" / "templates"
    projects_dir.mkdir(parents=True)
    proj = _make_project_with_manuscript(projects_dir, "good_book")
    cfg = proj / "manuscript" / "config.yaml"
    cfg.write_text("book:\n  title: 'My Book Project'\n")

    findings = detect_manuscript_config(tmp_path)
    doc203 = [f for f in findings if "DOC203" in f.code]
    assert doc203
    assert doc203[0].healthy is True
    assert "My Book Project" in doc203[0].description


def test_detect_manuscript_config_data_not_dict_warns(tmp_path: Path):
    """Emits a DOC203 WARN when config.yaml parses to a non-dict value."""
    from infrastructure.doctor.detectors.layout import detect_manuscript_config

    projects_dir = tmp_path / "projects" / "templates"
    projects_dir.mkdir(parents=True)
    proj = _make_project_with_manuscript(projects_dir, "scalar_yaml")
    cfg = proj / "manuscript" / "config.yaml"
    # YAML parses to a plain string, not a dict
    cfg.write_text("just a bare string\n")

    findings = detect_manuscript_config(tmp_path)
    doc203 = [f for f in findings if "DOC203" in f.code]
    assert doc203
    assert doc203[0].healthy is False


def test_detect_manuscript_config_skips_projects_without_manuscript(tmp_path: Path):
    """Projects without manuscript/ are silently skipped — no DOC203 findings."""
    from infrastructure.doctor.detectors.layout import detect_manuscript_config

    projects_dir = tmp_path / "projects" / "templates"
    projects_dir.mkdir(parents=True)
    # Valid project but no manuscript/ directory
    _make_valid_project(projects_dir, "code_only")

    findings = detect_manuscript_config(tmp_path)
    doc203 = [f for f in findings if "DOC203" in f.code]
    assert not doc203, f"Should produce no DOC203 findings; got: {doc203}"
