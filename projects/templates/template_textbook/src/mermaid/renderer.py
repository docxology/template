"""Render Mermaid sources to PNG, with a graceful ``.mmd`` fallback."""

from __future__ import annotations

import os
import signal
import shutil
import subprocess  # nosec B404
from dataclasses import dataclass
from pathlib import Path

from textbook_io import write_text_atomic
from textbook_logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class RenderResult:
    """Outcome of a single diagram render."""

    name: str
    path: Path
    rendered_png: bool  # True if mmdc produced a PNG; False if .mmd fallback


def _resolve_mmdc() -> str | None:
    """Resolve ``mmdc`` from PATH or a repository-local Node install."""
    candidate = shutil.which("mmdc")
    if candidate:
        return candidate
    for parent in Path(__file__).resolve().parents:
        local_candidate = parent / "node_modules" / ".bin" / "mmdc"
        if local_candidate.exists():
            return str(local_candidate)
    return None


def mmdc_available() -> bool:
    """Return True when the Mermaid CLI is on PATH or locally installed."""
    return _resolve_mmdc() is not None


class MermaidRenderer:
    """Render Mermaid source strings into an output directory."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render(self, name: str, source: str) -> RenderResult:
        """Render one diagram. Falls back to writing ``<name>.mmd`` if no mmdc."""
        mmd_path = self.output_dir / f"{name}.mmd"
        write_text_atomic(mmd_path, source)

        mmdc_bin = _resolve_mmdc()
        if mmdc_bin is None:
            logger.info("mmdc not found; wrote source fallback %s", mmd_path)
            return RenderResult(name=name, path=mmd_path, rendered_png=False)

        png_path = self.output_dir / f"{name}.png"
        try:  # pragma: no cover - exercised only where mmdc is installed
            _run_mmdc([mmdc_bin, "-i", str(mmd_path), "-o", str(png_path)], timeout=120)
        except (subprocess.SubprocessError, OSError) as exc:  # pragma: no cover
            logger.warning("mmdc failed for %s (%s); using .mmd fallback", name, exc)
            return RenderResult(name=name, path=mmd_path, rendered_png=False)
        return RenderResult(name=name, path=png_path, rendered_png=True)


def _run_mmdc(args: list[str], *, timeout: int) -> None:
    """Run Mermaid CLI and reap browser descendants if it times out."""
    process = subprocess.Popen(  # nosec B603
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        else:  # pragma: no cover - Windows-only fallback
            process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            if os.name == "posix":
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:  # pragma: no cover - Windows-only fallback
                process.kill()
        process.communicate()
        raise

    if process.returncode:
        raise subprocess.CalledProcessError(process.returncode, args, output=stdout, stderr=stderr)


__all__ = ["MermaidRenderer", "RenderResult", "mmdc_available"]
