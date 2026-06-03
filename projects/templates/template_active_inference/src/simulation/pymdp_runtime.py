"""Scoped pymdp/JAX runtime diagnostics for agent construction."""

from __future__ import annotations

import importlib.metadata
import json
import warnings
from pathlib import Path
from typing import Any, Callable

import numpy as np

from simulation.pymdp_config import PymdpConfig, config_hash

KNOWN_JAX_STATIC_WARNING = "A JAX array is being set as static"
RUNTIME_DIAGNOSTICS_SCHEMA = "template_active_inference.pymdp_runtime_diagnostics.v1"


def _package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def _backend_flags() -> dict[str, Any]:
    try:
        import jax

        return {
            "jax_default_backend": jax.default_backend(),
            "jax_enable_x64": bool(jax.config.jax_enable_x64),
            "jax_platforms": ",".join(str(device.platform) for device in jax.devices()),
        }
    except (AttributeError, ImportError, RuntimeError, ValueError) as exc:
        return {"jax_backend_error": type(exc).__name__}


def _numpy_factors(factors: list[Any]) -> list[np.ndarray]:
    return [np.asarray(factor, dtype=np.float64) for factor in factors]


def _warning_record(warning: warnings.WarningMessage) -> dict[str, str | bool]:
    message = str(warning.message)
    return {
        "category": warning.category.__name__,
        "message": message,
        "known": warning.category is UserWarning and KNOWN_JAX_STATIC_WARNING in message,
    }


def construct_agent_with_diagnostics(
    project_root: Path,
    *,
    config: PymdpConfig,
    model: dict[str, list[Any]],
    policy_len: int,
    context: str,
    agent_factory: Callable[..., Any] | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Construct ``pymdp.Agent`` while capturing the one audited JAX warning."""
    del project_root
    if agent_factory is None:
        from pymdp.agent import Agent

        agent_factory = Agent

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        agent = agent_factory(
            A=_numpy_factors(model["A"]),
            B=_numpy_factors(model["B"]),
            C=_numpy_factors(model["C"]),
            D=_numpy_factors(model["D"]),
            policy_len=policy_len,
            inference_algo=config.agent.inference_algo,
            action_selection=config.agent.action_selection,
        )

    records = [_warning_record(warning) for warning in captured]
    known = [record for record in records if record["known"]]
    unexpected = [record for record in records if not record["known"]]
    diagnostic = {
        "context": context,
        "config_hash": config_hash(config),
        "versions": {
            "inferactively_pymdp": _package_version("inferactively-pymdp"),
            "jax": _package_version("jax"),
            "jaxlib": _package_version("jaxlib"),
        },
        "backend_flags": _backend_flags(),
        "known_warning_count": len(known),
        "unexpected_warning_count": len(unexpected),
        "known_warnings": known,
        "unexpected_warnings": unexpected,
    }
    return agent, diagnostic


def build_runtime_diagnostics(records: list[dict[str, Any]]) -> dict[str, Any]:
    known_count = sum(int(record.get("known_warning_count", 0) or 0) for record in records)
    unexpected_count = sum(int(record.get("unexpected_warning_count", 0) or 0) for record in records)
    versions = records[-1].get("versions", {}) if records else {}
    backend_flags = records[-1].get("backend_flags", {}) if records else {}
    return {
        "schema": RUNTIME_DIAGNOSTICS_SCHEMA,
        "records": records,
        "construction_count": len(records),
        "config_hashes": sorted({str(record.get("config_hash")) for record in records if record.get("config_hash")}),
        "versions": versions,
        "backend_flags": backend_flags,
        "known_warning_count": known_count,
        "unexpected_warning_count": unexpected_count,
        "ok": bool(records) and unexpected_count == 0,
    }


def write_runtime_diagnostics(project_root: Path, records: list[dict[str, Any]]) -> Path:
    root = project_root.resolve()
    path = root / "output" / "reports" / "pymdp_runtime_diagnostics.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(build_runtime_diagnostics(records), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def validate_runtime_diagnostics(project_root: Path) -> list[str]:
    root = project_root.resolve()
    path = root / "output" / "reports" / "pymdp_runtime_diagnostics.json"
    if not path.is_file():
        return ["missing output/reports/pymdp_runtime_diagnostics.json"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    issues: list[str] = []
    if payload.get("schema") != RUNTIME_DIAGNOSTICS_SCHEMA:
        issues.append("pymdp_runtime_diagnostics.json schema mismatch")
    if int(payload.get("construction_count", 0) or 0) < 1:
        issues.append("pymdp_runtime_diagnostics.json records no agent constructions")
    if int(payload.get("unexpected_warning_count", 0) or 0) != 0:
        issues.append("pymdp_runtime_diagnostics.json captured unexpected warning")
    if not payload.get("config_hashes"):
        issues.append("pymdp_runtime_diagnostics.json lacks config hashes")
    if not payload.get("versions"):
        issues.append("pymdp_runtime_diagnostics.json lacks package versions")
    if not payload.get("backend_flags"):
        issues.append("pymdp_runtime_diagnostics.json lacks backend flags")
    if payload.get("ok") is not True:
        issues.append("pymdp_runtime_diagnostics.json does not record ok=true")
    return issues
