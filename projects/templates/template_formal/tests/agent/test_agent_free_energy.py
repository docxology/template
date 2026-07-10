"""Hand-computed expected-free-energy tests (ISC-28, ISC-29).

Every expected numeric value below is derived independently, by hand, from
the closed-form Gaussian KL-divergence and differential-entropy formulas
documented in ``agent/agent.py``'s module docstring -- not by calling the
implementation twice. ``expected_free_energy`` must match these numbers
within float tolerance, not merely "run without error".
"""

from __future__ import annotations

import math

import pytest

from template_formal.agent.agent import (
    Agent,
    BeliefState,
    CandidateAction,
    DecisionError,
    expected_free_energy,
    gaussian_differential_entropy,
    gaussian_kl_divergence,
)
from template_formal.types.ids import new_agent_id
from template_formal.types.result import Err, Ok

# Preference: P(o) = N(mean=0.0, variance=1.0)
_PREFERENCE = BeliefState(mean=0.0, variance=1.0)


def test_kl_divergence_of_identical_distributions_is_exactly_zero() -> None:
    predicted = BeliefState(mean=0.0, variance=1.0)
    # Hand derivation: KL(N(0,1) || N(0,1))
    #   = 0.5 * ( (1/1) + (0-0)**2/1 - 1 + ln(1/1) )
    #   = 0.5 * ( 1 + 0 - 1 + 0 ) = 0.0
    assert gaussian_kl_divergence(predicted, _PREFERENCE) == 0.0


def test_kl_divergence_shifted_mean_matches_hand_derivation() -> None:
    predicted = BeliefState(mean=2.0, variance=1.0)
    # Hand derivation: KL(N(2,1) || N(0,1))
    #   = 0.5 * ( (1/1) + (0-2)**2/1 - 1 + ln(1/1) )
    #   = 0.5 * ( 1 + 4 - 1 + 0 ) = 0.5 * 4 = 2.0
    kl = gaussian_kl_divergence(predicted, _PREFERENCE)
    assert abs(kl - 2.0) < 1e-12


def test_differential_entropy_of_unit_variance_matches_hand_derivation() -> None:
    belief = BeliefState(mean=0.0, variance=1.0)
    # Hand derivation: H[N(mu, 1)] = 0.5 * ln(2*pi*e*1)
    expected = 0.5 * math.log(2.0 * math.pi * math.e * 1.0)
    assert abs(expected - 1.4189385332046727) < 1e-12  # pin the hand-derived constant itself
    assert gaussian_differential_entropy(belief) == expected


def test_expected_free_energy_matches_hand_computed_value_for_matching_candidate() -> None:
    # Candidate A predicts exactly the preferred outcome: risk = 0, ambiguity = H[N(0,1)].
    candidate_a = BeliefState(mean=0.0, variance=1.0)
    expected_ga = 0.0 + (0.5 * math.log(2.0 * math.pi * math.e * 1.0))
    ga = expected_free_energy(candidate_a, _PREFERENCE)
    assert abs(ga - expected_ga) < 1e-12
    assert abs(ga - 1.4189385332046727) < 1e-9


def test_expected_free_energy_matches_hand_computed_value_for_shifted_candidate() -> None:
    # Candidate B predicts a mean 2.0 away from the preferred outcome: risk = 2.0 (hand-derived above).
    candidate_b = BeliefState(mean=2.0, variance=1.0)
    expected_gb = 2.0 + (0.5 * math.log(2.0 * math.pi * math.e * 1.0))
    gb = expected_free_energy(candidate_b, _PREFERENCE)
    assert abs(gb - expected_gb) < 1e-12
    assert abs(gb - 3.4189385332046727) < 1e-9


def test_decide_picks_the_lower_expected_free_energy_candidate(tmp_path) -> None:  # type: ignore[no-untyped-def]
    agent: Agent[BeliefState] = Agent(new_agent_id(), tmp_path / "decide_only.sqlite3", _PREFERENCE)
    candidates = [
        CandidateAction(name="matches_preference", predicted_state=BeliefState(mean=0.0, variance=1.0)),
        CandidateAction(name="shifted_away", predicted_state=BeliefState(mean=2.0, variance=1.0)),
    ]
    result = agent.decide(candidates)
    agent.close()
    assert isinstance(result, Ok)
    assert result.value.name == "matches_preference"


def test_decide_ties_break_to_the_first_candidate_in_order(tmp_path) -> None:  # type: ignore[no-untyped-def]
    agent: Agent[BeliefState] = Agent(new_agent_id(), tmp_path / "decide_ties.sqlite3", _PREFERENCE)
    identical = BeliefState(mean=1.0, variance=1.0)
    candidates = [
        CandidateAction(name="first", predicted_state=identical),
        CandidateAction(name="second", predicted_state=identical),
    ]
    result = agent.decide(candidates)
    agent.close()
    assert isinstance(result, Ok)
    assert result.value.name == "first"


def test_decide_over_empty_candidates_returns_err_decision_error(tmp_path) -> None:  # type: ignore[no-untyped-def]
    agent: Agent[BeliefState] = Agent(new_agent_id(), tmp_path / "decide_empty.sqlite3", _PREFERENCE)
    result = agent.decide([])
    agent.close()
    assert isinstance(result, Err)
    assert isinstance(result.error, DecisionError)


# --- Third-adversarial-pass negative controls (FirstPrinciples + security find,
# independently converged): BeliefState.variance was constructible as 0.0,
# negative, or non-finite with no guard, only failing three calls later inside
# gaussian_kl_divergence/gaussian_differential_entropy with an undocumented
# ZeroDivisionError/ValueError: math domain error. These prove the fix is
# load-bearing: the ValueError now fires at construction, not deep inside the
# free-energy computation. ---


def test_belief_state_rejects_zero_variance_at_construction_not_inside_free_energy() -> None:
    with pytest.raises(ValueError, match="variance must be finite and > 0.0"):
        BeliefState(mean=0.0, variance=0.0)


def test_belief_state_rejects_negative_variance_at_construction() -> None:
    with pytest.raises(ValueError, match="variance must be finite and > 0.0"):
        BeliefState(mean=0.0, variance=-1.0)


def test_belief_state_rejects_nan_and_inf_variance_at_construction() -> None:
    with pytest.raises(ValueError, match="variance must be finite and > 0.0"):
        BeliefState(mean=0.0, variance=math.nan)
    with pytest.raises(ValueError, match="variance must be finite and > 0.0"):
        BeliefState(mean=0.0, variance=math.inf)


def test_belief_state_accepts_small_positive_variance() -> None:
    belief = BeliefState(mean=0.0, variance=1e-9)
    assert belief.variance == 1e-9
