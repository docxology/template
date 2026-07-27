"""Controls for compression-invariant image content hashing.

The point of `roadmap_tracks.image_content_hash` is to be insensitive to PNG
compression and sensitive to everything else. A hash helper that is merely
insensitive would pass every artifact forever, so each property below is pinned
in both directions: a re-compression must NOT change the digest, and a
one-pixel edit, a resize, and an injected metadata chunk each MUST.

Originating defect (2026-07-27): `artifact_diffoscope.json` compared raw bytes.
Pillow ships a platform-specific wheel bundling its own zlib, so the committed
figures re-encoded differently on a different machine — 22 of 25 PNGs byte-
different, 0 pixel-different — and the gate could only be satisfied by re-pinning
the snapshot to whoever ran last.

Real files on disk throughout; no mocks.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from roadmap_tracks.image_content_hash import image_content_sha256, is_image_artifact

PIL = pytest.importorskip("PIL", reason="Pillow ships with matplotlib in this project")
from PIL import Image, PngImagePlugin  # noqa: E402


def _square(path: Path, *, colour: tuple[int, int, int] = (10, 120, 200), size: int = 24, level: int = 6) -> Path:
    Image.new("RGB", (size, size), colour).save(path, format="PNG", compress_level=level)
    return path


def test_recompression_does_not_change_the_content_hash(tmp_path: Path) -> None:
    """The whole point: identical picture, different compression, same digest."""
    fast = _square(tmp_path / "fast.png", level=1)
    slow = _square(tmp_path / "slow.png", level=9)

    assert fast.read_bytes() != slow.read_bytes(), "fixture failed to produce differing bytes"
    assert image_content_sha256(fast) == image_content_sha256(slow)


def test_single_pixel_change_does_change_the_content_hash(tmp_path: Path) -> None:
    """Positive control — the digest must still detect a real content edit."""
    original = _square(tmp_path / "a.png")
    before = image_content_sha256(original)

    with Image.open(original) as image:
        edited = image.convert("RGB")
    edited.putpixel((0, 0), (255, 0, 0))
    edited.save(tmp_path / "b.png", format="PNG")

    assert image_content_sha256(tmp_path / "b.png") != before


def test_resize_changes_the_content_hash(tmp_path: Path) -> None:
    a = _square(tmp_path / "a.png", size=24)
    b = _square(tmp_path / "b.png", size=25)
    assert image_content_sha256(a) != image_content_sha256(b)


def test_injected_metadata_chunk_changes_the_content_hash(tmp_path: Path) -> None:
    """Metadata is a tamper surface even though nothing here writes it today."""
    plain = _square(tmp_path / "plain.png")
    before = image_content_sha256(plain)

    info = PngImagePlugin.PngInfo()
    info.add_text("Comment", "injected")
    with Image.open(plain) as image:
        image.convert("RGB").save(tmp_path / "tagged.png", format="PNG", pnginfo=info)

    assert image_content_sha256(tmp_path / "tagged.png") != before


def test_missing_file_yields_empty_digest_not_a_false_match(tmp_path: Path) -> None:
    """Absent evidence must read as absent, never as a passing comparison."""
    assert image_content_sha256(tmp_path / "nope.png") == ""


def test_is_image_artifact_routes_only_raster_suffixes() -> None:
    assert is_image_artifact("output/figures/x.png")
    assert is_image_artifact("output/figures/x.gif")
    assert not is_image_artifact("output/data/x.json")
    assert not is_image_artifact("output/data/x.csv")


def test_live_figures_all_produce_a_content_digest() -> None:
    """Bind the helper to the real tree, not just fixtures."""
    figures = Path(__file__).resolve().parents[1] / "output" / "figures"
    images = sorted(p for p in figures.glob("*") if p.suffix.lower() in {".png", ".gif"})
    assert images, "no figures found — the scan set went empty"
    assert all(image_content_sha256(p) for p in images)


def test_diffoscope_compares_content_for_images_and_bytes_for_data() -> None:
    """The gate must declare, per row, which digest it actually compared."""
    import json

    root = Path(__file__).resolve().parents[1]
    report = json.loads((root / "output" / "reports" / "artifact_diffoscope.json").read_text(encoding="utf-8"))
    assert report["schema"].endswith(".artifact_diffoscope.v2")
    rows = report["rows"]
    assert rows, "diffoscope produced no rows"
    for row in rows:
        expected = "content_sha256" if is_image_artifact(row["artifact"]) else "sha256"
        assert row["compared_field"] == expected, row["artifact"]
        # Byte digests stay recorded for every row so the deposited bytes remain
        # independently checkable with `sha256sum`.
        assert row["saved_sha256"], row["artifact"]
