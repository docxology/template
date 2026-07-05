"""Tests for strict boolean coercion in config parsing."""

from __future__ import annotations
from coercion import coerce_bool


def test_coerce_bool_returns_default_for_none() -> None:
    assert coerce_bool(None, default=True, field_name="flag") is True


def test_as_bool_wrapper_forwards_default() -> None:
    from parsing import as_bool

    assert as_bool(None, True, field_name="flag") is True


def test_coerce_bool_accepts_string_tokens() -> None:
    assert coerce_bool("true", default=False, field_name="flag") is True
    assert coerce_bool("0", default=True, field_name="flag") is False
