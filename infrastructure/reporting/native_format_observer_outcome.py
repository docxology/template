"""Preserve all native source findings and unsupported obligations at admission."""

from __future__ import annotations

from typing import Any


def _outcome(value: object) -> dict[str, Any]:
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
    if value.get("status") != status:
        raise ValueError("native observer status conceals findings or unsupported obligations")
    return {"status": status, "findings": findings, "blockers": blockers}


def native_observer_outcome(observer: object) -> dict[str, Any]:
    """Combine EPUB spine and reader layout; unwrap Office layout explicitly."""
    if not isinstance(observer, dict) or observer.get("format") not in {"pdf", "html", "docx", "epub", "pptx"}:
        raise ValueError("native observer format is absent or unsupported")
    result = observer.get("observation")
    if observer["format"] in {"docx", "pptx"} and isinstance(result, dict) and "observation" in result:
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
    return outcome
