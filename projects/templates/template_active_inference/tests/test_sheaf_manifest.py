from pathlib import Path

import pytest

from gates.validation import validate_manuscript
from manuscript.sheaf import (
    SheafManifest,
    SheafSection,
    build_coverage_matrix,
    compose_all_sections,
    load_manifest,
    load_track_registry,
    validate_coverage_strict,
    validate_manifest,
)
from gate_support import ensure_gate_artifacts, refresh_generated_gate_artifacts


pytestmark = [pytest.mark.long_running, pytest.mark.timeout(300)]

def test_manifest_loads_imrad_sections() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(root / "manuscript" / "sheaf" / "manifest.yaml")
    assert len(manifest.sections) == 17
    assert manifest.sections[0].id == "intro"
    assert manifest.sections[0].kind == "group"
    appendix = next(s for s in manifest.sections if s.id == "appendix_full_sheaf")
    assert len(appendix.tracks) == 33
    assert sum(1 for s in manifest.sections if s.should_compose()) == 12
    # Every IMRAD block now carries a group row (uniform base poset).
    assert sum(1 for s in manifest.sections if s.kind == "group") == 5


def test_validate_manifest_reports_missing_file(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    broken = tmp_path / "manuscript" / "sheaf" / "manifest.yaml"
    broken.parent.mkdir(parents=True)
    broken.write_text(
        """
defaults:
  missing_track: error
sections:
  - id: broken
    order: 1
    title: Broken
    tracks:
      prose: manuscript/sections/does_not_exist.md
""",
        encoding="utf-8",
    )
    broken_manifest = load_manifest(broken, project_root=root)
    issues = validate_manifest(broken_manifest, root)
    assert any(i.code == "missing_track_file" for i in issues)


def test_validate_manifest_duplicate_and_unknown_tracks(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        """
sections:
  - id: dup
    order: 1
    title: One
    tracks:
      prose: manuscript/sections/preliminaries/prose.md
  - id: dup
    order: 2
    title: Two
    tracks:
      not_registered: manuscript/sections/preliminaries/prose.md
      prose: manuscript/sections/preliminaries/prose.md
    track_order: [prose, ghost]
""",
        encoding="utf-8",
    )
    manifest = load_manifest(manifest_path, project_root=root)
    issues = validate_manifest(manifest, root)
    assert any(i.code == "duplicate_section_id" for i in issues)
    assert any(i.code == "unknown_track" for i in issues)
    assert any(i.code == "track_order_unbound" for i in issues)


def test_validate_manifest_unknown_renderer(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    registry_path = tmp_path / "tracks.yaml"
    registry_path.write_text(
        """
tracks:
  prose:
    order: 1
    renderer: not_implemented
renderers:
  not_implemented:
    suffixes: [".md"]
""",
        encoding="utf-8",
    )
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        """
sections:
  - id: s
    order: 1
    title: S
    tracks:
      prose: manuscript/sections/preliminaries/prose.md
""",
        encoding="utf-8",
    )
    manifest = load_manifest(manifest_path, project_root=root)
    manifest = SheafManifest(
        defaults=manifest.defaults,
        sections=manifest.sections,
        registry_path=Path("tracks.yaml"),
    )
    issues = validate_manifest(
        manifest,
        root,
        registry=load_track_registry(registry_path),
    )
    assert any(i.code == "unknown_renderer" for i in issues)


def test_strict_validate_fails_on_gray(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(root / "manuscript" / "sheaf" / "manifest.yaml")
    registry = load_track_registry(root / "manuscript" / "sheaf" / "tracks.yaml")
    broken_section = SheafSection(
        id="broken_gray",
        title="Broken",
        short="b",
        order=99,
        tracks={"prose": "manuscript/sections/does_not_exist.md"},
        output_name="99_broken.md",
    )
    broken_manifest = SheafManifest(
        defaults=manifest.defaults,
        sections=manifest.sections + (broken_section,),
        registry_path=manifest.registry_path,
    )
    matrix = build_coverage_matrix(registry, broken_manifest, root)
    issues = validate_coverage_strict(matrix)
    assert any(i.code == "coverage_missing" for i in issues)
    validation = validate_manifest(broken_manifest, root, registry=registry, strict_coverage=True)
    assert any(i.code == "coverage_missing" for i in validation)


def test_group_rows_skip_compose(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    result = compose_all_sections(root, manuscript_dir=tmp_path / "manuscript")
    names = {p.name for p in result.paths}
    assert "_group_intro.md" not in names
    assert "02_intro_motivation.md" in names


@pytest.mark.timeout(900)
def test_validate_manuscript_strict_coverage() -> None:
    root = Path(__file__).resolve().parents[1]
    ensure_gate_artifacts(root)
    checks = validate_manuscript(root)
    if not checks["claim_ledger_valid"]:
        refresh_generated_gate_artifacts(root)
        checks = validate_manuscript(root)
    assert checks["sheaf_valid"]
    assert checks["coverage_matrix_valid"]
    assert checks["full_sheaf_appendix_tracks"]
    assert checks["imrad_groups_present"]
    assert checks["claim_ledger_valid"]
    assert checks["methods_sheaf_layers"]
    assert checks["manuscript_tokens_registered"]
    assert checks["resolved_manuscript_hydrated"]
