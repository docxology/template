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
) -> tuple[int, str, float | None, int | None]:
    """Return action, method label, expected free energy (if available), selected policy index."""
    del rng  # reserved for stochastic policy sampling when pymdp exposes it
    try:
        q_pi, neg_efe = agent.infer_policies(qs)
        action_arr = agent.sample_action(q_pi)
        action = int(np.asarray(action_arr).reshape(-1)[0])
        efe = float(np.asarray(neg_efe).reshape(-1)[0]) if neg_efe is not None else None
        policy_idx = int(np.argmax(np.asarray(q_pi).reshape(-1)))
        return action, "infer_policies", efe, policy_idx
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
    return action, "expected_utility_fallback", None, action
