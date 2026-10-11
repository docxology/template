"""Truthful stage completion and aggregate exit policy.

Child exit codes remain evidence. Run exit codes describe the overall execution
and cannot turn a paused, incomplete, or unverified skip into success.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from infrastructure.core.pipeline.types import PipelineStageResult


class StageStatus(StrEnum):
    """Machine-facing execution states, independent of display labels."""

    SUCCEEDED = "succeeded"
    CACHED = "cached"
    SKIPPED = "skipped"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    PAUSED = "paused"
    BLOCKED = "blocked"
    REJECTED = "rejected"
    ABORTED = "aborted"
    INTERRUPTED = "interrupted"


@dataclass(frozen=True)
class StageOutcome:
    """One positively classified execution outcome."""

    stage_key: str
    status: StageStatus
    child_exit_code: int | None = 0
    diagnostic: str = ""
    attempt_count: int = 1
    reason: str = ""
    receipt_validated: bool = False
    retryable: bool = False
    attempt_exit_codes: tuple[int, ...] = ()
    in_process_completed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.stage_key, str) or not self.stage_key or not isinstance(self.status, StageStatus):
            raise ValueError("Stage outcomes require a stable key and a declared state")
        if (
            (self.child_exit_code is not None and type(self.child_exit_code) is not int)
            or type(self.attempt_count) is not int
            or self.attempt_count < 1
        ):
            raise ValueError("Stage outcomes require integer exit codes and positive attempt counts")
        if (
            type(self.receipt_validated) is not bool
            or type(self.retryable) is not bool
            or type(self.in_process_completed) is not bool
            or not isinstance(self.attempt_exit_codes, tuple)
            or any(type(code) is not int for code in self.attempt_exit_codes)
        ):
            raise ValueError("Stage outcome receipt, retry, or attempt evidence is malformed")
        if self.in_process_completed and (self.child_exit_code is not None or self.attempt_exit_codes):
            raise ValueError("In-process completion cannot invent child exit evidence")

    @property
    def complete(self) -> bool:
        """Whether this outcome can satisfy its stage's contract."""
        if self.status is StageStatus.SUCCEEDED:
            return self.child_exit_code == 0 or (self.child_exit_code is None and self.in_process_completed)
        if self.status in {StageStatus.CACHED, StageStatus.SKIPPED}:
            return self.receipt_validated
        return False

    def __bool__(self) -> bool:
        """Completion is the only truth value of an outcome."""
        return self.complete

    def to_dict(self) -> dict[str, object]:
        """Serialize without losing child diagnostics."""
        return asdict(self)


def outcome_for_result(result: PipelineStageResult) -> StageOutcome:
    """Describe a canonical result, including in-process method stages."""
    if result.outcome is not None:
        return result.outcome
    key = result.stage_key or result.stage_name
    if result.hitl_pause and result.exit_code not in {124, 130}:
        status = StageStatus.PAUSED
    elif result.exit_code == 130:
        status = StageStatus.INTERRUPTED
    elif result.exit_code == 124:
        status = StageStatus.TIMED_OUT
    elif result.success and result.stage_completed and result.exit_code == 0:
        status = StageStatus.SUCCEEDED
    else:
        status = StageStatus.FAILED
    return StageOutcome(key, status, result.exit_code, result.error_message)


def attach_stage_outcome(result: PipelineStageResult, child: StageOutcome | None, key: str) -> PipelineStageResult:
    """Preserve child evidence while classifying hooks and intervention outcomes."""
    result.stage_key = key
    if child is not None and (child.status is StageStatus.INTERRUPTED or result.exit_code == 130):
        result.success = False
        result.exit_code = 130
        result.outcome = replace(
            child, stage_key=key, status=StageStatus.INTERRUPTED, diagnostic=result.error_message or child.diagnostic
        )
    elif result.hitl_pause and result.exit_code != 124:
        result.success = False
        result.exit_code = 75
        paused = child if child is not None else StageOutcome(key, StageStatus.PAUSED, None)
        result.outcome = replace(
            paused,
            stage_key=key,
            status=StageStatus.PAUSED,
            diagnostic=result.error_message or "Human decision required",
        )
    elif child is not None and result.exit_code in {124, 130}:
        result.outcome = replace(
            child,
            stage_key=key,
            status=StageStatus.TIMED_OUT if result.exit_code == 124 else StageStatus.INTERRUPTED,
            diagnostic=result.error_message or child.diagnostic,
        )
    elif child is not None and (not child.complete or result.success):
        result.outcome = replace(child, stage_key=key, diagnostic=result.error_message or child.diagnostic)
        result.exit_code = (
            75
            if child.status is StageStatus.BLOCKED
            else 124
            if child.status is StageStatus.TIMED_OUT
            else child.child_exit_code
            if child.child_exit_code is not None
            else (0 if child.complete else 1)
        )
        result.error_message = result.error_message or child.diagnostic
        result.success = child.complete
    elif child is not None:
        inferred = outcome_for_result(result)
        result.outcome = replace(child, stage_key=key, status=inferred.status, diagnostic=result.error_message)
    else:
        result.outcome = replace(
            outcome_for_result(result),
            stage_key=key,
            child_exit_code=None,
            in_process_completed=False,
        )
    return result


@dataclass(frozen=True)
class RunResult:
    """Completion of an explicit selected stage set."""

    expected_stage_keys: tuple[str, ...]
    outcomes: tuple[StageOutcome, ...]

    @classmethod
    def from_results(
        cls, results: list[PipelineStageResult], expected_stage_keys: tuple[str, ...] | None = None
    ) -> RunResult:
        """Convert execution results using the caller's compiled selection."""
        outcomes = tuple(outcome_for_result(result) for result in results)
        expected = expected_stage_keys if expected_stage_keys is not None else tuple(o.stage_key for o in outcomes)
        return cls(expected, outcomes)

    @property
    def complete(self) -> bool:
        """Every selected stage occurs exactly once in order and is complete."""
        keys = tuple(outcome.stage_key for outcome in self.outcomes)
        return (
            bool(self.expected_stage_keys)
            and len(set(self.expected_stage_keys)) == len(self.expected_stage_keys)
            and keys == self.expected_stage_keys
            and all(outcome.complete for outcome in self.outcomes)
        )

    @property
    def exit_code(self) -> int:
        """Return deterministic executed-run exit precedence."""
        states = {outcome.status for outcome in self.outcomes}
        if StageStatus.INTERRUPTED in states:
            return 130
        if StageStatus.TIMED_OUT in states:
            return 124
        if states & {StageStatus.FAILED, StageStatus.REJECTED, StageStatus.ABORTED}:
            return 1
        if states & {StageStatus.PAUSED, StageStatus.BLOCKED}:
            return 75
        return 0 if self.complete else 1


__all__ = ["RunResult", "StageOutcome", "StageStatus", "outcome_for_result", "attach_stage_outcome"]
