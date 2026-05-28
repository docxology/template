"""Opt-in animation artifacts for the sheaf animation extension track."""

from __future__ import annotations

from pathlib import Path


def write_belief_trajectory_gif(project_root: Path) -> Path:
    """Write a deterministic placeholder GIF derived from the SI entropy figure."""
    from PIL import Image

    root = project_root.resolve()
    source = root / "output" / "figures" / "si_belief_entropy_curve.png"
    if not source.is_file():
        raise FileNotFoundError(
            f"missing {source.relative_to(root)} — run generate_figures.py after simulate_si_tmaze.py"
        )
    out = root / "output" / "figures" / "si_belief_trajectory.gif"
    out.parent.mkdir(parents=True, exist_ok=True)
    frame = Image.open(source).convert("RGBA")
    frame.save(
        out,
        save_all=True,
        append_images=[frame.copy()],
        duration=500,
        loop=0,
    )
    return out
