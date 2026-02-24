"""Tests for pipeline package initialization and imports.

Verifies that all pipeline sub-modules are importable and their key classes
are accessible through the package namespace.
"""

from __future__ import annotations

import pytest


class TestPipelineImports:
    """Test pipeline package imports."""

    def test_import_pipeline_package(self) -> None:
        """Test that pipeline package is importable."""
        import pipeline
        assert pipeline is not None

    def test_import_simulation_module(self) -> None:
        """Test simulation module import."""
        from pipeline.simulation import SimulationBase, SimulationState, SimpleSimulation
        assert SimulationBase is not None
        assert SimulationState is not None
        assert SimpleSimulation is not None

    def test_import_reporting_module(self) -> None:
        """Test reporting module import."""
        from pipeline.reporting import ReportGenerator
        assert ReportGenerator is not None

    def test_simulation_state_dataclass(self) -> None:
        """Test SimulationState can be instantiated."""
        from pipeline.simulation import SimulationState
        state = SimulationState()
        assert state.iteration == 0
        assert state.parameters == {}
        assert state.results == {}

    def test_simple_simulation_instantiation(self) -> None:
        """Test SimpleSimulation can be created with default params."""
        from pipeline.simulation import SimpleSimulation
        sim = SimpleSimulation(seed=42)
        assert sim is not None
        sim.initialize()

    def test_report_generator_instantiation(self, tmp_path) -> None:
        """Test ReportGenerator can be created."""
        from pipeline.reporting import ReportGenerator
        gen = ReportGenerator(output_dir=str(tmp_path))
        assert gen is not None
        assert gen.output_dir == tmp_path
