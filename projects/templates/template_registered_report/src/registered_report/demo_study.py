"""Deterministic demonstration study for the registered-report exemplar.

This module contains **no real empirical data**. It synthesises a small,
fully deterministic two-group dataset from a fixed seed and executes the
*registered* analysis plan (a two-sided label-permutation test on the group
mean difference) so the manuscript can bind every reported number to code
that actually ran. Because the dataset and the permutation schedule are both
seeded, the primary statistic, p-value, and derived figures are byte-stable
across machines.

The computation lives here (tested, importable); figure rendering and I/O
live in ``scripts/`` following the thin-orchestrator pattern.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

__all__ = [
    "AnalysisStage",
    "DemoDataset",
    "HypothesisOutcomeEdge",
    "PermutationResult",
    "TimelineEvent",
    "analysis_plan_stages",
    "deviation_timeline",
    "generate_demo_dataset",
    "hypothesis_outcome_map",
    "mean",
    "permutation_null_distribution",
    "run_permutation_test",
    "run_registered_analysis",
]


@dataclass(frozen=True)
class DemoDataset:
    """A deterministic two-group demonstration dataset.

    Attributes:
        control: Synthetic control-group measurements.
        treatment: Synthetic treatment-group measurements.
    """

    control: tuple[float, ...]
    treatment: tuple[float, ...]

    @property
    def n_control(self) -> int:
        """Return the control-group sample size."""
        return len(self.control)

    @property
    def n_treatment(self) -> int:
        """Return the treatment-group sample size."""
        return len(self.treatment)


@dataclass(frozen=True)
class PermutationResult:
    """Outcome of a two-sided label-permutation test on the mean difference.

    Attributes:
        observed_difference: ``mean(treatment) - mean(control)``.
        control_mean: Mean of the control group.
        treatment_mean: Mean of the treatment group.
        p_value: Two-sided permutation p-value (add-one corrected).
        n_permutations: Number of label shuffles evaluated.
        n_at_least_as_extreme: Shuffles whose absolute mean difference was at
            least as large as the observed absolute difference.
    """

    observed_difference: float
    control_mean: float
    treatment_mean: float
    p_value: float
    n_permutations: int
    n_at_least_as_extreme: int


@dataclass(frozen=True)
class HypothesisOutcomeEdge:
    """A registered hypothesis linked to the outcome and analysis that test it."""

    hypothesis_id: str
    claim: str
    outcome: str
    measure: str
    analysis: str


@dataclass(frozen=True)
class AnalysisStage:
    """One ordered stage of the registered-report analysis workflow."""

    index: int
    key: str
    label: str
    locks_before_results: bool


@dataclass(frozen=True)
class TimelineEvent:
    """One registered-plan-versus-executed-analysis comparison event."""

    order: int
    kind: str
    target: str
    registered: bool
    documented: bool
    severity: str


def mean(values: tuple[float, ...] | list[float]) -> float:
    """Return the arithmetic mean of a non-empty sequence.

    Args:
        values: Numeric samples.

    Returns:
        The arithmetic mean.

    Raises:
        ValueError: If ``values`` is empty.
    """
    if not values:
        raise ValueError("mean() requires at least one value")
    return sum(values) / len(values)


def generate_demo_dataset(
    *,
    seed: int,
    n_per_group: int = 24,
    control_mean: float = 0.0,
    effect: float = 0.8,
    sigma: float = 1.0,
) -> DemoDataset:
    """Generate a deterministic two-group demonstration dataset.

    The control group is drawn from ``Normal(control_mean, sigma)`` and the
    treatment group from ``Normal(control_mean + effect, sigma)`` using a
    single seeded generator, so the whole dataset is a pure function of its
    keyword arguments.

    Args:
        seed: Seed for the pseudo-random generator.
        n_per_group: Samples per group (must be positive).
        control_mean: Mean of the control distribution.
        effect: True shift applied to the treatment distribution.
        sigma: Standard deviation shared by both groups (must be positive).

    Returns:
        A :class:`DemoDataset` with rounded samples for stable display.

    Raises:
        ValueError: If ``n_per_group`` or ``sigma`` is not positive.
    """
    if n_per_group <= 0:
        raise ValueError("n_per_group must be positive")
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    rng = random.Random(seed)
    control = tuple(round(rng.gauss(control_mean, sigma), 6) for _ in range(n_per_group))
    treatment = tuple(round(rng.gauss(control_mean + effect, sigma), 6) for _ in range(n_per_group))
    return DemoDataset(control=control, treatment=treatment)


def permutation_null_distribution(
    dataset: DemoDataset,
    *,
    seed: int,
    n_permutations: int = 2000,
) -> tuple[float, ...]:
    """Return the label-permutation null distribution of the mean difference.

    Pooled measurements are shuffled with a seeded generator and split back
    into two groups of the original sizes; the signed mean difference of each
    shuffle forms the null distribution.

    Args:
        dataset: The two-group dataset.
        seed: Seed for the permutation generator.
        n_permutations: Number of shuffles (must be positive).

    Returns:
        The signed mean-difference for each shuffle, in draw order.

    Raises:
        ValueError: If ``n_permutations`` is not positive.
    """
    if n_permutations <= 0:
        raise ValueError("n_permutations must be positive")
    pooled = list(dataset.control) + list(dataset.treatment)
    n_control = dataset.n_control
    rng = random.Random(seed)
    distribution: list[float] = []
    for _ in range(n_permutations):
        rng.shuffle(pooled)
        control_side = pooled[:n_control]
        treatment_side = pooled[n_control:]
        distribution.append(mean(tuple(treatment_side)) - mean(tuple(control_side)))
    return tuple(distribution)


def run_permutation_test(
    dataset: DemoDataset,
    *,
    seed: int,
    n_permutations: int = 2000,
) -> PermutationResult:
    """Run a two-sided label-permutation test on the mean difference.

    Args:
        dataset: The two-group dataset.
        seed: Seed for the permutation generator.
        n_permutations: Number of shuffles.

    Returns:
        A :class:`PermutationResult`. The p-value uses the add-one correction
        ``(k + 1) / (n_permutations + 1)`` so it is strictly positive.
    """
    control_mean = mean(dataset.control)
    treatment_mean = mean(dataset.treatment)
    observed = treatment_mean - control_mean
    distribution = permutation_null_distribution(dataset, seed=seed, n_permutations=n_permutations)
    threshold = abs(observed)
    at_least_as_extreme = sum(1 for value in distribution if abs(value) >= threshold)
    p_value = (at_least_as_extreme + 1) / (n_permutations + 1)
    return PermutationResult(
        observed_difference=round(observed, 6),
        control_mean=round(control_mean, 6),
        treatment_mean=round(treatment_mean, 6),
        p_value=round(p_value, 6),
        n_permutations=n_permutations,
        n_at_least_as_extreme=at_least_as_extreme,
    )


def run_registered_analysis(
    registration: dict[str, Any],
    *,
    n_per_group: int = 24,
    effect: float = 0.8,
    n_permutations: int = 2000,
) -> dict[str, Any]:
    """Execute the registered analysis plan against fresh demonstration data.

    The seed and significance threshold are read from the registration's
    ``analysis_plan`` so the executed analysis honours the frozen plan. The
    returned mapping is JSON-serialisable and is the single source of truth
    for every primary-outcome number quoted in the manuscript.

    Args:
        registration: A frozen registration mapping.
        n_per_group: Samples per group for the demo dataset.
        effect: True treatment shift injected into the demo dataset.
        n_permutations: Permutation-test shuffle count.

    Returns:
        A mapping with the executed model, seed, alpha, sample sizes, the
        primary-outcome statistics, and a ``significant`` decision flag.
    """
    plan = registration.get("analysis_plan", {})
    seed = int(plan.get("seed", 0))
    alpha = float(plan.get("alpha", 0.05))
    model = str(plan.get("primary_model", "permutation_test"))
    dataset = generate_demo_dataset(seed=seed, n_per_group=n_per_group, effect=effect)
    result = run_permutation_test(dataset, seed=seed, n_permutations=n_permutations)
    outcomes = registration.get("outcomes", [])
    primary_outcome = str(outcomes[0].get("name", "primary_score")) if outcomes else "primary_score"
    return {
        "primary_model": model,
        "seed": seed,
        "alpha": alpha,
        "effect": effect,
        "n_control": dataset.n_control,
        "n_treatment": dataset.n_treatment,
        "primary_outcome": primary_outcome,
        "observed_difference": result.observed_difference,
        "control_mean": result.control_mean,
        "treatment_mean": result.treatment_mean,
        "p_value": result.p_value,
        "n_permutations": result.n_permutations,
        "n_at_least_as_extreme": result.n_at_least_as_extreme,
        "significant": result.p_value < alpha,
        "outcomes": [primary_outcome],
    }


def hypothesis_outcome_map(registration: dict[str, Any]) -> tuple[HypothesisOutcomeEdge, ...]:
    """Map each registered hypothesis onto its outcome, measure, and analysis.

    Hypotheses are paired with outcomes positionally; when there are more
    hypotheses than outcomes the final outcome is reused so no hypothesis is
    dropped from the mapping.

    Args:
        registration: A registration mapping.

    Returns:
        One edge per hypothesis, in registration order.
    """
    hypotheses = registration.get("hypotheses", [])
    outcomes = registration.get("outcomes", [])
    edges: list[HypothesisOutcomeEdge] = []
    for index, hypothesis in enumerate(hypotheses):
        if not isinstance(hypothesis, dict):
            continue
        outcome = outcomes[min(index, len(outcomes) - 1)] if outcomes else {}
        edges.append(
            HypothesisOutcomeEdge(
                hypothesis_id=str(hypothesis.get("id", "")),
                claim=str(hypothesis.get("claim", "")),
                outcome=str(outcome.get("name", "")),
                measure=str(outcome.get("measure", "")),
                analysis=str(outcome.get("analysis", "")),
            )
        )
    return tuple(edges)


def analysis_plan_stages() -> tuple[AnalysisStage, ...]:
    """Return the ordered registered-report analysis workflow stages.

    The first four stages lock *before* results are observed; the final two
    interpret results only after the deviation ledger is built. The boolean
    boundary is what a registered report exists to protect.

    Returns:
        The workflow stages in execution order.
    """
    stages = (
        ("freeze", "Freeze registration", True),
        ("validate", "Validate completeness", True),
        ("collect", "Collect / simulate data", True),
        ("execute", "Execute registered analysis", True),
        ("compare", "Compare to plan + build ledger", False),
        ("interpret", "Interpret confirmatory claims", False),
    )
    return tuple(
        AnalysisStage(index=index, key=key, label=label, locks_before_results=locks)
        for index, (key, label, locks) in enumerate(stages)
    )


def deviation_timeline(
    ledger_rows: tuple[Any, ...] | list[Any],
) -> tuple[TimelineEvent, ...]:
    """Convert deviation-ledger rows into ordered timeline events.

    Args:
        ledger_rows: Rows produced by
            :func:`registered_report.protocol.build_deviation_ledger`. Each row
            must expose ``kind``, ``target``, ``registered``, ``documented``,
            and ``severity`` attributes.

    Returns:
        One timeline event per ledger row, in ledger order.
    """
    events: list[TimelineEvent] = []
    for order, row in enumerate(ledger_rows):
        events.append(
            TimelineEvent(
                order=order,
                kind=str(row.kind),
                target=str(row.target),
                registered=bool(row.registered),
                documented=bool(row.documented),
                severity=str(row.severity),
            )
        )
    return tuple(events)
