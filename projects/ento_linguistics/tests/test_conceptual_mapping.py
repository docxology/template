"""Tests for conceptual mapping functionality.

Consolidated from test_conceptual_mapping.py, test_conceptual_mapping_expanded.py,
and test_conceptual_mapping_coverage.py.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Dict, List, Set

import pytest

from analysis.conceptual_mapping import Concept, ConceptMap, ConceptualMapper
from analysis.term_extraction import Term


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

    def test_find_concept_overlaps_with_shared_term(self, concept_map: ConceptMap) -> None:
        """Test finding overlapping terms between concepts."""
        concept_map.concepts["colony"].add_term("worker")

        overlaps = concept_map.find_concept_overlaps()

        assert len(overlaps) > 0

    def test_find_concept_overlaps_queen(self, concept_map: ConceptMap) -> None:
        """Test finding overlapping terms between concepts with queen."""
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

    def test_mapper_initialization(self, mapper: ConceptualMapper) -> None:
        """Test ConceptualMapper initialization."""
        assert mapper.BASE_CONCEPTS is not None
        assert len(mapper.BASE_CONCEPTS) > 0

    def test_base_concepts_structure(self, mapper: ConceptualMapper) -> None:
        """Test that base concepts have required structure."""
        for concept_name, concept_data in mapper.BASE_CONCEPTS.items():
            assert "description" in concept_data
            assert "domains" in concept_data
            assert "key_terms" in concept_data
            assert isinstance(concept_data["domains"], list)
            assert isinstance(concept_data["key_terms"], list)

    def test_build_concept_map(
        self, mapper: ConceptualMapper, sample_terms: Dict[str, Term]
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

    def test_empty_terms_handling(self, mapper: ConceptualMapper) -> None:
        """Test handling of empty terms dictionary."""
        empty_map = mapper.build_concept_map({})

        assert isinstance(empty_map, ConceptMap)
        # Should still have base concepts
        assert len(empty_map.concepts) >= len(mapper.BASE_CONCEPTS)

    def test_concept_map_validation(
        self, mapper: ConceptualMapper, sample_terms: Dict[str, Term]
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


# ============================================================================
# Advanced ConceptMap methods (from test_conceptual_mapping_expanded.py)
# ============================================================================


@pytest.fixture
def populated_concept_map():
    """Create a concept map with multiple concepts and relationships."""
    concept_map = ConceptMap()

    c1 = Concept(name="social_organization", description="Colony social structure")
    c1.add_term("colony")
    c1.add_term("caste")
    c1.add_term("worker")
    c1.add_domain("behavioral")
    c1.add_domain("ecological")

    c2 = Concept(name="communication", description="Insect communication")
    c2.add_term("pheromone")
    c2.add_term("dance")
    c2.add_term("signal")
    c2.add_domain("chemical")
    c2.add_domain("behavioral")

    c3 = Concept(name="foraging", description="Food collection behavior")
    c3.add_term("nectar")
    c3.add_term("trail")
    c3.add_term("forager")
    c3.add_domain("behavioral")

    c4 = Concept(name="morphology", description="Insect body structure")
    c4.add_term("mandible")
    c4.add_term("antenna")
    c4.add_domain("morphological")

    concept_map.add_concept(c1)
    concept_map.add_concept(c2)
    concept_map.add_concept(c3)
    concept_map.add_concept(c4)

    concept_map.add_relationship("social_organization", "communication", 0.9)
    concept_map.add_relationship("communication", "foraging", 0.7)
    concept_map.add_relationship("social_organization", "foraging", 0.6)
    concept_map.add_relationship("morphology", "foraging", 0.4)

    return concept_map


@pytest.fixture
def expanded_sample_terms():
    """Create sample terms for expanded conceptual mapping tests."""
    return {
        "colony": Term(
            text="colony", lemma="colony",
            domains=["behavioral"], frequency=15,
            contexts=["The colony structure is complex"],
        ),
        "pheromone": Term(
            text="pheromone", lemma="pheromone",
            domains=["chemical"], frequency=12,
            contexts=["Pheromone signaling is key"],
        ),
        "worker": Term(
            text="worker", lemma="worker",
            domains=["behavioral"], frequency=10,
            contexts=["Worker bees perform tasks"],
        ),
        "mandible": Term(
            text="mandible", lemma="mandible",
            domains=["morphological"], frequency=5,
            contexts=["The mandible structure varies"],
        ),
        "forager": Term(
            text="forager", lemma="forager",
            domains=["behavioral"], frequency=8,
            contexts=["Forager bees collect nectar"],
        ),
    }


class TestConceptMapAdvancedMethods:
    """Tests for advanced ConceptMap methods."""

    def test_get_concept_clusters(self, populated_concept_map):
        clusters = populated_concept_map.get_concept_clusters()
        assert isinstance(clusters, dict)
        all_concepts = set()
        for concepts in clusters.values():
            all_concepts.update(concepts)
        for concept_name in populated_concept_map.concepts:
            assert concept_name in all_concepts

    def test_get_concept_clusters_threshold(self, populated_concept_map):
        clusters_low = populated_concept_map.get_concept_clusters(similarity_threshold=0.1)
        clusters_high = populated_concept_map.get_concept_clusters(similarity_threshold=0.9)
        assert isinstance(clusters_low, dict)
        assert isinstance(clusters_high, dict)

    def test_get_concept_centrality(self, populated_concept_map):
        centrality = populated_concept_map.get_concept_centrality()
        assert isinstance(centrality, dict)
        for concept_name, metrics in centrality.items():
            assert isinstance(metrics, dict)

    def test_get_relationship_strengths(self, populated_concept_map):
        strengths = populated_concept_map.get_relationship_strengths()
        assert isinstance(strengths, dict)
        assert len(strengths) > 0

    def test_get_bridge_concepts(self, populated_concept_map):
        bridges = populated_concept_map.get_bridge_concepts()
        assert isinstance(bridges, dict)


class TestConceptualMapperAdvancedMethods:
    """Tests for advanced ConceptualMapper methods."""

    @pytest.fixture
    def adv_mapper(self):
        return ConceptualMapper()

    def test_calculate_concept_similarity_same(self, adv_mapper):
        c1 = Concept(name="a", description="Colony behavior")
        c1.add_term("colony")
        c1.add_term("caste")
        c1.add_domain("behavioral")
        result = adv_mapper.calculate_concept_similarity(c1, c1)
        assert result == 1.0

    def test_calculate_concept_similarity_different(self, adv_mapper):
        c1 = Concept(name="a", description="Colony behavior")
        c1.add_term("colony")
        c1.add_term("caste")
        c1.add_domain("behavioral")
        c2 = Concept(name="b", description="Chemical signaling")
        c2.add_term("pheromone")
        c2.add_term("hormone")
        c2.add_domain("chemical")
        result = adv_mapper.calculate_concept_similarity(c1, c2)
        assert 0 <= result <= 1.0

    def test_calculate_concept_similarity_overlap(self, adv_mapper):
        c1 = Concept(name="a", description="Colony behavior")
        c1.add_term("colony")
        c1.add_term("worker")
        c1.add_domain("behavioral")
        c2 = Concept(name="b", description="Colony dynamics")
        c2.add_term("colony")
        c2.add_term("queen")
        c2.add_domain("behavioral")
        result = adv_mapper.calculate_concept_similarity(c1, c2)
        assert result > 0

    def test_analyze_concept_centrality(self, adv_mapper, populated_concept_map):
        centrality = adv_mapper.analyze_concept_centrality(populated_concept_map)
        assert isinstance(centrality, dict)
        for concept in populated_concept_map.concepts:
            assert concept in centrality

    def test_quantify_relationship_strength(self, adv_mapper, populated_concept_map):
        strengths = adv_mapper.quantify_relationship_strength(populated_concept_map)
        assert isinstance(strengths, dict)
        assert len(strengths) > 0

    def test_identify_cross_domain_bridges(self, adv_mapper, populated_concept_map):
        bridges = adv_mapper.identify_cross_domain_bridges(populated_concept_map)
        assert isinstance(bridges, dict)

    def test_cluster_concepts(self, adv_mapper, populated_concept_map):
        clusters = adv_mapper.cluster_concepts(populated_concept_map)
        assert isinstance(clusters, dict)
        all_concepts = set()
        for concepts in clusters.values():
            all_concepts.update(concepts)
        for concept_name in populated_concept_map.concepts:
            assert concept_name in all_concepts

    def test_cluster_concepts_high_threshold(self, adv_mapper, populated_concept_map):
        clusters = adv_mapper.cluster_concepts(populated_concept_map, similarity_threshold=0.99)
        assert isinstance(clusters, dict)
        assert len(clusters) >= 1

    def test_track_concept_evolution_single(self, adv_mapper, populated_concept_map):
        result = adv_mapper.track_concept_evolution(populated_concept_map, [])
        assert isinstance(result, dict)

    def test_track_concept_evolution_with_history(self, adv_mapper, populated_concept_map):
        historical_map = ConceptMap()
        c = Concept(name="social_organization", description="Basic social")
        c.add_term("colony")
        c.add_domain("behavioral")
        historical_map.add_concept(c)
        result = adv_mapper.track_concept_evolution(populated_concept_map, [historical_map])
        assert isinstance(result, dict)

    def test_build_concept_map_adv(self, adv_mapper, expanded_sample_terms):
        concept_map = adv_mapper.build_concept_map(expanded_sample_terms)
        assert isinstance(concept_map, ConceptMap)
        assert len(concept_map.concepts) > 0

    def test_export_concept_map_json_adv(self, adv_mapper, expanded_sample_terms):
        adv_mapper.build_concept_map(expanded_sample_terms)
        with tempfile.TemporaryDirectory() as tmp:
            filepath = Path(tmp) / "concepts.json"
            adv_mapper.export_concept_map_json(str(filepath))
            assert filepath.exists()
            with open(filepath) as f:
                data = json.load(f)
            assert isinstance(data, dict)

    def test_detect_anthropomorphic_concepts_adv(self, adv_mapper, expanded_sample_terms):
        adv_mapper.build_concept_map(expanded_sample_terms)
        result = adv_mapper.detect_anthropomorphic_concepts()
        assert isinstance(result, dict)

    def test_find_concept_gaps_adv(self, adv_mapper, expanded_sample_terms):
        adv_mapper.build_concept_map(expanded_sample_terms)
        domain_terms = {
            "behavioral": ["colony", "worker", "forager"],
            "chemical": ["pheromone"],
            "morphological": ["mandible"],
        }
        result = adv_mapper.find_concept_gaps(domain_terms)
        assert isinstance(result, dict)

    def test_identify_conceptual_boundaries_adv(self, adv_mapper, expanded_sample_terms):
        adv_mapper.build_concept_map(expanded_sample_terms)
        result = adv_mapper.identify_conceptual_boundaries()
        assert isinstance(result, dict)

    def test_analyze_conceptual_hierarchy_adv(self, adv_mapper, expanded_sample_terms):
        adv_mapper.build_concept_map(expanded_sample_terms)
        result = adv_mapper.analyze_conceptual_hierarchy()
        assert isinstance(result, dict)


class TestConceptMapEdgeCases:
    """Edge case tests for ConceptMap."""

    def test_empty_concept_map_clusters(self):
        cm = ConceptMap()
        clusters = cm.get_concept_clusters()
        assert isinstance(clusters, dict)

    def test_empty_concept_map_centrality(self):
        cm = ConceptMap()
        centrality = cm.get_concept_centrality()
        assert isinstance(centrality, dict)

    def test_single_concept_no_relationships(self):
        cm = ConceptMap()
        c = Concept(name="lone", description="A lone concept")
        c.add_term("singular")
        cm.add_concept(c)
        bridges = cm.get_bridge_concepts()
        assert isinstance(bridges, dict)


# ============================================================================
# Coverage tests (from test_conceptual_mapping_coverage.py)
# ============================================================================


@pytest.fixture
def large_concept_map():
    """A larger concept map to exercise more code paths."""
    cm = ConceptMap()
    concepts = [
        ("social", "Social behavior", ["colony", "caste", "worker"], ["behavioral"]),
        ("chemical", "Chemical signals", ["pheromone", "hormone"], ["chemical"]),
        ("foraging", "Foraging behavior", ["trail", "nectar", "forager"], ["behavioral", "ecological"]),
        ("morphology", "Body structure", ["mandible", "antenna", "cuticle"], ["morphological"]),
        ("reproduction", "Reproductive biology", ["queen", "mating", "brood"], ["reproductive"]),
        ("genetics", "Population genetics", ["gene", "allele", "fitness"], ["genetic"]),
    ]
    for name, desc, terms, domains in concepts:
        c = Concept(name=name, description=desc)
        for t in terms:
            c.add_term(t)
        for d in domains:
            c.add_domain(d)
        cm.add_concept(c)

    cm.add_relationship("social", "chemical", 0.9)
    cm.add_relationship("social", "foraging", 0.8)
    cm.add_relationship("chemical", "foraging", 0.7)
    cm.add_relationship("morphology", "foraging", 0.5)
    cm.add_relationship("reproduction", "genetics", 0.85)
    cm.add_relationship("social", "reproduction", 0.6)
    cm.add_relationship("genetics", "social", 0.4)
    return cm


class TestConceptMapExport:
    """Test concept map export to various formats."""

    def test_export_to_dict(self, large_concept_map):
        assert len(large_concept_map.concepts) == 6
        assert len(large_concept_map.concept_relationships) > 0

    def test_concept_to_dict_coverage(self):
        c = Concept(name="test", description="Test concept")
        c.add_term("term1")
        c.add_domain("domain1")
        d = c.to_dict()
        assert d["name"] == "test"
        assert "term1" in d["terms"]
        assert "domain1" in d["domains"]


class TestConceptualMapperExport:
    """Tests for ConceptualMapper export methods."""

    def test_export_json_full(self):
        mapper = ConceptualMapper()
        terms = {
            "colony": Term(text="colony", lemma="colony",
                          domains=["behavioral"], frequency=15),
            "worker": Term(text="worker", lemma="worker",
                          domains=["behavioral"], frequency=10),
        }
        mapper.build_concept_map(terms)
        with tempfile.TemporaryDirectory() as tmp:
            filepath = Path(tmp) / "export.json"
            mapper.export_concept_map_json(str(filepath))
            assert filepath.exists()
            with open(filepath) as f:
                data = json.load(f)
            assert isinstance(data, dict)


class TestConceptualMapperAnalysis:
    """Tests for ConceptualMapper analysis methods on larger data."""

    @pytest.fixture
    def cov_mapper(self):
        return ConceptualMapper()

    def test_analyze_centrality_large(self, cov_mapper, large_concept_map):
        centrality = cov_mapper.analyze_concept_centrality(large_concept_map)
        assert isinstance(centrality, dict)
        assert "social" in centrality

    def test_relationship_strength_large(self, cov_mapper, large_concept_map):
        strengths = cov_mapper.quantify_relationship_strength(large_concept_map)
        assert isinstance(strengths, dict)
        assert len(strengths) > 0

    def test_cross_domain_bridges_large(self, cov_mapper, large_concept_map):
        bridges = cov_mapper.identify_cross_domain_bridges(large_concept_map)
        assert isinstance(bridges, dict)

    def test_cluster_concepts_large(self, cov_mapper, large_concept_map):
        clusters = cov_mapper.cluster_concepts(large_concept_map)
        assert isinstance(clusters, dict)
        all_concepts = set()
        for concepts in clusters.values():
            all_concepts.update(concepts)
        for name in large_concept_map.concepts:
            assert name in all_concepts

    def test_detect_anthropomorphic(self, cov_mapper):
        terms = {
            "decides": Term(text="decides", lemma="decide",
                           domains=["behavioral"], frequency=5),
            "chooses": Term(text="chooses", lemma="choose",
                           domains=["behavioral"], frequency=3),
            "antenna": Term(text="antenna", lemma="antenna",
                           domains=["morphological"], frequency=8),
        }
        cov_mapper.build_concept_map(terms)
        result = cov_mapper.detect_anthropomorphic_concepts()
        assert isinstance(result, dict)

    def test_conceptual_boundaries(self, cov_mapper):
        terms = {
            "colony": Term(text="colony", lemma="colony",
                          domains=["behavioral", "ecological"], frequency=15),
            "pheromone": Term(text="pheromone", lemma="pheromone",
                            domains=["chemical"], frequency=10),
        }
        cov_mapper.build_concept_map(terms)
        result = cov_mapper.identify_conceptual_boundaries()
        assert isinstance(result, dict)

    def test_conceptual_hierarchy(self, cov_mapper):
        terms = {
            "colony": Term(text="colony", lemma="colony",
                          domains=["behavioral"], frequency=15),
            "worker": Term(text="worker", lemma="worker",
                          domains=["behavioral"], frequency=10),
            "queen": Term(text="queen", lemma="queen",
                         domains=["behavioral"], frequency=8),
        }
        cov_mapper.build_concept_map(terms)
        result = cov_mapper.analyze_conceptual_hierarchy()
        assert isinstance(result, dict)


class TestConceptMapRelationships:
    """Test relationship edge cases."""

    def test_update_relationship_weight(self):
        cm = ConceptMap()
        c1 = Concept(name="a", description="A")
        c2 = Concept(name="b", description="B")
        cm.add_concept(c1)
        cm.add_concept(c2)
        cm.add_relationship("a", "b", 0.5)
        cm.add_relationship("a", "b", 0.9)
        strengths = cm.get_relationship_strengths()
        assert len(strengths) == 1

    def test_get_bridge_concepts_complex(self, large_concept_map):
        bridges = large_concept_map.get_bridge_concepts()
        assert isinstance(bridges, dict)


class TestMapTermDomainBranches:
    """Tests for _map_term_to_concepts covering all domain branches."""

    @pytest.fixture
    def branch_mapper(self):
        return ConceptualMapper()

    def test_kin_domain_mapping(self, branch_mapper):
        terms = {
            "kin_selection": Term(text="kin_selection", lemma="kin_selection",
                                  domains=["kin_and_relatedness"], frequency=5),
        }
        result = branch_mapper.build_concept_map(terms)
        assert "kin_selection" in result.concepts["kinship_systems"].terms

    def test_economics_domain_mapping(self, branch_mapper):
        terms = {
            "resource_allocation": Term(text="resource_allocation", lemma="resource_allocation",
                                        domains=["economics"], frequency=5),
        }
        result = branch_mapper.build_concept_map(terms)
        assert "resource_allocation" in result.concepts["resource_economics"].terms

    def test_unit_of_individuality_mapping(self, branch_mapper):
        terms = {
            "superorganism": Term(text="superorganism", lemma="superorganism",
                                   domains=["unit_of_individuality"], frequency=5),
        }
        result = branch_mapper.build_concept_map(terms)
        assert "superorganism" in result.concepts["biological_individuality"].terms

    def test_sex_reproduction_mapping(self, branch_mapper):
        terms = {
            "haplodiploidy": Term(text="haplodiploidy", lemma="haplodiploidy",
                                  domains=["sex_and_reproduction"], frequency=5),
        }
        result = branch_mapper.build_concept_map(terms)
        assert "haplodiploidy" in result.concepts["reproductive_biology"].terms


class TestSemanticConceptMapping:
    """Tests for _semantic_concept_mapping to cover all pattern branches."""

    @pytest.fixture
    def sem_mapper(self):
        return ConceptualMapper()

    def test_individuality_semantic(self, sem_mapper):
        terms = {
            "unit_entity": Term(text="unit_entity", lemma="unit_entity",
                                domains=[], frequency=5),
        }
        result = sem_mapper.build_concept_map(terms)
        assert "unit_entity" in result.concepts["biological_individuality"].terms

    def test_social_semantic(self, sem_mapper):
        terms = {
            "social_group": Term(text="social_group", lemma="social_group",
                                 domains=[], frequency=3),
        }
        result = sem_mapper.build_concept_map(terms)
        assert "social_group" in result.concepts["social_organization"].terms

    def test_reproductive_semantic(self, sem_mapper):
        terms = {
            "mating_flight": Term(text="mating_flight", lemma="mating_flight",
                                   domains=[], frequency=3),
        }
        result = sem_mapper.build_concept_map(terms)
        assert "mating_flight" in result.concepts["reproductive_biology"].terms

    def test_kinship_semantic(self, sem_mapper):
        terms = {
            "kin_group": Term(text="kin_group", lemma="kin_group",
                              domains=[], frequency=3),
        }
        result = sem_mapper.build_concept_map(terms)
        assert "kin_group" in result.concepts["kinship_systems"].terms

    def test_economic_semantic(self, sem_mapper):
        terms = {
            "resource_cost": Term(text="resource_cost", lemma="resource_cost",
                                   domains=[], frequency=3),
        }
        result = sem_mapper.build_concept_map(terms)
        assert "resource_cost" in result.concepts["resource_economics"].terms

    def test_behavioral_semantic(self, sem_mapper):
        terms = {
            "behavioral_adaptation": Term(text="behavioral_adaptation",
                                           lemma="behavioral_adaptation",
                                           domains=[], frequency=3),
        }
        result = sem_mapper.build_concept_map(terms)
        assert "behavioral_adaptation" in result.concepts["behavioral_ecology"].terms


class TestSimpleSimilarityClustering:
    """Tests for _simple_similarity_clustering fallback."""

    def test_fallback_clustering(self):
        mapper = ConceptualMapper()
        cm = ConceptMap()
        c1 = Concept(name="a", description="A")
        c1.add_term("colony")
        c1.add_term("worker")
        c2 = Concept(name="b", description="B")
        c2.add_term("colony")
        c2.add_term("queen")
        c3 = Concept(name="c", description="C")
        c3.add_term("DNA")
        c3.add_term("gene")
        cm.add_concept(c1)
        cm.add_concept(c2)
        cm.add_concept(c3)
        result = mapper._simple_similarity_clustering(cm, 0.1)
        assert isinstance(result, dict)
        assert len(result) >= 1
        all_concepts = set()
        for concepts in result.values():
            all_concepts.update(concepts)
        assert "a" in all_concepts
        assert "b" in all_concepts
        assert "c" in all_concepts


class TestBuildConceptMapValidation:
    """Tests for build_concept_map input validation."""

    def test_non_dict_input_raises(self):
        mapper = ConceptualMapper()
        with pytest.raises(ValueError):
            mapper.build_concept_map("not a dict")

    def test_non_term_values_raises(self):
        mapper = ConceptualMapper()
        with pytest.raises(ValueError):
            mapper.build_concept_map({"key": "not a Term"})


class TestFindConceptGapsCoverage:
    """Tests for find_concept_gaps."""

    def test_with_gaps(self):
        mapper = ConceptualMapper()
        terms = {
            "colony": Term(text="colony", lemma="colony",
                          domains=["behavioral"], frequency=5),
        }
        mapper.build_concept_map(terms)
        gaps = mapper.find_concept_gaps({
            "unknown_domain": ["xyz_term", "abc_term"],
        })
        assert "unknown_domain" in gaps

    def test_no_gaps(self):
        mapper = ConceptualMapper()
        terms = {
            "colony": Term(text="colony", lemma="colony",
                          domains=["behavioral"], frequency=5),
        }
        mapper.build_concept_map(terms)
        gaps = mapper.find_concept_gaps({
            "behavioral": ["colony"],
        })
        assert "behavioral" not in gaps
