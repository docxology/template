from pathlib import Path

import pytest

from gnn.parser import GNNParseError, parse_gnn_file
from gnn.concordance import concordance_holds, parity_gaps

ROOT = Path(__file__).resolve().parents[1]
TOY = ROOT / "gnn" / "bernoulli_toy.gnn.md"


def test_parse_bernoulli_toy() -> None:
    model = parse_gnn_file(TOY)
    assert model.has("J")
    assert model.ontology["J"] == "CrossStreamCouplingPotential"


def test_concordance_holds_for_toy() -> None:
    model = parse_gnn_file(TOY)
    assert concordance_holds(model)


def test_missing_section_raises() -> None:
    from gnn.parser import parse_gnn

    with pytest.raises(GNNParseError):
        parse_gnn("## GNNSection\nonly\n")


def test_parity_gaps_when_ontology_incomplete() -> None:
    from dataclasses import replace

    model = parse_gnn_file(TOY)
    broken = replace(model, ontology={k: v for k, v in model.ontology.items() if k != "J"})
    gaps = parity_gaps(broken)
    assert any("J" in g for g in gaps)
