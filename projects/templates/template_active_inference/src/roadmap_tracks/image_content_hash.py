"""Compression-invariant content hashing for rendered image artifacts.

Why this exists
---------------
Artifact provenance hashes files with ``sha256`` over their raw bytes. That is
correct for the 75 JSON and 1 CSV artifacts, which are deterministic text. It is
wrong for rendered figures: PNG bytes depend on the zlib build that compressed
them, and Pillow ships a platform-specific wheel bundling its own zlib, so the
same figure encodes differently on macOS and Linux while the picture is
identical.

Measured 2026-07-27 against the previous commit's committed figures: 22 of 25
PNGs differed in bytes and **0 differed in pixels**. The byte hash was therefore
reporting drift that had no bearing on the artifact's content, and the only way
to make it pass was to re-pin the snapshot to whichever machine ran last.

What is hashed
--------------
Everything about the image except how it was compressed:

* colour mode and pixel dimensions,
* the decoded pixel data of every frame (animations included),
* every textual metadata chunk, sorted.

So a changed pixel, a resized canvas, a recoloured series, or an injected
metadata chunk all change the hash; re-compressing the identical picture does
not. This is deliberately *less* sensitive than a byte hash in exactly one
respect, and that respect carries no scientific meaning.

Byte hashes are still recorded alongside these — see ``sha256`` next to
``content_sha256`` in ``artifact_provenance.json`` and
``figure_hash_manifest.json``. The byte hash stays independently checkable with
``sha256sum`` by a third party who does not run this code; the content hash is
what the diffoscope gate compares. Neither replaces the other.
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path

#: Suffixes routed through content hashing rather than byte hashing.
IMAGE_SUFFIXES: frozenset[str] = frozenset({".png", ".gif"})


def is_image_artifact(relative_path: str) -> bool:
    """True when *relative_path* names a raster artifact this module can hash."""
    return Path(relative_path).suffix.lower() in IMAGE_SUFFIXES


@lru_cache(maxsize=256)
def _image_content_sha256_cached(resolved_path_str: str, _mtime_ns: int, _size: int) -> str:
    path = Path(resolved_path_str)
    if not path.is_file():
        return ""
    try:
        from PIL import Image, ImageSequence
    except ImportError:
        return ""

    digest = hashlib.sha256()
    try:
        with Image.open(path) as image:
            digest.update(f"size:{image.size[0]}x{image.size[1]}".encode())
            frames = 0
            for frame in ImageSequence.Iterator(image):
                digest.update(frame.convert("RGBA").tobytes())
                frames += 1
            digest.update(f"frames:{frames}".encode())
            text_chunks = dict(getattr(image, "text", {}) or {})
            for key in sorted(text_chunks):
                digest.update(f"meta:{key}={text_chunks[key]}".encode())
    except OSError:
        return ""
    return digest.hexdigest()


def image_content_sha256(path: Path) -> str:
    """Return a compression-invariant content digest for an image file.

    Returns an empty string when the file is missing or cannot be decoded, which
    callers treat the same way they treat a missing byte hash — absent evidence,
    never a silent pass.
    """
    if not path.is_file():
        return ""
    try:
        stat = path.stat()
        return _image_content_sha256_cached(str(path.resolve()), stat.st_mtime_ns, stat.st_size)
    except (OSError, ValueError):
        return ""


__all__ = ["IMAGE_SUFFIXES", "image_content_sha256", "is_image_artifact"]
