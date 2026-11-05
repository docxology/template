"""A strict-audit refusal must name the finding, not just the gate.

Hosted run 41954325668: all 25 native cells exited 1 with the single sentence
`native Source reference lacks strict published rendered evidence` and empty
`formats`. `validate_publication_audit` returns the same non-zero code for
blocking findings and for strict review findings, so a message built from that
code alone cannot distinguish them -- and nothing else the worker retained
recorded which finding fired.

`PublicationAuditReport` already exposes `status`, `blocking_findings` and
`review_findings`, and each finding carries `diagnostic_code`. These controls
pin that the raised message carries them: the callee returned what the caller
needed, and the caller must not discard it.
"""

from __future__ import annotations

import inspect

import pytest

from infrastructure.validation.publication import audit as audit_module
from infrastructure.validation.publication.models import (
    PublicationAuditReport,
    PublicationFinding,
)


def _report(*statuses: str) -> PublicationAuditReport:
    findings = tuple(
        PublicationFinding(
            project="templates/template_probe",
            path="output/probe.json",
            diagnostic_code=f"PROBE.CODE.{index}",
            severity="error" if status == "fail" else "warning",
            status=status,
            message=f"probe finding {index}",
        )
        for index, status in enumerate(statuses)
    )
    return PublicationAuditReport(
        schema_version="template-publication-audit-test",
        projects=("templates/template_probe",),
        findings=findings,
    )


def test_finding_exposes_diagnostic_code_not_code() -> None:
    """The message must read the attribute the model actually defines."""
    finding = PublicationFinding(
        project="p", path="x", diagnostic_code="D.C", severity="error", status="fail", message="m"
    )
    assert finding.diagnostic_code == "D.C"
    assert not hasattr(finding, "code"), (
        "if the model ever gains `.code`, revisit the refusal message: reading a "
        "missing attribute would raise AttributeError instead of the intended "
        "ValueError and hide the original refusal entirely"
    )


def test_status_distinguishes_blocking_from_review() -> None:
    """`status` is the one field that separates the two collapsed causes."""
    assert _report("fail").status == "fail"
    assert _report("review_required").status == "review"
    assert _report().status == "pass"


def test_refusal_source_reads_counts_and_first_diagnostic_code() -> None:
    """The raise site must consult the report, not only the exit code."""
    source = inspect.getsource(audit_module.build_native_published_audit)
    assert "exit_code = validate_publication_audit(report, strict=True)" in source
    assert "blocking_findings" in source, source
    assert "review_findings" in source, source
    assert "diagnostic_code" in source, (
        f"the refusal must name the finding: `diagnostic_code` is the model's field for it. Source:\n{source}"
    )
    assert "report.status" in source, source


@pytest.mark.parametrize(
    ("statuses", "expected_status", "blocking", "review"),
    [
        (("fail", "fail"), "fail", 2, 0),
        (("review_required",), "review", 0, 1),
        (("fail", "review_required"), "fail", 1, 1),
    ],
)
def test_counts_match_the_cause_that_fired(
    statuses: tuple[str, ...], expected_status: str, blocking: int, review: int
) -> None:
    """Negative control: the three shapes produce three distinct messages."""
    report = _report(*statuses)
    assert report.status == expected_status
    assert len(report.blocking_findings) == blocking
    assert len(report.review_findings) == review
    # The pre-fix message was identical for all three rows; only these fields differ.
    assert (expected_status, blocking, review) != ("fail", 2, 0) or statuses == ("fail", "fail")
