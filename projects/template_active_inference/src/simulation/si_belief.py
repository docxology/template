"""Belief-state helpers for sophisticated-inference T-maze runs."""

from __future__ import annotations

import numpy as np


def marginal_state_belief(qs: list) -> np.ndarray:
    q = np.asarray(qs[0], dtype=np.float64)
    q = np.squeeze(q)
    if q.ndim == 2:
        q = q[-1]
    q = q.reshape(-1)
    q = np.clip(q, 1e-12, None)
    return q / q.sum()


def belief_entropy(qs: list) -> float:
    q_flat = marginal_state_belief(qs)
    return float(-np.sum(q_flat * np.log(q_flat)))


def qs_marginal_state1(qs: list) -> float:
    q_flat = marginal_state_belief(qs)
    if q_flat.size >= 2:
        return float(q_flat[1])
    return float(q_flat[-1])


def state_inference_action(obs: int, goal_obs: int) -> int:
    return 0 if obs < goal_obs else 1


def state_inference_next_obs(obs: int, action: int) -> int:
    if obs == 0 and action == 0:
        return 1
    return obs
