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

import hashlib
import json
import os
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering import _mermaid_v122
from infrastructure.rendering._mermaid_source_font_default import (
    PROFILE_NAME,
    SCRIPT_NAME,
    default_font_profile_bytes,
    default_font_script_bytes,
)
from infrastructure.rendering.chrome import resolve_chrome_executable
from infrastructure.rendering.native_render_custody import native_render_custody
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
            "mmdc (mermaid-cli) not found on PATH. From the repository root, run "
            '`npm ci` and `export PATH="$PWD/node_modules/.bin:$PATH"` to render Mermaid diagrams to PNG.'
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    api122 = False
    package_root: Path | None = None
    try:
        entry = Path(mmdc).resolve(strict=True)
        manifest = entry.parent.parent / "package.json"
        if entry.name == "cli.js" and entry.parent.name == "src" and manifest.is_file():
            if manifest.is_symlink() or manifest.stat().st_size > 1024 * 1024:
                raise ValueError("selected Mermaid package declaration is aliased or unbounded")
            value = json.loads(manifest.read_bytes())
            api122 = (
                isinstance(value, dict)
                and value.get("name") == "@mermaid-js/mermaid-cli"
                and value.get("version") == "12.2.0"
            )
            if api122:
                package_root = _mermaid_v122.selected_package(mmdc)
    except (OSError, ValueError) as exc:
        raise RenderingError(f"Mermaid package admission failed: {exc}") from exc
    mmd_sidecar = output_path.with_suffix(".mmd")
    if (
        not api122
        and output_path.is_file()
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

    inputs: tuple[Path, ...] = (mmd_sidecar, *((puppeteer_config,) if puppeteer_config is not None else ()))
    cache = output_path.with_suffix(".mermaid-cache.json")
    cache_binding: dict[str, object] | None = None
    custody = None
    before: dict[str, str] = {}
    if api122:
        if package_root is None:
            raise RenderingError("Mermaid12.2 package admission is absent")
        node = shutil.which("node")
        if node is None:
            raise RenderingError("Mermaid12.2 requires its selected Node24 executable")
        if os.environ.get("NODE_OPTIONS") or os.environ.get("NODE_PATH"):
            raise RenderingError("Mermaid profile cannot admit environment-supplied JavaScript/module overrides")
        helper = output_path.parent / SCRIPT_NAME
        fonts = output_path.parent / PROFILE_NAME
        adapter = output_path.with_suffix(".mermaid-v122.mjs")
        request = output_path.with_suffix(".mermaid-v122-request.json")
        helper.write_bytes(default_font_script_bytes())
        fonts.write_bytes(default_font_profile_bytes())
        adapter.write_bytes(_mermaid_v122.adapter_bytes())
        if width == 1400 and height == 900 and background == "white":
            request.write_bytes(
                _mermaid_v122.request_bytes(
                    package_root,
                    mmd_sidecar.absolute(),
                    output_path.absolute(),
                    "png",
                    puppeteer_config.absolute() if puppeteer_config is not None else None,
                )
            )
        else:
            request.write_bytes(
                _mermaid_v122.standalone_request_bytes(
                    package_root,
                    mmd_sidecar.absolute(),
                    output_path.absolute(),
                    puppeteer_config.absolute() if puppeteer_config is not None else None,
                    width=width,
                    height=height,
                    background=background,
                )
            )
        inputs = (*inputs, helper, fonts, adapter, request)
        before = {str(path.absolute()): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}
        runtime_files: tuple[Path, ...] = (package_root / "package.json", package_root / "src/index.js")
        source_lock = package_root.parents[2] / "package-lock.json"
        if source_lock.is_file() and not source_lock.is_symlink():
            runtime_files = (*runtime_files, source_lock)
        cache_binding = {
            "schema_version": "template-mermaid122-standalone-cache-v1",
            "inputs": before,
            "runtime_inputs": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in runtime_files},
            "node": str(Path(node).resolve(strict=True)),
            "policy": _mermaid_v122.POLICY,
        }
        custody = native_render_custody(
            "native-origin Mermaid production lacks its independently admitted Source owner"
        )
        cache_identity_complete = (
            source_lock.is_file() and not source_lock.is_symlink() and source_lock.stat().st_size <= 4 * 1024 * 1024
        )
        if cache_identity_complete:
            try:
                selected_node = Path(node).resolve(strict=True)
                with selected_node.open("rb") as stream:
                    node_sha256 = hashlib.file_digest(stream, "sha256").hexdigest()
                cache_binding["tooling"] = {
                    "source_lock_sha256": hashlib.sha256(source_lock.read_bytes()).hexdigest(),
                    "node_path": str(selected_node),
                    "node_sha256": node_sha256,
                }
            except OSError:
                cache_identity_complete = False
        if (
            custody is None
            and cache_identity_complete
            and output_path.is_file()
            and output_path.stat().st_size > 0
            and cache.is_file()
        ):
            try:
                stored = json.loads(cache.read_bytes())
            except (OSError, ValueError):
                stored = None
            if stored == {**cache_binding, "png_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest()}:
                return output_path
        cmd = [str(Path(node).resolve(strict=True)), str(adapter.absolute()), str(request.absolute())]

    env = os.environ.copy()
    env["PATH"] = os.pathsep.join(part for part in (env.get("PATH", ""), os.defpath) if part)

    try:
        if not api122:
            custody = native_render_custody(
                "native-origin Mermaid production lacks its independently admitted Source owner"
            )
        # The launcher is called from this frame: native custody verifies
        # this exact function as its caller.
        completed = (
            None
            if custody is None
            else custody.mermaid_launcher()(
                cmd,
                mmd_sidecar,
                output_path,
                role="standalone",
                raw_source=source,
                input_paths=inputs,
                environment=env,
                timeout=timeout,
            )
        )
        if completed is None:
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

    if before and any(hashlib.sha256(path.read_bytes()).hexdigest() != before[str(path.absolute())] for path in inputs):
        raise RenderingError("Mermaid source adapter/request/font bytes changed during rendering")
    if cache_binding is not None:
        cache.write_text(
            json.dumps(
                {**cache_binding, "png_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest()}, sort_keys=True
            )
            + "\n"
        )
    return output_path


__all__ = ["render_mermaid_png"]
