"""Stdlib-only statistical rigor for the colony convergence claim.

No ``numpy``/``scipy`` -- this project's ``pyproject.toml`` declares
neither, and this module is deliberately kept dependency-free so a forking
project's statistics needs no extra install. Every closed-form computation
here is ordinary, exactly-checkable arithmetic (see
``tests/colony/test_colony_stats_unit.py`` for hand-computed expectations
each function is required to match, not merely "runs without error").

:func:`wilson_score_interval` is the load-bearing function: it is what
turns "we ran N trials and R of them converged" into a statistically
honest claim ("the true convergence rate's 95% lower confidence bound
exceeds 0.8") rather than a point estimate that could be a coincidence of
one particular batch of seeds. It derives its critical value from
``statistics.NormalDist().inv_cdf`` -- a real closed-form standard-normal
quantile computation -- rather than a hardcoded ``1.96`` (which is only an
approximation of the exact 95% two-sided z-value,
1.9599639845400545..., and would silently be wrong for any other
``confidence``).
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import Sequence

from template_formal.types.result import Err, Ok, Result


def convergence_rate(outcomes: Sequence[bool]) -> float:
    """The observed fraction of ``outcomes`` that are ``True``.

    Args:
        outcomes: One ``bool`` per trial (typically
            ``ColonyTrialResult.converged`` across many trials).

    Returns:
        ``successes / len(outcomes)``.

    Raises:
        ValueError: If ``outcomes`` is empty -- a rate over zero trials is
            undefined, not zero.
    """
    if not outcomes:
        raise ValueError("cannot compute a convergence rate over zero trials")
    successes = sum(1 for outcome in outcomes if outcome)
    return successes / len(outcomes)


def wilson_score_interval(successes: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """The closed-form Wilson score confidence interval for a binomial proportion.

    Uses the standard Wilson score formula::

        phat = successes / n
        z = NormalDist().inv_cdf(1 - (1 - confidence) / 2)
        center = phat + z**2 / (2*n)
        margin = z * sqrt(phat*(1-phat)/n + z**2/(4*n**2))
        denominator = 1 + z**2/n
        (lower, upper) = ((center - margin) / denominator, (center + margin) / denominator)

    The Wilson interval (rather than the naive normal-approximation
    interval) is used because it stays within ``[0, 1]`` and remains
    well-behaved even when ``phat`` is close to 0 or 1 -- exactly the
    regime a high-convergence-rate claim (e.g. ``phat`` near 0.9+) lives
    in.

    Args:
        successes: Number of trials that converged (``0 <= successes <= n``).
        n: Total number of trials (``n > 0``).
        confidence: Two-sided confidence level, e.g. ``0.95`` for a 95%
            interval (``0 < confidence < 1``).

    Returns:
        ``(lower, upper)``, each clamped to ``[0.0, 1.0]``.

    Raises:
        ValueError: If ``n <= 0``, ``successes`` is outside ``[0, n]``, or
            ``confidence`` is outside ``(0, 1)`` -- including a
            ``confidence`` so close to ``1.0`` that ``1 - (1-confidence)/2``
            rounds to exactly ``1.0`` in float arithmetic (found by a
            third-adversarial-pass RedTeam probe:
            ``wilson_score_interval(5, 10, confidence=0.9999999999999999)``
            previously leaked an undocumented ``statistics.StatisticsError``
            instead of this function's own documented ``ValueError``).
    """
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    if not (0 <= successes <= n):
        raise ValueError(f"successes must be within [0, n], got successes={successes}, n={n}")
    if not (0.0 < confidence < 1.0):
        raise ValueError(f"confidence must be within (0, 1), got {confidence}")

    quantile = 1.0 - (1.0 - confidence) / 2.0
    if not (0.0 < quantile < 1.0):
        raise ValueError(
            f"confidence={confidence} is too close to 1.0 -- "
            f"1 - (1-confidence)/2 rounds to {quantile!r} in float arithmetic, "
            "which has no valid normal quantile"
        )
    z = statistics.NormalDist().inv_cdf(quantile)
    phat = successes / n
    z_squared = z * z
    denominator = 1.0 + z_squared / n
    center = phat + z_squared / (2.0 * n)
    margin = z * math.sqrt(phat * (1.0 - phat) / n + z_squared / (4.0 * n * n))
    lower = (center - margin) / denominator
    upper = (center + margin) / denominator
    return (max(0.0, lower), min(1.0, upper))


@dataclass(frozen=True, slots=True)
class ConsensusTickSummary:
    """Descriptive statistics over a batch of converged trials' consensus ticks.

    Attributes:
        mean: Arithmetic mean of the consensus ticks.
        median: Median (``statistics.median``) of the consensus ticks.
        stdev: Sample standard deviation (``statistics.stdev``); ``0.0``
            when there is only one converged trial (a single observation
            has no sample variance to estimate).
        p25: 25th percentile (inclusive method).
        p50: 50th percentile (inclusive method).
        p75: 75th percentile (inclusive method).
        p90: 90th percentile (inclusive method).
        n: Number of converged trials this summary was computed over.
    """

    mean: float
    median: float
    stdev: float
    p25: float
    p50: float
    p75: float
    p90: float
    n: int


@dataclass(frozen=True, slots=True)
class EmptySummaryError:
    """Returned by :func:`consensus_tick_summary` when there is nothing to summarize."""

    reason: str


def consensus_tick_summary(consensus_ticks: Sequence[int]) -> Result[ConsensusTickSummary, EmptySummaryError]:
    """Summarize a batch of converged trials' consensus ticks -- mean/median/stdev/quantiles.

    Guarded against zero converged trials: rather than letting
    ``statistics.mean``/``statistics.quantiles`` raise
    ``StatisticsError`` on an empty sequence, this returns
    ``Err(EmptySummaryError(...))`` -- "no trial converged" is an expected,
    reportable outcome of a statistical-rigor run, not a programmer error.

    Args:
        consensus_ticks: One consensus-tick index per *converged* trial
            (callers should filter to ``result.consensus_tick`` values
            that are not ``None`` before calling this).

    Returns:
        ``Ok(ConsensusTickSummary(...))``, or
        ``Err(EmptySummaryError(...))`` if ``consensus_ticks`` is empty.
    """
    if not consensus_ticks:
        return Err(EmptySummaryError("cannot summarize consensus ticks over zero converged trials"))
    values = list(consensus_ticks)
    n = len(values)
    mean = statistics.mean(values)
    median = float(statistics.median(values))
    if n >= 2:
        stdev = statistics.stdev(values)
        p25, p50, p75 = statistics.quantiles(values, n=4, method="inclusive")
        deciles = statistics.quantiles(values, n=10, method="inclusive")
        p90 = deciles[8]
    else:
        stdev = 0.0
        p25 = p50 = p75 = p90 = float(values[0])
    return Ok(ConsensusTickSummary(mean=mean, median=median, stdev=stdev, p25=p25, p50=p50, p75=p75, p90=p90, n=n))


def pearson_r(xs: Sequence[float], ys: Sequence[float]) -> float:
    """Hand-derived Pearson product-moment correlation coefficient (no scipy).

    ``r = cov(x, y) / sqrt(var(x) * var(y))``, using the population-style
    (non-Bessel-corrected) sums of squares -- the ``n``/``n-1``
    normalization cancels between numerator and denominator, so this
    matches the standard Pearson ``r`` regardless of which convention is
    used for the individual variance terms.

    Args:
        xs: First series.
        ys: Second series, paired index-for-index with ``xs``.

    Returns:
        The Pearson correlation coefficient in ``[-1.0, 1.0]``. Returns
        ``0.0`` (documented, not a silent ``NaN``/``inf``) if either
        series has zero variance (a constant series has no defined
        correlation direction, so "no linear relationship detected" is
        the honest coercion).

    Raises:
        ValueError: If ``xs``/``ys`` differ in length, or either has
            fewer than 2 observations.
    """
    if len(xs) != len(ys):
        raise ValueError(f"xs and ys must have equal length, got {len(xs)} and {len(ys)}")
    n = len(xs)
    if n < 2:
        raise ValueError(f"pearson_r requires at least 2 paired observations, got {n}")

    mean_x = statistics.mean(xs)
    mean_y = statistics.mean(ys)
    covariance = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    variance_x = sum((x - mean_x) ** 2 for x in xs)
    variance_y = sum((y - mean_y) ** 2 for y in ys)
    if variance_x == 0.0 or variance_y == 0.0:
        return 0.0
    return covariance / math.sqrt(variance_x * variance_y)


def fisher_exact_test_two_sided(successes_a: int, n_a: int, successes_b: int, n_b: int) -> float:
    """Two-sided Fisher's exact test p-value for a 2x2 contingency table.

    Compares two independent binomial samples (``successes_a``/``n_a`` vs
    ``successes_b``/``n_b``) via the exact hypergeometric distribution,
    rather than a normal-approximation two-proportion z-test -- the
    correct choice specifically when one sample sits at or near the ``0``
    or ``n`` boundary (a proportion of exactly ``1.0`` or ``0.0``), where
    normal approximations are known to misbehave (the same boundary
    pathology :func:`wilson_score_interval` was hardened against, see its
    own docstring). Computed purely from ``math.comb`` -- no
    ``scipy.stats.fisher_exact`` dependency.

    The 2x2 table (using "failures" = non-successes in each group)::

                    successes   failures
        group A     successes_a   n_a - successes_a
        group B     successes_b   n_b - successes_b

    The two-sided p-value sums the hypergeometric probability of every
    table at least as extreme (in either direction) as the observed one,
    given the fixed marginal totals -- the standard definition of Fisher's
    exact test.

    Args:
        successes_a: Successes in group A (``0 <= successes_a <= n_a``).
        n_a: Total trials in group A (``n_a > 0``).
        successes_b: Successes in group B (``0 <= successes_b <= n_b``).
        n_b: Total trials in group B (``n_b > 0``).

    Returns:
        The two-sided exact p-value in ``[0.0, 1.0]``.

    Raises:
        ValueError: If any count is out of its valid range.
    """
    if n_a <= 0 or n_b <= 0:
        raise ValueError(f"n_a and n_b must be positive, got n_a={n_a}, n_b={n_b}")
    if not (0 <= successes_a <= n_a):
        raise ValueError(f"successes_a must be within [0, n_a], got {successes_a}")
    if not (0 <= successes_b <= n_b):
        raise ValueError(f"successes_b must be within [0, n_b], got {successes_b}")

    total_n = n_a + n_b
    total_successes = successes_a + successes_b
    low = max(0, total_successes - n_b)
    high = min(n_a, total_successes)

    def hypergeom_pmf(k: int) -> float:
        return math.comb(total_successes, k) * math.comb(total_n - total_successes, n_a - k) / math.comb(total_n, n_a)

    observed_p = hypergeom_pmf(successes_a)
    # Two-sided: sum every table at least as extreme (probability no
    # greater than the observed table's probability, within float
    # tolerance), over every value the "successes in group A" cell could
    # take given the fixed marginals.
    #
    # The tolerance MUST be relative, not additive (a cross-vendor audit
    # caught this: an earlier revision used `observed_p + 1e-10`, which is
    # only a safe float-equality guard when observed_p is itself order
    # 1e-10 or larger. For a highly-separated table -- e.g. 60/60 vs 0/60,
    # observed_p ~= 1e-35 -- the additive `1e-10` fudge term completely
    # swallows observed_p, so the inequality degenerated to "include every
    # table with pmf <= 1e-10", summing a huge, wrong swath of the tail
    # instead of only tables as extreme as observed. That bug inflated the
    # true two-sided p-value (2.07e-35 for the 60/60-vs-0/60 table,
    # independently confirmed against scipy.stats.fisher_exact and a
    # direct 2/C(120,60) computation) by 24 orders of magnitude, to
    # 4.31e-11. A relative tolerance scales with observed_p itself, so it
    # stays a tight float-equality guard at every magnitude.
    return sum(hypergeom_pmf(k) for k in range(low, high + 1) if hypergeom_pmf(k) <= observed_p * (1.0 + 1e-9))


def cochran_armitage_trend_test(
    ns: Sequence[int],
    successes: Sequence[int],
    scores: Sequence[float],
) -> tuple[float, float]:
    """Two-sided Cochran--Armitage test for a linear trend in a binary proportion (no scipy).

    Where :func:`fisher_exact_test_two_sided` compares *two* groups' success
    proportions, this answers the ordered-sweep question the pairwise test
    cannot: across ``k >= 2`` groups laid out at ordered numeric ``scores``
    (e.g. an increasing ``decay`` or an increasing preference-range width),
    is there a single, whole-sequence *linear association* between the score
    and the success proportion? It is the textbook test for exactly this
    design -- an ordered explanatory variable with a **binary** response
    (originally: dose-response with a binary endpoint, Cochran 1954 /
    Armitage 1955; see Agresti, *Categorical Data Analysis*) -- and is used
    here in preference to a Jonckheere--Terpstra test precisely because the
    response (``ColonyTrialResult.converged``) is binary, not ranked.

    The standard closed-form statistic for ``k`` ordered groups with scores
    ``x_i``, trial counts ``n_i``, and successes ``r_i``::

        N = sum(n_i) ; R = sum(r_i) ; xbar = sum(n_i * x_i) / N ; pbar = R / N
        numerator   = sum(x_i * r_i) - R * xbar
        denominator = sqrt( pbar * (1 - pbar) * sum(n_i * (x_i - xbar)**2) )
        Z = numerator / denominator          (~ N(0, 1) under H0)
        p = 2 * (1 - Phi(|Z|))               (two-sided)

    The null hypothesis H0 is that the success probability is *constant*
    across all groups (no linear trend); ``Z`` is asymptotically standard
    normal under H0, and ``p`` is the two-sided tail obtained from
    ``statistics.NormalDist().cdf`` -- a real closed-form standard-normal CDF
    computation, not a hardcoded critical value, matching the discipline of
    :func:`wilson_score_interval`.

    Interpretation caveat this function's callers must respect (it answers a
    *different* question than :func:`fisher_exact_test_two_sided`): a
    significant ``Z`` is evidence of a broad, whole-sequence *linear*
    association -- an overall increasing or decreasing tendency -- and is
    **not** evidence about, nor evidence against, *local* non-monotonicity
    between any specific adjacent pair. A sweep with a strong low-to-high
    rise and a small interior dip can yield a large significant ``Z`` (the
    dominant linear signal) while the interior dip remains real and is
    separately established by a pairwise test. Both statistics should be
    reported; neither supersedes the other.

    Args:
        ns: Trial count ``n_i`` per group (each ``> 0``), in score order.
        successes: Converged-trial count ``r_i`` per group
            (each ``0 <= r_i <= n_i``), index-aligned with ``ns``.
        scores: The ordered numeric score ``x_i`` assigned to each group
            (e.g. the actual ``decay`` value or preference-range width),
            index-aligned with ``ns``. Need not be evenly spaced.

    Returns:
        ``(z, p)``: the signed trend Z-statistic and its two-sided p-value.
        A positive ``z`` indicates success proportion rising with the score;
        a negative ``z`` indicates it falling. When the pooled success
        proportion ``pbar`` is exactly ``0.0`` or ``1.0`` -- every trial in
        every group failed, or every one succeeded -- the response is
        constant, so no trend is even defined; this returns ``(0.0, 1.0)``
        (the honest "no detectable trend, outcome is constant" coercion,
        mirroring :func:`pearson_r`'s ``0.0`` on a zero-variance series)
        rather than dividing by a zero denominator.

    Raises:
        ValueError: If ``ns``/``successes``/``scores`` differ in length; if
            there are fewer than 2 groups; if any ``n_i <= 0`` or any
            ``r_i`` is outside ``[0, n_i]``; or if all ``scores`` are
            identical (then ``sum(n_i * (x_i - xbar)**2) == 0`` and a trend
            along a constant score axis is undefined -- a real degeneracy,
            raised rather than silently returning a meaningless statistic).
    """
    if not (len(ns) == len(successes) == len(scores)):
        raise ValueError(
            f"ns, successes, scores must have equal length, got {len(ns)}, {len(successes)}, {len(scores)}"
        )
    k = len(ns)
    if k < 2:
        raise ValueError(f"cochran_armitage_trend_test requires at least 2 groups, got {k}")
    for index, (n_i, r_i) in enumerate(zip(ns, successes)):
        if n_i <= 0:
            raise ValueError(f"every n_i must be positive, got ns[{index}]={n_i}")
        if not (0 <= r_i <= n_i):
            raise ValueError(
                f"every successes_i must be within [0, n_i], got successes[{index}]={r_i}, ns[{index}]={n_i}"
            )

    total_n = sum(ns)
    total_successes = sum(successes)
    pbar = total_successes / total_n
    if pbar == 0.0 or pbar == 1.0:
        # Constant response across every group (all failures or all
        # successes): there is no proportion variation for a score to be
        # associated with, so "no detectable trend" is the honest answer,
        # not a 0/0 division.
        return (0.0, 1.0)

    mean_score = sum(n_i * x_i for n_i, x_i in zip(ns, scores)) / total_n
    weighted_score_variance = sum(n_i * (x_i - mean_score) ** 2 for n_i, x_i in zip(ns, scores))
    if weighted_score_variance == 0.0:
        raise ValueError("all scores are identical -- a linear trend along a constant score axis is undefined")

    numerator = sum(x_i * r_i for x_i, r_i in zip(scores, successes)) - total_successes * mean_score
    denominator = math.sqrt(pbar * (1.0 - pbar) * weighted_score_variance)
    z = numerator / denominator
    p_value = 2.0 * (1.0 - statistics.NormalDist().cdf(abs(z)))
    return (z, p_value)
