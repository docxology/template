"""Typed terminal identity for a supervised stage attempt.

One supervised attempt can end for several distinct reasons, and the *label* a
record carries decides whether a human or a reader can act on it. Deriving that
label from an exit-code convention alone conflates cases that need different
responses: the 4.5.0 acceptance attempt labelled a terminal-data mismatch as
``status: timed_out`` / "Python stage timeout" while the guardian reported
``timed_out: false`` and a deadline that was still thousands of seconds away,
and a single ``custody_refused`` boolean carried deadline expiry, terminal-data
mismatch and genuine custody refusal alike.

This module is the single source of that decision:

* :class:`SupervisionCondition` names the observed cause.
* :class:`ClockState` records the clock arithmetic as data, so "timed out" is
  only ever claimable from a clock that was actually consumed.
* :func:`terminal_identity` maps observed facts to a condition, a stage status
  and a diagnostic that names the cause.
* :func:`refuses_certification` is the conservative predicate behind the legacy
  ``custody_refused`` boolean: it stays true for every non-completed condition,
  so existing readers cannot silently start accepting a refused attempt. The
  typed condition narrows the *label*, never the *refusal*.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from infrastructure.core.pipeline.outcomes import StageStatus

#: Exit-code conventions the supervised legs use for non-ordinary endings.
INTERRUPTION_EXIT_CODES = frozenset({130, -2})
TIMEOUT_CONVENTION_EXIT = 124
BLOCKED_EXIT = 75


class SupervisionCondition(StrEnum):
    """Observed cause of a supervised attempt's terminal state."""

    COMPLETED = "completed"
    #: The declared clock was consumed (guardian flag or an exhausted deadline).
    DEADLINE_EXHAUSTED = "deadline_exhausted"
    #: The guardian's own timeout flag, independent of our deadline arithmetic.
    SUPERVISOR_TIMEOUT_FLAG = "supervisor_timeout_flag"
    #: Exit 124 with no consumed clock: the convention fired without a timeout.
    UNATTRIBUTED_EXIT_124 = "unattributed_exit_124"
    #: The supervision boundary refused to certify the child's terminal data.
    CUSTODY_REFUSAL = "custody_refusal"
    #: The child's terminal data disagreed with the supervised OS observation.
    TERMINAL_DATA_MISMATCH = "terminal_data_mismatch"
    #: An observation raised before any terminal verdict was reached.
    OBSERVATION_FAILED = "observation_failed"
    #: The stage script reported its own timeout convention (exit 124).
    SCRIPT_TIMEOUT_CONVENTION = "script_timeout_convention"
    #: No valid completion receipt could be read.
    RECEIPT_MISSING = "receipt_missing"
    #: The launch boundary reported a command/launch error.
    COMMAND_ERROR = "command_error"
    #: The stage script was interrupted (exit 130 / -2).
    SCRIPT_INTERRUPTED = "script_interrupted"
    #: The stage script exited non-zero for its own reason.
    SCRIPT_FAILED = "script_failed"


#: Conditions that mean the attempt is not certifiable as a completion.
_NON_COMPLETED = frozenset(
    condition for condition in SupervisionCondition if condition is not SupervisionCondition.COMPLETED
)


@dataclass(frozen=True)
class ClockState:
    """The clock arithmetic of one supervised attempt, recorded as data.

    Each field is an observation, not an inference: ``consumed_seconds`` stays
    ``None`` unless the launch instant was actually observed, and ``exhausted``
    is false whenever the deadline or the completion instant is unknown. An
    unknown clock is never a consumed clock.
    """

    deadline_monotonic: float | None = None
    observed_completion_monotonic: float | None = None
    observed_start_monotonic: float | None = None

    @property
    def consumed_seconds(self) -> float | None:
        """Seconds actually observed between launch and completion."""
        if self.observed_start_monotonic is None or self.observed_completion_monotonic is None:
            return None
        return max(0.0, self.observed_completion_monotonic - self.observed_start_monotonic)

    @property
    def remaining_seconds(self) -> float | None:
        """Seconds left on the declared clock when the attempt ended."""
        if self.deadline_monotonic is None or self.observed_completion_monotonic is None:
            return None
        return self.deadline_monotonic - self.observed_completion_monotonic

    @property
    def exhausted(self) -> bool:
        """True only when the declared clock was actually consumed."""
        remaining = self.remaining_seconds
        return remaining is not None and remaining <= 0

    def to_dict(self) -> dict[str, object]:
        """Serialize the observed clock facts without inferring a verdict."""
        return {
            "deadline_monotonic": self.deadline_monotonic,
            "observed_start_monotonic": self.observed_start_monotonic,
            "observed_completion_monotonic": self.observed_completion_monotonic,
            "remaining_seconds": self.remaining_seconds,
            "consumed_seconds": self.consumed_seconds,
            "exhausted": self.exhausted,
        }


@dataclass(frozen=True)
class SupervisionIdentity:
    """Typed terminal identity: the cause, the stage status, and its label."""

    condition: SupervisionCondition
    status: StageStatus
    diagnostic: str

    @property
    def refuses(self) -> bool:
        """Return whether this identity refuses to certify the attempt."""
        return refuses_certification(self.condition)


def refuses_certification(condition: SupervisionCondition) -> bool:
    """Conservative refusal predicate behind the legacy ``custody_refused``.

    True for every condition other than a plain completion. This keeps the
    extension of the existing boolean unchanged while the typed condition
    states which cause fired.
    """
    return condition in _NON_COMPLETED


def terminal_identity(
    *,
    clock: ClockState,
    supervisor_timed_out: bool = False,
    original_exit: int | None = None,
    observed_exit: int | None = None,
    custody_refused: bool = False,
    custody_condition: SupervisionCondition | None = None,
    observation_failed: str = "",
    command_error: str = "",
    receipt_error: str = "",
) -> SupervisionIdentity:
    """Map observed supervision facts onto one typed terminal identity.

    Precedence is by observed cause, not by exit-code convention: an
    interruption or an actually consumed clock is reported as such, a custody
    condition reports its own typed cause, and an exit-124 convention with no
    consumed clock is reported as unattributed instead of as a timeout.
    """
    exit_code = original_exit if original_exit is not None else observed_exit
    if exit_code in INTERRUPTION_EXIT_CODES:
        return SupervisionIdentity(
            SupervisionCondition.SCRIPT_INTERRUPTED,
            StageStatus.INTERRUPTED,
            "supervised attempt was interrupted",
        )
    if supervisor_timed_out:
        return SupervisionIdentity(
            SupervisionCondition.SUPERVISOR_TIMEOUT_FLAG,
            StageStatus.TIMED_OUT,
            "supervisor reported the declared clock was consumed",
        )
    if clock.exhausted:
        return SupervisionIdentity(
            SupervisionCondition.DEADLINE_EXHAUSTED,
            StageStatus.TIMED_OUT,
            "declared operation deadline was consumed by the attempt",
        )
    if observation_failed:
        return SupervisionIdentity(
            custody_condition or SupervisionCondition.OBSERVATION_FAILED,
            StageStatus.BLOCKED,
            observation_failed,
        )
    if custody_refused:
        return SupervisionIdentity(
            custody_condition or SupervisionCondition.CUSTODY_REFUSAL,
            StageStatus.BLOCKED,
            command_error or "supervision boundary refused to certify the attempt",
        )
    if exit_code == TIMEOUT_CONVENTION_EXIT:
        return SupervisionIdentity(
            SupervisionCondition.UNATTRIBUTED_EXIT_124,
            StageStatus.FAILED,
            "exit 124 was observed without a consumed clock; the timeout "
            "convention fired but no declared bound expired",
        )
    if receipt_error:
        return SupervisionIdentity(
            SupervisionCondition.RECEIPT_MISSING,
            StageStatus.BLOCKED,
            receipt_error,
        )
    if command_error:
        return SupervisionIdentity(
            SupervisionCondition.COMMAND_ERROR,
            StageStatus.FAILED,
            command_error,
        )
    if exit_code is None:
        return SupervisionIdentity(
            SupervisionCondition.RECEIPT_MISSING,
            StageStatus.BLOCKED,
            "the attempt produced neither a terminal exit nor a completion receipt",
        )
    if exit_code == 0:
        return SupervisionIdentity(SupervisionCondition.COMPLETED, StageStatus.SUCCEEDED, "")
    if exit_code == BLOCKED_EXIT:
        return SupervisionIdentity(
            SupervisionCondition.SCRIPT_FAILED,
            StageStatus.BLOCKED,
            "stage script exited 75 (blocked convention)",
        )
    return SupervisionIdentity(
        SupervisionCondition.SCRIPT_FAILED,
        StageStatus.FAILED,
        f"stage script exited {exit_code}",
    )


__all__ = [
    "BLOCKED_EXIT",
    "INTERRUPTION_EXIT_CODES",
    "TIMEOUT_CONVENTION_EXIT",
    "ClockState",
    "SupervisionCondition",
    "SupervisionIdentity",
    "refuses_certification",
    "terminal_identity",
]
