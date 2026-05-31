"""Animation artifacts for the sheaf animation extension track."""

from __future__ import annotations

import json
from pathlib import Path


def _load_trace_steps(root: Path) -> list[dict]:
    graph_trace = root / "output" / "data" / "si_graph_world_trace.json"
    si_trace = root / "output" / "data" / "si_tmaze_trace.json"
    path = graph_trace if graph_trace.is_file() else si_trace
    if not path.is_file():
        raise FileNotFoundError(
            "missing trace artifact under output/data — run simulate_si_tmaze.py or simulate_si_graph_world.py"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    steps = list(payload.get("steps") or [])
    if len(steps) < 2:
        raise ValueError(f"{path.relative_to(root)} must contain at least two steps for animation")
    return steps


def write_belief_trajectory_gif(project_root: Path) -> Path:
    """Write a deterministic multi-frame GIF from trace entropy/action state."""
    from PIL import Image, ImageDraw

    root = project_root.resolve()
    steps = _load_trace_steps(root)
    out = root / "output" / "figures" / "si_belief_trajectory.gif"
    out.parent.mkdir(parents=True, exist_ok=True)
    max_entropy = max(float(step.get("belief_entropy", 0.0)) for step in steps) or 1.0
    frames: list[Image.Image] = []
    width, height = 420, 180
    for idx, step in enumerate(steps):
        frame = Image.new("RGBA", (width, height), (248, 250, 252, 255))
        draw = ImageDraw.Draw(frame)
        progress = idx / max(len(steps) - 1, 1)
        entropy = float(step.get("belief_entropy", 0.0))
        node = str(step.get("node", step.get("obs", idx)))
        action = str(step.get("action", ""))
        draw.rectangle((24, 118, width - 24, 132), fill=(226, 232, 240, 255))
        draw.rectangle((24, 118, 24 + int((width - 48) * progress), 132), fill=(15, 118, 110, 255))
        bar_height = int(72 * entropy / max_entropy)
        draw.rectangle((44, 100 - bar_height, 92, 100), fill=(37, 99, 235, 255))
        draw.ellipse((width - 80, 46, width - 32, 94), fill=(220, 252, 231, 255), outline=(15, 118, 110, 255))
        draw.text((24, 20), f"step {idx}", fill=(17, 24, 39, 255))
        draw.text((112, 54), f"state: {node}", fill=(17, 24, 39, 255))
        draw.text((112, 78), f"action: {action}", fill=(100, 116, 139, 255))
        draw.text((24, 142), f"belief entropy {entropy:.4f} nats", fill=(17, 24, 39, 255))
        frames.append(frame)
    frames[0].save(
        out,
        save_all=True,
        append_images=frames[1:],
        duration=450,
        loop=0,
    )
    return out
