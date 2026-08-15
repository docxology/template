"""Direct negative controls for auxiliary-visualization freshness evidence."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from direct_recompute_support import copy_project_tree
from roadmap_tracks.visualization_audit import (
    validate_visualization_quality_audit,
    write_visualization_quality_audit,
)

_AUXILIARY_ISSUE = "stale or unclassified auxiliary visualizations"


def _pattern_image() -> Image.Image:
    image = Image.new("RGB", (96, 64))
    image.putdata(
        [
            ((x * 17 + y * 3) % 256, (x * 5 + y * 11) % 256, (x * 13 + y * 7) % 256)
            for y in range(image.height)
            for x in range(image.width)
        ]
    )
    return image


def _auxiliary_issues(root: Path) -> list[str]:
    return [issue for issue in validate_visualization_quality_audit(root) if _AUXILIARY_ISSUE in issue]


def test_auxiliary_audit_ignores_png_compression_but_rejects_content_and_inventory_drift(
    tmp_path: Path,
) -> None:
    """Same pixels pass; changed, blank, missing, or unclassified images fail."""
    root = copy_project_tree(tmp_path / "project")
    target = root / "output" / "figures" / "transmission_pairing.png"
    image = _pattern_image()
    image.save(target, format="PNG", compress_level=9)
    stored_bytes = target.read_bytes()
    write_visualization_quality_audit(root)

    saved_audit = json.loads(
        (root / "output" / "reports" / "visualization_quality_audit.json").read_text(encoding="utf-8")
    )
    saved_row = next(row for row in saved_audit["auxiliary_visualizations"] if row["path"].endswith(target.name))
    assert saved_row["content_sha256"]
    assert not _auxiliary_issues(root)

    image.save(target, format="PNG", compress_level=0)
    assert target.read_bytes() != stored_bytes
    assert target.stat().st_size != saved_row["size_bytes"]
    assert not _auxiliary_issues(root), "compression-only byte drift must not stale decoded image evidence"

    with Image.open(target) as rendered:
        changed = rendered.convert("RGB")
    red, green, blue = changed.getpixel((5, 5))
    changed.putpixel((5, 5), (255 - red, green, blue))
    changed.save(target, format="PNG", compress_level=0)
    assert _auxiliary_issues(root), "a changed pixel must stale the auxiliary evidence"

    image.save(target, format="PNG", compress_level=0)
    assert not _auxiliary_issues(root)
    unclassified = root / "output" / "figures" / "unclassified_visual.png"
    image.save(unclassified, format="PNG", compress_level=0)
    assert _auxiliary_issues(root), "an unclassified visual output must fail closed"

    unclassified.unlink()
    target.unlink()
    assert _auxiliary_issues(root), "a missing saved auxiliary output must fail closed"

    Image.new("RGB", image.size, "white").save(target, format="PNG", compress_level=0)
    assert _auxiliary_issues(root), "a blank auxiliary output must fail closed"

    image.save(target, format="PNG", compress_level=0)
    assert not _auxiliary_issues(root)
    saved_row["producer"] = "forged.producer"
    (root / "output" / "reports" / "visualization_quality_audit.json").write_text(
        json.dumps(saved_audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    assert _auxiliary_issues(root), "saved classification and producer evidence must remain freshness-bound"
