"""Shared admission mechanics for exact Mermaid version profiles."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def validate_profile(value: object, expected: dict[str, str | int | bool]) -> None:
    """Require the exact profile, including the types of its values."""
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError("Mermaid rendering profile differs from the source-owned default theme")
    for key, original in expected.items():
        if type(value[key]) is not type(original) or value[key] != original:
            raise ValueError("Mermaid rendering profile changes theme, embedding or viewport semantics")


def read_adapter(path: Path, expected_sha256: str) -> bytes:
    """Read the bounded packaged asset at the version wrapper's path."""
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 64 * 1024:
        raise ValueError("packaged Mermaid adapter is absent or not a bounded regular asset")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError("packaged Mermaid adapter bytes differ from the declared source profile")
    return data


def select_package(mmdc: str, version: str) -> Path:
    """Admit the exact package behind the selected Mermaid entrypoint."""
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
        or raw.get("version") != version
        or raw.get("bin") != {"mmdc": "./src/cli.js"}
    ):
        raise ValueError("selected Mermaid version has no admitted rectangular viewport API profile")
    return root
