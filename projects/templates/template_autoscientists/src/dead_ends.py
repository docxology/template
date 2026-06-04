"""Dead-end registry ``D``: failed directions, keyed by (axis, direction).

Mirrors the AutoScientists dead-end registry that agents consult *before*
proposing, so exhausted directions are not re-explored. A direction is retired
after it fails to improve the champion ``threshold`` times in a row.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DeadEnd:
    """A retired (axis, direction) pair with the reason it was abandoned."""

    axis: int
    direction: str
    failures: int
    reason: str


@dataclass
class DeadEndRegistry:
    """Tracks consecutive failures per (axis, direction) and retires them."""

    threshold: int = 3
    _failures: dict[tuple[int, str], int] = field(default_factory=dict)
    _retired: dict[tuple[int, str], DeadEnd] = field(default_factory=dict)

    def is_dead_end(self, axis: int, direction: str) -> bool:
        """True once a direction has been retired."""
        return (axis, direction) in self._retired

    def record_failure(self, axis: int, direction: str) -> None:
        """Register a non-improving result; retire the direction at threshold."""
        key = (axis, direction)
        count = self._failures.get(key, 0) + 1
        self._failures[key] = count
        if count >= self.threshold and key not in self._retired:
            self._retired[key] = DeadEnd(
                axis=axis,
                direction=direction,
                failures=count,
                reason=f"{count} consecutive non-improving experiments",
            )

    def record_success(self, axis: int, direction: str) -> None:
        """Clear the failure streak after an improvement on this direction."""
        self._failures.pop((axis, direction), None)

    def retired(self) -> tuple[DeadEnd, ...]:
        """All retired directions, ordered by (axis, direction)."""
        return tuple(self._retired[key] for key in sorted(self._retired))

    def retired_keys(self) -> frozenset[tuple[int, str]]:
        """Retired ``(axis, direction)`` pairs — the set agents consult to avoid."""
        return frozenset(self._retired)
