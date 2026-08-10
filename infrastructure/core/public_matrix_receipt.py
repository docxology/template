"""Deterministic public-matrix receipt for per-project release lanes.

The receipt records, for one bounded public-matrix run:

- roster revision (git HEAD commit)
- command / profile used
- per-project declared coverage floor
- per-project exit status
- per-project timeout status
- per-project measured coverage percent
- per-project output-isolation result (whether output/ tree was dirty after run)

A paired validator checks negative controls: missing project results, timeouts,
nonzero exits, coverage-floor failures, and test-generated output drift all
cause deterministic rejection.

Usage (produced by the runner):
    receipt = build_public_matrix_receipt(
        roster_revision=roster_revision,
        profile="quick",
        lanes=lane_results,
        combined_coverage_percent=75.0,
        combined_floor=75,
    )
    receipt.write(path)
    read_back = PublicMatrixReceipt.read(path)
    errors = read_back.validate(roster_names)
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Mapping, Sequence


@dataclass(frozen=True)
class PublicMatrixLaneResult:
    """Result for one project lane in a public-matrix run."""

    project_name: str
    declared_floor: int | None
    exit_code: int
    timed_out: bool
    coverage_percent: float | None
    output_isolation_ok: bool
    duration_seconds: float = 0.0
    resource_profile: str = "default"
    skip_reason: str = ""
    cache_key: str = ""
    collection_count: int | None = None
    output_isolation_digest: str = ""
    resource_limits: dict[str, str | int | float] = field(default_factory=dict)


@dataclass(frozen=True)
class PublicMatrixReceipt:
    """Deterministic receipt for a single public-matrix execution.

    ``roster_revision`` is the git commit SHA or ``"unknown"``.
    ``profile`` is the test profile name (``"quick"``, ``"release"``, etc.).
    ``marker_expression`` is the ``pytest -m`` expression, or ``None``.
    ``worker_info`` describes the concurrency model used.
    """

    roster_revision: str
    profile: str
    marker_expression: str | None = None
    worker_info: str = "serial"
    generated_at: str = ""
    lanes: tuple[PublicMatrixLaneResult, ...] = ()
    combined_coverage_percent: float | None = None
    combined_floor: int = 75
    overall_exit: int = 0
    schema_version: str = "template-public-matrix/v3"
    phase_durations: dict[str, float] = field(default_factory=dict)
    collection_counts: dict[str, int] = field(default_factory=dict)
    skip_reasons: dict[str, str] = field(default_factory=dict)
    cache_key: str = ""
    cache_inputs: dict[str, str] = field(default_factory=dict)

    def write(self, path: Path | str) -> Path:
        """Write deterministic JSON (sorted keys, no extraneous whitespace).

        ``generated_at`` is intentionally NOT part of the digest so the
        receipt is reproducible byte-for-byte when re-run against the same
        state.
        """
        path = Path(path) if isinstance(path, str) else path
        data = self._to_dict()
        content = json.dumps(data, indent=2, sort_keys=True, default=str) + "\n"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    @classmethod
    def read(cls, path: Path | str) -> PublicMatrixReceipt:
        """Load a previously written receipt from disk."""
        path = Path(path) if isinstance(path, str) else path
        data = json.loads(path.read_text(encoding="utf-8"))
        lanes = tuple(PublicMatrixLaneResult(**lane) for lane in data.pop("lanes", []))
        data.setdefault("schema_version", "template-public-matrix/v1")
        data.setdefault("phase_durations", {})
        data.setdefault("collection_counts", {})
        data.setdefault("skip_reasons", {})
        data.setdefault("cache_key", "")
        data.setdefault("cache_inputs", {})
        return cls(lanes=lanes, **data)

    def digest(self) -> str:
        """Content-addressable SHA-256 of the receipt payload (excluding generated_at)."""
        data = self._to_dict()
        data.pop("generated_at", None)
        raw = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def validate(self, roster: Sequence[str]) -> list[str]:
        """Negative-control validation.

        Returns a list of error strings. An empty list means the receipt
        is valid.

        Checks:
        1. Every name in *roster* has a lane result (missing-project failure).
        2. No lane has timed_out=True.
        3. No lane with exit_code != 0 (unless accounted for).
        4. No lane has coverage_percent < declared_floor (coverage-floor failure).
        5. No lane changed its project's output tree (output-isolation failure).
        """
        errors: list[str] = []
        lane_names = {lane.project_name for lane in self.lanes}
        if len(lane_names) != len(self.lanes):
            errors.append("DUPLICATE-PROJECT: receipt contains more than one lane for a project")

        # Negative control 1: missing project result
        for name in roster:
            if name not in lane_names:
                errors.append(f"MISSING-PROJECT: roster entry '{name}' has no lane result")

        # Negative control 2: lane errors
        if not self.phase_durations:
            errors.append("MISSING-PHASE-TIMING: receipt has no phase durations")
        elif any(duration < 0 for duration in self.phase_durations.values()):
            errors.append("INVALID-PHASE-TIMING: phase duration cannot be negative")
        if not self.cache_key:
            errors.append("MISSING-CACHE-IDENTITY: receipt has no cache key")
        if not self.cache_inputs:
            errors.append("MISSING-CACHE-INPUTS: receipt has no cache identity inputs")

        for lane in self.lanes:
            if lane.skip_reason:
                if lane.collection_count is not None:
                    errors.append(
                        f"SKIP-METADATA: skipped project '{lane.project_name}' must not report a collection count"
                    )
                if lane.skip_reason.startswith("error:") and lane.exit_code == 0:
                    errors.append(f"SKIP-STATUS: error skip for '{lane.project_name}' cannot have exit=0")
                continue
            if lane.exit_code == 0:
                if lane.collection_count is None:
                    errors.append(f"MISSING-COLLECTION: project '{lane.project_name}' has no collection count")
                elif lane.collection_count <= 0:
                    errors.append(f"EMPTY-COLLECTION: project '{lane.project_name}' reported zero collected tests")
                if lane.duration_seconds <= 0:
                    errors.append(f"MISSING-LANE-TIMING: project '{lane.project_name}' has no duration")
                if not lane.cache_key:
                    errors.append(f"MISSING-LANE-CACHE: project '{lane.project_name}' has no cache key")
                if not lane.output_isolation_digest:
                    errors.append(
                        f"MISSING-OUTPUT-DIGEST: project '{lane.project_name}' has no output-isolation digest"
                    )
                if not lane.resource_limits:
                    errors.append(f"MISSING-RESOURCE-LIMITS: project '{lane.project_name}' has no resource limits")
            if lane.timed_out:
                errors.append(f"TIMEOUT: project '{lane.project_name}' timed out")
            if lane.exit_code != 0:
                errors.append(f"EXIT-STATUS: project '{lane.project_name}' exit={lane.exit_code}")
            if not lane.output_isolation_ok:
                errors.append(f"OUTPUT-ISOLATION: project '{lane.project_name}' changed output/")

            # Negative control 4: coverage-floor failure
            if (
                lane.declared_floor is not None
                and lane.coverage_percent is not None
                and lane.coverage_percent < lane.declared_floor
            ):
                errors.append(
                    f"COVERAGE-FLOOR: project '{lane.project_name}' "
                    f"measured {lane.coverage_percent:.2f}% < "
                    f"declared floor {lane.declared_floor}%"
                )

        return errors

    def _to_dict(self) -> dict:
        """Deterministic dict for serialization (sorted lanes)."""
        raw = asdict(self)
        raw["lanes"] = sorted(raw["lanes"], key=lambda l: l["project_name"])
        return raw


def determine_worker_info(
    project_workers: str | int | None,
    parallel: str | int | None,
) -> str:
    """Describe the outer / inner concurrency model for the receipt."""
    outer = str(project_workers) if project_workers else "serial"
    inner = str(parallel) if parallel else "none"
    return f"outer={outer}, inner={inner}"


def build_public_matrix_receipt(
    *,
    roster_revision: str,
    profile: str = "quick",
    marker_expression: str | None = None,
    worker_info: str = "serial",
    lanes: Sequence[PublicMatrixLaneResult],
    combined_coverage_percent: float | None = None,
    combined_floor: int = 75,
    overall_exit: int = 0,
    phase_durations: dict[str, float] | None = None,
    collection_counts: dict[str, int] | None = None,
    skip_reasons: dict[str, str] | None = None,
    cache_key: str = "",
    cache_inputs: dict[str, str] | None = None,
) -> PublicMatrixReceipt:
    """Factory that builds a sorted-lane receipt from per-project results."""
    return PublicMatrixReceipt(
        roster_revision=roster_revision,
        profile=profile,
        marker_expression=marker_expression,
        worker_info=worker_info,
        generated_at="",
        lanes=tuple(lanes),
        combined_coverage_percent=combined_coverage_percent,
        combined_floor=combined_floor,
        overall_exit=overall_exit,
        phase_durations=dict(phase_durations or {}),
        collection_counts=dict(collection_counts or {}),
        skip_reasons=dict(skip_reasons or {}),
        cache_key=cache_key,
        cache_inputs=dict(cache_inputs or {}),
    )


def build_public_matrix_cache_key(
    *,
    roster_revision: str,
    profile: str,
    marker_expression: str | None,
    worker_info: str,
    project_names: Sequence[str],
    source_tree_identity: str = "",
    interpreter_identity: str = "",
    lockfile_identity: str = "",
    tool_versions: Mapping[str, str] | None = None,
) -> str:
    """Build a stable cache identity for a public-matrix execution plan."""
    payload = "\n".join(
        (
            roster_revision,
            profile,
            marker_expression or "",
            worker_info,
            source_tree_identity,
            interpreter_identity,
            lockfile_identity,
            *(f"{key}={value}" for key, value in sorted((tool_versions or {}).items())),
            *sorted(project_names),
        )
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


__all__ = [
    "PublicMatrixLaneResult",
    "PublicMatrixReceipt",
    "build_public_matrix_receipt",
    "build_public_matrix_cache_key",
    "determine_worker_info",
]
