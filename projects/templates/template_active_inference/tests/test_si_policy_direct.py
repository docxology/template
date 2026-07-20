"""Direct branch tests for ``simulation.si_policy.select_policy_action``.

The policy selector has two disjoint paths: a pymdp ``infer_policies`` posterior
path (the ``try`` block) and an expected-utility fallback taken when the agent
raises one of ``_POLICY_INFERENCE_ERRORS``. On the tracked snapshot only the
path matching the last-regenerated pymdp mode ran, leaving the other arm (and
its normalization / EFE-availability sub-branches) uncovered on every other leg.

These tests drive both paths with hand-built stub agents and plain numpy arrays
-- no pymdp import is required, because the selector only calls ``infer_policies``,
``sample_action`` and reads ``agent.A`` as duck-typed attributes. Every aggregate
asserted True (``q_pi_normalized``, ``expected_free_energy_available``) is paired
with a stub that forces the same field False.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from simulation.si_policy import select_policy_action


class _PosteriorAgent:
    """Stub whose ``infer_policies`` succeeds, exercising the pymdp path."""

    def __init__(self, q_pi: np.ndarray, neg_efe: Any, action: int) -> None:
        self._q_pi = q_pi
        self._neg_efe = neg_efe
        self._action = action
        self.A = [np.eye(2)]

    def infer_policies(self, qs: list) -> tuple[np.ndarray, Any]:
        del qs
        return self._q_pi, self._neg_efe

    def sample_action(self, q_pi: np.ndarray) -> np.ndarray:
        del q_pi
        return np.asarray([self._action])


class _FallbackAgent:
    """Stub whose ``infer_policies`` raises, forcing the utility fallback."""

    def __init__(self, a0: np.ndarray) -> None:
        self.A = [a0]

    def infer_policies(self, qs: list) -> tuple[np.ndarray, Any]:
        del qs
        raise ValueError("infer_policies unavailable in this stub")


_B = np.zeros((2, 2, 2))
_B[:, :, 0] = np.array([[1.0, 0.0], [0.0, 1.0]])
_B[:, :, 1] = np.array([[0.0, 1.0], [1.0, 0.0]])
_C = np.array([[3.0], [0.0]])
_RNG = np.random.default_rng(0)


def test_posterior_path_returns_normalized_evidence_with_efe() -> None:
    """A well-formed posterior yields normalized q_pi and a selected EFE."""
    agent = _PosteriorAgent(q_pi=np.array([0.7, 0.3]), neg_efe=np.array([-1.0, -2.0]), action=0)
    qs = [np.array([0.6, 0.4])]
    action, method, efe, policy_idx, evidence = select_policy_action(agent, qs, b=_B, c=_C, rng=_RNG)
    assert method == "infer_policies"
    assert action == 0
    assert policy_idx == 0
    assert efe == -1.0
    assert evidence["q_pi_normalized"] is True
    assert evidence["expected_free_energy_available"] is True
    assert evidence["selected_policy_expected_free_energy"] == -1.0
    assert evidence["efe_source"] == "pymdp_infer_policies_neg_efe"
    assert abs(evidence["q_pi_sum"] - 1.0) <= 1e-9


def test_posterior_path_rejects_zero_sum_and_missing_efe() -> None:
    """A degenerate posterior must fail closed instead of becoming evidence."""
    agent = _PosteriorAgent(q_pi=np.array([0.0, 0.0]), neg_efe=None, action=1)
    qs = [np.array([0.5, 0.5])]
    with pytest.raises(ValueError, match="positive mass"):
        select_policy_action(agent, qs, b=_B, c=_C, rng=_RNG)


def test_posterior_path_efe_available_but_index_out_of_range_is_none() -> None:
    """EFE evidence must be aligned with the policy posterior."""
    agent = _PosteriorAgent(q_pi=np.array([0.2, 0.8]), neg_efe=np.array([-5.0]), action=0)
    qs = [np.array([0.5, 0.5])]
    with pytest.raises(ValueError, match="length must match"):
        select_policy_action(agent, qs, b=_B, c=_C, rng=_RNG)


def test_posterior_path_rejects_negative_or_non_finite_weights() -> None:
    qs = [np.array([0.5, 0.5])]
    for q_pi in (np.array([1.0, -1.0]), np.array([np.nan, 1.0])):
        agent = _PosteriorAgent(q_pi=q_pi, neg_efe=None, action=0)
        with pytest.raises(ValueError, match="policy posterior"):
            select_policy_action(agent, qs, b=_B, c=_C, rng=_RNG)


def test_fallback_path_uses_expected_utility_when_infer_policies_raises() -> None:
    """A raising agent triggers the utility fallback with a positive-score distribution."""
    agent = _FallbackAgent(a0=np.eye(2))
    qs = [np.array([0.6, 0.4])]
    action, method, efe, policy_idx, evidence = select_policy_action(agent, qs, b=_B, c=_C, rng=_RNG)
    assert method == "expected_utility_fallback"
    assert efe is None
    assert action == policy_idx
    assert evidence["posterior_source"] == "expected_utility_fallback"
    assert evidence["expected_free_energy_available"] is False
    assert "fallback_reason" in evidence
    assert evidence["q_pi_normalized"] is True
    assert abs(evidence["q_pi_sum"] - 1.0) <= 1e-9


def test_fallback_path_zero_scores_produce_uniform_distribution() -> None:
    """A zero observation matrix drives all scores to zero -> uniform policy distribution."""
    agent = _FallbackAgent(a0=np.zeros((2, 2)))
    qs = [np.array([0.5, 0.5])]
    _, method, _, _, evidence = select_policy_action(agent, qs, b=_B, c=_C, rng=_RNG)
    assert method == "expected_utility_fallback"
    # sum(scores) <= 0 forces the uniform branch
    assert evidence["q_pi"] == [0.5, 0.5]
    assert evidence["q_pi_normalized"] is True
