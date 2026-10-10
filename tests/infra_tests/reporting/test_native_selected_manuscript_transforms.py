"""Deterministic real-file transforms; no Native original/admission is minted."""

from __future__ import annotations

import base64
import hashlib
import time
from pathlib import Path

import pytest

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.rendering._pdf_mermaid import _MERMAID_BLOCK_RE, _normalise_mermaid_source, _source_hash
from infrastructure.reporting.native_selected_manuscript_transforms import (
    reconstruct_inline_mermaid_source,
    reconstruct_project_authored_hydration,
    reconstruct_transmission_bookend,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

# Actual decodable 1x1 PNG bytes are a fixture. A successful textual predicate
# makes no claim that this fixture was rendered by a genuine Mermaid process.
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jIYkAAAAASUVORK5CYII=")


def _assert_custom_output_spans(graph: dict[str, object], output: bytes, payloads: list[bytes]) -> None:
    assert graph["output_mapping_complete"] is True
    assert graph["output_mapping_blockers"] == []
    rows = graph["occurrences"]
    assert isinstance(rows, list) and len(rows) == len(payloads)
    end = 0
    for ordinal, (row, payload) in enumerate(zip(rows, payloads, strict=True), 1):
        assert row["ordinal"] == ordinal
        assert end <= row["output_start_byte"] <= row["output_end_byte"] <= len(output)
        assert output[row["output_start_byte"] : row["output_end_byte"]] == payload
        assert row["replacement_sha256"] == hashlib.sha256(payload).hexdigest()
        end = row["output_end_byte"]


@pytest.mark.parametrize(
    ("scope", "source", "values", "expected", "payloads"),
    [
        (
            "templates/template_active_inference",
            "π {{rate:.2f}}\r\n{{enabled}}|{{empty}}|{{link}}\r\n".encode(),
            {"rate": 1.23456, "enabled": True, "empty": None, "link": "[x](../output/data/a.json)"},
            "π 1.23\ntrue||[x](../data/a.json)\n".encode(),
            [b"1.23", b"true", b"", b"[x](../data/a.json)"],
        ),
        (
            "templates/template_template",
            "π ${run_count}\r\n${run_items}|$$|${empty}\r\n".encode(),
            {"run": {"count": 4, "items": ["a", "b"]}, "empty": None},
            "π 4\n2|$|\n".encode(),
            [b"4", b"2", b"$", b""],
        ),
    ],
)
def test_custom_output_spans_follow_unicode_newlines_empty_and_actual_formatters(
    scope: str, source: bytes, values: dict[str, object], expected: bytes, payloads: list[bytes]
) -> None:
    result = reconstruct_project_authored_hydration(scope, source, values)
    assert result is not None and result[0] == expected
    _assert_custom_output_spans(result[1], result[0], payloads)


def _search_mapping_values(query: str) -> dict[str, object]:
    return {
        "config_query": query,
        "config_max_results": "",
        "config_sources": "",
        "result_num_papers": 7,
        "result_num_sources": "",
        "result_per_source": "",
        "result_errors": "",
        "result_year_min": "",
        "result_year_max": "",
        "result_with_abstract": "",
        "result_with_doi": "",
        "deep_max_results_per_keyword": "",
        "deep_keyword_count": "",
        "deep_keywords_joined": "",
        "deep_sources": "",
        "deep_unique_papers": "",
    }


def test_search_output_spans_follow_ordered_nested_and_repeated_authored_markers() -> None:
    source = "λ {{CONFIG_QUERY}} / {{RESULT_NUM_PAPERS}} / {{CONFIG_QUERY}}\r\n".encode()
    result = reconstruct_project_authored_hydration(
        "templates/template_search_project", source, _search_mapping_values("a{{RESULT_NUM_PAPERS}}b")
    )
    assert result is not None and result[0] == "λ a7b / 7 / a7b\r\n".encode()
    _assert_custom_output_spans(result[1], result[0], [b"a7b", b"7", b"a7b"])


def test_search_intermediate_expansion_preserves_existing_authored_occurrence_ceiling() -> None:
    query = "{{RESULT_NUM_PAPERS}}" * 10001
    result = reconstruct_project_authored_hydration(
        "templates/template_search_project", b"{{CONFIG_QUERY}}", _search_mapping_values(query)
    )
    assert result is not None and result[0] == b"7" * 10001
    _assert_custom_output_spans(result[1], result[0], [result[0]])


@pytest.mark.parametrize(
    ("scope", "source", "values", "expected"),
    [
        (
            "templates/template_search_project",
            b"{{CONFIG_QUERY}}NUM_PAPERS}}",
            _search_mapping_values("{{RESULT_"),
            b"7",
        ),
        (
            "templates/template_active_inference",
            b"[x]({{link}})",
            {"link": "../output/data/a.json"},
            b"[x](../data/a.json)",
        ),
    ],
)
def test_custom_cross_boundary_substitution_preserves_output_and_precise_mapping_residual(
    scope: str, source: bytes, values: dict[str, object], expected: bytes
) -> None:
    result = reconstruct_project_authored_hydration(scope, source, values)
    assert result is not None and result[0] == expected
    graph = result[1]
    assert graph["output_mapping_complete"] is False
    assert graph["output_mapping_blockers"] == [
        {"ordinal": 1, "reason": "later Source substitution crosses authored token boundary"}
    ]
    row = graph["occurrences"][0]
    assert row["output_start_byte"] is None
    assert row["output_end_byte"] is None
    assert row["replacement_sha256"] is None


def test_active_inference_complete_precision_links_and_newlines() -> None:
    raw = b"Rate {{rate:.2f}} {{enabled}} {{missing_value}}\r\n[x](../output/data/a.json)\r\n"
    result = reconstruct_project_authored_hydration(
        "templates/template_active_inference", raw, {"rate": 1.23456, "enabled": True, "missing_value": None}
    )
    assert result is not None
    assert result[0] == b"Rate 1.23 true \n[x](../data/a.json)\n"
    assert [row["key"] for row in result[1]["occurrences"]] == ["rate", "enabled", "missing_value"]
    with pytest.raises(ValueError, match="unresolved"):
        reconstruct_project_authored_hydration("templates/template_active_inference", raw, {"rate": 1.23})
    with pytest.raises(ValueError, match="malformed"):
        reconstruct_project_authored_hydration("templates/template_active_inference", b"A {rate}", {"rate": 1})


def test_template_metrics_preserves_dollars_math_and_nested_list_lengths() -> None:
    result = reconstruct_project_authored_hydration(
        "templates/template_template",
        b"${run_count} ${run_items} $$ ${empty}\r\n${(x+y)}\n",
        {"run": {"count": 4, "items": ["a", "b"]}, "empty": None},
    )
    assert result is not None
    assert result[0] == b"4 2 $ \n${(x+y)}\n"
    with pytest.raises(ValueError, match="unresolved"):
        reconstruct_project_authored_hydration("templates/template_template", b"${missing}", {})
    assert reconstruct_project_authored_hydration("templates/template_code_project", b"plain", {}) is None


def test_search_keeps_typed_full_dataclass_fields_and_repeated_markers(tmp_path: Path) -> None:
    fields = (
        "config_query",
        "config_max_results",
        "config_sources",
        "result_num_papers",
        "result_num_sources",
        "result_per_source",
        "result_errors",
        "result_year_min",
        "result_year_max",
        "result_with_abstract",
        "result_with_doi",
        "deep_max_results_per_keyword",
        "deep_keyword_count",
        "deep_keywords_joined",
        "deep_sources",
        "deep_unique_papers",
    )
    variables: dict[str, object] = {name: "" for name in fields}
    variables.update(config_query="graph", result_num_papers=7)
    result = reconstruct_project_authored_hydration(
        "templates/template_search_project", b"{{RESULT_NUM_PAPERS}} {{CONFIG_QUERY}} {{RESULT_NUM_PAPERS}}", variables
    )
    assert result is not None and result[0] == b"7 graph 7"
    assert [row["key"] for row in result[1]["occurrences"]] == [
        "RESULT_NUM_PAPERS",
        "CONFIG_QUERY",
        "RESULT_NUM_PAPERS",
    ]
    # The actual Search writer decodes confined raw bytes; unlike the two
    # read_text writers it preserves both CRLF and isolated CR exactly.
    source_path = tmp_path / "authored.md"
    source_path.write_bytes(b"Before\r\n{{RESULT_NUM_PAPERS}}\r{{CONFIG_QUERY}}\r\nAfter\r\n")
    raw = read_bytes_confined(tmp_path, source_path)
    crlf = reconstruct_project_authored_hydration("templates/template_search_project", raw, variables)
    assert crlf is not None and crlf[0] == b"Before\r\n7\rgraph\r\nAfter\r\n"
    assert (
        raw[crlf[1]["occurrences"][0]["source_start_byte"] : crlf[1]["occurrences"][0]["source_end_byte"]]
        == b"{{RESULT_NUM_PAPERS}}"
    )
    variables.pop("result_errors")
    with pytest.raises(ValueError, match="complete Source"):
        reconstruct_project_authored_hydration("templates/template_search_project", b"text", variables)


def test_bookend_real_file_config_pending_state_and_disabled_refusal(tmp_path: Path) -> None:
    project = tmp_path / "projects/templates/template_code_project"
    config = project / "manuscript/config.yaml"
    config.parent.mkdir(parents=True)
    config.write_text(
        "paper:\n  title: Example\n  version: '2.1'\npublication:\n  transmission_bookends:\n    enabled: true\n"
    )
    reader = SnapshotReader(tmp_path)
    held = reader.read(config.relative_to(tmp_path).as_posix())
    begin, begin_graph = reconstruct_transmission_bookend(held, None, "00_00_transmission_begin.md")
    end, end_graph = reconstruct_transmission_bookend(held, None, "99_zz_transmission_end.md")
    assert b"BEGINNING OF TRANSMISSION" in begin and b"END OF TRANSMISSION" in end
    assert b"unpublished / pending pairing" in begin and b"2.1" in begin
    assert begin_graph["boundary"] == "begin" and end_graph["boundary"] == "end"
    ledger_path = project / "output/data/publication_ledger.json"
    ledger_path.parent.mkdir(parents=True)
    ledger_path.write_text('{"schema":"template-publication-ledger-v1","releases":[]}')
    ledger = reader.read(ledger_path.relative_to(tmp_path).as_posix())
    empty_body, empty_graph = reconstruct_transmission_bookend(held, ledger, "00_00_transmission_begin.md")
    assert empty_body == begin
    assert empty_graph["ledger"] == {"path": ledger.relative, "sha256": ledger.sha256, "bytes": len(ledger.content)}
    assert reader.unchanged()
    config.write_text(config.read_text().replace("enabled: true", "enabled: 'false'"))
    assert not reader.unchanged()
    with pytest.raises(ValueError, match="disabled"):
        reconstruct_transmission_bookend(
            SnapshotReader(tmp_path).read(config.relative_to(tmp_path).as_posix()), None, "00_00_transmission_begin.md"
        )


def _held_mermaid_files(root: Path, source: bytes) -> None:
    directory = root / "projects/templates/template_code_project/output/figures/mermaid_inline"
    directory.mkdir(parents=True)
    for ordinal, match in enumerate(_MERMAID_BLOCK_RE.finditer(source.decode()), 1):
        normal = _normalise_mermaid_source(match.group("source").strip())
        stem = f"inline_mermaid_{ordinal:04d}_{_source_hash(normal)}"
        (directory / f"{stem}.mmd").write_text(normal + "\n")
        (directory / f"{stem}.png").write_bytes(PNG)


def test_repeated_mermaid_fences_keep_every_asset_and_replacement(tmp_path: Path) -> None:
    source = b"Before\n```mermaid\ngraph TD\nA-->B\n```\n\nBetween\n```mermaid\ngraph TD\nA-->B\n```\nAfter\n"
    _held_mermaid_files(tmp_path, source)
    body, rows, gaps = reconstruct_inline_mermaid_source(
        source, "templates/template_code_project", SnapshotReader(tmp_path), deadline=time.monotonic() + 20
    )
    assert body is not None and b"```mermaid" not in body
    assert len(rows) == 2 and rows[0]["production_stem"] != rows[1]["production_stem"]
    assert body.count(b"\\includegraphics") == 2
    assert b"Before" in body and b"Between" in body and b"After" in body
    assert gaps == ["actual-inline-mermaid-render-cache-origin-and-consuming-native-asset-lineage"]
    Path(tmp_path / rows[1]["source"]["path"]).write_text("changed\n")
    with pytest.raises(ValueError, match="normalization"):
        reconstruct_inline_mermaid_source(
            source, "templates/template_code_project", SnapshotReader(tmp_path), deadline=time.monotonic() + 20
        )


def test_absent_mermaid_asset_and_absent_diagram_are_distinct(tmp_path: Path) -> None:
    source = b"```mermaid\ngraph TD\nA-->B\n```\n"
    body, rows, gaps = reconstruct_inline_mermaid_source(
        source, "templates/template_code_project", SnapshotReader(tmp_path), deadline=time.monotonic() + 20
    )
    assert body is None and len(rows) == 1 and len(gaps) == 1
    plain, rows, gaps = reconstruct_inline_mermaid_source(
        b"No diagram", "templates/template_code_project", SnapshotReader(tmp_path), deadline=time.monotonic() + 20
    )
    assert plain == b"No diagram" and rows == [] and gaps == []
