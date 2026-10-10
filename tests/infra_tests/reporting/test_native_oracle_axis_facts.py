"""Real-file census and missing-witness boundaries; no native owner is minted."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_oracle_axis_facts import (
    _component,
    _pages,
    _pdf_current,
    _pdf_witness,
    _office_mermaid_reference,
    ordered_source_inputs,
)


def test_ordered_inputs_keep_exact_file_bytes_order_and_changed_digest(tmp_path: Path) -> None:
    first = tmp_path / "01_intro.md"
    second = tmp_path / "02_methods.md"
    first.write_bytes("α\r\nRepeated α\r\n".encode())
    second.write_bytes(b"methods\r\n")
    rows = [{"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in (first, second)]
    held = ordered_source_inputs(rows)
    assert held == tuple((row["path"], row["sha256"]) for row in rows)
    assert ordered_source_inputs(list(reversed(rows))) != held
    first.write_bytes(first.read_bytes().replace(b"\r\n", b"\n"))
    changed = [{"path": first.name, "sha256": hashlib.sha256(first.read_bytes()).hexdigest()}, rows[1]]
    assert ordered_source_inputs(changed) != held


@pytest.mark.parametrize(
    "value",
    [
        None,
        [],
        [{"path": "a.md", "sha256": "0" * 64}, {"path": "a.md", "sha256": "1" * 64}],
        [{"path": "/a.md", "sha256": "0" * 64}],
        [{"path": "../a.md", "sha256": "0" * 64}],
        [{"path": "a/../b.md", "sha256": "0" * 64}],
        [{"path": "a.md", "sha256": "G" * 64}],
        [{"path": "a.md", "sha256": "0" * 63}],
    ],
)
def test_missing_duplicate_escaping_or_invalid_census_refuses(value: object) -> None:
    assert ordered_source_inputs(value) is None


def test_declared_pass_or_empty_aggregate_supplies_no_component_witness() -> None:
    label = "actual Source witness"
    required = ("source_ast_sha256", "occurrences")
    for unproven in ({}, {"status": "pass"}, {"status": "pass", "findings": [], "blockers": []}):
        assert _component(unproven, label, required) == (label + ": complete actual component witness is unavailable",)
    with pytest.raises(ValueError, match="still has findings"):
        _component({"findings": ["changed byte"]}, label, required)


def test_all_page_comparison_needs_nonempty_ordered_roster_and_preserves_failures() -> None:
    label = "actual pages"
    empty = {"findings": [], "blockers": [], "reference_pages": [], "candidate_pages": []}
    assert _pages(empty, label) == (label + ": every actual native page is required",)
    pages = [{"page": 1, "sha256": "0" * 64}, {"page": 2, "sha256": "1" * 64}]
    data = {"findings": [], "blockers": ["unresolved font use"], "reference_pages": pages, "candidate_pages": pages}
    assert _pages(data, label) == ("unresolved font use",)
    with pytest.raises(ValueError, match="changed/omitted/reordered"):
        _pages({**data, "candidate_pages": list(reversed(pages))}, label)
    with pytest.raises(ValueError, match="still has findings"):
        _pages({**data, "findings": ["actual unequal page"]}, label)


def _plan_and_witness(tmp_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    source = tmp_path / "plain.md"
    source.write_bytes("Plain α\r\n".encode())
    plan = {
        "schema_version": "template-native-pdf-semantic-source-plan-v1",
        "artifact_id": "manuscript:pdf",
        "source_ast_sha256": "0" * 64,
        "sources": [[source.name, hashlib.sha256(source.read_bytes()).hexdigest()]],
        "text": [],
        "notes": [],
        "occurrences": [],
        "tables": [],
        "literal_members": [],
        "blockers": [],
    }
    witness = {
        "source_plan_digest": canonical_digest(plan),
        "literal": {},
        "tables": {},
        "figures": {},
        "pagebreaks": {},
        "notes": None,
        "citations": None,
        "equations": None,
        "findings": [],
        "blockers": [],
    }
    return plan, witness


def test_optional_pdf_none_needs_complete_unchanged_source_absence(tmp_path: Path) -> None:
    plan, witness = _plan_and_witness(tmp_path)
    assert _pdf_witness(witness, plan, "actual PDF") == ()
    assert _pdf_witness(witness, {}, "actual PDF") == (
        "actual PDF: complete exact Source semantic plan is unavailable",
    )
    assert _pdf_witness({key: value for key, value in witness.items() if key != "citations"}, plan, "actual PDF") == (
        "actual PDF: selected/required citations witness is unavailable",
    )
    with pytest.raises(ValueError, match="changed its complete Source semantic plan"):
        _pdf_witness(witness, {**plan, "notes": [{"text": "new selected note"}]}, "actual PDF")


@pytest.mark.parametrize("kind", ["Cite", "Math", "RawInline"])
def test_selected_pdf_node_needs_its_actual_witness_and_keeps_blockers(tmp_path: Path, kind: str) -> None:
    plan, witness = _plan_and_witness(tmp_path)
    row: dict[str, Any] = {"kind": kind}
    if kind == "RawInline":
        row["raw_citation_reference_ids"] = ["raw-citation-1"]
    plan["occurrences"] = [row]
    plan["blockers"] = ["actual selected semantic position is unresolved"]
    witness["source_plan_digest"] = canonical_digest(plan)
    reasons = _pdf_witness(witness, plan, "actual PDF")
    assert "actual selected semantic position is unresolved" in reasons
    assert any("selected/required " + ("equations" if kind == "Math" else "citations") in reason for reason in reasons)


def test_current_pdf_absent_parity_cannot_use_original_reference_reproduction(tmp_path: Path) -> None:
    plan, witness = _plan_and_witness(tmp_path)
    current = {
        "scientific_pdf_source": {"semantic_plan": plan, "witness": witness},
        "current_reproduction": {"candidate_current_every_page_parity": {"pages": [{"page": 1}], "findings": []}},
    }
    axes = _pdf_current(current)
    assert axes[0] == ()
    assert "PDF fresh Current Core output full-page glyph/vector/ink parity is unavailable" in axes[1]
    assert any("independent Source reference" in reason for reason in axes[2])


def test_selected_office_mermaid_keeps_its_distinct_reference_role_residuals() -> None:
    remaining = [
        "actual Source-only Node/Chrome library custody is unresolved",
        "actual unclipped Source SVG ink is unresolved",
    ]
    observer = {
        "office_complete_source": {
            "reference": {"source": {"mermaid": {"reference": {"remaining_admission": remaining}}}}
        }
    }
    assert _office_mermaid_reference(observer) == tuple(remaining)
    assert _office_mermaid_reference({}) == (
        "Office selected Source-only Mermaid reference obligations are unavailable",
    )
    with pytest.raises(ValueError, match="explicit residual roster"):
        _office_mermaid_reference(
            {
                "office_complete_source": {
                    "reference": {"source": {"mermaid": {"reference": {"remaining_admission": [None]}}}}
                }
            }
        )


@pytest.mark.parametrize(
    "failure", ["none", "empty-pages", "missing-reference", "finding", "source-drift", "unresolved"]
)
def test_current_whole_pdf_adjunct_requires_real_complete_fields_and_keeps_residuals(
    tmp_path: Path, failure: str
) -> None:
    # This tests only the DATA interpreter; it cannot create a native owner or
    # claim that the producer/reference/OS qualification has actually executed.
    plan, base = _plan_and_witness(tmp_path)
    complete = {
        **base,
        "whole_page_parity": {"findings": [], "pages": [{"page": 1}]},
        "source_reference_literal": {
            "findings": [],
            "pdf_sha256": "1" * 64,
            "raster_sha256": ["2" * 64],
            "contract_digest": "3" * 64,
            "pages": [{"page": 1}],
            "matches": [],
        },
        "source_reference_figures": {"findings": [], "figures": []},
    }
    blockers = []
    if failure == "empty-pages":
        complete["whole_page_parity"]["pages"] = []
    elif failure == "missing-reference":
        complete["source_reference_literal"] = None
    elif failure == "finding":
        complete["whole_page_parity"]["findings"] = [{"code": "pdf.reference.glyphs"}]
    elif failure == "source-drift":
        complete["source_plan_digest"] = "f" * 64
    elif failure == "unresolved":
        blockers = ["actual selected source figure input remains unresolved"]
    current = {
        "scientific_pdf_source": {"semantic_plan": plan, "witness": base},
        "current_whole_pdf": {
            "source_predicates": {
                "source_plan": plan,
                "assets": {},
                "witness": complete,
                "findings": [],
                "blockers": [],
            },
            "blockers": blockers,
        },
    }
    if failure in {"finding", "source-drift"}:
        with pytest.raises(ValueError):
            _pdf_current(current)
        return
    axes = _pdf_current(current)
    if failure == "none":
        assert axes == ((), (), ())
    elif failure == "empty-pages":
        assert any("full-page glyph/vector/ink parity is unavailable" in row for row in axes[1])
    elif failure == "missing-reference":
        assert any("independent Source reference literal" in row for row in axes[2])
    else:
        assert all(blockers[0] in axis for axis in axes)


def test_current_whole_pdf_refusal_retains_base_witness_without_original_parity(tmp_path: Path) -> None:
    plan, witness = _plan_and_witness(tmp_path)
    current = {
        "scientific_pdf_source": {"semantic_plan": plan, "witness": witness},
        "current_whole_pdf": {"source_predicates": None, "blockers": ["selected Mermaid inputs unresolved"]},
        "current_reproduction": {"candidate_current_every_page_parity": {"pages": [{"page": 1}], "findings": []}},
    }
    axes = _pdf_current(current)
    assert all("selected Mermaid inputs unresolved" in axis for axis in axes)
    assert any("full-page glyph/vector/ink parity is unavailable" in row for row in axes[1])


def test_current_whole_pdf_preserves_aggregate_only_control_residuals(tmp_path: Path) -> None:
    # Complete interpreter fields are DATA, not native Source/process authority.
    plan, base = _plan_and_witness(tmp_path)
    witness = {
        **base,
        "whole_page_parity": {"findings": [], "pages": [{"page": 1}]},
        "source_reference_literal": {
            "findings": [],
            "pdf_sha256": "1" * 64,
            "raster_sha256": ["2" * 64],
            "contract_digest": "3" * 64,
            "pages": [{"page": 1}],
            "matches": [],
        },
        "source_reference_figures": {"findings": [], "figures": []},
    }
    remaining = [
        "fixed SDK original whole-PDF child supervisor and actual signed OS results",
        "independently current complete Source/native control predicate replay",
    ]
    current = {
        "scientific_pdf_source": {"semantic_plan": plan, "witness": base},
        "current_whole_pdf": {
            "source_predicates": {
                "source_plan": plan,
                "assets": {},
                "witness": witness,
                "findings": [],
                "blockers": remaining,
                "control_requirements": {"remaining": remaining},
            },
            "blockers": [],
        },
    }
    axes = _pdf_current(current)
    assert axes == (tuple(remaining), tuple(remaining), tuple(remaining))
    current["current_whole_pdf"]["source_predicates"]["blockers"] = None
    with pytest.raises(ValueError, match="explicit residuals"):
        _pdf_current(current)
