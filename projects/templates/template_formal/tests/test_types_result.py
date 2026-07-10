"""Behavioral tests for the Result[T, E] ADT (ISC-3, ISC-5)."""

from __future__ import annotations

from template_formal.types.result import Err, Ok, and_then, is_ok, map_result, unwrap_or


def test_ok_carries_its_value_and_tag() -> None:
    result = Ok(42)
    assert result.value == 42
    assert result.tag == "ok"
    assert is_ok(result) is True


def test_err_carries_its_error_and_tag() -> None:
    result = Err("boom")
    assert result.error == "boom"
    assert result.tag == "err"
    assert is_ok(result) is False


def test_map_result_transforms_ok_only() -> None:
    ok_mapped = map_result(Ok(3), lambda x: x * 2)
    assert isinstance(ok_mapped, Ok)
    assert ok_mapped.value == 6

    err_mapped = map_result(Err("boom"), lambda x: x * 2)
    assert isinstance(err_mapped, Err)
    assert err_mapped.error == "boom"


def test_and_then_kleisli_composition() -> None:
    def half_if_even(x: int) -> "Ok[int] | Err[str]":
        if x % 2 == 0:
            return Ok(x // 2)
        return Err("odd")

    assert and_then(Ok(4), half_if_even).value == 2  # type: ignore[union-attr]
    assert and_then(Ok(3), half_if_even).error == "odd"  # type: ignore[union-attr]
    assert and_then(Err("prior failure"), half_if_even).error == "prior failure"  # type: ignore[union-attr]


def test_unwrap_or_returns_default_on_err() -> None:
    assert unwrap_or(Ok(5), 0) == 5
    assert unwrap_or(Err("boom"), 0) == 0
