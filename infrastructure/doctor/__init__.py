"""Doctor module — diagnose and safely repair template repository state.

Design summary (full contract in :mod:`.safety`):

* :mod:`.detectors` produce read-only :class:`~.models.Finding` objects.
* :mod:`.fixers` translate findings into :class:`~.models.FixPlan` objects.
* :func:`.safety.mutate` is the only entry point that touches the
  filesystem; it snapshots, executes, hashes, and journals every
  change so :func:`.safety.undo` can replay them in reverse.
* :mod:`.scorecard` summarises findings as a numeric score.
* :mod:`.reporter` renders text + JSON outputs and maps severities to
  stable exit codes.
* :mod:`.cli` exposes ``python -m infrastructure.doctor``.

Quick start::

    from pathlib import Path
    from infrastructure.doctor import run_detectors, compute_scorecard

    findings = run_detectors(Path("."))
    overall, dims = compute_scorecard(findings)

Or from the shell::

    uv run python -m infrastructure.doctor                  # diagnose
    uv run python -m infrastructure.doctor fix --plan       # dry-run
    uv run python -m infrastructure.doctor fix --apply      # safe set
    uv run python -m infrastructure.doctor fix --apply --aggressive
    uv run python -m infrastructure.doctor undo --last
    uv run python -m infrastructure.doctor history
    uv run python -m infrastructure.doctor capabilities

The agent-facing contract is intentionally narrow: every change is
logged in ``.doctor/actions.jsonl`` and a byte-for-byte backup lives in
``.doctor/backups/<action_id>/``. Healthy is provable, not vibes.
"""

from infrastructure.doctor.detectors import DETECTORS, run_detectors
from infrastructure.doctor.fixers import (
    FIXER_REGISTRY,
    build_plans_for_findings,
)
from infrastructure.doctor.models import (
    DoctorReport,
    Finding,
    FixPlan,
    MutateRecord,
    RepairLevel,
    Severity,
    TherapyLevel,
)
from infrastructure.doctor.reporter import (
    EXIT_CRITICAL,
    EXIT_ERROR,
    EXIT_HEALTHY,
    EXIT_REGRESSION,
    EXIT_USAGE,
    EXIT_WARN,
    compute_exit_code,
    render_report_json,
    render_report_text,
)
from infrastructure.doctor.safety import (
    DoctorSafetyError,
    DoctorState,
    load_journal,
    mutate,
    register_handler,
    undo,
)
from infrastructure.doctor.scorecard import (
    DIMENSION_WEIGHTS,
    DIMENSIONS,
    compute_scorecard,
)


__all__ = [
    # Models
    "Severity",
    "TherapyLevel",
    "Finding",
    "FixPlan",
    "RepairLevel",
    "MutateRecord",
    "DoctorReport",
    # Detectors
    "DETECTORS",
    "run_detectors",
    # Fixers
    "FIXER_REGISTRY",
    "build_plans_for_findings",
    # Safety
    "DoctorSafetyError",
    "DoctorState",
    "mutate",
    "undo",
    "load_journal",
    "register_handler",
    # Scorecard
    "DIMENSIONS",
    "DIMENSION_WEIGHTS",
    "compute_scorecard",
    # Reporter
    "render_report_text",
    "render_report_json",
    "compute_exit_code",
    "EXIT_HEALTHY",
    "EXIT_WARN",
    "EXIT_ERROR",
    "EXIT_CRITICAL",
    "EXIT_REGRESSION",
    "EXIT_USAGE",
]
