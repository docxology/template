"""Statistical rigor for the colony convergence claim (N=150 real trials).

``tests/colony/test_colony_integration.py`` proves the stigmergic
positive-feedback *mechanism* is real with one fixed, symmetric
configuration. This module proves a *rate* claim about that mechanism
under realistic variation -- heterogeneous per-agent preferences and
nonzero sensing noise (see ``colony/experiment.py``'s
:func:`~template_formal.colony.experiment.run_colony_trial`) -- using a
genuine, falsifiable statistical test rather than a single anecdotal run:

    H0: the true colony convergence rate is <= 0.8.
    Rejected at alpha=0.05 iff the real Wilson 95% lower confidence bound
    (:func:`~template_formal.colony.stats.wilson_score_interval`) over
    N=150 real trials exceeds 0.8.

Three guards keep this claim honest:

1. **Heterogeneity non-vacuity** (below): the injected per-agent
   preference spread is confirmed actually nonzero -- this is not a
   relabeled version of the old, fully-symmetric configuration.
2. **Negative control**: re-running the OLD deterministic configuration
   (identical preferences, zero sensing noise) through this SAME new
   harness must reproduce exact, literal 100% convergence -- proving the
   original test's "guaranteed by construction" claim is a real,
   reproducible fact under the harness that also produces the >0.8 claim
   above, not a coincidence of two unrelated code paths.
3. **Positive-control-that-can-fail**: an intentionally-defeated
   configuration (near-total pheromone evaporation each tick + noise far
   exceeding the preference-mean signal) must show a Wilson *upper* bound
   well below 0.5 -- proving the >0.8 gate is not vacuously satisfied by
   every configuration regardless of whether the underlying mechanism
   actually works.

All configuration parameters below (``num_agents=8``, ``decay=0.46``,
``sensing_noise_std=0.5``, ...) were hand-calibrated by iterating on
``preference_mean_range``/``sensing_noise_std``/``decay``/``num_ticks``
against real trial batches until the true rate sat comfortably above 0.8
(observed ~0.93-0.95 across multiple independent seed-base re-runs during
calibration), not tuned to sit exactly at the 0.8 boundary.
"""

from __future__ import annotations

import math
import time
from statistics import pstdev

import pytest

from template_formal.colony.experiment import ColonyTrialConfig, ColonyTrialResult, run_colony_trial
from template_formal.colony.stats import convergence_rate, pearson_r, wilson_score_interval

_MAIN_N = 150
_WALL_CLOCK_BUDGET_SECONDS = 45.0
"""Generous soft budget: calibration runs of N=150 trials measured ~9s
locally. A budget well above that (rather than a tight one) avoids a
flaky CI failure on a slower runner while still catching a genuine
performance regression (e.g. an accidental O(n^2) blowup) that would push
the real number an order of magnitude higher."""

_GOOD_CONFIG_KWARGS: dict[str, object] = {
    "num_agents": 8,
    "locations": ("north", "south"),
    "num_ticks": 30,
    "preference_mean_range": (8.0, 12.0),
    "preference_variance": 1.0,
    "sensing_noise_std": 0.5,
    "deposit_amount": 1.0,
    "decay": 0.46,
}
"""The calibrated configuration the >0.8 convergence-rate claim is bound to."""


def _run_batch(n: int, db_dir, seed0: int, **kwargs: object) -> list[ColonyTrialResult]:  # type: ignore[no-untyped-def]
    return [
        run_colony_trial(ColonyTrialConfig(seed=seed0 + i, **kwargs), db_dir)  # type: ignore[arg-type]
        for i in range(n)
    ]


@pytest.fixture(scope="module")
def main_batch(tmp_path_factory):  # type: ignore[no-untyped-def]
    """Run the N=150 calibrated-configuration batch exactly once per module.

    Several tests below examine different statistical facets of the same
    batch (rate, heterogeneity, correlation, timing) -- computing it once
    keeps the real wall-clock cost of this file to one N=150 run, not
    four.
    """
    db_dir = tmp_path_factory.mktemp("colony_stats_main")
    start = time.perf_counter()
    results = _run_batch(_MAIN_N, db_dir, seed0=0, **_GOOD_CONFIG_KWARGS)
    elapsed = time.perf_counter() - start
    return results, elapsed


def test_wall_clock_benchmark_stays_within_budget(main_batch) -> None:  # type: ignore[no-untyped-def]
    _, elapsed = main_batch
    print(f"\nN={_MAIN_N} colony trials wall-clock: {elapsed:.2f}s")
    assert elapsed < _WALL_CLOCK_BUDGET_SECONDS, (
        f"N={_MAIN_N} trial batch took {elapsed:.2f}s, exceeding the "
        f"{_WALL_CLOCK_BUDGET_SECONDS}s budget -- reduce N or investigate a regression"
    )


def test_true_convergence_rate_wilson_lower_bound_exceeds_0_8(main_batch) -> None:  # type: ignore[no-untyped-def]
    """H0: true convergence rate <= 0.8. Rejected at alpha=0.05 iff the real
    Wilson 95% lower bound over N=150 real trials exceeds 0.8."""
    results, _ = main_batch
    outcomes = [result.converged for result in results]
    successes = sum(1 for outcome in outcomes if outcome)
    rate = convergence_rate(outcomes)
    lower, upper = wilson_score_interval(successes, _MAIN_N, confidence=0.95)
    print(f"convergence: successes={successes}/{_MAIN_N} rate={rate:.4f} wilson_95%=({lower:.4f}, {upper:.4f})")
    assert lower > 0.8, (
        f"H0 (true convergence rate <= 0.8) NOT rejected: Wilson 95% lower "
        f"bound {lower:.4f} does not exceed 0.8 (successes={successes}/{_MAIN_N})"
    )
    # Comfortably above the boundary, not merely clearing it by a hair.
    assert rate > 0.85, f"observed rate {rate:.4f} is not comfortably above 0.8"


def test_heterogeneity_guard_preference_spread_is_actually_nonzero(main_batch) -> None:  # type: ignore[no-untyped-def]
    """Non-vacuity guard: confirm the injected preference heterogeneity is
    real, not a relabeled identical-preferences configuration."""
    results, _ = main_batch
    spreads = [pstdev(result.preference_means) for result in results]
    assert min(spreads) > 0.0, "every trial must show real, nonzero preference heterogeneity"
    assert max(spreads) > min(spreads), "preference spread must actually vary trial-to-trial, not be a constant"


def test_negative_control_identical_preferences_zero_noise_converges_exactly(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Re-run the OLD deterministic configuration (identical preferences,
    zero sensing noise -- matching
    ``tests/colony/test_colony_integration.py``'s 3-agent, 2-location,
    5-tick setup) through THIS new seeded/noisy harness. The manuscript's
    "guaranteed by construction" claim about that configuration is only
    honest if it reproduces exact, literal 100% convergence under the same
    harness that also produces the >0.8 statistical claim above -- not a
    claim resting on two unrelated code paths.
    """
    results = _run_batch(
        20,
        tmp_path,
        seed0=0,
        num_agents=3,
        locations=("north", "south"),
        num_ticks=5,
        preference_mean_range=(10.0, 10.0),  # identical preference for every agent
        preference_variance=1.0,
        sensing_noise_std=0.0,  # zero noise
        deposit_amount=1.0,
        decay=0.02,
    )
    outcomes = [result.converged for result in results]
    assert convergence_rate(outcomes) == 1.0
    for result in results:
        assert result.converged
        # Unanimous from the very first tick, per the original test's
        # documented tie-break mechanism (identical agents, identical
        # empty field -> identical free-energy minimizer for all).
        assert result.consensus_tick == 0


def test_positive_control_that_can_fail_wilson_upper_bound_well_below_0_5(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Anti-vacuity for the >0.8 gate above.

    Decay near 1.0 wipes out essentially all pheromone reinforcement every
    tick (no lasting positive feedback), and sensing noise (std=4.0) is
    far larger than the entire preference-mean range (8-12) -- if this
    deliberately-defeated configuration still cleared a high convergence
    rate, the >0.8 gate above would be suspect (satisfiable regardless of
    whether the underlying stigmergic mechanism does anything at all).
    """
    n = 50
    results = _run_batch(
        n,
        tmp_path,
        seed0=0,
        num_agents=8,
        locations=("north", "south"),
        num_ticks=30,
        preference_mean_range=(8.0, 12.0),
        preference_variance=1.0,
        sensing_noise_std=4.0,  # noise swamps the preference-mean signal
        deposit_amount=1.0,
        decay=0.97,  # near-total evaporation each tick -- no lasting reinforcement
    )
    outcomes = [result.converged for result in results]
    successes = sum(1 for outcome in outcomes if outcome)
    rate = convergence_rate(outcomes)
    _, upper = wilson_score_interval(successes, n, confidence=0.95)
    print(f"positive-control-that-can-fail: successes={successes}/{n} rate={rate:.4f} wilson_upper={upper:.4f}")
    assert upper < 0.5, (
        f"the defeated configuration's Wilson upper bound {upper:.4f} is not "
        "well below 0.5 -- the >0.8 gate above would be vacuously satisfiable"
    )


def test_exploratory_pearson_correlation_preference_spread_vs_consensus_tick(main_batch) -> None:  # type: ignore[no-untyped-def]
    """Exploratory only: correlate each converged trial's preference spread
    against its consensus tick. Asserted only as "finite" plus a loose
    non-degenerate-direction guard -- per the statistics-specialist spec,
    NOT hard-asserted to a tight sign/magnitude without cross-run
    calibration (a single mechanism-level run is not enough evidence for
    a precise correlation claim, only enough to confirm the computation
    itself is well-defined and not a degenerate +-1.0 artifact).
    """
    results, _ = main_batch
    converged = [result for result in results if result.converged and result.consensus_tick is not None]
    assert len(converged) >= 2, "need at least 2 converged trials for a correlation to be defined"
    spreads = [pstdev(result.preference_means) for result in converged]
    ticks = [float(result.consensus_tick) for result in converged]
    r_value = pearson_r(spreads, ticks)
    print(f"exploratory pearson r (preference spread vs consensus tick): {r_value:.4f}")
    assert math.isfinite(r_value)
    # Loose guard only: reject an implausibly perfect correlation in
    # either direction (which would suggest a degenerate/artifactual
    # relationship), without pinning a specific sign or magnitude.
    assert -0.99 < r_value < 0.99
