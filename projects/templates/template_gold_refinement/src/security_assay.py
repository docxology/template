from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class SecurityAssayRecord:
    """Data container for SecurityAssayRecord."""

    assay_id: str
    threat: str
    standard: str
    evidence_surface: str
    validator: str
    claim_boundary: str

    def as_dict(self) -> dict[str, str]:
        """Process as dict."""
        return asdict(self)


def build_security_assay(config: Any) -> tuple[SecurityAssayRecord, ...]:
    """Build security assay."""
    rows = getattr(config, "security_assay", [])
    if not isinstance(rows, list):
        return ()

    records: list[SecurityAssayRecord] = []
    for index, item in enumerate((row for row in rows if isinstance(row, dict)), start=1):
        records.append(
            SecurityAssayRecord(
                assay_id=f"S{index}",
                threat=str(item.get("threat", "")),
                standard=str(item.get("standard", "")),
                evidence_surface=str(item.get("evidence_surface", "")),
                validator=str(item.get("validator", "")),
                claim_boundary=str(item.get("claim_boundary", "")),
            )
        )
    return tuple(records)


def security_assay_table_rows(records: tuple[SecurityAssayRecord, ...]) -> str:
    """Process security assay table rows."""
    if not records:
        return "| not configured | not configured | not configured | not configured | not configured | not configured |"
    return "\n".join(
        "| "
        f"{item.assay_id} | {item.threat} | {item.standard} | {item.evidence_surface} | "
        f"{item.validator} | {item.claim_boundary} |"
        for item in records
    )


def security_assay_summary_line(records: tuple[SecurityAssayRecord, ...]) -> str:
    """Process security assay summary line."""
    if not records:
        return "0 adversarial assay rows are configured; no security-scope claim should be made."
    return (
        f"{len(records)} adversarial assay rows mapping threats and standards to local evidence surfaces, "
        "validators, and claim boundaries; they are scope controls, not completed scan findings."
    )


def security_assay_records(records: tuple[SecurityAssayRecord, ...]) -> list[dict[str, str]]:
    """Process security assay records."""
    return [item.as_dict() for item in records]


__all__ = [
    "SecurityAssayRecord",
    "build_security_assay",
    "security_assay_records",
    "security_assay_summary_line",
    "security_assay_table_rows",
]
