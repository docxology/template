from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from types import SimpleNamespace

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
    summary = visuals.verify_dev_variant_outputs(tmp_path, page_counter=lambda _path: 1)

    assert summary["valid"] is True
    assert summary["pdf_count"] == 32
    assert summary["hash_manifest_count"] == 16
    assert summary["expected_variant_ids"] == visuals.expected_visual_variant_ids()
    assert set(summary["actual_variant_ids"]) == set(visuals.expected_visual_variant_ids())

    tampered = tmp_path / "blackout_on_white_steganography.pdf"
    tampered.write_bytes(b"tampered\n")
    failed = visuals.verify_dev_variant_outputs(tmp_path, page_counter=lambda _path: 1)

    assert failed["valid"] is False
    assert any("sha256 differs from matrix" in error for error in failed["errors"])


def test_kmyth_status_resolution_distinguishes_tool_and_seal_readiness() -> None:
    class FakeAvailability:
        seal_path = Path("/tmp/kmyth-seal")  # nosec B108 - fake path constant on a test double, never touched
        unseal_path = Path("/tmp/kmyth-unseal")  # nosec B108 - fake path constant on a test double, never touched

        def __init__(self, available: bool) -> None:
            self.available = available

        def summary(self) -> str:
            return "fake kmyth summary"

    skipped = visuals._resolve_kmyth_status(
        include_kmyth=False,
        binary_dir=None,
        seal_probe_timeout_seconds=1,
    )
    assert skipped["requested"] is False
    assert skipped["summary"] == "Kmyth not requested."

    unavailable = FakeAvailability(False)
    missing = visuals._resolve_kmyth_status(
        include_kmyth=True,
        binary_dir="bin",
        seal_probe_timeout_seconds=1,
        installation_validator=lambda binary_dir=None: unavailable,
    )
    assert missing["available"] is False
    assert missing["tools_runnable"] is False

    available = FakeAvailability(True)
    no_tpm = visuals._resolve_kmyth_status(
        include_kmyth=True,
        binary_dir="bin",
        seal_probe_timeout_seconds=1,
        installation_validator=lambda binary_dir=None: available,
        help_checker=lambda tool_path: "",
        seal_probe=lambda tool_path, *, timeout_seconds: "no tpm",
    )
    assert no_tpm["available"] is False
    assert no_tpm["tools_runnable"] is True
    assert "TPM seal probe failed" in str(no_tpm["summary"])

    ready = visuals._resolve_kmyth_status(
        include_kmyth=True,
        binary_dir="bin",
        seal_probe_timeout_seconds=1,
        installation_validator=lambda binary_dir=None: available,
        help_checker=lambda tool_path: "",
        seal_probe=lambda tool_path, *, timeout_seconds: "",
    )
    assert ready["available"] is True
    assert ready["tools_runnable"] is True


def test_kmyth_subprocess_helpers_and_sidecar_names() -> None:
    def successful_run(argv: list[str], **_kwargs: object) -> SimpleNamespace:
        if "--output" in argv:
            Path(argv[argv.index("--output") + 1]).write_text("sealed", encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    assert visuals._kmyth_help_error(Path("kmyth-seal"), runner=successful_run) == ""
    assert visuals._kmyth_seal_probe_error(Path("kmyth-seal"), timeout_seconds=1, runner=successful_run) == ""

    def failed_run(_argv, **_kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="no tpm")

    assert "no tpm" in visuals._kmyth_help_error(Path("kmyth-seal"), runner=failed_run)
    assert "no tpm" in visuals._kmyth_seal_probe_error(Path("kmyth-seal"), timeout_seconds=1, runner=failed_run)

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
        "Contact analyst@example.org on 2031-04-05 from 192.0.2.10 near 38.8977, -77.0365. NOFORN HUMINT.",
        policy,
    )
    names = {risk["name"] for risk in risks}

    assert {"email_address", "ipv4_address", "coordinate_pair", "controlled_dissemination"} <= names
    assert "iso_calendar_date" in names
    assert "collection_discipline" in names


def test_secret_fixture_redacts_both_collection_platform_mentions() -> None:
    """Repeated operational nouns need distinct decisions, not first-match coverage."""
    _authority, segments, decisions = load_packet()
    segment = next(item for item in segments if item.id == "s4")
    redacted = redact_text(segment.text, [item for item in decisions if item.segment_id == "s4"])

    assert "platform" not in redacted.lower()


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


def test_source_control_uncovered_counts_each_distinct_control() -> None:
    """A single source_identity decision must not vacuously cover every control.

    Regression guard for a bug where `_check_decisions` used
    `any(decision.reason == "source_identity" ...)`, so one matching decision
    anywhere in the segment was treated as covering *all* of that segment's
    source_controls regardless of how many distinct controls existed.
    """
    segment = RedactionSegment(
        "multi-1",
        "SECRET",
        "Alpha reported to Bravo about the mission.",
        ("HUMINT", "SIGINT"),
    )

    # Only one covering decision for two distinct controls: must be flagged.
    under_covered = [RedactionDecision("multi-1", 0, 5, "source_identity")]
    audit = audit_release_packet([segment], under_covered, release_authority="review-board")
    codes = [finding.code for finding in audit.findings]
    assert codes.count("source_control_uncovered") == 1

    # One covering decision per control: fully covered, no findings.
    fully_covered = [
        RedactionDecision("multi-1", 0, 5, "source_identity"),
        RedactionDecision("multi-1", 19, 24, "source_identity"),
    ]
    audit_ok = audit_release_packet([segment], fully_covered, release_authority="review-board")
    assert "source_control_uncovered" not in {finding.code for finding in audit_ok.findings}


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


def test_paragraph_audit_keeps_original_text_when_decisions_are_invalid() -> None:
    segment = RedactionSegment("s1", "UNCLASSIFIED", "Contact analyst@example.org for details.")
    decisions = [RedactionDecision("s1", 5, 999, "privacy")]

    rows = paragraph_audit_table([segment], decisions)

    assert rows[0]["decision_count"] == 1
    assert rows[0]["redacted_length"] == len(segment.text)
    assert "email_address" in rows[0]["residual_markers"]


def test_hash_manifest_uses_empty_public_hash_when_redaction_fails() -> None:
    segment = RedactionSegment("s1", "UNCLASSIFIED", "public text")
    decisions = [RedactionDecision("s1", 5, 999, "privacy")]

    rows = segment_hash_manifest([segment], decisions)

    assert rows[0]["source_sha256"] == hashlib.sha256(segment.text.encode("utf-8")).hexdigest()
    assert rows[0]["public_sha256"] == hashlib.sha256(b"").hexdigest()


def test_duplicate_segment_ids_are_reported_as_errors() -> None:
    segments = [
        RedactionSegment("s1", "UNCLASSIFIED", "first copy"),
        RedactionSegment("s1", "UNCLASSIFIED", "second copy"),
    ]

    audit = audit_release_packet(segments, [], release_authority="review-board")

    assert audit.releasable is False
    assert "duplicate_segment_id" in {finding.code for finding in audit.findings}


def test_segment_s5_redaction_spans_leave_no_stray_letter_beside_a_box() -> None:
    """Regression pin for a fixed off-by-a-few-characters offset bug.

    Segment s5's redaction decisions previously started/ended a few characters
    short of the real word boundaries. The leak was NOT the whole word
    surviving intact (the trailing/leading characters were still consumed by
    the neighbouring box) — it was single stray letters glued directly onto a
    "[REDACTED]" marker, e.g. "S[REDACTED]p[REDACTED]" instead of a clean
    "[REDACTED] [REDACTED]" for "SIGINT platform". A substring check for the
    full words ("SIGINT" not in sanitized) would NOT have caught this, since
    the full word was never intact even in the buggy version. This test binds
    directly to the shipped fixture so a future offset regression in
    data/example_segments.json — of any size, including a single character —
    is caught even though the coarser 6+ character token scan in
    test_visuals_proofs.py would miss it.
    """
    release_authority, segments, decisions = load_packet()
    segment = next(item for item in segments if item.id == "s5")
    segment_decisions = [decision for decision in decisions if decision.segment_id == "s5"]

    sanitized = redact_text(segment.text, segment_decisions)

    assert not re.search(r"[A-Za-z]\[REDACTED\]", sanitized), sanitized
    assert not re.search(r"\[REDACTED\][A-Za-z]", sanitized), sanitized


def _test_file_digest(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    digest.update(path.read_bytes())
    return digest.hexdigest()
