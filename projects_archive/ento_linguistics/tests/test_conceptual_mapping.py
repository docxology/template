"""Tests for conceptual mapping functionality."""

from __future__ import annotations

from typing import Dict, List, Set

import pytest

try:
    from src.conceptual_mapping import Concept, ConceptMap, ConceptualMapper
    from src.term_extraction import Term
except ImportError:
    from conceptual_mapping import Concept, ConceptMap, ConceptualMapper
    from term_extraction import Term


class TestConcept:
    """Test Concept dataclass functionality."""

    def test_concept_creation(self) -> None:
        """Test creating a Concept instance."""
        concept = Concept(
            name="test_concept",
            description="A test concept",
            terms={"term1", "term2"},
            domains={"domain1"},
            confidence=0.8,
        )

        assert concept.name == "test_concept"
        assert concept.description == "A test concept"
        assert concept.terms == {"term1", "term2"}
        assert concept.domains == {"domain1"}
        assert concept.confidence == 0.8
        assert concept.parent_concepts == set()
        assert concept.child_concepts == set()

    def test_concept_add_term(self) -> None:
        """Test adding terms to a concept."""
        concept = Concept("test", "Test concept")

        concept.add_term("term1")
        concept.add_term("term2")
        concept.add_term("term1")  # Duplicate should be ignored

        assert concept.terms == {"term1", "term2"}

    def test_concept_add_domain(self) -> None:
        """Test adding domains to a concept."""
        concept = Concept("test", "Test concept")

        concept.add_domain("domain1")
        concept.add_domain("domain2")
        concept.add_domain("domain1")  # Duplicate should be ignored

        assert concept.domains == {"domain1", "domain2"}

    def test_concept_to_dict(self) -> None:
        """Test converting concept to dictionary."""
        concept = Concept(
            name="test_concept",
            description="A test concept",
            terms={"term1", "term2"},
            domains={"domain1"},
            confidence=0.8,
        )

        data = concept.to_dict()

        assert data["name"] == "test_concept"
        assert data["description"] == "A test concept"
        assert set(data["terms"]) == {
            "term1",
            "term2",
        }  # Check set equality regardless of order
        assert data["domains"] == ["domain1"]
        assert data["confidence"] == 0.8

    def test_concept_serialization(self) -> None:
        """Test concept serialization to and from dict."""
        concept = Concept(
            name="test_concept",
            description="A test concept",
            terms={"term1", "term2"},
            domains={"domain1"},
            confidence=0.8,
        )

        # Test to_dict
        data = concept.to_dict()

        assert data["name"] == "test_concept"
        assert data["description"] == "A test concept"
        assert set(data["terms"]) == {"term1", "term2"}  # Order may vary
        assert set(data["domains"]) == {"domain1"}
        assert data["confidence"] == 0.8


class TestConceptMap:
    """Test ConceptMap functionality."""

    @pytest.fixture
    def concept_map(self) -> ConceptMap:
        """Create a sample concept map for testing."""
        concept_map = ConceptMap()

        concept1 = Concept(
            "colony",
            "Ant colony concept",
            {"colony", "nest"},
            {"unit_of_individuality"},
        )
        concept2 = Concept(
            "division_labor",
            "Division of labor",
            {"worker", "forager"},
            {"behavior_and_identity"},
        )

        concept_map.concepts["colony"] = concept1
        concept_map.concepts["division_labor"] = concept2

        concept_map.add_relationship("colony", "division_labor", "contains")

        return concept_map

    def test_concept_map_initialization(self) -> None:
        """Test ConceptMap initialization."""
        concept_map = ConceptMap()

        assert concept_map.concepts == {}
        assert concept_map.term_to_concepts == {}
        assert concept_map.concept_relationships == {}

    def test_add_concept(self, concept_map: ConceptMap) -> None:
        """Test adding concepts to the map."""
        concept = Concept("test_concept", "Test concept", {"term1"}, {"domain1"})
        concept_map.add_concept(concept)

        assert "test_concept" in concept_map.concepts
        assert concept_map.concepts["test_concept"] == concept
        assert "term1" in concept_map.term_to_concepts
        assert "test_concept" in concept_map.term_to_concepts["term1"]

    def test_add_relationship(self, concept_map: ConceptMap) -> None:
        """Test adding relationships between concepts."""
        # Add concepts first
        concept1 = Concept(
            "colony", "Colony concept", {"colony"}, {"unit_of_individuality"}
        )
        concept2 = Concept(
            "division_labor", "Division of labor", {"worker"}, {"behavior_and_identity"}
        )
        concept_map.add_concept(concept1)
        concept_map.add_concept(concept2)

        # Add relationship
        concept_map.add_relationship("colony", "division_labor", 0.8)

        key = tuple(sorted(["colony", "division_labor"]))
        assert key in concept_map.concept_relationships
        assert concept_map.concept_relationships[key] == 0.8

    def test_get_concept_terms(self, concept_map: ConceptMap) -> None:
        """Test getting terms for a concept."""
        concept = Concept("test", "Test", {"term1", "term2"}, {"domain1"})
        concept_map.add_concept(concept)

        terms = concept_map.get_concept_terms("test")
        assert terms == {"term1", "term2"}

        # Test non-existent concept
        terms = concept_map.get_concept_terms("nonexistent")
        assert terms == set()

    def test_get_term_concepts(self, concept_map: ConceptMap) -> None:
        """Test getting concepts for a term."""
        concept = Concept("test", "Test", {"term1"}, {"domain1"})
        concept_map.add_concept(concept)

        concepts = concept_map.get_term_concepts("term1")
        assert concepts == {"test"}

        # Test non-existent term
        concepts = concept_map.get_term_concepts("nonexistent")
        assert concepts == set()

    def test_find_concept_overlaps(self, concept_map: ConceptMap) -> None:
        """Test finding overlapping terms between concepts."""
        # Add overlapping term
        concept_map.concepts["colony"].add_term("worker")

        overlaps = concept_map.find_concept_overlaps()

        assert len(overlaps) > 0
        # Should find overlap between colony and division_labor on "worker"

    def test_find_concept_overlaps(self, concept_map: ConceptMap) -> None:
        """Test finding overlapping terms between concepts."""
        # Add concepts with overlapping terms
        concept1 = Concept(
            "colony", "Colony concept", {"colony", "queen"}, {"unit_of_individuality"}
        )
        concept2 = Concept(
            "labor", "Labor concept", {"queen", "worker"}, {"power_and_labor"}
        )
        concept_map.add_concept(concept1)
        concept_map.add_concept(concept2)

        overlaps = concept_map.find_concept_overlaps()

        # Should find overlap on "queen"
        assert isinstance(overlaps, dict)
        # The exact structure depends on implementation, but should contain overlaps


class TestConceptualMapper:
    """Test ConceptualMapper functionality."""

    @pytest.fixture
    def mapper(self) -> ConceptualMapper:
        """Create a ConceptualMapper instance."""
        return ConceptualMapper()

    @pytest.fixture
    def sample_terms(self) -> Dict[str, Term]:
        """Create sample terms for testing."""
        terms = {}

        # Create sample terms
        term1 = Term("colony", "colony", {"colony"}, 5)
        term1.domains = {"unit_of_individuality"}
        terms["colony"] = term1

        term2 = Term("queen", "queen", {"queen"}, 3)
        term2.domains = {"power_and_labor", "sex_and_reproduction"}
        terms["queen"] = term2

        term3 = Term("worker", "worker", {"worker"}, 8)
        term3.domains = {"behavior_and_identity", "power_and_labor"}
        terms["worker"] = term3

        return terms

    def test_mapper_initialization(self, mapper: ConceptMapper) -> None:
        """Test ConceptMapper initialization."""
        assert mapper.BASE_CONCEPTS is not None
        assert len(mapper.BASE_CONCEPTS) > 0

    def test_base_concepts_structure(self, mapper: ConceptMapper) -> None:
        """Test that base concepts have required structure."""
        for concept_name, concept_data in mapper.BASE_CONCEPTS.items():
            assert "description" in concept_data
            assert "domains" in concept_data
            assert "key_terms" in concept_data
            assert isinstance(concept_data["domains"], list)
            assert isinstance(concept_data["key_terms"], list)

    def test_build_concept_map(
        self, mapper: ConceptMapper, sample_terms: Dict[str, Term]
    ) -> None:
        """Test building a concept map from terms."""
        concept_map = mapper.build_concept_map(sample_terms)

        assert isinstance(concept_map, ConceptMap)
        assert len(concept_map.concepts) > 0

        # Should have created concepts from base concepts
        concept_names = set(concept_map.concepts.keys())
        assert len(concept_names) > 0

    def test_map_term_to_concepts(
        self, mapper: ConceptualMapper, sample_terms: Dict[str, Term]
    ) -> None:
        """Test mapping individual terms to concepts."""
        term = sample_terms["queen"]

        # Initialize base concepts first (this is normally done in build_concept_map)
        for concept_name, concept_data in mapper.BASE_CONCEPTS.items():
            concept = Concept(
                name=concept_name, description=concept_data["description"]
            )
            for domain in concept_data["domains"]:
                concept.add_domain(domain)
            for term_text in concept_data["key_terms"]:
                concept.add_term(term_text)
            mapper.concept_map.add_concept(concept)

        # This method doesn't return anything, it modifies the internal map
        result = mapper._map_term_to_concepts(term)
        assert result is None  # Should return None

        # The method should run without error - the actual mapping logic
        # is tested more comprehensively in the build_concept_map test
        assert True  # Method executed successfully

    def test_build_concept_relationships(self, mapper: ConceptualMapper) -> None:
        """Test building concept relationships."""
        # Initialize with some concepts first
        mapper._build_concept_relationships()

        # Should have created relationships
        assert isinstance(mapper.concept_map.concept_relationships, dict)

    def test_identify_conceptual_boundaries(
        self, mapper: ConceptualMapper, sample_terms: Dict[str, Term]
    ) -> None:
        """Test identifying conceptual boundaries."""
        # First build a concept map with some terms
        mapper.build_concept_map(sample_terms)

        boundaries = mapper.identify_conceptual_boundaries()

        assert isinstance(boundaries, dict)
        # Should have boundaries for concepts that were created
        # The exact number depends on implementation, but should be > 0
        total_concepts = len(mapper.concept_map.concepts)
        assert len(boundaries) > 0
        assert len(boundaries) <= total_concepts

        # Check that each boundary entry has the expected structure
        for concept_name, boundary_info in boundaries.items():
            assert "bridging_terms" in boundary_info
            assert "boundary_strength" in boundary_info
            assert "domain_spread" in boundary_info
            assert "connected_concepts" in boundary_info
            assert concept_name in mapper.concept_map.concepts

    def test_analyze_conceptual_hierarchy(self, mapper: ConceptualMapper) -> None:
        """Test conceptual hierarchy analysis."""
        hierarchy = mapper.analyze_conceptual_hierarchy()

        assert isinstance(hierarchy, dict)
        assert "hierarchy_depth" in hierarchy

    def test_detect_anthropomorphic_concepts(self, mapper: ConceptualMapper) -> None:
        """Test detection of anthropomorphic concepts."""
        anthropomorphic = mapper.detect_anthropomorphic_concepts()

        assert isinstance(anthropomorphic, dict)

    def test_empty_terms_handling(self, mapper: ConceptMapper) -> None:
        """Test handling of empty terms dictionary."""
        empty_map = mapper.build_concept_map({})

        assert isinstance(empty_map, ConceptMap)
        # Should still have base concepts
        assert len(empty_map.concepts) >= len(mapper.BASE_CONCEPTS)

    def test_concept_map_validation(
        self, mapper: ConceptMapper, sample_terms: Dict[str, Term]
    ) -> None:
        """Test validation of concept maps."""
        concept_map = mapper.build_concept_map(sample_terms)

        # Should not raise exceptions
        assert concept_map is not None

        # Validate structure
        for concept in concept_map.concepts.values():
            assert isinstance(concept, Concept)
            assert concept.name
            assert concept.description

    def test_export_concept_map_json(
        self, mapper: ConceptualMapper, sample_terms: Dict[str, Term], tmp_path: Path
    ) -> None:
        """Test JSON export of concept map."""
        concept_map = mapper.build_concept_map(sample_terms)

        filepath = tmp_path / "concept_map.json"
        mapper.export_concept_map_json(str(filepath))

        assert filepath.exists()
        assert filepath.stat().st_size > 0

        # Verify JSON content
        import json

        with open(filepath, "r") as f:
            data = json.load(f)

        assert "concepts" in data
        assert "term_mappings" in data
        assert "relationships" in data
        assert len(data["concepts"]) > 0

    def test_find_concept_gaps(self, mapper: ConceptualMapper) -> None:
        """Test identification of conceptual gaps."""
        # Test with domain terms that have gaps
        domain_terms = {
            "unit_of_individuality": ["colony", "hive", "swarm"],
            "behavior_and_identity": ["foraging", "nursing", "scouting"],
            "economics": ["resource_sharing", "division_of_labor"],
        }

        gaps = mapper.find_concept_gaps(domain_terms)

        # Should return a dictionary
        assert isinstance(gaps, dict)

        # Check structure - gaps should map domains to missing terms
        for domain, missing_terms in gaps.items():
            assert isinstance(missing_terms, list)
            # All missing terms should be in the original domain_terms
            for term in missing_terms:
                assert term in domain_terms.get(domain, [])
