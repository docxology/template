"""Matplotlib figure rendering for the colony demo/sweep (moved out
of ``scripts/`` per the thin-orchestrator rule -- figure construction,
guarding against empty/near-empty distributions, and computing the plotted
statistics are business logic, not I/O orchestration).

The two functions return ``None`` only when the requested distribution is
honestly unplottable (empty demo history or too few converged trials). Once a
plot is expected, rendering and artifact-quality failures raise: this project
has a publication figure contract, so a missing or blank figure must stop the
analysis stage rather than silently produce a PDF with stale visual evidence.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from template_formal.colony.experiment import ColonyTrialResult
from template_formal.colony.stats import consensus_tick_summary
from template_formal.types.result import Err

from template_formal.colony.demo import LOCATIONS

# Anti (ISC-67-style honesty guard): a plot over fewer than this many
# converged trials would be a near-empty/unreliable distribution -- skip
# the figure with a clear log message rather than draw a misleading
# near-empty histogram or crash on ``statistics.stdev`` of <2 points.
MIN_CONVERGED_FOR_HISTOGRAM = 5


def _validate_rendered_png(output_path: Path) -> None:
    """Fail closed unless ``output_path`` is a readable, non-blank PNG."""
    try:
        with Image.open(output_path) as image:
            image.verify()
        with Image.open(output_path) as image:
            if image.format != "PNG":
                raise RuntimeError(f"expected PNG, got {image.format!r}")
            if image.width < 100 or image.height < 100:
                raise RuntimeError(f"figure is too small: {image.width}x{image.height}")
            colors = image.convert("RGBA").getcolors(maxcolors=4096)
            if colors is not None and len(colors) <= 1:
                raise RuntimeError("figure contains only one rendered color")
    except (OSError, UnidentifiedImageError) as exc:
        raise RuntimeError(f"figure is not a readable PNG: {output_path}") from exc


def write_demo_convergence_figure(
    summary: dict[str, object], figures_dir: Path, *, num_agents: int, num_ticks: int
) -> Path | None:
    """Render the deterministic demo's concentration history: north/south + winner share.

    Two panels over the same 0..``num_ticks - 1`` tick axis:

    - Top: each location's sensed pheromone concentration per tick, read
      directly from ``summary["concentration_history"]`` (real per-tick
      field state, not a re-derivation).
    - Bottom: the eventual winner's share of total concentration per tick
      -- the same "winner's share is non-decreasing and reaches 1.0" claim
      @sec:results-discussion's colony-convergence section already makes
      about this exact deterministic run, plotted rather than only stated.

    This figure documents the *mechanism* demonstration only -- three
    identical agents, a deterministic tie-break -- and is captioned in the
    manuscript accordingly (not presented as emergence or as a rate claim;
    that is :func:`write_convergence_tick_histogram` below).

    Returns the written path, or ``None`` for an empty history. Rendering and
    output-quality failures raise because this figure is part of the
    publication contract.
    """
    concentration_history = summary["concentration_history"]
    assert isinstance(concentration_history, list)  # narrows for mypy/readability only
    if not concentration_history:
        print("demo convergence figure skipped: empty concentration_history", file=sys.stderr)
        return None

    ticks = list(range(len(concentration_history)))
    series: dict[str, list[float]] = {location: [] for location in LOCATIONS}
    for tick_concentrations in concentration_history:
        for location in LOCATIONS:
            series[location].append(float(tick_concentrations[location]))

    final_values = {location: series[location][-1] for location in LOCATIONS}
    winner = max(final_values, key=lambda location: final_values[location])
    totals = [sum(series[location][t] for location in LOCATIONS) for t in ticks]
    winner_share = [(series[winner][t] / totals[t]) if totals[t] > 0.0 else 0.0 for t in ticks]

    import matplotlib.pyplot as plt

    figures_dir.mkdir(parents=True, exist_ok=True)
    output_path = figures_dir / "colony_demo_convergence.png"

    fig, (ax_concentration, ax_share) = plt.subplots(2, 1, figsize=(6, 6), sharex=True)
    try:
        for location in LOCATIONS:
            ax_concentration.plot(ticks, series[location], marker="o", label=location)
        ax_concentration.set_ylabel("sensed pheromone concentration")
        ax_concentration.set_title(f"Deterministic demo colony ({num_agents} agents, {num_ticks} ticks)")
        ax_concentration.legend()

        ax_share.plot(ticks, winner_share, marker="o", color="tab:green")
        ax_share.set_ylim(-0.05, 1.05)
        ax_share.set_xlabel("tick")
        ax_share.set_ylabel(f"'{winner}' share of total concentration")

        fig.tight_layout()
        fig.savefig(output_path, dpi=120)
        _validate_rendered_png(output_path)
        return output_path
    finally:
        plt.close(fig)


def write_convergence_tick_histogram(results: list[ColonyTrialResult], figures_dir: Path) -> Path | None:
    """Render a histogram + ECDF of the real ``consensus_tick`` distribution.

    Guarded honestly against the empty/near-empty case (ISC-67-style
    discipline: no fabricated plot over an unreliable sample): if fewer
    than :data:`MIN_CONVERGED_FOR_HISTOGRAM` trials converged, this logs a
    clear message and returns ``None`` rather than drawing a misleading
    near-empty distribution or crashing on ``statistics.stdev`` of a
    single point.

    Returns the written path, or ``None`` if too few trials converged.
    Rendering and output-quality failures raise because this figure is part of
    the publication contract.
    """
    consensus_ticks = [result.consensus_tick for result in results if result.consensus_tick is not None]
    num_converged = len(consensus_ticks)
    if num_converged < MIN_CONVERGED_FOR_HISTOGRAM:
        print(
            f"convergence-tick histogram skipped: only {num_converged}/{len(results)} trials converged "
            f"(need >= {MIN_CONVERGED_FOR_HISTOGRAM})",
            file=sys.stderr,
        )
        return None

    summary_result = consensus_tick_summary(consensus_ticks)
    if isinstance(summary_result, Err):  # pragma: no cover - unreachable given the guard above
        print(f"convergence-tick histogram skipped: {summary_result.error.reason}", file=sys.stderr)
        return None
    summary = summary_result.value

    sorted_ticks = sorted(consensus_ticks)
    ecdf_y = [(i + 1) / num_converged for i in range(num_converged)]

    import matplotlib.pyplot as plt

    figures_dir.mkdir(parents=True, exist_ok=True)
    output_path = figures_dir / "colony_convergence_tick_distribution.png"

    fig, (ax_hist, ax_ecdf) = plt.subplots(1, 2, figsize=(9, 4))
    try:
        ax_hist.hist(
            consensus_ticks, bins=range(min(sorted_ticks), max(sorted_ticks) + 2), color="tab:blue", edgecolor="white"
        )
        ax_hist.axvline(summary.mean, color="tab:red", linestyle="--", label=f"mean={summary.mean:.1f}")
        ax_hist.set_xlabel("consensus tick")
        ax_hist.set_ylabel("converged trials")
        ax_hist.set_title(f"Histogram (n={summary.n})")
        ax_hist.legend()

        ax_ecdf.step(sorted_ticks, ecdf_y, where="post", color="tab:blue")
        ax_ecdf.set_xlabel("consensus tick")
        ax_ecdf.set_ylabel("empirical CDF")
        ax_ecdf.set_title("ECDF")
        ax_ecdf.set_ylim(0.0, 1.05)

        fig.suptitle(
            f"N={len(results)} heterogeneous trials, {num_converged} converged ({num_converged / len(results):.1%})"
        )
        fig.tight_layout()
        fig.savefig(output_path, dpi=120)
        _validate_rendered_png(output_path)
        return output_path
    finally:
        plt.close(fig)
