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


def test_gnn_roundtrip_detects_lossy_payload(project_root: Path) -> None:
    """The GNN round-trip must FAIL on an unrepresentable field (not be a dict==itself tautology)."""
    from roadmap_tracks.formal_interop import _gnn_paths, _model_payload, roundtrip_payload_lossless

    paths = _gnn_paths(project_root)
    assert paths, "expected at least one .gnn.md file"
    payload = _model_payload(paths[0])
    # Clean real payload round-trips losslessly through GNN text.
    assert roundtrip_payload_lossless(payload) is True
    # A connection label with whitespace cannot survive the `\\w+` edge grammar:
    # serializing and re-parsing must report a loss, proving the gate is not vacuous.
    assert payload["connections"], "expected connections in the toy model"
    corrupted = {**payload, "connections": [dict(payload["connections"][0]), *payload["connections"][1:]]}
    corrupted["connections"][0]["label"] = "bad label"
    assert roundtrip_payload_lossless(corrupted) is False
