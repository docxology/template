"""Single source of truth for numeric parameters (feeds manuscript variables)."""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_LAMBDA_GRID_POINTS = 21
DEFAULT_LAMBDA_MAX = 4.0
DEFAULT_GAMMA = 1.0
BERNOULLI_VERIFICATION_TOLERANCE = 1e-9


@dataclass(frozen=True)
class Hyperparameters:
    lambda_grid_points: int = DEFAULT_LAMBDA_GRID_POINTS
    lambda_max: float = DEFAULT_LAMBDA_MAX
    gamma: float = DEFAULT_GAMMA
    bernoulli_state_count: int = 2
    bernoulli_verification_tolerance: float = BERNOULLI_VERIFICATION_TOLERANCE


def load_hyperparameters() -> Hyperparameters:
    return Hyperparameters()


def lambda_grid(hp: Hyperparameters | None = None) -> list[float]:
    params = hp or load_hyperparameters()
    import numpy as np

    return [float(x) for x in np.linspace(0.0, params.lambda_max, params.lambda_grid_points)]
