"""Minimal T-maze generative model for sophisticated-inference demos."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

import numpy as np

from .pymdp_config import PymdpConfig, TMazeConfig, validate_pymdp_config


@dataclass(frozen=True)
class TMazeSpec:
    """Data container for TMazeSpec."""

    num_states: int = 2
    num_obs: int = 2
    num_actions: int = 2
    policy_len: int = 2
    seed: int = 0
    likelihood_diag: float = 0.9
    preference_goal: float = 2.0


def spec_from_config(config: PymdpConfig) -> TMazeSpec:
    """Process spec from config."""
    tmaze: TMazeConfig = config.tmaze
    return TMazeSpec(
        num_states=tmaze.num_states,
        num_obs=tmaze.num_obs,
        num_actions=tmaze.num_actions,
        policy_len=config.policy_len,
        seed=config.random_seed,
        likelihood_diag=tmaze.likelihood_diag,
        preference_goal=tmaze.preference_goal,
    )


def build_tmaze_generative_model(spec: TMazeSpec | PymdpConfig | None = None) -> dict[str, Any]:
    """Return A, B, C, D for a 2-state start/goal POMDP (single factor)."""
    if isinstance(spec, PymdpConfig):
        validate_pymdp_config(spec)
        params = spec_from_config(spec)
    else:
        params = spec or TMazeSpec()
    if (params.num_states, params.num_obs, params.num_actions) != (2, 2, 2):
        raise ValueError("minimal T-maze requires num_states=num_obs=num_actions=2")
    if params.policy_len <= 0:
        raise ValueError(f"policy_len must be positive, got {params.policy_len!r}")
    if not math.isfinite(params.likelihood_diag) or not 0.0 <= params.likelihood_diag <= 1.0:
        raise ValueError("likelihood_diag must be finite and between 0 and 1")
    if not math.isfinite(params.preference_goal):
        raise ValueError("preference_goal must be finite")
    n_s = params.num_states
    n_o = params.num_obs
    n_u = params.num_actions
    diag = float(params.likelihood_diag)
    off = (1.0 - diag) / max(n_o - 1, 1)

    a = np.zeros((n_o, n_s), dtype=np.float64)
    for s in range(n_s):
        a[s, s] = diag
        for o in range(n_o):
            if o != s:
                a[o, s] = off
        a[:, s] /= a[:, s].sum()

    b = np.zeros((n_s, n_s, n_u), dtype=np.float64)
    b[1, 0, 0] = 1.0
    b[0, 0, 1] = 1.0
    b[1, 1, :] = 1.0

    c = np.zeros((n_o, 1), dtype=np.float64)
    c[1, 0] = params.preference_goal

    d = np.zeros((n_s, 1), dtype=np.float64)
    d[0, 0] = 1.0

    return {
        "A": [np.asarray(a, dtype=np.float64)],
        "B": [np.asarray(b, dtype=np.float64)],
        "C": [np.asarray(c, dtype=np.float64)],
        "D": [np.asarray(d, dtype=np.float64)],
        "policy_len": params.policy_len,
        "seed": params.seed,
    }
