"""Known-bad fixture: a non-exhaustive ``match`` over ``Result`` (ISC-4).

`mypy --strict` MUST reject this file. ``match_result`` handles only the
``Ok`` arm and falls through to ``typing.assert_never`` without a
``case Err(...)`` arm. Because ``Result[int, str]`` narrows to
``Ok[int] | Err[str]``, mypy's exhaustiveness checking on the *falling
through* branch still sees the un-narrowed ``Err[str]`` possibility --
the type of ``result`` at the ``assert_never`` call site has not been
narrowed away by the sole ``Ok`` case, so the argument type is
``Err[str]`` instead of the required ``Never``, and mypy --strict flags
that mismatch. This is the closest structural analogue Python offers to
compiler-enforced sum-type exhaustiveness (see
``template_formal.types.result`` docstring) -- it is a static proof
obligation discharged by mypy, not a runtime check. Never imported or
executed -- only type-checked in isolation by tests/test_mypy_oracle.py.
"""

from __future__ import annotations

from typing import assert_never

from template_formal.types.result import Ok, Result


def bad_usage(result: Result[int, str]) -> int:
    match result:
        case Ok(value=value):
            return value
    # error: Argument 1 to "assert_never" has incompatible type "Err[str]"; expected "Never"
    assert_never(result)
