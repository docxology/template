"""Typed terminal identity: refusal is preserved, labels name the cause.

Negative controls first: every condition except a plain completion must keep
refusing certification, so migrating a reader onto the typed condition can
never turn a refused attempt into an accepted one.
"""

from __future__ import annotations

import pytest

from infrastructure.core.pipeline.failure_identity import (
    ClockState,
    SupervisionCondition,
    refuses_certification,
    terminal_identity,
)
from infrastructure.core.pipeline.outcomes import StageStatus

NON_COMPLETED = tuple(
    condition for condition in SupervisionCondition if condition is not SupervisionCondition.COMPLETED
)


@pytest.mark.parametrize("condition", NON_COMPLETED)
def test_every_non_completed_condition_still_refuses_certification(condition: SupervisionCondition) -> None:
    """The conservative predicate is a superset: adding a label narrows nothing."""
    assert refuses_certification(condition) is True


def test_only_a_plain_completion_stops_refusing() -> None:
    assert refuses_certification(SupervisionCondition.COMPLETED) is False


def test_genuine_custody_refusal_stays_blocked_with_its_own_label() -> None:
    identity = terminal_identity(
        clock=ClockState(deadline_monotonic=1000.0, observed_completion_monotonic=120.0),
        custody_refused=True,
        command_error="bounded-run guardian refused source custody: token mismatch",
        original_exit=75,
    )
    assert identity.condition is SupervisionCondition.CUSTODY_REFUSAL
    assert identity.status is StageStatus.BLOCKED
    assert identity.refuses is True
    assert "token mismatch" in identity.diagnostic


def test_terminal_data_mismatch_is_typed_and_still_refuses() -> None:
    """The 4.5.0 acceptance recorded this condition under a custody label."""
    identity = terminal_identity(
        clock=ClockState(deadline_monotonic=15000.0, observed_completion_monotonic=10268.0),
        observation_failed="native original terminal data differs from actual supervised original OS custody",
        custody_condition=SupervisionCondition.TERMINAL_DATA_MISMATCH,
        original_exit=1,
    )
    assert identity.condition is SupervisionCondition.TERMINAL_DATA_MISMATCH
    assert identity.refuses is True
    assert "terminal data differs" in identity.diagnostic


def test_exit_124_without_a_consumed_clock_is_not_reported_as_a_timeout() -> None:
    """Regression: this exact shape was labelled `status: timed_out` / "Python stage timeout".

    Observed in acceptance attempt 1: original exit 124, guardian `timed_out: false`,
    deadline still ~4,400 s away.
    """
    identity = terminal_identity(
        clock=ClockState(deadline_monotonic=14667.95, observed_completion_monotonic=10268.80),
        supervisor_timed_out=False,
        original_exit=124,
        observed_exit=124,
    )
    assert identity.condition is SupervisionCondition.UNATTRIBUTED_EXIT_124
    assert identity.status is not StageStatus.TIMED_OUT
    assert identity.status is StageStatus.FAILED
    assert "timed out" not in identity.diagnostic
    assert "exit 124" in identity.diagnostic


def test_a_consumed_clock_is_still_a_timeout() -> None:
    identity = terminal_identity(
        clock=ClockState(deadline_monotonic=100.0, observed_completion_monotonic=100.0),
        original_exit=124,
    )
    assert identity.condition is SupervisionCondition.DEADLINE_EXHAUSTED
    assert identity.status is StageStatus.TIMED_OUT


def test_the_supervisor_timeout_flag_is_still_a_timeout() -> None:
    identity = terminal_identity(
        clock=ClockState(deadline_monotonic=9000.0, observed_completion_monotonic=10.0),
        supervisor_timed_out=True,
        original_exit=124,
    )
    assert identity.condition is SupervisionCondition.SUPERVISOR_TIMEOUT_FLAG
    assert identity.status is StageStatus.TIMED_OUT


def test_interruption_outranks_a_consumed_clock() -> None:
    identity = terminal_identity(
        clock=ClockState(deadline_monotonic=1.0, observed_completion_monotonic=5.0),
        supervisor_timed_out=True,
        original_exit=130,
    )
    assert identity.condition is SupervisionCondition.SCRIPT_INTERRUPTED
    assert identity.status is StageStatus.INTERRUPTED


def test_clock_state_records_arithmetic_and_never_infers_exhaustion_from_absence() -> None:
    """Consumption is only ever reported from a launch instant we actually saw."""
    real = ClockState(
        deadline_monotonic=14667.95,
        observed_completion_monotonic=10268.80,
        observed_start_monotonic=95.30,
    )
    assert real.remaining_seconds == pytest.approx(4399.15)
    assert real.consumed_seconds == pytest.approx(10173.50)
    assert real.exhausted is False
    payload = real.to_dict()
    assert payload["exhausted"] is False
    assert payload["remaining_seconds"] == pytest.approx(4399.15)

    no_start = ClockState(deadline_monotonic=14667.95, observed_completion_monotonic=10268.80)
    assert no_start.consumed_seconds is None
    assert no_start.exhausted is False

    unknown = ClockState()
    assert unknown.remaining_seconds is None
    assert unknown.consumed_seconds is None
    assert unknown.exhausted is False
    identity = terminal_identity(clock=unknown, original_exit=124)
    assert identity.condition is SupervisionCondition.UNATTRIBUTED_EXIT_124


def test_a_timeout_convention_inside_a_live_clock_is_never_a_timeout_label() -> None:
    """Known-wrong outcome: any 124 becoming `timed_out` regardless of the clock."""
    still_live = ClockState(deadline_monotonic=86_400.0, observed_completion_monotonic=86_399.0)
    assert still_live.exhausted is False
    identity = terminal_identity(clock=still_live, original_exit=124, supervisor_timed_out=False)
    assert identity.status is not StageStatus.TIMED_OUT


def test_success_and_ordinary_failures_keep_their_meanings() -> None:
    live = ClockState(deadline_monotonic=1000.0, observed_completion_monotonic=10.0)
    assert terminal_identity(clock=live, original_exit=0).status is StageStatus.SUCCEEDED
    assert terminal_identity(clock=live, original_exit=75).status is StageStatus.BLOCKED
    assert terminal_identity(clock=live, original_exit=3).status is StageStatus.FAILED
    missing = terminal_identity(clock=live, receipt_error="no completion receipt")
    assert missing.condition is SupervisionCondition.RECEIPT_MISSING
    assert missing.status is StageStatus.BLOCKED


def test_a_bare_124_under_the_declared_convention_keeps_the_timeout_label() -> None:
    """The repository's own 124 convention stays; only the refusal escapes it."""
    live = ClockState(deadline_monotonic=86_400.0, observed_completion_monotonic=86_399.0)
    identity = terminal_identity(
        clock=live,
        original_exit=124,
        script_timeout_convention=True,
    )
    assert identity.condition is SupervisionCondition.SCRIPT_TIMEOUT_CONVENTION
    assert identity.status is StageStatus.TIMED_OUT
    assert identity.refuses is True


def test_the_124_convention_cannot_relabel_an_unobserved_attempt() -> None:
    """The 4.5.0 mislabel: a composed 124 plus a failed observation read as a timeout.

    The acceptance run recorded `stage_key: render_pdf`, `status: timed_out`,
    `child_exit_code: 124` while the same attempt's supervision record reported
    `timed_out: false`, `custody_refused: true`, and the terminal-data
    mismatch. A real child timeout outranks a *later* refusal, but a 124 whose
    observation itself failed is not a timeout, and the convention must not
    relabel it.
    """
    live = ClockState(deadline_monotonic=14667.95, observed_completion_monotonic=10268.80)
    identity = terminal_identity(
        clock=live,
        original_exit=124,
        observed_exit=124,
        custody_refused=True,
        custody_condition=SupervisionCondition.TERMINAL_DATA_MISMATCH,
        observation_failed="native original terminal data differs from actual supervised original OS custody",
        script_timeout_convention=True,
    )
    assert identity.condition is SupervisionCondition.TERMINAL_DATA_MISMATCH
    assert identity.status is not StageStatus.TIMED_OUT
    assert identity.status is StageStatus.BLOCKED
    assert identity.refuses is True
