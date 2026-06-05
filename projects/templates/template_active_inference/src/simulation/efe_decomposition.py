"""Closed-form Expected-Free-Energy (EFE) decomposition on the T-maze model.

Active Inference selects policies by minimising the Expected Free Energy

    G(pi) = sum_tau [ risk_tau + ambiguity_tau ]

which admits the two canonical, *exactly equal* decompositions used throughout the
literature:

* **risk + ambiguity** -- ``risk`` is the KL divergence of the policy-predicted
  outcomes ``q(o|pi)`` from the preferred outcomes ``p(o) = softmax(C)`` (the
  pragmatic deviation), and ``ambiguity`` is the expected entropy of the
  likelihood ``E_q(s)[ H[p(o|s)] ]`` (outcome uncertainty given the state).
* **pragmatic + epistemic value** -- ``pragmatic_value = E_q(o)[ ln p(o) ]`` is
  the expected log-preference (utility), and ``epistemic_value = I(s; o | pi)`` is
  the mutual information between hidden states and outcomes (expected information
  gain / salience that drives exploration).

These satisfy the exact algebraic identity (per timestep, hence summed):

    risk + ambiguity + pragmatic_value + epistemic_value == 0
    <=>  G(pi) == -(pragmatic_value + epistemic_value)

derived from ``risk = -H[q(o)] - pragmatic_value`` and
``epistemic_value = H[q(o)] - ambiguity``. This module computes every term in
closed form from the finite T-maze generative model (``A, B, C, D``) -- no
sampling, no pymdp dependency -- so the outputs are byte-deterministic and the
identity is machine-checkable to floating-point tolerance, mirroring the
analytical track's ``decomposition_identity_holds`` (Theorem 5.1).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from itertools import product
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

ArrayF = NDArray[np.float64]

# Identity / non-negativity tolerance shared with the analytical decomposition track.
EFE_IDENTITY_ATOL: float = 1e-10


@dataclass(frozen=True)
class EFETerms:
    """The four EFE terms for a single policy, summed over the horizon.

    ``total`` is the Expected Free Energy itself (``risk + ambiguity``).
    ``identity_residual`` is ``total + pragmatic_value + epistemic_value`` and is
    zero (to ``EFE_IDENTITY_ATOL``) whenever the closed form is correct.
    """

    risk: float
    ambiguity: float
    pragmatic_value: float
    epistemic_value: float

    @property
    def total(self) -> float:
        """Expected Free Energy G(pi) = risk + ambiguity."""
        return self.risk + self.ambiguity

    @property
    def identity_residual(self) -> float:
        """``(risk + ambiguity) + pragmatic_value + epistemic_value`` (== 0 when valid)."""
        return self.total + self.pragmatic_value + self.epistemic_value

    @property
    def identity_holds(self) -> bool:
        return abs(self.identity_residual) <= EFE_IDENTITY_ATOL

    def to_dict(self) -> dict[str, float | bool]:
        return {
            "risk": self.risk,
            "ambiguity": self.ambiguity,
            "pragmatic_value": self.pragmatic_value,
            "epistemic_value": self.epistemic_value,
            "total": self.total,
            "identity_residual": self.identity_residual,
            "identity_holds": self.identity_holds,
        }


def _as_2d(matrix: Any) -> ArrayF:
    return cast(ArrayF, np.asarray(matrix, dtype=np.float64))


def softmax_preference(c_vector: ArrayF) -> ArrayF:
    """Preferred-outcome distribution ``p(o) = softmax(C)`` from log-preferences."""
    c = np.asarray(c_vector, dtype=np.float64).reshape(-1)
    shifted = c - np.max(c)
    weights = np.exp(shifted)
    return cast(ArrayF, weights / weights.sum())


def _entropy(distribution: ArrayF) -> float:
    """Shannon entropy in nats, ignoring zero-probability outcomes."""
    p = np.asarray(distribution, dtype=np.float64).reshape(-1)
    nonzero = p[p > 0.0]
    return float(-np.sum(nonzero * np.log(nonzero)))


def _kl_divergence(q: ArrayF, p: ArrayF) -> float:
    """KL(q || p) in nats; +inf where q has support that p does not."""
    qa = np.asarray(q, dtype=np.float64).reshape(-1)
    pa = np.asarray(p, dtype=np.float64).reshape(-1)
    total = 0.0
    for qi, pi in zip(qa, pa, strict=True):
        if qi <= 0.0:
            continue
        if pi <= 0.0:
            return float("inf")
        total += qi * float(np.log(qi / pi))
    return total


def _first_factor(model: dict[str, Any], key: str) -> ArrayF:
    value = model[key]
    if isinstance(value, (list, tuple)):
        return _as_2d(value[0])
    return _as_2d(value)


def decompose_policy_efe(model: dict[str, Any], policy: Sequence[int]) -> EFETerms:
    """Closed-form EFE term decomposition for one policy (action sequence).

    Beliefs are propagated deterministically from the prior ``D`` through the
    transition tensor ``B`` under ``policy``; at each visited timestep the four
    EFE terms are accumulated. Single hidden-state factor and outcome modality,
    matching :func:`build_tmaze_generative_model`.
    """
    a_matrix = _first_factor(model, "A")  # (n_o, n_s)  P(o | s)
    b_tensor = np.asarray(model["B"][0] if isinstance(model["B"], (list, tuple)) else model["B"], dtype=np.float64)
    c_vector = _first_factor(model, "C")  # (n_o, 1)
    d_vector = _first_factor(model, "D")  # (n_s, 1)

    preference = softmax_preference(c_vector)
    # Per-state likelihood entropy H[p(o | s)] for every hidden state.
    state_entropy = np.array([_entropy(a_matrix[:, s]) for s in range(a_matrix.shape[1])], dtype=np.float64)

    state_belief = d_vector.reshape(-1).astype(np.float64)
    risk = ambiguity = pragmatic = epistemic = 0.0

    for action in policy:
        predicted_obs = a_matrix @ state_belief  # q(o | pi) at this step
        ambiguity_step = float(state_belief @ state_entropy)  # E_q(s)[ H[p(o|s)] ]
        risk += _kl_divergence(predicted_obs, preference)
        ambiguity += ambiguity_step
        # pragmatic value = E_q(o)[ ln p(o) ]; ln p(o) is finite (softmax > 0).
        pragmatic += float(np.sum(predicted_obs * np.log(preference)))
        # epistemic value = mutual information I(s;o) = H[q(o)] - E_q(s)[H[p(o|s)]].
        epistemic += _entropy(predicted_obs) - ambiguity_step
        # Propagate the state belief one step under the chosen action.
        state_belief = b_tensor[:, :, int(action)] @ state_belief

    return EFETerms(
        risk=risk,
        ambiguity=ambiguity,
        pragmatic_value=pragmatic,
        epistemic_value=epistemic,
    )


def enumerate_policies(num_actions: int, policy_len: int) -> list[tuple[int, ...]]:
    """All deterministic action sequences of length ``policy_len``."""
    return [tuple(seq) for seq in product(range(num_actions), repeat=policy_len)]


def decompose_all_policies(model: dict[str, Any]) -> dict[str, Any]:
    """Decompose every length-``policy_len`` policy and summarise the result.

    Returns a JSON-ready dict with one row per policy plus aggregate fields used
    by the manuscript / claim ledger: the EFE-minimising policy, whether the
    risk+ambiguity == -(pragmatic+epistemic) identity holds for all policies, and
    the maximal identity residual observed.
    """
    a_matrix = _first_factor(model, "A")
    num_actions = int(np.asarray(model["B"][0]).shape[2])
    policy_len = int(model.get("policy_len", 1))
    policies = enumerate_policies(num_actions, policy_len)

    rows: list[dict[str, Any]] = []
    for policy in policies:
        terms = decompose_policy_efe(model, policy)
        row: dict[str, Any] = {"policy": list(policy)}
        row.update(terms.to_dict())
        rows.append(row)

    totals = [row["total"] for row in rows]
    best_index = int(np.argmin(totals))
    max_residual = max(abs(row["identity_residual"]) for row in rows)

    return {
        "schema": "template_active_inference.efe_decomposition.v1",
        "num_states": int(a_matrix.shape[1]),
        "num_obs": int(a_matrix.shape[0]),
        "num_actions": num_actions,
        "policy_len": policy_len,
        "policy_count": len(rows),
        "rows": rows,
        "efe_minimizing_policy": list(policies[best_index]),
        "efe_minimizing_total": float(totals[best_index]),
        "all_identity_holds": bool(all(row["identity_holds"] for row in rows)),
        "max_identity_residual": float(max_residual),
        "identity_atol": EFE_IDENTITY_ATOL,
    }
