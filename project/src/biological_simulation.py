"""Biological simulation framework for tree grafting processes.

This module provides simulation of cambium integration, callus formation,
vascular connection, and healing timelines for graft union development.
"""
from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class GraftSimulationState:
    """Represents the state of a graft healing simulation."""
    day: int = 0
    parameters: Dict[str, Any] = field(default_factory=dict)
    cambium_contact: float = 0.0  # 0-1, proportion of cambium in contact
    callus_formation: float = 0.0  # 0-1, callus tissue development
    vascular_connection: float = 0.0  # 0-1, vascular tissue connection
    union_strength: float = 0.0  # 0-1, overall union strength
    results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    seed: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GraftSimulationState:
        """Create state from dictionary."""
        return cls(**data)


class GraftSimulationBase(ABC):
    """Base class for graft healing simulations.
    
    Provides common functionality for simulating biological processes
    in graft union formation, including cambium integration, callus
    formation, and vascular connection.
    """
    
    def __init__(
        self,
        parameters: Optional[Dict[str, Any]] = None,
        seed: Optional[int] = None,
        output_dir: Optional[str] = None,
        checkpoint_interval: int = 10
    ):
        """Initialize graft simulation.
        
        Args:
            parameters: Simulation parameters (compatibility, temperature, etc.)
            seed: Random seed for reproducibility
            output_dir: Directory for saving results
            checkpoint_interval: Days between checkpoints
        """
        self.parameters = parameters or {}
        self.seed = seed
        self.output_dir = Path(output_dir) if output_dir else Path("output/simulations")
        self.checkpoint_interval = checkpoint_interval
        
        # Initialize state
        self.state = GraftSimulationState(
            day=0,
            parameters=self.parameters.copy(),
            seed=self.seed,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # Setup random seed
        if self.seed is not None:
            np.random.seed(self.seed)
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Progress tracking
        self.start_time: Optional[float] = None
        self.last_checkpoint_time: Optional[float] = None
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize simulation state."""
        pass
    
    @abstractmethod
    def step(self, day: int) -> Dict[str, Any]:
        """Perform one simulation day.
        
        Args:
            day: Current day number
            
        Returns:
            Dictionary of day results
        """
        pass
    
    @abstractmethod
    def should_continue(self, day: int) -> bool:
        """Determine if simulation should continue.
        
        Args:
            day: Current day number
            
        Returns:
            True if simulation should continue
        """
        pass
    
    def run(
        self,
        max_days: Optional[int] = None,
        save_checkpoints: bool = True,
        verbose: bool = True
    ) -> GraftSimulationState:
        """Run the graft healing simulation.
        
        Args:
            max_days: Maximum number of days to simulate
            save_checkpoints: Whether to save checkpoints
            verbose: Whether to print progress
            
        Returns:
            Final simulation state
        """
        self.start_time = time.time()
        self.initialize()
        
        day = 0
        while self.should_continue(day):
            if max_days is not None and day >= max_days:
                break
            
            # Perform simulation step
            step_results = self.step(day)
            
            # Update state
            self.state.day = day
            self.state.results[f"day_{day}"] = step_results
            
            # Update biological state variables
            if "cambium_contact" in step_results:
                self.state.cambium_contact = step_results["cambium_contact"]
            if "callus_formation" in step_results:
                self.state.callus_formation = step_results["callus_formation"]
            if "vascular_connection" in step_results:
                self.state.vascular_connection = step_results["vascular_connection"]
            if "union_strength" in step_results:
                self.state.union_strength = step_results["union_strength"]
            
            # Checkpoint
            if save_checkpoints and day % self.checkpoint_interval == 0:
                self.save_checkpoint(day)
            
            day += 1
            
            if verbose and day % 5 == 0:
                elapsed = time.time() - self.start_time
                print(f"Day {day}, Union strength: {self.state.union_strength:.3f}, "
                      f"Elapsed: {elapsed:.2f}s")
        
        # Final state update
        self.state.day = day
        self.state.metadata["total_time"] = time.time() - self.start_time
        self.state.metadata["total_days"] = day
        
        return self.state
    
    def save_checkpoint(self, day: int) -> None:
        """Save simulation checkpoint.
        
        Args:
            day: Current day number
        """
        checkpoint_file = self.output_dir / f"checkpoint_day_{day:04d}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(self.state.to_dict(), f, indent=2, default=str)
        
        self.last_checkpoint_time = time.time()
    
    def load_checkpoint(self, day: int) -> bool:
        """Load simulation checkpoint.
        
        Args:
            day: Day number to load
            
        Returns:
            True if checkpoint loaded successfully
        """
        checkpoint_file = self.output_dir / f"checkpoint_day_{day:04d}.json"
        if not checkpoint_file.exists():
            return False
        
        try:
            with open(checkpoint_file, 'r') as f:
                data = json.load(f)
            self.state = GraftSimulationState.from_dict(data)
            
            # Restore random seed if available
            if self.state.seed is not None:
                np.random.seed(self.state.seed)
            
            return True
        except Exception:
            return False
    
    def save_results(
        self,
        filename: Optional[str] = None,
        formats: Optional[List[str]] = None
    ) -> Dict[str, Path]:
        """Save simulation results.
        
        Args:
            filename: Base filename (without extension)
            formats: List of formats to save (json, npz, csv)
            
        Returns:
            Dictionary mapping format to file path
        """
        if filename is None:
            filename = f"graft_simulation_{self.state.timestamp.replace(' ', '_')}"
        
        if formats is None:
            formats = ["json", "npz"]
        
        saved_files = {}
        
        # Save as JSON
        if "json" in formats:
            json_file = self.output_dir / f"{filename}.json"
            with open(json_file, 'w') as f:
                json.dump(self.state.to_dict(), f, indent=2, default=str)
            saved_files["json"] = json_file
        
        # Save as NPZ
        if "npz" in formats:
            npz_file = self.output_dir / f"{filename}.npz"
            np.savez_compressed(
                npz_file,
                day=np.array([self.state.day]),
                cambium_contact=np.array([self.state.cambium_contact]),
                callus_formation=np.array([self.state.callus_formation]),
                vascular_connection=np.array([self.state.vascular_connection]),
                union_strength=np.array([self.state.union_strength])
            )
            saved_files["npz"] = npz_file
        
        # Save as CSV
        if "csv" in formats:
            import csv
            csv_file = self.output_dir / f"{filename}.csv"
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "day", "cambium_contact", "callus_formation",
                    "vascular_connection", "union_strength"
                ])
                writer.writerow([
                    self.state.day,
                    self.state.cambium_contact,
                    self.state.callus_formation,
                    self.state.vascular_connection,
                    self.state.union_strength
                ])
            saved_files["csv"] = csv_file
        
        return saved_files


class CambiumIntegrationSimulation(GraftSimulationBase):
    """Simulate cambium integration and callus formation process."""
    
    def __init__(self, **kwargs):
        """Initialize cambium integration simulation."""
        super().__init__(**kwargs)
        self.compatibility = self.parameters.get("compatibility", 0.8)
        self.temperature = self.parameters.get("temperature", 22.0)
        self.humidity = self.parameters.get("humidity", 0.8)
        self.technique_quality = self.parameters.get("technique_quality", 0.8)
        self.max_days = self.parameters.get("max_days", 60)
        
        # Biological parameters
        self.cambium_growth_rate = 0.05 * self.compatibility * self.technique_quality
        self.callus_growth_rate = 0.03 * self.compatibility
        self.vascular_growth_rate = 0.02 * self.compatibility
    
    def initialize(self) -> None:
        """Initialize simulation."""
        # Initial state: cambium contact depends on technique quality
        self.state.cambium_contact = 0.6 * self.technique_quality
        self.state.callus_formation = 0.0
        self.state.vascular_connection = 0.0
        self.state.union_strength = 0.0
    
    def step(self, day: int) -> Dict[str, Any]:
        """Simulate one day of healing."""
        # Temperature and humidity effects
        temp_factor = 1.0
        if 20 <= self.temperature <= 25:
            temp_factor = 1.2
        elif 15 <= self.temperature < 20 or 25 < self.temperature <= 30:
            temp_factor = 1.0
        else:
            temp_factor = 0.7
        
        humidity_factor = 1.0
        if 0.7 <= self.humidity <= 0.9:
            humidity_factor = 1.1
        elif 0.5 <= self.humidity < 0.7 or 0.9 < self.humidity <= 1.0:
            humidity_factor = 1.0
        else:
            humidity_factor = 0.8
        
        env_factor = temp_factor * humidity_factor
        
        # Cambium contact increases (plateaus at 1.0)
        if self.state.cambium_contact < 1.0:
            growth = self.cambium_growth_rate * env_factor
            self.state.cambium_contact = min(1.0, 
                self.state.cambium_contact + growth * (1.0 - self.state.cambium_contact))
        
        # Callus formation starts after cambium contact > 0.3
        if self.state.cambium_contact > 0.3 and self.state.callus_formation < 1.0:
            growth = self.callus_growth_rate * env_factor * self.state.cambium_contact
            self.state.callus_formation = min(1.0,
                self.state.callus_formation + growth * (1.0 - self.state.callus_formation))
        
        # Vascular connection starts after callus > 0.5
        if self.state.callus_formation > 0.5 and self.state.vascular_connection < 1.0:
            growth = self.vascular_growth_rate * env_factor * self.state.callus_formation
            self.state.vascular_connection = min(1.0,
                self.state.vascular_connection + growth * (1.0 - self.state.vascular_connection))
        
        # Union strength combines all factors
        self.state.union_strength = (
            0.3 * self.state.cambium_contact +
            0.3 * self.state.callus_formation +
            0.4 * self.state.vascular_connection
        ) * self.compatibility
        
        return {
            "cambium_contact": self.state.cambium_contact,
            "callus_formation": self.state.callus_formation,
            "vascular_connection": self.state.vascular_connection,
            "union_strength": self.state.union_strength,
            "temperature": self.temperature,
            "humidity": self.humidity
        }
    
    def should_continue(self, day: int) -> bool:
        """Check if should continue."""
        if day >= self.max_days:
            return False
        
        # Stop if union is fully established
        if self.state.union_strength >= 0.95:
            return False
        
        return True

