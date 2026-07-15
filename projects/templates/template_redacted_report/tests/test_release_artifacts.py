"""Real-behavior tests for typed release loading and public JSON artifacts."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from redacted_report import (
    AUDIT_SCHEMA,
    LEDGER_SCHEMA,
    RedactionDecision,
    RedactionSegment,
    ReleaseInputError,
    ReviewRecord,
    build_public_release_artifacts,
    load_release_fixture,
    write_release_artifacts,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_INPUT = PROJECT_ROOT / "data" / "example_segments.json"
GENERATOR = PROJECT_ROOT / "scripts" / "01_generate_release_artifacts.py"


def _minimal_payload(secret: str = "SOURCE-CANARY-7f38c0") -> dict[str, object]:
    text = f"Public preface {secret} public conclusion."
    start = text.index(secret)
    return {
        "release_authority": "public-review-board",
        "release_policy": "intelligence_release_review",
        "public_ceiling": "UNCLASSIFIED",
        "segments": [
            {
                "id": "secret-1",
                "classification": "SECRET",
                "text": text,
                "source_controls": ["HUMINT"],
            }
        ],
        "redactions": [
            {
                "segment_id": "secret-1",
                "start": start,
                "end": start + len(secret),
                "reason": "source_identity",
            }
        ],
        "reviews": [
            {
                "reviewer": "originator-a",
                "role": "originator",
                "decision": "approve",
                "rationale": "source equities reviewed",
            },
            {
                "reviewer": "classification-reviewer",
                "role": "classification_reviewer",
                "decision": "approve",
                "rationale": "classification checked",
            },
            {
                "reviewer": "release-board",
                "role": "release_authority",
                "decision": "approve",
                "rationale": "public fixture authorized",
            },
        ],
    }


def _write_payload(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _has_key(value: object, target: str) -> bool:
    if isinstance(value, dict):
        return target in value or any(_has_key(item, target) for item in value.values())
    if isinstance(value, list):
        return any(_has_key(item, target) for item in value)
    return False


def test_loader_constructs_typed_records_and_declared_policy() -> None:
    fixture = load_release_fixture(EXAMPLE_INPUT)

    assert fixture.policy.name == "intelligence_release_review"
    assert fixture.public_ceiling == fixture.policy.public_ceiling == "UNCLASSIFIED"
    assert len(fixture.segments) == 14
    assert len(fixture.decisions) == 22
    assert len(fixture.reviews) == 3
    assert isinstance(fixture.segments[0], RedactionSegment)
    assert isinstance(fixture.decisions[0], RedactionDecision)
    assert isinstance(fixture.reviews[0], ReviewRecord)
    assert fixture.source_fixture_sha256 == hashlib.sha256(EXAMPLE_INPUT.read_bytes()).hexdigest()


def test_public_artifacts_are_deterministic_and_text_free(tmp_path: Path) -> None:
    first = write_release_artifacts(EXAMPLE_INPUT, tmp_path / "first")
    second = write_release_artifacts(EXAMPLE_INPUT, tmp_path / "second")

    assert first.redaction_audit.read_bytes() == second.redaction_audit.read_bytes()
    assert first.release_ledger.read_bytes() == second.release_ledger.read_bytes()

    audit = json.loads(first.redaction_audit.read_text(encoding="utf-8"))
    ledger = json.loads(first.release_ledger.read_text(encoding="utf-8"))
    combined = first.redaction_audit.read_text(encoding="utf-8") + first.release_ledger.read_text(encoding="utf-8")

    assert audit["schema_version"] == AUDIT_SCHEMA
    assert ledger["schema_version"] == LEDGER_SCHEMA
    assert audit["narrative_exported"] is False
    assert ledger["source_text_exported"] is False
    assert audit["policy"] == ledger["policy"] == "intelligence_release_review"
    assert not _has_key(audit, "text")
    assert not _has_key(ledger, "text")
    assert "segments" not in audit
    assert "Alpha reported" not in combined
    assert "analyst@example.org" not in combined
    assert "38.8977, -77.0365" not in combined
    assert "192.0.2.10" not in combined
    assert all(len(row["source_span_sha256"]) == 64 for row in ledger["redaction_ledger"])
    assert all("source_sha256" in row for row in ledger["segment_hash_manifest"])


def test_unique_sensitive_span_is_hashed_never_serialized(tmp_path: Path) -> None:
    secret = "SOURCE-CANARY-7f38c0"
    input_path = _write_payload(tmp_path / "fixture.json", _minimal_payload(secret))

    fixture = load_release_fixture(input_path)
    in_memory = build_public_release_artifacts(fixture)
    paths = write_release_artifacts(input_path, tmp_path / "output")
    serialized = paths.redaction_audit.read_text() + paths.release_ledger.read_text()
    ledger = json.loads(paths.release_ledger.read_text(encoding="utf-8"))

    assert in_memory.redaction_audit["final_release_recommended"] is True
    assert secret not in serialized
    assert fixture.segments[0].text not in serialized
    assert ledger["redaction_ledger"][0]["source_span_sha256"] == hashlib.sha256(secret.encode("utf-8")).hexdigest()


def test_loader_rejects_missing_and_malformed_inputs(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="release fixture not found"):
        load_release_fixture(tmp_path / "missing.json")

    malformed = tmp_path / "malformed.json"
    malformed.write_text("{", encoding="utf-8")
    with pytest.raises(ReleaseInputError, match="not valid UTF-8 JSON"):
        load_release_fixture(malformed)

    missing_keys = _write_payload(tmp_path / "missing-keys.json", {})
    with pytest.raises(ReleaseInputError, match="missing required key: release_policy"):
        load_release_fixture(missing_keys)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("unsupported_policy", "release_policy must be intelligence_release_review"),
        ("wrong_ceiling", "public_ceiling must match"),
        ("unknown_classification", "classification is not declared"),
        ("custom_replacement", r"source-safe \[REDACTED\] token"),
        ("orphan_decision", "unknown segment_id"),
        ("invalid_bounds", "invalid redaction bounds"),
        ("bad_review_decision", "decision is not supported"),
    ],
)
def test_loader_rejects_unsafe_or_structurally_invalid_records(
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    payload = _minimal_payload()
    if mutation == "unsupported_policy":
        payload["release_policy"] = "unreviewed"
    elif mutation == "wrong_ceiling":
        payload["public_ceiling"] = "SECRET"
    elif mutation == "unknown_classification":
        payload["segments"][0]["classification"] = "COSMIC_SECRET"
    elif mutation == "custom_replacement":
        payload["redactions"][0]["replacement"] = "SOURCE-CANARY-7f38c0"
    elif mutation == "orphan_decision":
        payload["redactions"][0]["segment_id"] = "missing-segment"
    elif mutation == "invalid_bounds":
        payload["redactions"][0]["end"] = 99_999
    elif mutation == "bad_review_decision":
        payload["reviews"][0]["decision"] = "defer"

    input_path = _write_payload(tmp_path / f"{mutation}.json", payload)
    with pytest.raises(ReleaseInputError, match=message):
        load_release_fixture(input_path)


def test_thin_script_writes_declared_paths_and_fails_closed_on_missing_input(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "output"
    completed = subprocess.run(
        [
            sys.executable,
            str(GENERATOR),
            "--input",
            str(EXAMPLE_INPUT),
            "--output-root",
            str(output_root),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert (output_root / "reports" / "redaction_audit.json").is_file()
    assert (output_root / "data" / "release_ledger.json").is_file()

    failed = subprocess.run(
        [
            sys.executable,
            str(GENERATOR),
            "--input",
            str(tmp_path / "missing.json"),
            "--output-root",
            str(tmp_path / "missing-output"),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert failed.returncode == 2
    assert "release fixture not found" in failed.stderr
    assert not (tmp_path / "missing-output").exists()
