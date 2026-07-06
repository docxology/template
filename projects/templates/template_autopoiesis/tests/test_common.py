"""Tests for src/common.py — trunc() and the CheckResult/CheckReport dataclasses."""
from __future__ import annotations

from src.common import CheckReport, CheckResult, trunc


# ---------------------------------------------------------------------------
# trunc()
# ---------------------------------------------------------------------------


def test_trunc_short_text_unchanged():
    assert trunc("short", max_len=80) == "short"


def test_trunc_exact_length_unchanged():
    text = "x" * 80
    assert trunc(text, max_len=80) == text


def test_trunc_long_text_clips_with_ellipsis():
    text = "x" * 100
    result = trunc(text, max_len=80)
    assert len(result) == 80
    assert result.endswith("…")
    assert result == "x" * 79 + "…"


def test_trunc_default_max_len_is_80():
    text = "y" * 90
    result = trunc(text)
    assert len(result) == 80


# ---------------------------------------------------------------------------
# CheckResult / CheckReport
# ---------------------------------------------------------------------------


def test_check_result_fields():
    r = CheckResult(name="foo", passed=True, detail="ok")
    assert r.name == "foo"
    assert r.passed is True
    assert r.detail == "ok"


def test_check_report_all_passed_true():
    report = CheckReport(
        child_root="child",
        checks=(CheckResult("a", True), CheckResult("b", True)),
    )
    assert report.all_passed is True
    assert report.failed == ()


def test_check_report_all_passed_false_and_failed_subset():
    passing = CheckResult("a", True)
    failing_one = CheckResult("b", False, detail="broke")
    failing_two = CheckResult("c", False, detail="also broke")
    report = CheckReport(child_root="child", checks=(passing, failing_one, failing_two))
    assert report.all_passed is False
    assert report.failed == (failing_one, failing_two)
