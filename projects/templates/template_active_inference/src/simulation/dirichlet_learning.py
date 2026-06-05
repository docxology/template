"""Closed-form Dirichlet model-learning track on the T-maze likelihood A.

Active Inference agents do not only *plan* (minimise Expected Free Energy, see
:mod:`simulation.efe_decomposition`); they also *learn* the parameters of their
generative model. The canonical likelihood-learning rule places a Dirichlet prior
with concentration parameters ``pA`` over each column of the likelihood ``A`` and
updates it by accumulating observation-state co-occurrence counts:

    pA <- pA + counts      (conjugate Dirichlet update)
    E[A] = pA / sum_o(pA)  (expected likelihood = column-normalised concentrations)

As counts accumulate, the expected likelihood ``E[A]`` converges to the
data-generating ``A``, which we measure with the per-column KL divergence

    KL(A_true || A_learned) = sum_s sum_o A_true[o, s] * ln( A_true[o, s] / A_learned[o, s] )

(summed over hidden-state columns ``s``). This module drives the update with a
*fixed deterministic* count stream proportional to the true ``A`` (the expected
sufficient statistics under the true model -- no sampling, no RNG), so every
KL value and the learned matrix are byte-deterministic, mirroring the closed-form
EFE decomposition track. KL decreases monotonically toward zero, demonstrating
convergence to the true generative model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

ArrayF = NDArray[np.float64]

# Default deterministic learning schedule (no sampling): a flat unit Dirichlet
# prior and a fixed batch of expected counts (scale * true A) added each step.
DEFAULT_PRIOR_CONCENTRATION: float = 1.0
DEFAULT_COUNT_SCALE: float = 10.0
DEFAULT_NUM_STEPS: int = 8
# A learned likelihood is "converged" when KL(true || learned) drops below this.
CONVERGENCE_KL_ATOL: float = 1e-2


@dataclass(frozen=True)
class DirichletLearningResult:
    """Trajectory of a deterministic Dirichlet likelihood-learning run.

    ``kl_trajectory[k]`` is ``KL(true A || learned A)`` *before* the k-th count
    batch is applied, so index 0 is the prior (largest) and the sequence is
    monotonically non-increasing. ``expected_a`` is the final learned likelihood.
    """

    kl_trajectory: tuple[float, ...]
    expected_a: tuple[tuple[float, ...], ...]
    num_states: int
    num_obs: int
    count_scale: float
    prior_concentration: float

    @property
    def final_kl(self) -> float:
        return self.kl_trajectory[-1]

    @property
    def initial_kl(self) -> float:
        return self.kl_trajectory[0]

    @property
    def is_monotone_decreasing(self) -> bool:
        return all(
            self.kl_trajectory[i] >= self.kl_trajectory[i + 1] - 1e-15 for i in range(len(self.kl_trajectory) - 1)
        )

    @property
    def steps_to_converge(self) -> int:
        """First update step whose KL is below ``CONVERGENCE_KL_ATOL``.

        Returns ``len(kl_trajectory)`` (i.e. "not within the recorded horizon")
        if convergence is never reached -- it never is here, but the contract is
        explicit and total.
        """
        for index, value in enumerate(self.kl_trajectory):
            if value < CONVERGENCE_KL_ATOL:
                return index
        return len(self.kl_trajectory)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "template_active_inference.dirichlet_learning.v1",
            "num_states": self.num_states,
            "num_obs": self.num_obs,
            "count_scale": self.count_scale,
            "prior_concentration": self.prior_concentration,
            "num_steps": len(self.kl_trajectory),
            "kl_trajectory": list(self.kl_trajectory),
            "initial_kl": self.initial_kl,
            "final_kl": self.final_kl,
            "steps_to_converge": self.steps_to_converge,
            "convergence_kl_atol": CONVERGENCE_KL_ATOL,
            "is_monotone_decreasing": self.is_monotone_decreasing,
            "expected_a": [list(col) for col in self.expected_a],
        }


def _true_likelihood(model: dict[str, Any]) -> ArrayF:
    """Extract the (n_o, n_s) likelihood A from a (possibly list-wrapped) model."""
    value = model["A"]
    first = value[0] if isinstance(value, (list, tuple)) else value
    return cast(ArrayF, np.asarray(first, dtype=np.float64))


def expected_likelihood(concentration: ArrayF) -> ArrayF:
    """Expected likelihood ``E[A] = pA / sum_o(pA)`` (column-normalised)."""
    pa = np.asarray(concentration, dtype=np.float64)
    column_totals = pa.sum(axis=0, keepdims=True)
    return cast(ArrayF, pa / column_totals)


def _kl_columns(true_a: ArrayF, learned_a: ArrayF) -> float:
    """``sum_s KL(true_a[:, s] || learned_a[:, s])`` in nats.

    The learned likelihood always has full support (Dirichlet prior > 0), so the
    divergence is finite; ``true_a`` zeros contribute nothing (0 * log 0 == 0).
    """
    total = 0.0
    for s in range(true_a.shape[1]):
        p = true_a[:, s]
        q = learned_a[:, s]
        for o in range(true_a.shape[0]):
            if p[o] > 0.0:
                total += float(p[o] * np.log(p[o] / q[o]))
    return total


def learn_likelihood(
    model: dict[str, Any],
    *,
    num_steps: int = DEFAULT_NUM_STEPS,
    count_scale: float = DEFAULT_COUNT_SCALE,
    prior_concentration: float = DEFAULT_PRIOR_CONCENTRATION,
) -> DirichletLearningResult:
    """Deterministically learn ``A`` via Dirichlet concentration updates.

    Starts from a flat ``prior_concentration`` over every column of ``pA`` and
    repeatedly adds ``count_scale * true_A`` (the expected sufficient statistics
    under the true model -- a fixed, sampling-free count stream). Records
    ``KL(true A || expected A)`` at each step, before applying that step's batch,
    so index 0 is the prior. Single hidden-state factor / outcome modality,
    matching :func:`build_tmaze_generative_model`.
    """
    if num_steps < 1:
        raise ValueError("num_steps must be >= 1")
    if count_scale <= 0.0:
        raise ValueError("count_scale must be positive")
    if prior_concentration <= 0.0:
        raise ValueError("prior_concentration must be positive")

    true_a = _true_likelihood(model)
    n_o, n_s = true_a.shape
    counts = count_scale * true_a  # deterministic expected counts, no sampling
    concentration = np.full((n_o, n_s), float(prior_concentration), dtype=np.float64)

    kls: list[float] = []
    learned = expected_likelihood(concentration)
    for _ in range(num_steps):
        learned = expected_likelihood(concentration)
        kls.append(_kl_columns(true_a, learned))
        concentration = concentration + counts

    return DirichletLearningResult(
        kl_trajectory=tuple(kls),
        expected_a=tuple(tuple(float(v) for v in learned[:, s]) for s in range(n_s)),
        num_states=int(n_s),
        num_obs=int(n_o),
        count_scale=float(count_scale),
        prior_concentration=float(prior_concentration),
    )


def summarize_learning(model: dict[str, Any]) -> dict[str, Any]:
    """JSON-ready summary used by figures, tokens, and the claim ledger."""
    return learn_likelihood(model).to_dict()
