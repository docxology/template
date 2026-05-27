from pathlib import Path

from analysis import run_analysis
from visualizations.figures import generate_all_figures
from simulation.si_runner import pymdp_available, run_and_persist


def test_analytical_sweep_writes_csv(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    # use project root logic but write under tmp by copying approach
    paths = run_analysis(root)
    assert paths["parameter_sweep"].exists()


def test_figures_after_pipeline_artifacts() -> None:
    root = Path(__file__).resolve().parents[1]
    from manuscript.sheaf import compose_all_sections

    if pymdp_available():
        run_and_persist(root)
    run_analysis(root)
    compose_all_sections(root)
    figs = generate_all_figures(root)
    assert len(figs) >= 3
    assert all(p.exists() for p in figs)
    heatmap = root / "output" / "figures" / "sheaf_coverage_heatmap.png"
    assert heatmap in figs
    assert heatmap.exists()
