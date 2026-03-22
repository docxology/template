"""Import smoke tests for package __init__."""

from __future__ import annotations


def test_public_imports() -> None:
    import importlib

    m = importlib.import_module("__init__")
    assert hasattr(m, "ideal_gas_density_kg_m3")
    assert hasattr(m, "mixture_density_for_preset")
    assert hasattr(m, "BuoyancyRegime")
