"""Tests for knowledge_graph.schema module.

Verifies namespace URIs, assertion types, hypothesis categories, and
subfield URIs are well-formed and contain the expected entries.
"""

from __future__ import annotations

import knowledge_graph.schema as schema
from knowledge_graph.schema import (
    AIF_NAMESPACE,
    ASSERTION_TYPES,
    SUBFIELD_URIS,
)


class TestAIFNamespace:
    """Validate the base namespace URI."""

    def test_namespace_is_string(self) -> None:
        """AIF_NAMESPACE should be a plain string."""
        assert isinstance(AIF_NAMESPACE, str)

    def test_namespace_ends_with_slash(self) -> None:
        """URI namespaces should end with a trailing slash."""
        assert AIF_NAMESPACE.endswith("/")

    def test_namespace_starts_with_http(self) -> None:
        """URI should use the http scheme."""
        assert AIF_NAMESPACE.startswith("http://")


class TestAssertionTypes:
    """Validate the five core assertion type predicates."""

    def test_has_five_entries(self) -> None:
        """ASSERTION_TYPES must contain exactly 5 predicate keys."""
        assert len(ASSERTION_TYPES) == 5

    def test_expected_keys(self) -> None:
        """The five required predicate names must be present."""
        expected = {"asserts", "cites", "belongsTo", "supports", "contradicts"}
        assert set(ASSERTION_TYPES.keys()) == expected

    def test_values_are_well_formed_uris(self) -> None:
        """Each predicate URI must start with the base namespace."""
        for key, uri in ASSERTION_TYPES.items():
            assert uri.startswith(AIF_NAMESPACE), f"{key}: {uri}"

    def test_values_are_unique(self) -> None:
        """No two predicates should share the same URI."""
        uris = list(ASSERTION_TYPES.values())
        assert len(uris) == len(set(uris))


class TestHypothesisCategories:
    """Validate the eight standard hypothesis category URIs."""

    def test_has_eight_entries(self) -> None:
        """schema.HYPOTHESIS_CATEGORIES must contain exactly 8 entries."""
        assert len(schema.HYPOTHESIS_CATEGORIES) == 8

    def test_expected_keys(self) -> None:
        """All eight hypothesis keys must be present."""
        expected = {
            "PRIMARY_EFFICACY",
            "OPTIMAL_PERFORMANCE",
            "MECHANISTIC_BASIS",
            "PROCESS_MODEL",
            "SCALABILITY",
            "CLINICAL_UTILITY",
            "BIOLOGICAL_BASIS",
            "DOMAIN_GENERALIZATION",
        }
        assert set(schema.HYPOTHESIS_CATEGORIES.keys()) == expected

    def test_values_are_well_formed_uris(self) -> None:
        """Each hypothesis URI must start with the base namespace."""
        for key, uri in schema.HYPOTHESIS_CATEGORIES.items():
            assert uri.startswith(AIF_NAMESPACE), f"{key}: {uri}"
            assert "/hypothesis/" in uri, f"{key} URI missing /hypothesis/ segment"

    def test_values_are_unique(self) -> None:
        """No two hypotheses should share the same URI."""
        uris = list(schema.HYPOTHESIS_CATEGORIES.values())
        assert len(uris) == len(set(uris))


class TestSubfieldURIs:
    """Validate the subfield classification URIs."""

    def test_has_eight_entries(self) -> None:
        """SUBFIELD_URIS must contain exactly 8 entries."""
        assert len(SUBFIELD_URIS) == 8

    def test_expected_keys(self) -> None:
        """All eight domain keys must be present."""
        expected = {
            "A2_philosophy",
            "A1_formal",
            "B_tools",
            "C1_neuroscience",
            "C2_robotics",
            "C3_language",
            "C4_psychiatry",
            "C5_biology",
        }
        assert set(SUBFIELD_URIS.keys()) == expected

    def test_values_are_well_formed_uris(self) -> None:
        """Each subfield URI must start with the base namespace."""
        for key, uri in SUBFIELD_URIS.items():
            assert uri.startswith(AIF_NAMESPACE), f"{key}: {uri}"
            assert "/subfield/" in uri, f"{key} URI missing /subfield/ segment"

    def test_values_are_unique(self) -> None:
        """No two subfields should share the same URI."""
        uris = list(SUBFIELD_URIS.values())
        assert len(uris) == len(set(uris))
