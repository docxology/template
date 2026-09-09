"""Stable-local inventory mode, runtime-history exclusions, and declared output paths."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from infrastructure.core.pipeline.artifacts import (
    STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    collect_stable_output_inventory,
    snapshot_current_artifact_manifest,
)
from infrastructure.core.pipeline.types import StageContract


def test_whole_ignored_project_output_uses_explicit_stable_local_mode(tmp_path: Path) -> None:
    """Private project output remains testable without claiming Git shippability."""
    project = tmp_path / "private-project"
    stable = project / "output" / "data" / "result.json"
    hidden = project / "output" / "data" / ".private" / "token.txt"
    runtime = project / "output" / "logs" / "pipeline.log"
    renderer_intermediate = project / "output" / "pdf" / "_combined_manuscript.tex"
    for path in (stable, hidden, runtime, renderer_intermediate):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("payload\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=project, check=True, capture_output=True)
    (project / ".gitignore").write_text("output/\n", encoding="utf-8")

    strict = collect_stable_output_inventory(project / "output")
    inventory = collect_stable_output_inventory(
        project / "output",
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )

    assert strict.mode == "stable-shippable-output-v1"
    assert strict.files == ()
    assert inventory.mode == "stable-local-output-v1"
    assert [path.relative_to(project / "output").as_posix() for path in inventory.files] == ["data/result.json"]


@pytest.mark.parametrize("blanket_rule", ["output/", "output/*", "output/**"])
def test_stable_local_mode_bypasses_equivalent_blanket_packaging_rules(
    tmp_path: Path,
    blanket_rule: str,
) -> None:
    project = tmp_path / "private-project"
    stable = project / "output" / "data" / "result.json"
    stable.parent.mkdir(parents=True)
    stable.write_text("{}\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=project, check=True, capture_output=True)
    (project / ".gitignore").write_text(blanket_rule + "\n", encoding="utf-8")

    inventory = collect_stable_output_inventory(
        project / "output",
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )

    assert [path.relative_to(project / "output").as_posix() for path in inventory.files] == ["data/result.json"]


def test_stable_local_mode_still_honors_selective_git_ignores(tmp_path: Path) -> None:
    project = tmp_path / "private-project"
    stable = project / "output" / "data" / "result.json"
    scratch = project / "output" / "data" / "local.scratch"
    for path in (stable, scratch):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("payload\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=project, check=True, capture_output=True)
    (project / ".gitignore").write_text("output/data/*.scratch\n", encoding="utf-8")

    inventory = collect_stable_output_inventory(
        project / "output",
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )

    assert [path.relative_to(project / "output").as_posix() for path in inventory.files] == ["data/result.json"]


def test_stable_local_mode_does_not_misclassify_extension_ignore_as_blanket(tmp_path: Path) -> None:
    project = tmp_path / "private-project"
    stable = project / "output" / "data" / "result.json"
    binary = project / "output" / "data" / "private.bin"
    for path in (stable, binary):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("payload\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=project, check=True, capture_output=True)
    (project / ".gitignore").write_text("*.bin\n", encoding="utf-8")

    inventory = collect_stable_output_inventory(
        project / "output",
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )

    assert [path.relative_to(project / "output").as_posix() for path in inventory.files] == ["data/result.json"]


def test_runtime_history_is_not_stable_but_regular_reports_are(tmp_path: Path) -> None:
    """Telemetry history stays local without hiding genuine stable reports."""
    project = tmp_path / "nogit"
    reports = project / "output" / "reports"
    history = reports / ".history"
    history.mkdir(parents=True)
    (history / "telemetry-123.json").write_text('{"runtime": true}\n', encoding="utf-8")
    (reports / "quality_summary.json").write_text('{"all_passed": true}\n', encoding="utf-8")

    manifest = snapshot_current_artifact_manifest(project / "output")

    recorded = {entry.path for entry in manifest.entries}
    assert "output/reports/.history/telemetry-123.json" not in recorded
    assert "output/reports/quality_summary.json" in recorded


def test_optional_full_evidence_registry_is_not_stable(tmp_path: Path) -> None:
    """The opt-in diagnostic registry cannot perturb publication statistics."""
    output = tmp_path / "project" / "output"
    result = output / "data" / "result.json"
    result.parent.mkdir(parents=True)
    result.write_text('{"measured": 7}\n', encoding="utf-8")

    baseline = collect_stable_output_inventory(output)
    debug_registry = output / "reports" / "evidence_registry_full.json"
    debug_registry.parent.mkdir(parents=True)
    debug_registry.write_text('{"debug_fact_count": 999}\n', encoding="utf-8")
    rerun = collect_stable_output_inventory(output)

    assert rerun == baseline
    assert debug_registry not in rerun.files


def test_runtime_history_is_gitignored_after_public_template_negations() -> None:
    """Post-negation rules must ignore project history and the generated mirror."""
    repo_root = Path(__file__).resolve().parents[3]
    candidates = (
        "projects/templates/template_code_project/output/reports/.history/telemetry-123.json",
        "projects/templates/template_code_project/output/reports/diagnostics.json",
        "projects/templates/template_code_project/output/reports/evidence_registry_full.json",
        "output/templates/template_code_project/reports/.history/telemetry-123.json",
    )

    for candidate in candidates:
        completed = subprocess.run(
            ["git", "check-ignore", "--no-index", "--quiet", candidate],
            cwd=repo_root,
            check=False,
        )
        assert completed.returncode == 0, f"runtime history is not ignored: {candidate}"


def test_every_public_exemplar_manifest_references_only_tracked_files() -> None:
    """Bind to the live tree — this is the assertion CI was failing on."""
    import json
    import subprocess

    from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

    repo_root = Path(__file__).resolve().parents[3]
    tracked = set(
        subprocess.run(["git", "ls-files"], cwd=repo_root, capture_output=True, text=True, check=True).stdout.split()
    )
    checked = 0
    offenders: list[str] = []
    for qualified in PUBLIC_PROJECT_NAMES:
        manifest_path = repo_root / "projects" / qualified / "output" / "reports" / "artifact_manifest.json"
        if f"projects/{qualified}/output/reports/artifact_manifest.json" not in tracked:
            continue
        checked += 1
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in payload.get("entries", []):
            rel = entry.get("path")
            if rel and f"projects/{qualified}/{rel}" not in tracked:
                offenders.append(f"{qualified}: {rel}")
    assert checked > 0, "no tracked exemplar manifests found — the scan set went empty"
    assert not offenders, offenders[:10]


def test_declared_output_paths_reject_parent_traversal(tmp_path: Path) -> None:
    """A projects/ prefix must not be enough to walk out of the repository."""
    from infrastructure.core.pipeline.artifacts import declared_output_paths

    repo = tmp_path / "repo"
    project = repo / "projects" / "p"
    project.mkdir(parents=True)
    victim = tmp_path / "victim.txt"
    victim.write_text("SECRET_OUTSIDE\n", encoding="utf-8")

    with pytest.raises(ValueError, match="escapes confinement"):
        declared_output_paths(repo, project, StageContract(output_artifacts=("projects/../victim.txt",)))
    assert victim.read_text(encoding="utf-8") == "SECRET_OUTSIDE\n"


def test_declared_output_paths_keep_in_repo_outputs(tmp_path: Path) -> None:
    from infrastructure.core.pipeline.artifacts import declared_output_paths

    repo = tmp_path / "repo"
    project = repo / "projects" / "p"
    project.mkdir(parents=True)
    paths = declared_output_paths(
        repo,
        project,
        StageContract(output_artifacts=("projects/{project}/output/data/result.json",)),
    )
    assert paths == (repo / "projects" / "p" / "output" / "data" / "result.json",)
