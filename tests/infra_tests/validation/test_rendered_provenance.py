"""Behavioral tests for fail-closed rendered publication provenance."""

from __future__ import annotations

import json
import subprocess
import threading
from pathlib import Path

import pytest

from infrastructure.core.files.secure_write import atomic_write_text_confined
from infrastructure.core.pipeline.artifacts import (
    STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    snapshot_current_artifact_manifest,
)
from infrastructure.rendering.manuscript_composition import (
    COMPOSITION_RELATIVE_PATH,
    read_manuscript_composition,
    write_manuscript_composition,
)
from infrastructure.validation.publication.audit import (
    AuditContext,
    build_publication_audit,
    check_placeholder_tokens,
)
from infrastructure.validation.publication.rendered_provenance import (
    RECEIPT_RELATIVE_PATH,
    RenderedProvenanceError,
    validate_rendered_provenance,
    write_rendered_provenance_receipt,
)
from infrastructure.validation.rendered_snapshot import (
    RenderedSnapshotError,
    _output_records,
    build_current_rendered_snapshot,
)
from infrastructure.validation.output.validator import collect_detailed_validation_results
from infrastructure.validation.output.pipeline import execute_validation_pipeline
from tests._support.projects import make_project, write_doc

PROJECT = "templates/template_test"
EXTERNAL_PROJECT = "working/demo"
REPO_ROOT = Path(__file__).resolve().parents[3]


def _write_green_validation_report(root: Path, project: Path) -> dict[str, object]:
    snapshot = build_current_rendered_snapshot(root, PROJECT)
    checks = {"Rendered structure": True, "Artifact manifest": True}
    detailed_validation = collect_detailed_validation_results(project / "output", require_pdf=False)
    payload: dict[str, object] = {
        "timestamp": "2026-01-01T00:00:00Z",
        "checks": checks,
        "figure_issues": [],
        "output_statistics": {
            "inventory_mode": "stable-shippable-output-v1",
            "detailed_validation": detailed_validation,
        },
        "summary": {
            "total_checks": len(checks),
            "passed": len(checks),
            "failed": 0,
            "figure_issues_count": 0,
            "all_passed": True,
        },
        "recommendations": [],
        "validated_inputs": snapshot.validated_inputs_dict(),
    }
    write_doc(
        project / "output" / "reports" / "validation_report.json",
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
    )
    return payload


def _green_project(
    root: Path,
    *,
    hydrated: bool = True,
    composition_algorithm: str = "web-renderer-combine-v1",
) -> Path:
    project = make_project(
        root,
        "template_test",
        program="templates",
        with_manuscript=True,
        with_output=True,
    )
    write_doc(root / ".gitignore", "# synthetic release ignore policy\n")
    write_doc(root / "pyproject.toml", '[project]\nname = "synthetic-template"\n')
    write_doc(
        root / "infrastructure" / "core" / "pipeline" / "pipeline.yaml",
        "stages:\n  - name: Render\n    script: scripts/pipeline/stage_03_render.py\n",
    )
    write_doc(
        root / "infrastructure" / "research" / "runtime_prompt.md",
        "Render every canonical source.\n",
    )
    write_doc(
        root / "infrastructure" / "rendering" / "layout.template",
        "<main>{{ manuscript }}</main>\n",
    )
    write_doc(
        root / "infrastructure" / "validation" / "output" / "runtime_gate.py",
        "REQUIRE_CURRENT_OUTPUT = True\n",
    )
    write_doc(root / "scripts" / "__init__.py", '"""Runtime stage bootstrap."""\n')
    write_doc(root / "scripts" / "pipeline" / "stage_03_render.py", 'print("render")\n')
    write_doc(
        project / "manuscript" / "00_abstract.md",
        "# Abstract\n\nAuthoring token {{RESULT_COUNT}} is hydratable.\n",
    )
    write_doc(project / "manuscript" / "01_methods.md", "# Methods\n\nMethod source.\n")

    if hydrated:
        write_doc(
            project / "output" / "manuscript" / "00_abstract.md",
            "# Abstract\n\nThere were 7 results.\n",
        )
        write_doc(
            project / "output" / "manuscript" / "01_methods.md",
            "# Methods\n\nMethod source.\n",
        )
        rendered_inputs = sorted((project / "output" / "manuscript").glob("*.md"))
    else:
        rendered_inputs = sorted(path for path in (project / "manuscript").glob("*.md") if path.name != "config.yaml")

    combined = project / "output" / "web" / "_combined_manuscript.md"
    combined_text = "\n\n".join(path.read_text(encoding="utf-8").rstrip() for path in rendered_inputs) + "\n"
    write_doc(combined, combined_text)
    write_manuscript_composition(
        project,
        PROJECT,
        rendered_inputs,
        combined,
        algorithm=composition_algorithm,
    )
    write_doc(project / "output" / "data" / "result.json", '{"count": 7}\n')
    snapshot_current_artifact_manifest(project / "output")
    _write_green_validation_report(root, project)
    return project


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


def test_receipt_is_deterministic_and_current_for_green_real_files(tmp_path: Path) -> None:
    project = _green_project(tmp_path)

    first = write_rendered_provenance_receipt(tmp_path, PROJECT)
    first_bytes = (project / RECEIPT_RELATIVE_PATH).read_bytes()
    second = write_rendered_provenance_receipt(tmp_path, PROJECT)

    assert first == second
    assert (project / RECEIPT_RELATIVE_PATH).read_bytes() == first_bytes
    assert first.evidence_mode == "validated-co-snapshot-fingerprint-bridge"
    assert first.stage.file_count == 6
    assert first.source.file_count >= 3
    assert first.config.file_count >= 3
    assert first.output.file_count >= 4
    assert validate_rendered_provenance(tmp_path, PROJECT).valid


def test_rendered_snapshot_accepts_explicit_stable_local_manifest(tmp_path: Path) -> None:
    """A blanket-ignored lifecycle output compares within its authorized mode."""
    project = tmp_path / "private" / "demo"
    result = project / "output" / "data" / "result.json"
    result.parent.mkdir(parents=True)
    result.write_text('{"count": 7}\n', encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(project)], check=True)
    (project / ".gitignore").write_text("output/\n", encoding="utf-8")
    snapshot_current_artifact_manifest(
        project / "output",
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )

    records, manifest = _output_records(
        project,
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )

    assert [record.key for record in records] == ["output/data/result.json"]
    assert manifest.path == "output/reports/artifact_manifest.json"


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


def test_rendered_snapshot_rejects_manifest_from_another_inventory_mode(tmp_path: Path) -> None:
    project = _green_project(tmp_path)
    manifest_path = project / "output" / "reports" / "artifact_manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["inventory_mode"] = STABLE_LOCAL_OUTPUT_INVENTORY_MODE
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(RenderedSnapshotError) as exc_info:
        build_current_rendered_snapshot(tmp_path, PROJECT)

    assert exc_info.value.code == "ARTIFACT_MANIFEST_INVALID"
    assert "artifact inventory mode mismatch" in str(exc_info.value)


@pytest.mark.parametrize(
    ("relative_path", "replacement", "fingerprint"),
    [
        (
            "infrastructure/research/runtime_prompt.md",
            "Changed runtime research prompt.\n",
            "stage",
        ),
        (
            "infrastructure/rendering/layout.template",
            "<article>{{ manuscript }}</article>\n",
            "stage",
        ),
        (
            "infrastructure/validation/output/runtime_gate.py",
            "REQUIRE_CURRENT_OUTPUT = False\n",
            "stage",
        ),
        (
            "scripts/__init__.py",
            '"""Changed stage bootstrap."""\n',
            "stage",
        ),
        (
            "projects/templates/template_test/src/stub.py",
            '"""Changed project source."""\n',
            "source",
        ),
        (
            "projects/templates/template_test/manuscript/config.yaml",
            "paper:\n  title: Changed title\n",
            "config",
        ),
        (
            ".gitignore",
            "# changed release ignore semantics\n*.never-created\n",
            "config",
        ),
    ],
)
def test_complete_stage_source_and_config_closures_detect_drift(
    tmp_path: Path,
    relative_path: str,
    replacement: str,
    fingerprint: str,
) -> None:
    project = _green_project(tmp_path)
    write_rendered_provenance_receipt(tmp_path, PROJECT)
    before = build_current_rendered_snapshot(tmp_path, PROJECT)

    write_doc(tmp_path / relative_path, replacement)
    after = build_current_rendered_snapshot(tmp_path, PROJECT)

    assert getattr(before, fingerprint) != getattr(after, fingerprint)
    _write_green_validation_report(tmp_path, project)
    issue_codes = {issue.code for issue in validate_rendered_provenance(tmp_path, PROJECT).issues}
    assert f"{fingerprint.upper()}_FINGERPRINT_DRIFT" in issue_codes
    assert "VALIDATION_REPORT_DRIFT" in issue_codes


def test_staged_new_non_python_runtime_asset_participates_in_stage_closure(tmp_path: Path) -> None:
    project = _green_project(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    _write_green_validation_report(tmp_path, project)
    write_rendered_provenance_receipt(tmp_path, PROJECT)
    before = build_current_rendered_snapshot(tmp_path, PROJECT)

    runtime_asset = tmp_path / "infrastructure" / "rendering" / "new_runtime_asset.template"
    write_doc(runtime_asset, "<aside>new behavior</aside>\n")
    subprocess.run(["git", "add", str(runtime_asset)], cwd=tmp_path, check=True)
    after = build_current_rendered_snapshot(tmp_path, PROJECT)

    assert after.stage.file_count == before.stage.file_count + 1
    assert after.stage != before.stage
    with pytest.raises(RenderedProvenanceError, match="exact current rendered snapshot") as error:
        write_rendered_provenance_receipt(tmp_path, PROJECT)
    assert error.value.code == "VALIDATION_INPUTS_DRIFT"


def test_clean_index_requires_every_manifest_and_evidence_path(tmp_path: Path) -> None:
    project = _green_project(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    _write_green_validation_report(tmp_path, project)
    write_rendered_provenance_receipt(tmp_path, PROJECT)

    untracked = validate_rendered_provenance(tmp_path, PROJECT)
    assert [issue.code for issue in untracked.issues] == ["CLEAN_INDEX_INCOMPLETE"]
    assert "rendered_provenance.json" in untracked.issues[0].message

    subprocess.run(
        ["git", "add", str(project / RECEIPT_RELATIVE_PATH)],
        cwd=tmp_path,
        check=True,
    )
    assert validate_rendered_provenance(tmp_path, PROJECT).valid


def test_advanced_publication_surfaces_are_trackable_but_intermediates_stay_ignored() -> None:
    project = "projects/templates/template_advanced_literature_review/output"
    stable = (
        f"{project}/manuscript/00_abstract.md",
        f"{project}/figures/figure_registry.json",
        f"{project}/web/_combined_manuscript.md",
        f"{project}/pdf/template_advanced_literature_review_combined.pdf",
        f"{project}/slides/00_abstract_slides.pdf",
        f"{project}/reports/artifact_manifest.json",
        f"{project}/reports/manuscript_composition.json",
        f"{project}/reports/rendered_provenance.json",
        f"{project}/reports/validation_report.json",
    )
    for relative in stable:
        result = subprocess.run(
            ["git", "check-ignore", "--quiet", "--no-index", relative],
            cwd=REPO_ROOT,
            check=False,
        )
        assert result.returncode == 1, relative

    transient = subprocess.run(
        [
            "git",
            "check-ignore",
            "--quiet",
            "--no-index",
            f"{project}/pdf/_combined_manuscript.tex",
        ],
        cwd=REPO_ROOT,
        check=False,
    )
    assert transient.returncode == 0


def test_historical_green_report_cannot_reattest_changed_source(tmp_path: Path) -> None:
    project = _green_project(tmp_path)
    write_rendered_provenance_receipt(tmp_path, PROJECT)
    receipt_path = project / RECEIPT_RELATIVE_PATH
    old_receipt = receipt_path.read_bytes()

    write_doc(project / "src" / "stub.py", '"""Changed after validation."""\n')

    with pytest.raises(RenderedProvenanceError) as error:
        write_rendered_provenance_receipt(tmp_path, PROJECT)
    assert error.value.code == "VALIDATION_INPUTS_DRIFT"
    assert receipt_path.read_bytes() == old_receipt


def test_internally_contradictory_validation_report_fails_closed(tmp_path: Path) -> None:
    project = _green_project(tmp_path)
    write_rendered_provenance_receipt(tmp_path, PROJECT)
    receipt_path = project / RECEIPT_RELATIVE_PATH
    old_receipt = receipt_path.read_bytes()
    report_path = project / "output" / "reports" / "validation_report.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    payload["checks"]["Rendered structure"] = False
    write_doc(report_path, json.dumps(payload, indent=2, sort_keys=True) + "\n")

    validation = validate_rendered_provenance(tmp_path, PROJECT)

    assert [issue.code for issue in validation.issues] == ["VALIDATION_REPORT_INCONSISTENT"]
    with pytest.raises(RenderedProvenanceError) as error:
        write_rendered_provenance_receipt(tmp_path, PROJECT)
    assert error.value.code == "VALIDATION_REPORT_INCONSISTENT"
    assert receipt_path.read_bytes() == old_receipt


def test_extra_stable_output_is_rejected_until_manifest_attests_it(tmp_path: Path) -> None:
    project = _green_project(tmp_path)
    write_rendered_provenance_receipt(tmp_path, PROJECT)
    receipt_path = project / RECEIPT_RELATIVE_PATH
    old_receipt = receipt_path.read_bytes()

    write_doc(project / "output" / "web" / "unattested-runtime.js", "export const value = 1;\n")
    validation = validate_rendered_provenance(tmp_path, PROJECT)

    assert [issue.code for issue in validation.issues] == ["ARTIFACT_MANIFEST_INCOMPLETE"]
    assert "output/web/unattested-runtime.js" in validation.issues[0].message
    with pytest.raises(RenderedProvenanceError) as error:
        write_rendered_provenance_receipt(tmp_path, PROJECT)
    assert error.value.code == "ARTIFACT_MANIFEST_INCOMPLETE"
    assert receipt_path.read_bytes() == old_receipt


def test_runtime_history_is_nonstable_but_unattested_report_still_fails(tmp_path: Path) -> None:
    project = _green_project(tmp_path)
    write_rendered_provenance_receipt(tmp_path, PROJECT)

    write_doc(
        project / "output" / "reports" / ".history" / "telemetry-123.json",
        '{"runtime": true}\n',
    )
    assert validate_rendered_provenance(tmp_path, PROJECT).valid

    write_doc(project / "output" / "reports" / "unattested_quality_report.json", '{"quality": "green"}\n')
    validation = validate_rendered_provenance(tmp_path, PROJECT)

    assert [issue.code for issue in validation.issues] == ["ARTIFACT_MANIFEST_INCOMPLETE"]
    assert "output/reports/unattested_quality_report.json" in validation.issues[0].message


def test_report_and_receipt_are_fixed_points_over_ignored_runtime_state(tmp_path: Path) -> None:
    """Regenerating validation evidence must ignore machine-local residue."""
    project = _green_project(tmp_path)
    write_rendered_provenance_receipt(tmp_path, PROJECT)
    report_path = project / "output" / "reports" / "validation_report.json"
    receipt_path = project / RECEIPT_RELATIVE_PATH
    baseline_report = report_path.read_bytes()
    baseline_receipt = receipt_path.read_bytes()

    ignored_files = {
        "pdf/build.aux": b"latex auxiliary",
        "reports/.history/telemetry-123.json": b"{}\n",
        "reports/snapshots/stage.json": b"{}\n",
        "logs/pipeline.log": b"runtime log\n",
        "figures/.partial.png": b"atomic leftover",
    }
    for relative, payload in ignored_files.items():
        path = project / "output" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    for relative in ("slides", "simulations", "llm"):
        (project / "output" / relative).mkdir(parents=True, exist_ok=True)

    _write_green_validation_report(tmp_path, project)
    write_rendered_provenance_receipt(tmp_path, PROJECT)

    assert report_path.read_bytes() == baseline_report
    assert receipt_path.read_bytes() == baseline_receipt
    assert validate_rendered_provenance(tmp_path, PROJECT).valid


def test_manifest_and_validation_report_digests_are_bound_separately(tmp_path: Path) -> None:
    project = _green_project(tmp_path)
    write_rendered_provenance_receipt(tmp_path, PROJECT)
    manifest_path = project / "output" / "reports" / "artifact_manifest.json"
    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    write_doc(manifest_path, json.dumps(manifest_payload, separators=(",", ":")) + "\n")
    _write_green_validation_report(tmp_path, project)

    manifest_codes = {issue.code for issue in validate_rendered_provenance(tmp_path, PROJECT).issues}
    assert "ARTIFACT_MANIFEST_DRIFT" in manifest_codes
    assert "VALIDATION_REPORT_DRIFT" in manifest_codes

    write_rendered_provenance_receipt(tmp_path, PROJECT)
    report_path = project / "output" / "reports" / "validation_report.json"
    report_payload = json.loads(report_path.read_text(encoding="utf-8"))
    report_payload["recommendations"].append({"action": "Review deterministic evidence."})
    write_doc(report_path, json.dumps(report_payload, indent=2, sort_keys=True) + "\n")

    assert [issue.code for issue in validate_rendered_provenance(tmp_path, PROJECT).issues] == [
        "VALIDATION_REPORT_DRIFT"
    ]


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


def test_rendered_placeholder_scan_covers_grammar_without_duplicate_propagation(
    tmp_path: Path,
) -> None:
    project = _green_project(tmp_path)
    propagated = """# Abstract

Unresolved {{ RESULT_COUNT }}, {{analysis.mean:.4f}}, {{verify.*}}, {{#if result}}, ${DATASET:-missing}, and ${REQUIRED:?set it}.

Cross-reference {{#fig:overview}}, Mermaid KW{{For each keyword}}, and LaTeX ${(\beta)} remain legitimate.

Literal `{{INLINE_EXAMPLE}}`.
Literal double-backtick ``{{DOUBLE_INLINE_EXAMPLE}}``.

Paragraph continuation
    {{ PARAGRAPH_CONTINUATION_VISIBLE }}

- list item

    {{ LIST_PARAGRAPH_VISIBLE }}

After the list.

- list code item

        {{ NESTED_LIST_CODE_MASKED }}

```text
${FENCED_EXAMPLE:-default}
```

````markdown
```text
{{NESTED_BACKTICK_EXAMPLE}}
```
````

~~~~text
~~~text
{{NESTED_TILDE_EXAMPLE}}
~~~
~~~~

Mismatched inline bad`` {{ MISMATCHED_INLINE_VISIBLE }} ```

```lang`not-a-commonmark-fence
{{ INVALID_FENCE_VISIBLE }}
"""
    write_doc(project / "output" / "web" / "_combined_manuscript.md", propagated)
    write_doc(
        project / "output" / "manuscript" / "00_abstract.md",
        propagated + "\nHydrated-only unresolved {{ HYDRATED_ONLY }}.\n",
    )
    ctx = AuditContext(
        repo_root=tmp_path,
        project=PROJECT,
        project_root=project,
        rendered=True,
        include_drift=False,
    )

    findings = list(check_placeholder_tokens(ctx))

    tokens = [finding.message.rsplit(": ", 1)[1] for finding in findings]
    assert tokens == [
        "{{ RESULT_COUNT }}",
        "{{analysis.mean:.4f}}",
        "{{verify.*}}",
        "{{#if result}}",
        "${DATASET:-missing}",
        "${REQUIRED:?set it}",
        "{{ PARAGRAPH_CONTINUATION_VISIBLE }}",
        "{{ LIST_PARAGRAPH_VISIBLE }}",
        "{{ MISMATCHED_INLINE_VISIBLE }}",
        "{{ INVALID_FENCE_VISIBLE }}",
        "{{ HYDRATED_ONLY }}",
    ]
    assert len(tokens) == len(set(tokens))
    assert findings[0].path.endswith("output/web/_combined_manuscript.md")
    assert findings[-1].path.endswith("output/manuscript/00_abstract.md")

    parity_source = """Paragraph
    {{PARAGRAPH_VISIBLE}}

- item

    {{LIST_VISIBLE}}

- code item

        {{LIST_CODE_MASKED}}
"""
    pandoc = subprocess.run(
        ["pandoc", "--from=commonmark", "--to=html"],
        input=parity_source,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "{{PARAGRAPH_VISIBLE}}" in pandoc
    assert "{{LIST_VISIBLE}}" in pandoc
    assert "<code>  {{LIST_CODE_MASKED}}</code>" in pandoc


def test_source_publication_mode_permits_declared_hydratable_tokens(tmp_path: Path) -> None:
    _green_project(tmp_path)

    report = build_publication_audit(
        tmp_path,
        [PROJECT],
        rendered=False,
        include_drift=False,
    )

    assert all(finding.diagnostic_code != "PUBLICATION.PLACEHOLDER_TOKEN" for finding in report.findings)


def test_receipt_fails_closed_when_missing_or_malformed(tmp_path: Path) -> None:
    project = _green_project(tmp_path)

    missing = validate_rendered_provenance(tmp_path, PROJECT)
    assert [issue.code for issue in missing.issues] == ["MISSING"]

    write_doc(project / RECEIPT_RELATIVE_PATH, '{"schema_version": "wrong"}\n')
    malformed = validate_rendered_provenance(tmp_path, PROJECT)
    assert [issue.code for issue in malformed.issues] == ["MALFORMED"]


def test_confined_atomic_writer_rejects_symlink_components_without_overwrite(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "validation_report.json"
    write_doc(sentinel, "original\n")
    project.mkdir()
    (project / "output").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="symlink component"):
        atomic_write_text_confined(
            project,
            project / "output" / "validation_report.json",
            "replacement\n",
        )

    assert sentinel.read_text(encoding="utf-8") == "original\n"


def test_confined_atomic_writer_resists_parent_symlink_swap_race(tmp_path: Path) -> None:
    project = tmp_path / "project"
    reports = project / "output" / "reports"
    reports.mkdir(parents=True)
    displaced = project / "output" / "reports-displaced"
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "validation_report.json"
    write_doc(sentinel, "outside sentinel\n")
    encode_started = threading.Event()
    parent_swapped = threading.Event()

    class CoordinatedText(str):
        def encode(self, encoding: str = "utf-8", errors: str = "strict") -> bytes:
            encode_started.set()
            assert parent_swapped.wait(timeout=5)
            return super().encode(encoding, errors)

    def swap_parent_for_symlink() -> None:
        assert encode_started.wait(timeout=5)
        reports.rename(displaced)
        reports.symlink_to(outside, target_is_directory=True)
        parent_swapped.set()

    attacker = threading.Thread(target=swap_parent_for_symlink)
    attacker.start()
    try:
        with pytest.raises(ValueError, match="write parent changed"):
            atomic_write_text_confined(
                project,
                reports / "validation_report.json",
                CoordinatedText("replacement\n"),
            )
    finally:
        attacker.join(timeout=5)

    assert not attacker.is_alive()
    assert sentinel.read_text(encoding="utf-8") == "outside sentinel\n"
    assert not (displaced / "validation_report.json").exists()


def test_source_symlink_target_is_confined_and_fingerprinted(tmp_path: Path) -> None:
    project = _green_project(tmp_path)
    shared = tmp_path / "projects" / "templates" / "shared" / "src" / "engine.py"
    write_doc(shared, "VALUE = 1\n")
    (project / "src" / "shared").symlink_to(shared.parent, target_is_directory=True)
    _write_green_validation_report(tmp_path, project)
    write_rendered_provenance_receipt(tmp_path, PROJECT)
    before = build_current_rendered_snapshot(tmp_path, PROJECT)

    write_doc(shared, "VALUE = 2\n")
    after = build_current_rendered_snapshot(tmp_path, PROJECT)

    assert after.source != before.source
    _write_green_validation_report(tmp_path, project)
    assert "SOURCE_FINGERPRINT_DRIFT" in {
        issue.code for issue in validate_rendered_provenance(tmp_path, PROJECT).issues
    }


def test_directory_symlink_fingerprint_is_checkout_root_independent(tmp_path: Path) -> None:
    snapshots = []
    for checkout_name in ("checkout-a", "different-checkout-root"):
        root = tmp_path / checkout_name
        project = _green_project(root)
        shared = root / "projects" / "templates" / "shared" / "src" / "engine.py"
        write_doc(shared, "VALUE = 1\n")
        (project / "src" / "shared").symlink_to(shared.parent, target_is_directory=True)
        snapshots.append(build_current_rendered_snapshot(root, PROJECT))

    assert snapshots[0].source == snapshots[1].source
