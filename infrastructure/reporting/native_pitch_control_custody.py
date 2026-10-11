"""One fixed Pitch child role in the existing Source control custodian."""

from __future__ import annotations

from infrastructure.reporting.native_pitch_control_worker import CHILD_SCHEMA, WORKER
from infrastructure.reporting.native_print_child_custody import _ControlRole, _SourceControlReaderOperation

PITCH_ROLE = _ControlRole(
    CHILD_SCHEMA,
    WORKER,
    "pitch-child",
    "PITCH_OBSERVATION_V1",
    "PITCH_CLOSURE_V1",
    False,
    (
        "reporting/native_pitch_control_worker.py",
        "reporting/native_pitch_control_plan.py",
        "reporting/native_pitch_control_run.py",
        "reporting/native_pitch_control_mutations.py",
        "reporting/native_pitch_source_parity.py",
        "reporting/native_projection_checks.py",
        "reporting/native_source_external_admission.py",
        "reporting/native_tool_process.py",
    ),
    frozenset({"formats", "plan_digest"}),
)


class PitchControlReaderOperation(_SourceControlReaderOperation):
    """Actual parent plus audited fixed Pitch Code, never constructed from DATA."""
