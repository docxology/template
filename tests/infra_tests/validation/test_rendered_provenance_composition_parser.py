"""Rendered publication provenance: combined-manuscript composition parser and algorithm binding."""

from __future__ import annotations
import json
from pathlib import Path
import pytest
from infrastructure.core.pipeline.artifacts import snapshot_current_artifact_manifest
from infrastructure.rendering.manuscript_composition import (
    COMPOSITION_RELATIVE_PATH,
    read_manuscript_composition,
    write_manuscript_composition,
)
from infrastructure.rendering.manuscript_discovery import discover_manuscript_files
from infrastructure.validation.publication.rendered_provenance import (
    RECEIPT_RELATIVE_PATH,
    RenderedProvenanceError,
    validate_rendered_provenance,
    write_rendered_provenance_receipt,
)
from infrastructure.validation.rendered_snapshot import (
    RenderedSnapshotError,
    build_current_rendered_snapshot,
    declared_generated_manuscript_inputs,
    read_committed_validation_report,
)
from tests._support.projects import write_doc
from tests.infra_tests.validation._rendered_provenance_helpers import (
    PROJECT,
    _green_project,
    _write_green_validation_report,
)


def test_nonhydrated_sources_are_bound_to_actual_combined_manuscript(tmp_path: Path) -> None:
    project = _green_project(tmp_path, hydrated=False)

    receipt = write_rendered_provenance_receipt(tmp_path, PROJECT)

    assert {row.rendered_path for row in receipt.consumed_manuscript} == {"output/web/_combined_manuscript.md"}
    assert all(row.rendered_sha256 == receipt.combined_manuscript.sha256 for row in receipt.consumed_manuscript)
    composition = read_manuscript_composition(project / COMPOSITION_RELATIVE_PATH)
    assert composition.input_root_kind == "source"


def test_shared_combined_algorithm_is_accepted_by_current_snapshot(tmp_path: Path) -> None:
    """Strict provenance rebuilds a shared composition with its recorded algorithm."""

    project = _green_project(
        tmp_path,
        hydrated=False,
        composition_algorithm="shared-combined-markdown-v1",
    )

    snapshot = build_current_rendered_snapshot(tmp_path, PROJECT)
    receipt = write_rendered_provenance_receipt(tmp_path, PROJECT)

    assert snapshot.combined_manuscript.path == "output/web/_combined_manuscript.md"
    assert receipt.combined_manuscript.sha256 == snapshot.combined_manuscript.sha256
    composition = read_manuscript_composition(project / COMPOSITION_RELATIVE_PATH)
    assert composition.algorithm == "shared-combined-markdown-v1"


def test_composition_drift_blocks_refresh_and_preserves_receipt(tmp_path: Path) -> None:
    project = _green_project(tmp_path, hydrated=False)
    write_rendered_provenance_receipt(tmp_path, PROJECT)
    receipt_path = project / RECEIPT_RELATIVE_PATH
    old_receipt = receipt_path.read_bytes()

    write_doc(project / "manuscript" / "01_methods.md", "# Methods\n\nChanged without rerender.\n")

    validation = validate_rendered_provenance(tmp_path, PROJECT)
    assert [issue.code for issue in validation.issues] == ["COMPOSITION_DRIFT"]
    with pytest.raises(RenderedProvenanceError) as error:
        write_rendered_provenance_receipt(tmp_path, PROJECT)
    assert error.value.code == "COMPOSITION_DRIFT"
    assert receipt_path.read_bytes() == old_receipt


@pytest.mark.parametrize("bad_size", [True, "12", -1])
def test_composition_parser_rejects_noncanonical_combined_sizes(
    tmp_path: Path,
    bad_size: object,
) -> None:
    project = _green_project(tmp_path)
    path = project / COMPOSITION_RELATIVE_PATH
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["combined_size_bytes"] = bad_size
    write_doc(path, json.dumps(payload))

    with pytest.raises(ValueError, match="combined_size_bytes"):
        read_manuscript_composition(path)


@pytest.mark.parametrize(
    "field",
    [
        "ordered_inputs.0.sha256",
        "ordered_inputs_sha256",
        "combined_sha256",
        "binding_sha256",
    ],
)
def test_composition_parser_rejects_every_malformed_sha_field(
    tmp_path: Path,
    field: str,
) -> None:
    project = _green_project(tmp_path)
    path = project / COMPOSITION_RELATIVE_PATH
    payload = json.loads(path.read_text(encoding="utf-8"))
    if field == "ordered_inputs.0.sha256":
        payload["ordered_inputs"][0]["sha256"] = "A" * 64
    else:
        payload[field] = "A" * 64
    write_doc(path, json.dumps(payload))

    with pytest.raises(ValueError, match="lowercase hexadecimal"):
        read_manuscript_composition(path)


def test_composition_parser_rejects_mixed_or_noncanonical_roots(tmp_path: Path) -> None:
    project = _green_project(tmp_path)
    path = project / COMPOSITION_RELATIVE_PATH
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["ordered_inputs"][1]["path"] = "manuscript/01_methods.md"
    write_doc(path, json.dumps(payload))

    with pytest.raises(ValueError, match="one canonical manuscript root"):
        read_manuscript_composition(path)


_GENERATED_CONFIG = """# Generated manuscript ordering
book:
  title: Compiled study
  version: 0.2.0
front_matter:
  files: [z_overview.md, a_scope.md]
units:
  - directory: chapters
    chapters: [methods.md]
appendices:
  include_reference: true
  reference: [glossary.md]
"""


def _generated_project(root: Path, *, authored: bool = False) -> Path:
    project = _green_project(root)
    for directory in (project / "manuscript", project / "output/manuscript"):
        for path in directory.glob("*.md"):
            path.unlink()
    write_doc(project / "docs/manuscript/templates/section.md", "# {{SECTION}}\n")
    write_doc(project / "docs/manuscript/config.yaml", "book:\n  title: Compiler template\n")
    if authored:
        write_doc(project / "manuscript/z_overview.md", "# Uncompiled overview template\n")
        write_doc(project / "manuscript/obsolete.md", "# Not a compiler input section\n")
    rendered = project / "output/manuscript"
    write_doc(rendered / "config.yaml", _GENERATED_CONFIG)
    for name in (
        "z_overview.md",
        "a_scope.md",
        "chapters/unit_intro.md",
        "chapters/methods.md",
        "appendices/glossary.md",
    ):
        write_doc(rendered / name, f"# Compiled {name}\n\nCompiler-owned content.\n")
    paths = discover_manuscript_files(rendered)
    combined = project / "output/web/_combined_manuscript.md"
    write_doc(combined, "\n\n".join(path.read_text(encoding="utf-8") for path in paths))
    write_manuscript_composition(project, PROJECT, paths, combined)
    snapshot_current_artifact_manifest(project / "output")
    _write_green_validation_report(root, project)
    return project


def test_generated_marker_after_block_scalar_selects_declared_input(tmp_path: Path) -> None:
    manuscript = tmp_path / "output/manuscript"
    chapter = manuscript / "intro.md"
    write_doc(chapter, "# Compiler-owned introduction\n")
    write_doc(
        manuscript / "config.yaml",
        "note: |\n  Compiler documentation.\n# Generated manuscript ordering\nfront_matter:\n  files: [intro.md]\n",
    )

    assert declared_generated_manuscript_inputs(tmp_path) == (chapter,)


@pytest.mark.parametrize("authored", (False, True))
def test_declared_generated_roster_binds_actual_order_without_authorship(tmp_path: Path, authored: bool) -> None:
    project = _generated_project(tmp_path, authored=authored)
    snapshot = build_current_rendered_snapshot(tmp_path, PROJECT)
    receipt = write_rendered_provenance_receipt(tmp_path, PROJECT)

    assert [row.rendered_path for row in snapshot.consumed_manuscript] == [
        "output/manuscript/z_overview.md",
        "output/manuscript/a_scope.md",
        "output/manuscript/chapters/unit_intro.md",
        "output/manuscript/chapters/methods.md",
        "output/manuscript/appendices/glossary.md",
    ]
    assert all(row.source_path is None and row.source_sha256 is None for row in receipt.consumed_manuscript)
    assert receipt.consumed_manuscript == snapshot.consumed_manuscript
    assert validate_rendered_provenance(tmp_path, PROJECT).valid
    payload = json.loads((project / RECEIPT_RELATIVE_PATH).read_text(encoding="utf-8"))
    assert all(row["source_path"] is None and row["source_sha256"] is None for row in payload["consumed_manuscript"])


@pytest.mark.parametrize(
    ("config", "code"),
    [
        (_GENERATED_CONFIG.replace("# Generated manuscript ordering\n", ""), "MANUSCRIPT_SOURCE_MISSING"),
        (
            _GENERATED_CONFIG.replace("Generated manuscript ordering", "Project-resolved config"),
            "MANUSCRIPT_SOURCE_MISSING",
        ),
        ("# Generated manuscript ordering\nbook: [\n", "GENERATED_MANUSCRIPT_INVALID"),
        ("# Generated manuscript ordering\n{}\n", "GENERATED_MANUSCRIPT_INVALID"),
        ("# Generated manuscript ordering\n- scalar\n", "GENERATED_MANUSCRIPT_INVALID"),
        ('note: "# Generated manuscript ordering"\n', "GENERATED_MANUSCRIPT_INVALID"),
        (_GENERATED_CONFIG.replace("Compiled study", "{{TITLE}}"), "GENERATED_MANUSCRIPT_INVALID"),
        (
            _GENERATED_CONFIG.replace("units:\n  - directory: chapters\n    chapters: [methods.md]", "units: wrong"),
            "GENERATED_MANUSCRIPT_INVALID",
        ),
        (_GENERATED_CONFIG.replace("methods.md", "missing.md"), "GENERATED_MANUSCRIPT_INVALID"),
        ("# Generated manuscript ordering\nfront_matter:\n  files: []\n", "GENERATED_MANUSCRIPT_INVALID"),
    ],
)
def test_generated_manuscript_requires_valid_explicit_declaration(tmp_path: Path, config: str, code: str) -> None:
    project = _generated_project(tmp_path)
    write_doc(project / "output/manuscript/config.yaml", config)
    snapshot_current_artifact_manifest(project / "output")

    with pytest.raises(RenderedSnapshotError) as error:
        build_current_rendered_snapshot(tmp_path, PROJECT)

    assert error.value.code == code


@pytest.mark.parametrize("change", ("input", "order", "combined", "extra", "missing"))
def test_generated_roster_cannot_rebind_stale_composition(tmp_path: Path, change: str) -> None:
    project = _generated_project(tmp_path)
    rendered = project / "output/manuscript"
    if change == "input":
        write_doc(rendered / "chapters/methods.md", "# Changed compiler output\n")
    elif change == "order":
        write_doc(
            rendered / "config.yaml",
            _GENERATED_CONFIG.replace("[z_overview.md, a_scope.md]", "[a_scope.md, z_overview.md]"),
        )
    elif change == "combined":
        write_doc(project / "output/web/_combined_manuscript.md", "# Changed combined bytes\n")
    elif change == "extra":
        write_doc(rendered / "extra.md", "# Unknown output selected after rendering\n")
        write_doc(
            rendered / "config.yaml",
            _GENERATED_CONFIG.replace("[z_overview.md, a_scope.md]", "[z_overview.md, a_scope.md, extra.md]"),
        )
    else:
        (rendered / "chapters/unit_intro.md").unlink()
    # Renewing the output inventory alone must not establish render custody.
    snapshot_current_artifact_manifest(project / "output")

    with pytest.raises(RenderedSnapshotError) as error:
        build_current_rendered_snapshot(tmp_path, PROJECT)

    assert error.value.code == "COMPOSITION_DRIFT"


@pytest.mark.parametrize("field", ("title", "version"))
def test_generated_config_metadata_drift_changes_config_commitment(tmp_path: Path, field: str) -> None:
    project = _generated_project(tmp_path)
    before = build_current_rendered_snapshot(tmp_path, PROJECT)
    old, new = ("Compiled study", "Changed study") if field == "title" else ("0.2.0", "0.3.0")
    write_doc(project / "output/manuscript/config.yaml", _GENERATED_CONFIG.replace(old, new))
    snapshot_current_artifact_manifest(project / "output")
    current = build_current_rendered_snapshot(tmp_path, PROJECT)

    assert current.config != before.config
    assert current.source == before.source
    assert current.consumed_manuscript == before.consumed_manuscript
    with pytest.raises(RenderedSnapshotError) as error:
        read_committed_validation_report(tmp_path, PROJECT, current)
    assert error.value.code == "VALIDATION_INPUTS_DRIFT"
    assert "fingerprints.config" in str(error.value)


def test_generated_declaration_does_not_select_nested_only_output(tmp_path: Path) -> None:
    project = _generated_project(tmp_path)
    rendered = project / "output/manuscript"
    for path in rendered.glob("*.md"):
        path.unlink()
    write_doc(
        rendered / "config.yaml",
        """# Generated manuscript ordering
units:
  - directory: chapters
    chapters: [methods.md]
""",
    )

    with pytest.raises(RenderedSnapshotError) as error:
        declared_generated_manuscript_inputs(project)
    assert error.value.code == "GENERATED_MANUSCRIPT_INVALID"


@pytest.mark.parametrize("component", ("input", "config"))
def test_generated_declaration_cannot_admit_outside_project_bytes(tmp_path: Path, component: str) -> None:
    project = _generated_project(tmp_path)
    path = project / "output/manuscript" / ("a_scope.md" if component == "input" else "config.yaml")
    outside = tmp_path / ("outside.md" if component == "input" else "outside.yaml")
    write_doc(outside, path.read_text(encoding="utf-8"))
    path.unlink()
    path.symlink_to(outside)

    with pytest.raises(RenderedSnapshotError) as error:
        declared_generated_manuscript_inputs(project)
    assert error.value.code == "GENERATED_MANUSCRIPT_INVALID"
