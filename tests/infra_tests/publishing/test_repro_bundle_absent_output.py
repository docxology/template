#!/usr/bin/env python3
"""Regression test for REPRO-VERIFY-1: declared-but-absent outputs must not pass."""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.publishing.repro_bundle import (
    BUNDLE_MANIFEST_NAME,
    build_repro_bundle,
    verify_repro_bundle,
)
from tests._support.projects import make_project, write_doc


# NOTE: artifact_manifest.json stores output paths RELATIVE TO THE PROJECT DIR
# (infrastructure.core.pipeline.artifacts records ``path.relative_to(project_dir)``),
# e.g. ``output/figures/x.png``; the repro bundle rebases them onto the repo root
# (``projects/<name>/output/figures/x.png``). These scaffolds therefore declare
# project-relative manifest paths and place files under the project's own output/
# tree — matching the real pipeline (and the REPRO-1 resolver fix).


def _scaffold_with_absent_declared_output(root: Path, name: str) -> tuple[Path, str]:
    project = make_project(root, name, with_manuscript=True, with_scripts=True)
    write_doc(root / "uv.lock", "# lock contents\n")
    write_doc(root / "pyproject.toml", "[project]\nname = 'demo'\n")
    write_doc(root / "docs" / "_generated" / "COUNTS.md", "# Canonical Facts\n\n- 214\n")

    artifact_manifest = project / "output" / "reports" / "artifact_manifest.json"
    write_doc(
        artifact_manifest,
        json.dumps({"entries": [{"path": "output/figures/missing.png"}]}),
    )
    declared = project / "output" / "figures" / "missing.png"
    assert not declared.exists(), "test precondition: declared output must be absent"
    # The bundle records output paths rebased onto the repo root.
    declared_rel = declared.relative_to(root).as_posix()
    return project, declared_rel


def test_declared_absent_output_refuses_at_build_or_fails_verify(tmp_path: Path) -> None:
    name = "repro_absent_output"
    _project, declared_rel = _scaffold_with_absent_declared_output(tmp_path, name)

    try:
        out_dir = build_repro_bundle(tmp_path, name, generated_at="2026-06-08T00:00:00+00:00")
    except (ValueError, RuntimeError):
        return

    report = verify_repro_bundle(out_dir / BUNDLE_MANIFEST_NAME, checkout_root=tmp_path)
    assert report.ok is False, "declared-but-absent output verified GREEN — reproduces nothing"
    missing = [m for m in report.mismatches if m["path"] == declared_rel]
    assert len(missing) == 1
    assert missing[0]["reason"] in {"missing", "missing-declared-output"}


def test_infra_input_absent_remains_allowed(tmp_path: Path) -> None:
    name = "repro_infra_absent"
    project = make_project(tmp_path, name, with_manuscript=True, with_scripts=True)
    artifact_manifest = project / "output" / "reports" / "artifact_manifest.json"
    write_doc(
        artifact_manifest,
        json.dumps({"entries": [{"path": "output/figures/result.png"}]}),
    )
    # Declared output present under the project tree; infra inputs (uv.lock,
    # pyproject, COUNTS) are intentionally absent and must not fail verify.
    write_doc(project / "output" / "figures" / "result.png", "PNG-BYTES")

    out_dir = build_repro_bundle(tmp_path, name, generated_at="2026-06-08T00:00:00+00:00")
    report = verify_repro_bundle(out_dir / BUNDLE_MANIFEST_NAME, checkout_root=tmp_path)

    assert report.ok is True, f"absent infra inputs wrongly failed verify: {report.mismatches}"
