"""Independently compare child artifacts with the parent's unchanged kernels."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from ..primitives import collect_primitives
from .custody_paths import confined_path


def _decode(value: Any) -> Any:
    if isinstance(value, dict):
        if set(value) == {"complex_real", "complex_imag"}:
            return complex(_decode(value["complex_real"]), _decode(value["complex_imag"]))
        return {key: _decode(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_decode(item) for item in value]
    if type(value) not in {float, int} or not np.isfinite(value):
        raise ValueError("child numerical results require finite numeric values")
    return value


def _matches(actual: Any, expected: Any, tolerance: float) -> bool:
    if isinstance(expected, dict):
        return (
            isinstance(actual, dict)
            and set(actual) == set(expected)
            and all(_matches(actual[key], value, tolerance) for key, value in expected.items())
        )
    left, right = np.asarray(actual), np.asarray(expected)
    return bool(left.shape == right.shape and np.allclose(left, right, rtol=0, atol=max(tolerance, 1e-12)))


def verify_analysis_results(child_root: Path, domain: str) -> dict[str, object]:
    """Require every primitive's actual output, independently recomputed in parent."""
    artifact = confined_path(child_root, "output/data/analysis_results.json", regular=True)
    if artifact.stat().st_size > 1048576:
        raise ValueError("child analysis must produce bounded regular analysis_results.json")
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != "autopoiesis/child-analysis/1":
        raise ValueError("child analysis artifact schema is invalid")
    if payload.get("domain") != domain or not isinstance(payload.get("results"), dict):
        raise ValueError("child analysis artifact does not bind the selected domain")
    primitives = collect_primitives().get(domain, ())
    if not primitives or set(payload["results"]) != {primitive.name for primitive in primitives}:
        raise ValueError("child analysis must report exactly every selected primitive")
    for primitive in primitives:
        actual = _decode(payload["results"][primitive.name])
        expected = primitive.fn(primitive.example_input)
        if not _matches(actual, expected, primitive.tolerance):
            raise ValueError(f"independent child computation mismatch: {primitive.name}")
    return {"status": "passed", "domain": domain, "primitive_count": len(primitives)}
