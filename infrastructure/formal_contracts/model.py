"""Typed block model for well-typed research manuscripts (GOAL C seed).

The core object language is a finite set of frozen dataclass blocks. A
manuscript is a directed graph over these blocks: containment edges from
``Section`` blocks, typed dependency edges (``DependencyEdge``) between
content blocks. Formally, this is a **preorder-enriched graph with a
monoidal composition**: blocks form objects, dependency edges form a
preorder relation on those objects, and manuscript composition is the
monoidal product (disjoint union of block sequences) with the empty
manuscript (``EMPTY_MANUSCRIPT``) as identity. What is verified (and
property-tested) are: associativity of composition, the identity law,
and acyclicity/resolvability of the relation. What is NOT claimed: this
is not a topos, not a full categorical structure — no limits, exponentials,
or subobject classifier are defined or verified. The dependency relation
is only a preorder once reflexive/transitive closure is taken; we check
it is well-founded (acyclic) and that named references resolve.

Evidence strength is a linearly ordered tier (``EvidenceTier``); a claim's
support policy declares the minimum tier its supporting evidence must
carry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum


class EvidenceTier(IntEnum):
    """Linearly ordered strength tiers for evidence blocks."""

    WEAK = 1
    MODERATE = 2
    STRONG = 3


class EdgeKind(Enum):
    """Typed dependency edge kinds between blocks."""

    SUPPORTS = "supports"
    RESOLVES = "resolves"
    REFERENCES = "references"
    DEPENDS_ON = "depends_on"


@dataclass(frozen=True)
class MatchPolicy:
    """Declared constraint on what satisfies a dependency edge.

    ``min_tier`` applies to SUPPORTS edges: the target evidence block must
    carry at least this tier. ``require_registered`` applies to RESOLVES
    edges: the target must be a registered definition/theorem statement.
    """

    min_tier: EvidenceTier = EvidenceTier.WEAK
    require_registered: bool = True


@dataclass(frozen=True)
class DependencyEdge:
    """A typed, directed dependency from one block to another."""

    target_id: str
    kind: EdgeKind
    policy: MatchPolicy | None = None


@dataclass(frozen=True)
class Block:
    """Base block: identifier, optional title, declared dependency edges."""

    id: str
    title: str = ""
    edges: tuple[DependencyEdge, ...] = ()


@dataclass(frozen=True)
class Evidence(Block):
    """A piece of supporting evidence with a declared strength tier."""

    tier: EvidenceTier = EvidenceTier.WEAK


@dataclass(frozen=True)
class Claim(Block):
    """A research claim. Its SUPPORTS edges name evidence blocks."""

    statement: str = ""
    evidence: tuple[DependencyEdge, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class FormalStatement(Block):
    """A definition/theorem/lemma/proposition statement.

    ``resolves_to`` names the registered formal identifiers it depends on
    (e.g. a theorem referencing a definition id); each is checked as a
    RESOLVES edge.
    """

    kind: str = "theorem"
    resolves_to: tuple[str, ...] = ()


@dataclass(frozen=True)
class Derivation(Block):
    """A derivation step: premises flow to an optional conclusion."""

    premises: tuple[str, ...] = ()
    conclusion: str | None = None


@dataclass(frozen=True)
class Figure(Block):
    """A figure artifact at a path."""

    path: str = ""


@dataclass(frozen=True)
class Table(Block):
    """A table artifact at a path."""

    path: str = ""


@dataclass(frozen=True)
class Dataset(Block):
    """A dataset artifact at a path with an optional record count."""

    path: str = ""
    records: int | None = None


@dataclass(frozen=True)
class Section(Block):
    """A section containing child block ids in document order."""

    children: tuple[str, ...] = ()


ALL_BLOCK_TYPES = (Claim, Evidence, FormalStatement, Derivation, Figure, Table, Dataset, Section)

__all__ = [
    "ALL_BLOCK_TYPES",
    "Block",
    "Claim",
    "Dataset",
    "DependencyEdge",
    "Derivation",
    "EdgeKind",
    "Evidence",
    "EvidenceTier",
    "Figure",
    "FormalStatement",
    "MatchPolicy",
    "Section",
    "Table",
]
