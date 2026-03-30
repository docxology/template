"""Tests for infrastructure.llm.core.log_preview."""

from infrastructure.llm.core.log_preview import preview_for_log


def test_preview_for_log_empty() -> None:
    assert preview_for_log("") == ""


def test_preview_for_log_short_untouched() -> None:
    assert preview_for_log("hello world") == "hello world"


def test_preview_for_log_collapses_whitespace() -> None:
    assert preview_for_log("a\n\tb   c") == "a b c"


def test_preview_for_log_truncates() -> None:
    long = "x" * 100
    out = preview_for_log(long, max_chars=10)
    assert len(out) == 10
    assert out.endswith("…")
