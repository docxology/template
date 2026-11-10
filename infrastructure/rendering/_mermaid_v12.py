"""Literal requests for the packaged, exact Mermaid 12 rectangular viewport API."""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.rendering._mermaid_profile_io import read_adapter, select_package, validate_profile

SCHEMA = "template-mermaid-v12-legacy11-default-theme-viewport-request-v2"
POLICY = "template-mermaid-v12-official-run-legacy11-default-theme-1400x900-v2"
ADAPTER_SHA256 = "2e819f40d052ab6c4789dabfcb9df5214ba8fba5063145b0832d1ceaf5ab0b79"


def rendering_profile() -> dict[str, str | int | bool]:
    """Preserve the pinned CLI11 default theme through CLI12's public API.

    Embedding remains enabled; an actual embedded resource still needs the
    independent SVG/font admission and cannot be approved by this profile.
    """
    return {
        "theme": "default",
        "font_embed": True,
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
    path = Path(__file__).with_name("_mermaid_v12_adapter.mjs")
    return read_adapter(path, ADAPTER_SHA256)


def selected_package(mmdc: str) -> Path:
    """Resolve the actual mmdc entrypoint, without environment package overrides."""
    return select_package(mmdc, "12.0.0")


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
        "render_profile": rendering_profile(),
        "package_root": str(package_root),
        "input": str(source),
        "output": str(output),
        "output_format": output_format,
        "puppeteer_config": str(puppeteer_config) if puppeteer_config is not None else None,
    }
    return (json.dumps(raw, sort_keys=True, allow_nan=False) + "\n").encode()
