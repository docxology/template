"""Tests for src.methods_dsl.units — dimensional safety."""

from __future__ import annotations

import pytest

from src.methods_dsl.units import Dimension, DimensionError, Quantity, check_compatible, dimension_of, known_units


def test_dimension_of_known_units():
    assert dimension_of("mL") is Dimension.VOLUME
    assert dimension_of("g") is Dimension.MASS
    assert dimension_of("min") is Dimension.TIME
    assert dimension_of("degC") is Dimension.TEMPERATURE
    assert dimension_of("mM") is Dimension.CONCENTRATION
    assert dimension_of("count") is Dimension.COUNT
    assert dimension_of("fraction") is Dimension.DIMENSIONLESS


def test_dimension_of_unknown_unit_raises():
    with pytest.raises(DimensionError, match="unknown unit"):
        dimension_of("furlongs")


def test_known_units_contains_temperature_and_table_units():
    units = known_units()
    assert "mL" in units
    assert "degC" in units
    assert "K" in units
    assert units == tuple(sorted(set(units)))  # sorted, de-duplicated


def test_quantity_dimension_property():
    q = Quantity(10.0, "mL")
    assert q.dimension is Dimension.VOLUME


def test_quantity_to_base_conversion():
    assert Quantity(1.0, "kg").to_base() == pytest.approx(1000.0)
    assert Quantity(1000.0, "mg").to_base() == pytest.approx(1.0)
    assert Quantity(1.0, "h").to_base() == pytest.approx(3600.0)
    assert Quantity(1.0, "min").to_base() == pytest.approx(60.0)


def test_quantity_to_base_rejects_temperature():
    with pytest.raises(DimensionError, match="no shared base"):
        Quantity(37.0, "degC").to_base()


def test_check_compatible_same_dimension_passes():
    check_compatible(Quantity(1.0, "g"), Quantity(2.0, "kg"))  # no raise


def test_check_compatible_incompatible_dimensions_raises():
    with pytest.raises(DimensionError, match="incompatible dimensions"):
        check_compatible(Quantity(1.0, "mL"), Quantity(1.0, "g"))


def test_quantity_addition_same_unit():
    result = Quantity(10.0, "mL") + Quantity(5.0, "mL")
    assert result.unit == "mL"
    assert result.value == pytest.approx(15.0)


def test_quantity_addition_cross_unit_within_dimension():
    # 1 L + 500 mL = 1.5 L expressed in the left operand's unit (L)
    result = Quantity(1.0, "L") + Quantity(500.0, "mL")
    assert result.unit == "L"
    assert result.value == pytest.approx(1.5)


def test_quantity_addition_incompatible_dimensions_raises():
    with pytest.raises(DimensionError):
        Quantity(1.0, "mL") + Quantity(1.0, "g")


def test_quantity_addition_temperature_rejected():
    with pytest.raises(DimensionError, match="not additive"):
        Quantity(37.0, "degC") + Quantity(1.0, "degC")
