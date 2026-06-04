"""Security review markdown renderer."""

from __future__ import annotations

from src.json_coerce import mapping, mapping_list


def render_security_review_markdown(
    profile: dict[str, object],
    threat_model: dict[str, object],
    inventory: dict[str, object],
    attestation: dict[str, object],
) -> str:
    """Render the generated security review packet."""
    summary = mapping(threat_model.get("summary"))
    lines = [
        "# AutoResearch Security Review",
        "",
        "## Scope",
        "",
        f"- Mode: `{profile.get('mode')}`",
        f"- Network policy: `{profile.get('network_policy')}`",
        f"- Integrity algorithm: `{profile.get('integrity_algorithm')}`",
        f"- External signing: `{str(profile.get('external_signing')).lower()}`",
        f"- Claim scope: {profile.get('claim_scope')}",
        "",
        "## Threat Model Summary",
        "",
        f"- Assets: `{summary.get('asset_count')}`",
        f"- Threats: `{summary.get('threat_count')}`",
        f"- Controls: `{summary.get('control_count')}`",
        "",
        "## Integrity Attestation",
        "",
        f"- Status: `{attestation.get('status')}`",
        f"- Checked files: `{attestation.get('checked_count')}`",
        f"- Missing files: `{attestation.get('missing_count')}`",
        f"- Checksum mismatches: `{attestation.get('mismatch_count')}`",
        "- External signature: `false`",
        "",
        "## Inventory Summary",
        "",
        f"- Input records: `{len(mapping_list(inventory.get('inputs')))}`",
        f"- Generated artifact records: `{len(mapping_list(inventory.get('generated_artifacts')))}`",
        "",
        "## Non-Claims",
        "",
    ]
    non_claims = profile.get("non_claims", [])
    if not isinstance(non_claims, list):
        non_claims = []
    lines.extend(f"- {item}" for item in non_claims if isinstance(item, str))
    lines.extend(
        (
            "",
            "## Review Prompt",
            "",
            "A human reviewer should confirm that the local checksum, inventory, and threat-model "
            "evidence is sufficient for the manuscript's limited security claims before publication.",
            "",
        )
    )
    return "\n".join(lines)
