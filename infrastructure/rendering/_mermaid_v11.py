"""Literal requests for the packaged, exact Source-pinned Mermaid 11 rectangular viewport API."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from infrastructure.rendering._mermaid_source_font_default import PROFILE_NAME, default_font_profile_bytes

SCHEMA = "template-mermaid-v11-source-pinned-default-theme-viewport-licensed-font-request-v2"
POLICY = "template-mermaid-v11-source-pinned-official-render-default-theme-liberation-sans-before-layout-1400x900-v2"
ADAPTER_SHA256 = "41f8ef156292b253344ba56afe46d27b34641ff7e1bdc666d2092770387e968f"


def rendering_profile() -> dict[str, str | int | bool]:
    """Admit Source11's actual theme/platform-font/rectangular profile.

    No embedding API exists in this version; actual platform fonts and complete
    source pixels remain independently authenticated by native admission.
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
    expected = rendering_profile()
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError("Mermaid rendering profile differs from the source-owned legacy default theme")
    for key, original in expected.items():
        if type(value[key]) is not type(original) or value[key] != original:
            raise ValueError("Mermaid rendering profile changes theme, embedding or viewport semantics")


def adapter_bytes() -> bytes:
    """Consume the packaged SDK asset; missing or changed bytes refuse execution."""
    path = Path(__file__).with_name("_mermaid_v11_adapter.mjs")
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 64 * 1024:
        raise ValueError("packaged Mermaid adapter is absent or not a bounded regular asset")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != ADAPTER_SHA256:
        raise ValueError("packaged Mermaid adapter bytes differ from the declared source profile")
    return data


def selected_package(mmdc: str) -> Path:
    """Resolve the actual mmdc entrypoint, without environment package overrides."""
    selected = Path(mmdc).resolve(strict=True)
    root = selected.parent.parent
    manifest = root / "package.json"
    if selected.name != "cli.js" or selected.parent.name != "src":
        raise ValueError("selected Mermaid entrypoint requires a separately admitted runtime profile")
    if manifest.is_symlink() or not manifest.is_file() or manifest.stat().st_size > 1024 * 1024:
        raise ValueError("selected Mermaid package manifest is absent or unbounded")
    raw = json.loads(manifest.read_bytes())
    if (
        not isinstance(raw, dict)
        or raw.get("name") != "@mermaid-js/mermaid-cli"
        or raw.get("version") != "11.16.0"
        or raw.get("bin") != {"mmdc": "./src/cli.js"}
    ):
        raise ValueError("selected Mermaid version has no admitted rectangular viewport API profile")
    return root


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
