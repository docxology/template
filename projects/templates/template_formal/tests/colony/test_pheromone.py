"""Behavioral tests for the typed pheromone-field substrate (ISC-32)."""

from __future__ import annotations

import pytest

from template_formal.colony.pheromone import InMemoryPheromoneField, PheromoneField


def test_sensing_an_unvisited_location_returns_zero() -> None:
    field: PheromoneField = InMemoryPheromoneField()
    assert field.sense("nest") == 0.0


def test_deposit_accumulates_across_calls() -> None:
    field: PheromoneField = InMemoryPheromoneField()
    field.deposit("trail_a", 1.0)
    field.deposit("trail_a", 2.5)
    assert field.sense("trail_a") == 3.5


def test_deposit_rejects_negative_amounts() -> None:
    field: PheromoneField = InMemoryPheromoneField()
    with pytest.raises(ValueError):
        field.deposit("trail_a", -1.0)


def test_evaporate_scales_every_location_uniformly() -> None:
    field: PheromoneField = InMemoryPheromoneField()
    field.deposit("trail_a", 10.0)
    field.deposit("trail_b", 4.0)

    field.evaporate(0.5)

    assert field.sense("trail_a") == 5.0
    assert field.sense("trail_b") == 2.0


def test_evaporate_rejects_decay_outside_unit_interval() -> None:
    field: PheromoneField = InMemoryPheromoneField()
    with pytest.raises(ValueError):
        field.evaporate(1.5)
    with pytest.raises(ValueError):
        field.evaporate(-0.1)


def test_pheromone_field_never_exposes_its_backing_dict_publicly() -> None:
    field = InMemoryPheromoneField()
    public_members = [name for name in dir(field) if not name.startswith("_")]
    assert set(public_members) == {"deposit", "sense", "evaporate"}
