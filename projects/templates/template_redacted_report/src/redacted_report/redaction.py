"""Disclosure-control checks for redacted release reports."""

from __future__ import annotations

import re
from dataclasses import dataclass
import hashlib
from typing import Mapping

_CLASSIFICATION_ORDER = {
    "UNCLASSIFIED": 0,
    "CUI": 1,
    "SECRET": 2,
    "TOP_SECRET": 3,
}
_ALLOWED_REASONS = {
    "source_identity",
    "operational_detail",
    "time_place_selector",
    "legal_privilege",
    "privacy",
}
_SENSITIVE_MARKERS = ("HUMINT", "SIGINT", "source", "selector", "location", "2026-")
_REVIEW_DECISIONS = {"approve", "reject", "changes_requested"}


@dataclass(frozen=True)
class RedactionSegment:
    """One report segment before public release."""

    id: str
    classification: str
    text: str
    source_controls: tuple[str, ...] = ()


@dataclass(frozen=True)
class RedactionDecision:
    """A bounded redaction decision for one segment."""

    segment_id: str
    start: int
    end: int
    reason: str
    replacement: str = "[REDACTED]"


@dataclass(frozen=True)
class RedactionFinding:
    """One release-audit finding."""

    severity: str
    code: str
    message: str


@dataclass(frozen=True)
class ClassificationTaxonomy:
    """Classification-level mapping for an organization's release policy."""

    name: str
    order: Mapping[str, int]
    public_ceiling: str = "UNCLASSIFIED"


@dataclass(frozen=True)
class ResidualPattern:
    """One residual-risk detector for sanitized release text."""

    name: str
    pattern: str
    severity: str = "warning"


@dataclass(frozen=True)
class RedactionPolicy:
    """Policy bundle for release gating and residual-risk detection."""

    name: str
    taxonomy: ClassificationTaxonomy
    public_ceiling: str
    residual_patterns: tuple[ResidualPattern, ...]
    required_review_roles: tuple[str, ...] = ("release_authority",)
    minimum_approvals: int = 1
    mosaic_threshold: float = 0.45
    block_warnings: bool = False


@dataclass(frozen=True)
class ReviewRecord:
    """One human or organizational review decision."""

    reviewer: str
    role: str
    decision: str
    rationale: str


@dataclass(frozen=True)
class ReleaseAudit:
    """Summary of a redacted release packet."""

    releasable: bool
    release_safety_score: float
    redaction_coverage: float
    mosaic_risk_score: float
    findings: tuple[RedactionFinding, ...]


@dataclass(frozen=True)
class ReleaseGateReport:
    """Review-gate status after applying approval requirements."""

    approved: bool
    approval_count: int
    required_roles_present: tuple[str, ...]
    findings: tuple[RedactionFinding, ...]


DEFAULT_RESIDUAL_PATTERNS = tuple(
    ResidualPattern(f"marker:{marker}", re.escape(marker), "warning") for marker in _SENSITIVE_MARKERS
) + (
    ResidualPattern("email_address", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "warning"),
    ResidualPattern("ipv4_address", r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "warning"),
    ResidualPattern("coordinate_pair", r"\b-?\d{1,2}\.\d{3,},\s*-?\d{1,3}\.\d{3,}\b", "warning"),
    ResidualPattern("controlled_dissemination", r"\b(?:NOFORN|ORCON|REL\s+TO)\b", "warning"),
)
DEFAULT_TAXONOMY = ClassificationTaxonomy("default", _CLASSIFICATION_ORDER)
DEFAULT_POLICY = RedactionPolicy(
    name="default",
    taxonomy=DEFAULT_TAXONOMY,
    public_ceiling="UNCLASSIFIED",
    residual_patterns=DEFAULT_RESIDUAL_PATTERNS,
)


def intelligence_agency_taxonomy() -> ClassificationTaxonomy:
    """Return a common intelligence-style taxonomy with SCI alias support.

    This is a release-safety taxonomy only. It does not authorize publication;
    callers still need a release authority and redaction decisions.
    """
    return ClassificationTaxonomy(
        name="intelligence_agency",
        order={
            "UNCLASSIFIED": 0,
            "CUI": 1,
            "CONFIDENTIAL": 2,
            "SECRET": 3,
            "TOP_SECRET": 4,
            "TOP_SECRET_SCI": 5,
            "TS_SCI": 5,
        },
    )


def intelligence_release_policy() -> RedactionPolicy:
    """Return a conservative release-review policy for invented intelligence fixtures."""
    taxonomy = intelligence_agency_taxonomy()
    return RedactionPolicy(
        name="intelligence_release_review",
        taxonomy=taxonomy,
        public_ceiling="UNCLASSIFIED",
        residual_patterns=DEFAULT_RESIDUAL_PATTERNS
        + (
            ResidualPattern("collection_discipline", r"\b(?:HUMINT|SIGINT|IMINT|MASINT|OSINT)\b", "warning"),
            ResidualPattern("compartment_marker", r"\b(?:SCI|TS_SCI|TOP\s+SECRET)\b", "warning"),
        ),
        required_review_roles=("originator", "classification_reviewer", "release_authority"),
        minimum_approvals=3,
        mosaic_threshold=0.30,
        block_warnings=True,
    )


def redact_text(text: str, decisions: list[RedactionDecision]) -> str:
    """Apply non-overlapping redaction decisions to text."""
    _validate_decision_bounds(text, decisions)
    result = text
    for decision in sorted(decisions, key=lambda item: item.start, reverse=True):
        result = result[: decision.start] + decision.replacement + result[decision.end :]
    return result


def audit_release_packet(
    segments: list[RedactionSegment],
    decisions: list[RedactionDecision],
    *,
    release_authority: str,
    public_ceiling: str = "UNCLASSIFIED",
    mosaic_threshold: float = 0.45,
    taxonomy: ClassificationTaxonomy | None = None,
    policy: RedactionPolicy | None = None,
) -> ReleaseAudit:
    """Audit a proposed public release packet."""
    findings: list[RedactionFinding] = []
    policy = policy or DEFAULT_POLICY
    taxonomy = taxonomy or policy.taxonomy
    if not release_authority.strip():
        findings.append(RedactionFinding("error", "missing_release_authority", "release authority is required"))
    _check_segment_and_decision_ids(segments, decisions, findings)
    ceiling_rank = _classification_rank(public_ceiling, findings, taxonomy)
    decision_map = _decisions_by_segment(decisions)
    for segment in segments:
        rank = _classification_rank(segment.classification, findings, taxonomy)
        segment_decisions = decision_map.get(segment.id, [])
        _check_classification_ceiling(segment, rank, ceiling_rank, segment_decisions, findings)
        _check_decisions(segment, segment_decisions, findings)
        _check_sensitive_residue(segment, segment_decisions, findings, policy)
    coverage = _redaction_coverage(segments, decision_map)
    mosaic = _mosaic_risk(segments, decision_map, policy)
    if mosaic > mosaic_threshold:
        findings.append(RedactionFinding("warning", "mosaic_risk", "combined residual selectors exceed threshold"))
    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    score = max(0.0, round(1.0 - len(errors) * 0.25 - len(warnings) * 0.10 - mosaic * 0.20, 3))
    return ReleaseAudit(
        releasable=not errors,
        release_safety_score=score,
        redaction_coverage=coverage,
        mosaic_risk_score=mosaic,
        findings=tuple(findings),
    )


def redacted_segments(
    segments: list[RedactionSegment],
    decisions: list[RedactionDecision],
) -> tuple[dict[str, object], ...]:
    """Return sanitized segment records containing redacted text only."""
    decision_map = _decisions_by_segment(decisions)
    output: list[dict[str, object]] = []
    for segment in segments:
        output.append(
            {
                "id": segment.id,
                "classification": segment.classification,
                "text": redact_text(segment.text, decision_map.get(segment.id, [])),
                "source_controls": segment.source_controls,
            }
        )
    return tuple(output)


def paragraph_audit_table(
    segments: list[RedactionSegment],
    decisions: list[RedactionDecision],
    *,
    public_ceiling: str = "UNCLASSIFIED",
    taxonomy: ClassificationTaxonomy | None = None,
    policy: RedactionPolicy | None = None,
) -> tuple[dict[str, object], ...]:
    """Build a paragraph/segment-level release audit table."""
    policy = policy or DEFAULT_POLICY
    taxonomy = taxonomy or policy.taxonomy
    findings: list[RedactionFinding] = []
    ceiling_rank = _classification_rank(public_ceiling, findings, taxonomy)
    decision_map = _decisions_by_segment(decisions)
    rows: list[dict[str, object]] = []
    for segment in segments:
        segment_findings: list[RedactionFinding] = []
        rank = _classification_rank(segment.classification, segment_findings, taxonomy)
        segment_decisions = decision_map.get(segment.id, [])
        try:
            redacted = redact_text(segment.text, segment_decisions)
            residual = _residual_markers(redacted, policy)
        except ValueError:
            redacted = segment.text
            residual = _residual_markers(redacted, policy)
        rows.append(
            {
                "segment_id": segment.id,
                "classification": segment.classification,
                "above_ceiling": rank > ceiling_rank,
                "source_controls": segment.source_controls,
                "decision_count": len(segment_decisions),
                "residual_markers": residual,
                "redacted_length": len(redacted),
                "status": "blocked" if rank > ceiling_rank and not segment_decisions else "reviewed",
            }
        )
    return tuple(rows)


def build_release_packet(
    segments: list[RedactionSegment],
    decisions: list[RedactionDecision],
    *,
    release_authority: str,
    public_ceiling: str = "UNCLASSIFIED",
    mosaic_threshold: float = 0.45,
    taxonomy: ClassificationTaxonomy | None = None,
    policy: RedactionPolicy | None = None,
) -> dict[str, object]:
    """Build a JSON-ready sanitized release packet for publication review."""
    policy = policy or DEFAULT_POLICY
    taxonomy = taxonomy or policy.taxonomy
    audit = audit_release_packet(
        segments,
        decisions,
        release_authority=release_authority,
        public_ceiling=public_ceiling,
        mosaic_threshold=mosaic_threshold,
        taxonomy=taxonomy,
        policy=policy,
    )
    return {
        "release_authority": release_authority,
        "public_ceiling": public_ceiling,
        "taxonomy": taxonomy.name,
        "releasable": audit.releasable,
        "release_safety_score": audit.release_safety_score,
        "redaction_coverage": audit.redaction_coverage,
        "mosaic_risk_score": audit.mosaic_risk_score,
        "findings": tuple(finding.__dict__ for finding in audit.findings),
        "segments": redacted_segments(segments, decisions),
        "paragraph_audit": paragraph_audit_table(
            segments,
            decisions,
            public_ceiling=public_ceiling,
            taxonomy=taxonomy,
            policy=policy,
        ),
    }


def detect_residual_risks(text: str, policy: RedactionPolicy | None = None) -> tuple[dict[str, str], ...]:
    """Detect residual markers in sanitized text without exposing source text."""
    policy = policy or DEFAULT_POLICY
    risks: list[dict[str, str]] = []
    for pattern in policy.residual_patterns:
        if re.search(pattern.pattern, text, flags=re.IGNORECASE):
            risks.append({"name": pattern.name, "severity": pattern.severity})
    return tuple(risks)


def build_redaction_ledger(
    segments: list[RedactionSegment],
    decisions: list[RedactionDecision],
) -> tuple[dict[str, object], ...]:
    """Build a source-safe decision ledger with hashes instead of source excerpts."""
    segments_by_id = {segment.id: segment for segment in segments}
    rows: list[dict[str, object]] = []
    for decision in sorted(decisions, key=lambda item: (item.segment_id, item.start, item.end, item.reason)):
        segment = segments_by_id.get(decision.segment_id)
        valid_span = bool(segment and 0 <= decision.start < decision.end <= len(segment.text))
        span_text = segment.text[decision.start : decision.end] if valid_span and segment else ""
        row_payload = f"{decision.segment_id}|{decision.start}|{decision.end}|{decision.reason}|{decision.replacement}"
        rows.append(
            {
                "decision_id": _hash_text(row_payload)[:16],
                "segment_id": decision.segment_id,
                "start": decision.start,
                "end": decision.end,
                "span_length": max(0, decision.end - decision.start),
                "reason": decision.reason,
                "replacement": decision.replacement,
                "valid_span": valid_span,
                "source_span_sha256": _hash_text(span_text) if valid_span else "",
            }
        )
    return tuple(rows)


def segment_hash_manifest(
    segments: list[RedactionSegment],
    decisions: list[RedactionDecision],
) -> tuple[dict[str, str], ...]:
    """Return source and public hashes for reproducible release audits."""
    decision_map = _decisions_by_segment(decisions)
    rows: list[dict[str, str]] = []
    for segment in segments:
        try:
            public_text = redact_text(segment.text, decision_map.get(segment.id, []))
        except ValueError:
            public_text = ""
        rows.append(
            {
                "segment_id": segment.id,
                "source_sha256": _hash_text(segment.text),
                "public_sha256": _hash_text(public_text),
            }
        )
    return tuple(rows)


def evaluate_review_gate(
    reviews: list[ReviewRecord],
    policy: RedactionPolicy | None = None,
) -> ReleaseGateReport:
    """Evaluate reviewer approvals against a release policy."""
    policy = policy or DEFAULT_POLICY
    findings: list[RedactionFinding] = []
    approvals = [review for review in reviews if review.decision == "approve"]
    approval_roles = {review.role for review in approvals}
    for review in reviews:
        if review.decision not in _REVIEW_DECISIONS:
            findings.append(RedactionFinding("error", "bad_review_decision", f"unsupported review: {review.decision}"))
        if not review.rationale.strip():
            findings.append(RedactionFinding("error", "review_without_rationale", f"{review.reviewer} lacks rationale"))
        if review.decision == "reject":
            findings.append(RedactionFinding("error", "release_rejected", f"{review.role} rejected release"))
        if review.decision == "changes_requested":
            findings.append(
                RedactionFinding("warning", "changes_requested", f"{review.role} requested release changes")
            )
    if len(approvals) < policy.minimum_approvals:
        findings.append(
            RedactionFinding(
                "error",
                "insufficient_approvals",
                f"{len(approvals)} approvals is below required {policy.minimum_approvals}",
            )
        )
    for role in policy.required_review_roles:
        if role not in approval_roles:
            findings.append(RedactionFinding("error", "missing_required_role", f"missing approval role: {role}"))
    errors = [finding for finding in findings if finding.severity == "error"]
    return ReleaseGateReport(
        approved=not errors,
        approval_count=len(approvals),
        required_roles_present=tuple(sorted(approval_roles & set(policy.required_review_roles))),
        findings=tuple(findings),
    )


def build_comprehensive_release_packet(
    segments: list[RedactionSegment],
    decisions: list[RedactionDecision],
    reviews: list[ReviewRecord],
    *,
    release_authority: str,
    policy: RedactionPolicy | None = None,
) -> dict[str, object]:
    """Build the full release packet: sanitized text, audit, ledger, hashes, and review gate."""
    policy = policy or DEFAULT_POLICY
    release_packet = build_release_packet(
        segments,
        decisions,
        release_authority=release_authority,
        public_ceiling=policy.public_ceiling,
        mosaic_threshold=policy.mosaic_threshold,
        taxonomy=policy.taxonomy,
        policy=policy,
    )
    review_gate = evaluate_review_gate(reviews, policy)
    raw_findings = release_packet.get("findings", ())
    audit_findings = (
        tuple(
            RedactionFinding(str(item["severity"]), str(item["code"]), str(item["message"]))
            for item in raw_findings
            if isinstance(item, dict)
        )
        if isinstance(raw_findings, tuple)
        else ()
    )
    warning_block = policy.block_warnings and any(finding.severity == "warning" for finding in audit_findings)
    return {
        **release_packet,
        "policy": policy.name,
        "redaction_ledger": build_redaction_ledger(segments, decisions),
        "hash_manifest": segment_hash_manifest(segments, decisions),
        "review_gate": {
            "approved": review_gate.approved,
            "approval_count": review_gate.approval_count,
            "required_roles_present": review_gate.required_roles_present,
            "findings": tuple(finding.__dict__ for finding in review_gate.findings),
        },
        "final_release_recommended": bool(release_packet["releasable"] and review_gate.approved and not warning_block),
    }


def _validate_decision_bounds(text: str, decisions: list[RedactionDecision]) -> None:
    spans: list[tuple[int, int]] = []
    for decision in decisions:
        if decision.start < 0 or decision.end > len(text) or decision.start >= decision.end:
            raise ValueError(f"invalid redaction bounds: {decision.start}:{decision.end}")
        if decision.reason not in _ALLOWED_REASONS:
            raise ValueError(f"unsupported redaction reason: {decision.reason}")
        for start, end in spans:
            if max(start, decision.start) < min(end, decision.end):
                raise ValueError("overlapping redaction decisions")
        spans.append((decision.start, decision.end))


def _classification_rank(
    value: str,
    findings: list[RedactionFinding],
    taxonomy: ClassificationTaxonomy | None = None,
) -> int:
    taxonomy = taxonomy or DEFAULT_TAXONOMY
    normalized = _normalize_classification(value)
    if normalized not in taxonomy.order:
        findings.append(RedactionFinding("error", "unknown_classification", f"unknown classification: {value}"))
        return 99
    return taxonomy.order[normalized]


def _normalize_classification(value: str) -> str:
    return value.upper().replace("//", "_").replace(" ", "_").replace("-", "_")


def _decisions_by_segment(decisions: list[RedactionDecision]) -> dict[str, list[RedactionDecision]]:
    grouped: dict[str, list[RedactionDecision]] = {}
    for decision in decisions:
        grouped.setdefault(decision.segment_id, []).append(decision)
    return grouped


def _check_segment_and_decision_ids(
    segments: list[RedactionSegment],
    decisions: list[RedactionDecision],
    findings: list[RedactionFinding],
) -> None:
    segment_ids: set[str] = set()
    for segment in segments:
        if segment.id in segment_ids:
            findings.append(RedactionFinding("error", "duplicate_segment_id", f"duplicate segment id: {segment.id}"))
        segment_ids.add(segment.id)
    for decision in decisions:
        if decision.segment_id not in segment_ids:
            findings.append(
                RedactionFinding("error", "orphan_redaction_decision", f"decision references {decision.segment_id}")
            )


def _check_classification_ceiling(
    segment: RedactionSegment,
    rank: int,
    ceiling_rank: int,
    decisions: list[RedactionDecision],
    findings: list[RedactionFinding],
) -> None:
    if rank > ceiling_rank and not decisions:
        findings.append(
            RedactionFinding(
                "error", "above_ceiling_unredacted", f"{segment.id} exceeds public ceiling without redaction"
            )
        )


def _check_decisions(
    segment: RedactionSegment,
    decisions: list[RedactionDecision],
    findings: list[RedactionFinding],
) -> None:
    try:
        redact_text(segment.text, decisions)
    except ValueError as exc:
        findings.append(RedactionFinding("error", "bad_redaction_decision", f"{segment.id}: {exc}"))
    for control in segment.source_controls:
        if not any(decision.reason == "source_identity" for decision in decisions):
            findings.append(
                RedactionFinding(
                    "error", "source_control_uncovered", f"{segment.id} source control {control} lacks source redaction"
                )
            )


def _check_sensitive_residue(
    segment: RedactionSegment,
    decisions: list[RedactionDecision],
    findings: list[RedactionFinding],
    policy: RedactionPolicy,
) -> None:
    try:
        redacted = redact_text(segment.text, decisions)
    except ValueError:
        return
    for risk in detect_residual_risks(redacted, policy):
        findings.append(
            RedactionFinding(risk["severity"], "sensitive_residue", f"{segment.id} retains marker {risk['name']}")
        )


def _redaction_coverage(segments: list[RedactionSegment], decision_map: dict[str, list[RedactionDecision]]) -> float:
    sensitive_segments = [
        segment for segment in segments if segment.classification.upper() != "UNCLASSIFIED" or segment.source_controls
    ]
    if not sensitive_segments:
        return 1.0
    covered = sum(1 for segment in sensitive_segments if decision_map.get(segment.id))
    return round(covered / len(sensitive_segments), 3)


def _mosaic_risk(
    segments: list[RedactionSegment],
    decision_map: dict[str, list[RedactionDecision]],
    policy: RedactionPolicy,
) -> float:
    residual_markers = 0
    for segment in segments:
        try:
            redacted = redact_text(segment.text, decision_map.get(segment.id, []))
        except ValueError:
            redacted = segment.text
        residual_markers += len(_residual_markers(redacted, policy))
    denominator = max(1, len(segments) * len(policy.residual_patterns))
    return round(residual_markers / denominator, 3)


def _residual_markers(text: str, policy: RedactionPolicy) -> tuple[str, ...]:
    return tuple(risk["name"] for risk in detect_residual_risks(text, policy))


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
