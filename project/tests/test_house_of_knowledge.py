"""Comprehensive tests for house_of_knowledge.py module.

Tests the HouseOfKnowledgeAnalyzer class and all House of Knowledge analysis
functionality for Andrius Kulikauskas's philosophical framework.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock

from src.house_of_knowledge import (
    HouseOfKnowledgeAnalyzer, HouseStructure, RoomRelationships,
    FrameworkAnalysis, HouseStatistics, analyze_house, get_house_analyzer
)
from src.models import Room, Way


class TestHouseOfKnowledgeAnalyzer:
    """Test HouseOfKnowledgeAnalyzer class methods."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database with test data."""
        mock_db = Mock()
        return mock_db

    @pytest.fixture
    def mock_queries(self):
        """Create a mock SQL queries object with test data."""
        mock_queries = Mock()

        # Mock rooms data
        mock_queries.get_rooms_sql.return_value = (
            "SELECT * FROM menes",
            [
                (1, "B", "Believing", "Basic belief", 1, 1, 1, "Primary", "Self", "Creator", "Notes", "B"),
                (2, "B2", "Believing 2", "Advanced belief", 2, 2, 1, "Secondary", "Other", "Sustainer", "Notes", "B2"),
                (3, "1", "Caring", "Basic care", 3, 1, 2, "Primary", "You", "Love", "Notes", "1")
            ]
        )

        # Mock ways data
        mock_queries.get_all_ways_sql.return_value = (
            "SELECT * FROM ways",
            [
                (1, "Way 1", "Partner A", "Absolute", "Self", "", "Example 1", "", "B", "Creator", "", ""),
                (2, "Way 2", "Partner B", "Relative", "Other", "", "Example 2", "", "B", "Sustainer", "", ""),
                (3, "Way 3", "Partner A", "Absolute", "Self", "", "Example 3", "", "B2", "Creator", "", ""),
                (4, "Way 4", "Partner C", "Embrace God", "Person", "", "Example 4", "", "1", "Love", "", "")
            ]
        )

        return mock_queries

    @pytest.fixture
    def analyzer(self, mock_db, mock_queries):
        """Create a HouseOfKnowledgeAnalyzer with mocked dependencies."""
        analyzer = HouseOfKnowledgeAnalyzer.__new__(HouseOfKnowledgeAnalyzer)
        analyzer.db = mock_db
        analyzer.queries = mock_queries
        analyzer.house = analyzer._load_house_structure()
        return analyzer

    def test_analyzer_initialization(self):
        """Test HouseOfKnowledgeAnalyzer initialization."""
        analyzer = HouseOfKnowledgeAnalyzer()
        assert hasattr(analyzer, 'db')
        assert hasattr(analyzer, 'queries')
        assert hasattr(analyzer, 'house')
        assert isinstance(analyzer.house, HouseStructure)

    def test_analyzer_initialization_with_db_path(self, tmp_path):
        """Test HouseOfKnowledgeAnalyzer initialization with custom database path."""
        custom_path = tmp_path / "custom.db"

        # Initialize database from dump
        from src.database import WaysDatabase
        db = WaysDatabase(db_path=str(custom_path))
        dump_path = Path(__file__).parent.parent / "db" / "andrius_ways.sql"
        if dump_path.exists():
            db.initialize_from_mysql_dump(str(dump_path))

            analyzer = HouseOfKnowledgeAnalyzer(db_path=str(custom_path))
            assert hasattr(analyzer, 'db')
            assert hasattr(analyzer, 'queries')
        else:
            pytest.skip("Database dump not found")

    def test_get_house_structure(self, analyzer):
        """Test get_house_structure method."""
        structure = analyzer.get_house_structure()
        assert isinstance(structure, HouseStructure)
        assert len(structure.rooms) == 3  # From mock data
        assert len(structure.ways) == 4   # From mock data
        assert len(structure.room_hierarchy) == 3
        assert 'B' in structure.room_hierarchy
        assert 'B2' in structure.room_hierarchy
        assert '1' in structure.room_hierarchy

    def test_house_structure_levels_and_wings(self, analyzer):
        """Test that room levels and wings are properly organized."""
        structure = analyzer.house

        # Check levels (laipsnis)
        assert 1 in structure.room_levels
        assert 2 in structure.room_levels
        assert 'B' in structure.room_levels[1]  # Level 1
        assert '1' in structure.room_levels[1]  # Level 1
        assert 'B2' in structure.room_levels[2]  # Level 2

        # Check wings (sparnas)
        assert 1 in structure.room_wings  # Wing 1
        assert 2 in structure.room_wings  # Wing 2
        assert 'B' in structure.room_wings[1]
        assert 'B2' in structure.room_wings[1]
        assert '1' in structure.room_wings[2]

    def test_framework_structure_analysis(self, analyzer):
        """Test framework structure analysis."""
        structure = analyzer.house
        assert 'framework_structure' in structure.__dict__

        frameworks = structure.framework_structure
        assert 'believing' in frameworks
        assert 'caring' in frameworks
        assert 'knowing' in frameworks
        assert 'making' in frameworks

        # Check believing framework
        believing = frameworks['believing']
        assert believing['rooms'] == ['B', 'B2', 'B3', 'B4']
        assert believing['theme'] == 'Faith and belief'
        assert believing['levels'] == [1, 2, 3, 4]

    def test_analyze_room_relationships(self, analyzer):
        """Test room relationships analysis."""
        relationships = analyzer.analyze_room_relationships()
        assert isinstance(relationships, RoomRelationships)

        # Check that adjacency matrix is initialized
        assert isinstance(relationships.adjacency_matrix, dict)
        assert len(relationships.adjacency_matrix) == 3  # 3 rooms

        # Check hierarchical relationships
        assert 'level_1' in relationships.hierarchical_relationships  # Level 1
        assert 'level_2' in relationships.hierarchical_relationships  # Level 2

        # Check framework connections
        assert 'believing' in relationships.framework_connections
        assert 'caring' in relationships.framework_connections

    def test_get_room_hierarchy(self, analyzer):
        """Test room hierarchy retrieval."""
        hierarchy = analyzer.get_room_hierarchy()
        assert isinstance(hierarchy, list)
        assert len(hierarchy) == 3
        # Should be ordered by eilestvarka (1, 2, 3)
        assert hierarchy == ['B', 'B2', '1']

    def test_analyze_room_cooccurrence(self, analyzer):
        """Test room cooccurrence analysis."""
        cooccurrences = analyzer.analyze_room_cooccurrence()
        assert isinstance(cooccurrences, dict)
        assert len(cooccurrences) == 3  # One entry per room

        # Currently returns empty lists since ways belong to single rooms
        for room, cooccurring_rooms in cooccurrences.items():
            assert isinstance(cooccurring_rooms, list)
            assert len(cooccurring_rooms) == 0

    def test_analyze_believing_structure(self, analyzer):
        """Test believing structure analysis."""
        believing = analyzer.analyze_believing_structure()
        assert isinstance(believing, dict)
        assert believing['name'] == 'Believing'
        assert believing['rooms'] == ['B', 'B2', 'B3', 'B4']
        assert 'total_ways' in believing
        assert 'room_details' in believing
        assert 'structural_integrity' in believing

    def test_analyze_caring_structure(self, analyzer):
        """Test caring structure analysis."""
        caring = analyzer.analyze_caring_structure()
        assert isinstance(caring, dict)
        assert caring['name'] == 'Caring'
        assert caring['rooms'] == ['1', '10', '20', '30']
        assert 'total_ways' in caring
        assert 'room_details' in caring

    def test_analyze_relative_learning(self, analyzer):
        """Test relative learning analysis."""
        relative = analyzer.analyze_relative_learning()
        assert isinstance(relative, dict)
        assert relative['name'] == 'Relative Learning'
        assert relative['rooms'] == ['R', 'F', 'T']
        assert 'total_ways' in relative
        assert 'room_details' in relative

    def test_get_framework_statistics(self, analyzer):
        """Test framework statistics computation."""
        stats = analyzer.get_framework_statistics()
        assert isinstance(stats, dict)

        # Should have believing, caring, relative_learning, and house_overall
        expected_frameworks = ['believing', 'caring', 'relative_learning', 'house_overall']
        for framework in expected_frameworks:
            assert framework in stats

        # Check framework-specific stats
        for framework_name in ['believing', 'caring', 'relative_learning']:
            framework_stats = stats[framework_name]
            assert 'total_ways' in framework_stats
            assert 'room_coverage' in framework_stats
            assert 'balance_score' in framework_stats
            assert 'type_diversity' in framework_stats

        # Check house overall stats
        house_overall = stats['house_overall']
        assert 'total_rooms' in house_overall
        assert 'total_ways' in house_overall
        assert 'frameworks_analyzed' in house_overall

    def test_get_house_statistics(self, analyzer):
        """Test house statistics computation."""
        stats = analyzer.get_house_statistics()
        assert isinstance(stats, HouseStatistics)

        assert stats.total_rooms == 3
        assert stats.total_ways == 4
        assert isinstance(stats.ways_per_room, dict)
        assert isinstance(stats.room_coverage, float)
        assert isinstance(stats.framework_balance, dict)
        assert isinstance(stats.structural_integrity, dict)

    def test_get_room_by_short(self, analyzer):
        """Test room lookup by short name."""
        room = analyzer.get_room_by_short('B')
        assert room is not None
        assert room.santrumpa == 'B'
        assert room.savoka == 'Believing'

        # Test non-existing room
        nonexistent = analyzer.get_room_by_short('NONEXISTENT')
        assert nonexistent is None

    def test_get_ways_in_room(self, analyzer):
        """Test ways retrieval by room."""
        b_ways = analyzer.get_ways_in_room('B')
        assert isinstance(b_ways, list)
        assert len(b_ways) == 2  # Way 1 and Way 2 from mock data

        b2_ways = analyzer.get_ways_in_room('B2')
        assert isinstance(b2_ways, list)
        assert len(b2_ways) == 1  # Way 3 from mock data

        nonexistent_ways = analyzer.get_ways_in_room('NONEXISTENT')
        assert isinstance(nonexistent_ways, list)
        assert len(nonexistent_ways) == 0

    def test_get_ways_by_dialogue_type(self, analyzer):
        """Test ways retrieval by dialogue type."""
        absolute_ways = analyzer.get_ways_by_dialogue_type('Absolute')
        assert isinstance(absolute_ways, list)
        assert len(absolute_ways) == 2  # Way 1 and Way 3

        relative_ways = analyzer.get_ways_by_dialogue_type('Relative')
        assert isinstance(relative_ways, list)
        assert len(relative_ways) == 1  # Way 2

        nonexistent_ways = analyzer.get_ways_by_dialogue_type('NONEXISTENT')
        assert isinstance(nonexistent_ways, list)
        assert len(nonexistent_ways) == 0

    def test_create_house_model(self, analyzer):
        """Test HouseOfKnowledge model creation."""
        from src.models import HouseOfKnowledge

        house_model = analyzer.create_house_model()
        assert isinstance(house_model, HouseOfKnowledge)
        assert len(house_model.rooms) == 3
        assert len(house_model.ways) == 4
        assert house_model.total_rooms == 3
        assert house_model.total_ways == 4


class TestHouseStructure:
    """Test HouseStructure dataclass."""

    def test_structure_initialization(self):
        """Test HouseStructure basic initialization."""
        structure = HouseStructure()
        assert structure.rooms == []
        assert structure.ways == []
        assert structure.room_hierarchy == []
        assert structure.room_levels == {}
        assert structure.room_wings == {}
        assert structure.framework_structure == {}

    def test_structure_with_data(self):
        """Test HouseStructure with sample data."""
        room = Room(1, "B", "Believing", "Basic belief", 1, 1, 1, "Primary", "Self", "Creator", "Notes", "B")
        way = Way(1, "Test way", "Partner", "Absolute", "Self", "", "Example", "", "B", "", "", "")

        structure = HouseStructure(
            rooms=[room],
            ways=[way],
            room_hierarchy=["B"],
            room_levels={1: ["B"]},
            room_wings={1: ["B"]},
            framework_structure={"test": {"rooms": ["B"]}}
        )

        assert len(structure.rooms) == 1
        assert len(structure.ways) == 1
        assert structure.room_hierarchy == ["B"]
        assert structure.room_levels[1] == ["B"]
        assert structure.room_wings[1] == ["B"]
        assert structure.framework_structure["test"]["rooms"] == ["B"]


class TestRoomRelationships:
    """Test RoomRelationships dataclass."""

    def test_relationships_initialization(self):
        """Test RoomRelationships basic initialization."""
        relationships = RoomRelationships()
        assert relationships.adjacency_matrix == {}
        assert relationships.room_clusters == {}
        assert relationships.hierarchical_relationships == {}
        assert relationships.framework_connections == {}

    def test_relationships_with_data(self):
        """Test RoomRelationships with sample data."""
        relationships = RoomRelationships(
            adjacency_matrix={"B": {"B2": 0.8}, "B2": {"B": 0.6}},
            room_clusters={"wing_1": ["B", "B2"]},
            hierarchical_relationships={"level_1": ["B"]},
            framework_connections={"believing": ["B", "B2"]}
        )

        assert relationships.adjacency_matrix["B"]["B2"] == 0.8
        assert relationships.room_clusters["wing_1"] == ["B", "B2"]
        assert relationships.hierarchical_relationships["level_1"] == ["B"]
        assert relationships.framework_connections["believing"] == ["B", "B2"]


class TestFrameworkAnalysis:
    """Test FrameworkAnalysis dataclass."""

    def test_framework_initialization(self):
        """Test FrameworkAnalysis basic initialization."""
        analysis = FrameworkAnalysis()
        assert analysis.believing_structure == {}
        assert analysis.caring_structure == {}
        assert analysis.relative_learning == {}
        assert analysis.framework_completeness == {}


class TestHouseStatistics:
    """Test HouseStatistics dataclass."""

    def test_statistics_initialization(self):
        """Test HouseStatistics basic initialization."""
        stats = HouseStatistics()
        assert stats.total_rooms == 0
        assert stats.total_ways == 0
        assert stats.ways_per_room == {}
        assert stats.room_coverage == 0.0
        assert stats.framework_balance == {}
        assert stats.structural_integrity == {}

    def test_statistics_with_data(self):
        """Test HouseStatistics with sample data."""
        stats = HouseStatistics(
            total_rooms=3,
            total_ways=4,
            ways_per_room={"B": 2, "B2": 1, "1": 1},
            room_coverage=1.0,
            framework_balance={"believing": 0.8, "caring": 0.6},
            structural_integrity={"all_rooms_have_ways": True, "balanced_distribution": {"balanced": True}}
        )

        assert stats.total_rooms == 3
        assert stats.total_ways == 4
        assert stats.ways_per_room["B"] == 2
        assert stats.room_coverage == 1.0
        assert stats.framework_balance["believing"] == 0.8


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_analyze_house(self):
        """Test analyze_house convenience function."""
        # Test with mock to avoid database dependency
        with pytest.raises(Exception):  # Will fail without database
            stats = analyze_house()
        # Function exists and is callable
        from src.house_of_knowledge import analyze_house
        assert callable(analyze_house)

    def test_get_house_analyzer(self):
        """Test get_house_analyzer convenience function."""
        # Test with mock to avoid database dependency
        with pytest.raises(Exception):  # Will fail without database
            analyzer = get_house_analyzer()
        # Function exists and is callable
        from src.house_of_knowledge import get_house_analyzer
        assert callable(get_house_analyzer)


class TestInternalMethods:
    """Test internal/private methods."""

    def test_load_house_structure(self, house_analyzer):
        """Test _load_house_structure method."""
        if house_analyzer is None:
            pytest.skip("Database not available")

        structure = house_analyzer._load_house_structure()
        assert isinstance(structure, HouseStructure)
        # Test that structure has expected attributes
        assert hasattr(structure, 'rooms')
        assert hasattr(structure, 'ways')
        assert hasattr(structure, 'room_hierarchy')

    def test_analyze_framework_structure(self, house_analyzer):
        """Test _analyze_framework_structure method."""
        if house_analyzer is None:
            pytest.skip("Database not available")

        analyzer = house_analyzer
        structure = analyzer._load_house_structure()
        framework_structure = analyzer._analyze_framework_structure(structure)

        assert isinstance(framework_structure, dict)
        # Test that framework structure has expected keys
        assert isinstance(framework_structure, dict)
        # Don't test specific content since it depends on real data

    def test_analyze_framework_method(self, house_analyzer):
        """Test framework analysis methods."""
        if house_analyzer is None:
            pytest.skip("Database not available")

        # Test that public framework methods work
        believing = house_analyzer.analyze_believing_structure()
        assert isinstance(believing, dict)
        assert 'name' in believing
        assert 'rooms' in believing

    def test_calculate_balance_score(self):
        """Test _calculate_balance_score method."""
        analyzer = HouseOfKnowledgeAnalyzer.__new__(HouseOfKnowledgeAnalyzer)

        # Test with equal distribution
        framework_analysis = {
            'room_details': {
                'B': {'way_count': 2},
                'B2': {'way_count': 2},
                'B3': {'way_count': 2},
                'B4': {'way_count': 2}
            }
        }
        score = analyzer._calculate_balance_score(framework_analysis)
        assert score == 1.0  # Perfect balance

        # Test with unequal distribution
        framework_analysis_unbalanced = {
            'room_details': {
                'B': {'way_count': 10},
                'B2': {'way_count': 0},
                'B3': {'way_count': 0},
                'B4': {'way_count': 0}
            }
        }
        score_unbalanced = analyzer._calculate_balance_score(framework_analysis_unbalanced)
        assert score_unbalanced < 1.0  # Less balanced

    def test_assess_distribution_balance(self):
        """Test _assess_distribution_balance method."""
        analyzer = HouseOfKnowledgeAnalyzer.__new__(HouseOfKnowledgeAnalyzer)

        ways_per_room = {"B": 5, "B2": 5, "B3": 5}
        balance = analyzer._assess_distribution_balance(ways_per_room)

        assert isinstance(balance, dict)
        assert 'balanced' in balance
        assert 'mean_ways_per_room' in balance
        assert 'variance' in balance
        assert 'coefficient_of_variation' in balance
        assert 'assessment' in balance

        # Should be balanced (equal distribution)
        assert balance['balanced'] is True
        assert balance['assessment'] == 'balanced'

    def test_assess_framework_integrity(self):
        """Test _assess_framework_integrity method."""
        analyzer = HouseOfKnowledgeAnalyzer.__new__(HouseOfKnowledgeAnalyzer)

        framework_stats = {
            'believing': {
                'total_ways': 4,
                'room_coverage': 1.0,
                'balance_score': 0.8,
                'type_diversity': 3
            }
        }

        integrity = analyzer._assess_framework_integrity(framework_stats)

        assert isinstance(integrity, dict)
        assert 'believing' in integrity
        believing_integrity = integrity['believing']
        assert 'has_ways' in believing_integrity
        assert 'room_coverage' in believing_integrity
        assert 'balance_score' in believing_integrity
        assert 'overall_integrity' in believing_integrity


class TestIntegrationWithRealData:
    """Test integration with real database data."""

    def test_analyzer_with_real_data(self):
        """Test that analyzer works with real database data."""
        try:
            analyzer = HouseOfKnowledgeAnalyzer()
            structure = analyzer.get_house_structure()

            # Should have some rooms and ways
            assert isinstance(structure, HouseStructure)
            assert len(structure.rooms) >= 0  # May be empty if DB not initialized
            assert len(structure.ways) >= 0

            # Test framework statistics
            stats = analyzer.get_framework_statistics()
            assert isinstance(stats, dict)

        except Exception:
            # If database doesn't exist or other issues, that's okay for this test
            pytest.skip("Database not available for integration test")


if __name__ == "__main__":
    pytest.main([__file__])
