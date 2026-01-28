"""Tests to ensure 100% coverage for simulation.py including abstract methods and error handling."""

import json

import pytest
from simulation import SimpleSimulation, SimulationBase, SimulationState


class AbstractMethodsCoverageHelper(SimulationBase):
    """Helper class to call abstract methods for coverage."""

    def __init__(self):
        super().__init__()

    def initialize(self):
        super().initialize()

    def step(self, iteration):
        return super().step(iteration)

    def should_continue(self, iteration):
        return super().should_continue(iteration)


def test_abstract_methods_coverage():
    """Test that abstract methods can be called (to satisfy coverage)."""
    # We need to patch ABCMeta to allow instantiation or just use the helper that calls super
    # Since SimulationBase is an ABC, we can't instantiate it directly if it has abstract methods.
    # However, our helper class implements them but calls super().

    # This is a bit tricky with ABCs. If we implement them, we can instantiate.
    sim = AbstractMethodsCoverageHelper()

    # Call the methods to execute the 'pass' statements in the base class
    sim.initialize()
    sim.step(0)
    sim.should_continue(0)


def test_load_checkpoint_exception(tmp_path):
    """Test exception handling in load_checkpoint."""
    sim = SimpleSimulation(output_dir=str(tmp_path))

    # Create a corrupted checkpoint file
    checkpoint_path = tmp_path / "checkpoint_000001.json"
    with open(checkpoint_path, "w") as f:
        f.write("{invalid_json")

    # Attempt to load - should return False and handle exception
    result = sim.load_checkpoint(1)
    assert result is False


def test_load_checkpoint_json_error_handling(tmp_path):
    """Test load_checkpoint handles JSON parsing errors gracefully."""
    sim = SimpleSimulation(output_dir=str(tmp_path))

    # Create a checkpoint file with invalid JSON
    checkpoint_file = tmp_path / f"checkpoint_1.json"
    checkpoint_file.write_text("invalid json content {")

    # Try to load the corrupted checkpoint
    result = sim.load_checkpoint(1)
    assert result is False
