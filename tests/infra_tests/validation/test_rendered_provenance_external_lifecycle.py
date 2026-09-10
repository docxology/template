"""Rendered publication provenance: external managed-working-project snapshot and receipt binding."""

from __future__ import annotations
import subprocess
from pathlib import Path
import pytest
from infrastructure.core.pipeline.artifacts import (
    STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    snapshot_current_artifact_manifest,
)
from infrastructure.rendering.manuscript_composition import write_manuscript_composition
from infrastructure.validation.publication.rendered_provenance import (
    RECEIPT_RELATIVE_PATH,
    write_rendered_provenance_receipt,
)
from infrastructure.validation.rendered_snapshot import (
    RenderedSnapshotError,
    build_current_rendered_snapshot,
)
from infrastructure.validation.output.pipeline import execute_validation_pipeline
from tests._support.projects import make_project, write_doc

EXTERNAL_PROJECT = "working/demo"


def _external_stage4_project(tmp_path: Path) -> tuple[Path, Path]:
    """Create tracked template/private worktrees joined by a managed lifecycle link."""

    template_root = tmp_path / "template"
    private_project = tmp_path / "private" / "demo"
    make_project(
        private_project.parent,
        "demo",
        repo_layout=False,
        with_manuscript=True,
        with_output=True,
    )
    write_doc(template_root / ".gitignore", "# synthetic template policy\n")
    write_doc(template_root / "pyproject.toml", '[project]\nname = "synthetic-template"\n')
    write_doc(
        template_root / "infrastructure" / "core" / "pipeline" / "pipeline.yaml",
        "stages:\n  - name: Render\n    script: scripts/pipeline/stage_03_render.py\n",
    )
    write_doc(template_root / "infrastructure" / "rendering" / "runtime.py", "ENABLED = True\n")
    write_doc(template_root / "scripts" / "__init__.py", '"""Synthetic stage scripts."""\n')
    write_doc(template_root / "scripts" / "pipeline" / "stage_03_render.py", 'print("render")\n')

    write_doc(private_project / ".gitignore", "output/\n")
    render_config = (
        "render:\n  formats:\n    pdf: false\n    html: true\n    slides: false\n    docx: false\n    epub: false\n"
    )
    write_doc(private_project / "manuscript" / "config.yaml", render_config)
    write_doc(private_project / "manuscript" / "01_intro.md", "# Intro\n\nCurrent prose.\n")
    write_doc(private_project / "output" / "manuscript" / "config.yaml", render_config)
    write_doc(private_project / "output" / "manuscript" / "01_intro.md", "# Intro\n\nCurrent prose.\n")
    write_doc(
        private_project / "output" / "web" / "index.html",
        "<!doctype html><html><body>Current prose.</body></html>\n",
    )
    combined = private_project / "output" / "web" / "_combined_manuscript.md"
    write_doc(combined, "# Intro\n\nCurrent prose.\n")
    write_doc(private_project / "output" / "data" / "result.json", '{"status": "current"}\n')
    write_manuscript_composition(
        private_project,
        EXTERNAL_PROJECT,
        [private_project / "output" / "manuscript" / "01_intro.md"],
        combined,
    )

    managed = template_root / "projects" / "working" / "demo"
    managed.parent.mkdir(parents=True)
    managed.symlink_to(private_project, target_is_directory=True)
    for repository in (template_root, private_project):
        subprocess.run(["git", "init", "-q"], cwd=repository, check=True, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=repository, check=True, capture_output=True)
    snapshot_current_artifact_manifest(
        private_project / "output",
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )
    return template_root, private_project


def test_external_working_project_stage4_and_receipt_bind_both_worktrees(tmp_path: Path) -> None:
    """Stage 4 binds private source/output and shared template implementation."""

    template_root, private_project = _external_stage4_project(tmp_path)

    assert execute_validation_pipeline(EXTERNAL_PROJECT, repo_root=template_root) == 0
    snapshot = build_current_rendered_snapshot(template_root, EXTERNAL_PROJECT)
    receipt = write_rendered_provenance_receipt(template_root, EXTERNAL_PROJECT)

    assert (private_project / RECEIPT_RELATIVE_PATH).is_file()
    assert snapshot.stage.file_count > 0
    assert snapshot.source.file_count > 0
    assert snapshot.config.file_count > 0
    assert snapshot.output.file_count > 0
    assert receipt.stage == snapshot.stage
    assert receipt.source == snapshot.source
    assert receipt.config == snapshot.config
    assert receipt.output == snapshot.output


def test_external_snapshot_bare_name_recovers_managed_working_leaf(tmp_path: Path) -> None:
    """Bare selection retains the same managed lifecycle authority as qualified."""

    template_root, private_project = _external_stage4_project(tmp_path)
    combined = private_project / "output" / "web" / "_combined_manuscript.md"
    write_manuscript_composition(
        private_project,
        "demo",
        [private_project / "output" / "manuscript" / "01_intro.md"],
        combined,
    )
    snapshot_current_artifact_manifest(
        private_project / "output",
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )

    snapshot = build_current_rendered_snapshot(template_root, "demo")

    assert snapshot.project == "demo"
    assert snapshot.source.file_count > 0
    assert snapshot.config.file_count > 0


def test_external_snapshot_requires_real_private_git_boundary(tmp_path: Path) -> None:
    """An arbitrary external directory cannot become source-bound evidence."""

    template_root = tmp_path / "template"
    private_project = tmp_path / "outside" / "demo"
    write_doc(private_project / "src" / "analysis.py", "VALUE = 1\n")
    write_doc(private_project / "manuscript" / "01_intro.md", "# Intro\n")
    managed = template_root / "projects" / "working" / "demo"
    managed.parent.mkdir(parents=True)
    managed.symlink_to(private_project, target_is_directory=True)

    with pytest.raises(RenderedSnapshotError) as exc_info:
        build_current_rendered_snapshot(template_root, EXTERNAL_PROJECT)

    assert exc_info.value.code == "PROJECT_REPOSITORY_MISSING"


def test_external_snapshot_rejects_intermediate_lifecycle_symlink(tmp_path: Path) -> None:
    """Only the selected project leaf may cross into the private sidecar."""

    template_root, private_project = _external_stage4_project(tmp_path)
    leaf = template_root / "projects" / "working" / "demo"
    leaf.unlink()
    lifecycle = leaf.parent
    lifecycle.rmdir()
    lifecycle.symlink_to(private_project.parent, target_is_directory=True)

    with pytest.raises(RenderedSnapshotError) as exc_info:
        build_current_rendered_snapshot(template_root, EXTERNAL_PROJECT)

    assert exc_info.value.code == "PROJECT_LINK_INVALID"


def test_external_snapshot_rejects_symlinked_projects_root(tmp_path: Path) -> None:
    """A broad projects-directory redirect cannot authorize private source."""

    template_root, _private_project = _external_stage4_project(tmp_path)
    projects_root = template_root / "projects"
    redirected = tmp_path / "redirected-projects"
    projects_root.rename(redirected)
    projects_root.symlink_to(redirected, target_is_directory=True)

    with pytest.raises(RenderedSnapshotError) as exc_info:
        build_current_rendered_snapshot(template_root, EXTERNAL_PROJECT)

    assert exc_info.value.code == "PROJECT_LINK_INVALID"


def test_external_snapshot_rejects_public_template_leaf_symlink(tmp_path: Path) -> None:
    """Tracked public-template identity cannot be delegated to an external leaf."""

    template_root, private_project = _external_stage4_project(tmp_path)
    public_link = template_root / "projects" / "templates" / "demo"
    public_link.parent.mkdir(parents=True)
    public_link.symlink_to(private_project, target_is_directory=True)

    with pytest.raises(RenderedSnapshotError) as exc_info:
        build_current_rendered_snapshot(template_root, "templates/demo")

    assert exc_info.value.code == "PROJECT_LINK_INVALID"


def test_external_snapshot_rejects_source_symlink_outside_private_worktree(tmp_path: Path) -> None:
    """A managed project link does not authorize nested source escapes."""

    template_root = tmp_path / "template"
    private_project = tmp_path / "private" / "demo"
    outside = tmp_path / "outside"
    write_doc(private_project / "src" / "analysis.py", "VALUE = 1\n")
    write_doc(private_project / "manuscript" / "01_intro.md", "# Intro\n")
    write_doc(outside / "secret.py", "SECRET = True\n")
    (private_project / "src" / "escape").symlink_to(outside, target_is_directory=True)
    subprocess.run(["git", "init", "-q"], cwd=private_project, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=private_project, check=True, capture_output=True)
    managed = template_root / "projects" / "working" / "demo"
    managed.parent.mkdir(parents=True)
    managed.symlink_to(private_project, target_is_directory=True)

    with pytest.raises(RenderedSnapshotError) as exc_info:
        build_current_rendered_snapshot(template_root, EXTERNAL_PROJECT)

    assert exc_info.value.code == "SOURCE_SYMLINK_ESCAPE"
