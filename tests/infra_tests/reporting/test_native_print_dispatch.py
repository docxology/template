"""Configured print selection and real bounded pixels; no acceptance surrogates."""

from __future__ import annotations

import importlib.util
import marshal
import os
import shutil
import struct
import time
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_format_observer_outcome import native_observer_outcome
from infrastructure.reporting.native_print_artifact_controls import (
    print_control_artifacts,
    print_control_names,
    selected_control_artifacts,
)
from infrastructure.reporting.native_print_artifact_observer import (
    FINDING,
    configured_print_target,
    inspect_configured_print,
    selected_print_artifact,
)
from infrastructure.reporting.native_print_child_custody import (
    BasicBrowserControlReaderOperation,
    PrintControlReaderOperation,
    SemanticBrowserControlReaderOperation,
    SlideControlReaderOperation,
)
from infrastructure.reporting.native_print_control_replay import validate_print_controls
from infrastructure.reporting.native_print_mutations import mutate_print
from infrastructure.reporting.native_print_source_loader import PrintSourceLoader
from infrastructure.reporting.native_storybook_source import StorybookReference
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("kind", ["storybook", "newspaper"])
def test_source_configured_roles_selected_and_substitute_paths_refused(tmp_path: Path, kind: str) -> None:
    scope = f"templates/template_{kind}"
    project = tmp_path / "projects" / scope
    project.mkdir(parents=True)
    for name in ("src", "content"):
        shutil.copytree(ROOT / "projects" / scope / name, project / name)
    artifacts = print_control_artifacts(tmp_path, scope)
    assert artifacts and all(selected_print_artifact(scope, artifact) for artifact in artifacts)
    for artifact in artifacts:
        configured_print_target(tmp_path, scope, artifact)
        substitute = NativeArtifact(artifact.id, artifact.format, artifact.path + ".substitute")
        with pytest.raises(ValueError, match="configured"):
            configured_print_target(tmp_path, scope, substitute)
        assert not selected_print_artifact("templates/template_code_project", artifact)
    assert not selected_print_artifact(scope, NativeArtifact("manuscript:pdf", "pdf", "output/report.pdf"))
    assert not selected_print_artifact(scope, NativeArtifact("storybook:page:01", "png", "output/page.png"))
    assert selected_control_artifacts(tmp_path, scope, "baseline") == artifacts
    for name in print_control_names(scope)[1:]:
        selected = selected_control_artifacts(tmp_path, scope, name)
        assert selected and all(artifact in artifacts for artifact in selected)


def _png() -> bytes:
    with Image.new("RGB", (800, 900), (30, 80, 140)) as image:
        stream = BytesIO()
        image.save(stream, format="PNG")
        return stream.getvalue()


@pytest.mark.parametrize("name", ["caption-pixels", "background-pixels", "png-transparency"])
def test_real_valid_png_mutants_preserve_intended_source_diagnostic(name: str) -> None:
    original = _png()
    reference = StorybookReference("0" * 64, (800, 900), ("page.png",), (original,), original)
    baseline = inspect_configured_print(original, reference, kind="page", page_number=0, deadline=time.monotonic() + 10)
    assert baseline["status"] == "pass" and baseline["findings"] == baseline["blockers"] == []
    mutant = mutate_print(original, name, "storybook")
    assert mutant != original
    observed = inspect_configured_print(mutant, reference, kind="page", page_number=0, deadline=time.monotonic() + 10)
    assert observed["status"] == "fail" and observed["blockers"] == []
    assert {finding["code"] for finding in observed["findings"]} == {FINDING}
    outcome = native_observer_outcome(
        {
            "format": "png",
            "observation": observed,
            "print_reference": {"path": "output/readiness/reference.json", "sha256": "0" * 64},
        }
    )
    assert outcome == observed


def test_arbitrary_png_cannot_claim_configured_print_outcome() -> None:
    with pytest.raises(ValueError, match="configured print custody"):
        native_observer_outcome({"format": "png", "observation": {"status": "pass", "findings": [], "blockers": []}})


@pytest.mark.parametrize("scope", ["templates/template_storybook", "templates/template_newspaper"])
def test_missing_or_reordered_print_suite_fails_before_receipt_admission(tmp_path: Path, scope: str) -> None:
    names = print_control_names(scope)
    for records in ([], [{"name": name} for name in reversed(names)], [{"name": name} for name in names[:-1]]):
        with pytest.raises(ValueError, match="missing, duplicated or reordered"):
            validate_print_controls(
                records,
                tmp_path,
                tmp_path / "output/readiness/native",
                scope,
                SnapshotReader(tmp_path),
                run_id="0" * 32,
                custody={},
                runtime={},
                versions={},
                expected_pid=os.getpid(),
                expected_platform="Darwin",
                original_deadline=time.monotonic() + 10,
                deadline=time.monotonic() + 10,
                source=None,
            )


@pytest.mark.parametrize(
    "operation",
    [
        PrintControlReaderOperation,
        SlideControlReaderOperation,
        BasicBrowserControlReaderOperation,
        SemanticBrowserControlReaderOperation,
    ],
)
def test_data_cannot_construct_original_control_reader(tmp_path: Path, operation: type) -> None:
    with pytest.raises(ValueError, match="genuine unwrapped"):
        operation(
            None,
            SnapshotReader(tmp_path),
            [],
            scope="templates/template_storybook",
            run_id="0" * 32,
            deadline=time.monotonic() + 10,
        )


def test_control_subclass_cannot_choose_an_original_child_role(tmp_path: Path) -> None:
    class CallerSelectedRole(SlideControlReaderOperation):
        schema = "template-source-owned-print-child-v1"

    with pytest.raises(ValueError, match="exact Source-owned concrete reader type"):
        CallerSelectedRole(
            None,
            SnapshotReader(tmp_path),
            [],
            scope="templates/template_scientific_slides",
            run_id="0" * 32,
            deadline=time.monotonic() + 10,
        )


def test_print_source_loader_ignores_same_size_timestamp_pyc(tmp_path: Path) -> None:
    source = tmp_path / "provider.py"
    source.write_bytes(b"VALUE = 42\n")
    observed = source.stat()
    cached = Path(importlib.util.cache_from_source(str(source)))
    cached.parent.mkdir(parents=True, exist_ok=True)
    poisoned = compile(b"VALUE = 99\n", str(source), "exec", dont_inherit=True)
    cached.write_bytes(
        importlib.util.MAGIC_NUMBER
        + struct.pack("<III", 0, int(observed.st_mtime), observed.st_size)
        + marshal.dumps(poisoned)
    )
    try:
        namespace: dict[str, object] = {}
        exec(PrintSourceLoader("provider", source, tmp_path).get_code("provider"), namespace)
        assert namespace["VALUE"] == 42
        assert cached.read_bytes().endswith(marshal.dumps(poisoned))
    finally:
        cached.unlink()


def test_print_source_loader_refuses_aliased_body(tmp_path: Path) -> None:
    source = tmp_path / "original.py"
    source.write_text("VALUE = 42\n")
    alias = tmp_path / "alias.py"
    alias.symlink_to(source)
    with pytest.raises(ValueError, match="escaped"):
        PrintSourceLoader("provider", alias, tmp_path).get_code("provider")
