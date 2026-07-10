"""A real parameter-sweep runner over ``colony/experiment.py``'s ``run_colony_trial``.

``tests/colony/test_colony_convergence_statistics.py`` establishes one
Wilson-bounded convergence-rate claim at one fixed configuration. Answering
a hypothesis of the shape "does convergence rate change as parameter X
varies" requires running that same real harness at several real values of X
and comparing real Wilson intervals across them -- exactly what a manual,
copy-pasted-per-value test file would do, except reusable, generic over
which field is swept, and itself unit-tested. This module adds that missing
layer: no fabricated or interpolated numbers, no numpy/scipy -- every point
in the returned sweep is ``n_per_value`` real, independently seeded calls to
:func:`~template_formal.colony.experiment.run_colony_trial`, summarized by
:func:`~template_formal.colony.stats.convergence_rate` and
:func:`~template_formal.colony.stats.wilson_score_interval`.

Design choice -- **paired seeds across sweep values**: every value in the
sweep reuses the identical sequence of trial seeds (``seed_base`` ..
``seed_base + n_per_value - 1``), each in its own value-specific
subdirectory of ``db_dir`` (so a shared ``seed`` never collides across two
different sweep values' SQLite files). This means every other source of
randomness in the trial -- the per-agent preference draws, the sensing-noise
sequence -- is held identical across the swept dimension; only the swept
field actually differs between two sweep points run at "the same" seed
index. This is a deliberate variance-reduction choice (a paired-samples
design), not an accident: it makes a rate difference between two sweep
points attributable to the swept parameter, not to which random seeds
happened to land in which bucket.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Mapping, Sequence

from template_formal.colony.experiment import ColonyTrialConfig, run_colony_trial
from template_formal.colony.stats import convergence_rate, wilson_score_interval

_SWEEPABLE_FIELD_NAMES = frozenset(f.name for f in fields(ColonyTrialConfig) if f.name != "seed")
"""Every ``ColonyTrialConfig`` field except ``seed`` may legally be swept --
``seed`` is what varies *within* a sweep point (across its ``n_per_value``
trials), never *across* sweep points, so sweeping it would conflate the two
axes."""


@dataclass(frozen=True, slots=True)
class SweepPointResult:
    """The real, aggregated result of ``n`` trials at one swept value.

    Attributes:
        value: The swept parameter's value at this point.
        n: Number of trials run at this value.
        successes: Number of those trials that converged.
        rate: ``successes / n`` (see
            :func:`~template_formal.colony.stats.convergence_rate`).
        wilson_lower: Lower bound of the Wilson score confidence interval.
        wilson_upper: Upper bound of the Wilson score confidence interval.
    """

    value: float
    n: int
    successes: int
    rate: float
    wilson_lower: float
    wilson_upper: float


def run_parameter_sweep(
    base_config_kwargs: Mapping[str, object],
    *,
    param_name: str,
    values: Sequence[float],
    n_per_value: int,
    seed_base: int,
    db_dir: Path,
    confidence: float = 0.95,
) -> tuple[SweepPointResult, ...]:
    """Run ``n_per_value`` real trials at each of ``values`` for ``param_name``.

    Args:
        base_config_kwargs: Every ``ColonyTrialConfig`` field *except*
            ``seed`` and ``param_name`` itself (``param_name``'s value is
            overridden per sweep point below; a value supplied for it here
            is silently replaced, never merged).
        param_name: Which ``ColonyTrialConfig`` field to vary. Must be a
            real field of ``ColonyTrialConfig`` other than ``seed`` --
            checked eagerly against the dataclass's own field names (not a
            free-text string that could silently typo past every
            downstream check; see the repo's
            ``config-knob-consumption-not-naming`` discipline) rather than
            only failing much later when ``ColonyTrialConfig(**kwargs)``
            raises ``TypeError``.
        values: The real values of ``param_name`` to test, in the order
            reported (must be non-empty).
        n_per_value: How many independently-seeded trials to run at each
            value (must be >= 1).
        seed_base: The first trial seed; trial ``i`` at every sweep point
            uses ``seed_base + i`` (see module docstring for why every
            sweep point reuses the identical seed sequence).
        db_dir: Parent directory for every trial's per-agent SQLite files;
            each sweep point gets its own subdirectory
            (``db_dir / f"{param_name}_point_{index}"``) so trials at
            different values never collide on a shared ``seed``.
        confidence: Two-sided confidence level passed to
            :func:`~template_formal.colony.stats.wilson_score_interval`.

    Returns:
        One :class:`SweepPointResult` per entry in ``values``, in the same
        order.

    Raises:
        ValueError: If ``param_name`` is not a real, sweepable
            ``ColonyTrialConfig`` field, if ``values`` is empty, or if
            ``n_per_value < 1``.
    """
    if param_name not in _SWEEPABLE_FIELD_NAMES:
        raise ValueError(
            f"param_name={param_name!r} is not a sweepable ColonyTrialConfig field "
            f"(valid names: {sorted(_SWEEPABLE_FIELD_NAMES)})"
        )
    if not values:
        raise ValueError("values must be non-empty")
    if n_per_value < 1:
        raise ValueError(f"n_per_value must be >= 1, got {n_per_value}")

    points: list[SweepPointResult] = []
    for index, value in enumerate(values):
        kwargs: dict[str, object] = dict(base_config_kwargs)
        kwargs[param_name] = value
        value_dir = db_dir / f"{param_name}_point_{index}"

        outcomes: list[bool] = []
        for trial_index in range(n_per_value):
            seed = seed_base + trial_index
            # Justification for the ignore below: kwargs is a
            # dict[str, object] built from a caller-supplied Mapping (its
            # keys/shapes come from tests and analysis scripts, not from an
            # untyped external boundary) spread into the strongly-typed
            # ColonyTrialConfig constructor -- mypy cannot verify a dict
            # spread matches a dataclass's field types. The runtime
            # compensating check is ColonyTrialConfig.__post_init__
            # (ISC-80), which validates decay/sensing_noise_std/
            # preference_variance unconditionally on every construction,
            # typed spread or not; param_name itself is separately
            # validated against the dataclass's real field names above.
            config = ColonyTrialConfig(seed=seed, **kwargs)  # type: ignore[arg-type]
            result = run_colony_trial(config, value_dir)
            outcomes.append(result.converged)

        successes = sum(1 for outcome in outcomes if outcome)
        rate = convergence_rate(outcomes)
        lower, upper = wilson_score_interval(successes, n_per_value, confidence=confidence)
        points.append(
            SweepPointResult(
                value=float(value),
                n=n_per_value,
                successes=successes,
                rate=rate,
                wilson_lower=lower,
                wilson_upper=upper,
            )
        )
    return tuple(points)
