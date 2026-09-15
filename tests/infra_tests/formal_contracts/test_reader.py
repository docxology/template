"""Reader tests: markdown formalism conventions -> typed blocks."""

from __future__ import annotations

import pytest

from infrastructure.formal_contracts.checker import check_manuscript, compose
from infrastructure.formal_contracts.model import (
    Claim,
    Dataset,
    Evidence,
    EvidenceTier,
    Figure,
    FormalStatement,
    Section,
    Table,
)
from infrastructure.formal_contracts.reader import ReaderError, read_blocks

FULL_MD = """# Introduction

::: {.definition #def:x}
A thing.
:::

::: {.claim #claim:y tier=strong}
We claim [@ev:e1].
:::

::: {.evidence #ev:e1 tier=strong}
data.
:::

::: {.figure #fig:f path=figures/f.png}
:::

::: {.table #tbl:t path=tables/t.csv}
:::

::: {.dataset #ds:d path=data/d.csv records=10}
:::

::: {.section #sec:appendix title=Appendix}
:::
"""


def test_read_full_document() -> None:
    blocks = read_blocks(FULL_MD)
    by_type: dict[type, list] = {}
    for b in blocks:
        by_type.setdefault(type(b), []).append(b)
    assert len(by_type[Section]) == 2
    assert len(by_type[FormalStatement]) == 1
    assert by_type[FormalStatement][0].kind == "definition"
    assert len(by_type[Claim]) == 1
    assert len(by_type[Evidence]) == 1
    assert by_type[Evidence][0].tier is EvidenceTier.STRONG
    assert by_type[Figure][0].path == "figures/f.png"
    assert by_type[Table][0].path == "tables/t.csv"
    ds = by_type[Dataset][0]
    assert ds.path == "data/d.csv"
    assert ds.records == 10


def test_reader_claim_edges_and_policy() -> None:
    blocks = read_blocks(FULL_MD)
    claim = next(b for b in blocks if isinstance(b, Claim))
    assert claim.evidence[0].target_id == "ev:e1"
    assert claim.evidence[0].policy is not None
    assert claim.evidence[0].policy.min_tier is EvidenceTier.STRONG


def test_reader_output_composes_and_checks() -> None:
    ms = compose(list(read_blocks(FULL_MD)))
    report = check_manuscript(ms)
    assert report.ok, [d.message for d in report.diagnostics]


def test_heading_section_id() -> None:
    blocks = read_blocks("# Results\n\nsome text\n")
    assert blocks[0].id == "sec:results"


def test_section_div_attaches_following_blocks() -> None:
    md = "::: {.section #sec:a}\n:::\n\n::: {.evidence #ev:1}\n:::\n"
    blocks = read_blocks(md)
    assert isinstance(blocks[0], Section)
    assert blocks[0].children == ("ev:1",)


def test_missing_class_raises() -> None:
    with pytest.raises(ReaderError):
        read_blocks("::: {#x}\nbody\n:::\n")


def test_missing_id_raises() -> None:
    with pytest.raises(ReaderError):
        read_blocks("::: {.claim}\nbody\n:::\n")


def test_unknown_tier_on_claim_raises() -> None:
    with pytest.raises(ReaderError):
        read_blocks("::: {.claim #c tier=bogus}\nbody\n:::\n")


def test_unknown_tier_on_evidence_raises() -> None:
    with pytest.raises(ReaderError):
        read_blocks("::: {.evidence #e tier=weakish}\n:::\n")


def test_unsupported_class_raises() -> None:
    with pytest.raises(ReaderError):
        read_blocks("::: {.bananas #b}\n:::\n")


def test_unclosed_div_raises() -> None:
    with pytest.raises(ReaderError):
        read_blocks("::: {.claim #c}\nnever closed\n")


def test_stray_close_is_ignored() -> None:
    blocks = read_blocks(":::\n")
    assert blocks == ()


def test_reader_error_carries_diagnostic() -> None:
    with pytest.raises(ReaderError) as excinfo:
        read_blocks("::: {.claim}\nbody\n:::\n")
    assert excinfo.value.diagnostic.code == "FORMAL.READER_PARSE"


def test_claim_without_tier_defaults_weak_policy() -> None:
    md = "::: {.claim #c}\nsee [@ev:1]\n:::\n"
    claim = read_blocks(md)[0]
    assert claim.evidence[0].policy is not None
    assert claim.evidence[0].policy.min_tier is EvidenceTier.WEAK


def test_blocks_before_any_section_stay_orphans() -> None:
    md = "::: {.evidence #e tier=strong}\n:::\n"
    blocks = read_blocks(md)
    ms = compose(list(blocks))
    report = check_manuscript(ms)
    assert report.has("FORMAL.ORPHAN_BLOCK")
