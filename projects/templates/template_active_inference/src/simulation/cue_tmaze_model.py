"""Cue-then-reward T-maze where epistemic (information-seeking) value is strictly necessary.

The minimal T-maze in :mod:`tmaze_model` admits *no behavioural advantage* for
expected-free-energy (EFE) policy inference over a greedy pragmatic rule -- the
documented "deliberately too small" null. The reason is structural: flat EFE
propagation (:func:`simulation.efe_decomposition.decompose_policy_efe`) advances
the state belief through ``B`` but never conditions it on observations, so the
hidden reward location is never resolved and cue-sampling earns nothing.

This module builds a generative model in which the reward location is an
*uninformative latent* (50/50 at the start) that is hidden until the agent visits
a CUE location, and supplies a closed-form **sophisticated** (observation-
conditioned) evaluator that anticipates the cue resolving context and selects a
*contingent* arm. A pure-pragmatic / greedy agent that commits to an arm before
sampling the cue reaches reward only by chance; the epistemic agent samples the
cue first and reaches reward with certainty. Both quantities are computed in
closed form (no sampling) so every claim is byte-deterministic and machine-checkable.

Factorisation (single JOINT hidden-state factor, single JOINT outcome modality,
so the existing :class:`EFETerms` and :func:`decompose_policy_efe` are reused
unchanged for the flat baseline):

* Hidden state ``s = (position, context)``, ``position in {CENTER, CUE, LEFT, RIGHT}``
  (4) times ``context in {L, R}`` (2) = **8 states**, ``index = position*2 + context``.
  ``context`` is a fixed latent (the reward location) that ``B`` never changes.
* Outcomes (5): ``NULL`` (uninformative, emitted at CENTER), ``CUE_LEFT`` /
  ``CUE_RIGHT`` (the cue reading at CUE), ``REWARD`` / ``NO_REWARD`` (the arm payoff).
* Actions (4): ``GO_CUE``, ``GO_LEFT``, ``GO_RIGHT``, ``STAY``.
* ``C``: ``REWARD = +preference_reward``, ``NO_REWARD = -preference_reward``.
* ``D``: at CENTER with the context **unknown** (50/50) -- the uninformative start.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

from .efe_decomposition import EFETerms, _entropy, decompose_policy_efe, softmax_preference

ArrayF = NDArray[np.float64]

# Position and outcome indices (module-level so tests and figures share one source).
CENTER, CUE, LEFT, RIGHT = 0, 1, 2, 3
NUM_POSITIONS = 4
NUM_CONTEXTS = 2  # context 0 == reward-LEFT, context 1 == reward-RIGHT
NUM_STATES = NUM_POSITIONS * NUM_CONTEXTS
NULL, CUE_LEFT, CUE_RIGHT, REWARD, NO_REWARD = 0, 1, 2, 3, 4
NUM_OUTCOMES = 5
GO_CUE, GO_LEFT, GO_RIGHT, STAY = 0, 1, 2, 3
NUM_ACTIONS = 4

# Strict-positivity tolerance for the epistemic-advantage claims.
EPISTEMIC_ATOL: float = 1e-10


@dataclass(frozen=True)
class CueTMazeSpec:
    """Parameters of the cue-then-reward T-maze (deterministic, finite)."""

    preference_reward: float = 4.0  # |C| for REWARD / NO_REWARD; sets the advantage scale.
    context_prior: float = 0.5  # P(reward-LEFT) at the start; 0.5 == maximally uninformative.
    policy_len: int = 3  # CENTER -> CUE -> arm needs three evaluated steps.


def state_index(position: int, context: int) -> int:
    """Joint hidden-state index for ``(position, context)``."""
    return position * NUM_CONTEXTS + context


def build_cue_tmaze_generative_model(spec: CueTMazeSpec | None = None) -> dict[str, Any]:
    """Return ``A, B, C, D`` for the cue-then-reward T-maze (single joint factor)."""
    params = spec or CueTMazeSpec()
    a = np.zeros((NUM_OUTCOMES, NUM_STATES), dtype=np.float64)
    for context in range(NUM_CONTEXTS):
        a[NULL, state_index(CENTER, context)] = 1.0  # uninformative at the start
        a[CUE_LEFT if context == 0 else CUE_RIGHT, state_index(CUE, context)] = 1.0  # cue reveals context
        a[REWARD if context == 0 else NO_REWARD, state_index(LEFT, context)] = 1.0  # left pays iff ctx=L
        a[REWARD if context == 1 else NO_REWARD, state_index(RIGHT, context)] = 1.0  # right pays iff ctx=R

    # B: position is set deterministically by the action; context is a fixed latent.
    b = np.zeros((NUM_STATES, NUM_STATES, NUM_ACTIONS), dtype=np.float64)
    target_position = {GO_CUE: CUE, GO_LEFT: LEFT, GO_RIGHT: RIGHT}
    for context in range(NUM_CONTEXTS):
        for position in range(NUM_POSITIONS):
            src = state_index(position, context)
            for action in range(NUM_ACTIONS):
                dest_pos = target_position.get(action, position)  # STAY keeps position
                b[state_index(dest_pos, context), src, action] = 1.0

    c = np.zeros((NUM_OUTCOMES, 1), dtype=np.float64)
    c[REWARD, 0] = float(params.preference_reward)
    c[NO_REWARD, 0] = -float(params.preference_reward)

    d = np.zeros((NUM_STATES, 1), dtype=np.float64)
    d[state_index(CENTER, 0), 0] = float(params.context_prior)
    d[state_index(CENTER, 1), 0] = 1.0 - float(params.context_prior)

    return {
        "A": [a],
        "B": [b],
        "C": [c],
        "D": [d],
        "policy_len": int(params.policy_len),
        "preference_reward": float(params.preference_reward),
    }


def _context_marginal(state_belief: ArrayF) -> ArrayF:
    """Marginal over the 2 reward contexts from a joint state belief."""
    belief = np.asarray(state_belief, dtype=np.float64).reshape(-1)
    marg = (
        np.array(
            [belief[state_index(p, c)] for c in range(NUM_CONTEXTS) for p in range(NUM_POSITIONS)],
            dtype=np.float64,
        )
        .reshape(NUM_CONTEXTS, NUM_POSITIONS)
        .sum(axis=1)
    )
    total = marg.sum()
    return cast(ArrayF, marg / total if total > 0 else marg)


def cue_information_gain(model: dict[str, Any]) -> float:
    """Expected information gain ``I(context; o_cue)`` of one cue sample (nats).

    Closed form: ``H[context] - E_{o_cue}[ H[context | o_cue] ]`` after moving from
    the start to the CUE location. Strictly positive whenever the start belief is
    uninformative and the cue is informative.
    """
    a = np.asarray(model["A"][0], dtype=np.float64)
    b = np.asarray(model["B"][0], dtype=np.float64)
    d = np.asarray(model["D"][0], dtype=np.float64).reshape(-1)

    belief_at_cue = b[:, :, GO_CUE] @ d
    prior_ctx_entropy = _entropy(_context_marginal(d))
    predicted_cue = a @ belief_at_cue
    expected_posterior_entropy = 0.0
    for outcome in (CUE_LEFT, CUE_RIGHT):
        p_o = float(predicted_cue[outcome])
        if p_o <= 0.0:
            continue
        posterior = a[outcome, :] * belief_at_cue
        posterior = posterior / posterior.sum()
        expected_posterior_entropy += p_o * _entropy(_context_marginal(posterior))
    return float(prior_ctx_entropy - expected_posterior_entropy)


def _expected_reward_log_pref(model: dict[str, Any], *, sample_cue: bool) -> float:
    """Sophisticated (observation-conditioned) expected reward log-preference E[ln p(o_reward)].

    ``sample_cue=True``  -> go CUE, condition the belief on each predicted cue
    reading, then take the *contingent* arm matching the revealed context.
    ``sample_cue=False`` -> commit to the LEFT arm under the prior (a greedy /
    pure-pragmatic agent that cannot condition on a cue it never samples).
    """
    a = np.asarray(model["A"][0], dtype=np.float64)
    b = np.asarray(model["B"][0], dtype=np.float64)
    d = np.asarray(model["D"][0], dtype=np.float64).reshape(-1)
    preference = softmax_preference(np.asarray(model["C"][0], dtype=np.float64))
    log_pref = np.log(preference)

    if not sample_cue:
        # Greedy: rush to an arm (LEFT) under the unresolved prior; reward is 50/50.
        arm_belief = b[:, :, GO_LEFT] @ d
        predicted_reward = a @ arm_belief
        return float(np.sum(predicted_reward * log_pref))

    belief_at_cue = b[:, :, GO_CUE] @ d
    predicted_cue = a @ belief_at_cue
    contingent_action = {CUE_LEFT: GO_LEFT, CUE_RIGHT: GO_RIGHT}
    total = 0.0
    for outcome in (CUE_LEFT, CUE_RIGHT):
        p_o = float(predicted_cue[outcome])
        if p_o <= 0.0:
            continue
        posterior = a[outcome, :] * belief_at_cue
        posterior = posterior / posterior.sum()
        arm_belief = b[:, :, contingent_action[outcome]] @ posterior
        predicted_reward = a @ arm_belief
        total += p_o * float(np.sum(predicted_reward * log_pref))
    return total


@dataclass(frozen=True)
class CueAdvantage:
    """Measured epistemic advantage of cue-sampling on the cue T-maze (nats)."""

    cue_information_gain: float  # I(context; o_cue) > 0
    epistemic_reward_log_pref: float  # E[ln p(reward)] for cue-then-contingent-arm
    greedy_reward_log_pref: float  # E[ln p(reward)] for commit-to-arm (no cue)
    flat_efe_cue: float  # decompose_policy_efe G for the cue-first policy (baseline)
    flat_efe_greedy: float  # decompose_policy_efe G for the greedy policy (baseline)

    @property
    def behavioral_advantage(self) -> float:
        """How much better the cue-sampling agent's expected reward is (nats)."""
        return self.epistemic_reward_log_pref - self.greedy_reward_log_pref

    @property
    def epistemic_required(self) -> bool:
        """True iff the cue carries information AND yields a behavioural advantage."""
        return bool(self.cue_information_gain > EPISTEMIC_ATOL and self.behavioral_advantage > EPISTEMIC_ATOL)

    @property
    def flat_efe_indistinguishable(self) -> bool:
        """True iff *flat* EFE cannot tell the cue and greedy policies apart.

        This is the documented limitation: without observation conditioning the
        two policies score identically, so the sophisticated evaluator is what
        makes epistemic value strictly necessary.
        """
        return bool(abs(self.flat_efe_cue - self.flat_efe_greedy) <= EPISTEMIC_ATOL)

    def to_dict(self) -> dict[str, float | bool]:
        return {
            "cue_information_gain": self.cue_information_gain,
            "epistemic_reward_log_pref": self.epistemic_reward_log_pref,
            "greedy_reward_log_pref": self.greedy_reward_log_pref,
            "behavioral_advantage": self.behavioral_advantage,
            "flat_efe_cue": self.flat_efe_cue,
            "flat_efe_greedy": self.flat_efe_greedy,
            "flat_efe_indistinguishable": self.flat_efe_indistinguishable,
            "epistemic_required": self.epistemic_required,
        }


def compare_cue_vs_greedy(model: dict[str, Any] | None = None) -> CueAdvantage:
    """Closed-form comparison proving epistemic cue-sampling is strictly necessary.

    Reuses :func:`decompose_policy_efe` for the *flat* baseline (which is blind to
    the cue, by construction) and the module's sophisticated evaluator for the
    observation-conditioned reward expectations.
    """
    mdl = model or build_cue_tmaze_generative_model()
    cue_first = (GO_CUE, GO_LEFT, STAY)  # sample cue, then an arm, then settle
    greedy = (GO_LEFT, STAY, STAY)  # commit to an arm immediately
    flat_cue: EFETerms = decompose_policy_efe(mdl, cue_first)
    flat_greedy: EFETerms = decompose_policy_efe(mdl, greedy)
    return CueAdvantage(
        cue_information_gain=cue_information_gain(mdl),
        epistemic_reward_log_pref=_expected_reward_log_pref(mdl, sample_cue=True),
        greedy_reward_log_pref=_expected_reward_log_pref(mdl, sample_cue=False),
        flat_efe_cue=float(flat_cue.total),
        flat_efe_greedy=float(flat_greedy.total),
    )


def cue_advantage_summary(model: dict[str, Any] | None = None) -> dict[str, Any]:
    """JSON-ready summary for the manuscript / figure / claim ledger."""
    advantage = compare_cue_vs_greedy(model)
    return {
        "schema": "template_active_inference.cue_tmaze.v1",
        "num_states": NUM_STATES,
        "num_outcomes": NUM_OUTCOMES,
        "num_actions": NUM_ACTIONS,
        **advantage.to_dict(),
        "epistemic_atol": EPISTEMIC_ATOL,
    }
