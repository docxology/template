"""Animation artifacts for the sheaf animation extension track."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ANIMATION_DELTAS_SCHEMA = "template_active_inference.animation_frame_deltas.v1"


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


def build_animation_frame_deltas(project_root: Path) -> dict[str, Any]:
    """Compute a deterministic manifest proving adjacent GIF frames change."""
    from PIL import Image, ImageChops, ImageSequence

    root = project_root.resolve()
    gif_path = root / "output" / "figures" / "si_belief_trajectory.gif"
    if not gif_path.is_file():
        return {
            "schema": ANIMATION_DELTAS_SCHEMA,
            "artifact": "output/figures/si_belief_trajectory.gif",
            "frame_count": 0,
            "delta_count": 0,
            "rows": [],
            "all_nonzero": False,
        }

    with Image.open(gif_path) as image:
        frames = [frame.convert("RGB") for frame in ImageSequence.Iterator(image)]
    rows: list[dict[str, Any]] = []
    for idx, (left, right) in enumerate(zip(frames, frames[1:], strict=False), start=1):
        diff = ImageChops.difference(left, right)
        bbox = diff.getbbox()
        if bbox is None:
            area = 0
            bbox_values: list[int] = []
        else:
            x0, y0, x1, y1 = bbox
            area = int((x1 - x0) * (y1 - y0))
            bbox_values = [int(x0), int(y0), int(x1), int(y1)]
        rows.append(
            {
                "from_frame": idx - 1,
                "to_frame": idx,
                "changed_bbox": bbox_values,
                "delta_bbox_area": area,
                "nonzero": bool(bbox is not None and area > 0),
            }
        )
    return {
        "schema": ANIMATION_DELTAS_SCHEMA,
        "artifact": "output/figures/si_belief_trajectory.gif",
        "frame_count": len(frames),
        "delta_count": len(rows),
        "rows": rows,
        "all_nonzero": len(frames) >= 2 and bool(rows) and all(row["nonzero"] for row in rows),
    }


def write_animation_frame_deltas(project_root: Path) -> Path:
    """Write the frame-delta manifest for the deterministic animation track."""
    root = project_root.resolve()
    path = root / "output" / "data" / "animation_frame_deltas.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_animation_frame_deltas(root), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def validate_animation_frame_deltas(project_root: Path) -> list[str]:
    """Return frame-delta manifest issues."""
    root = project_root.resolve()
    path = root / "output" / "data" / "animation_frame_deltas.json"
    if not path.is_file():
        return ["missing output/data/animation_frame_deltas.json"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    issues: list[str] = []
    if payload.get("schema") != ANIMATION_DELTAS_SCHEMA:
        issues.append("animation_frame_deltas.json schema mismatch")
    if int(payload.get("frame_count", 0) or 0) < 2:
        issues.append("animation_frame_deltas.json frame count is too small")
    if int(payload.get("delta_count", -1) or -1) != int(payload.get("frame_count", 0) or 0) - 1:
        issues.append("animation_frame_deltas.json delta count does not match frame count")
    if payload.get("all_nonzero") is not True:
        issues.append("animation_frame_deltas.json contains static adjacent frames")
    live = build_animation_frame_deltas(root)
    stable_keys = ("frame_count", "delta_count", "rows", "all_nonzero")
    if payload and {key: payload.get(key) for key in stable_keys} != {key: live.get(key) for key in stable_keys}:
        issues.append("animation_frame_deltas.json is stale relative to GIF frames")
    return issues
