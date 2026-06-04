"""The AutoScientists coordination loop.

Ties the mechanisms together into a propose -> filter -> evaluate -> confirm ->
promote -> reorganize cycle over a fixed experiment budget. Each mechanism can
be switched off via :class:`SearchConfig`, which is what the ablation script
uses to reproduce the paper's "remove one component" table. With every toggle
off and a single team, the loop reduces to the single-thread baseline.

The loop is deterministic given the objective, proposer, and config, so the
rendered trajectories are reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .agents import Proposer
from .confirmation import confirm_improvement
from .dead_ends import DeadEnd, DeadEndRegistry
from .objective import SyntheticObjective
from .ranking import rank_axes
from .stagnation import StagnationDetector, reorganize_axes
from .state import Champion, ExperimentOutcome, Proposal, SharedState


@dataclass(frozen=True)
class SearchConfig:
    """Toggles and budgets controlling one search run."""

    budget: int = 60
    num_teams: int = 3
    use_confirmation: bool = True
    use_dead_ends: bool = True
    use_ranking: bool = True
    use_reorganization: bool = True
    confirm_seeds: tuple[int, ...] = (101, 202, 303)
    base_seed: int = 7
    stagnation_window: int = 10
    dead_end_threshold: int = 3
    sigma: float = 2.0
    target_tolerance: float = 1e-9

    @classmethod
    def single_thread_baseline(cls, budget: int = 60) -> SearchConfig:
        """Config matching a single-agent baseline: one team, no coordination."""
        return cls(
            budget=budget,
            num_teams=1,
            use_confirmation=True,
            use_dead_ends=False,
            use_ranking=False,
            use_reorganization=False,
        )


@dataclass(frozen=True)
class SearchResult:
    """Outcome of a search run.

    ``trajectory`` is the reported (noisy) champion metric per experiment;
    ``clean_trajectory`` is the noise-free ground-truth value of the same
    champion, so the gap between them is exactly the noise the confirmation
    mechanism failed to filter. ``experiments_to_target`` and
    ``redundant_experiments`` are the honest *efficiency* signals: how soon the
    clean optimum was reached and how often the search re-probed a direction the
    dead-end registry had already retired.
    """

    champion: Champion
    trajectory: tuple[float, ...]
    clean_trajectory: tuple[float, ...]
    num_confirmed_improvements: int
    retired_dead_ends: tuple[DeadEnd, ...]
    experiments_to_target: int | None
    redundant_experiments: int
    log: tuple[ExperimentOutcome, ...]


@dataclass
class _Runner:
    objective: SyntheticObjective
    proposer: Proposer
    config: SearchConfig
    state: SharedState = field(init=False)
    registry: DeadEndRegistry = field(init=False)
    shadow: DeadEndRegistry = field(init=False)
    detector: StagnationDetector = field(init=False)

    def __post_init__(self) -> None:
        start = self.objective.start_params()
        metric = self._baseline_metric(start)
        self.state = SharedState(champion=Champion(params=start, metric=metric, experiment_index=-1))
        self.registry = DeadEndRegistry(threshold=self.config.dead_end_threshold)
        # Always-on mirror used purely to *measure* redundant re-exploration,
        # so the figure can compare configurations that have the registry off.
        # It never steers the search; only ``registry`` (gated by use_dead_ends)
        # does that.
        self.shadow = DeadEndRegistry(threshold=self.config.dead_end_threshold)
        self.detector = StagnationDetector(window=self.config.stagnation_window)

    def _baseline_metric(self, params: tuple[float, ...]) -> float:
        if self.config.use_confirmation:
            samples = [self.objective.evaluate(params, seed) for seed in self.config.confirm_seeds]
            return sum(samples) / len(samples)
        return self.objective.evaluate(params, self.config.base_seed)

    def _all_axes(self) -> list[int]:
        return list(range(self.objective.dimensions))

    def _team_assignment(self) -> list[list[int]]:
        axes = rank_axes(self.state.log, self._all_axes()) if self.config.use_ranking else self._all_axes()
        if self.config.use_dead_ends:
            return reorganize_axes(axes, self.config.num_teams, self.registry)
        teams: list[list[int]] = [[] for _ in range(self.config.num_teams)]
        for index, axis in enumerate(axes):
            teams[index % self.config.num_teams].append(axis)
        return teams

    def _evaluate(self, proposal: Proposal) -> ExperimentOutcome:
        params = list(self.state.champion.params)
        params[proposal.axis] += proposal.step
        candidate = tuple(params)
        primary = self.objective.evaluate(candidate, self.config.base_seed)
        if self.config.use_confirmation:
            check = confirm_improvement(
                self.objective.evaluate,
                candidate,
                self.state.champion.metric,
                self.config.confirm_seeds,
                self.objective.noise_scale,
                sigma=self.config.sigma,
            )
            metric, delta, confirmed = check.candidate_mean, check.delta, check.confirmed
        else:
            metric = primary
            delta = primary - self.state.champion.metric
            confirmed = delta > 0.0
        return ExperimentOutcome(
            proposal=proposal,
            params=candidate,
            metric=metric,
            delta_vs_champion=delta,
            seed=self.config.base_seed,
            confirmed=confirmed,
        )

    def run(self) -> SearchResult:
        trajectory: list[float] = []
        clean_trajectory: list[float] = []
        confirmed_improvements = 0
        redundant_experiments = 0
        experiments_to_target: int | None = None
        teams = self._team_assignment()
        for experiment in range(self.config.budget):
            team_axes = teams[experiment % len(teams)] or self._all_axes()
            if self.config.use_dead_ends:
                live = [a for a in team_axes if not self._fully_retired(a)]
                team_axes = live or [a for a in self._all_axes() if not self._fully_retired(a)]
            if not team_axes:
                break
            avoid = self.registry.retired_keys() if self.config.use_dead_ends else frozenset()
            proposal = self.proposer.propose(self.state, team_axes, f"team{experiment % len(teams)}", avoid)
            if (proposal.axis, proposal.direction) in self.shadow.retired_keys():
                redundant_experiments += 1
            outcome = self._evaluate(proposal)
            self.state.record(outcome)
            self._update_registry(outcome)
            self._update_shadow(outcome)
            if outcome.improved:
                confirmed_improvements += 1
            if self.config.use_reorganization and self.detector.is_stagnant(self.state):
                teams = self._team_assignment()
            trajectory.append(self.state.best_so_far())
            clean_value = self.objective.clean(self.state.champion.params)
            clean_trajectory.append(clean_value)
            if experiments_to_target is None and clean_value >= -self.config.target_tolerance:
                experiments_to_target = experiment + 1
        return SearchResult(
            champion=self.state.champion,
            trajectory=tuple(trajectory),
            clean_trajectory=tuple(clean_trajectory),
            num_confirmed_improvements=confirmed_improvements,
            retired_dead_ends=self.registry.retired(),
            experiments_to_target=experiments_to_target,
            redundant_experiments=redundant_experiments,
            log=tuple(self.state.log),
        )

    def _fully_retired(self, axis: int) -> bool:
        return self.registry.is_dead_end(axis, "increase") and self.registry.is_dead_end(axis, "decrease")

    def _update_registry(self, outcome: ExperimentOutcome) -> None:
        if not self.config.use_dead_ends:
            return
        axis, direction = outcome.proposal.axis, outcome.proposal.direction
        if outcome.improved:
            self.registry.record_success(axis, direction)
        else:
            self.registry.record_failure(axis, direction)

    def _update_shadow(self, outcome: ExperimentOutcome) -> None:
        axis, direction = outcome.proposal.axis, outcome.proposal.direction
        if outcome.improved:
            self.shadow.record_success(axis, direction)
        else:
            self.shadow.record_failure(axis, direction)


def run_search(
    objective: SyntheticObjective,
    proposer: Proposer,
    config: SearchConfig | None = None,
) -> SearchResult:
    """Run one coordinated (or baseline) search and return its result."""
    return _Runner(objective, proposer, config or SearchConfig()).run()
