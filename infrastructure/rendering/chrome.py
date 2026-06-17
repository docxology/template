"""Shared Chrome/Chromium executable resolution for mmdc (mermaid-cli) / Puppeteer.

`mmdc` launches Puppeteer, which needs a Chromium-compatible browser. Three
call sites historically resolved that browser independently and inconsistently
(combined-PDF mermaid rendering, the docs mermaid linter, and the architecture
diagram generator). This module is the single source of truth they all delegate
to, so the resolution order — and the env vars CI exports — stay consistent.

Resolution order (``resolve_chrome_executable``):

1. ``PUPPETEER_EXECUTABLE_PATH`` env var (Puppeteer's own convention).
2. ``CHROME_EXECUTABLE_PATH`` env var (the var ``.github/workflows/ci.yml``
   exports after ``puppeteer browsers install chrome-headless-shell``).
3. Newest browser under the Puppeteer cache (``PUPPETEER_CACHE_DIR`` or
   ``~/.cache/puppeteer``), version-sorted.
4. A system browser on ``PATH`` (``shutil.which``).
5. A browser in the home directory.
6. *(opt-in)* the macOS system Chrome app bundle, when ``include_macos_app`` is
   set — used by the local-dev doc renderers, but NOT by the PDF path, whose
   test suite asserts ``None`` when no on-``PATH``/cache browser resolves.
7. ``None`` — let Puppeteer fall back to its own bundled Chromium.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Final

_CACHE_CHROME_FILENAMES: Final[tuple[str, ...]] = (
    "chrome",
    "chrome-headless-shell",
    "Google Chrome for Testing",
)
_SYSTEM_CHROME_NAMES: Final[tuple[str, ...]] = (
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
)
_MACOS_APP_CHROME: Final[Path] = Path(
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
)

__all__ = ["resolve_chrome_executable"]


def _is_executable_file(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)


def _cache_version_key(dirname: str) -> tuple[int, tuple[int, ...], str]:
    _, _, version = dirname.partition("-")
    if version:
        parts = version.split(".")
        if all(part.isdigit() for part in parts):
            return (1, tuple(int(part) for part in parts), version)
    return (0, tuple(), dirname)


def _iter_cache_chrome_candidates(
    cache_root: Path,
) -> list[tuple[tuple[int, tuple[int, ...], str], Path]]:
    candidates: list[tuple[tuple[int, tuple[int, ...], str], Path]] = []
    for subtree in ("chrome", "chrome-headless-shell"):
        subtree_root = cache_root / subtree
        if not subtree_root.is_dir():
            continue
        for version_dir in subtree_root.iterdir():
            if not version_dir.is_dir():
                continue
            for candidate in sorted(version_dir.rglob("*")):
                if candidate.name in _CACHE_CHROME_FILENAMES and _is_executable_file(candidate):
                    candidates.append((_cache_version_key(version_dir.name), candidate))
                    break
    return candidates


def resolve_chrome_executable(*, include_macos_app: bool = False) -> Path | None:
    """Resolve the browser executable mmdc's Puppeteer should launch.

    Args:
        include_macos_app: when True, fall back to the macOS system Chrome app
            bundle if nothing else resolves. The PDF mermaid path leaves this
            False (its tests assert ``None`` past the on-PATH/cache search); the
            doc renderers set it True so local macOS dev works without a
            separate Chromium download.

    Returns:
        An executable browser :class:`~pathlib.Path`, or ``None`` to let
        Puppeteer use its bundled Chromium.
    """
    for env_var in ("PUPPETEER_EXECUTABLE_PATH", "CHROME_EXECUTABLE_PATH"):
        env_path = os.environ.get(env_var)
        if env_path:
            candidate = Path(env_path)
            if _is_executable_file(candidate):
                return candidate

    cache_dir = Path(os.environ.get("PUPPETEER_CACHE_DIR", Path.home() / ".cache" / "puppeteer"))
    cache_candidates = _iter_cache_chrome_candidates(cache_dir)
    if cache_candidates:
        return max(cache_candidates, key=lambda item: item[0])[1]

    for executable_name in _SYSTEM_CHROME_NAMES:
        resolved = shutil.which(executable_name)
        if resolved is None:
            continue
        candidate = Path(resolved)
        if _is_executable_file(candidate):
            return candidate

    for executable_name in _SYSTEM_CHROME_NAMES:
        candidate = Path.home() / executable_name
        if _is_executable_file(candidate):
            return candidate

    if include_macos_app and _MACOS_APP_CHROME.exists():
        return _MACOS_APP_CHROME

    return None
