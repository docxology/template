"""Fail-closed composition and checking tests, with negative controls."""

from __future__ import annotations

import pytest

from infrastructure.formal_contracts.checker import (
    EMPTY_MANUSCRIPT,
    CompositionError,
    check_manuscript,
    compose,
    compose_manuscripts,
)
from infrastructure.formal_contracts.diagnostics import FormalCode
from infrastructure.formal_contracts.model import (
    Claim,
    DependencyEdge,
    EdgeKind,
    Evidence,
    EvidenceTier,
    FormalStatement,
    MatchPolicy,
    Section,
)


def valid_blocks() -> list[object]:
    return [
        Section(id="sec:main", children=("claim:1", "ev:1", "def:1")),
        FormalStatement(id="def:1", kind="definition"),
        Evidence(id="ev:1", tier=EvidenceTier.STRONG),
        Claim(
            id="claim:1",
            statement="X holds",
            evidence=(
                DependencyEdge(
                    target_id="ev:1",
                    kind=EdgeKind.SUPPORTS,
                    policy=MatchPolicy(min_tier=EvidenceTier.STRONG),
                ),
            ),
        ),
    ]


def test_valid_manuscript_passes() -> None:
    ms = compose(valid_blocks())
    report = check_manuscript(ms)
    assert report.ok, [d.message for d in report.diagnostics]
    assert report.diagnostics == ()


def test_unsupported_claim_fails_with_specific_code() -> None:
    ms = compose([Section(id="s", children=("c",)), Claim(id="c")])
    report = check_manuscript(ms)
    assert not report.ok
    assert report.has(FormalCode.UNSUPPORTED_CLAIM)


def test_insufficient_tier_fails_with_specific_code() -> None:
    ms = compose(
        [
            Section(id="s", children=("c", "e")),
            Evidence(id="e", tier=EvidenceTier.WEAK),
            Claim(
                id="c",
                evidence=(
                    DependencyEdge(
                        target_id="e",
                        kind=EdgeKind.SUPPORTS,
                        policy=MatchPolicy(min_tier=EvidenceTier.STRONG),
                    ),
                ),
            ),
        ]
    )
    report = check_manuscript(ms)
    assert report.has(FormalCode.INSUFFICIENT_TIER)
    assert "STRONG" in next(d.message for d in report.diagnostics if d.code == FormalCode.INSUFFICIENT_TIER)


def test_dangling_formal_ref_fails_in_compose() -> None:
    with pytest.raises(CompositionError) as excinfo:
        compose(
            [
                Section(id="s", children=("t",)),
                FormalStatement(id="t", resolves_to=("def:missing",)),
            ]
        )
    assert any(d.code == FormalCode.DANGLING_REF for d in excinfo.value.diagnostics)


def test_check_manuscript_flags_unresolved_formal_statement() -> None:
    """Defense in depth: a hand-built Manuscript with a dangling resolve
    (bypassing compose) still fails check_manuscript with DANGLING_REF."""
    from infrastructure.formal_contracts.checker import Manuscript
    from infrastructure.formal_contracts.model import Section

    statement = FormalStatement(id="t", resolves_to=("def:missing",))
    section = Section(id="s", children=("t",))
    ms = Manuscript(blocks=(section, statement), index={section.id: section, statement.id: statement})
    report = check_manuscript(ms)
    assert report.has(FormalCode.DANGLING_REF)


def test_resolve_to_non_statement_fails_in_compose() -> None:
    with pytest.raises(CompositionError) as excinfo:
        compose(
            [
                Section(id="s", children=("t", "e")),
                FormalStatement(id="t", resolves_to=("e",)),
                Evidence(id="e"),
            ]
        )
    assert any(d.code == FormalCode.DANGLING_REF for d in excinfo.value.diagnostics)


def test_duplicate_id_fails_with_specific_code() -> None:
    with pytest.raises(CompositionError) as excinfo:
        compose([Claim(id="x"), Evidence(id="x")])
    assert any(d.code == FormalCode.DUPLICATE_ID for d in excinfo.value.diagnostics)


def test_dangling_edge_fails_with_specific_code() -> None:
    with pytest.raises(CompositionError) as excinfo:
        compose(
            [
                Section(id="s", children=("c",)),
                Claim(id="c", edges=(DependencyEdge("missing", EdgeKind.SUPPORTS),)),
            ]
        )
    assert any(d.code == FormalCode.DANGLING_EDGE for d in excinfo.value.diagnostics)


def test_missing_section_child_fails_with_specific_code() -> None:
    with pytest.raises(CompositionError) as excinfo:
        compose([Section(id="s", children=("ghost",))])
    assert any(d.code == FormalCode.SECTION_CHILD_MISSING for d in excinfo.value.diagnostics)


def test_cycle_fails_with_actual_path() -> None:
    blocks = [
        Claim(id="a", edges=(DependencyEdge("b", EdgeKind.DEPENDS_ON),)),
        Claim(id="b", edges=(DependencyEdge("a", EdgeKind.DEPENDS_ON),)),
    ]
    with pytest.raises(CompositionError) as excinfo:
        compose(blocks)
    assert any(d.code == FormalCode.CYCLE_DETECTED for d in excinfo.value.diagnostics)
    diag = next(d for d in excinfo.value.diagnostics if d.code == FormalCode.CYCLE_DETECTED)
    assert "a -> b -> a" in diag.message


def test_orphan_block_fails_with_specific_code() -> None:
    ms = compose(
        [
            Section(id="s"),
            Claim(id="lonely", edges=(DependencyEdge("s", EdgeKind.REFERENCES),)),
        ]
    )
    report = check_manuscript(ms)
    assert report.has(FormalCode.ORPHAN_BLOCK)


def test_chain_from_section_is_reachable() -> None:
    ms = compose(
        [
            Section(id="s", children=("c",)),
            Claim(id="c", evidence=(DependencyEdge("e", EdgeKind.SUPPORTS),)),
            Evidence(id="e"),
        ]
    )
    assert check_manuscript(ms).ok


def test_non_block_type_rejected() -> None:
    with pytest.raises(CompositionError) as excinfo:
        compose(["not-a-block"])  # type: ignore[list-item]
    assert any(d.code == FormalCode.READER_PARSE for d in excinfo.value.diagnostics)
    assert excinfo.value.diagnostics[0].block_id is None


def test_composition_error_message_truncates() -> None:
    blocks = [Claim(id=f"c{i}", edges=(DependencyEdge(f"missing{i}", EdgeKind.SUPPORTS),)) for i in range(8)]
    blocks.append(Section(id="s"))
    with pytest.raises(CompositionError) as excinfo:
        compose(blocks)
    assert "+3 more" in str(excinfo.value)


def test_monoid_identity_and_associativity() -> None:
    a = compose([Section(id="s1", children=("c1",)), Claim(id="c1")])
    b = compose([Section(id="s2", children=("e1",)), Evidence(id="e1")])
    c = compose([Section(id="s3")])
    assert compose_manuscripts(EMPTY_MANUSCRIPT, a).blocks == a.blocks
    assert compose_manuscripts(a, EMPTY_MANUSCRIPT).blocks == a.blocks
    left = compose_manuscripts(compose_manuscripts(a, b), c).blocks
    right = compose_manuscripts(a, compose_manuscripts(b, c)).blocks
    assert left == right


def test_empty_manuscript_check_is_clean() -> None:
    assert check_manuscript(EMPTY_MANUSCRIPT).ok


def test_manuscript_diagnostics_method() -> None:
    ms = compose(valid_blocks())
    assert ms.diagnostics() == ()
