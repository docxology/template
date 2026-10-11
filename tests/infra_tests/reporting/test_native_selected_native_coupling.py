"""Exact bounded selected projection cases; DATA never supplies native custody."""

from __future__ import annotations

import copy
from typing import Any

import pytest

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_oracle_selected_lineage import (
    classify_selected_native_lineage,
    selected_asset_lineage_residuals,
)

PROJECT = "projects/templates/template_code_project"


def _binding(path: str, digest: str = "a") -> dict[str, Any]:
    return {"path": path, "sha256": digest * 64, "bytes": 100}


def _seal(body: dict[str, Any]) -> dict[str, Any]:
    body.pop("content_digest", None)
    return {**body, "content_digest": canonical_digest(body)}


def _graphs() -> tuple[dict[str, Any], dict[str, Any]]:
    common = {
        "scope": "templates/template_code_project",
        "source_binding": ["b" * 40, "c" * 64],
        "pipeline_run_id": "actual-checked-DATA",
        "plan_digest": "d" * 64,
    }
    source = _binding(PROJECT + "/manuscript/01.md")
    return _seal(
        {
            **common,
            "schema_version": "template-native-analysis-boundary-graph-v3",
            "unresolved_edges": [],
            "produced_current_bodies": [],
        }
    ), _seal(
        {
            **common,
            "schema_version": "template-native-hydration-reconstruction-v3",
            "unresolved_edges": [],
            "ordered_inputs": [
                {"ordinal": 1, "source": source, "consumed": source, "transformation": "exact-authored-source-body"}
            ],
        }
    )


def _bookend() -> tuple[dict[str, Any], dict[str, Any]]:
    analysis, hydration = _graphs()
    body = _binding(PROJECT + "/output/manuscript/00_00_transmission_begin.md")
    hydration["ordered_inputs"] = [
        {
            "ordinal": 1,
            "consumed": body,
            "transformation": "Source-generated-transmission-boundary",
            "bookend": {
                "algorithm": "Source-transmission-config-ledger-context-and-boundary-v1",
                "config": _binding(PROJECT + "/manuscript/config.yaml"),
                "ledger": None,
                "boundary": "begin",
                "output_sha256": body["sha256"],
                "publication_history_is_data": True,
            },
        }
    ]
    hydration["unresolved_edges"] = [
        "generated-transmission-figure-integrity-strip-and-publication-history-authority:" + body["path"]
    ]
    return analysis, _seal(hydration)


def test_reconstructed_bookend_text_closes_only_its_text_role() -> None:
    analysis, hydration = _bookend()
    result = classify_selected_native_lineage(analysis, hydration)
    assert result["residuals"] == hydration["unresolved_edges"]


@pytest.mark.parametrize("change", ["foreign-path", "boundary", "history", "config", "digest"])
def test_bookend_wrong_exact_source_binding_cannot_close_text(change: str) -> None:
    analysis, hydration = _bookend()
    row = hydration["ordered_inputs"][0]
    if change == "foreign-path":
        row["consumed"]["path"] = "unrelated/00_00_transmission_begin.md"
    elif change == "boundary":
        row["bookend"]["boundary"] = "end"
    elif change == "history":
        row["bookend"]["publication_history_is_data"] = False
    elif change == "config":
        row["bookend"]["config"]["path"] = "foreign/config.yaml"
    else:
        row["bookend"]["output_sha256"] = "e" * 64
    with pytest.raises(ValueError):
        classify_selected_native_lineage(analysis, _seal(hydration))


def test_exact_figure_domain_alias_needs_actual_native_qualification() -> None:
    analysis, hydration = _graphs()
    body = _binding(PROJECT + "/output/figures/science.png")
    analysis["produced_current_bodies"] = [{"producer_stage": "analysis", "body": body}]
    analysis = _seal(analysis)
    asset = {key: body[key] for key in ("path", "sha256")}
    domains = _seal(
        {
            "source_binding": analysis["source_binding"],
            "pipeline_run_id": analysis["pipeline_run_id"],
            "analysis_digest": analysis["content_digest"],
            "residuals": [],
            "figures": [
                {"png": body, "selected_occurrences": [{"identity": "manuscript:pdf:blocks/0/c/0", "asset": asset}]}
            ],
        }
    )
    facts = classify_selected_native_lineage(analysis, hydration, figure_domains=domains)
    plan = {
        "schema_version": "template-native-pdf-semantic-source-plan-v1",
        "occurrences": [{"identity": "blocks/0/c/0", "kind": "Image"}],
    }
    pdf = {
        "source_predicates": {
            "assets": {"blocks/0/c/0": asset},
            "source_plan": plan,
            "witness": {"source_plan_digest": canonical_digest(plan)},
        }
    }
    assert selected_asset_lineage_residuals(facts, "manuscript:pdf", {}, pdf=pdf)
    assert selected_asset_lineage_residuals(facts, "manuscript:pdf", {}, pdf=pdf, native_qualified=True) == ()
    changed = copy.deepcopy(facts)
    changed["code_figure_domains"]["figures"][0]["selected_occurrences"][0]["identity"] = "different:blocks/0/c/0"
    assert selected_asset_lineage_residuals(changed, "manuscript:pdf", {}, pdf=pdf, native_qualified=True)


def test_figure_model_unknown_selected_domain_residual_stays_in_scope_facts() -> None:
    analysis, hydration = _graphs()
    domains = _seal(
        {
            "source_binding": analysis["source_binding"],
            "pipeline_run_id": analysis["pipeline_run_id"],
            "analysis_digest": analysis["content_digest"],
            "residuals": ["actual-unknown-selected-figure-domain"],
            "figures": [],
        }
    )
    assert (
        classify_selected_native_lineage(analysis, hydration, figure_domains=domains)["residuals"]
        == domains["residuals"]
    )
