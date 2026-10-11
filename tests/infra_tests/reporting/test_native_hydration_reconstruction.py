"""Exact byte/occurrence controls; no invented original execution authority."""

import time
from pathlib import Path

import pytest

from infrastructure.rendering.manuscript_hydration_replay import (
    combine_held_manuscripts,
    reconstruct_shared_hydration,
    require_shared_hydration,
)
from infrastructure.rendering.manuscript_injection import write_resolved_manuscript_tree
from infrastructure.rendering._pdf_markdown_combine import combine_manuscript_markdown_sections
from infrastructure.rendering._pdf_combined_markdown import preprocess_combined_markdown
from infrastructure.reporting.native_hydration_reconstruction import (
    _pdf_body,
    replay_native_hydration_reconstruction,
    replay_native_pdf_recomposition,
)
from infrastructure.reporting.native_projection_contracts import ProjectionSourceUnsupported
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def test_repeated_unicode_occurrences_keep_exact_original_and_output_offsets() -> None:
    source = "α {{VALUE}}\r\nβ {{VALUE}} {{UNIT}}\r\n".encode()
    values = {"VALUE": "-2.50", "UNIT": "µm"}
    expected = "α -2.50\nβ -2.50 µm\n".encode()
    proof = require_shared_hydration(source, values, expected)
    assert proof.output == expected and [row.key for row in proof.occurrences] == ["VALUE", "VALUE", "UNIT"]
    assert [row.ordinal for row in proof.occurrences] == [1, 2, 3]
    for row in proof.occurrences:
        assert source[row.source_start_byte : row.source_end_byte] == ("{{" + row.key + "}}").encode()
        assert expected[row.output_start_byte : row.output_end_byte] == values[row.key].encode()


@pytest.mark.parametrize(
    "changed",
    [
        b"2.50 mm then -2.50 mm",
        b"-2.50 cm then -2.50 mm",
        b"-2.50 mm",
        b"-2.50 mm then -2.50 mm then -2.50 mm",
    ],
)
def test_changed_sign_unit_omitted_or_repeated_consumed_body_is_refused(changed: bytes) -> None:
    source = b"{{VALUE}} {{UNIT}} then {{VALUE}} {{UNIT}}"
    with pytest.raises(ValueError, match="differs from exact"):
        require_shared_hydration(source, {"VALUE": "-2.50", "UNIT": "mm"}, changed)


def test_unresolved_source_token_cannot_be_promoted_by_equal_consumed_bytes() -> None:
    source = b"actual {{MISSING}} and KW{{For each keyword}}"
    proof = reconstruct_shared_hydration(source, {})
    assert len(proof.occurrences) == 1 and proof.occurrences[0].resolved is False
    with pytest.raises(ValueError, match="unresolved"):
        require_shared_hydration(source, {}, source)


def test_actual_source_order_is_not_collapsed_or_selected_by_content_equality() -> None:
    assert combine_held_manuscripts((b"one\n", b"two\n", b"one\n"), separator="\n---\n\n") == (
        b"one\n\n\n\n---\n\n\n\ntwo\n\n\n\n---\n\n\n\none\n"
    )


def test_real_shared_writer_and_composer_match_complete_unicode_occurrences(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source_dir = project / "manuscript"
    source_dir.mkdir(parents=True)
    bodies = ("α {{VALUE}} {{UNIT}}\r\n", "β {{VALUE}}\n{{VALUE}} {{UNIT}}\n")
    inputs = []
    for ordinal, body in enumerate(bodies):
        path = source_dir / f"{ordinal:02d}_section.md"
        path.write_bytes(body.encode())
        inputs.append(path)
    variables = {"VALUE": "-2.50", "UNIT": "µm"}
    resolved_dir = write_resolved_manuscript_tree(project, variables)
    resolved = [resolved_dir / path.name for path in inputs]
    held = []
    for path, consumed in zip(inputs, resolved, strict=True):
        actual = consumed.read_bytes()
        proof = require_shared_hydration(path.read_bytes(), variables, actual)
        assert proof.output == actual and all(row.resolved for row in proof.occurrences)
        held.append(actual)
    for breaks in (False, True):
        actual_combined = combine_manuscript_markdown_sections(resolved, section_breaks=breaks).encode()
        separator = "\n```{=latex}\n\\newpage\n```\n" if breaks else ""
        assert combine_held_manuscripts(tuple(held), separator=separator) == actual_combined
    assert combine_held_manuscripts((b"two", b"one", b"one"), separator="") != combine_held_manuscripts(
        (b"one", b"two", b"one"),
        separator="",
    )


def test_serialized_hydration_data_cannot_create_an_original_or_reader_operation(tmp_path: Path) -> None:
    reader = SnapshotReader(tmp_path)
    path = tmp_path / "output/readiness/original.json"
    path.parent.mkdir(parents=True)
    path.write_text('{"scope":"templates/template_code_project","status":"pass","fulfilled":true}')
    with pytest.raises(ProjectionSourceUnsupported, match="externally admitted"):
        replay_native_hydration_reconstruction(
            "templates/template_code_project", reader.read("output/readiness/original.json"), reader
        )
    with pytest.raises(ProjectionSourceUnsupported, match="externally admitted"):
        replay_native_pdf_recomposition(
            "templates/template_code_project", reader.read("output/readiness/original.json"), reader
        )


@pytest.mark.parametrize("breaks", [False, True])
def test_pdf_recomposition_uses_actual_pdf_algorithm_even_when_last_composition_is_web(
    tmp_path: Path, breaks: bool
) -> None:
    manuscript = tmp_path / "projects/templates/template_code_project/manuscript"
    manuscript.mkdir(parents=True)
    bodies = (b"\xef\xbb\xbf# First\r\n{{maturity.real}}\r\n", b"# Second\n![plot](../../output/figures/plot.png)\n")
    paths = []
    for ordinal, body in enumerate(bodies):
        path = manuscript / f"{ordinal:02d}_section.md"
        path.write_bytes(body)
        paths.append(path)
    (manuscript / "manuscript_vars.yaml").write_text("maturity:\n  real: 7\n")
    reader = SnapshotReader(tmp_path)
    variables = reader.read("projects/templates/template_code_project/manuscript/manuscript_vars.yaml")
    actual = preprocess_combined_markdown(
        combine_manuscript_markdown_sections(paths, section_breaks=breaks), manuscript_dir=manuscript
    ).content.encode()
    independently_rebuilt, mermaid_rows, mermaid_gaps = _pdf_body(
        bodies,
        {"rendering": {"section_breaks": breaks}},
        variables,
        reader,
        "templates/template_code_project",
        deadline=time.monotonic() + 20,
    )
    assert independently_rebuilt == actual
    assert independently_rebuilt != combine_held_manuscripts(bodies, separator="\n---\n\n")
    assert b"7" in actual and b"../figures/plot.png" in actual
    assert mermaid_rows == [] and mermaid_gaps == []
    assert reader.unchanged()


@pytest.mark.parametrize("body", [b"```mermaid\ngraph LR; A-->B\n```\n", b"```mermaid\ngraph LR; A-->B\n"])
def test_pdf_mermaid_transform_stays_unqualified_without_original_renderer(tmp_path: Path, body: bytes) -> None:
    reader = SnapshotReader(tmp_path)
    rebuilt, mermaid_rows, mermaid_gaps = _pdf_body(
        (body,), {}, None, reader, "templates/template_code_project", deadline=time.monotonic() + 20
    )
    assert rebuilt is None
    assert reader.native_operation is None and reader.native_producer_operation is None
    assert reader.native_control_operation is None
    if body.endswith(b"```\n"):
        assert len(mermaid_rows) == 1 and mermaid_rows[0]["ordinal"] == 1
        assert mermaid_gaps == [
            "selected-inline-mermaid-missing-positive-source-and-asset:" + mermaid_rows[0]["production_stem"]
        ]
    else:
        assert mermaid_rows == []
        assert mermaid_gaps == ["unsupported-selected-mermaid-fence-transformation"]
    assert reader.unchanged()
