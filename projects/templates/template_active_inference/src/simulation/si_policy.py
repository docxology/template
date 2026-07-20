"""Policy selection for sophisticated-inference T-maze runs."""

from __future__ import annotations

from typing import Any

import numpy as np

from simulation.si_belief import marginal_state_belief

_POLICY_INFERENCE_ERRORS = (
    AttributeError,
    IndexError,
    NotImplementedError,
    RuntimeError,
    TypeError,
    ValueError,
)


def _normalise_policy_posterior(q_pi: Any) -> np.ndarray:
    """Validate and normalize a pymdp policy posterior."""
    values = np.asarray(q_pi, dtype=np.float64).reshape(-1)
    if values.size == 0 or not np.all(np.isfinite(values)):
        raise ValueError("pymdp policy posterior must be finite and non-empty")
    if np.any(values < 0.0):
        raise ValueError("pymdp policy posterior must be non-negative")
    total = float(values.sum())
    if total <= 0.0:
        raise ValueError("pymdp policy posterior must have positive mass")
    return values / total


def _expected_utility_fallback(
    agent: Any,
    qs: list,
    *,
    b: np.ndarray,
    c: np.ndarray,
    fallback_reason: str,
) -> tuple[int, str, float | None, int | None, dict[str, Any]]:
    """Select an action from one-step expected utility when pymdp lacks policy inference."""
    q = marginal_state_belief(qs)
    transition = np.asarray(b, dtype=np.float64)
    if transition.ndim != 3 or transition.shape[2] <= 0:
        raise ValueError(f"transition model must be 3-dimensional with actions, got shape {transition.shape}")
    likelihood = np.asarray(agent.A[0], dtype=np.float64)
    preferences = np.asarray(c, dtype=np.float64).reshape(-1)
    if not np.all(np.isfinite(transition)) or not np.all(np.isfinite(likelihood)):
        raise ValueError("fallback model factors must be finite")
    if not np.all(np.isfinite(preferences)):
        raise ValueError("fallback preferences must be finite")
    preference_weights = np.exp(preferences - float(np.max(preferences)))
    scores = []
    for action in range(transition.shape[2]):
        next_state_probs = transition[:, :, action] @ q
        obs_probs = likelihood @ next_state_probs
        scores.append(float(np.dot(obs_probs.reshape(-1), preference_weights.reshape(-1))))
    score_arr = np.asarray(scores, dtype=np.float64)
    if not np.all(np.isfinite(score_arr)):
        raise ValueError("fallback expected-utility scores must be finite")
    score_arr = np.clip(score_arr, 0.0, None)
    if float(score_arr.sum()) <= 0:
        policy_dist = np.full(transition.shape[2], 1.0 / transition.shape[2])
    else:
        policy_dist = score_arr / float(score_arr.sum())
    q_pi_entropy = float(-np.sum([p * np.log(p) for p in policy_dist if p > 0]))
    action = int(np.argmax(policy_dist))
    return (
        action,
        "expected_utility_fallback",
        None,
        action,
        {
            "posterior_available": True,
            "posterior_source": "expected_utility_fallback",
            "q_pi": [float(value) for value in policy_dist],
            "q_pi_sum": float(policy_dist.sum()),
            "q_pi_entropy": q_pi_entropy,
            "q_pi_normalized": abs(float(policy_dist.sum()) - 1.0) <= 1e-9,
            "selected_policy": action,
            "expected_free_energy_available": False,
            "expected_free_energy_values": [],
            "selected_policy_expected_free_energy": None,
            "fallback_reason": fallback_reason,
        },
    )


def select_policy_action(
    agent: Any,
    qs: list,
    *,
    b: np.ndarray,
    c: np.ndarray,
    rng: np.random.Generator,
) -> tuple[int, str, float | None, int | None, dict[str, Any]]:
    """Return action, method label, selected EFE, selected policy index, and policy evidence."""
    del rng  # reserved for stochastic policy sampling when pymdp exposes it
    fallback_reason = "agent.infer_policies unavailable"
    try:
        q_pi, neg_efe = agent.infer_policies(qs)
    except _POLICY_INFERENCE_ERRORS as exc:
        fallback_reason = f"agent.infer_policies unavailable ({type(exc).__name__}); used expected-utility fallback"
        return _expected_utility_fallback(agent, qs, b=b, c=c, fallback_reason=fallback_reason)

    q_pi_norm = _normalise_policy_posterior(q_pi)
    try:
        action = int(np.asarray(agent.sample_action(q_pi)).reshape(-1)[0])
    except _POLICY_INFERENCE_ERRORS as exc:
        fallback_reason = f"agent.sample_action unavailable ({type(exc).__name__}); used expected-utility fallback"
        return _expected_utility_fallback(agent, qs, b=b, c=c, fallback_reason=fallback_reason)
    if not 0 <= action < b.shape[2]:
        raise ValueError(f"pymdp selected action {action} outside model range 0..{b.shape[2] - 1}")

    efe_values: list[float] = []
    if neg_efe is not None:
        raw_efe = np.asarray(neg_efe, dtype=np.float64).reshape(-1)
        if raw_efe.size and raw_efe.size != q_pi_norm.size:
            raise ValueError(
                "expected free-energy vector length must match policy posterior length; "
                f"got {raw_efe.size} and {q_pi_norm.size}"
            )
        if raw_efe.size and not np.all(np.isfinite(raw_efe)):
            raise ValueError("expected free-energy values must be finite")
        efe_values = [float(value) for value in raw_efe]
    policy_idx = int(np.argmax(q_pi_norm))
    efe = efe_values[policy_idx] if efe_values else None
    q_pi_entropy = float(-np.sum([p * np.log(p) for p in q_pi_norm if p > 0]))
    evidence = {
        "posterior_available": True,
        "q_pi": [float(value) for value in q_pi_norm],
        "q_pi_sum": float(q_pi_norm.sum()),
        "q_pi_entropy": q_pi_entropy,
        "q_pi_normalized": abs(float(q_pi_norm.sum()) - 1.0) <= 1e-9,
        "selected_policy": policy_idx,
        "expected_free_energy_available": bool(efe_values),
        "expected_free_energy_values": efe_values,
        "selected_policy_expected_free_energy": efe,
        "efe_source": "pymdp_infer_policies_neg_efe" if efe_values else "pymdp_infer_policies_without_efe",
    }
    return action, "infer_policies", efe, policy_idx, evidence
