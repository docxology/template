"""Preserve all native source findings and unsupported obligations at admission."""

from __future__ import annotations

from typing import Any


def _outcome(value: object, *, source_observation: bool = False) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("native observer outcome must be an object")
    findings, blockers = value.get("findings"), value.get("blockers")
    if (
        not isinstance(findings, list)
        or any(
            not isinstance(item, dict) or not isinstance(item.get("code"), str) or not item["code"] for item in findings
        )
        or not isinstance(blockers, list)
        or any(not isinstance(item, str) or not item for item in blockers)
    ):
        raise ValueError("native observer findings/blockers are malformed")
    status = "fail" if findings else "blocked" if blockers else "pass"
    source_status = "failed" if findings else "blocked" if blockers else "observed"
    if value.get("status") != (source_status if source_observation else status):
        raise ValueError("native observer status conceals findings or unsupported obligations")
    return {"status": status, "findings": findings, "blockers": blockers}


def native_observer_outcome(observer: object) -> dict[str, Any]:
    """Combine EPUB spine and reader layout; unwrap Office layout explicitly."""
    if not isinstance(observer, dict) or observer.get("format") not in {"pdf", "html", "docx", "epub", "pptx", "png"}:
        raise ValueError("native observer format is absent or unsupported")
    if observer["format"] == "png" and (
        not isinstance(observer.get("print_reference"), dict) or set(observer["print_reference"]) != {"path", "sha256"}
    ):
        raise ValueError("native PNG outcome requires independently replayable configured print custody")
    result = observer.get("observation")
    if observer["format"] in {"docx", "epub"} and "office_complete_source" in observer:
        from infrastructure.reporting.native_office_full_observer import SCHEMA

        complete = observer["office_complete_source"]
        if (
            not isinstance(complete, dict)
            or complete.get("schema_version") != SCHEMA
            or result != complete.get("observation")
        ):
            raise ValueError("complete Office outcome differs from its source-owned observation schema")
        if observer["format"] == "epub" and observer.get("spine") != complete.get("spine"):
            raise ValueError("complete EPUB outcome omits or changes its original spine")
        outcome = _outcome(result, source_observation=True)
    elif observer["format"] in {"docx", "pptx"} and isinstance(result, dict) and "observation" in result:
        if set(result) != {"conversion", "raster", "observation", "status"}:
            raise ValueError("native Office layout wrapper is malformed")
        outcome = _outcome(result["observation"])
        if result["status"] != outcome["status"]:
            raise ValueError("native Office wrapper status differs from its actual layout")
    else:
        outcome = _outcome(result)
    if observer["format"] == "epub":
        spine = _outcome(observer.get("spine"))
        findings = [*spine["findings"], *outcome["findings"]]
        blockers = [*spine["blockers"], *outcome["blockers"]]
        return {
            "status": "fail" if findings else "blocked" if blockers else "pass",
            "findings": findings,
            "blockers": blockers,
        }
    if "manuscript_projection" in observer:
        complete = observer["manuscript_projection"]
        if not isinstance(complete, dict) or complete.get("observation") != observer["observation"]:
            raise ValueError("manuscript projection aggregate differs from full source observation")
    if "projection_contract" in observer and str(observer.get("id", "")).startswith("pitch:"):
        key = "source_package" if observer["format"] == "pptx" else "source_native_reference"
        companion = _outcome(observer.get(key))
        findings = [*outcome["findings"], *companion["findings"]]
        blockers = [*outcome["blockers"], *companion["blockers"]]
        return {
            "status": "fail" if findings else "blocked" if blockers else "pass",
            "findings": findings,
            "blockers": blockers,
        }
    return outcome
