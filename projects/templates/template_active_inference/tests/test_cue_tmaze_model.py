"""Tests for the cue-then-reward T-maze (epistemic value strictly necessary).

Deterministic, no-mocks numerical checks on the finite generative model: the cue
carries strictly positive information, the sophisticated (observation-conditioned)
agent that samples the cue reaches reward with a measured advantage over a greedy
agent, and -- the documented limitation -- *flat* EFE cannot tell the two apart.
"""

from __future__ import annotations

import math

import numpy as np

from simulation.cue_tmaze_model import (
    CENTER,
    CUE,
    EPISTEMIC_ATOL,
    LEFT,
    NO_REWARD,
    NULL,
    NUM_ACTIONS,
    NUM_OUTCOMES,
    NUM_STATES,
    REWARD,
    RIGHT,
    CueAdvantage,
    CueTMazeSpec,
    build_cue_tmaze_generative_model,
    compare_cue_vs_greedy,
    cue_advantage_summary,
    cue_information_gain,
    state_index,
)
from simulation.efe_decomposition import decompose_policy_efe


def test_model_shapes_and_indices() -> None:
    model = build_cue_tmaze_generative_model()
    a = np.asarray(model["A"][0])
    b = np.asarray(model["B"][0])
    assert a.shape == (NUM_OUTCOMES, NUM_STATES)
    assert b.shape == (NUM_STATES, NUM_STATES, NUM_ACTIONS)
    # Likelihood columns are normalized probability distributions.
    assert np.allclose(a.sum(axis=0), 1.0)
    # Transition columns are normalized for every action.
    for action in range(NUM_ACTIONS):
        assert np.allclose(b[:, :, action].sum(axis=0), 1.0)
    assert state_index(CUE, 1) == CUE * 2 + 1


def test_center_is_uninformative_and_cue_reveals_context() -> None:
    a = np.asarray(build_cue_tmaze_generative_model()["A"][0])
    # CENTER emits NULL for both contexts -> hides the reward location.
    assert a[NULL, state_index(CENTER, 0)] == 1.0
    assert a[NULL, state_index(CENTER, 1)] == 1.0
    # The arms pay off iff the context matches.
    assert a[REWARD, state_index(LEFT, 0)] == 1.0
    assert a[NO_REWARD, state_index(LEFT, 1)] == 1.0
    assert a[REWARD, state_index(RIGHT, 1)] == 1.0


def test_context_is_a_fixed_latent() -> None:
    b = np.asarray(build_cue_tmaze_generative_model()["B"][0])
    # Going to the LEFT arm from CENTER never changes the context bit.
    for context in (0, 1):
        nxt = b[:, :, 1] @ np.eye(NUM_STATES)[state_index(CENTER, context)]
        assert nxt[state_index(LEFT, context)] == 1.0
        assert nxt[state_index(LEFT, 1 - context)] == 0.0


def test_prior_is_uninformative() -> None:
    d = np.asarray(build_cue_tmaze_generative_model()["D"][0]).reshape(-1)
    assert d[state_index(CENTER, 0)] == 0.5
    assert d[state_index(CENTER, 1)] == 0.5
    assert math.isclose(float(d.sum()), 1.0)


def test_cue_information_gain_is_log_two() -> None:
    ig = cue_information_gain(build_cue_tmaze_generative_model())
    assert ig > EPISTEMIC_ATOL
    assert abs(ig - math.log(2.0)) < 1e-12


def test_cue_information_gain_zero_when_context_known() -> None:
    # A degenerate prior that already knows the context exercises the p_o<=0 skip
    # and yields zero information gain (nothing left to learn).
    model = build_cue_tmaze_generative_model(CueTMazeSpec(context_prior=1.0))
    assert abs(cue_information_gain(model)) < 1e-12


def test_epistemic_agent_beats_greedy_by_preference_gap() -> None:
    adv = compare_cue_vs_greedy()
    # Cue-sampling carries information and produces a behavioural advantage.
    assert adv.cue_information_gain > EPISTEMIC_ATOL
    assert adv.behavioral_advantage > EPISTEMIC_ATOL
    assert adv.epistemic_required is True
    # Greedy commits to a 50/50 arm; the epistemic agent resolves context first.
    assert adv.epistemic_reward_log_pref > adv.greedy_reward_log_pref
    # The advantage equals the preference gap over the 50/50 greedy outcome (== 4.0
    # for the default |C| = 4): ln p(REWARD) - 0.5*(ln p(REWARD)+ln p(NO_REWARD)).
    assert abs(adv.behavioral_advantage - 4.0) < 1e-9


def test_epistemic_path_skips_impossible_cue_outcome() -> None:
    # A degenerate prior (context known) makes one cue reading impossible, exercising
    # the p_o<=0 skip inside the sophisticated sample_cue=True evaluator.
    adv = compare_cue_vs_greedy(build_cue_tmaze_generative_model(CueTMazeSpec(context_prior=1.0)))
    # Context already resolved -> no information gain, so epistemic is not required.
    assert adv.cue_information_gain < EPISTEMIC_ATOL
    assert adv.epistemic_required is False


def test_flat_efe_cannot_distinguish_cue_from_greedy() -> None:
    # The documented limitation: flat EFE propagation never conditions on the cue,
    # so the cue-first and greedy policies score identically. This is *why* the
    # sophisticated evaluator is required for an honest epistemic-necessity claim.
    adv = compare_cue_vs_greedy()
    assert adv.flat_efe_indistinguishable is True
    assert abs(adv.flat_efe_cue - adv.flat_efe_greedy) <= EPISTEMIC_ATOL


def test_advantage_scales_with_preference() -> None:
    weak = compare_cue_vs_greedy(build_cue_tmaze_generative_model(CueTMazeSpec(preference_reward=2.0)))
    strong = compare_cue_vs_greedy(build_cue_tmaze_generative_model(CueTMazeSpec(preference_reward=4.0)))
    # Larger reward/penalty magnitude -> larger measured behavioural advantage.
    assert strong.behavioral_advantage > weak.behavioral_advantage
    assert abs(weak.behavioral_advantage - 2.0) < 1e-9


def test_cue_advantage_dataclass_properties() -> None:
    adv = CueAdvantage(
        cue_information_gain=math.log(2.0),
        epistemic_reward_log_pref=-0.05,
        greedy_reward_log_pref=-4.05,
        flat_efe_cue=10.0,
        flat_efe_greedy=10.0,
    )
    assert abs(adv.behavioral_advantage - 4.0) < 1e-9
    assert adv.epistemic_required is True
    assert adv.flat_efe_indistinguishable is True
    payload = adv.to_dict()
    assert payload["epistemic_required"] is True
    assert payload["behavioral_advantage"] == adv.behavioral_advantage
    # A no-information / no-advantage case must report epistemic NOT required.
    none = CueAdvantage(0.0, -1.0, -1.0, 5.0, 9.0)
    assert none.epistemic_required is False
    assert none.flat_efe_indistinguishable is False


def test_cue_advantage_summary_structure() -> None:
    summary = cue_advantage_summary()
    assert summary["schema"] == "template_active_inference.cue_tmaze.v1"
    assert summary["num_states"] == NUM_STATES
    assert summary["epistemic_required"] is True
    for key in ("cue_information_gain", "behavioral_advantage", "flat_efe_indistinguishable"):
        assert key in summary


def test_byte_deterministic() -> None:
    assert cue_advantage_summary() == cue_advantage_summary()
    first = compare_cue_vs_greedy().to_dict()
    second = compare_cue_vs_greedy().to_dict()
    assert first == second


def test_flat_decompose_still_runs_on_joint_model() -> None:
    # The single-joint-factor construction keeps the existing flat decomposer usable.
    model = build_cue_tmaze_generative_model()
    terms = decompose_policy_efe(model, (0, 1, 3))
    assert abs(terms.identity_residual) <= 1e-9
