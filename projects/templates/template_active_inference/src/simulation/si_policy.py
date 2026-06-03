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
    try:
        q_pi, neg_efe = agent.infer_policies(qs)
        action_arr = agent.sample_action(q_pi)
        action = int(np.asarray(action_arr).reshape(-1)[0])
        q_pi_arr = np.asarray(q_pi, dtype=np.float64).reshape(-1)
        q_pi_sum = float(q_pi_arr.sum())
        q_pi_norm = q_pi_arr / q_pi_sum if q_pi_sum > 0 else q_pi_arr
        q_pi_entropy = float(-np.sum([p * np.log(p) for p in q_pi_norm if p > 0]))
        policy_idx = int(np.argmax(q_pi_norm))
        efe_values = (
            [float(value) for value in np.asarray(neg_efe, dtype=np.float64).reshape(-1)] if neg_efe is not None else []
        )
        efe = efe_values[policy_idx] if policy_idx < len(efe_values) else None
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
    except _POLICY_INFERENCE_ERRORS:
        pass

    q = marginal_state_belief(qs)
    n_actions = b.shape[2]
    scores = []
    for action in range(n_actions):
        next_state_probs = np.asarray(b[:, :, action], dtype=np.float64) @ q
        obs_probs = np.asarray(agent.A[0], dtype=np.float64) @ next_state_probs
        pref = np.exp(np.asarray(c[:, 0], dtype=np.float64))
        scores.append(float(np.dot(np.asarray(obs_probs).reshape(-1), pref.reshape(-1))))
    action = int(np.argmax(scores))
    score_arr = np.asarray(scores, dtype=np.float64)
    score_arr = np.clip(score_arr, 0.0, None)
    if float(score_arr.sum()) <= 0:
        policy_dist = np.full(n_actions, 1.0 / n_actions)
    else:
        policy_dist = score_arr / float(score_arr.sum())
    q_pi_entropy = float(-np.sum([p * np.log(p) for p in policy_dist if p > 0]))
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
            "fallback_reason": "agent.infer_policies unavailable; used expected-utility fallback",
        },
    )
