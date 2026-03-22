"""Tests for named constant registry."""

import math

import pytest

from constants import NumberClass, constant_lookup, named_constants


def test_named_constants_keys_stable() -> None:
    reg = named_constants()
    assert set(reg.keys()) >= {
        "pi",
        "e",
        "sqrt2",
        "sqrt3",
        "golden_ratio",
        "one_sixth",
        "ln2",
    }


def test_ln2_value() -> None:
    reg = named_constants()
    assert reg["ln2"].value == pytest.approx(math.log(2.0))
    assert constant_lookup()["ln2"] == pytest.approx(math.log(2.0))


def test_one_sixth_is_rational_class() -> None:
    reg = named_constants()
    assert reg["one_sixth"].number_class == NumberClass.RATIONAL


def test_pi_transcendental_label() -> None:
    reg = named_constants()
    assert reg["pi"].number_class == NumberClass.TRANSCENDENTAL


def test_constant_lookup_values() -> None:
    lk = constant_lookup()
    assert lk["one_sixth"] == pytest.approx(1.0 / 6.0)


def test_named_constant_note_nonempty() -> None:
    for nc in named_constants().values():
        assert len(nc.note) >= 8
