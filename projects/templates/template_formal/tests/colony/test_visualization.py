"""Behavioral tests for template_formal.colony.visualization (moved out of
scripts/ per the thin-orchestrator rule -- real business logic now living
in src/, so it needs real test coverage). Real matplotlib, real PNG files
on disk -- no mocking of the rendering call."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from template_formal.colony.demo import (
    DEMO_DEPOSIT_AMOUNT,
    LOCATIONS,
    run_demo_colony,
    run_statistics_sweep,
)
from template_formal.colony.visualization import (
    MIN_CONVERGED_FOR_HISTOGRAM,
    _validate_rendered_png,
    write_convergence_tick_histogram,
    write_demo_convergence_figure,
)


def test_write_demo_convergence_figure_produces_a_real_nonempty_png(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    figures_dir = tmp_path / "figures"
    summary = run_demo_colony(data_dir)

    output_path = write_demo_convergence_figure(
        summary,
        figures_dir,
        num_agents=summary["num_agents"],
        num_ticks=summary["num_ticks"],  # type: ignore[arg-type]
    )

    assert output_path is not None
    assert output_path.name == "colony_demo_convergence.png"
    assert output_path.is_file()
    assert output_path.stat().st_size > 0
    with Image.open(output_path) as image:
        assert image.format == "PNG"
        assert image.width >= 100
        assert image.height >= 100
        colors = image.convert("RGBA").getcolors(maxcolors=4096)
        assert colors is None or len(colors) > 1


def test_write_demo_convergence_figure_returns_none_for_empty_history(tmp_path: Path) -> None:
    empty_summary: dict[str, object] = {"concentration_history": []}
    result = write_demo_convergence_figure(empty_summary, tmp_path, num_agents=0, num_ticks=0)
    assert result is None


def test_write_convergence_tick_histogram_produces_a_real_nonempty_png(tmp_path: Path) -> None:
    config_kwargs: dict[str, object] = {
        "num_agents": 8,
        "locations": LOCATIONS,
        "num_ticks": 20,
        "preference_mean_range": (8.0, 12.0),
        "preference_variance": 1.0,
        "sensing_noise_std": 0.5,
        "deposit_amount": DEMO_DEPOSIT_AMOUNT,
        "decay": 0.46,
    }
    results = run_statistics_sweep(
        tmp_path / "sweep", num_trials=MIN_CONVERGED_FOR_HISTOGRAM + 5, seed_base=7000, config_kwargs=config_kwargs
    )
    figures_dir = tmp_path / "figures"

    output_path = write_convergence_tick_histogram(results, figures_dir)

    num_converged = sum(1 for result in results if result.converged)
    if num_converged < MIN_CONVERGED_FOR_HISTOGRAM:  # pragma: no cover - calibration guard, not expected to fire
        assert output_path is None
        return
    assert output_path is not None
    assert output_path.name == "colony_convergence_tick_distribution.png"
    assert output_path.is_file()
    assert output_path.stat().st_size > 0
    with Image.open(output_path) as image:
        assert image.format == "PNG"
        assert image.width >= 100
        assert image.height >= 100
        colors = image.convert("RGBA").getcolors(maxcolors=4096)
        assert colors is None or len(colors) > 1


def test_figure_writer_surfaces_broken_output_destination(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    blocked_destination = tmp_path / "not_a_directory"
    blocked_destination.write_bytes(b"not a directory")

    with pytest.raises(FileExistsError):
        write_demo_convergence_figure(
            run_demo_colony(data_dir),
            blocked_destination,
            num_agents=3,
            num_ticks=5,
        )


def test_figure_quality_oracle_rejects_invalid_and_blank_pngs(tmp_path: Path) -> None:
    invalid_path = tmp_path / "invalid.png"
    invalid_path.write_bytes(b"not a png")
    with pytest.raises(RuntimeError, match="readable PNG"):
        _validate_rendered_png(invalid_path)

    blank_path = tmp_path / "blank.png"
    Image.new("RGBA", (120, 120), (0, 0, 0, 255)).save(blank_path)
    with pytest.raises(RuntimeError, match="one rendered color"):
        _validate_rendered_png(blank_path)


def test_write_convergence_tick_histogram_skips_below_minimum_converged(tmp_path: Path) -> None:
    """A defeated config (near-total evaporation) that converges on fewer
    than MIN_CONVERGED_FOR_HISTOGRAM trials must skip the figure honestly,
    not draw a misleading near-empty plot."""
    defeated_config: dict[str, object] = {
        "num_agents": 8,
        "locations": LOCATIONS,
        "num_ticks": 10,
        "preference_mean_range": (8.0, 12.0),
        "preference_variance": 1.0,
        "sensing_noise_std": 4.0,
        "deposit_amount": DEMO_DEPOSIT_AMOUNT,
        "decay": 0.97,
    }
    # N=10 (not fewer) so "below minimum converged" is a real property of the
    # defeated config, not merely an artifact of running too few trials to
    # ever reach MIN_CONVERGED_FOR_HISTOGRAM=5 regardless of the mechanism.
    results = run_statistics_sweep(tmp_path / "sweep", num_trials=10, seed_base=8000, config_kwargs=defeated_config)

    output_path = write_convergence_tick_histogram(results, tmp_path / "figures")

    num_converged = sum(1 for result in results if result.converged)
    assert num_converged < MIN_CONVERGED_FOR_HISTOGRAM
    assert output_path is None
