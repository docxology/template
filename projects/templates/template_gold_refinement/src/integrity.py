from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class IntegrityDimension:
    dimension_id: str
    name: str
    failure_mode: str
    severity: int
    detectability: int
    evidence_surface: str
    validator: str
    owner: str
    source_tier: str
    mitigation: str

    @property
    def residual_risk(self) -> int:
        return self.severity * (6 - self.detectability)

    def as_dict(self) -> dict[str, str | int]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceTier:
    tier: str
    count: int
    role: str

    def as_dict(self) -> dict[str, str | int]:
        return asdict(self)


_FALLBACK_FAILURES = {
    "Non-monotone purity": (
        "A stage has lower output purity than input.",
        "Fix stage purity targets in src/refinery.py.",
    ),
    "Empty lexicon category": (
        "A required lexicon category is empty or missing.",
        "Add vocabulary to manuscript/config.yaml.",
    ),
    "Unresolved token": (
        "A manuscript placeholder has no generated variable.",
        "Add variable in src/manuscript_variables.py.",
    ),
    "Rhetorical-only analogy": (
        "The analogy is decorative with no operational mapping.",
        "Connect stages to template pipeline operations.",
    ),
}

_TIER_ROLES = {
    "artifact": "Generated artifacts exposed to readers",
    "bibliography": "Reference records and citation metadata",
    "claim_ledger": "Source-owned claim and fact declarations",
    "config": "Author-controlled project configuration",
    "generated_metric": "Numbers regenerated from project analysis",
    "source_code": "Executable source files and symbols",
    "validation": "Template gates and test results",
}


def _records(config: Any, field: str) -> list[dict[str, Any]]:
    value = getattr(config, field, [])
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _failure(config: Any, name: str) -> tuple[str, str]:
    for item in _records(config, "failure_modes"):
        if str(item.get("name", "")).lower() == name.lower():
            return str(item.get("risk", "")), str(item.get("mitigation", ""))
    return _FALLBACK_FAILURES[name]


def _audit(config: Any, keyword: str, fallback: str) -> str:
    for item in _records(config, "audit_rules"):
        text = f"{item.get('name', '')} {item.get('check', '')}".lower()
        if keyword.lower() in text:
            return str(item.get("test", fallback))
    return fallback


def build_integrity_dimensions(config: Any) -> tuple[IntegrityDimension, ...]:
    non_monotone_risk, non_monotone_mitigation = _failure(config, "Non-monotone purity")
    lexicon_risk, lexicon_mitigation = _failure(config, "Empty lexicon category")
    token_risk, token_mitigation = _failure(config, "Unresolved token")
    analogy_risk, analogy_mitigation = _failure(config, "Rhetorical-only analogy")
    claim_count = len(_records(config, "contribution_claims"))
    return (
        IntegrityDimension(
            "I1",
            "Monotone refinery",
            non_monotone_risk,
            4,
            5,
            "src/refinery.py::assert_monotone_increase",
            _audit(config, "purity", "tests/test_refinery.py"),
            "source code",
            "source_code",
            non_monotone_mitigation,
        ),
        IntegrityDimension(
            "I2",
            "Lexicon completeness",
            lexicon_risk,
            3,
            5,
            "manuscript/config.yaml#gold_refinement.lexicon",
            _audit(config, "config", "tests/test_config.py"),
            "config",
            "config",
            lexicon_mitigation,
        ),
        IntegrityDimension(
            "I3",
            "Token hydration",
            token_risk,
            5,
            5,
            "src/manuscript_variables.py::generate_variables",
            _audit(config, "token coverage", "tests/test_manuscript_variables.py"),
            "generated variables",
            "generated_metric",
            token_mitigation,
        ),
        IntegrityDimension(
            "I4",
            "Analogy boundary",
            analogy_risk,
            5,
            3,
            "data/claim_ledger.yaml::non_claims",
            "infrastructure.validation.cli evidence --fail-on-issues",
            "claim ledger",
            "claim_ledger",
            analogy_mitigation,
        ),
        IntegrityDimension(
            "I5",
            "Claim support",
            f"{claim_count} configured contribution claims require local evidence pointers.",
            5,
            4,
            "src/evidence.py::build_evidence_registry",
            "output/reports/claim_support_registry.json",
            "evidence assay",
            "artifact",
            "Keep unsupported contribution claims out of publication-strength prose.",
        ),
        IntegrityDimension(
            "I6",
            "Figure registry",
            "A manuscript figure reference could lack a generated registry entry or PNG.",
            4,
            4,
            "src/figures.py::generate_all_figures",
            "tests/test_registry_integrity.py",
            "figure producer",
            "artifact",
            "Register every generated figure and test the registry against manuscript references.",
        ),
        IntegrityDimension(
            "I7",
            "Citation hygiene",
            "A citation key could be unresolved or backed by malformed bibliography metadata.",
            4,
            5,
            "manuscript/references.bib",
            "infrastructure.reference.citation validate",
            "bibliography",
            "bibliography",
            "Validate references before render promotion.",
        ),
        IntegrityDimension(
            "I8",
            "Render readiness",
            "A hydrated manuscript could pass local source tests but fail render or output validation.",
            4,
            4,
            "scripts/03_render_pdf.py and scripts/04_validate_output.py",
            "template pipeline render and validate stages",
            "template pipeline",
            "validation",
            "Treat render output as disposable until the validation stage passes.",
        ),
    )


def integrity_dimension_table_rows(dimensions: tuple[IntegrityDimension, ...]) -> str:
    return "\n".join(
        f"| {item.dimension_id} | {item.name} | {item.residual_risk} | {item.owner} | {item.validator} |"
        for item in dimensions
    )


def integrity_owner_table_rows(dimensions: tuple[IntegrityDimension, ...]) -> str:
    counts = Counter(item.owner for item in dimensions)
    return "\n".join(f"| {owner} | {count} |" for owner, count in sorted(counts.items()))


def integrity_summary_line(dimensions: tuple[IntegrityDimension, ...]) -> str:
    highest = max(dimensions, key=lambda item: item.residual_risk)
    return (
        f"{len(dimensions)} integrity dimensions; highest residual risk is "
        f"{highest.dimension_id} ({highest.name}) at {highest.residual_risk}."
    )


def build_evidence_tiers(
    shared_evidence: dict[str, Any],
    dimensions: tuple[IntegrityDimension, ...],
) -> tuple[EvidenceTier, ...]:
    source_tiers = shared_evidence.get("source_tiers", {})
    if isinstance(source_tiers, dict) and source_tiers:
        rows = [
            EvidenceTier(str(tier), int(count), _TIER_ROLES.get(str(tier), "Evidence source tier"))
            for tier, count in source_tiers.items()
        ]
        return tuple(sorted(rows, key=lambda item: (-item.count, item.tier)))
    counts = Counter(item.source_tier for item in dimensions)
    rows = [EvidenceTier(tier, count, _TIER_ROLES.get(tier, "Evidence source tier")) for tier, count in counts.items()]
    return tuple(sorted(rows, key=lambda item: (-item.count, item.tier)))


def evidence_tier_table_rows(tiers: tuple[EvidenceTier, ...]) -> str:
    return "\n".join(f"| {item.tier} | {item.count} | {item.role} |" for item in tiers)


def integrity_records(dimensions: tuple[IntegrityDimension, ...]) -> list[dict[str, str | int]]:
    return [item.as_dict() for item in dimensions]


def evidence_tier_records(tiers: tuple[EvidenceTier, ...]) -> list[dict[str, str | int]]:
    return [item.as_dict() for item in tiers]


__all__ = [
    "EvidenceTier",
    "IntegrityDimension",
    "build_evidence_tiers",
    "build_integrity_dimensions",
    "evidence_tier_records",
    "evidence_tier_table_rows",
    "integrity_dimension_table_rows",
    "integrity_owner_table_rows",
    "integrity_records",
    "integrity_summary_line",
]
