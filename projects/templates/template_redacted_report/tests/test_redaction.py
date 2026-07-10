from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

import redacted_report.visuals as visuals
from redacted_report import (
    KMYTH_SEAL_ARTIFACTS,
    PDF_BACKGROUND_MODES,
    REDACTION_VISUAL_STYLES,
    SECURITY_METHODS,
    RedactionDecision,
    RedactionSegment,
    ReviewRecord,
    audit_release_packet,
    build_comprehensive_release_packet,
    build_redaction_ledger,
    build_release_packet,
    build_visual_variant_matrix,
    detect_residual_risks,
    evaluate_review_gate,
    intelligence_release_policy,
    intelligence_agency_taxonomy,
    normalize_pdf_background,
    normalize_redaction_style,
    paragraph_audit_table,
    redact_text,
    redacted_segments,
    render_visual_redaction_text,
    segment_hash_manifest,
    visual_redacted_segments,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_packet() -> tuple[str, list[RedactionSegment], list[RedactionDecision]]:
    payload = json.loads((PROJECT_ROOT / "data" / "example_segments.json").read_text(encoding="utf-8"))
    segments = [
        RedactionSegment(
            id=item["id"],
            classification=item["classification"],
            text=item["text"],
            source_controls=tuple(item.get("source_controls", [])),
        )
        for item in payload["segments"]
    ]
    decisions = [RedactionDecision(**item) for item in payload["redactions"]]
    return payload["release_authority"], segments, decisions


def load_reviews() -> list[ReviewRecord]:
    payload = json.loads((PROJECT_ROOT / "data" / "example_segments.json").read_text(encoding="utf-8"))
    return [ReviewRecord(**item) for item in payload["reviews"]]


def test_redact_text_applies_non_overlapping_decisions() -> None:
    text = "Source Alpha met at location Bravo."
    result = redact_text(
        text,
        [
            RedactionDecision("s1", 0, 12, "source_identity"),
            RedactionDecision("s1", 20, 34, "time_place_selector"),
        ],
    )

    assert result == "[REDACTED] met at [REDACTED]."


def test_visual_redaction_styles_cover_requested_modes_without_source_leakage() -> None:
    text = "Source Alpha reported location Bravo."
    decisions = [
        RedactionDecision("s1", 0, 12, "source_identity"),
        RedactionDecision("s1", 22, 36, "operational_detail"),
    ]

    assert {profile.name for profile in REDACTION_VISUAL_STYLES} == {"blackout", "whiteout", "grayout", "blur"}
    assert {profile.name for profile in PDF_BACKGROUND_MODES} == {"white", "gray", "black", "blur"}
    for style in ("blackout", "whiteout", "grayout", "blur"):
        rendered = render_visual_redaction_text(text, decisions, style=style)
        assert "Alpha" not in rendered
        assert "Bravo" not in rendered
        assert normalize_redaction_style(style).token in rendered

    assert normalize_pdf_background("Black").name == "black"


def test_visual_variant_matrix_enumerates_all_background_and_redaction_combinations() -> None:
    _authority, segments, decisions = load_packet()

    matrix = build_visual_variant_matrix(
        segments,
        decisions,
        include_steganography=True,
        include_kmyth=True,
        kmyth_available=True,
        kmyth_summary="Kmyth available for tests.",
        kmyth_binary_dir="infrastructure/steganography/kmyth/bin",
    )
    unsealed_matrix = build_visual_variant_matrix(
        segments,
        decisions,
        include_steganography=True,
        include_kmyth=False,
        pdf_password_configured=True,
    )
    variants = matrix["variants"]

    assert matrix["variant_count"] == 16
    assert len(variants) == 16
    assert "pdf_info_metadata" in SECURITY_METHODS
    assert "sha256_sha512_hash_manifest" in matrix["security_methods"]
    assert "kmyth_tpm_sidecar_sealing_requested" in matrix["security_methods"]
    assert "kmyth_tpm_sidecar_sealing_available" in matrix["security_methods"]
    assert "pdf_password_encryption" in unsealed_matrix["security_methods"]
    assert "kmyth_tpm_sidecar_sealing_requested" not in unsealed_matrix["security_methods"]
    assert matrix["kmyth"]["requested"] is True
    assert matrix["kmyth"]["available"] is True
    assert matrix["kmyth"]["seal_artifacts"] == KMYTH_SEAL_ARTIFACTS
    assert set(matrix["redaction_styles"]) == {"blackout", "whiteout", "grayout", "blur"}
    assert set(matrix["pdf_backgrounds"]) == {"white", "gray", "black", "blur"}
    assert all("steganography_pdf" in variant for variant in variants)
    assert all("kmyth_sidecar_count" in variant for variant in variants)
    assert all("Alpha" not in str(row) for row in matrix["redaction_ledger"])

    with pytest.raises(ValueError, match="unsupported redaction style"):
        normalize_redaction_style("sepia")
    with pytest.raises(ValueError, match="unsupported PDF background"):
        normalize_pdf_background("transparent")


def test_dev_variant_output_verifier_enforces_filenames_and_hashes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _authority, segments, decisions = load_packet()
    matrix = build_visual_variant_matrix(segments, decisions, include_steganography=True, include_kmyth=False)
    variants: list[dict[str, object]] = []

    for raw_variant in matrix["variants"]:
        variant = dict(raw_variant)
        variant_id = str(variant["variant_id"])
        base_pdf = tmp_path / str(variant["base_pdf"])
        steganography_pdf = tmp_path / str(variant["steganography_pdf"])
        hash_manifest = tmp_path / str(variant["hash_manifest"])
        base_pdf.write_bytes(f"base proof {variant_id}\n".encode("utf-8"))
        steganography_pdf.write_bytes(f"steganography proof {variant_id}\n".encode("utf-8"))
        hash_manifest.write_text(
            json.dumps(
                {
                    "source_file": base_pdf.name,
                    "hashes": {
                        "sha256": _test_file_digest(base_pdf, "sha256"),
                        "sha512": _test_file_digest(base_pdf, "sha512"),
                    },
                    "steganography_applied": "true",
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        variant.update(
            {
                "base_pdf_bytes": base_pdf.stat().st_size,
                "base_pdf_sha256": _test_file_digest(base_pdf, "sha256"),
                "steganography_pdf_bytes": steganography_pdf.stat().st_size,
                "steganography_pdf_sha256": _test_file_digest(steganography_pdf, "sha256"),
                "hash_manifest_exists": True,
                "hash_manifest_sha256": _test_file_digest(hash_manifest, "sha256"),
            }
        )
        variants.append(variant)

    matrix = {**matrix, "variants": variants}
    (tmp_path / "variant_matrix.json").write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    monkeypatch.setattr(visuals, "_pdf_page_count", lambda _path: 1)

    summary = visuals.verify_dev_variant_outputs(tmp_path)

    assert summary["valid"] is True
    assert summary["pdf_count"] == 32
    assert summary["hash_manifest_count"] == 16
    assert summary["expected_variant_ids"] == visuals.expected_visual_variant_ids()
    assert set(summary["actual_variant_ids"]) == set(visuals.expected_visual_variant_ids())

    tampered = tmp_path / "blackout_on_white_steganography.pdf"
    tampered.write_bytes(b"tampered\n")
    failed = visuals.verify_dev_variant_outputs(tmp_path)

    assert failed["valid"] is False
    assert any("sha256 differs from matrix" in error for error in failed["errors"])


def test_kmyth_status_resolution_distinguishes_tool_and_seal_readiness(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeAvailability:
        seal_path = Path("/tmp/kmyth-seal")
        unseal_path = Path("/tmp/kmyth-unseal")

        def __init__(self, available: bool) -> None:
            self.available = available

        def summary(self) -> str:
            return "fake kmyth summary"

    infrastructure_module = ModuleType("infrastructure")
    steganography_module = ModuleType("infrastructure.steganography")
    setattr(infrastructure_module, "steganography", steganography_module)
    monkeypatch.setitem(sys.modules, "infrastructure", infrastructure_module)
    monkeypatch.setitem(sys.modules, "infrastructure.steganography", steganography_module)

    skipped = visuals._resolve_kmyth_status(
        include_kmyth=False,
        binary_dir=None,
        seal_probe_timeout_seconds=1,
    )
    assert skipped["requested"] is False
    assert skipped["summary"] == "Kmyth not requested."

    unavailable = FakeAvailability(False)
    setattr(steganography_module, "validate_kmyth_installation", lambda binary_dir=None: unavailable)
    missing = visuals._resolve_kmyth_status(
        include_kmyth=True,
        binary_dir="bin",
        seal_probe_timeout_seconds=1,
    )
    assert missing["available"] is False
    assert missing["tools_runnable"] is False

    available = FakeAvailability(True)
    setattr(steganography_module, "validate_kmyth_installation", lambda binary_dir=None: available)
    monkeypatch.setattr(visuals, "_kmyth_help_error", lambda tool_path: "")
    monkeypatch.setattr(visuals, "_kmyth_seal_probe_error", lambda tool_path, *, timeout_seconds: "no tpm")
    no_tpm = visuals._resolve_kmyth_status(
        include_kmyth=True,
        binary_dir="bin",
        seal_probe_timeout_seconds=1,
    )
    assert no_tpm["available"] is False
    assert no_tpm["tools_runnable"] is True
    assert "TPM seal probe failed" in str(no_tpm["summary"])

    monkeypatch.setattr(visuals, "_kmyth_seal_probe_error", lambda tool_path, *, timeout_seconds: "")
    ready = visuals._resolve_kmyth_status(
        include_kmyth=True,
        binary_dir="bin",
        seal_probe_timeout_seconds=1,
    )
    assert ready["available"] is True
    assert ready["tools_runnable"] is True


def test_kmyth_subprocess_helpers_and_sidecar_names(monkeypatch: pytest.MonkeyPatch) -> None:
    def successful_run(argv: list[str], **_kwargs: object) -> SimpleNamespace:
        if "--output" in argv:
            Path(argv[argv.index("--output") + 1]).write_text("sealed", encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(visuals.subprocess, "run", successful_run)
    assert visuals._kmyth_help_error(Path("kmyth-seal")) == ""
    assert visuals._kmyth_seal_probe_error(Path("kmyth-seal"), timeout_seconds=1) == ""

    monkeypatch.setattr(
        visuals.subprocess,
        "run",
        lambda _argv, **_kwargs: SimpleNamespace(returncode=1, stdout="", stderr="no tpm"),
    )
    assert "no tpm" in visuals._kmyth_help_error(Path("kmyth-seal"))
    assert "no tpm" in visuals._kmyth_seal_probe_error(Path("kmyth-seal"), timeout_seconds=1)

    sidecars = visuals._kmyth_sidecars_for(Path("base.pdf"), Path("base_steganography.pdf"))
    assert sidecars["hash_manifest"].name == "base.hashes.json.ski"
    assert sidecars["pdf"].name == "base_steganography.pdf.ski"


def test_visual_redacted_segments_are_source_safe() -> None:
    _authority, segments, decisions = load_packet()

    sanitized = visual_redacted_segments(segments, decisions, style="grayout")

    assert sanitized[2]["redaction_style"] == "grayout"
    assert "[GRAYOUT]" in str(sanitized[2]["text"])
    assert "Alpha" not in str(sanitized)


def test_valid_release_packet_is_releasable_with_warnings_for_residue() -> None:
    authority, segments, decisions = load_packet()

    audit = audit_release_packet(segments, decisions, release_authority=authority, mosaic_threshold=1.0)

    assert audit.releasable is True
    assert audit.redaction_coverage == 1.0
    assert audit.mosaic_risk_score > 0
    assert audit.release_safety_score < 1.0
    assert all(finding.severity == "warning" for finding in audit.findings)


def test_release_packet_exports_redacted_text_and_paragraph_audit() -> None:
    authority, segments, decisions = load_packet()

    packet = build_release_packet(segments, decisions, release_authority=authority, mosaic_threshold=1.0)
    sanitized = redacted_segments(segments, decisions)
    audit_rows = paragraph_audit_table(segments, decisions)

    assert packet["releasable"] is True
    assert packet["segments"] == sanitized
    assert sanitized[2]["text"].count("[REDACTED]") == 7
    assert "Alpha" not in str(sanitized[2]["text"])
    assert audit_rows[2]["decision_count"] == 7
    assert audit_rows[2]["above_ceiling"] is True
    assert packet["paragraph_audit"][2]["status"] == "reviewed"


def test_redaction_ledger_and_hash_manifest_do_not_expose_source_text() -> None:
    _authority, segments, decisions = load_packet()

    ledger = build_redaction_ledger(segments, decisions)
    hashes = segment_hash_manifest(segments, decisions)

    assert len(ledger) == len(decisions)
    assert all(row["valid_span"] is True for row in ledger)
    assert all(len(str(row["source_span_sha256"])) == 64 for row in ledger)
    assert "Alpha" not in str(ledger)
    assert len(hashes) == len(segments)
    assert all(len(row["source_sha256"]) == 64 for row in hashes)
    assert all(len(row["public_sha256"]) == 64 for row in hashes)


def test_residual_risk_detection_covers_common_public_release_leaks() -> None:
    policy = intelligence_release_policy()

    risks = detect_residual_risks(
        "Contact analyst@example.org from 192.0.2.10 near 38.8977, -77.0365. NOFORN HUMINT.",
        policy,
    )
    names = {risk["name"] for risk in risks}

    assert {"email_address", "ipv4_address", "coordinate_pair", "controlled_dissemination"} <= names
    assert "collection_discipline" in names


def test_comprehensive_release_packet_combines_audit_ledger_hashes_and_review_gate() -> None:
    authority, segments, decisions = load_packet()
    policy = intelligence_release_policy()
    reviews = load_reviews()

    packet = build_comprehensive_release_packet(
        segments,
        decisions,
        reviews,
        release_authority=authority,
        policy=policy,
    )

    assert packet["policy"] == "intelligence_release_review"
    assert packet["review_gate"]["approved"] is True
    assert packet["review_gate"]["approval_count"] == 3
    assert len(packet["redaction_ledger"]) == len(decisions)
    assert len(packet["hash_manifest"]) == len(segments)
    assert "Alpha" not in str(packet["segments"])
    assert packet["final_release_recommended"] is False


def test_comprehensive_release_packet_recommends_clean_release_when_policy_is_satisfied() -> None:
    segment = RedactionSegment("s1", "UNCLASSIFIED", "Public summary contains no controlled markers.")
    policy = intelligence_release_policy()
    reviews = [
        ReviewRecord("originator-a", "originator", "approve", "no source equities"),
        ReviewRecord("class-reviewer", "classification_reviewer", "approve", "classification checked"),
        ReviewRecord("release-board", "release_authority", "approve", "release authorized"),
    ]

    packet = build_comprehensive_release_packet(
        [segment],
        [],
        reviews,
        release_authority="release-board",
        policy=policy,
    )

    assert packet["releasable"] is True
    assert packet["review_gate"]["approved"] is True
    assert packet["findings"] == ()
    assert packet["final_release_recommended"] is True


def test_review_gate_blocks_missing_roles_rejections_and_bad_review_records() -> None:
    policy = intelligence_release_policy()
    reviews = [
        ReviewRecord("originator-a", "originator", "approve", "source equities reviewed"),
        ReviewRecord("class-reviewer", "classification_reviewer", "reject", "classification mismatch"),
        ReviewRecord("release-board", "release_authority", "changes_requested", ""),
        ReviewRecord("observer", "observer", "defer", "not a release decision"),
    ]

    gate = evaluate_review_gate(reviews, policy)
    codes = {finding.code for finding in gate.findings}

    assert gate.approved is False
    assert "release_rejected" in codes
    assert "review_without_rationale" in codes
    assert "bad_review_decision" in codes
    assert "insufficient_approvals" in codes
    assert "missing_required_role" in codes


def test_intelligence_taxonomy_accepts_sci_markings_with_release_authority() -> None:
    text = "HUMINT source Alpha reported compartmented details."
    segment = RedactionSegment("sci-1", "TOP SECRET//SCI", text, ("HUMINT",))
    decisions = [RedactionDecision("sci-1", 0, len(text), "source_identity")]

    audit = audit_release_packet(
        [segment],
        decisions,
        release_authority="classification-review-board",
        public_ceiling="SECRET",
        taxonomy=intelligence_agency_taxonomy(),
    )
    rows = paragraph_audit_table(
        [segment],
        decisions,
        public_ceiling="SECRET",
        taxonomy=intelligence_agency_taxonomy(),
    )

    assert audit.releasable is True
    assert rows[0]["above_ceiling"] is True
    assert rows[0]["residual_markers"] == ()


def test_missing_redactions_block_above_ceiling_segment() -> None:
    _authority, segments, _decisions = load_packet()

    audit = audit_release_packet(segments, [], release_authority="review-board")
    codes = {finding.code for finding in audit.findings}

    assert audit.releasable is False
    assert "above_ceiling_unredacted" in codes
    assert "source_control_uncovered" in codes


def test_missing_release_authority_is_error() -> None:
    authority, segments, decisions = load_packet()
    assert authority

    audit = audit_release_packet(segments, decisions, release_authority="")

    assert audit.releasable is False
    assert "missing_release_authority" in {finding.code for finding in audit.findings}


def test_bad_decision_bounds_and_reason_raise_for_direct_redaction() -> None:
    with pytest.raises(ValueError, match="invalid redaction bounds"):
        redact_text("short", [RedactionDecision("s1", 4, 99, "privacy")])
    with pytest.raises(ValueError, match="unsupported redaction reason"):
        redact_text("short", [RedactionDecision("s1", 0, 2, "unknown")])
    with pytest.raises(ValueError, match="overlapping redaction decisions"):
        redact_text(
            "abcdef",
            [
                RedactionDecision("s1", 0, 4, "privacy"),
                RedactionDecision("s1", 2, 5, "legal_privilege"),
            ],
        )


def test_packet_audit_converts_bad_decisions_to_findings() -> None:
    segment = RedactionSegment("s1", "UNCLASSIFIED", "public text")
    decisions = [RedactionDecision("s1", 1, 20, "privacy")]

    audit = audit_release_packet([segment], decisions, release_authority="review-board")

    assert audit.releasable is False
    assert "bad_redaction_decision" in {finding.code for finding in audit.findings}


def test_orphan_redaction_decisions_are_reported() -> None:
    segment = RedactionSegment("s1", "UNCLASSIFIED", "public text")
    decision = RedactionDecision("missing", 0, 4, "privacy")

    audit = audit_release_packet([segment], [decision], release_authority="review-board")

    assert audit.releasable is False
    assert "orphan_redaction_decision" in {finding.code for finding in audit.findings}


def test_redaction_ledger_marks_invalid_or_orphan_spans_without_raising() -> None:
    segment = RedactionSegment("s1", "UNCLASSIFIED", "public text")
    decisions = [
        RedactionDecision("s1", 2, 99, "privacy"),
        RedactionDecision("missing", 0, 4, "privacy"),
    ]

    ledger = build_redaction_ledger([segment], decisions)

    assert [row["valid_span"] for row in ledger] == [False, False]
    assert all(row["source_span_sha256"] == "" for row in ledger)


def test_unknown_classification_and_high_mosaic_risk_are_reported() -> None:
    segment = RedactionSegment("s1", "UNKNOWN", "HUMINT source selector location 2026-07-09")

    audit = audit_release_packet([segment], [], release_authority="review-board", mosaic_threshold=0.0)
    codes = {finding.code for finding in audit.findings}

    assert audit.releasable is False
    assert "unknown_classification" in codes
    assert "mosaic_risk" in codes


def _test_file_digest(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    digest.update(path.read_bytes())
    return digest.hexdigest()
