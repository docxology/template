"""Simulation framework for Ento-Linguistic model stability analysis.

This module provides a reproducible simulation engine for testing the stability
of terminology extraction and discourse mapping under varying parameters.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

__all__ = [
    "SimulationState",
    "SimulationBase",
    "SimpleSimulation",
]

# Infrastructure integration
try:
    # simulation.py -> pipeline/ -> src/ -> ento_linguistics/ -> projects_archive/ -> template/
    repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    sys.path.insert(0, str(repo_root))
    from infrastructure.core import get_logger
    INFRASTRUCTURE_AVAILABLE = True
    logger = get_logger("ento_linguistics.simulation")
except ImportError:
    INFRASTRUCTURE_AVAILABLE = False
    logger = logging.getLogger("ento_linguistics.simulation")


@dataclass
class SimulationState:
    """Represents the state of a simulation run."""

    iteration: int = 0
    parameters: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    seed: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SimulationState:
        """Create state from dictionary."""
        return cls(**data)


class SimulationBase(ABC):
    """Base class for scientific simulations.

    Provides common functionality for parameter management, reproducibility,
    progress tracking, checkpointing, and result serialization.
    """

    def __init__(
        self,
        parameters: Optional[Dict[str, Any]] = None,
        seed: Optional[int] = None,
        output_dir: Optional[str] = None,
        checkpoint_interval: int = 100,
    ):
        """Initialize simulation.

        Args:
            parameters: Simulation parameters
            seed: Random seed for reproducibility
            output_dir: Directory for saving results
            checkpoint_interval: Iterations between checkpoints
        """
        self.parameters = parameters or {}
        self.seed = seed
        self.output_dir = Path(output_dir) if output_dir else Path("output/simulations")
        self.checkpoint_interval = checkpoint_interval

        # Initialize state
        self.state = SimulationState(
            iteration=0,
            parameters=self.parameters.copy(),
            seed=self.seed,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        )

        # Setup random number generator
        self.rng = np.random.default_rng(self.seed)

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
    def step(self, iteration: int) -> Dict[str, Any]:
        """Perform one simulation step.

        Args:
            iteration: Current iteration number

        Returns:
            Dictionary of step results
        """
        pass

    @abstractmethod
    def should_continue(self, iteration: int) -> bool:
        """Determine if simulation should continue.

        Args:
            iteration: Current iteration number

        Returns:
            True if simulation should continue
        """
        pass

    def run(
        self,
        max_iterations: Optional[int] = None,
        save_checkpoints: bool = True,
        verbose: bool = True,
    ) -> SimulationState:
        """Run the simulation.

        Args:
            max_iterations: Maximum number of iterations
            save_checkpoints: Whether to save checkpoints
            verbose: Whether to print progress

        Returns:
            Final simulation state
        """
        self.start_time = time.time()
        self.initialize()

        iteration = 0
        while self.should_continue(iteration):
            if max_iterations is not None and iteration >= max_iterations:
                break

            # Perform simulation step
            step_results = self.step(iteration)

            # Update state
            self.state.iteration = iteration
            self.state.results[f"iteration_{iteration}"] = step_results

            # Checkpoint
            if save_checkpoints and iteration % self.checkpoint_interval == 0:
                self.save_checkpoint(iteration)

            iteration += 1

            if verbose and iteration % 10 == 0:
                elapsed = time.time() - self.start_time
                logger.info(f"Iteration {iteration}, elapsed: {elapsed:.2f}s")
                print(f"Iteration {iteration}, elapsed: {elapsed:.2f}s")

        # Final state update
        self.state.iteration = iteration
        self.state.metadata["total_time"] = time.time() - self.start_time
        self.state.metadata["total_iterations"] = iteration

        return self.state

    def save_checkpoint(self, iteration: int) -> None:
        """Save simulation checkpoint.

        Args:
            iteration: Current iteration number
        """
        checkpoint_file = self.output_dir / f"checkpoint_{iteration:06d}.json"
        with open(checkpoint_file, "w") as f:
            json.dump(self.state.to_dict(), f, indent=2, default=str)

        self.last_checkpoint_time = time.time()

    def load_checkpoint(self, iteration: int) -> bool:
        """Load simulation checkpoint.

        Args:
            iteration: Iteration number to load

        Returns:
            True if checkpoint loaded successfully
        """
        checkpoint_file = self.output_dir / f"checkpoint_{iteration:06d}.json"
        if not checkpoint_file.exists():
            return False

        try:
            with open(checkpoint_file, "r") as f:
                data = json.load(f)
            self.state = SimulationState.from_dict(data)

            # Restore random number generator
            self.rng = np.random.default_rng(self.state.seed)

            # Mark that simulation has started (for progress tracking)
            if self.state.iteration > 0:
                self.start_time = (
                    time.time()
                )  # Approximate, checkpoint doesn't store this

            return True
        except Exception:
            return False

    def save_results(
        self, filename: Optional[str] = None, formats: Optional[List[str]] = None
    ) -> Dict[str, Path]:
        """Save simulation results.

        Args:
            filename: Base filename (without extension)
            formats: List of formats to save (json, npz, csv)

        Returns:
            Dictionary mapping format to file path
        """
        if filename is None:
            filename = f"simulation_{self.state.timestamp.replace(' ', '_')}"

        if formats is None:
            formats = ["json", "npz"]

        saved_files = {}

        # Save as JSON
        if "json" in formats:
            json_file = self.output_dir / f"{filename}.json"
            with open(json_file, "w") as f:
                json.dump(self.state.to_dict(), f, indent=2, default=str)
            saved_files["json"] = json_file

        # Save as NPZ (numpy compressed)
        if "npz" in formats:
            npz_file = self.output_dir / f"{filename}.npz"
            np.savez_compressed(
                npz_file,
                iteration=np.array([self.state.iteration]),
                **{
                    k: np.array(v) if isinstance(v, (list, tuple)) else v
                    for k, v in self.state.results.items()
                },
            )
            saved_files["npz"] = npz_file

        # Save as CSV (flattened results)
        if "csv" in formats:
            csv_file = self.output_dir / f"{filename}.csv"
            self._save_results_csv(csv_file)
            saved_files["csv"] = csv_file

        return saved_files

    def _save_results_csv(self, csv_file: Path) -> None:
        """Save results as CSV.

        Args:
            csv_file: Path to CSV file
        """
        import csv

        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(["iteration", "key", "value"])

            # Write data
            for iteration_key, results in self.state.results.items():
                if iteration_key.startswith("iteration_"):
                    iter_num = int(iteration_key.split("_")[1])
                    for key, value in results.items():
                        writer.writerow([iter_num, key, value])

    def get_progress(self) -> Dict[str, Any]:
        """Get simulation progress information.

        Returns:
            Dictionary with progress metrics
        """
        if self.start_time is None:
            return {"status": "not_started"}

        elapsed = time.time() - self.start_time
        iterations_per_second = self.state.iteration / elapsed if elapsed > 0 else 0

        return {
            "iteration": self.state.iteration,
            "elapsed_time": elapsed,
            "iterations_per_second": iterations_per_second,
            "estimated_remaining": None,  # Can be calculated if max_iterations known
        }


class SimpleSimulation(SimulationBase):
    """Simple example simulation for testing."""

    def __init__(self, **kwargs):
        """Initialize simple simulation."""
        super().__init__(**kwargs)
        self.data: List[float] = []
        self.max_iterations = self.parameters.get("max_iterations", 100)
        self.target_value = self.parameters.get("target_value", 10.0)

    def initialize(self) -> None:
        """Initialize simulation."""
        self.data = []

    def step(self, iteration: int) -> Dict[str, Any]:
        """Perform one step."""
        # Simple random walk
        step_size = self.rng.normal(0, 1)
        if not self.data:
            self.data.append(step_size)
        else:
            self.data.append(self.data[-1] + step_size)

        current_value = self.data[-1]
        error = abs(current_value - self.target_value)

        return {"value": current_value, "error": error, "step_size": step_size}

    def should_continue(self, iteration: int) -> bool:
        """Check if should continue."""
        if iteration >= self.max_iterations:
            return False

        # Stop if close to target
        if self.data and abs(self.data[-1] - self.target_value) < 0.01:
            return False

        return True
