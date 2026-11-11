"""Literal requests for the packaged, exact Source-pinned Mermaid CLI 12.2 rectangular viewport API."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from infrastructure.rendering._mermaid_profile_io import read_adapter, select_package, validate_profile
from infrastructure.rendering._mermaid_source_font_default import PROFILE_NAME, default_font_profile_bytes

SCHEMA = "template-mermaid-v122-source-pinned-default-theme-viewport-licensed-font-request-v1"
POLICY = "template-mermaid-v122-source-pinned-official-render-default-theme-liberation-sans-before-layout-1400x900-v1"
ADAPTER_SHA256 = "213bcbf9c36eff37c05843c2c2ea6ec625747ded52a2c783b2bb7f0c2a8413dd"


def rendering_profile() -> dict[str, str | int | bool]:
    """Admit Source122's actual theme/platform-font/rectangular profile.

    Upstream font embedding is disabled explicitly. The existing SDK font
    constructor and used-face embedding remain independently authenticated.
    """
    return {
        "theme": "default",
        "source_default_font": "template-source-mermaid-licensed-default-font-v1",
        "source_used_face_embedding": True,
        "font_embed": False,
        "background_color": "white",
        "viewport_width": 1400,
        "viewport_height": 900,
        "device_scale_factor": 1,
    }


def validate_rendering_profile(value: object) -> None:
    """Reject altered values and Python's bool/int equality ambiguity."""
    validate_profile(value, rendering_profile())


def adapter_bytes() -> bytes:
    """Consume the packaged SDK asset; missing or changed bytes refuse execution."""
    path = Path(__file__).with_name("_mermaid_v122_adapter.mjs")
    return read_adapter(path, ADAPTER_SHA256)


def selected_package(mmdc: str) -> Path:
    """Resolve the actual mmdc entrypoint, without environment package overrides."""
    return select_package(mmdc, "12.2.0")


def request_bytes(
    package_root: Path,
    source: Path,
    output: Path,
    output_format: str,
    puppeteer_config: Path | None,
) -> bytes:
    """Freeze literal file identities; all render dimensions remain SDK constants."""
    if output_format not in {"svg", "png"}:
        raise ValueError("Mermaid adapter only admits the original SVG/PNG source formats")
    paths = (package_root, source, output, *((puppeteer_config,) if puppeteer_config is not None else ()))
    if any(not path.is_absolute() or ".." in path.parts or len(str(path)) > 4096 for path in paths):
        raise ValueError("Mermaid adapter requires explicit bounded absolute source/runtime/output paths")
    if source.suffix != ".mmd" or output.suffix != "." + output_format:
        raise ValueError("Mermaid adapter requires original diagram data and its declared output format")
    raw = {
        "schema_version": SCHEMA,
        "font_profile": str(source.parent / PROFILE_NAME),
        "font_profile_sha256": hashlib.sha256(default_font_profile_bytes()).hexdigest(),
        "render_profile": rendering_profile(),
        "package_root": str(package_root),
        "input": str(source),
        "output": str(output),
        "output_format": output_format,
        "puppeteer_config": str(puppeteer_config) if puppeteer_config is not None else None,
    }
    return (json.dumps(raw, sort_keys=True, allow_nan=False) + "\n").encode()


def standalone_request_bytes(
    package_root: Path,
    source: Path,
    output: Path,
    puppeteer_config: Path | None,
    *,
    width: int,
    height: int,
    background: str,
) -> bytes:
    """Preserve the public standalone viewport without borrowing native proof."""
    if type(width) is not int or type(height) is not int or not 0 < width <= 2**53 - 1 or not 0 < height <= 2**53 - 1:
        raise ValueError("standalone Mermaid viewport requires positive literal integers")
    if not isinstance(background, str) or not background or len(background) > 4096:
        raise ValueError("standalone Mermaid background requires a bounded literal string")
    value = json.loads(request_bytes(package_root, source, output, "png", puppeteer_config))
    value["schema_version"] = "template-mermaid-v122-standalone-viewport-licensed-font-request-v1"
    value["render_profile"].update(viewport_width=width, viewport_height=height, background_color=background)
    return (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode()
