"""Tests for the analysis-figure helpers (no mocks; real PNG output).

The figure functions live in ``src`` so the analysis scripts stay thin. These
tests render each figure with real data and a real ``SearchResult`` (computed by
the deterministic loop) and assert a non-empty PNG is written. Coverage of the
matplotlib drawing code is incidental; correctness here means "produces a valid,
non-empty image file from honest inputs."
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
from infrastructure.validation.content.figure_validator import validate_figure_registry

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from src.agents import DeterministicProposer  # noqa: E402
from src.figures import (  # noqa: E402
    AblationRow,
    ablation_alt_text,
    build_ablation_figure,
    build_comparison_figure,
    build_efficiency_figure,
    comparison_alt_text,
    efficiency_alt_text,
    figure_specs_for_results,
    write_ablation_figure,
    write_comparison_figure,
    write_efficiency_figure,
    write_figure_registry,
)
from src.objective import SyntheticObjective  # noqa: E402
from src.search import SearchConfig, run_search  # noqa: E402

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _rows() -> list[AblationRow]:
    return [
        {
            "configuration": "full coordination",
            "reported_metric": 0.91,
            "clean_metric": 0.90,
            "noise_inflation": 0.01,
            "confirmed_improvements": 7,
            "experiments_used": 60,
            "experiments_to_target": 41,
            "redundant_experiments": 0,
        },
        {
            "configuration": "no dead-end registry",
            "reported_metric": 0.93,
            "clean_metric": 0.88,
            "noise_inflation": 0.05,
            "confirmed_improvements": 6,
            "experiments_used": 60,
            "experiments_to_target": None,
            "redundant_experiments": 12,
        },
    ]


def _assert_png(path: Path) -> None:
    assert path.exists(), f"figure not written: {path}"
    data = path.read_bytes()
    assert data.startswith(_PNG_MAGIC), "output is not a PNG"
    assert len(data) > 1000, "PNG is implausibly small"


def test_write_ablation_figure(tmp_path: Path) -> None:
    path = tmp_path / "ablation.png"
    write_ablation_figure(_rows(), path)
    _assert_png(path)


def test_write_efficiency_figure(tmp_path: Path) -> None:
    path = tmp_path / "efficiency.png"
    write_efficiency_figure(_rows(), path)
    _assert_png(path)


def test_write_comparison_figure(tmp_path: Path) -> None:
    objective = SyntheticObjective(dimensions=4, noise_scale=0.02)
    proposer = DeterministicProposer()
    coordinated = run_search(objective, proposer, SearchConfig(budget=30))
    baseline = run_search(objective, proposer, SearchConfig.single_thread_baseline(budget=30))

    path = tmp_path / "comparison.png"
    write_comparison_figure(coordinated, baseline, path)
    _assert_png(path)


# --- Content assertions (catch axis/label/linestyle regressions a PNG-exists check misses) ---


def test_ablation_figure_content() -> None:
    rows = _rows()
    fig, ax = build_ablation_figure(rows)
    try:
        # Two bar series (reported + clean) × len(rows) bars each.
        bars = ax.containers
        assert len(bars) == 2
        assert all(len(series) == len(rows) for series in bars)
        # y tick labels are the configuration names, in order.
        assert [t.get_text() for t in ax.get_yticklabels()] == [r["configuration"] for r in rows]
        legend = {t.get_text() for t in ax.get_legend().get_texts()}
        assert legend == {"Reported metric", "Clean (ground-truth) metric"}
    finally:
        plt.close(fig)


def test_efficiency_figure_content() -> None:
    rows = _rows()
    fig, ax = build_efficiency_figure(rows)
    try:
        bars = ax.containers
        assert len(bars) == 2
        # First reported bar equals the row's experiments_used (binds plot to data).
        assert bars[0][0].get_width() == rows[0]["experiments_used"]
        legend = {t.get_text() for t in ax.get_legend().get_texts()}
        assert legend == {"Experiments used", "Redundant re-probes of retired directions"}
    finally:
        plt.close(fig)


def test_comparison_figure_linestyle_matches_caption() -> None:
    """@fig:comparison caption: coordinated=solid, baseline=dashed. Pin it."""
    objective = SyntheticObjective(dimensions=4, noise_scale=0.02)
    proposer = DeterministicProposer()
    coordinated = run_search(objective, proposer, SearchConfig(budget=30))
    baseline = run_search(objective, proposer, SearchConfig.single_thread_baseline(budget=30))

    fig, ax = build_comparison_figure(coordinated, baseline)
    try:
        lines = ax.get_lines()
        by_label = {ln.get_label(): ln for ln in lines}
        assert by_label["Coordinated teams"].get_linestyle() == "-"  # solid
        assert by_label["Single-thread baseline"].get_linestyle() == "--"  # dashed
    finally:
        plt.close(fig)


def test_figure_registry_validates_manuscript_references(tmp_path: Path) -> None:
    objective = SyntheticObjective(dimensions=4, noise_scale=0.02)
    proposer = DeterministicProposer()
    coordinated = run_search(objective, proposer, SearchConfig(budget=30))
    baseline = run_search(objective, proposer, SearchConfig.single_thread_baseline(budget=30))

    write_ablation_figure(_rows(), tmp_path / "ablation.png")
    write_efficiency_figure(_rows(), tmp_path / "ablation_efficiency.png")
    write_comparison_figure(coordinated, baseline, tmp_path / "search_comparison.png")
    registry = write_figure_registry(
        tmp_path,
        figure_specs_for_results(coordinated, baseline, _rows()),
    )

    ok, issues = validate_figure_registry(
        registry,
        Path(__file__).resolve().parent.parent / "manuscript",
        require_accessibility=True,
    )

    assert ok, issues


def test_write_figure_registry_schema_version(tmp_path: Path) -> None:
    """The registry JSON carries the expected schema_version sentinel."""
    import json

    path = write_figure_registry(tmp_path)
    payload = json.loads(path.read_text())
    assert payload["schema_version"] == "template-autoscientists-figure-registry-v1"
    assert len(payload["figures"]) == 3  # comparison + ablation + ablation_efficiency
    assert all(record["metadata"]["alt_text"].strip() for record in payload["figures"])


def test_ablation_row_none_experiments_to_target_is_serializable(tmp_path: Path) -> None:
    """A row with experiments_to_target=None must write a valid PNG (no crash)."""
    rows: list[AblationRow] = [
        {
            "configuration": "unreachable",
            "reported_metric": -5.0,
            "clean_metric": -5.0,
            "noise_inflation": 0.0,
            "confirmed_improvements": 0,
            "experiments_used": 60,
            "experiments_to_target": None,
            "redundant_experiments": 0,
        }
    ]
    path = tmp_path / "ablation_none.png"
    write_ablation_figure(rows, path)
    _assert_png(path)


def test_alt_text_changes_with_real_alternate_results() -> None:
    objective = SyntheticObjective(dimensions=4, noise_scale=0.02)
    proposer = DeterministicProposer()
    coordinated_long = run_search(objective, proposer, SearchConfig(budget=30))
    baseline_long = run_search(objective, proposer, SearchConfig.single_thread_baseline(budget=30))
    coordinated_short = run_search(objective, proposer, SearchConfig(budget=8))
    baseline_short = run_search(objective, proposer, SearchConfig.single_thread_baseline(budget=8))
    alternate_rows: list[AblationRow] = [row.copy() for row in _rows()]
    alternate_rows[0]["reported_metric"] = 0.5
    alternate_rows[0]["experiments_used"] = 17
    alternate_rows[0]["redundant_experiments"] = 4

    original = {spec.label: spec for spec in figure_specs_for_results(coordinated_long, baseline_long, _rows())}
    alternate = {
        spec.label: spec
        for spec in figure_specs_for_results(
            coordinated_short,
            baseline_short,
            alternate_rows,
        )
    }

    assert all(alternate[label].alt_text != original[label].alt_text for label in alternate)
    assert "solid coordinated-teams line contains 8 points" in alternate["fig:comparison"].alt_text
    assert "reported 0.5000" in alternate["fig:ablation"].alt_text
    assert "17 used, 4 redundant" in alternate["fig:ablation_efficiency"].alt_text
    assert "not evidence of general agent performance" in alternate["fig:ablation"].alt_text


def test_empty_alt_text_controls_make_no_snapshot_claims() -> None:
    assert "neither" in comparison_alt_text((), ())
    assert "no configuration rows" in ablation_alt_text(())
    assert "no configuration rows" in efficiency_alt_text(())
