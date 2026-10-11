"""Exact source checks survive producer path removal and reject changed bytes."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from infrastructure.core.pipeline.fingerprints import source_content_fingerprint
from infrastructure.project.public_acceptance_evidence import runtime_identity
from infrastructure.reporting.native_format_portable_custody import producer_custody
from infrastructure.reporting.native_format_portable_source import native_source_content_identity


def test_external_sdk_original_labels_preserve_actual_source_after_relocation(tmp_path: Path) -> None:
    original = tmp_path / "producer/source"
    project = original / "projects/templates/template_code_project"
    for path in (original / "infrastructure", original / "scripts", project / "src"):
        path.mkdir(parents=True)
    (original / "infrastructure/candidate.py").write_text("VALUE = 42\n")
    (original / "scripts/stage.py").write_text("print('actual source')\n")
    (project / "src/model.py").write_text("def measure():\n    return 42\n")
    (original / "pyproject.toml").write_text('[project]\nname="source-fixture"\n')
    definition = original / "pipeline.yaml"
    definition.write_text("stages: []\n")
    custody = producer_custody(original, runtime_identity(), "a" * 64)
    expected = source_content_fingerprint(original, project, definition_path=definition)
    relocated = tmp_path / "elsewhere/reader"
    shutil.copytree(original, relocated)
    shutil.rmtree(original)
    moved_project = relocated / project.relative_to(original)
    assert (
        native_source_content_identity(relocated, moved_project, custody, definition_path=relocated / "pipeline.yaml")
        == expected
    )
    model = moved_project / "src/model.py"
    model.write_text("def measure():\n    return 43\n")
    assert (
        native_source_content_identity(relocated, moved_project, custody, definition_path=relocated / "pipeline.yaml")
        != expected
    )
    model.unlink()
    model.symlink_to(tmp_path / "outside")
    with pytest.raises((ValueError, OSError)):
        native_source_content_identity(relocated, moved_project, custody, definition_path=relocated / "pipeline.yaml")
