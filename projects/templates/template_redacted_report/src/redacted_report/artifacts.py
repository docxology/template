"""Typed fixture loading and source-safe release-artifact serialization."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from redacted_report.redaction import (
    RedactionDecision,
    RedactionPolicy,
    RedactionSegment,
    ReviewRecord,
    build_comprehensive_release_packet,
    intelligence_release_policy,
    redact_text,
)

AUDIT_SCHEMA = "template_redacted_report/redaction_audit/v1"
LEDGER_SCHEMA = "template_redacted_report/release_ledger/v1"
_PUBLIC_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REVIEW_DECISIONS = frozenset({"approve", "reject", "changes_requested"})
_FORBIDDEN_PUBLIC_KEYS = frozenset({"text", "source_text", "source_span", "sanitized_text"})


class ReleaseInputError(ValueError):
    """Raised when a release fixture cannot satisfy the typed input contract."""


@dataclass(frozen=True)
class ReleaseFixture:
    """Validated release input with typed domain records and policy."""

    release_authority: str
    policy: RedactionPolicy
    public_ceiling: str
    segments: tuple[RedactionSegment, ...]
    decisions: tuple[RedactionDecision, ...]
    reviews: tuple[ReviewRecord, ...]
    source_fixture_sha256: str


@dataclass(frozen=True)
class PublicReleaseArtifacts:
    """Text-free public projections of a comprehensive release packet."""

    redaction_audit: dict[str, object]
    release_ledger: dict[str, object]


@dataclass(frozen=True)
class ReleaseArtifactPaths:
    """Paths written by :func:`write_release_artifacts`."""

    redaction_audit: Path
    release_ledger: Path


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ReleaseInputError(f"{label} must be a JSON object")
    return value


def _rows(value: object, label: str, *, allow_empty: bool = False) -> list[object]:
    if not isinstance(value, list):
        raise ReleaseInputError(f"{label} must be a JSON array")
    if not value and not allow_empty:
        raise ReleaseInputError(f"{label} must not be empty")
    return value


def _required(row: Mapping[str, object], key: str, label: str) -> object:
    if key not in row:
        raise ReleaseInputError(f"{label} is missing required key: {key}")
    return row[key]


def _string(value: object, label: str, *, public_identifier: bool = False) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReleaseInputError(f"{label} must be a non-empty string")
    if public_identifier and not _PUBLIC_IDENTIFIER.fullmatch(value):
        raise ReleaseInputError(f"{label} must be a public-safe identifier")
    return value


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReleaseInputError(f"{label} must be an integer")
    return value


def _parse_segment(value: object, index: int, policy: RedactionPolicy) -> RedactionSegment:
    label = f"segments[{index}]"
    row = _mapping(value, label)
    segment_id = _string(_required(row, "id", label), f"{label}.id", public_identifier=True)
    classification = _string(_required(row, "classification", label), f"{label}.classification")
    normalized = classification.upper().replace("//", "_").replace(" ", "_").replace("-", "_")
    if normalized not in policy.taxonomy.order:
        raise ReleaseInputError(f"{label}.classification is not declared by the release policy")
    text = _string(_required(row, "text", label), f"{label}.text")
    controls = tuple(
        _string(item, f"{label}.source_controls", public_identifier=True)
        for item in _rows(row.get("source_controls", []), f"{label}.source_controls", allow_empty=True)
    )
    return RedactionSegment(segment_id, classification, text, controls)


def _parse_decision(value: object, index: int) -> RedactionDecision:
    label = f"redactions[{index}]"
    row = _mapping(value, label)
    replacement = _string(row.get("replacement", "[REDACTED]"), f"{label}.replacement")
    if replacement != "[REDACTED]":
        raise ReleaseInputError(f"{label}.replacement must use the source-safe [REDACTED] token")
    return RedactionDecision(
        segment_id=_string(
            _required(row, "segment_id", label),
            f"{label}.segment_id",
            public_identifier=True,
        ),
        start=_integer(_required(row, "start", label), f"{label}.start"),
        end=_integer(_required(row, "end", label), f"{label}.end"),
        reason=_string(_required(row, "reason", label), f"{label}.reason", public_identifier=True),
        replacement=replacement,
    )


def _parse_review(value: object, index: int) -> ReviewRecord:
    label = f"reviews[{index}]"
    row = _mapping(value, label)
    decision = _string(_required(row, "decision", label), f"{label}.decision")
    if decision not in _REVIEW_DECISIONS:
        raise ReleaseInputError(f"{label}.decision is not supported")
    return ReviewRecord(
        reviewer=_string(_required(row, "reviewer", label), f"{label}.reviewer"),
        role=_string(_required(row, "role", label), f"{label}.role", public_identifier=True),
        decision=decision,
        rationale=_string(_required(row, "rationale", label), f"{label}.rationale"),
    )


def _validate_relations(fixture: ReleaseFixture) -> None:
    segments_by_id = {segment.id: segment for segment in fixture.segments}
    if len(segments_by_id) != len(fixture.segments):
        raise ReleaseInputError("segments contain duplicate ids")
    grouped: dict[str, list[RedactionDecision]] = {}
    for decision in fixture.decisions:
        if decision.segment_id not in segments_by_id:
            raise ReleaseInputError("redactions contain an unknown segment_id")
        grouped.setdefault(decision.segment_id, []).append(decision)
    for segment_id, decisions in grouped.items():
        try:
            redact_text(segments_by_id[segment_id].text, decisions)
        except ValueError as exc:
            raise ReleaseInputError(f"redactions for {segment_id} are invalid: {exc}") from exc


def load_release_fixture(path: Path) -> ReleaseFixture:
    """Load and validate a JSON release fixture as typed domain records."""
    if not path.is_file():
        raise FileNotFoundError(f"release fixture not found: {path}")
    raw_bytes = path.read_bytes()
    try:
        payload = _mapping(json.loads(raw_bytes), "release fixture")
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ReleaseInputError("release fixture is not valid UTF-8 JSON") from exc

    policy = intelligence_release_policy()
    policy_name = _string(_required(payload, "release_policy", "release fixture"), "release_policy")
    if policy_name != policy.name:
        raise ReleaseInputError("release_policy must be intelligence_release_review")
    public_ceiling = _string(_required(payload, "public_ceiling", "release fixture"), "public_ceiling")
    if public_ceiling != policy.public_ceiling:
        raise ReleaseInputError("public_ceiling must match the declared release policy")

    fixture = ReleaseFixture(
        release_authority=_string(
            _required(payload, "release_authority", "release fixture"),
            "release_authority",
            public_identifier=True,
        ),
        policy=policy,
        public_ceiling=public_ceiling,
        segments=tuple(
            _parse_segment(item, index, policy)
            for index, item in enumerate(_rows(_required(payload, "segments", "release fixture"), "segments"))
        ),
        decisions=tuple(
            _parse_decision(item, index)
            for index, item in enumerate(
                _rows(_required(payload, "redactions", "release fixture"), "redactions", allow_empty=True)
            )
        ),
        reviews=tuple(
            _parse_review(item, index)
            for index, item in enumerate(_rows(_required(payload, "reviews", "release fixture"), "reviews"))
        ),
        source_fixture_sha256=hashlib.sha256(raw_bytes).hexdigest(),
    )
    _validate_relations(fixture)
    return fixture


def _assert_text_free(value: object, path: str = "artifact") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in _FORBIDDEN_PUBLIC_KEYS:
                raise RuntimeError(f"public artifact contains forbidden text field: {path}.{key}")
            _assert_text_free(item, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _assert_text_free(item, f"{path}[{index}]")


def _canonical_json(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def build_public_release_artifacts(fixture: ReleaseFixture) -> PublicReleaseArtifacts:
    """Build text-free audit and hashed-ledger projections of the full packet."""
    packet = build_comprehensive_release_packet(
        list(fixture.segments),
        list(fixture.decisions),
        list(fixture.reviews),
        release_authority=fixture.release_authority,
        policy=fixture.policy,
    )
    common = {
        "source_fixture_sha256": fixture.source_fixture_sha256,
        "release_authority": packet["release_authority"],
        "policy": packet["policy"],
        "public_ceiling": packet["public_ceiling"],
        "taxonomy": packet["taxonomy"],
        "segment_count": len(fixture.segments),
        "decision_count": len(fixture.decisions),
        "review_count": len(fixture.reviews),
    }
    audit: dict[str, object] = {
        "schema_version": AUDIT_SCHEMA,
        **common,
        "releasable": packet["releasable"],
        "final_release_recommended": packet["final_release_recommended"],
        "release_safety_score": packet["release_safety_score"],
        "redaction_coverage": packet["redaction_coverage"],
        "mosaic_risk_score": packet["mosaic_risk_score"],
        "findings": packet["findings"],
        "review_gate": packet["review_gate"],
        "paragraph_audit": packet["paragraph_audit"],
        "narrative_exported": False,
    }
    ledger: dict[str, object] = {
        "schema_version": LEDGER_SCHEMA,
        **common,
        "redaction_ledger": packet["redaction_ledger"],
        "segment_hash_manifest": packet["hash_manifest"],
        "source_text_exported": False,
    }
    artifacts = PublicReleaseArtifacts(audit, ledger)
    for payload in (artifacts.redaction_audit, artifacts.release_ledger):
        _assert_text_free(payload)
        serialized = _canonical_json(payload)
        if any(segment.text in serialized for segment in fixture.segments):
            raise RuntimeError("public artifact contains an unredacted source segment")
    return artifacts


def write_release_artifacts(input_path: Path, output_root: Path) -> ReleaseArtifactPaths:
    """Write deterministic public audit and ledger JSON beneath ``output_root``."""
    fixture = load_release_fixture(input_path)
    artifacts = build_public_release_artifacts(fixture)
    audit_path = output_root / "reports" / "redaction_audit.json"
    ledger_path = output_root / "data" / "release_ledger.json"
    for path, payload in (
        (audit_path, artifacts.redaction_audit),
        (ledger_path, artifacts.release_ledger),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_canonical_json(payload), encoding="utf-8")
    return ReleaseArtifactPaths(audit_path, ledger_path)


__all__ = [
    "AUDIT_SCHEMA",
    "LEDGER_SCHEMA",
    "PublicReleaseArtifacts",
    "ReleaseArtifactPaths",
    "ReleaseFixture",
    "ReleaseInputError",
    "build_public_release_artifacts",
    "load_release_fixture",
    "write_release_artifacts",
]
