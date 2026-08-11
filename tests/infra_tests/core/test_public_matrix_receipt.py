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
    build_public_matrix_cache_key,
    build_public_matrix_receipt,
    determine_worker_info,
)

ROSTER = ("templates/template_a", "templates/template_b", "templates/template_c")


def _lane_metadata() -> dict:
    """Return the required execution metadata for a synthetic lane."""
    return {
        "duration_seconds": 1.0,
        "cache_key": "lane-cache",
        "output_isolation_digest": "digest",
        "resource_limits": {"timeout_seconds": 120},
    }


def _passing_lane(name: str, coverage: float = 95.0, floor: int = 90) -> PublicMatrixLaneResult:
    return PublicMatrixLaneResult(
        project_name=name,
        declared_floor=floor,
        exit_code=0,
        timed_out=False,
        coverage_percent=coverage,
        output_isolation_ok=True,
        collection_count=1,
        **_lane_metadata(),
    )


def _receipt(lanes: tuple[PublicMatrixLaneResult, ...], **overrides) -> PublicMatrixReceipt:
    fields = {
        "phase_durations": {"project_matrix": 1.0, "coverage_combine": 1.0, "coverage_gate": 1.0},
        "cache_key": "receipt-cache",
        "cache_inputs": {"revision": "abc123"},
        "combined_coverage_percent": 94.0,
        "combined_floor": 75,
        "overall_exit": 0,
    }
    fields.update(overrides)
    return build_public_matrix_receipt(
        roster_revision="abc123",
        profile="quick",
        marker_expression="not slow and not long_running",
        worker_info="outer=serial, inner=none",
        lanes=lanes,
        **fields,
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
    assert loaded.schema_version == "template-public-matrix/v3"


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
        phase_durations=base.phase_durations,
        cache_key=base.cache_key,
        cache_inputs=base.cache_inputs,
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
        **_lane_metadata(),
    )
    failed = PublicMatrixLaneResult(
        project_name="templates/template_b",
        declared_floor=90,
        exit_code=1,
        timed_out=False,
        coverage_percent=90.0,
        output_isolation_ok=True,
        **_lane_metadata(),
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
        collection_count=1,
        **_lane_metadata(),
    )
    receipt = _receipt(
        (
            _passing_lane("templates/template_a"),
            drifted,
            _passing_lane("templates/template_c"),
        )
    )

    assert receipt.validate(ROSTER) == ["OUTPUT-ISOLATION: project 'templates/template_b' changed output/"]


def test_validate_allows_lane_without_floor_but_requires_combined_coverage() -> None:
    """A lane may omit a floor, but a passing receipt needs combined coverage."""
    no_floor = PublicMatrixLaneResult(
        project_name="templates/template_a",
        declared_floor=None,
        exit_code=0,
        timed_out=False,
        coverage_percent=80.0,
        output_isolation_ok=True,
        collection_count=1,
        **_lane_metadata(),
    )
    no_coverage = PublicMatrixLaneResult(
        project_name="templates/template_b",
        declared_floor=90,
        exit_code=0,
        timed_out=False,
        coverage_percent=None,
        output_isolation_ok=True,
        collection_count=1,
        **_lane_metadata(),
    )
    receipt = _receipt((no_floor, no_coverage, _passing_lane("templates/template_c")))
    assert receipt.validate(ROSTER) == []

    missing_combined = _receipt(
        (no_floor, no_coverage, _passing_lane("templates/template_c")),
        combined_coverage_percent=None,
    )
    assert any("MISSING-COMBINED-COVERAGE" in error for error in missing_combined.validate(ROSTER))


def test_validate_rejects_overall_exit_combined_floor_and_unexpected_lane() -> None:
    receipt = _receipt(
        tuple(_passing_lane(name) for name in ROSTER) + (_passing_lane("templates/extra"),),
        overall_exit=1,
        combined_coverage_percent=74.0,
    )
    errors = receipt.validate(ROSTER)
    assert any("OVERALL-EXIT" in error for error in errors)
    assert any("COMBINED-COVERAGE-FLOOR" in error for error in errors)
    assert any("UNEXPECTED-PROJECT" in error for error in errors)


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
        phase_durations={"project_matrix": 1.0},
        cache_key="receipt-cache",
        cache_inputs={"revision": "unknown"},
    )
    assert receipt.validate(ROSTER) == []
    assert receipt.roster_revision == "unknown"


def test_receipt_records_phase_and_cache_metadata() -> None:
    receipt = _receipt(
        tuple(_passing_lane(name) for name in ROSTER),
        phase_durations={"project_matrix": 12.5},
        collection_counts={"templates/template_a": 10},
        skip_reasons={"templates/optional": "tool unavailable"},
        cache_key="abc",
    )
    assert receipt.phase_durations == {"project_matrix": 12.5}
    assert receipt.collection_counts["templates/template_a"] == 10
    assert receipt.skip_reasons["templates/optional"] == "tool unavailable"
    assert receipt.cache_key == "abc"


def test_validate_rejects_non_vacuous_zero_collection() -> None:
    lane = PublicMatrixLaneResult(
        project_name="templates/template_a",
        declared_floor=90,
        exit_code=0,
        timed_out=False,
        coverage_percent=95.0,
        output_isolation_ok=True,
        collection_count=0,
        **_lane_metadata(),
    )
    receipt = _receipt((lane, _passing_lane("templates/template_b"), _passing_lane("templates/template_c")))
    assert receipt.validate(ROSTER) == [
        "EMPTY-COLLECTION: project 'templates/template_a' reported zero collected tests"
    ]


def test_validate_accepts_explicit_skip_reason_metadata() -> None:
    lane = PublicMatrixLaneResult(
        project_name="templates/template_a",
        declared_floor=None,
        exit_code=0,
        timed_out=False,
        coverage_percent=None,
        output_isolation_ok=True,
        skip_reason="optional tool unavailable",
    )
    receipt = _receipt((lane, _passing_lane("templates/template_b"), _passing_lane("templates/template_c")))
    assert receipt.validate(ROSTER) == []


def test_matrix_cache_key_is_order_independent_but_plan_bound() -> None:
    first = build_public_matrix_cache_key(
        roster_revision="abc",
        profile="quick",
        marker_expression="not slow",
        worker_info="outer=serial, inner=none",
        project_names=("templates/b", "templates/a"),
    )
    reordered = build_public_matrix_cache_key(
        roster_revision="abc",
        profile="quick",
        marker_expression="not slow",
        worker_info="outer=serial, inner=none",
        project_names=("templates/a", "templates/b"),
    )
    changed = build_public_matrix_cache_key(
        roster_revision="abc",
        profile="release",
        marker_expression="not slow",
        worker_info="outer=serial, inner=none",
        project_names=("templates/a", "templates/b"),
    )
    assert first == reordered
    assert first != changed
