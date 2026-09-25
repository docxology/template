"""Tests for the typed block model."""

from __future__ import annotations

import dataclasses

import pytest

from infrastructure.formal_contracts.model import (
    ALL_BLOCK_TYPES,
    Block,
    Claim,
    Dataset,
    DependencyEdge,
    Derivation,
    EdgeKind,
    EvidenceTier,
    Figure,
    FormalStatement,
    MatchPolicy,
    Section,
    Table,
)


def test_evidence_tiers_are_linearly_ordered() -> None:
    assert EvidenceTier.WEAK < EvidenceTier.MODERATE < EvidenceTier.STRONG


def test_edge_kinds_are_unique() -> None:
    values = {kind.value for kind in EdgeKind}
    assert len(values) == len(list(EdgeKind))


def test_blocks_are_frozen() -> None:
    claim = Claim(id="c1")
    with pytest.raises(dataclasses.FrozenInstanceError):
        claim.id = "other"  # type: ignore[misc]


def test_match_policy_defaults() -> None:
    policy = MatchPolicy()
    assert policy.min_tier is EvidenceTier.WEAK
    assert policy.require_registered is True


def test_all_block_types_are_block_subclasses() -> None:
    for cls in ALL_BLOCK_TYPES:
        assert issubclass(cls, Block)


def test_block_defaults() -> None:
    edge = DependencyEdge(target_id="t", kind=EdgeKind.SUPPORTS)
    assert edge.policy is None
    assert Figure(id="f").path == ""
    assert Table(id="t").path == ""
    assert Dataset(id="d").records is None
    assert Section(id="s").children == ()
    assert Derivation(id="dv").conclusion is None
    assert FormalStatement(id="fs").kind == "theorem"
