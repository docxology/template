"""Render a standalone Mermaid diagram source string to a PNG file.

This is a generic, project-agnostic sibling of the inline-fence Mermaid
support in :mod:`infrastructure.rendering._pdf_mermaid` (which rewrites
Mermaid fences found inside a combined manuscript). Use this module instead
when a caller already has one Mermaid diagram source string and wants a PNG
at a specific path — e.g. a slide deck embedding an architecture diagram as
a :class:`infrastructure.rendering.slide_deck.Slide` figure.

Requires ``mmdc`` (mermaid-cli) on ``PATH``; raises
:class:`~infrastructure.core.exceptions.RenderingError` with a clear message
if it is absent, rather than a bare ``FileNotFoundError``.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering.chrome import resolve_chrome_executable
from infrastructure.rendering.security import run_isolated_subprocess

logger = get_logger(__name__)


def render_mermaid_png(
    source: str,
    output_path: Path,
    *,
    width: int = 1400,
    height: int = 900,
    background: str = "white",
    timeout: int = 90,
    executable_resolver: Callable[[str], str | None] = shutil.which,
) -> Path:
    """Render ``source`` (a Mermaid diagram definition) to a PNG at ``output_path``.

    Deterministic: re-rendering identical ``source`` to the same
    ``output_path`` is a no-op if the target already exists with matching
    content recorded alongside it (mirrors the caching behavior of the
    inline-fence renderer).
    """
    mmdc = executable_resolver("mmdc")
    if mmdc is None:
        raise RenderingError(
            "mmdc (mermaid-cli) not found on PATH. Install it (e.g. `npm install -g @mermaid-js/mermaid-cli`) "
            "to render Mermaid diagrams to PNG."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    mmd_sidecar = output_path.with_suffix(".mmd")
    if (
        output_path.is_file()
        and output_path.stat().st_size > 0
        and mmd_sidecar.is_file()
        and mmd_sidecar.read_text(encoding="utf-8").rstrip("\n") == source.rstrip("\n")
    ):
        return output_path

    mmd_sidecar.write_text(source + "\n", encoding="utf-8")

    cmd = [
        mmdc,
        "--input",
        str(mmd_sidecar),
        "--output",
        str(output_path),
        "--width",
        str(width),
        "--height",
        str(height),
        "--backgroundColor",
        background,
        "--quiet",
    ]

    chrome_executable = resolve_chrome_executable(include_macos_app=True)
    puppeteer_config: Path | None = None
    if chrome_executable is not None:
        puppeteer_config = output_path.parent / f"{output_path.stem}.puppeteer.json"
        puppeteer_config.write_text(
            json.dumps({"executablePath": str(chrome_executable)}) + "\n",
            encoding="utf-8",
        )
        cmd.extend(["--puppeteerConfigFile", str(puppeteer_config)])

    env = os.environ.copy()
    env["PATH"] = os.pathsep.join(part for part in (env.get("PATH", ""), os.defpath) if part)

    try:
        completed = run_isolated_subprocess(cmd, env=env, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise RenderingError(f"mmdc timed out while rendering {output_path.name}") from exc
    except OSError as exc:
        raise RenderingError(f"Could not execute mmdc while rendering {output_path.name}: {exc}") from exc

    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip()
        raise RenderingError(f"mmdc failed for {output_path.name}: {stderr[:800]}")
    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise RenderingError(f"mmdc reported success for {output_path.name} but did not produce a PNG")

    return output_path


__all__ = ["render_mermaid_png"]
