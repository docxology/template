"""Finite exact Mermaid profiles; current CLI12.2 retains SDK-owned fonts.

CLI12.2.0 declares patched KaTeX and Mermaid12 dependencies. The complete root
npm lock binds both standalone KaTeX/CSS and Mermaid's embedded browser renderer;
updating a standalone KaTeX package alone cannot patch an older Mermaid bundle.
Historical CLI11.16.0 and CLI12.0.0 profiles remain separate exact adapters.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from infrastructure.rendering import _mermaid_v11, _mermaid_v12, _mermaid_v122


@dataclass(frozen=True)
class NativeMermaidProfile:
    adapter: ModuleType
    suffix: str
    sdk_fonts: bool
    bind_inline_tooling: bool


_PROFILES = {
    "11.16.0": NativeMermaidProfile(_mermaid_v11, "v11", sdk_fonts=True, bind_inline_tooling=False),
    "12.0.0": NativeMermaidProfile(_mermaid_v12, "v12", sdk_fonts=False, bind_inline_tooling=False),
    "12.2.0": NativeMermaidProfile(_mermaid_v122, "v122", sdk_fonts=True, bind_inline_tooling=True),
}


def find_native_profile(version: object) -> NativeMermaidProfile | None:
    """Select a Source-owned row without applying the caller's refusal policy."""
    return _PROFILES.get(version) if isinstance(version, str) else None


def _profile(version: str) -> NativeMermaidProfile:
    profile = find_native_profile(version)
    if profile is None:
        raise ValueError("selected Mermaid version has no Source-owned finite native profile")
    return profile


def adapter_filename(version: str) -> str:
    return f"original-mermaid-{_profile(version).suffix}.mjs"


def adapter_sha256(version: str) -> str:
    return str(_profile(version).adapter.ADAPTER_SHA256)


def adapter_bytes(version: str) -> bytes:
    value: bytes = _profile(version).adapter.adapter_bytes()
    return value


def policy(version: str) -> str:
    return str(_profile(version).adapter.POLICY)


def rendering_profile(version: str) -> dict[str, str | int | bool]:
    value: dict[str, str | int | bool] = _profile(version).adapter.rendering_profile()
    return value


def validate_rendering_profile(version: str, value: object) -> None:
    _profile(version).adapter.validate_rendering_profile(value)


def request_bytes(
    version: str,
    package_root: Path,
    source: Path,
    output: Path,
    output_format: str,
    puppeteer_config: Path | None,
) -> bytes:
    value: bytes = _profile(version).adapter.request_bytes(
        package_root, source, output, output_format, puppeteer_config
    )
    return value
