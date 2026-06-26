"""Tests for the dead-end registry."""

from __future__ import annotations

from src.dead_ends import DeadEndRegistry


def test_direction_retires_at_threshold() -> None:
    reg = DeadEndRegistry(threshold=3)
    assert reg.is_dead_end(0, "increase") is False
    reg.record_failure(0, "increase")
    reg.record_failure(0, "increase")
    assert reg.is_dead_end(0, "increase") is False
    reg.record_failure(0, "increase")
    assert reg.is_dead_end(0, "increase") is True


def test_success_clears_failure_streak() -> None:
    reg = DeadEndRegistry(threshold=2)
    reg.record_failure(1, "decrease")
    reg.record_success(1, "decrease")
    reg.record_failure(1, "decrease")
    assert reg.is_dead_end(1, "decrease") is False


def test_directions_are_tracked_independently() -> None:
    reg = DeadEndRegistry(threshold=1)
    reg.record_failure(0, "increase")
    assert reg.is_dead_end(0, "increase") is True
    assert reg.is_dead_end(0, "decrease") is False


def test_retired_is_sorted_and_records_reason() -> None:
    reg = DeadEndRegistry(threshold=1)
    reg.record_failure(2, "increase")
    reg.record_failure(0, "decrease")
    retired = reg.retired()
    assert [(d.axis, d.direction) for d in retired] == [(0, "decrease"), (2, "increase")]
    assert retired[0].failures == 1
    assert "non-improving" in retired[0].reason


def test_retiring_is_idempotent() -> None:
    reg = DeadEndRegistry(threshold=1)
    reg.record_failure(0, "increase")
    first = reg.retired()[0]
    reg.record_failure(0, "increase")
    # Already retired: the original record (failures=1) is preserved.
    assert reg.retired()[0] is first
    assert reg.retired()[0].failures == 1


def test_success_on_unseen_direction_is_noop() -> None:
    reg = DeadEndRegistry(threshold=1)
    reg.record_success(5, "increase")
    assert reg.is_dead_end(5, "increase") is False


def test_retired_keys_returns_retired_pairs() -> None:
    reg = DeadEndRegistry(threshold=1)
    assert reg.retired_keys() == frozenset()
    reg.record_failure(1, "increase")
    reg.record_failure(0, "decrease")
    assert reg.retired_keys() == frozenset({(1, "increase"), (0, "decrease")})


def test_success_on_retired_direction_does_not_unretire() -> None:
    """Negative control: a success after retirement must not re-open the direction.

    Retirement is permanent.  A ``record_success`` call on an already-retired
    ``(axis, direction)`` clears the *failure streak counter* for future
    bookkeeping but must not remove the key from ``_retired`` or cause
    ``is_dead_end`` to return False.
    """
    reg = DeadEndRegistry(threshold=1)
    reg.record_failure(0, "increase")  # now retired
    assert reg.is_dead_end(0, "increase") is True
    reg.record_success(0, "increase")  # attempt to re-open
    # Must still be retired.
    assert reg.is_dead_end(0, "increase") is True
    assert (0, "increase") in reg.retired_keys()


def test_default_threshold_is_three() -> None:
    """Convenience guard: the default threshold is 3 (as documented)."""
    reg = DeadEndRegistry()
    reg.record_failure(0, "increase")
    reg.record_failure(0, "increase")
    assert reg.is_dead_end(0, "increase") is False
    reg.record_failure(0, "increase")
    assert reg.is_dead_end(0, "increase") is True
