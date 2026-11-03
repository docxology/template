"""The typed terminal condition reaches the retained stage outcome record.

The acceptance run that motivated this file reported its failure as a bare
``Python stage timeout`` while the retained execution record held ``render_pdf``
with ``status: timed_out``, ``child_exit_code: 124`` and
``attempt_exit_codes: [124]``. Nothing in the pipeline record said that the
child's own exit had decided, so recovering that fact took an artifact
download. These tests pin the two properties that make the condition usable:
it names the cause without moving the verdict, and it is absent from records
that have no condition at all.
"""

from __future__ import annotations

import time

from infrastructure.core.execution_boundary import BoundedSubprocessResult
from infrastructure.core.pipeline.failure_identity import SupervisionCondition
from infrastructure.core.pipeline.outcomes import StageOutcome, StageStatus
from infrastructure.core.pipeline.stage_launch import _typed_condition

_LONG_CLOCK = 3600.0


def _child(**overrides: object) -> BoundedSubprocessResult:
    """Build a real supervised child record; no stand-ins are involved."""
    fields: dict[str, object] = {
        "argv": ("python", "-m", "infrastructure.core.pipeline.stage_worker"),
        "returncode": 124,
        "timed_out": False,
        "original_returncode": 124,
    }
    fields.update(overrides)
    return BoundedSubprocessResult(**fields)  # type: ignore[arg-type]


def _condition(child: BoundedSubprocessResult, *, original: int, decided: bool, convention: bool) -> str:
    """Name the condition exactly as the stage launch sites do."""
    return _typed_condition(
        child=child,
        original=original,
        deadline=time.monotonic() + _LONG_CLOCK,
        known_original=True,
        child_decided_124=decided,
        convention_124=convention,
    )


def test_untyped_outcomes_serialize_exactly_as_before() -> None:
    """A success and an ordinary failure keep the exact recorded shape."""
    succeeded = StageOutcome("setup", StageStatus.SUCCEEDED, 0)
    failed = StageOutcome("analysis", StageStatus.FAILED, 1, "Stage script exited 1", attempt_exit_codes=(1,))
    assert succeeded.to_dict() == {
        "stage_key": "setup",
        "status": StageStatus.SUCCEEDED,
        "child_exit_code": 0,
        "diagnostic": "",
        "attempt_count": 1,
        "reason": "",
        "receipt_validated": False,
        "retryable": False,
        "attempt_exit_codes": (),
        "in_process_completed": False,
    }
    assert "condition" not in failed.to_dict()


def test_child_owned_124_is_named_without_a_declared_convention() -> None:
    """A bare 124 with the clock running is the child deciding, not a supervisor."""
    assert _condition(_child(), original=124, decided=True, convention=False) == (
        SupervisionCondition.UNATTRIBUTED_EXIT_124
    )


def test_supervisor_timeout_keeps_its_own_label() -> None:
    """A real supervision timeout is not relabelled as a child decision."""
    child = _child(timed_out=True, original_returncode=None)
    assert _condition(child, original=124, decided=False, convention=False) == (
        SupervisionCondition.SUPERVISOR_TIMEOUT_FLAG
    )


def test_declared_convention_keeps_the_convention_label() -> None:
    """A declared script-timeout convention still says so."""
    assert _condition(_child(), original=124, decided=True, convention=True) == (
        SupervisionCondition.SCRIPT_TIMEOUT_CONVENTION
    )


def test_downstream_refusal_does_not_overwrite_the_child_cause() -> None:
    """A refusal observed after the child's own 124 stays evidence, not cause."""
    child = _child(custody_refused=True, command_error="completed stage bindings changed")
    assert _condition(child, original=124, decided=True, convention=True) == (
        SupervisionCondition.SCRIPT_TIMEOUT_CONVENTION
    )


def test_unordered_refusal_keeps_the_refusal_label() -> None:
    """Without the child's own 124 there is no ordering evidence, so it stands."""
    child = _child(returncode=75, original_returncode=75, custody_refused=True, command_error="custody refused")
    assert _condition(child, original=75, decided=False, convention=False) == SupervisionCondition.CUSTODY_REFUSAL


def test_typed_condition_reaches_the_retained_record() -> None:
    """The condition lands in the serialized record beside the stage it belongs to."""
    child = _child(custody_refused=True, command_error="completed stage bindings changed")
    record = StageOutcome(
        "render_pdf",
        StageStatus.TIMED_OUT,
        124,
        "Python stage timeout",
        attempt_exit_codes=(124,),
        condition=_condition(child, original=124, decided=True, convention=False),
    ).to_dict()
    assert record["stage_key"] == "render_pdf"
    assert record["attempt_exit_codes"] == (124,)
    assert record["status"] is StageStatus.TIMED_OUT
    assert record["diagnostic"] == "Python stage timeout"
    assert record["condition"] == SupervisionCondition.UNATTRIBUTED_EXIT_124
