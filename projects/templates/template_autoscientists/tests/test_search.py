"""Tests for the coordination loop and its ablation toggles.

The public entry point is :func:`run_search`. A few tests below deliberately
reach into the private :class:`_Runner` and its ``_``-prefixed helpers
(``_team_assignment``, ``_fully_retired``, ``state``) to unit-test individual
branches in isolation — exercising them only through ``run_search`` would make
the assertions indirect and brittle. This is a conscious testing trade-off, not
a sign that callers should bypass the ``run_search`` seam.
"""

from __future__ import annotations

from collections.abc import Sequence

import pytest

from src.agents import DeterministicProposer
from src.objective import SyntheticObjective
from src.search import SearchConfig, _Runner, run_search
from src.state import Proposal, SharedState


class _AlternatingProposer:
    """Real proposer that flips probe direction each call (no mocks).

    Unlike :class:`DeterministicProposer` it does not commit to a single
    direction per axis, so on a hopeless objective both directions of an axis
    fail and retire — which is what exercises the loop's all-axes-retired break.
    """

    def __init__(self, step: float = 0.5) -> None:
        self.step = step

    def propose(
        self,
        state: SharedState,
        axes: Sequence[int],
        proposer_id: str,
        avoid: frozenset[tuple[int, str]] = frozenset(),
    ) -> Proposal:
        sign = 1.0 if len(state.log) % 2 == 0 else -1.0
        return Proposal(axis=axes[0], step=sign * self.step, rationale="alt", proposer=proposer_id)


def _objective() -> SyntheticObjective:
    return SyntheticObjective(dimensions=4, noise_scale=0.02)


def test_full_run_improves_over_start() -> None:
    obj = _objective()
    result = run_search(obj, DeterministicProposer(), SearchConfig(budget=40))
    assert result.champion.metric > obj.clean(obj.start_params())
    # The registry-consulting search halts once every direction is exhausted,
    # so it may use fewer than the full budget; both trajectories stay aligned.
    assert 0 < len(result.trajectory) <= 40
    assert len(result.clean_trajectory) == len(result.trajectory)
    assert result.num_confirmed_improvements > 0


def test_run_is_deterministic() -> None:
    obj = _objective()
    a = run_search(obj, DeterministicProposer(), SearchConfig(budget=30))
    b = run_search(obj, DeterministicProposer(), SearchConfig(budget=30))
    assert a.trajectory == b.trajectory
    assert a.champion.metric == b.champion.metric


def test_trajectory_is_monotonic_non_decreasing() -> None:
    # The champion only ever improves, so best-so-far never drops.
    result = run_search(_objective(), DeterministicProposer(), SearchConfig(budget=40))
    for earlier, later in zip(result.trajectory, result.trajectory[1:]):
        assert later >= earlier


def test_single_thread_baseline_config() -> None:
    config = SearchConfig.single_thread_baseline(budget=25)
    assert config.num_teams == 1
    assert config.use_dead_ends is False
    assert config.use_ranking is False
    assert config.use_reorganization is False
    result = run_search(_objective(), DeterministicProposer(), config)
    assert len(result.trajectory) == 25
    assert not result.retired_dead_ends  # registry unused when dead-ends off


def test_dead_ends_get_retired_during_run() -> None:
    result = run_search(_objective(), DeterministicProposer(), SearchConfig(budget=60))
    assert len(result.retired_dead_ends) > 0


def test_confirmation_off_uses_single_seed_path() -> None:
    obj = _objective()
    config = SearchConfig(budget=20, use_confirmation=False)
    result = run_search(obj, DeterministicProposer(), config)
    assert all(o.seed == config.base_seed for o in result.log)


def test_ranking_off_uses_index_team_assignment() -> None:
    runner = _Runner(
        _objective(), DeterministicProposer(), SearchConfig(use_ranking=False, use_dead_ends=False, num_teams=2)
    )
    teams = runner._team_assignment()
    assert teams == [[0, 2], [1, 3]]


def test_team_assignment_with_ranking_and_dead_ends() -> None:
    runner = _Runner(_objective(), DeterministicProposer(), SearchConfig(num_teams=2))
    teams = runner._team_assignment()
    flat = sorted(axis for team in teams for axis in team)
    assert flat == [0, 1, 2, 3]


def test_baseline_metric_matches_confirmation_mean() -> None:
    obj = _objective()
    config = SearchConfig()
    runner = _Runner(obj, DeterministicProposer(), config)
    start = obj.start_params()
    expected = sum(obj.evaluate(start, s) for s in config.confirm_seeds) / len(config.confirm_seeds)
    assert runner.state.champion.metric == expected


def test_baseline_metric_single_seed_without_confirmation() -> None:
    obj = _objective()
    config = SearchConfig(use_confirmation=False)
    runner = _Runner(obj, DeterministicProposer(), config)
    start = obj.start_params()
    assert runner.state.champion.metric == obj.evaluate(start, config.base_seed)


def test_fully_retired_requires_both_directions() -> None:
    runner = _Runner(_objective(), DeterministicProposer(), SearchConfig(dead_end_threshold=1))
    runner.registry.record_failure(0, "increase")
    assert runner._fully_retired(0) is False
    runner.registry.record_failure(0, "decrease")
    assert runner._fully_retired(0) is True


def test_reorganization_runs_without_error_under_tight_window() -> None:
    # A tiny stagnation window forces reorganization to fire mid-run.
    config = SearchConfig(budget=40, stagnation_window=2, use_reorganization=True)
    result = run_search(_objective(), DeterministicProposer(), config)
    assert 0 < len(result.trajectory) <= 40


def test_clean_trajectory_tracks_champion_ground_truth() -> None:
    obj = _objective()
    result = run_search(obj, DeterministicProposer(), SearchConfig(budget=40))
    # Each clean-trajectory point is the noise-free value of the champion at
    # that step, and the champion only improves, so it is non-decreasing and
    # ends at the clean optimum (0.0).
    assert len(result.clean_trajectory) == len(result.trajectory)
    for earlier, later in zip(result.clean_trajectory, result.clean_trajectory[1:]):
        assert later >= earlier
    assert result.clean_trajectory[-1] == obj.clean(result.champion.params)


def test_experiments_to_target_is_reached_and_finite() -> None:
    result = run_search(_objective(), DeterministicProposer(), SearchConfig(budget=60))
    # The deterministic descent reaches the clean optimum well within budget.
    assert result.experiments_to_target is not None
    assert 0 < result.experiments_to_target <= 60


def test_experiments_to_target_is_none_when_optimum_unreached() -> None:
    # An optimum far below the start that no probe can reach within a tiny
    # budget leaves the target flag unset.
    obj = SyntheticObjective(dimensions=1, optimum=(-100.0,), noise_scale=0.0)
    result = run_search(obj, DeterministicProposer(), SearchConfig(budget=3, num_teams=1))
    assert result.experiments_to_target is None


def test_dead_ends_eliminate_redundant_reexploration() -> None:
    # With the registry on, the consulting proposer never re-probes a retired
    # direction; with it off, the same proposer wastes experiments doing so.
    obj = _objective()
    proposer = DeterministicProposer()
    with_registry = run_search(obj, proposer, SearchConfig(budget=60))
    without_registry = run_search(obj, proposer, SearchConfig(budget=60, use_dead_ends=False))
    assert with_registry.redundant_experiments == 0
    assert without_registry.redundant_experiments > 0


def test_dead_ends_do_not_change_the_clean_optimum() -> None:
    # The honesty invariant: search hygiene buys efficiency, not a better answer.
    obj = _objective()
    proposer = DeterministicProposer()
    with_registry = run_search(obj, proposer, SearchConfig(budget=60))
    without_registry = run_search(obj, proposer, SearchConfig(budget=60, use_dead_ends=False))
    assert obj.clean(with_registry.champion.params) == obj.clean(without_registry.champion.params)


def test_run_breaks_when_all_axes_retired() -> None:
    # A 1-D objective whose optimum sits far below the start means every probe
    # fails. The alternating proposer tries both directions, so with threshold 1
    # both retire and the loop has no live axis left — it must break early.
    obj = SyntheticObjective(dimensions=1, optimum=(-100.0,), noise_scale=0.0)
    config = SearchConfig(budget=50, num_teams=1, dead_end_threshold=1, use_confirmation=False)
    result = run_search(obj, _AlternatingProposer(), config)
    assert len(result.trajectory) < 50  # broke early
    assert len(result.retired_dead_ends) == 2  # both directions of axis 0


def test_redundant_experiments_measure_uses_shadow_registry_not_gated() -> None:
    """Shadow registry counts redundant re-probes even when use_dead_ends=False.

    The gated registry (use_dead_ends) steers the search; the shadow is
    always-on and only measures.  Even with the registry turned off the shadow
    still records failures, so redundant_experiments is nonzero in the
    no-registry configuration.
    """
    obj = _objective()
    proposer = DeterministicProposer()
    no_registry = run_search(obj, proposer, SearchConfig(budget=60, use_dead_ends=False))
    # Shadow catches the re-probes that the disabled gated registry misses.
    assert no_registry.redundant_experiments > 0


def test_no_confirmation_allows_noise_inflated_champion() -> None:
    """Negative control: without confirmation the reported metric can diverge from clean.

    With confirmation off, a single noisy evaluation determines acceptance, so
    the champion may be promoted based on a lucky noise draw — the reported
    metric can be larger than the clean ground-truth.  We verify the run
    completes and the two metrics are available for comparison.
    """
    obj = _objective()
    result = run_search(obj, DeterministicProposer(), SearchConfig(budget=40, use_confirmation=False))
    reported = result.champion.metric
    clean = obj.clean(result.champion.params)
    # Both are finite floats; the reported-vs-clean gap is the noise the
    # run accepted without multi-seed filtering.
    assert isinstance(reported, float)
    assert isinstance(clean, float)
    # Confirm the trajectory is non-empty and within the stated budget.
    assert 0 < len(result.trajectory) <= 40


def test_target_tolerance_boundary() -> None:
    """experiments_to_target records the first experiment that crosses the threshold."""
    # The clean optimum is 0.0; with the default tolerance (1e-9) it must be
    # reached exactly.  Use a very relaxed tolerance to verify it fires early.
    obj = _objective()
    config = SearchConfig(budget=60, target_tolerance=100.0)  # trivially satisfied
    result = run_search(obj, DeterministicProposer(), config)
    # With tolerance=100 even the start is within range, so the counter fires
    # on the very first experiment (experiment 1).
    assert result.experiments_to_target == 1


def test_search_config_frozen_prevents_mutation() -> None:
    """SearchConfig is frozen; attribute assignment must raise AttributeError."""
    config = SearchConfig()
    with pytest.raises((AttributeError, TypeError)):
        config.budget = 99  # type: ignore[misc]
