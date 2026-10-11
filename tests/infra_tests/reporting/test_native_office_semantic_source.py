"""Actual combined-source parsing and admission controls, without native pass claims."""

from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

import pytest

from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact, native_environment
from infrastructure.reporting.native_office_semantic_source import observe_office_semantic_source
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.validation.publication.rendered_provenance import write_rendered_provenance_receipt
from tests.infra_tests.validation._rendered_provenance_helpers import _green_project

PROJECT = "templates/template_sia"


def _admitted_project(root: Path) -> Path:
    """Bind an invented source fixture under an actual admitted public identity."""
    from infrastructure.rendering.manuscript_composition import write_manuscript_composition
    from infrastructure.validation.rendered_snapshot import build_current_rendered_snapshot
    from infrastructure.validation.output.validator import collect_detailed_validation_results
    from infrastructure.core.pipeline.artifacts import snapshot_current_artifact_manifest

    original = _green_project(root)
    project = original.with_name("template_sia")
    original.rename(project)
    methods = "# Methods\n\nMeasured $n+1$ [@invented].\n\n| Quantity | Measured |\n|---|---|\n| Offset | -3.25 mV |\n"
    bibliography = "@article{invented, author={Doe, Jane}, title={Invented measurement}, year={2020}, journal={Invented Journal}}\n"
    for relative in ("manuscript", "output/manuscript"):
        (project / relative / "01_methods.md").write_text(methods)
        (project / relative / "references.bib").write_text(bibliography)
    paths = sorted((project / "output/manuscript").glob("*.md"))
    combined = project / "output/web/_combined_manuscript.md"
    combined.write_text("\n\n".join(path.read_text().rstrip() for path in paths) + "\n")
    write_manuscript_composition(project, PROJECT, paths, combined, algorithm="web-renderer-combine-v1")
    snapshot_current_artifact_manifest(project / "output")
    snapshot = build_current_rendered_snapshot(root, PROJECT)
    report = project / "output/reports/validation_report.json"
    payload = json.loads(report.read_text())
    payload["validated_inputs"] = snapshot.validated_inputs_dict()
    payload["output_statistics"]["detailed_validation"] = collect_detailed_validation_results(
        project / "output", require_pdf=False
    )
    report.write_text(json.dumps(payload))
    return project


@pytest.mark.parametrize("kind", ("docx", "epub"))
def test_actual_combined_source_parser_preserves_hydrated_occurrences(tmp_path: Path, kind: str) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("actual Pandoc is unavailable")
    _admitted_project(tmp_path)
    write_rendered_provenance_receipt(tmp_path, PROJECT)
    directory = tmp_path / "output/readiness/semantic"
    directory.mkdir(parents=True)
    artifact = NativeArtifact(f"manuscript:{kind}", kind, f"output/invented.{kind}")
    ast, receipt = observe_office_semantic_source(
        tmp_path,
        directory,
        PROJECT,
        artifact,
        SnapshotReader(tmp_path),
        env=native_environment(tmp_path, Path(sys.executable), directory),
        deadline=time.monotonic() + 30,
        run_id="invented-combined-source",
    )
    document = json.loads(ast)
    text = json.dumps(document["blocks"])
    assert '"7"' in text
    assert "RESULT_COUNT" not in text
    assert len(receipt["sources"]) == 2
    assert receipt["tool"]["original_exit_code"] == 0
    assert receipt["format"] == kind
    assert receipt["filters"]
    assert len(receipt["bibliographies"]) == 1
    assert '"Math"' in text and "n+1" in text
    assert '"Table"' in text and "-3.25" in text
    assert '"Cite"' in text and "invented" in text and "2020" in text
    assert receipt["blockers"] == []
    assert receipt["source_coverage_tool"]["original_exit_code"] == 0
    assert receipt["source_coverage"]["counts"]["RawBlock"] == 1
    assert receipt["source_coverage"]["counts"]["Cite"] == 1
    from infrastructure.reporting.native_office_source_coverage import office_coverage_obligations

    coverage = office_coverage_obligations(ast)
    assert coverage["counts"]["Math"] == 1
    assert coverage["counts"]["Table"] == 1
    assert coverage["counts"]["Cite"] == 1
    assert coverage["counts"]["RawBlock"] == 1
    assert len(coverage["blockers"]) == 4
    # Both candidate and reference can share an omission. The independent
    # source census must retain that requirement rather than count equality.
    omitted = json.loads(ast)
    omitted["blocks"] = []
    empty = office_coverage_obligations(json.dumps(omitted).encode())
    assert empty["counts"]["Math"] == 0
    assert coverage["source_ast_sha256"] != empty["source_ast_sha256"]


def test_source_parser_rejects_stale_hydration_before_native_command(tmp_path: Path) -> None:
    project = _admitted_project(tmp_path)
    write_rendered_provenance_receipt(tmp_path, PROJECT)
    (project / "output/manuscript/00_abstract.md").write_text("# Changed\n\nThere were 8 results.\n")
    directory = tmp_path / "output/readiness/semantic"
    directory.mkdir(parents=True)
    with pytest.raises(ValueError, match="current consumed hydration"):
        observe_office_semantic_source(
            tmp_path,
            directory,
            PROJECT,
            NativeArtifact("manuscript:docx", "docx", "invented.docx"),
            SnapshotReader(tmp_path),
            env={},
            deadline=time.monotonic() + 30,
            run_id="invented-stale-source",
        )
    assert not (directory / "office-semantic-source.md").exists()
