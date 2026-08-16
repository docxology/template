"""Real-file tests for the typed descriptor figure producer (no mocks)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, cast

import pytest

from data_descriptor import (
    DESCRIPTOR_FIGURE_SPECS,
    DescriptorFigureInputs,
    DescriptorFigureRun,
    FigureRegistryError,
    FileVerification,
    descriptor_figure_specs_for_data,
    generate_descriptor_figure_assets,
    load_descriptor_figure_inputs,
    publish_descriptor_figure_run,
    render_descriptor_figures,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FILENAMES = {spec.filename for spec in DESCRIPTOR_FIGURE_SPECS}


def _load_fixture() -> dict[str, Any]:
    return cast(
        "dict[str, Any]",
        json.loads((PROJECT_ROOT / "data" / "example_descriptor.json").read_text(encoding="utf-8")),
    )


def test_load_inputs_binds_report_and_byte_checks_to_one_descriptor() -> None:
    inputs = load_descriptor_figure_inputs(PROJECT_ROOT)

    assert inputs.descriptor == _load_fixture()
    assert inputs.readiness_score == 1.0
    assert [check.status for check in inputs.checks] == ["verified", "verified"]


def test_renderer_writes_complete_byte_deterministic_real_png_set(tmp_path: Path) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    shutil.copytree(PROJECT_ROOT / "data", first_root / "data")
    shutil.copytree(PROJECT_ROOT / "data", second_root / "data")

    first = render_descriptor_figures(first_root)
    second = render_descriptor_figures(second_root)

    assert {path.name for path in first.rendered_paths} == EXPECTED_FILENAMES
    first_bytes = {path.name: path.read_bytes() for path in first.rendered_paths}
    second_bytes = {path.name: path.read_bytes() for path in second.rendered_paths}
    assert first_bytes == second_bytes
    assert all(payload.startswith(b"\x89PNG\r\n\x1a\n") for payload in first_bytes.values())


def test_full_source_producer_publishes_exact_run_and_truthful_alternate_text(tmp_path: Path) -> None:
    alternate = _load_fixture()
    alternate["fields"] = alternate["fields"][:2]
    alternate["files"] = [
        {
            "path": "fixtures/alternate.csv",
            "media_type": "text/csv",
            "rows": 99,
            "checksum": "sha256:alternate",
        }
    ]
    alternate["provenance"] = [{"step": "inspect", "agent": "reviewer"}]
    alternate.pop("license")
    inputs = DescriptorFigureInputs(
        descriptor=alternate,
        checks=(
            FileVerification(
                "fixtures/alternate.csv",
                "row_mismatch",
                "sha256:alternate",
                "sha256:observed",
                99,
                98,
                False,
                False,
            ),
            FileVerification(
                "fixtures/absent.csv",
                "absent",
                "sha256:absent",
                "",
                4,
                -1,
                False,
                False,
            ),
        ),
        readiness_score=0.625,
    )

    run = render_descriptor_figures(tmp_path, inputs=inputs)
    published = publish_descriptor_figure_run(tmp_path, run)

    assert len(published) == len(EXPECTED_FILENAMES) + 1
    registry_path = tmp_path / "output" / "figures" / "figure_registry.json"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    descriptions = {record["label"]: record["metadata"]["alt_text"] for record in payload["figures"]}
    assert "2-row data dictionary" in descriptions["fig:schema_overview"]
    assert "fixtures/alternate.csv: 99" in descriptions["fig:file_inventory"]
    assert "inspect (reviewer)" in descriptions["fig:provenance_flow"]
    assert "status row_mismatch" in descriptions["fig:checksum_verification"]
    assert "status absent" in descriptions["fig:checksum_verification"]
    assert "0.625" in descriptions["fig:checksum_verification"]


def test_empty_input_renders_without_inventing_fixture_content(tmp_path: Path) -> None:
    inputs = DescriptorFigureInputs(descriptor={}, checks=(), readiness_score=0.0)

    run = render_descriptor_figures(tmp_path, inputs=inputs)
    specs = {
        spec.label: spec
        for spec in descriptor_figure_specs_for_data(
            run.inputs.descriptor,
            run.inputs.checks,
            readiness_score=run.inputs.readiness_score,
        )
    }

    assert {path.name for path in run.rendered_paths} == EXPECTED_FILENAMES
    assert "Empty data-dictionary table" in specs["fig:schema_overview"].alt_text
    assert "Empty file-inventory bar chart" in specs["fig:file_inventory"].alt_text
    assert "Empty provenance-flow panel" in specs["fig:provenance_flow"].alt_text
    assert "Empty descriptor-to-file verification table" in specs["fig:checksum_verification"].alt_text


def test_incomplete_render_run_fails_before_creating_publication_directory(tmp_path: Path) -> None:
    shutil.copytree(PROJECT_ROOT / "data", tmp_path / "data")
    complete = render_descriptor_figures(tmp_path)
    incomplete = DescriptorFigureRun(
        inputs=complete.inputs,
        specs=complete.specs,
        rendered_paths=complete.rendered_paths[:-1],
    )

    with pytest.raises(FigureRegistryError, match="missing generated figure file"):
        publish_descriptor_figure_run(tmp_path, incomplete)

    assert not (tmp_path / "output").exists()


def test_publication_uses_descriptions_bound_at_render_time(tmp_path: Path) -> None:
    shutil.copytree(PROJECT_ROOT / "data", tmp_path / "data")
    run = render_descriptor_figures(tmp_path)
    expected = {spec.label: spec.alt_text for spec in run.specs}

    run.inputs.descriptor["fields"] = []
    run.inputs.descriptor["files"] = []
    published = publish_descriptor_figure_run(tmp_path, run)

    registry_path = published[-1]
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    observed = {record["label"]: record["metadata"]["alt_text"] for record in payload["figures"]}
    assert observed == expected
    assert "6-row data dictionary" in observed["fig:schema_overview"]
    assert "2 horizontal bars" in observed["fig:file_inventory"]


def test_generate_assets_is_the_complete_typed_producer(tmp_path: Path) -> None:
    shutil.copytree(PROJECT_ROOT / "data", tmp_path / "data")

    written = generate_descriptor_figure_assets(tmp_path)

    assert len(written) == (len(EXPECTED_FILENAMES) * 2) + 1
    assert {path.name for path in written[:-1]} == EXPECTED_FILENAMES
    assert written[-1] == tmp_path / "output" / "figures" / "figure_registry.json"
