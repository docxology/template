"""Tests for insect_composition presets."""

from __future__ import annotations

import pytest

import insect_composition


def test_each_preset_sums_to_one() -> None:
    for preset in insect_composition.list_presets():
        s = sum(preset.mass_fractions.values())
        assert abs(s - 1.0) < 1e-9


def test_find_preset_roundtrip() -> None:
    p = insect_composition.find_preset("larva_illustrative")
    assert p.name == "larva_illustrative"


def test_find_preset_unknown() -> None:
    with pytest.raises(ValueError, match="unknown"):
        insect_composition.find_preset("nonexistent")


def test_normalize_fractions() -> None:
    fr = insect_composition.normalize_fractions({"a": 2.0, "b": 3.0})
    assert fr["a"] == pytest.approx(0.4)
    assert fr["b"] == pytest.approx(0.6)


def test_normalize_empty_rejected() -> None:
    with pytest.raises(ValueError):
        insect_composition.normalize_fractions({})


def test_normalize_zero_sum_rejected() -> None:
    with pytest.raises(ValueError, match="positive"):
        insect_composition.normalize_fractions({"a": 0.0, "b": 0.0})


def test_default_densities_positive() -> None:
    d = insect_composition.default_component_densities_kg_m3()
    assert all(v > 0 for v in d.values())
    assert set(d.keys()) == {"cuticle", "soft_tissue", "hemolymph", "internal_gas"}
