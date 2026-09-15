"""Property tests for the monoid laws of manuscript composition.

Deterministic (fixed seed / derandomized); hypothesis is a dev dependency
and the root pytest config already loads its plugin.
"""

from __future__ import annotations

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from infrastructure.formal_contracts.checker import (
    EMPTY_MANUSCRIPT,
    compose,
    compose_manuscripts,
)
from infrastructure.formal_contracts.model import Claim, Evidence, Section

# Well-formed block groups: each group is a valid manuscript fragment on
# its own, so every generated sequence composes cleanly. Ids are
# namespaced per manuscript family so that the monoidal union of three
# distinct families stays collision-free (composition is a disjoint
# union; collisions are a caller error, not a law violation).


_GROUP_MAKERS = (
    lambda p: [Section(id=f"{p}s1")],
    lambda p: [Section(id=f"{p}s2", children=(f"{p}c1",)), Claim(id=f"{p}c1")],
    lambda p: [
        Section(id=f"{p}s3", children=(f"{p}c2", f"{p}e1")),
        Claim(id=f"{p}c2"),
        Evidence(id=f"{p}e1", tier=1),
    ],
    lambda p: [Section(id=f"{p}s4", children=(f"{p}e2",)), Evidence(id=f"{p}e2", tier=2)],
)


def manuscript(prefix: str) -> st.SearchStrategy[object]:
    """A well-formed manuscript with ids namespaced by ``prefix``."""

    def build(indices: list[int]) -> object:
        blocks = [b for i in indices for b in _GROUP_MAKERS[i](prefix)]
        return compose(blocks)

    return st.builds(build, st.lists(st.integers(0, 3), max_size=4, unique=True).map(sorted))


@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
    derandomize=True,
)
@given(a=manuscript("a"), b=manuscript("b"), c=manuscript("c"))
def test_composition_is_associative(a: object, b: object, c: object) -> None:
    left = compose_manuscripts(compose_manuscripts(a, b), c).blocks  # type: ignore[arg-type]
    right = compose_manuscripts(a, compose_manuscripts(b, c)).blocks  # type: ignore[arg-type]
    assert left == right


@settings(max_examples=25, deadline=None, derandomize=True)
@given(a=manuscript("a"))
def test_empty_manuscript_is_identity(a: object) -> None:
    assert compose_manuscripts(EMPTY_MANUSCRIPT, a).blocks == a.blocks  # type: ignore[attr-defined]
    assert compose_manuscripts(a, EMPTY_MANUSCRIPT).blocks == a.blocks  # type: ignore[attr-defined]
