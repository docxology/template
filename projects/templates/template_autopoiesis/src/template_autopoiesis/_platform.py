"""Resolve the generator's declared exact platform dependency before admission."""

from __future__ import annotations

import re
import tomllib
from importlib.metadata import distribution
from pathlib import Path


def required_platform_version() -> str:
    """Read the actual source contract or installed generator requirement."""
    package_root = Path(__file__).absolute().parent
    if package_root.parent.name == "src":
        try:
            metadata = tomllib.loads((package_root.parent.parent / "pyproject.toml").read_text(encoding="utf-8"))
            required = metadata["tool"]["template"]["platform_version"]
        except (OSError, tomllib.TOMLDecodeError, KeyError, TypeError) as exc:
            raise ValueError("generator checkout requires its declared platform metadata") from exc
        if not isinstance(required, str) or not required.strip():
            raise ValueError("generator platform_version must be a non-empty string")
        return required
    requirements = distribution("template_autopoiesis").requires or []
    exact = [
        match.group(1)
        for requirement in requirements
        if (match := re.fullmatch(r"research[-_]project[-_]template\s*==\s*([A-Za-z0-9.!+_-]+)", requirement))
    ]
    if len(exact) != 1:
        raise ValueError("installed generator must declare one exact platform dependency")
    return exact[0]
