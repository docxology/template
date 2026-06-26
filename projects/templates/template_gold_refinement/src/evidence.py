"""Evidence registry for the gold-refinement exemplar.

Cross-checks every contribution claim against its evidence source and
builds a machine-readable evidence registry. This is the "assaying" stage
operationalized: each claim is tested against evidence before the
manuscript is allowed to render.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

try:
    from .config import GoldRefinementConfig
except ImportError:  # pragma: no cover
    from config import GoldRefinementConfig  # type: ignore[no-redef]

import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EvidenceEntry:
    """One evidence entry: a claim and its supporting evidence."""

    claim_name: str
    claim_statement: str
    evidence_source: str
    boundary: str
    supported: bool
    notes: str = ""

    def as_dict(self) -> dict[str, str | bool]:
        return asdict(self)


@dataclass
class EvidenceRegistry:
    """Full evidence registry across all claims."""

    entries: list[EvidenceEntry] = field(default_factory=list)
    total_claims: int = 0
    supported_claims: int = 0
    unsupported_claims: int = 0

    @property
    def support_rate(self) -> float:
        if self.total_claims == 0:
            return 0.0
        return self.supported_claims / self.total_claims

    @property
    def is_passing(self) -> bool:
        return self.unsupported_claims == 0 and self.total_claims > 0

    def to_dict(self) -> dict[str, object]:
        return {
            "total_claims": self.total_claims,
            "supported_claims": self.supported_claims,
            "unsupported_claims": self.unsupported_claims,
            "support_rate": self.support_rate,
            "is_passing": self.is_passing,
            "entries": [e.as_dict() for e in self.entries],
        }


def _check_evidence_source(source: str, project_root: Path) -> tuple[bool, str]:
    """Check if an evidence source exists.

    Sources are strings like ``src/refinery.py::CANONICAL_STAGES`` or
    ``manuscript/config.yaml#gold_refinement.seed``.
    """
    # Split on :: or #
    if "::" in source:
        file_part = source.split("::")[0]
        symbol_part = source.split("::", 1)[1] if "::" in source else ""
    elif "#" in source:
        file_part = source.split("#")[0]
        symbol_part = source.split("#", 1)[1] if "#" in source else ""
    else:
        file_part = source
        symbol_part = ""

    # Check file exists relative to project root
    file_path = project_root / file_part
    if not file_path.exists():
        return False, f"File not found: {file_part}"

    # If symbol specified, check it appears in the file
    if symbol_part:
        content = file_path.read_text(encoding="utf-8")
        # Strip method call part (e.g. _choose_value becomes just the name)
        symbol_name = symbol_part.split("(")[0].split(".")[0].split("[")[0]
        if symbol_name and symbol_name not in content:
            return False, f"Symbol '{symbol_name}' not found in {file_part}"

    return True, ""


def build_evidence_registry(
    config: GoldRefinementConfig,
    project_root: Path,
) -> EvidenceRegistry:
    """Build the evidence registry from config contribution_claims.

    Cross-checks each claim's evidence source against the actual files
    and symbols in the project.
    """
    entries: list[EvidenceEntry] = []

    for claim in config.contribution_claims:
        name = claim.get("name", "")
        statement = claim.get("claim", "")
        evidence = claim.get("evidence", "")
        boundary = claim.get("boundary", "local")

        supported, notes = _check_evidence_source(evidence, project_root)
        entries.append(
            EvidenceEntry(
                claim_name=name,
                claim_statement=statement,
                evidence_source=evidence,
                boundary=boundary,
                supported=supported,
                notes=notes,
            )
        )

    total = len(entries)
    supported_count = sum(1 for e in entries if e.supported)
    unsupported_count = total - supported_count

    return EvidenceRegistry(
        entries=entries,
        total_claims=total,
        supported_claims=supported_count,
        unsupported_claims=unsupported_count,
    )


def write_evidence_registry(
    registry: EvidenceRegistry,
    output_path: Path,
) -> Path:
    """Write the evidence registry as JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(registry.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Wrote evidence registry to %s", output_path)
    return output_path


def check_claim_ledger_alignment(
    config: GoldRefinementConfig,
    ledger_path: Path,
) -> list[str]:
    """Check that contribution_claims in config match claim_ledger.yaml entries.

    Returns a list of mismatch descriptions (empty if aligned).
    """
    mismatches: list[str] = []

    if not ledger_path.exists():
        mismatches.append(f"Claim ledger not found: {ledger_path}")
        return mismatches

    with ledger_path.open("r") as f:
        ledger = yaml.safe_load(f) or {}

    ledger_claims = {c.get("id", ""): c for c in ledger.get("claims", [])}

    for claim in config.contribution_claims:
        name = claim.get("name", "")
        # Look for a matching ledger entry by name, ID, or statement overlap
        found = False
        for lid, entry in ledger_claims.items():
            entry_stmt = entry.get("statement", "")
            # Match by ID (slugified name), by statement content, or by name in statement
            name_lower = name.lower()
            if (
                name_lower in lid.lower()
                or name_lower in entry_stmt.lower()
                or any(word in entry_stmt.lower() for word in name_lower.split() if len(word) > 3)
                or any(word in lid.lower() for word in name_lower.replace("-", "_").split("_") if len(word) > 3)
            ):
                found = True
                break
        if not found:
            mismatches.append(f"Config claim '{name}' has no matching claim_ledger.yaml entry")

    return mismatches


__all__ = [
    "EvidenceEntry",
    "EvidenceRegistry",
    "build_evidence_registry",
    "check_claim_ledger_alignment",
    "write_evidence_registry",
]
