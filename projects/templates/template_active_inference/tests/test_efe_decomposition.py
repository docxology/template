"""Tests for the closed-form Expected-Free-Energy decomposition.

Deterministic, no-mocks numerical checks (fixed generative model) covering the
risk/ambiguity == -(pragmatic+epistemic) identity, term non-negativity, and the
edge behaviour of the entropy/KL/softmax helpers.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from simulation.efe_decomposition import (
    EFE_IDENTITY_ATOL,
    EFETerms,
    _entropy,
    _kl_divergence,
    decompose_all_policies,
    decompose_policy_efe,
    enumerate_policies,
    softmax_preference,
)
from simulation.tmaze_model import TMazeSpec, build_tmaze_generative_model


def test_softmax_preference_normalizes_and_orders() -> None:
    p = softmax_preference(np.array([[0.0], [2.0]]))
    assert abs(float(p.sum()) - 1.0) < 1e-12
    # Higher log-preference -> higher probability mass.
    assert p[1] > p[0]
    expected_hi = math.exp(2.0) / (math.exp(0.0) + math.exp(2.0))
    assert abs(float(p[1]) - expected_hi) < 1e-12


def test_softmax_preference_uniform_when_flat() -> None:
    p = softmax_preference(np.array([5.0, 5.0, 5.0]))
    assert np.allclose(p, np.full(3, 1.0 / 3.0), atol=1e-12)


def test_entropy_one_hot_is_zero_and_uniform_is_log_n() -> None:
    assert _entropy(np.array([1.0, 0.0, 0.0])) == 0.0
    assert abs(_entropy(np.array([0.5, 0.5])) - math.log(2.0)) < 1e-12
    assert abs(_entropy(np.full(4, 0.25)) - math.log(4.0)) < 1e-12


def test_kl_divergence_identical_is_zero_and_disjoint_is_inf() -> None:
    q = np.array([0.3, 0.7])
    assert abs(_kl_divergence(q, q)) < 1e-12
    # q places mass where p has none -> infinite divergence.
    assert _kl_divergence(np.array([0.5, 0.5]), np.array([1.0, 0.0])) == float("inf")
    # q with a zero component is skipped (0 * log 0 == 0), stays finite.
    assert math.isfinite(_kl_divergence(np.array([0.0, 1.0]), np.array([0.5, 0.5])))


def test_enumerate_policies_count_and_shape() -> None:
    policies = enumerate_policies(num_actions=2, policy_len=3)
    assert len(policies) == 2**3
    assert all(len(p) == 3 for p in policies)
    assert len(set(policies)) == len(policies)  # all distinct


def test_efeterms_total_identity_and_dict() -> None:
    terms = EFETerms(risk=1.0, ambiguity=0.5, pragmatic_value=-1.2, epistemic_value=-0.3)
    assert abs(terms.total - 1.5) < 1e-12
    assert abs(terms.identity_residual - 0.0) < 1e-12
    assert terms.identity_holds is True
    payload = terms.to_dict()
    assert payload["total"] == terms.total
    assert payload["identity_holds"] is True
    # A broken set of terms must report the identity as violated.
    broken = EFETerms(risk=1.0, ambiguity=0.0, pragmatic_value=0.0, epistemic_value=0.0)
    assert broken.identity_holds is False


def test_decompose_policy_efe_identity_holds() -> None:
    model = build_tmaze_generative_model()
    for policy in enumerate_policies(2, model["policy_len"]):
        terms = decompose_policy_efe(model, policy)
        # The exact algebraic identity: G == -(pragmatic + epistemic).
        assert abs(terms.identity_residual) <= EFE_IDENTITY_ATOL
        # Risk (a KL) and ambiguity (an expected entropy) are non-negative.
        assert terms.risk >= -EFE_IDENTITY_ATOL
        assert terms.ambiguity >= -EFE_IDENTITY_ATOL


def test_deterministic_likelihood_has_zero_ambiguity() -> None:
    # A perfectly informative likelihood (diag == 1.0) carries no ambiguity, so
    # the epistemic value reduces to the entropy of the predicted outcomes.
    model = build_tmaze_generative_model(TMazeSpec(likelihood_diag=1.0))
    terms = decompose_policy_efe(model, (0, 0))
    assert abs(terms.ambiguity) < 1e-12
    assert terms.epistemic_value >= -1e-12


def test_decompose_all_policies_structure_and_identity() -> None:
    model = build_tmaze_generative_model()
    result = decompose_all_policies(model)
    assert result["schema"] == "template_active_inference.efe_decomposition.v1"
    assert result["policy_count"] == 2 ** model["policy_len"]
    assert len(result["rows"]) == result["policy_count"]
    assert result["all_identity_holds"] is True
    assert result["max_identity_residual"] <= EFE_IDENTITY_ATOL
    # Each row exposes the four terms plus the derived fields.
    row = result["rows"][0]
    for key in ("policy", "risk", "ambiguity", "pragmatic_value", "epistemic_value", "total"):
        assert key in row
    # The reported minimiser really is the argmin over totals.
    totals = [r["total"] for r in result["rows"]]
    assert abs(result["efe_minimizing_total"] - min(totals)) < 1e-12


def test_efe_minimizing_policy_moves_toward_goal() -> None:
    # The T-maze rewards reaching the goal observation; the EFE-minimising policy
    # must take the goal-seeking action first (action 0: state 0 -> state 1).
    model = build_tmaze_generative_model()
    result = decompose_all_policies(model)
    assert result["efe_minimizing_policy"][0] == 0


def test_decompose_is_byte_deterministic() -> None:
    model = build_tmaze_generative_model()
    first = decompose_all_policies(model)
    second = decompose_all_policies(build_tmaze_generative_model())
    assert first == second


def test_pragmatic_value_prefers_goal_observation() -> None:
    # Pragmatic value is the expected log-preference; a policy whose predicted
    # outcomes concentrate on the preferred goal observation must score higher
    # pragmatic value than one that stays at the (non-preferred) start.
    model = build_tmaze_generative_model()
    go = decompose_policy_efe(model, (0, 0))  # moves to goal state
    stay = decompose_policy_efe(model, (1, 1))  # stays at start
    assert go.pragmatic_value > stay.pragmatic_value


def test_first_factor_accepts_bare_array() -> None:
    # decompose helpers must tolerate a non-listed C/D (defensive _first_factor).
    model = build_tmaze_generative_model()
    model_bare = dict(model)
    model_bare["C"] = np.asarray(model["C"][0])
    model_bare["D"] = np.asarray(model["D"][0])
    terms = decompose_policy_efe(model_bare, (0, 1))
    assert abs(terms.identity_residual) <= EFE_IDENTITY_ATOL


@pytest.mark.parametrize("diag", [0.6, 0.75, 0.9, 0.99])
def test_identity_robust_across_likelihoods(diag: float) -> None:
    model = build_tmaze_generative_model(TMazeSpec(likelihood_diag=diag))
    result = decompose_all_policies(model)
    assert result["all_identity_holds"] is True
