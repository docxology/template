"""Closed-form observable helpers for the analytical toy sweep."""

from __future__ import annotations

import math

from analytical.bernoulli_toy import ising_joint_posterior


def _same_state_probability(lam: float) -> float:
    q = ising_joint_posterior(lam)
    return float(q[0, 0] + q[1, 1])


def _posterior_correlation(lam: float) -> float:
    q = ising_joint_posterior(lam)
    return float(q[0, 0] + q[1, 1] - q[0, 1] - q[1, 0])


def _joint_entropy(lam: float) -> float:
    q = ising_joint_posterior(lam)
    return float(-sum(value * math.log(value) for value in q.reshape(-1) if value > 0))


def _marginal_entropy(lam: float) -> float:
    q = ising_joint_posterior(lam)
    marginal = q.sum(axis=1)
    return float(-sum(value * math.log(value) for value in marginal if value > 0))
