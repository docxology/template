"""Composition and fail-closed checking of typed manuscripts.

``compose(blocks)`` builds a ``Manuscript`` (the monoidal product of the
block sequence) after validating: unique ids, resolvable edges and section
children, acyclicity (with the actual cycle path in the diagnostic), and
resolvable formal references. ``check_manuscript`` then enforces the
fail-closed contract rules on the composed manuscript: every claim bound
to at least one evidence block of sufficient tier, every formal statement
resolved, and no orphan blocks.

Diagnostics carry stable dotted codes from
``infrastructure.formal_contracts.diagnostics.FormalCode``.
"""

from __future__ import annotations

from dataclasses import dataclass

from infrastructure.formal_contracts.diagnostics import FormalCode
from infrastructure.formal_contracts.model import (
    ALL_BLOCK_TYPES,
    Block,
    Claim,
    DependencyEdge,
    EdgeKind,
    Evidence,
    EvidenceTier,
    Derivation,
    FormalStatement,
    Section,
)


@dataclass(frozen=True)
class Diagnostic:
    """One machine-checkable finding with a stable dotted code."""

    code: str
    message: str
    block_id: str | None = None


class CompositionError(ValueError):
    """Raised by ``compose`` when the block graph is not well-formed."""

    def __init__(self, diagnostics: tuple[Diagnostic, ...]) -> None:
        self.diagnostics = diagnostics
        shown = "; ".join(f"{d.code}: {d.message}" for d in diagnostics[:5])
        extra = "" if len(diagnostics) <= 5 else f" (+{len(diagnostics) - 5} more)"
        super().__init__(shown + extra)


@dataclass(frozen=True)
class Report:
    """Result of ``check_manuscript``: fail-closed validity plus findings."""

    ok: bool
    diagnostics: tuple[Diagnostic, ...] = ()

    def has(self, code: str) -> bool:
        """Return True if any diagnostic carries ``code``."""
        return any(d.code == code for d in self.diagnostics)


@dataclass(frozen=True)
class Manuscript:
    """A composed manuscript: the ordered block sequence plus an index."""

    blocks: tuple[Block, ...]
    index: dict[str, Block]

    def diagnostics(self) -> tuple[Diagnostic, ...]:
        """Fail-closed check of the whole manuscript contract."""
        return check_manuscript(self).diagnostics


EMPTY_MANUSCRIPT = Manuscript(blocks=(), index={})


def _block_references(block: Block) -> list[tuple[str, str]]:
    """Return (target_id, label) pairs a block points at."""
    refs: list[tuple[str, str]] = [(e.target_id, "edge") for e in block.edges]
    if isinstance(block, Claim):
        refs += [(e.target_id, "evidence") for e in block.evidence]
    if isinstance(block, FormalStatement):
        refs += [(t, "resolves") for t in block.resolves_to]
    if isinstance(block, Section):
        refs += [(c, "section-child") for c in block.children]
    if isinstance(block, Derivation):
        refs += [(p, "premise") for p in block.premises]
        if block.conclusion is not None:
            refs.append((block.conclusion, "conclusion"))
    return refs


def _all_edges(block: Block) -> tuple[DependencyEdge, ...]:
    return tuple(block.edges) + (tuple(block.evidence) if isinstance(block, Claim) else ())


def compose(blocks: tuple[Block, ...] | list[Block]) -> Manuscript:
    """Compose blocks into a Manuscript, validating the graph. Monoidal:
    concatenating block sequences then composing equals composing the
    parts (associativity); the empty sequence is the identity."""
    diagnostics: list[Diagnostic] = []
    index: dict[str, Block] = {}
    for block in blocks:
        if not isinstance(block, ALL_BLOCK_TYPES):
            diagnostics.append(
                Diagnostic(
                    code=FormalCode.READER_PARSE,
                    message=f"unregistered block type {type(block).__name__!r}",
                    block_id=None,
                )
            )
            continue
        if block.id in index:
            diagnostics.append(
                Diagnostic(
                    code=FormalCode.DUPLICATE_ID,
                    message=f"block id {block.id!r} used more than once",
                    block_id=block.id,
                )
            )
        index[block.id] = block

    for block in blocks:
        if not isinstance(block, ALL_BLOCK_TYPES):
            continue
        for target_id, label in _block_references(block):
            if target_id not in index:
                code = (
                    FormalCode.SECTION_CHILD_MISSING
                    if label == "section-child"
                    else FormalCode.DANGLING_REF
                    if label == "resolves"
                    else FormalCode.DANGLING_EDGE
                )
                diagnostics.append(
                    Diagnostic(
                        code=code,
                        message=(f"{type(block).__name__} {block.id!r} references missing {label} {target_id!r}"),
                        block_id=block.id,
                    )
                )
            elif label == "resolves" and not isinstance(index[target_id], FormalStatement):
                diagnostics.append(
                    Diagnostic(
                        code=FormalCode.DANGLING_REF,
                        message=(f"{block.id!r} resolves to {target_id!r}, which is not a registered FormalStatement"),
                        block_id=block.id,
                    )
                )

    if diagnostics:
        raise CompositionError(tuple(diagnostics))

    block_tuple = tuple(blocks)
    _check_acyclic(block_tuple, index)
    return Manuscript(blocks=block_tuple, index=dict(index))


def _check_acyclic(blocks: tuple[Block, ...], index: dict[str, Block]) -> None:
    """Raise CompositionError with the cycle path if the graph is cyclic."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {b.id: WHITE for b in blocks}
    path: list[str] = []

    def visit(node_id: str) -> None:
        if color.get(node_id, BLACK) == BLACK:
            return
        if color[node_id] == GRAY:
            cycle_start = path.index(node_id)
            cycle = path[cycle_start:] + [node_id]
            raise CompositionError(
                (
                    Diagnostic(
                        code=FormalCode.CYCLE_DETECTED,
                        message="dependency cycle: " + " -> ".join(cycle),
                        block_id=node_id,
                    ),
                )
            )
        color[node_id] = GRAY
        path.append(node_id)
        for target_id, _ in _block_references(index[node_id]):
            if target_id in color:
                visit(target_id)
        path.pop()
        color[node_id] = BLACK

    for block in blocks:
        visit(block.id)


def compose_manuscripts(*parts: Manuscript) -> Manuscript:
    """Monoidal composition: disjoint union of block sequences, revalidated."""
    return compose([b for part in parts for b in part.blocks])


def check_manuscript(manuscript: Manuscript) -> Report:
    """Fail-closed contract check of a composed manuscript."""
    diagnostics: list[Diagnostic] = []
    index = manuscript.index

    for block in manuscript.blocks:
        if isinstance(block, Claim):
            _check_claim(block, index, diagnostics)
        if isinstance(block, FormalStatement):
            _check_formal_statement(block, index, diagnostics)

    diagnostics.extend(_find_orphans(manuscript))
    return Report(ok=not diagnostics, diagnostics=tuple(diagnostics))


def _check_claim(claim: Claim, index: dict[str, Block], diagnostics: list[Diagnostic]) -> None:
    supporting: list[Evidence] = []
    for edge in claim.evidence + claim.edges:
        if edge.kind is not EdgeKind.SUPPORTS:
            continue
        target = index.get(edge.target_id)
        if isinstance(target, Evidence):
            supporting.append(target)
            policy = edge.policy
            min_tier = policy.min_tier if policy is not None else EvidenceTier.WEAK
            if target.tier < min_tier:
                diagnostics.append(
                    Diagnostic(
                        code=FormalCode.INSUFFICIENT_TIER,
                        message=(
                            f"claim {claim.id!r} requires evidence tier >= "
                            f"{min_tier.name}, {target.id!r} is {target.tier.name}"
                        ),
                        block_id=claim.id,
                    )
                )
    if not supporting:
        diagnostics.append(
            Diagnostic(
                code=FormalCode.UNSUPPORTED_CLAIM,
                message=f"claim {claim.id!r} has no supporting evidence",
                block_id=claim.id,
            )
        )


def _check_formal_statement(
    statement: FormalStatement,
    index: dict[str, Block],
    diagnostics: list[Diagnostic],
) -> None:
    for target_id in statement.resolves_to:
        target = index.get(target_id)
        if not isinstance(target, FormalStatement):
            diagnostics.append(
                Diagnostic(
                    code=FormalCode.DANGLING_REF,
                    message=(
                        f"formal statement {statement.id!r} does not resolve to a registered statement: {target_id!r}"
                    ),
                    block_id=statement.id,
                )
            )


def _find_orphans(manuscript: Manuscript) -> list[Diagnostic]:
    """Blocks unreachable from any section via containment or edges."""
    index = manuscript.index
    forward: dict[str, set[str]] = {bid: set() for bid in index}
    for block in manuscript.blocks:
        for target_id, _ in _block_references(block):
            if target_id in forward:
                forward[block.id].add(target_id)

    reachable: set[str] = set()
    stack = [b.id for b in manuscript.blocks if isinstance(b, Section)]
    while stack:
        node = stack.pop()
        if node in reachable:
            continue
        reachable.add(node)
        stack.extend(sorted(forward[node]))

    return [
        Diagnostic(
            code=FormalCode.ORPHAN_BLOCK,
            message=f"block {block.id!r} is not reachable from any section",
            block_id=block.id,
        )
        for block in manuscript.blocks
        if block.id not in reachable
    ]


__all__ = [
    "CompositionError",
    "Diagnostic",
    "EMPTY_MANUSCRIPT",
    "Manuscript",
    "Report",
    "check_manuscript",
    "compose",
    "compose_manuscripts",
]
