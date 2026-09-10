"""Rendered publication provenance: combined-manuscript composition parser and algorithm binding."""

from __future__ import annotations
import json
from pathlib import Path
import pytest
from infrastructure.rendering.manuscript_composition import (
    COMPOSITION_RELATIVE_PATH,
    read_manuscript_composition,
)
from infrastructure.validation.publication.rendered_provenance import (
    RECEIPT_RELATIVE_PATH,
    RenderedProvenanceError,
    validate_rendered_provenance,
    write_rendered_provenance_receipt,
)
from infrastructure.validation.rendered_snapshot import build_current_rendered_snapshot
from tests._support.projects import write_doc
from tests.infra_tests.validation._rendered_provenance_helpers import PROJECT, _green_project


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
