"""Tests for scorecard math and the text/JSON renderers."""

import json

from infrastructure.doctor.models import (
    DoctorReport,
    Finding,
    Severity,
)
from infrastructure.doctor.reporter import (
    EXIT_CRITICAL,
    EXIT_ERROR,
    EXIT_HEALTHY,
    EXIT_WARN,
    compute_exit_code,
    render_report_json,
    render_report_text,
)
from infrastructure.doctor.scorecard import (
    DIMENSIONS,
    compute_scorecard,
    dimension_for_code,
)


def _finding(code: str, severity: Severity, healthy: bool) -> Finding:
    return Finding(
        code=code,
        title=code,
        severity=severity,
        healthy=healthy,
        description="",
    )


def test_dimension_for_code_maps_prefix():
    assert dimension_for_code("DOC101") == "environment"
    assert dimension_for_code("DOC201[x]") == "project_layout"
    assert dimension_for_code("DOC601") == "safety_surface"
    assert dimension_for_code("DOC999") == "uncategorised"


def test_scorecard_healthy_findings_score_100():
    findings = [_finding("DOC101", Severity.INFO, True)]
    overall, dims = compute_scorecard(findings)
    assert overall == 100.0
    assert dims["environment"] == 100.0


def test_scorecard_warn_deducts_15_per_finding():
    findings = [
        _finding("DOC301", Severity.WARN, False),
        _finding("DOC301", Severity.WARN, False),
    ]
    overall, dims = compute_scorecard(findings)
    assert dims["hygiene"] == pytest_approx(70.0)


def test_scorecard_critical_deducts_70():
    findings = [_finding("DOC601", Severity.CRITICAL, False)]
    _, dims = compute_scorecard(findings)
    assert dims["safety_surface"] == pytest_approx(30.0)


def test_scorecard_clamps_to_zero():
    findings = [_finding("DOC601", Severity.CRITICAL, False)] * 5
    _, dims = compute_scorecard(findings)
    assert dims["safety_surface"] == 0.0


def test_dimensions_match_weights():
    # Every weighted dimension must also be present in DIMENSIONS as a
    # value (the codes can be many but the dimension names must align).
    from infrastructure.doctor.scorecard import DIMENSION_WEIGHTS

    assert set(DIMENSION_WEIGHTS).issubset(set(DIMENSIONS.values()))


# ---------------------------------------------------------------------------
# Exit codes
# ---------------------------------------------------------------------------


def test_exit_code_healthy_when_all_ok():
    findings = [_finding("DOC101", Severity.INFO, True)]
    assert compute_exit_code(findings) == EXIT_HEALTHY


def test_exit_code_warn():
    findings = [_finding("DOC301", Severity.WARN, False)]
    assert compute_exit_code(findings) == EXIT_WARN


def test_exit_code_error():
    findings = [
        _finding("DOC101", Severity.INFO, True),
        _finding("DOC202", Severity.ERROR, False),
    ]
    assert compute_exit_code(findings) == EXIT_ERROR


def test_exit_code_critical():
    findings = [_finding("DOC601", Severity.CRITICAL, False)]
    assert compute_exit_code(findings) == EXIT_CRITICAL


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------


def test_text_renderer_shows_score_and_findings():
    findings = [_finding("DOC101", Severity.INFO, True)]
    overall, dims = compute_scorecard(findings)
    report = DoctorReport(
        findings=findings,
        applied=[],
        skipped=[],
        failed=[],
        overall_score=overall,
        dimension_scores=dims,
        exit_code=EXIT_HEALTHY,
    )
    out = render_report_text(report)
    assert "infrastructure.doctor" in out
    assert "score" in out
    assert "DOC101" in out
    assert "[ OK ]" in out


def test_json_renderer_is_parseable_and_has_stable_keys():
    findings = [_finding("DOC301", Severity.WARN, False)]
    overall, dims = compute_scorecard(findings)
    report = DoctorReport(
        findings=findings,
        applied=[],
        skipped=[],
        failed=[],
        overall_score=overall,
        dimension_scores=dims,
        exit_code=EXIT_WARN,
    )
    payload = json.loads(render_report_json(report))
    assert {"findings", "applied", "skipped", "failed", "overall_score", "dimension_scores", "exit_code"} <= set(
        payload
    )
    assert payload["exit_code"] == EXIT_WARN
    assert payload["findings"][0]["code"] == "DOC301"
    assert payload["findings"][0]["severity"] == "warn"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def pytest_approx(value: float, tol: float = 0.001):
    """Minimal local approx helper to avoid importing pytest.approx at top
    level (keeps the file lint-clean if someone reads it standalone)."""
    import pytest

    return pytest.approx(value, abs=tol)
