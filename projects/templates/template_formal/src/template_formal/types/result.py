"""``Result[T, E]`` — a tagged-union ADT standing in for typed effects.

Python has no built-in algebraic data types and no checked effect system.
``Result`` recovers the useful part of both for error handling: a value is
either ``Ok(value)`` or ``Err(error)``, distinguished by a ``Literal`` tag
field that ``match``/``case`` can narrow on exhaustively. mypy --strict,
combined with ``typing.assert_never`` in the default arm, rejects a
``match`` that only handles ``Ok`` and forgets ``Err`` — this is the
closest structural analogue Python offers to Haskell/OCaml sum-type
exhaustiveness checking (see manuscript §"Algebraic data types").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Generic, Literal, TypeVar, Union

T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E")


@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
    """The success arm of :class:`Result`."""

    value: T
    tag: Literal["ok"] = field(default="ok", init=False)


@dataclass(frozen=True, slots=True)
class Err(Generic[E]):
    """The failure arm of :class:`Result`."""

    error: E
    tag: Literal["err"] = field(default="err", init=False)


Result = Union[Ok[T], Err[E]]


def is_ok(result: Result[T, E]) -> bool:
    """Return ``True`` iff ``result`` is the :class:`Ok` arm."""
    match result:
        case Ok():
            return True
        case Err():
            return False


def map_result(result: Result[T, E], func: Callable[[T], U]) -> "Result[U, E]":
    """Apply ``func`` to the ``Ok`` payload; pass ``Err`` through unchanged."""
    match result:
        case Ok(value=value):
            return Ok(func(value))
        case Err(error=error):
            return Err(error)


def and_then(result: Result[T, E], func: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
    """Kleisli-composition bind: chain a ``Result``-returning function."""
    match result:
        case Ok(value=value):
            return func(value)
        case Err(error=error):
            return Err(error)


def unwrap_or(result: Result[T, E], default: T) -> T:
    """Return the ``Ok`` payload, or ``default`` if ``result`` is ``Err``."""
    match result:
        case Ok(value=value):
            return value
        case Err():
            return default
