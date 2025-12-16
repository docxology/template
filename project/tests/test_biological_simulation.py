"""Comprehensive tests for biological_simulation module."""
import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from biological_simulation import (
    CambiumIntegrationSimulation,
    GraftSimulationBase,
    GraftSimulationState
)


class TestGraftSimulationState:
    """Test GraftSimulationState dataclass."""
    
    def test_state_creation(self):
        """Test creating simulation state."""
        state = GraftSimulationState(
            day=10,
            parameters={"compatibility": 0.8},
            cambium_contact=0.5,
            callus_formation=0.3,
            seed=42
        )
        assert state.day == 10
        assert state.cambium_contact == 0.5
        assert state.seed == 42
    
    def test_state_to_dict(self):
        """Test converting state to dictionary."""
        state = GraftSimulationState(day=5, cambium_contact=0.6)
        state_dict = state.to_dict()
        assert state_dict["day"] == 5
        assert state_dict["cambium_contact"] == 0.6
    
    def test_state_from_dict(self):
        """Test creating state from dictionary."""
        data = {
            "day": 3,
            "parameters": {},
            "cambium_contact": 0.4,
            "callus_formation": 0.2,
            "vascular_connection": 0.1,
            "union_strength": 0.3,
            "results": {},
            "metadata": {},
            "timestamp": "",
            "seed": None
        }
        state = GraftSimulationState.from_dict(data)
        assert state.day == 3
        assert state.cambium_contact == 0.4


class TestCambiumIntegrationSimulation:
    """Test CambiumIntegrationSimulation."""
    
    def test_initialization(self):
        """Test simulation initialization."""
        sim = CambiumIntegrationSimulation(
            parameters={"compatibility": 0.8, "temperature": 22.0},
            seed=42
        )
        assert sim.compatibility == 0.8
        assert sim.temperature == 22.0
    
    def test_initialize(self):
        """Test simulation initialization method."""
        sim = CambiumIntegrationSimulation(parameters={"compatibility": 0.8, "technique_quality": 0.8})
        sim.initialize()
        assert sim.state.cambium_contact > 0
        assert sim.state.callus_formation == 0.0
    
    def test_step(self):
        """Test simulation step."""
        sim = CambiumIntegrationSimulation(
            parameters={"compatibility": 0.8, "temperature": 22.0, "humidity": 0.8, "technique_quality": 0.8}
        )
        sim.initialize()
        result = sim.step(0)
        assert "cambium_contact" in result
        assert "callus_formation" in result
        assert "union_strength" in result
    
    def test_should_continue(self):
        """Test continuation logic."""
        sim = CambiumIntegrationSimulation(parameters={"max_days": 10, "compatibility": 0.8})
        assert sim.should_continue(0) is True
        assert sim.should_continue(10) is False
    
    def test_run_simulation(self, tmp_path):
        """Test running a simulation."""
        sim = CambiumIntegrationSimulation(
            parameters={"compatibility": 0.8, "temperature": 22.0, "humidity": 0.8, "technique_quality": 0.8, "max_days": 20},
            seed=42,
            output_dir=str(tmp_path)
        )
        state = sim.run(max_days=20, verbose=False)
        assert state.day > 0
        assert state.union_strength >= 0
    
    def test_save_results(self, tmp_path):
        """Test saving simulation results."""
        sim = CambiumIntegrationSimulation(
            parameters={"compatibility": 0.8, "temperature": 22.0, "humidity": 0.8, "technique_quality": 0.8},
            seed=42,
            output_dir=str(tmp_path)
        )
        sim.run(max_days=10, verbose=False)
        saved_files = sim.save_results("test_sim", formats=["json", "npz"])
        assert "json" in saved_files
        assert "npz" in saved_files
    
    def test_save_results_csv(self, tmp_path):
        """Test saving simulation results in CSV format."""
        sim = CambiumIntegrationSimulation(
            parameters={"compatibility": 0.8, "temperature": 22.0, "humidity": 0.8, "technique_quality": 0.8},
            seed=42,
            output_dir=str(tmp_path)
        )
        sim.run(max_days=10, verbose=False)
        saved_files = sim.save_results("test_sim_csv", formats=["csv"])
        assert "csv" in saved_files
        assert saved_files["csv"].exists()
    
    def test_save_checkpoint(self, tmp_path):
        """Test saving checkpoint."""
        sim = CambiumIntegrationSimulation(
            parameters={"compatibility": 0.8, "temperature": 22.0, "humidity": 0.8, "technique_quality": 0.8},
            seed=42,
            output_dir=str(tmp_path)
        )
        sim.initialize()
        sim.state.day = 5
        sim.save_checkpoint(5)
        
        # Check checkpoint file exists
        checkpoint_file = tmp_path / "checkpoint_day_0005.json"
        assert checkpoint_file.exists()
        
        # Verify checkpoint content
        with open(checkpoint_file, 'r') as f:
            data = json.load(f)
        assert data["day"] == 5
    
    def test_load_checkpoint_valid(self, tmp_path):
        """Test loading valid checkpoint."""
        sim = CambiumIntegrationSimulation(
            parameters={"compatibility": 0.8, "temperature": 22.0, "humidity": 0.8, "technique_quality": 0.8},
            seed=42,
            output_dir=str(tmp_path)
        )
        sim.initialize()
        sim.state.day = 10
        sim.save_checkpoint(10)
        
        # Create new simulation and load checkpoint
        sim2 = CambiumIntegrationSimulation(
            parameters={"compatibility": 0.8, "temperature": 22.0, "humidity": 0.8, "technique_quality": 0.8},
            seed=42,
            output_dir=str(tmp_path)
        )
        loaded = sim2.load_checkpoint(10)
        assert loaded is True
        assert sim2.state.day == 10
    
    def test_load_checkpoint_invalid(self, tmp_path):
        """Test loading non-existent checkpoint."""
        sim = CambiumIntegrationSimulation(
            parameters={"compatibility": 0.8, "temperature": 22.0, "humidity": 0.8, "technique_quality": 0.8},
            seed=42,
            output_dir=str(tmp_path)
        )
        loaded = sim.load_checkpoint(999)  # Non-existent checkpoint
        assert loaded is False
    
    def test_load_checkpoint_corrupted(self, tmp_path):
        """Test loading corrupted checkpoint."""
        sim = CambiumIntegrationSimulation(
            parameters={"compatibility": 0.8, "temperature": 22.0, "humidity": 0.8, "technique_quality": 0.8},
            seed=42,
            output_dir=str(tmp_path)
        )
        
        # Create corrupted checkpoint file
        checkpoint_file = tmp_path / "checkpoint_day_0015.json"
        with open(checkpoint_file, 'w') as f:
            f.write("invalid json content {")
        
        loaded = sim.load_checkpoint(15)
        assert loaded is False  # Should handle exception gracefully
    
    def test_run_with_checkpoints(self, tmp_path):
        """Test running simulation with checkpoints enabled."""
        sim = CambiumIntegrationSimulation(
            parameters={"compatibility": 0.8, "temperature": 22.0, "humidity": 0.8, "technique_quality": 0.8, "max_days": 30},
            seed=42,
            output_dir=str(tmp_path),
            checkpoint_interval=10
        )
        state = sim.run(max_days=30, save_checkpoints=True, verbose=False)
        assert state.day > 0
        # Check that checkpoint files were created (at days 0, 10, 20, 30)
        checkpoint_files = list(tmp_path.glob("checkpoint_day_*.json"))
        assert len(checkpoint_files) > 0
    
    def test_run_with_verbose(self, tmp_path, capsys):
        """Test running simulation with verbose output."""
        sim = CambiumIntegrationSimulation(
            parameters={"compatibility": 0.8, "temperature": 22.0, "humidity": 0.8, "technique_quality": 0.8, "max_days": 15},
            seed=42,
            output_dir=str(tmp_path)
        )
        state = sim.run(max_days=15, verbose=True)
        assert state.day > 0
        # Check that verbose output was printed (every 5 days)
        captured = capsys.readouterr()
        assert "Day" in captured.out or "Union strength" in captured.out
    
    def test_step_temperature_ranges(self):
        """Test step with different temperature ranges."""
        # Test temperature 15-20 range
        sim1 = CambiumIntegrationSimulation(
            parameters={"compatibility": 0.8, "temperature": 18.0, "humidity": 0.8, "technique_quality": 0.8}
        )
        sim1.initialize()
        result1 = sim1.step(0)
        assert "cambium_contact" in result1
        
        # Test temperature 25-30 range
        sim2 = CambiumIntegrationSimulation(
            parameters={"compatibility": 0.8, "temperature": 27.0, "humidity": 0.8, "technique_quality": 0.8}
        )
        sim2.initialize()
        result2 = sim2.step(0)
        assert "cambium_contact" in result2
        
        # Test temperature < 15
        sim3 = CambiumIntegrationSimulation(
            parameters={"compatibility": 0.8, "temperature": 10.0, "humidity": 0.8, "technique_quality": 0.8}
        )
        sim3.initialize()
        result3 = sim3.step(0)
        assert "cambium_contact" in result3
        
        # Test temperature > 30
        sim4 = CambiumIntegrationSimulation(
            parameters={"compatibility": 0.8, "temperature": 35.0, "humidity": 0.8, "technique_quality": 0.8}
        )
        sim4.initialize()
        result4 = sim4.step(0)
        assert "cambium_contact" in result4
    
    def test_step_humidity_ranges(self):
        """Test step with different humidity ranges."""
        # Test humidity 0.5-0.7 range
        sim1 = CambiumIntegrationSimulation(
            parameters={"compatibility": 0.8, "temperature": 22.0, "humidity": 0.6, "technique_quality": 0.8}
        )
        sim1.initialize()
        result1 = sim1.step(0)
        assert "cambium_contact" in result1
        
        # Test humidity 0.9-1.0 range
        sim2 = CambiumIntegrationSimulation(
            parameters={"compatibility": 0.8, "temperature": 22.0, "humidity": 0.95, "technique_quality": 0.8}
        )
        sim2.initialize()
        result2 = sim2.step(0)
        assert "cambium_contact" in result2
        
        # Test humidity < 0.5
        sim3 = CambiumIntegrationSimulation(
            parameters={"compatibility": 0.8, "temperature": 22.0, "humidity": 0.3, "technique_quality": 0.8}
        )
        sim3.initialize()
        result3 = sim3.step(0)
        assert "cambium_contact" in result3
    
    def test_should_continue_high_union_strength(self):
        """Test should_continue when union strength is high."""
        sim = CambiumIntegrationSimulation(
            parameters={"compatibility": 0.8, "temperature": 22.0, "humidity": 0.8, "technique_quality": 0.8, "max_days": 100}
        )
        sim.initialize()
        # Manually set high union strength
        sim.state.union_strength = 0.96
        assert sim.should_continue(10) is False  # Should stop due to high union strength


if __name__ == "__main__":
    pytest.main([__file__])

