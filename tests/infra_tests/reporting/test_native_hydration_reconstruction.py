"""Exact byte/occurrence controls; no invented original execution authority."""

import hashlib
import time
from pathlib import Path

import pytest

from infrastructure.rendering.manuscript_hydration_replay import (
    SharedHydrationWriter,
    combine_held_manuscripts,
    reconstruct_shared_hydration,
    require_shared_hydration,
)
from infrastructure.rendering.manuscript_injection import (
    _rebase_output_links_for_destination,
    hydrate_manuscript_tree,
    substitute_manuscript_text,
    write_resolved_manuscript_tree,
)
from infrastructure.rendering._pdf_markdown_combine import combine_manuscript_markdown_sections
from infrastructure.rendering._pdf_combined_markdown import preprocess_combined_markdown
from infrastructure.rendering.manuscript_ordinal_anchors import (
    annotate_manuscript_ordinals,
    require_unannotated_parser_bytes,
)
from infrastructure.reporting.native_html_hydration_ordinals import compose_html_ordinal_input
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
    proof = require_shared_hydration(source, values, expected, writer=SharedHydrationWriter.RESOLVED_TREE)
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
        require_shared_hydration(
            source, {"VALUE": "-2.50", "UNIT": "mm"}, changed, writer=SharedHydrationWriter.RESOLVED_TREE
        )


def test_unresolved_source_token_cannot_be_promoted_by_equal_consumed_bytes() -> None:
    source = b"actual {{MISSING}} and KW{{For each keyword}}"
    proof = reconstruct_shared_hydration(source, {}, writer=SharedHydrationWriter.RESOLVED_TREE)
    assert len(proof.occurrences) == 1 and proof.occurrences[0].resolved is False
    with pytest.raises(ValueError, match="unresolved"):
        require_shared_hydration(source, {}, source, writer=SharedHydrationWriter.RESOLVED_TREE)


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
        proof = require_shared_hydration(
            path.read_bytes(), variables, actual, writer=SharedHydrationWriter.RESOLVED_TREE
        )
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


def test_real_ownership_writer_normalizes_after_replacement_without_touching_authored_bytes(tmp_path: Path) -> None:
    project = tmp_path / "project"
    manuscript = project / "manuscript"
    manuscript.mkdir(parents=True)
    source = (
        "é /Users/authored/cache\r\nprefix /Users/{{USER}}/data {{VALUE}} | {{HOME}}/work\r"
        "repeat {{VALUE}} {{HOME}}/work\n[plot](../output/figures/plot.png)\n"
    ).encode()
    authored = manuscript / "01_body.md"
    authored.write_bytes(source)
    values = {"USER": "zoë", "VALUE": "µm", "HOME": "/home/alice"}

    def render(_filename: str, text: str) -> str:
        substituted, unresolved = substitute_manuscript_text(text, values)
        assert not unresolved
        return _rebase_output_links_for_destination(substituted)

    hydrate_manuscript_tree(project, render)
    consumed = (project / "output/manuscript/01_body.md").read_bytes()
    expected = (
        "é <home>/cache\r\nprefix <home>/data µm | <home>/work\r"
        "repeat µm <home>/work\n[plot](../figures/plot.png)\n"
    ).encode()
    proof = require_shared_hydration(source, values, consumed, writer=SharedHydrationWriter.HYDRATED_UPPERCASE_TREE)
    assert authored.read_bytes() == source and proof.source == source and consumed == expected
    assert proof.data()["source_sha256"] == hashlib.sha256(source).hexdigest()
    prefixes = (
        "é <home>/cache\r\nprefix ",
        "é <home>/cache\r\nprefix <home>/data ",
        "é <home>/cache\r\nprefix <home>/data µm | ",
        "é <home>/cache\r\nprefix <home>/data µm | <home>/work\rrepeat ",
        "é <home>/cache\r\nprefix <home>/data µm | <home>/work\rrepeat µm ",
    )
    payloads = (b"<home>", "µm".encode(), b"<home>", "µm".encode(), b"<home>")
    for row, prefix, payload in zip(proof.occurrences, prefixes, payloads, strict=True):
        assert (row.output_start_byte, row.output_end_byte) == (len(prefix.encode()), len(prefix.encode()) + len(payload))
        assert expected[row.output_start_byte:row.output_end_byte] == payload
        assert row.replacement_sha256 == hashlib.sha256(payload).hexdigest()
        assert source[row.source_start_byte:row.source_end_byte] == ("{{" + row.key + "}}").encode()
    with pytest.raises(ValueError, match="differs from exact"):
        require_shared_hydration(source, values, consumed, writer=SharedHydrationWriter.RESOLVED_TREE)


def test_legacy_writer_keeps_home_bytes_and_converts_only_authored_newlines(tmp_path: Path) -> None:
    project = tmp_path / "project"
    manuscript = project / "manuscript"
    manuscript.mkdir(parents=True)
    source = "é /Users/authored/cache\r\n{{PATH}}\r[plot](../output/figures/plot.png)\n".encode()
    (manuscript / "01_body.md").write_bytes(source)
    values = {"PATH": "/home/generated/work\r\n"}
    output = write_resolved_manuscript_tree(project, values)
    consumed = (output / "01_body.md").read_bytes()
    expected = "é /Users/authored/cache\n/home/generated/work\r\n\n[plot](../figures/plot.png)\n".encode()
    proof = require_shared_hydration(source, values, consumed, writer=SharedHydrationWriter.RESOLVED_TREE)
    assert proof.output == expected and proof.source == source
    row, = proof.occurrences
    assert consumed[row.output_start_byte:row.output_end_byte] == values["PATH"].encode()
    with pytest.raises(ValueError, match="differs from exact"):
        require_shared_hydration(source, values, consumed, writer=SharedHydrationWriter.HYDRATED_UPPERCASE_TREE)


def test_raw_copy_normalization_keeps_utf8_newlines_and_exact_source_identity() -> None:
    source = "é /Users/alice/work\r\n/home/bob/data\r".encode()
    output = "é <home>/work\r\n<home>/data\r".encode()
    proof = require_shared_hydration(source, {}, output, writer=SharedHydrationWriter.HYDRATED_WORD_TREE)
    assert proof.source == source and not proof.occurrences
    assert proof.data()["source_sha256"] == hashlib.sha256(source).hexdigest()
    changed_source = source.replace(b"alice", b"another-author")
    changed = require_shared_hydration(changed_source, {}, output, writer=SharedHydrationWriter.HYDRATED_WORD_TREE)
    assert proof.output == changed.output and proof.data() != changed.data()


def test_normalization_crossing_both_token_boundaries_retains_every_raw_ordinal() -> None:
    source = "α /Users/{{FIRST}}{{LAST}}/data {{FIRST}}\r\n".encode()
    values = {"FIRST": "zo", "LAST": "ë"}
    output = "α <home>/data zo\r\n".encode()
    proof = require_shared_hydration(source, values, output, writer=SharedHydrationWriter.HYDRATED_UPPERCASE_TREE)
    first = len("α ".encode())
    assert [(row.ordinal, row.key) for row in proof.occurrences] == [(1, "FIRST"), (2, "LAST"), (3, "FIRST")]
    assert [(row.output_start_byte, row.output_end_byte) for row in proof.occurrences[:2]] == [(first, first + 6)] * 2
    for row in proof.occurrences:
        assert source[row.source_start_byte:row.source_end_byte] == ("{{" + row.key + "}}").encode()
        assert row.replacement_sha256 == hashlib.sha256(output[row.output_start_byte:row.output_end_byte]).hexdigest()
    selected = tuple((0, row.ordinal, row.key, row.output_start_byte, row.output_end_byte, row.replacement_sha256)
                     for row in proof.occurrences)
    with pytest.raises(ValueError, match="overlap"):
        annotate_manuscript_ordinals((output,), selected)


def test_normalization_cannot_hide_an_unresolved_token_or_promote_an_empty_replacement() -> None:
    source = b"/Users/{{MISSING}}/data"
    with pytest.raises(ValueError, match="unresolved"):
        require_shared_hydration(source, {}, b"<home>/data", writer=SharedHydrationWriter.HYDRATED_UPPERCASE_TREE)
    proof = require_shared_hydration(
        b"/Users/al{{EMPTY}}ice/data", {"EMPTY": ""}, b"<home>/data", writer=SharedHydrationWriter.HYDRATED_UPPERCASE_TREE
    )
    row, = proof.occurrences
    assert row.output_start_byte == row.output_end_byte == 0
    assert row.replacement_sha256 == hashlib.sha256(b"").hexdigest()


def test_source_writer_grammars_are_not_selected_by_equal_output_or_a_serialized_flag() -> None:
    source = "{{lower}} {{ÉTÉ}} {{UPPER}} {{with space}}\r\n".encode()
    values = {"lower": "one", "ÉTÉ": "été", "UPPER": "three"}
    proof = require_shared_hydration(
        source, values, "one été three {{with space}}\r\n".encode(), writer=SharedHydrationWriter.HYDRATED_WORD_TREE
    )
    assert [row.key for row in proof.occurrences] == ["lower", "ÉTÉ", "UPPER"]
    with pytest.raises(ValueError, match="differs from exact"):
        require_shared_hydration(source, values, proof.output, writer=SharedHydrationWriter.HYDRATED_UPPERCASE_TREE)
    with pytest.raises(ValueError, match="Source-selected writer"):
        require_shared_hydration(source, values, proof.output, writer={"normalize": True})


@pytest.mark.parametrize("consumed", [
    b"<home>/other 7 8", b"<home>/data -7 8", b"<home>/data 7", b"<home>/data 7 8 8", b"<home>/data 8 7",
])
def test_normalized_consumed_mutation_omission_and_duplication_still_refuse(consumed: bytes) -> None:
    with pytest.raises(ValueError, match="differs from exact"):
        require_shared_hydration(
            b"/Users/author/data {{FIRST}} {{SECOND}}", {"FIRST": "7", "SECOND": "8"}, consumed,
            writer=SharedHydrationWriter.HYDRATED_UPPERCASE_TREE,
        )


def test_normalized_offsets_reach_complete_html_and_shared_pdf_office_parser_bytes() -> None:
    source = "α /home/author/work {{VALUE}} then {{VALUE}}\r\n".encode()
    proof = reconstruct_shared_hydration(source, {"VALUE": "µm"}, writer=SharedHydrationWriter.HYDRATED_UPPERCASE_TREE)
    selected = tuple((0, row.ordinal, row.key, row.output_start_byte, row.output_end_byte, row.replacement_sha256)
                     for row in proof.occurrences)
    marked, anchors = annotate_manuscript_ordinals((proof.output,), selected)
    bodies = (proof.output,)
    pairs = (
        (compose_html_ordinal_input(marked, boundary_bodies=bodies), compose_html_ordinal_input(bodies)),
        (combine_held_manuscripts(marked, separator=""), combine_held_manuscripts(bodies, separator="")),
    )
    for annotated, original in pairs:
        spans = require_unannotated_parser_bytes(annotated, original, anchors)
        assert [original[first:last] for first, last in spans] == ["µm".encode(), "µm".encode()]
    altered = list(selected)
    altered[1] = (*altered[1][:-1], hashlib.sha256(b"changed").hexdigest())
    with pytest.raises(ValueError, match="genuine nonempty hydration"):
        annotate_manuscript_ordinals(bodies, tuple(altered))


def test_normalization_across_token_start_and_end_keeps_exact_resulting_intervals() -> None:
    source = b"{{ROOT}}/author/data; /Users/al{{MIDDLE}}ce/cache"
    output = b"<home>/data; <home>/cache"
    proof = require_shared_hydration(
        source, {"ROOT": "/home", "MIDDLE": "i"}, output, writer=SharedHydrationWriter.HYDRATED_UPPERCASE_TREE
    )
    assert [(row.output_start_byte, row.output_end_byte) for row in proof.occurrences] == [(0, 6), (13, 19)]
    for row in proof.occurrences:
        assert source[row.source_start_byte:row.source_end_byte] == ("{{" + row.key + "}}").encode()
        assert row.replacement_sha256 == hashlib.sha256(b"<home>").hexdigest()


def test_equal_normalized_output_cannot_rebind_original_authored_token_offsets_or_hash() -> None:
    source = "é /Users/alice/data {{VALUE}}\r\n".encode()
    changed_source = source.replace(b"alice", b"another-author")
    values = {"VALUE": "µm"}
    first = reconstruct_shared_hydration(source, values, writer=SharedHydrationWriter.HYDRATED_UPPERCASE_TREE)
    second = reconstruct_shared_hydration(changed_source, values, writer=SharedHydrationWriter.HYDRATED_UPPERCASE_TREE)
    assert first.output == second.output
    one, = first.occurrences
    two, = second.occurrences
    assert one.output_start_byte == two.output_start_byte and one.replacement_sha256 == two.replacement_sha256
    shift = len(b"another-author") - len(b"alice")
    assert (two.source_start_byte, two.source_end_byte) == (one.source_start_byte + shift, one.source_end_byte + shift)
    assert first.data()["source_sha256"] == hashlib.sha256(source).hexdigest()
    assert second.data()["source_sha256"] == hashlib.sha256(changed_source).hexdigest()
    assert first.data() != second.data()
