"""Data models for the doctor module.

Dataclasses describing what a doctor run produces:

* :class:`Severity` — ordered severity levels.
* :class:`Finding` — a single read-only diagnostic result.
* :class:`RepairLevel` — one therapy intensity (conservative/moderate/radical).
* :class:`FixPlan` — a declarative description of an intended mutation.
* :class:`MutateRecord` — the audit record produced by the safety chokepoint.
* :class:`DoctorReport` — the aggregate result of one diagnose / fix run.

The models are intentionally pure data containers so they serialise cleanly
to JSON for ``--json`` output, the ``actions.jsonl`` journal, and the
robot-readable capability surface used by agentic callers.
"""

from dataclasses import asdict, dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any


__all__ = [
    "Severity",
    "TherapyLevel",
    "RepairLevel",
    "Finding",
    "FixPlan",
    "MutateRecord",
    "DoctorReport",
    "to_jsonable",
]


class Severity(IntEnum):
    """Ordered diagnostic severity. Higher = worse."""

    INFO = 0
    WARN = 1
    ERROR = 2
    CRITICAL = 3

    @property
    def label(self) -> str:
        """Human-readable label for tables / logs."""
        return self.name.lower()


class TherapyLevel(IntEnum):
    """How radical a fixer is.

    * ``CONSERVATIVE`` — touches only disposable / derived state
      (caches, executable bits, idempotent file moves).
    * ``MODERATE`` — reproducible side effects (re-run ``uv sync``,
      regenerate a derived file from source).
    * ``RADICAL`` — destructive or non-trivially reversible
      operations (delete an orphan output tree). Always backed up.
    """

    CONSERVATIVE = 0
    MODERATE = 1
    RADICAL = 2

    @property
    def label(self) -> str:
        """Process label."""
        return self.name.lower()


@dataclass(frozen=True)
class RepairLevel:
    """One available therapy for a finding.

    The doctor never decides on its own which level to apply: the user
    (or an agent) picks via ``--apply`` / ``--aggressive``.
    """

    level: TherapyLevel
    fix_id: str
    description: str


@dataclass(frozen=True)
class Finding:
    """Outcome of one read-only detector.

    A ``Finding`` is *always* produced — even when the detector finds
    nothing wrong (``severity == INFO`` and ``healthy is True``). That
    way the scorecard sees the full diagnostic surface and an absent
    detector never silently inflates the score.
    """

    code: str
    title: str
    severity: Severity
    healthy: bool
    description: str
    evidence: dict[str, Any] = field(default_factory=dict)
    repair_levels: tuple[RepairLevel, ...] = field(default_factory=tuple)

    def to_jsonable(self) -> dict[str, Any]:
        """Convert this object to a JSON-serializable form."""
        return {
            "code": self.code,
            "title": self.title,
            "severity": self.severity.label,
            "healthy": self.healthy,
            "description": self.description,
            "evidence": to_jsonable(self.evidence),
            "repair_levels": [
                {
                    "level": rl.level.label,
                    "fix_id": rl.fix_id,
                    "description": rl.description,
                }
                for rl in self.repair_levels
            ],
        }


@dataclass(frozen=True)
class FixPlan:
    """Declarative description of an intended mutation.

    The plan is consumed by :func:`infrastructure.doctor.safety.mutate`,
    which is the only place that touches the filesystem on behalf of a
    fixer. Plans must enumerate every path they intend to read, write,
    delete, or chmod so the safety layer can snapshot them up front.

    Attributes:
        fix_id: Stable identifier — matches ``RepairLevel.fix_id``.
        title: Short human description, e.g. ``"Make run.sh executable"``.
        therapy: How radical the operation is.
        finding_code: Code of the originating finding (for traceability).
        affected_paths: Paths the fixer will mutate (read-only paths do
            not need to be listed).
        action_kind: Free-form discriminator consumed by
            :func:`apply_fix` — e.g. ``"delete_paths"``, ``"chmod"``,
            ``"write_file"``, ``"run_command"``.
        params: Action-specific parameters (file contents, modes, etc.).
        reversible: ``True`` iff the safety layer can restore the
            previous state from its backup. ``False`` for actions like
            ``run_command`` whose side effects cannot be undone by
            replacing files (e.g. ``uv sync`` already changed the venv).
    """

    fix_id: str
    title: str
    therapy: TherapyLevel
    finding_code: str
    affected_paths: tuple[Path, ...] = field(default_factory=tuple)
    action_kind: str = "noop"
    params: dict[str, Any] = field(default_factory=dict)
    reversible: bool = True

    def to_jsonable(self) -> dict[str, Any]:
        """Convert this object to a JSON-serializable form."""
        return {
            "fix_id": self.fix_id,
            "title": self.title,
            "therapy": self.therapy.label,
            "finding_code": self.finding_code,
            "affected_paths": [str(p) for p in self.affected_paths],
            "action_kind": self.action_kind,
            "params": to_jsonable(self.params),
            "reversible": self.reversible,
        }


@dataclass(frozen=True)
class MutateRecord:
    """Audit record produced by the mutate() chokepoint.

    Stored as one JSON line in ``.doctor/actions.jsonl``. The combination
    of ``action_id`` and ``backup_dir`` is sufficient to undo a
    reversible action.
    """

    action_id: str
    timestamp_utc: str
    fix_id: str
    finding_code: str
    therapy: str
    title: str
    backup_dir: str
    pre_hashes: dict[str, str]
    post_hashes: dict[str, str]
    affected_paths: list[str]
    reversible: bool
    applied: bool
    error: str | None = None

    def to_jsonable(self) -> dict[str, Any]:
        """Convert this object to a JSON-serializable form."""
        return asdict(self)


@dataclass(frozen=True)
class DoctorReport:
    """Aggregate result of one doctor run.

    Attributes:
        findings: Every finding produced by detectors, in deterministic
            order (sorted by ``code``).
        applied: Mutate records for fixes that ran successfully.
        skipped: Plans the user elected not to apply (or that were
            filtered out by ``--select``).
        failed: Plans that errored during application.
        overall_score: 0–100 scorecard score (see :mod:`.scorecard`).
        dimension_scores: Per-dimension 0–100 scores.
        exit_code: Stable BSD-style exit code (see :mod:`.reporter`).
    """

    findings: list[Finding]
    applied: list[MutateRecord]
    skipped: list[FixPlan]
    failed: list[MutateRecord]
    overall_score: float
    dimension_scores: dict[str, float]
    exit_code: int

    def to_jsonable(self) -> dict[str, Any]:
        """Convert this object to a JSON-serializable form."""
        return {
            "findings": [f.to_jsonable() for f in self.findings],
            "applied": [r.to_jsonable() for r in self.applied],
            "skipped": [p.to_jsonable() for p in self.skipped],
            "failed": [r.to_jsonable() for r in self.failed],
            "overall_score": round(self.overall_score, 2),
            "dimension_scores": {name: round(score, 2) for name, score in self.dimension_scores.items()},
            "exit_code": self.exit_code,
        }


def to_jsonable(value: Any) -> Any:
    """Recursively convert ``value`` into a JSON-serialisable form.

    Used by ``Finding.evidence`` and ``FixPlan.params`` which may
    contain :class:`Path` objects. Falls back to ``str()`` for any type
    the default JSON encoder cannot handle.
    """

    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)
