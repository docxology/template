"""Direct real-file controls for failure-safe figure writes."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pytest

from visualizations.figure_io import save_figure_png


def test_save_figure_png_removes_atomic_work_file_when_save_fails(tmp_path: Path) -> None:
    """A real matplotlib failure must not leave a hidden pseudo-artifact."""
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    output = tmp_path / "figures" / "line.png"

    with pytest.raises(ValueError, match="dpi must be positive"):
        save_figure_png(fig, output, dpi=0)

    assert not output.exists()
    assert not list(output.parent.glob(".line.*.png"))
    assert not plt.fignum_exists(fig.number)
