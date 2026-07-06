"""Tests for the primitives registry (collect_primitives)."""
from __future__ import annotations


from src.primitives import collect_primitives, PrimitiveSpec
from src.grammar import KNOWN_DOMAINS


def test_collect_primitives_returns_dict():
    prims = collect_primitives()
    assert isinstance(prims, dict)


def test_collect_primitives_has_all_domains():
    prims = collect_primitives()
    for domain in KNOWN_DOMAINS:
        assert domain in prims, f"Missing domain: {domain}"


def test_collect_primitives_values_are_tuples():
    prims = collect_primitives()
    for domain, specs in prims.items():
        assert isinstance(specs, tuple), f"Domain {domain}: expected tuple"


def test_collect_primitives_all_are_primitive_specs():
    prims = collect_primitives()
    for domain, specs in prims.items():
        for spec in specs:
            assert isinstance(spec, PrimitiveSpec), f"Not a PrimitiveSpec: {spec}"


def test_collect_primitives_each_domain_non_empty():
    prims = collect_primitives()
    for domain in KNOWN_DOMAINS:
        assert len(prims[domain]) >= 1, f"Domain {domain} has no primitives"


def test_collect_primitives_domain_matches_spec():
    prims = collect_primitives()
    for domain, specs in prims.items():
        for spec in specs:
            assert spec.domain == domain, f"Spec domain mismatch: {spec.name}"


def test_collect_primitives_all_have_callable_fn():
    prims = collect_primitives()
    for domain, specs in prims.items():
        for spec in specs:
            assert callable(spec.fn), f"{spec.name}.fn is not callable"


def test_collect_primitives_all_have_example_input():
    prims = collect_primitives()
    for domain, specs in prims.items():
        for spec in specs:
            assert spec.example_input is not None, f"{spec.name} has no example_input"


def test_collect_primitives_expected_modules():
    prims = collect_primitives()
    expected_domains = {"optimization", "dynamics", "statistics", "signal", "graph"}
    assert set(prims.keys()) == expected_domains


def test_total_primitive_count():
    prims = collect_primitives()
    total = sum(len(v) for v in prims.values())
    # optimization: 2, dynamics: 1, statistics: 1, signal: 2, graph: 2 = 8
    assert total == 8
