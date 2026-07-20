"""Belief-state helpers for sophisticated-inference T-maze runs."""

from __future__ import annotations

import numpy as np


def marginal_state_belief(qs: list) -> np.ndarray:
    """Process marginal state belief."""
    if not qs:
        raise ValueError("state belief must contain at least one factor")
    q = np.asarray(qs[0], dtype=np.float64)
    q = np.squeeze(q)
    if q.ndim == 2:
        q = q[-1]
    q = q.reshape(-1)
    if q.size == 0 or not np.all(np.isfinite(q)):
        raise ValueError("state belief must contain finite values")
    q = np.clip(q, 1e-12, None)
    normalized: np.ndarray = q / q.sum()
    return normalized


def belief_entropy(qs: list) -> float:
    """Process belief entropy."""
    q_flat = marginal_state_belief(qs)
    return float(-np.sum(q_flat * np.log(q_flat)))


def qs_marginal_state1(qs: list) -> float:
    """Process qs marginal state1."""
    q_flat = marginal_state_belief(qs)
    if q_flat.size >= 2:
        return float(q_flat[1])
    return float(q_flat[-1])


def state_inference_action(obs: int, goal_obs: int) -> int:
    """Process state inference action."""
    return 0 if obs < goal_obs else 1


def state_inference_next_obs(obs: int, action: int) -> int:
    """Process state inference next obs."""
    if obs == 0 and action == 0:
        return 1
    return obs
