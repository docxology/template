"""Contract tests for template_active_inference public exemplar."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from infrastructure.project.discovery import discover_projects
from infrastructure.project.git_guards import ALLOWED_PROJECT_DIRS
from infrastructure.project.public_scope import public_project_names


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _project_root() -> Path:
    return _repo_root() / "projects" / "templates" / "template_active_inference"


def test_template_active_inference_is_public_and_discoverable() -> None:
    repo_root = _repo_root()
    names = {p.qualified_name for p in discover_projects(repo_root)}
    assert "templates/template_active_inference" in names
    assert "templates/template_active_inference" in public_project_names(repo_root)
    assert "projects/templates/template_active_inference/" in ALLOWED_PROJECT_DIRS


def test_required_project_layout() -> None:
    root = _project_root()
    for part in ("src", "tests", "scripts", "manuscript"):
        assert (root / part).is_dir(), f"missing {part}/"
    assert (root / "manuscript" / "sheaf" / "manifest.yaml").is_file()
    assert (root / "manuscript" / "sheaf" / "tracks.yaml").is_file()
    assert (root / "manuscript" / "sheaf" / "coverage.yaml").is_file()
    assert (root / "figures.yaml").is_file()
    assert (root / "tracks.yaml").is_file()
    assert (root / "data" / "claim_ledger.yaml").is_file()
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert "skip_combined_pytest" not in pyproject


def test_compose_manuscript_validate_only_strict() -> None:
    root = _project_root()
    result = subprocess.run(
        [sys.executable, str(root / "scripts" / "compose_manuscript.py"), "--validate-only", "--strict"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_sheaf_coverage_page_exists() -> None:
    root = _project_root()
    assert (root / "manuscript" / "00_00_sheaf_coverage.md").is_file()


def test_full_sheaf_appendix_binds_registry_tracks() -> None:
    root = _project_root()
    path = root / "manuscript" / "16_appendix_full_sheaf.md"
    if not path.is_file():
        subprocess.run(
            [sys.executable, str(root / "scripts" / "compose_manuscript.py")],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    text = path.read_text(encoding="utf-8")
    expected = (
        "prose",
        "formalism",
        "simulation",
        "pymdp",
        "visualization",
        "lean",
        "gnn",
        "ontology",
        "animation",
    )
    for track_id in expected:
        assert f"<!-- sheaf-track:{track_id} -->" in text, f"missing marker for {track_id}"


def test_coverage_json_schema_on_clean_tree() -> None:
    root = _project_root()
    json_path = root / "output" / "data" / "sheaf_coverage_matrix.json"
    if not json_path.is_file():
        subprocess.run(
            [sys.executable, str(root / "scripts" / "compose_manuscript.py")],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    import json

    sys.path.insert(0, str(root / "src"))
    from manuscript.sheaf.counts import structural_counts

    counts = structural_counts(root)
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert len(data.get("tracks") or []) == counts["sheaf_track_count"]
    assert len(data.get("sections") or []) == counts["imrad_manifest_rows"]
    gray = sum(
        1
        for section in data.get("sections") or []
        for cell in section.get("cells") or []
        if cell.get("color") == "gray"
    )
    assert gray == 0


def test_methods_sheaf_layers_in_composed_manuscript() -> None:
    root = _project_root()
    path = root / "manuscript" / "08_methods_sheaf.md"
    if not path.is_file():
        subprocess.run(
            [sys.executable, str(root / "scripts" / "compose_manuscript.py")],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    text = path.read_text(encoding="utf-8")
    assert "sheaf_layers_overview.png" in text
    assert "<!-- sheaf-layers:registry -->" in text
    assert "<!-- sheaf-layers:binding-matrix -->" in text
    assert "<!-- sheaf-layers:legend -->" in text


def test_build_lean_when_present_must_succeed() -> None:
    """Build the Lean package when lake is installed and the project ships one.

    Skipped when the lake toolchain is absent (e.g. standard CI workers that
    don't install elan/lake; only the fep-lean CI job carries the toolchain).
    """
    if shutil.which("lake") is None:
        import pytest

        pytest.skip("lake toolchain not installed — skipping Lean build contract")
    root = _project_root()
    assert (root / "lean" / "lakefile.lean").is_file()
    sys.path.insert(0, str(root / "src"))
    from gates.validation import build_lean

    code, msg = build_lean(root)
    assert code == 0, msg


def test_z_generate_writes_resolved_manuscript_without_tokens() -> None:
    root = _project_root()
    result = subprocess.run(
        [sys.executable, str(root / "scripts" / "z_generate_manuscript_variables.py"), "--allow-draft"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    resolved_dir = root / "output" / "manuscript"
    assert resolved_dir.is_dir()
    abstract = (resolved_dir / "00_abstract.md").read_text(encoding="utf-8")
    assert "{{" not in abstract
    assert "fragment tracks" in abstract.lower()
