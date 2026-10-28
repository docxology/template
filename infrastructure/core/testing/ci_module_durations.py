"""Measured CI test-module durations and the shard load weights derived from them.

The committed manifest records observed hosted job seconds per test module. Shard
balancing prefers those measurements and only estimates the remaining modules
from their byte size, so the manifest is a measurement source, never a selection
source: no module is added, removed or restricted by this file.

This module is the single reader of measured module durations; the contract
dispatch order and the functional shard balance both derive from it.
"""

from __future__ import annotations

import json
import math
from collections.abc import Iterable, Mapping
from pathlib import Path

from infrastructure.core.files.secure_write import read_bytes_confined

SCHEMA_VERSION = "template-ci-module-durations-v1"
MANIFEST_RELATIVE_PATH = Path("infrastructure/config/ci-module-durations.json")
MAX_MANIFEST_BYTES = 256 * 1024


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Refuse duplicate manifest keys instead of silently keeping the last one."""
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"module duration manifest repeats {key!r}")
        value[key] = item
    return value


def _relative_module(name: object) -> str:
    if not isinstance(name, str) or not name or "\\" in name:
        raise ValueError("module duration keys must be non-empty repository-relative POSIX paths")
    candidate = Path(name)
    if candidate.is_absolute() or ".." in candidate.parts or candidate.suffix != ".py" or candidate.as_posix() != name:
        raise ValueError(f"module duration key escapes the repository test roster: {name!r}")
    return name


def _seconds(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"module duration for {name} must be a number")
    measured = float(value)
    if not math.isfinite(measured) or measured <= 0:
        raise ValueError(f"module duration for {name} must be a finite positive number")
    return measured


def load_module_durations(root: Path, manifest: Path = MANIFEST_RELATIVE_PATH) -> dict[str, float]:
    """Read the committed per-module measurements, refusing malformed evidence."""
    payload = json.loads(
        read_bytes_confined(root, root / manifest, max_bytes=MAX_MANIFEST_BYTES).decode("utf-8"),
        object_pairs_hook=_unique_pairs,
    )
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"module duration manifest must declare schema {SCHEMA_VERSION}")
    provenance = payload.get("provenance")
    if not isinstance(provenance, str) or not provenance.strip():
        raise ValueError("module duration manifest must record a provenance note")
    if payload.get("unit") != "seconds":
        raise ValueError("module duration manifest unit must be seconds")
    modules = payload.get("modules")
    if not isinstance(modules, dict):
        raise ValueError("module duration manifest must declare a modules mapping")
    return {_relative_module(name): _seconds(name, value) for name, value in modules.items()}


def validate_module_durations(durations: Mapping[str, float], roster: Iterable[str]) -> None:
    """Require every measurement to belong to the current functional roster."""
    known = set(roster)
    unknown = sorted(set(durations) - known)
    if unknown:
        raise ValueError("module durations name modules outside the functional roster: " + ", ".join(unknown))


def module_weights(
    root: Path,
    modules: Iterable[str],
    durations: Mapping[str, float] | None = None,
) -> dict[str, float]:
    """Return comparable shard loads: measured seconds, bytes elsewhere.

    Measured modules keep their observed seconds. Unmeasured modules are scaled
    from their byte size by the median seconds-per-byte rate of the measured
    modules in the same selection, so both sources share one load scale. Without
    any measurement in the selection the previous byte-size balance is preserved
    exactly.
    """
    names = tuple(modules)
    measured = dict(load_module_durations(root) if durations is None else durations)
    sizes = {name: (root / name).stat().st_size for name in names}
    observed = {name: measured[name] for name in names if name in measured and sizes[name]}
    if not observed:
        return {name: float(sizes[name]) for name in names}
    rates = sorted(observed[name] / sizes[name] for name in observed)
    rate = rates[len(rates) // 2]
    return {name: observed.get(name, sizes[name] * rate) for name in names}


__all__ = [
    "MANIFEST_RELATIVE_PATH",
    "SCHEMA_VERSION",
    "load_module_durations",
    "module_weights",
    "validate_module_durations",
]
