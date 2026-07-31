"""Tests for ``infrastructure.core.public_matrix_receipt``.

Covers the deterministic JSON round-trip, the content digest, and release
negative controls including missing projects, coverage floors, and output
isolation. All checks run against constructed payloads (no subprocess needed).
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.public_matrix_receipt import (
    PublicMatrixLaneResult,
    PublicMatrixReceipt,
    build_public_matrix_receipt,
    determine_worker_info,
)

ROSTER = ("templates/template_a", "templates/template_b", "templates/template_c")


def _passing_lane(name: str, coverage: float = 95.0, floor: int = 90) -> PublicMatrixLaneResult:
    return PublicMatrixLaneResult(
        project_name=name,
        declared_floor=floor,
        exit_code=0,
        timed_out=False,
        coverage_percent=coverage,
        output_isolation_ok=True,
    )


def _receipt(lanes: tuple[PublicMatrixLaneResult, ...], **overrides) -> PublicMatrixReceipt:
    return build_public_matrix_receipt(
        roster_revision="abc123",
        profile="quick",
        marker_expression="not slow and not long_running",
        worker_info="outer=serial, inner=none",
        lanes=lanes,
        combined_coverage_percent=94.0,
        combined_floor=75,
        overall_exit=0,
        **overrides,
    )


def test_receipt_round_trip_is_deterministic(tmp_path: Path) -> None:
    receipt = _receipt(tuple(_passing_lane(name) for name in ROSTER))
    path = tmp_path / "matrix.json"

    receipt.write(path)
    first = path.read_bytes()
    receipt.write(path)
    second = path.read_bytes()

    assert first == second, "repeated writes must be byte-identical"
    loaded = PublicMatrixReceipt.read(path)
    assert loaded == receipt
    assert loaded.lanes == receipt.lanes


def test_receipt_digest_ignores_generated_at_and_tracks_content(tmp_path: Path) -> None:
    base = _receipt(tuple(_passing_lane(name) for name in ROSTER))
    different_time = PublicMatrixReceipt(
        roster_revision=base.roster_revision,
        profile=base.profile,
        marker_expression=base.marker_expression,
        worker_info=base.worker_info,
        generated_at="2026-07-31T00:00:00Z",
        lanes=base.lanes,
        combined_coverage_percent=base.combined_coverage_percent,
        combined_floor=base.combined_floor,
        overall_exit=base.overall_exit,
    )
    assert base.digest() == different_time.digest(), "generated_at must not enter the digest"

    mutated = _receipt(
        tuple(
            _passing_lane(name, coverage=99.0) if name == "templates/template_a" else _passing_lane(name)
            for name in ROSTER
        )
    )
    assert base.digest() != mutated.digest(), "content change must change the digest"


def test_validate_passes_for_full_green_receipt() -> None:
    receipt = _receipt(tuple(_passing_lane(name) for name in ROSTER))
    assert receipt.validate(ROSTER) == []


def test_validate_rejects_missing_project_result() -> None:
    """Negative control: a roster entry with no lane result must be rejected."""
    receipt = _receipt(tuple(_passing_lane(name) for name in ROSTER[:2]))
    errors = receipt.validate(ROSTER)
    assert any("MISSING-PROJECT" in error and "templates/template_c" in error for error in errors)


def test_validate_rejects_coverage_floor_failure() -> None:
    """Negative control: measured coverage below the declared floor must fail."""
    lanes = (
        _passing_lane("templates/template_a"),
        _passing_lane("templates/template_b", coverage=89.0, floor=90),
        _passing_lane("templates/template_c"),
    )
    receipt = _receipt(lanes)
    errors = receipt.validate(ROSTER)
    assert any("COVERAGE-FLOOR" in error and "templates/template_b" in error and "89.00%" in error for error in errors)


def test_validate_rejects_timeout_and_nonzero_exit() -> None:
    timed_out = PublicMatrixLaneResult(
        project_name="templates/template_a",
        declared_floor=90,
        exit_code=124,
        timed_out=True,
        coverage_percent=None,
        output_isolation_ok=True,
    )
    failed = PublicMatrixLaneResult(
        project_name="templates/template_b",
        declared_floor=90,
        exit_code=1,
        timed_out=False,
        coverage_percent=90.0,
        output_isolation_ok=True,
    )
    receipt = _receipt((timed_out, failed, _passing_lane("templates/template_c")))
    errors = receipt.validate(ROSTER)
    assert any("TIMEOUT" in error and "templates/template_a" in error for error in errors)
    assert any("EXIT-STATUS" in error and "templates/template_b" in error for error in errors)


def test_validate_rejects_output_tree_drift() -> None:
    """Negative control: a test-generated output change must fail validation."""
    drifted = PublicMatrixLaneResult(
        project_name="templates/template_b",
        declared_floor=90,
        exit_code=0,
        timed_out=False,
        coverage_percent=95.0,
        output_isolation_ok=False,
    )
    receipt = _receipt(
        (
            _passing_lane("templates/template_a"),
            drifted,
            _passing_lane("templates/template_c"),
        )
    )

    assert receipt.validate(ROSTER) == ["OUTPUT-ISOLATION: project 'templates/template_b' changed output/"]


def test_validate_ignores_missing_floor_or_missing_coverage() -> None:
    """No floor or no measured coverage must not produce a floor error."""
    no_floor = PublicMatrixLaneResult(
        project_name="templates/template_a",
        declared_floor=None,
        exit_code=0,
        timed_out=False,
        coverage_percent=80.0,
        output_isolation_ok=True,
    )
    no_coverage = PublicMatrixLaneResult(
        project_name="templates/template_b",
        declared_floor=90,
        exit_code=0,
        timed_out=False,
        coverage_percent=None,
        output_isolation_ok=True,
    )
    receipt = _receipt((no_floor, no_coverage, _passing_lane("templates/template_c")))
    assert receipt.validate(ROSTER) == []


def test_determine_worker_info_describes_concurrency() -> None:
    assert determine_worker_info(None, None) == "outer=serial, inner=none"
    assert determine_worker_info("auto", "4") == "outer=auto, inner=4"
    assert determine_worker_info("serial", None) == "outer=serial, inner=none"


def test_receipt_accepts_unknown_roster_revision() -> None:
    receipt = PublicMatrixReceipt(
        roster_revision="unknown",
        profile="quick",
        marker_expression="not slow and not long_running",
        worker_info="outer=serial, inner=none",
        generated_at="",
        lanes=tuple(_passing_lane(name) for name in ROSTER),
        combined_coverage_percent=94.0,
        combined_floor=75,
        overall_exit=0,
    )
    assert receipt.validate(ROSTER) == []
    assert receipt.roster_revision == "unknown"
