"""Unit tests for ``colony/stats.py``'s pure functions, plus ``experiment.py``'s
pure ``find_sustained_consensus_tick`` -- all hand-crafted-fixture, none
derived from a real simulation run (that's what
``test_colony_convergence_statistics.py`` is for).

Every expected value below is computed independently of the function
under test (either genuinely by hand from the documented closed-form
formula, or via a *different* stdlib call than the one the function under
test itself uses) -- never by calling the function under test and
asserting it equals itself.
"""

from __future__ import annotations

import math

import pytest

from template_formal.colony.experiment import find_sustained_consensus_tick
from template_formal.colony.stats import (
    EmptySummaryError,
    cochran_armitage_trend_test,
    consensus_tick_summary,
    convergence_rate,
    fisher_exact_test_two_sided,
    pearson_r,
    wilson_score_interval,
)
from template_formal.types.result import Err, Ok

# --------------------------------------------------------------------------
# convergence_rate
# --------------------------------------------------------------------------


def test_convergence_rate_all_true_is_one() -> None:
    assert convergence_rate([True, True, True]) == 1.0


def test_convergence_rate_all_false_is_zero() -> None:
    assert convergence_rate([False, False, False, False]) == 0.0


def test_convergence_rate_mixed_matches_hand_computed_fraction() -> None:
    # 3 of 5 True -> 0.6, computed by hand, not derived from the function.
    outcomes = [True, False, True, True, False]
    assert convergence_rate(outcomes) == pytest.approx(0.6)


def test_convergence_rate_raises_on_empty_sequence() -> None:
    with pytest.raises(ValueError, match="zero trials"):
        convergence_rate([])


# --------------------------------------------------------------------------
# wilson_score_interval -- hand-computed against the documented closed-form
# formula, using the well-known standard-normal critical values
# z(0.95) = 1.9599639845400545 and z(0.90) = 1.6448536269514722 (independent
# mathematical constants, not obtained by calling this module's code).
# --------------------------------------------------------------------------


def _hand_wilson(successes: int, n: int, z: float) -> tuple[float, float]:
    """Reference Wilson-interval computation, hand-derived from the formula
    directly in this test file (deliberately *not* calling
    ``wilson_score_interval`` itself -- see module docstring)."""
    phat = successes / n
    z2 = z * z
    denominator = 1.0 + z2 / n
    center = phat + z2 / (2.0 * n)
    margin = z * math.sqrt(phat * (1.0 - phat) / n + z2 / (4.0 * n * n))
    return ((center - margin) / denominator, (center + margin) / denominator)


def test_wilson_score_interval_matches_hand_computed_95_percent_example() -> None:
    # successes=95, n=100, confidence=0.95.
    # Hand-computed (via _hand_wilson with the independently-known z(0.95)
    # constant above): lower=0.8882495307680808, upper=0.9784563208456318.
    expected_lower, expected_upper = 0.8882495307680808, 0.9784563208456318
    lower, upper = wilson_score_interval(95, 100, confidence=0.95)
    assert lower == pytest.approx(expected_lower, abs=1e-5)
    assert upper == pytest.approx(expected_upper, abs=1e-5)
    # Cross-check the hand-reference implementation in this file agrees too.
    ref_lower, ref_upper = _hand_wilson(95, 100, 1.9599639845400545)
    assert lower == pytest.approx(ref_lower, abs=1e-9)
    assert upper == pytest.approx(ref_upper, abs=1e-9)


def test_wilson_score_interval_matches_hand_computed_90_percent_example() -> None:
    # successes=10, n=20, confidence=0.90.
    # Hand-computed: lower=0.32740376788515596, upper=0.6725962321148441.
    expected_lower, expected_upper = 0.32740376788515596, 0.6725962321148441
    lower, upper = wilson_score_interval(10, 20, confidence=0.90)
    assert lower == pytest.approx(expected_lower, abs=1e-5)
    assert upper == pytest.approx(expected_upper, abs=1e-5)


def test_wilson_score_interval_bounds_stay_within_unit_interval() -> None:
    lower, upper = wilson_score_interval(150, 150, confidence=0.95)
    assert 0.0 <= lower <= upper <= 1.0


def test_wilson_score_interval_n_equals_one_all_success_is_a_controlled_result() -> None:
    """Edge case: the smallest legal batch size, a single success. Must
    return a well-defined, finite, in-range interval -- not raise, not
    NaN/inf -- exercising the ``n=1`` denominator through every term of
    the closed-form formula (``z**2/n``, ``z**2/(4*n**2)``)."""
    lower, upper = wilson_score_interval(1, 1, confidence=0.95)
    assert 0.0 <= lower <= upper <= 1.0
    assert math.isfinite(lower) and math.isfinite(upper)


def test_wilson_score_interval_n_equals_one_all_failure_is_a_controlled_result() -> None:
    """Edge case: the smallest legal batch size, a single failure."""
    lower, upper = wilson_score_interval(0, 1, confidence=0.95)
    assert 0.0 <= lower <= upper <= 1.0
    assert math.isfinite(lower) and math.isfinite(upper)
    assert lower == 0.0


def test_wilson_score_interval_raises_on_nonpositive_n() -> None:
    with pytest.raises(ValueError, match="n must be positive"):
        wilson_score_interval(0, 0)


def test_wilson_score_interval_raises_on_successes_out_of_range() -> None:
    with pytest.raises(ValueError, match="successes must be within"):
        wilson_score_interval(11, 10)
    with pytest.raises(ValueError, match="successes must be within"):
        wilson_score_interval(-1, 10)


def test_wilson_score_interval_raises_on_confidence_out_of_range() -> None:
    with pytest.raises(ValueError, match="confidence must be within"):
        wilson_score_interval(5, 10, confidence=1.0)


def test_wilson_score_interval_raises_valueerror_not_statistics_error_near_one() -> None:
    """Third-adversarial-pass regression: a RedTeam probe found
    confidence=0.9999999999999999 satisfies 0.0 < confidence < 1.0 but makes
    1 - (1-confidence)/2 round to exactly 1.0, which previously leaked an
    undocumented statistics.StatisticsError from NormalDist().inv_cdf(1.0)
    instead of this function's own documented ValueError."""
    with pytest.raises(ValueError, match="too close to 1.0"):
        wilson_score_interval(5, 10, confidence=0.9999999999999999)
    # One tick below the rounding boundary still works normally.
    lower, upper = wilson_score_interval(5, 10, confidence=0.999999999999999)
    assert 0.0 <= lower <= upper <= 1.0
    with pytest.raises(ValueError, match="confidence must be within"):
        wilson_score_interval(5, 10, confidence=0.0)


# --------------------------------------------------------------------------
# consensus_tick_summary -- ground truth computed via a direct call to the
# stdlib ``statistics`` module in this test (ordinary round numbers chosen
# so the arithmetic is independently checkable), not via
# ``consensus_tick_summary`` itself.
# --------------------------------------------------------------------------


def test_consensus_tick_summary_matches_hand_verified_statistics() -> None:
    # values = [10, 20, 30, 40]; ground truth via `statistics` directly:
    # mean=25, median=25.0, stdev=12.909944487358056,
    # quartiles=[17.5, 25.0, 32.5], 90th-percentile decile cut = 37.0.
    result = consensus_tick_summary([10, 20, 30, 40])
    assert isinstance(result, Ok)
    summary = result.value
    assert summary.n == 4
    assert summary.mean == pytest.approx(25.0)
    assert summary.median == pytest.approx(25.0)
    assert summary.stdev == pytest.approx(12.909944487358056)
    assert summary.p25 == pytest.approx(17.5)
    assert summary.p50 == pytest.approx(25.0)
    assert summary.p75 == pytest.approx(32.5)
    assert summary.p90 == pytest.approx(37.0)


def test_consensus_tick_summary_single_value_has_zero_stdev() -> None:
    result = consensus_tick_summary([7])
    assert isinstance(result, Ok)
    summary = result.value
    assert summary.n == 1
    assert summary.mean == pytest.approx(7.0)
    assert summary.stdev == 0.0
    assert summary.p25 == summary.p50 == summary.p75 == summary.p90 == pytest.approx(7.0)


def test_consensus_tick_summary_returns_err_on_zero_converged_trials() -> None:
    result = consensus_tick_summary([])
    assert isinstance(result, Err)
    assert isinstance(result.error, EmptySummaryError)


# --------------------------------------------------------------------------
# pearson_r -- known-shape series (perfect positive/negative correlation,
# and a degenerate zero-variance series), computed by hand.
# --------------------------------------------------------------------------


def test_pearson_r_perfect_positive_correlation_is_one() -> None:
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    ys = [2.0, 4.0, 6.0, 8.0, 10.0]  # ys = 2*xs, exact linear relationship
    assert pearson_r(xs, ys) == pytest.approx(1.0)


def test_pearson_r_perfect_negative_correlation_is_negative_one() -> None:
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    ys = [10.0, 8.0, 6.0, 4.0, 2.0]  # ys = -2*xs + 12, exact inverse relationship
    assert pearson_r(xs, ys) == pytest.approx(-1.0)


def test_pearson_r_zero_variance_series_returns_zero_not_nan() -> None:
    xs = [5.0, 5.0, 5.0, 5.0]  # constant -> zero variance
    ys = [1.0, 2.0, 3.0, 4.0]
    r = pearson_r(xs, ys)
    assert r == 0.0
    assert math.isfinite(r)


def test_pearson_r_raises_on_mismatched_lengths() -> None:
    with pytest.raises(ValueError, match="equal length"):
        pearson_r([1.0, 2.0], [1.0])


def test_pearson_r_raises_on_fewer_than_two_observations() -> None:
    with pytest.raises(ValueError, match="at least 2"):
        pearson_r([1.0], [1.0])


# --------------------------------------------------------------------------
# find_sustained_consensus_tick -- hand-crafted fixtures (not derived from
# any real simulation run).
# --------------------------------------------------------------------------


def test_sustained_consensus_from_tick_one() -> None:
    # Unanimous on "north" from the very first tick, through the last.
    choice_history = [
        ("north", "north", "north"),
        ("north", "north", "north"),
        ("north", "north", "north"),
    ]
    assert find_sustained_consensus_tick(choice_history) == 0


def test_agreement_then_broken_returns_the_later_sustained_point() -> None:
    # Tick 0 is a false start: unanimous on "north", but tick 1 breaks
    # agreement. Tick 2 onward is a genuine sustained consensus on "south".
    # The correct answer is 2 (the later, real sustained point) -- NOT 0
    # (the earlier false start that didn't hold).
    choice_history = [
        ("north", "north", "north"),  # false start: unanimous but doesn't hold
        ("north", "south", "north"),  # disagreement -- breaks the tick-0 "start"
        ("south", "south", "south"),  # genuine sustained start
        ("south", "south", "south"),
        ("south", "south", "south"),
    ]
    assert find_sustained_consensus_tick(choice_history) == 2


def test_never_converges_returns_none() -> None:
    # Disagreement persists through the very last tick -- no sustained
    # consensus tick exists anywhere in this history.
    choice_history = [
        ("north", "south", "north"),
        ("south", "north", "south"),
        ("north", "north", "south"),
        ("south", "north", "north"),
    ]
    assert find_sustained_consensus_tick(choice_history) is None


def test_empty_choice_history_returns_none() -> None:
    assert find_sustained_consensus_tick([]) is None


def test_single_unanimous_tick_is_trivially_sustained() -> None:
    assert find_sustained_consensus_tick([("north", "north")]) == 0


def test_multiple_false_starts_before_the_real_sustained_run() -> None:
    # Two separate false starts (tick 0 on "north", tick 2 on "south"),
    # each broken by the following tick, before the real sustained run
    # (on "north" again) begins at tick 4.
    choice_history = [
        ("north", "north"),  # false start #1
        ("south", "north"),  # breaks it
        ("south", "south"),  # false start #2
        ("north", "south"),  # breaks it
        ("north", "north"),  # genuine sustained start
        ("north", "north"),
    ]
    assert find_sustained_consensus_tick(choice_history) == 4


# --------------------------------------------------------------------------
# fisher_exact_test_two_sided -- added to back manuscript/05_results_discussion.md's
# precision correction (a second Forge cross-vendor pass found the decay
# 0.8->1.0 "not statistical noise" phrasing overreached what a formal test
# supports; this pins the real, computed p-value the corrected prose quotes).
# --------------------------------------------------------------------------


def test_fisher_exact_matches_manuscript_quoted_decay_dip_pvalue() -> None:
    # 60/60 (decay in {0.60, 0.80}) vs 56/60 (decay=1.00) -- see
    # manuscript/05_results_discussion.md's "Precision correction" paragraph.
    p = fisher_exact_test_two_sided(60, 60, 56, 60)
    assert abs(p - 0.1187244128420599) < 1e-9
    # Not significant at the conventional alpha=0.05 threshold -- this is
    # exactly the point the manuscript's precision correction makes.
    assert p > 0.05


def test_fisher_exact_is_symmetric_in_group_order() -> None:
    assert fisher_exact_test_two_sided(60, 60, 56, 60) == fisher_exact_test_two_sided(56, 60, 60, 60)


def test_fisher_exact_identical_proportions_gives_p_close_to_one() -> None:
    p = fisher_exact_test_two_sided(30, 60, 30, 60)
    assert p > 0.9


def test_fisher_exact_extreme_difference_gives_small_p() -> None:
    # The real-vs-null comparison (140/150 vs 1/150) should be overwhelmingly significant.
    p = fisher_exact_test_two_sided(140, 150, 1, 150)
    assert p < 1e-6


def test_fisher_exact_perfectly_separated_table_matches_hand_computed_value() -> None:
    """Regression test for a real bug a cross-vendor audit caught (round 8):
    the two-sided tail's tolerance was additive (``observed_p + 1e-10``),
    which is only a safe float-equality guard when ``observed_p`` is itself
    around ``1e-10`` or larger. For a perfectly-separated 2x2 table --
    60/60 vs 0/60, whose observed hypergeometric probability is
    ``~1e-35`` -- the additive fudge term completely swallowed
    ``observed_p``, so the two-sided sum degenerated to "every table with
    pmf <= 1e-10" instead of "every table at least as extreme as observed",
    inflating the true p-value (``2/C(120,60) = 2.070073888186964e-35``,
    the closed-form two-sided value for this symmetric, maximally-extreme
    table) by 24 orders of magnitude to a wrong ``4.31e-11``. Fixed to a
    relative tolerance; this test pins the correct value against an
    independent hand computation (``2/C(120,60)``, not the function's own
    internal route), so a regression back to an additive tolerance would
    fail this test immediately rather than only showing up as a silently
    wrong number three call-sites away in a manuscript quote."""
    p = fisher_exact_test_two_sided(60, 60, 0, 60)
    expected = 2.0 / math.comb(120, 60)
    assert p == pytest.approx(expected, rel=1e-9)
    assert p == pytest.approx(2.070073888186964e-35, rel=1e-9)
    assert p < 1e-30, "a perfectly-separated table must be overwhelmingly significant, not merely 'small'"


def test_fisher_exact_raises_on_nonpositive_n() -> None:
    with pytest.raises(ValueError, match="must be positive"):
        fisher_exact_test_two_sided(1, 0, 1, 10)


def test_fisher_exact_raises_on_successes_out_of_range() -> None:
    with pytest.raises(ValueError, match="successes_a must be within"):
        fisher_exact_test_two_sided(11, 10, 5, 10)
    with pytest.raises(ValueError, match="successes_b must be within"):
        fisher_exact_test_two_sided(5, 10, -1, 10)


# --------------------------------------------------------------------------
# cochran_armitage_trend_test -- the Z-statistic is hand-derived directly
# from the documented closed-form formula, and the two-sided p-value is
# cross-checked via math.erfc(|z|/sqrt(2)) -- a DIFFERENT stdlib route
# (math.erfc) than the function itself uses (statistics.NormalDist().cdf),
# per this module's independent-expectation convention.
# --------------------------------------------------------------------------


def test_cochran_armitage_matches_hand_computed_two_group_example() -> None:
    # The minimum valid group count (k=2) is a real, mathematically distinct
    # code path from the >=3-group case above -- pinned separately rather
    # than only covered by the "raises below 2 groups" boundary test.
    # ns=[10,10], successes=[3,9], scores=[0,1]. Hand-computed:
    #   N=20, R=12, xbar=(0*10+1*10)/20=0.5, pbar=12/20=0.6
    #   numerator   = (0*3 + 1*9) - 12*0.5 = 9 - 6 = 3
    #   sum n_i(x_i-xbar)^2 = 10*0.25 + 10*0.25 = 5
    #   denominator = sqrt(0.6*0.4*5) = sqrt(1.2)
    #   Z = 3 / sqrt(1.2) = 2.7386127875258306 (a positive rising trend)
    z, p = cochran_armitage_trend_test([10, 10], [3, 9], [0.0, 1.0])
    expected_z = 3.0 / math.sqrt(1.2)
    assert z == pytest.approx(expected_z, abs=1e-12)
    expected_p = math.erfc(abs(expected_z) / math.sqrt(2.0))
    assert p == pytest.approx(expected_p, abs=1e-12)
    assert p < 0.05  # significant rising trend


def test_cochran_armitage_matches_hand_computed_three_group_example() -> None:
    # ns=[10,10,10], successes=[2,5,8], scores=[0,1,2]. Hand-computed:
    #   N=30, R=15, xbar=(0*10+1*10+2*10)/30 = 1.0, pbar=15/30=0.5
    #   numerator   = (0*2 + 1*5 + 2*8) - 15*1.0 = 21 - 15 = 6
    #   sum n_i(x_i-xbar)^2 = 10*1 + 10*0 + 10*1 = 20
    #   denominator = sqrt(0.5*0.5*20) = sqrt(5)
    #   Z = 6 / sqrt(5) = 2.6832815729997477 (a positive rising trend)
    z, p = cochran_armitage_trend_test([10, 10, 10], [2, 5, 8], [0.0, 1.0, 2.0])
    expected_z = 6.0 / math.sqrt(5.0)
    assert z == pytest.approx(expected_z, abs=1e-12)
    # Two-sided tail via an independent stdlib route (erfc, not NormalDist).
    expected_p = math.erfc(abs(expected_z) / math.sqrt(2.0))
    assert p == pytest.approx(expected_p, abs=1e-12)
    assert p < 0.05  # significant rising trend


def test_cochran_armitage_matches_manuscript_full_decay_sweep() -> None:
    # The full ordered decay sweep pinned in the experiments module:
    # scores {0.10,0.30,0.46,0.60,0.80,1.00}, n=60 each, successes
    # {0,0,56,60,60,56}. A strong POSITIVE (rising) whole-sequence trend --
    # which does NOT contradict the local 0.60/0.80-vs-1.00 dip that
    # test_fisher_exact_matches_manuscript_quoted_decay_dip_pvalue pins.
    z, p = cochran_armitage_trend_test(
        [60, 60, 60, 60, 60, 60], [0, 0, 56, 60, 60, 56], [0.10, 0.30, 0.46, 0.60, 0.80, 1.00]
    )
    assert z == pytest.approx(14.568352736133356, abs=1e-6)
    assert p < 1e-10


def test_cochran_armitage_matches_manuscript_full_heterogeneity_sweep() -> None:
    # The full ordered heterogeneity sweep: widths {2,4,10,16}, n=60 each,
    # successes {60,56,15,2}. A strong NEGATIVE (falling) trend.
    z, p = cochran_armitage_trend_test([60, 60, 60, 60], [60, 56, 15, 2], [2.0, 4.0, 10.0, 16.0])
    assert z == pytest.approx(-12.755854588960661, abs=1e-6)
    assert p < 1e-10


def test_cochran_armitage_p_value_agrees_with_erfc_route_on_the_decay_sweep() -> None:
    # Belt-and-suspenders: the module's NormalDist-based p must agree with
    # the erfc-based two-sided tail on a real (non-degenerate) sweep too.
    z, p = cochran_armitage_trend_test([60, 60, 60], [5, 30, 55], [0.0, 1.0, 2.0])
    assert p == pytest.approx(math.erfc(abs(z) / math.sqrt(2.0)), abs=1e-12)


def test_cochran_armitage_all_successes_returns_no_trend_not_division_by_zero() -> None:
    # Degenerate pbar == 1.0 (every trial in every group succeeded): the
    # response is constant, so there is no trend to detect -- (0.0, 1.0),
    # not a 0/0 crash.
    z, p = cochran_armitage_trend_test([10, 10, 10], [10, 10, 10], [0.0, 1.0, 2.0])
    assert z == 0.0
    assert p == 1.0


def test_cochran_armitage_all_failures_returns_no_trend() -> None:
    # Degenerate pbar == 0.0 (every trial failed).
    z, p = cochran_armitage_trend_test([10, 10], [0, 0], [1.0, 2.0])
    assert z == 0.0
    assert p == 1.0


def test_cochran_armitage_raises_on_constant_scores() -> None:
    # All scores identical -> zero score variance -> a trend along a
    # constant axis is undefined -> ValueError, not a silent 0/0.
    with pytest.raises(ValueError, match="all scores are identical"):
        cochran_armitage_trend_test([10, 10, 10], [2, 5, 8], [1.0, 1.0, 1.0])


def test_cochran_armitage_raises_on_mismatched_lengths() -> None:
    with pytest.raises(ValueError, match="equal length"):
        cochran_armitage_trend_test([10, 10], [2, 5, 8], [0.0, 1.0, 2.0])


def test_cochran_armitage_raises_on_fewer_than_two_groups() -> None:
    with pytest.raises(ValueError, match="at least 2 groups"):
        cochran_armitage_trend_test([10], [5], [0.0])


def test_cochran_armitage_raises_on_nonpositive_n() -> None:
    with pytest.raises(ValueError, match="n_i must be positive"):
        cochran_armitage_trend_test([10, 0], [5, 0], [0.0, 1.0])


def test_cochran_armitage_raises_on_successes_out_of_range() -> None:
    with pytest.raises(ValueError, match="successes_i must be within"):
        cochran_armitage_trend_test([10, 10], [5, 11], [0.0, 1.0])


def test_cochran_armitage_sign_flips_with_score_direction() -> None:
    # Reversing the score axis must negate Z (same data, mirrored scores).
    z_rising, _ = cochran_armitage_trend_test([20, 20, 20], [2, 10, 18], [0.0, 1.0, 2.0])
    z_falling, _ = cochran_armitage_trend_test([20, 20, 20], [2, 10, 18], [2.0, 1.0, 0.0])
    assert z_rising == pytest.approx(-z_falling, abs=1e-12)
    assert z_rising > 0.0
