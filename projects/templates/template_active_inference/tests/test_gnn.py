"""Tests for the GNN parser, model, and concordance modules.

No mocks — uses real .gnn.md files and injected minimal GNN strings.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from gnn.concordance import BERNOULLI_EXPECTED_TERMS, BERNOULLI_SYMBOL_MAP, concordance_holds, parity_gaps
from gnn.model import GnnModel, GnnVariable
from gnn.parser import GNNParseError, parse_gnn, parse_gnn_file

ROOT = Path(__file__).resolve().parents[1]
TOY = ROOT / "gnn" / "bernoulli_toy.gnn.md"

# Minimal valid GNN document used by several tests.
_MINIMAL_GNN = """\
## GNNSection
test

## GNNVersionAndFlags
v1

## ModelName
TestModel

## StateSpaceBlock
x[2, type=float] # a variable

## Connections
x > x:self
"""


def test_parse_bernoulli_toy() -> None:
    model = parse_gnn_file(TOY)
    assert model.has("J")
    assert model.ontology["J"] == "CrossStreamCouplingPotential"


def test_concordance_holds_for_toy() -> None:
    model = parse_gnn_file(TOY)
    assert concordance_holds(model)


def test_missing_section_raises() -> None:
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


# ---- Additional coverage tests ----


def test_parse_gnn_minimal_valid() -> None:
    """The minimal valid GNN document must parse without raising."""
    model = parse_gnn(_MINIMAL_GNN)
    assert model.name == "TestModel"
    assert model.has("x")


def test_parse_gnn_variable_size_mismatch_raises() -> None:
    """A variable whose InitialParameterization size differs from declared dimensions must raise."""
    bad = _MINIMAL_GNN + "\n## InitialParameterization\nx = {1.0, 2.0, 3.0}\n"
    with pytest.raises(GNNParseError, match="size mismatch"):
        parse_gnn(bad)


def test_parse_gnn_malformed_state_space_raises() -> None:
    """A StateSpaceBlock with a broken declaration must raise GNNParseError."""
    bad = """
## GNNSection
s
## GNNVersionAndFlags
v1
## ModelName
M
## StateSpaceBlock
bad_no_brackets_here
## Connections
x > x
"""
    with pytest.raises(GNNParseError, match="malformed StateSpaceBlock"):
        parse_gnn(bad)


def test_parse_gnn_variable_missing_type_raises() -> None:
    """A variable without 'type=' must raise GNNParseError."""
    bad = """
## GNNSection
s
## GNNVersionAndFlags
v1
## ModelName
M
## StateSpaceBlock
x[2]
## Connections
x > x
"""
    with pytest.raises(GNNParseError, match="missing required 'type='"):
        parse_gnn(bad)


def test_parse_gnn_variable_no_dims_raises() -> None:
    """A variable with type= but no integer dimensions must raise."""
    bad = """
## GNNSection
s
## GNNVersionAndFlags
v1
## ModelName
M
## StateSpaceBlock
x[type=float]
## Connections
x > x
"""
    with pytest.raises(GNNParseError, match="no integer dimensions"):
        parse_gnn(bad)


def test_parse_gnn_malformed_connection_raises() -> None:
    """A Connections block with a broken edge syntax must raise GNNParseError."""
    bad = """
## GNNSection
s
## GNNVersionAndFlags
v1
## ModelName
M
## StateSpaceBlock
x[2, type=float]
## Connections
x ??? y
"""
    with pytest.raises(GNNParseError, match="malformed connection"):
        parse_gnn(bad)


def test_gnn_model_variable_raises_key_error() -> None:
    """GnnModel.variable() must raise KeyError for an undeclared variable name."""
    model = GnnModel(section="s", version="v1", name="M")
    with pytest.raises(KeyError, match="no variable"):
        model.variable("undefined")


def test_gnn_model_variable_returns_spec_for_declared_name() -> None:
    """GnnModel.variable() must return the GnnVariable for a declared name."""
    var = GnnVariable(name="q", dims=(2,), dtype="float")
    model = GnnModel(section="s", version="v1", name="M", variables={"q": var})
    assert model.variable("q") is var


def test_gnn_model_has_returns_correct_bool() -> None:
    var = GnnVariable(name="q", dims=(2,), dtype="float")
    model = GnnModel(section="s", version="v1", name="M", variables={"q": var})
    assert model.has("q") is True
    assert model.has("missing") is False


def test_gnn_variable_size_product() -> None:
    """GnnVariable.size must return the product of all dims."""
    var = GnnVariable(name="A", dims=(2, 3), dtype="float")
    assert var.size == 6


def test_parity_gaps_detects_undeclared_variable() -> None:
    """parity_gaps must report a gap when a mapped symbol is not declared in the model."""
    model = parse_gnn_file(TOY)
    # Inject a symbol map that points to a non-existent variable.
    extra_map = dict(BERNOULLI_SYMBOL_MAP)
    extra_map["nonexistent_symbol"] = "totally_missing_variable"
    gaps = parity_gaps(model, symbol_map=extra_map)
    assert any("totally_missing_variable" in g for g in gaps)


def test_parity_gaps_detects_wrong_ontology_term() -> None:
    """parity_gaps must report a gap when the ontology term is wrong."""
    model = parse_gnn_file(TOY)
    # Corrupt the expected terms so J should be "WrongTerm".
    wrong_expected = dict(BERNOULLI_EXPECTED_TERMS)
    wrong_expected["J"] = "WrongOntologyTerm"
    gaps = parity_gaps(model, expected_terms=wrong_expected)
    assert any("J" in g for g in gaps)


def test_concordance_holds_false_with_wrong_terms() -> None:
    """concordance_holds must return False when the expected term is wrong."""
    model = parse_gnn_file(TOY)
    wrong_expected = dict(BERNOULLI_EXPECTED_TERMS)
    wrong_expected["J"] = "WrongOntologyTerm"
    assert concordance_holds(model, expected_terms=wrong_expected) is False


def test_gnn_connection_undirected() -> None:
    """A '-' edge must produce directed=False."""
    text = """
## GNNSection
s
## GNNVersionAndFlags
v1
## ModelName
M
## StateSpaceBlock
x[2, type=float]
y[2, type=float]
## Connections
x - y
"""
    model = parse_gnn(text)
    conn = model.connections[0]
    assert conn.directed is False
    assert conn.source == "x"
    assert conn.target == "y"


def test_parse_gnn_param_block_nested_braces() -> None:
    """A nested-brace InitialParameterization block must parse correctly."""
    text = """
## GNNSection
s
## GNNVersionAndFlags
v1
## ModelName
M
## StateSpaceBlock
A[2, 2, type=float]
## Connections
A > A
## InitialParameterization
A = {{0.9, 0.1}, {0.1, 0.9}}
"""
    model = parse_gnn(text)
    assert model.has("A")
    assert model.variables["A"].value is not None
    assert model.variables["A"].value.shape == (2, 2)


def test_parse_gnn_extra_kv_annotation_is_ignored() -> None:
    """Extra key=value tokens (besides type=) in a variable declaration must be ignored."""
    text = """
## GNNSection
s
## GNNVersionAndFlags
v1
## ModelName
M
## StateSpaceBlock
x[2, type=float, label=myvar]
## Connections
x > x
"""
    model = parse_gnn(text)
    assert model.has("x")
    assert model.variables["x"].dtype == "float"


def test_parse_gnn_unsupported_dimension_token_raises() -> None:
    """A non-integer, non-kv token inside a variable bracket must raise GNNParseError."""
    text = """
## GNNSection
s
## GNNVersionAndFlags
v1
## ModelName
M
## StateSpaceBlock
x[abc, type=float]
## Connections
x > x
"""
    with pytest.raises(GNNParseError, match="unsupported dimension token"):
        parse_gnn(text)


def test_parse_gnn_empty_body_token_skipped() -> None:
    """Trailing comma in body (empty token after split) must not raise."""
    text = """
## GNNSection
s
## GNNVersionAndFlags
v1
## ModelName
M
## StateSpaceBlock
x[2, , type=float]
## Connections
x > x
"""
    model = parse_gnn(text)
    assert model.has("x")  # empty token is skipped silently
