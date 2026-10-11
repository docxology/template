"""Finite explicit Source11 and separately nominated historical12 API profiles."""

from __future__ import annotations

from pathlib import Path
from types import ModuleType

from infrastructure.rendering import _mermaid_v11, _mermaid_v12


def _profile(version: str) -> ModuleType:
    if version == "11.16.0":
        return _mermaid_v11
    if version == "12.0.0":
        return _mermaid_v12
    raise ValueError("selected Mermaid version has no Source-owned finite native profile")


def adapter_filename(version: str) -> str:
    _profile(version)
    return "original-mermaid-v11.mjs" if version == "11.16.0" else "original-mermaid-v12.mjs"


def adapter_sha256(version: str) -> str:
    return str(_profile(version).ADAPTER_SHA256)


def adapter_bytes(version: str) -> bytes:
    value: bytes = _profile(version).adapter_bytes()
    return value


def policy(version: str) -> str:
    return str(_profile(version).POLICY)


def rendering_profile(version: str) -> dict[str, str | int | bool]:
    value: dict[str, str | int | bool] = _profile(version).rendering_profile()
    return value


def validate_rendering_profile(version: str, value: object) -> None:
    _profile(version).validate_rendering_profile(value)


def request_bytes(
    version: str,
    package_root: Path,
    source: Path,
    output: Path,
    output_format: str,
    puppeteer_config: Path | None,
) -> bytes:
    value: bytes = _profile(version).request_bytes(package_root, source, output, output_format, puppeteer_config)
    return value
