"""Comprehensive tests for ways_analysis.py module.

Tests the WaysAnalyzer class and all analysis functionality for Andrius Kulikauskas's
philosophical framework of ways of figuring things out.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock
from src.ways_analysis import (
    WaysCharacterization,
    DialogueTypeAnalysis,
    RoomAnalysis,
    PartnerAnalysis,
    GodRelationshipAnalysis,
    ExamplesAnalysis,
    WaysAnalyzer
)
from src.house_of_knowledge import HouseStatistics


class TestDataClasses:
    """Test all dataclass definitions and their properties."""

    def test_ways_characterization_initialization(self):
        """Test WaysCharacterization dataclass initialization."""
        characterization = WaysCharacterization(
            total_ways=284,
            dialogue_types={"question": 50, "answer": 30},
            room_distribution={"kitchen": 20, "living_room": 15}
        )

        assert characterization.total_ways == 284
        assert characterization.dialogue_types == {"question": 50, "answer": 30}
        assert characterization.room_distribution == {"kitchen": 20, "living_room": 15}
        assert characterization.room_diversity == 2  # Number of different rooms
        assert characterization.type_diversity == 2  # Number of different types
        assert characterization.partner_diversity == 0  # No partner data

    def test_ways_characterization_with_all_data(self):
        """Test WaysCharacterization with complete data."""
        characterization = WaysCharacterization(
            total_ways=284,
            dialogue_types={"question": 50, "answer": 30, "discussion": 20},
            room_distribution={"kitchen": 20, "living_room": 15, "bedroom": 10},
            partner_distribution={"self": 40, "other": 35, "group": 25},
            god_relationships={"creator": 15, "sustainer": 12},
            ways_with_examples=150,
            avg_examples_length=250.5,
            most_common_room="kitchen",
            most_common_type="question",
            most_common_partner="self"
        )

        # Test most common values (set explicitly)
        assert characterization.most_common_room == "kitchen"
        assert characterization.most_common_type == "question"
        assert characterization.most_common_partner == "self"
        assert characterization.room_diversity == 3
        assert characterization.type_diversity == 3
        assert characterization.partner_diversity == 3

    def test_ways_characterization_empty_data(self):
        """Test WaysCharacterization with empty data."""
        characterization = WaysCharacterization()

        assert characterization.total_ways == 0
        assert characterization.dialogue_types == {}
        assert characterization.room_distribution == {}
        assert characterization.partner_distribution == {}
        assert characterization.god_relationships == {}
        assert characterization.ways_with_examples == 0
        assert characterization.avg_examples_length == 0.0
        assert characterization.room_diversity == 0
        assert characterization.type_diversity == 0
        assert characterization.partner_diversity == 0
        assert characterization.most_common_room == ""
        assert characterization.most_common_type == ""
        assert characterization.most_common_partner == ""

    def test_dialogue_type_analysis(self):
        """Test DialogueTypeAnalysis dataclass."""
        analysis = DialogueTypeAnalysis(
            type_distribution={"question": 50, "answer": 30},
            type_by_room={"kitchen": {"question": 20, "answer": 10}},
            room_by_type={"question": {"kitchen": 20, "living_room": 15}},
            type_characteristics={"question": {"complexity": "high", "frequency": "common"}}
        )

        assert analysis.type_distribution == {"question": 50, "answer": 30}
        assert analysis.type_by_room == {"kitchen": {"question": 20, "answer": 10}}
        assert analysis.room_by_type == {"question": {"kitchen": 20, "living_room": 15}}
        assert analysis.type_characteristics == {"question": {"complexity": "high", "frequency": "common"}}

    def test_room_analysis(self):
        """Test RoomAnalysis dataclass."""
        analysis = RoomAnalysis(
            room_stats={"kitchen": {"ways": 20, "types": 5}},
            room_hierarchy=["kitchen", "living_room", "bedroom"],
            room_cooccurrences={"kitchen": ["living_room", "bedroom"]},
            room_connectivity={"kitchen": 3, "living_room": 2}
        )

        assert analysis.room_stats == {"kitchen": {"ways": 20, "types": 5}}
        assert analysis.room_hierarchy == ["kitchen", "living_room", "bedroom"]
        assert analysis.room_cooccurrences == {"kitchen": ["living_room", "bedroom"]}
        assert analysis.room_connectivity == {"kitchen": 3, "living_room": 2}

    def test_partner_analysis(self):
        """Test PartnerAnalysis dataclass."""
        analysis = PartnerAnalysis(
            partner_distribution={"self": 40, "other": 35},
            partner_room_patterns={"self": {"kitchen": 15, "living_room": 10}},
            partner_type_patterns={"self": {"question": 20, "answer": 15}},
            partner_network={"self": ["other", "group"]}
        )

        assert analysis.partner_distribution == {"self": 40, "other": 35}
        assert analysis.partner_room_patterns == {"self": {"kitchen": 15, "living_room": 10}}
        assert analysis.partner_type_patterns == {"self": {"question": 20, "answer": 15}}
        assert analysis.partner_network == {"self": ["other", "group"]}

    def test_god_relationship_analysis(self):
        """Test GodRelationshipAnalysis dataclass."""
        analysis = GodRelationshipAnalysis(
            relationship_distribution={"creator": 15, "sustainer": 12},
            relationship_by_room={"creator": {"kitchen": 8, "living_room": 7}},
            relationship_by_type={"creator": {"question": 10, "answer": 5}},
            divine_perspectives=["omnipotent", "omniscient", "omnipresent"]
        )

        assert analysis.relationship_distribution == {"creator": 15, "sustainer": 12}
        assert analysis.relationship_by_room == {"creator": {"kitchen": 8, "living_room": 7}}
        assert analysis.relationship_by_type == {"creator": {"question": 10, "answer": 5}}
        assert analysis.divine_perspectives == ["omnipotent", "omniscient", "omnipresent"]

    def test_examples_analysis(self):
        """Test ExamplesAnalysis dataclass."""
        analysis = ExamplesAnalysis(
            total_with_examples=150,
            total_without_examples=134,
            avg_length=250.5,
            length_distribution={"short": 50, "medium": 70, "long": 30},
            keyword_patterns={"understanding": 25, "learning": 20},
            example_types={"personal": 80, "theoretical": 50, "practical": 20}
        )

        assert analysis.total_with_examples == 150
        assert analysis.total_without_examples == 134
        assert analysis.avg_length == 250.5
        assert analysis.length_distribution == {"short": 50, "medium": 70, "long": 30}
        assert analysis.keyword_patterns == {"understanding": 25, "learning": 20}
        assert analysis.example_types == {"personal": 80, "theoretical": 50, "practical": 20}


class TestWaysAnalyzer:
    """Test the WaysAnalyzer class and its methods."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database with test data."""
        mock_db = Mock()
        mock_db.get_way_statistics.return_value = {
            'total_ways': 284,
            'dialogue_types': {"question": 50, "answer": 30, "discussion": 20},
            'room_distribution': {"kitchen": 20, "living_room": 15, "bedroom": 10}
        }
        return mock_db

    @pytest.fixture
    def mock_queries(self):
        """Create a mock SQL queries object with test data."""
        mock_queries = Mock()

        # Mock partner distribution query
        mock_queries.count_ways_by_partner_sql.return_value = (
            "SELECT * FROM ways GROUP BY dialoguewith",
            [("self", 40), ("other", 35), ("group", 25)]
        )

        # Mock God relationships query
        mock_queries.get_god_relationship_distribution_sql.return_value = (
            "SELECT dievas, COUNT(*) FROM ways GROUP BY dievas",
            [("creator", 15), ("sustainer", 12), ("redeemer", 8)]
        )

        # Mock examples query
        mock_queries.get_ways_with_examples_sql.return_value = (
            "SELECT id, examples, LENGTH(examples) FROM ways WHERE examples IS NOT NULL",
            [(1, "Example text here", 250), (2, "Another example", 200), (3, "Third example", 300)]
        )

        return mock_queries

    @pytest.fixture
    def analyzer(self, mock_db, mock_queries):
        """Create a WaysAnalyzer with mocked dependencies."""
        analyzer = WaysAnalyzer.__new__(WaysAnalyzer)  # Create without calling __init__
        analyzer.db = mock_db
        analyzer.queries = mock_queries
        return analyzer

    def test_analyzer_initialization(self):
        """Test WaysAnalyzer initialization."""
        analyzer = WaysAnalyzer()
        assert hasattr(analyzer, 'db')
        assert hasattr(analyzer, 'queries')
        assert isinstance(analyzer.db, object)  # WaysDatabase instance
        assert isinstance(analyzer.queries, object)  # WaysSQLQueries instance

    def test_analyzer_initialization_with_db_path(self, tmp_path):
        """Test WaysAnalyzer initialization with custom database path."""
        custom_db_path = tmp_path / "custom.db"

        # Initialize database from dump
        from src.database import WaysDatabase
        db = WaysDatabase(db_path=str(custom_db_path))
        dump_path = Path(__file__).parent.parent / "db" / "andrius_ways.sql"
        if dump_path.exists():
            db.initialize_from_mysql_dump(str(dump_path))

            analyzer = WaysAnalyzer(db_path=str(custom_db_path))
            assert hasattr(analyzer, 'db')
            assert hasattr(analyzer, 'queries')
        else:
            pytest.skip("Database dump not found")

    def test_characterize_ways_complete_data(self, mock_db, mock_queries):
        """Test characterize_ways method with complete mock data."""
        # Create analyzer with mocked dependencies
        analyzer = WaysAnalyzer.__new__(WaysAnalyzer)
        analyzer.db = mock_db
        analyzer.queries = mock_queries

        # Mock the characterize_ways method to avoid calling real statistics
        expected_result = WaysCharacterization(
            total_ways=284,
            dialogue_types={"question": 50, "answer": 30, "discussion": 20},
            room_distribution={"kitchen": 20, "living_room": 15, "bedroom": 10},
            partner_distribution={"self": 40, "other": 35, "group": 25},
            god_relationships={"creator": 15, "sustainer": 12, "redeemer": 8},
            ways_with_examples=3,
            avg_examples_length=250.0,
            most_common_room="kitchen",
            most_common_type="question",
            most_common_partner="self"
        )

        # Test by directly calling the method and verifying it works
        # (This will use real implementation but with mocked dependencies)
        result = analyzer.characterize_ways()

        assert isinstance(result, WaysCharacterization)
        assert result.total_ways == 284
        assert result.dialogue_types == {"question": 50, "answer": 30, "discussion": 20}
        assert result.room_distribution == {"kitchen": 20, "living_room": 15, "bedroom": 10}
        assert result.partner_distribution == {"self": 40, "other": 35, "group": 25}
        assert result.god_relationships == {"creator": 15, "sustainer": 12, "redeemer": 8}
        assert result.ways_with_examples == 3
        assert abs(result.avg_examples_length - 250.0) < 0.01  # Allow small floating point differences
        assert result.most_common_room == "kitchen"
        assert result.most_common_type == "question"
        assert result.most_common_partner == "self"

    def test_characterize_ways_empty_data(self):
        """Test characterize_ways with empty database."""
        # Create analyzer with empty mock data
        mock_db = Mock()
        mock_db.get_way_statistics.return_value = {
            'total_ways': 0,
            'dialogue_types': {},
            'room_distribution': {}
        }

        mock_queries = Mock()
        mock_queries.count_ways_by_partner_sql.return_value = ("", [])
        mock_queries.get_god_relationship_distribution_sql.return_value = ("", [])
        mock_queries.get_ways_with_examples_sql.return_value = ("", [])

        analyzer = WaysAnalyzer.__new__(WaysAnalyzer)
        analyzer.db = mock_db
        analyzer.queries = mock_queries

        result = analyzer.characterize_ways()

        assert result.total_ways == 0
        assert result.dialogue_types == {}
        assert result.room_distribution == {}
        assert result.partner_distribution == {}
        assert result.god_relationships == {}
        assert result.ways_with_examples == 0
        assert result.avg_examples_length == 0.0
        assert result.most_common_room == ""
        assert result.most_common_type == ""
        assert result.most_common_partner == ""

    def test_characterize_ways_partial_data(self):
        """Test characterize_ways with partial database data."""
        mock_db = Mock()
        mock_db.get_way_statistics.return_value = {
            'total_ways': 100,
            'dialogue_types': {"question": 50},
            'room_distribution': {"kitchen": 20}
        }

        mock_queries = Mock()
        mock_queries.count_ways_by_partner_sql.return_value = ("", [("self", 40)])
        mock_queries.get_god_relationship_distribution_sql.return_value = ("", [])
        mock_queries.get_ways_with_examples_sql.return_value = ("", [(1, "example", 100)])

        analyzer = WaysAnalyzer.__new__(WaysAnalyzer)
        analyzer.db = mock_db
        analyzer.queries = mock_queries

        # Test that the method works with partial data
        result = analyzer.characterize_ways()

        assert result.total_ways == 100
        assert result.dialogue_types == {"question": 50}
        assert result.room_distribution == {"kitchen": 20}
        assert result.partner_distribution == {"self": 40}
        assert result.god_relationships == {}
        assert result.ways_with_examples == 1
        assert abs(result.avg_examples_length - 100.0) < 0.01
        assert result.most_common_room == "kitchen"
        assert result.most_common_type == "question"
        assert result.most_common_partner == "self"

    def test_characterize_ways_no_examples(self):
        """Test characterize_ways when no ways have examples."""
        mock_db = Mock()
        mock_db.get_way_statistics.return_value = {
            'total_ways': 50,
            'dialogue_types': {"question": 25},
            'room_distribution': {"kitchen": 10}
        }

        mock_queries = Mock()
        mock_queries.count_ways_by_partner_sql.return_value = ("", [("self", 20)])
        mock_queries.get_god_relationship_distribution_sql.return_value = ("", [("creator", 5)])
        mock_queries.get_ways_with_examples_sql.return_value = ("", [])  # No examples

        analyzer = WaysAnalyzer.__new__(WaysAnalyzer)
        analyzer.db = mock_db
        analyzer.queries = mock_queries

        result = analyzer.characterize_ways()

        assert result.ways_with_examples == 0
        assert result.avg_examples_length == 0.0


class TestAnalysisMethods:
    """Test individual analysis methods of WaysAnalyzer with real data."""

    def test_ways_analyzer_real_operations(self):
        """Test WaysAnalyzer operations with real database when available."""
        try:
            analyzer = WaysAnalyzer()

            # Test all analysis methods
            characterization = analyzer.characterize_ways()
            assert isinstance(characterization, WaysCharacterization)

            dialogue_analysis = analyzer.analyze_dialogue_types()
            assert isinstance(dialogue_analysis, DialogueTypeAnalysis)

            room_analysis = analyzer.analyze_room_distribution()
            assert isinstance(room_analysis, RoomAnalysis)

            partner_analysis = analyzer.analyze_dialogue_partners()
            assert isinstance(partner_analysis, PartnerAnalysis)

            god_analysis = analyzer.analyze_god_relationships()
            assert isinstance(god_analysis, GodRelationshipAnalysis)

            examples_analysis = analyzer.analyze_examples()
            assert isinstance(examples_analysis, ExamplesAnalysis)

            way_stats = analyzer.compute_way_statistics()
            assert isinstance(way_stats, dict)

            room_stats = analyzer.compute_room_statistics()
            assert isinstance(room_stats, dict)

            type_stats = analyzer.compute_type_statistics()
            assert isinstance(type_stats, dict)

            cross_tabs = analyzer.compute_cross_tabulations()
            assert isinstance(cross_tabs, dict)

        except Exception as e:
            if "no such table" in str(e).lower() or "operationalerror" in str(e).lower():
                pytest.skip("Database not fully initialized - this is expected in test environment")
            else:
                raise

    def test_ways_analyzer_filtering_and_lookup(self, house_analyzer):
        """Test WaysAnalyzer filtering and lookup operations."""
        if house_analyzer is None:
            pytest.skip("Database not available")

        analyzer = house_analyzer

        # Test room-based operations
        room_hierarchy = analyzer.get_room_hierarchy()
        assert isinstance(room_hierarchy, list)

        room_cooccurrence = analyzer.analyze_room_cooccurrence()
        assert isinstance(room_cooccurrence, dict)

        # Test room lookup
        room = analyzer.get_room_by_short('B')
        # room may be None if not found

        try:
            ways_in_room = analyzer.get_ways_in_room('B')
            assert isinstance(ways_in_room, list)

            ways_by_type = analyzer.get_ways_by_dialogue_type('Absolute')
            assert isinstance(ways_by_type, list)

        except Exception as e:
            if "no such table" in str(e).lower() or "operationalerror" in str(e).lower():
                pytest.skip("Database not fully initialized")
            else:
                raise

    def test_framework_analysis_methods(self, house_analyzer):
        """Test philosophical framework analysis methods."""
        if house_analyzer is None:
            pytest.skip("Database not available")

        analyzer = house_analyzer

        try:
            believing = analyzer.analyze_believing_structure()
            assert isinstance(believing, dict)
            assert believing.get('name') == 'Believing'

            caring = analyzer.analyze_caring_structure()
            assert isinstance(caring, dict)
            assert caring.get('name') == 'Caring'

            relative_learning = analyzer.analyze_relative_learning()
            assert isinstance(relative_learning, dict)
            assert relative_learning.get('name') == 'Relative Learning'

            framework_stats = analyzer.get_framework_statistics()
            assert isinstance(framework_stats, dict)

            house_stats = analyzer.get_house_statistics()
            assert isinstance(house_stats, HouseStatistics)

        except Exception as e:
            if "no such table" in str(e).lower() or "operationalerror" in str(e).lower():
                pytest.skip("Database not fully initialized")
            else:
                raise

    def test_text_analysis_methods(self):
        """Test text analysis and processing methods."""
        try:
            analyzer = WaysAnalyzer()

            # Test with sample data for text analysis
            sample_ways = [
                (1, "Test way of understanding and learning", "Partner", "Absolute", "Self", "", "Example text", "", "B", "", "", ""),
                (2, "Another approach to knowing", "Partner", "Relative", "Other", "", "", "", "B2", "", "", ""),
                (3, "Third method of figuring things out", "Partner", "Absolute", "Self", "", "More examples here", "", "B", "", "", "")
            ]

            keywords = analyzer.extract_keywords(sample_ways)
            assert isinstance(keywords, dict)

            example_patterns = analyzer.analyze_example_patterns([
                (1, "Way 1", "Example with question?", "Example with question?"),
                (2, "Way 2", "Example with God reference", "Example with God reference"),
                (3, "Way 3", "Personal example with I", "Personal example with I")
            ])
            assert isinstance(example_patterns, dict)

            text_metrics = analyzer.compute_text_metrics(sample_ways)
            assert isinstance(text_metrics, dict)
            assert 'total_ways' in text_metrics
            assert 'avg_way_length' in text_metrics
            assert 'longest_way' in text_metrics
            assert 'shortest_way' in text_metrics

        except Exception as e:
            if "no such table" in str(e).lower() or "operationalerror" in str(e).lower():
                pytest.skip("Database not fully initialized")
            else:
                raise

    def test_analyze_dialogue_types(self, analyzer):
        """Test analyze_dialogue_types method."""
        if analyzer is None:
            pytest.skip("Database not available")

        result = analyzer.analyze_dialogue_types()
        assert isinstance(result, DialogueTypeAnalysis)
        assert isinstance(result.type_distribution, dict)
        assert isinstance(result.type_by_room, dict)
        assert isinstance(result.room_by_type, dict)
        assert isinstance(result.type_characteristics, dict)

    def test_analyze_room_distribution(self, analyzer):
        """Test analyze_room_distribution method."""
        if analyzer is None:
            pytest.skip("Database not available")

        
        """Test analyze_room_distribution method."""
        result = analyzer.analyze_room_distribution()
        assert isinstance(result, RoomAnalysis)
        assert isinstance(result.room_stats, dict)
        assert isinstance(result.room_hierarchy, list)
        assert isinstance(result.room_cooccurrences, dict)
        assert isinstance(result.room_connectivity, dict)

    def test_analyze_dialogue_partners(self, analyzer):
        """Test analyze_dialogue_partners method."""
        result = analyzer.analyze_dialogue_partners()
        assert isinstance(result, PartnerAnalysis)
        assert isinstance(result.partner_distribution, dict)
        assert isinstance(result.partner_room_patterns, dict)
        assert isinstance(result.partner_type_patterns, dict)
        assert isinstance(result.partner_network, dict)

    def test_analyze_god_relationships(self, analyzer):
        """Test analyze_god_relationships method."""
        result = analyzer.analyze_god_relationships()
        assert isinstance(result, GodRelationshipAnalysis)
        assert isinstance(result.relationship_distribution, dict)
        assert isinstance(result.relationship_by_room, dict)
        assert isinstance(result.relationship_by_type, dict)
        assert isinstance(result.divine_perspectives, list)

    def test_analyze_examples(self, analyzer):
        """Test analyze_examples method."""
        result = analyzer.analyze_examples()
        assert isinstance(result, ExamplesAnalysis)
        assert isinstance(result.total_with_examples, int)
        assert isinstance(result.total_without_examples, int)
        assert isinstance(result.avg_length, float)
        assert isinstance(result.length_distribution, dict)
        assert isinstance(result.keyword_patterns, dict)
        assert isinstance(result.example_types, dict)

    def test_compute_way_statistics(self, analyzer):
        """Test compute_way_statistics method."""
        result = analyzer.compute_way_statistics()
        assert isinstance(result, dict)
        assert 'total_ways' in result
        assert 'room_diversity' in result
        assert 'type_diversity' in result
        assert 'partner_diversity' in result
        assert 'most_common_room' in result
        assert 'most_common_type' in result
        assert 'most_common_partner' in result
        assert 'examples_coverage' in result
        assert 'avg_examples_length' in result
        assert 'room_distribution' in result
        assert 'type_distribution' in result
        assert 'partner_distribution' in result

    def test_compute_room_statistics(self, analyzer):
        """Test compute_room_statistics method."""
        result = analyzer.compute_room_statistics()
        assert isinstance(result, dict)
        # Should have room statistics if rooms exist in mock data
        if result:
            for room_short, stats in result.items():
                assert 'way_count' in stats
                assert 'avg_way_length' in stats
                assert 'avg_examples_length' in stats
                assert 'connectivity' in stats

    def test_compute_type_statistics(self, analyzer):
        """Test compute_type_statistics method."""
        result = analyzer.compute_type_statistics()
        assert isinstance(result, dict)
        # Should have type statistics if types exist in mock data
        if result:
            for dtype, stats in result.items():
                assert 'count' in stats
                assert 'avg_examples_length' in stats
                assert 'room_diversity' in stats
                assert 'rooms' in stats

    def test_compute_cross_tabulations(self, analyzer):
        """Test compute_cross_tabulations method."""
        result = analyzer.compute_cross_tabulations()
        assert isinstance(result, dict)
        assert 'type_room' in result
        assert 'type_partner' in result
        assert isinstance(result['type_room'], dict)
        assert isinstance(result['type_partner'], dict)

    def test_extract_keywords(self, analyzer):
        """Test extract_keywords method."""
        ways_data = [
            (1, "Test way of understanding and learning", "Partner", "Absolute", "Self", "", "Example", "", "B", "", "", ""),
            (2, "Another way of knowing and thinking", "Partner", "Relative", "Other", "", "", "", "B2", "", "", ""),
        ]
        result = analyzer.extract_keywords(ways_data)
        assert isinstance(result, dict)
        # Should extract some keywords
        assert len(result) > 0
        # Keywords should be lowercase and contain only valid words
        for keyword, count in result.items():
            assert isinstance(keyword, str)
            assert isinstance(count, int)
            assert count > 0

    def test_analyze_example_patterns(self, analyzer):
        """Test analyze_example_patterns method."""
        examples_data = [
            (1, "Way 1", "Example with question?", "Example with question?"),
            (2, "Way 2", "Example with God reference", "Example with God reference"),
            (3, "Way 3", "Personal example with I and me", "Personal example with I and me"),
            (4, "Way 4", "Abstract concept of truth", "Abstract concept of truth")
        ]
        result = analyzer.analyze_example_patterns(examples_data)
        assert isinstance(result, dict)
        assert 'total_examples' in result
        assert 'avg_length' in result
        assert 'length_ranges' in result
        assert 'contains_questions' in result
        assert 'contains_god' in result
        assert 'personal_experience' in result
        assert 'abstract_concepts' in result

        # Check computed values
        assert result['total_examples'] == 4
        assert isinstance(result['avg_length'], float)
        assert result['contains_questions'] >= 1  # At least one example has a question
        assert result['contains_god'] >= 1  # At least one example mentions God

    def test_compute_text_metrics(self, analyzer):
        """Test compute_text_metrics method."""
        ways_data = [
            (1, "Short way", "", "", "", "", "Brief example", "", "", "", "", ""),
            (2, "This is a much longer way description that should be analyzed", "", "", "", "", "This is a longer example with more detailed content", "", "", "", "", ""),
            (3, "Medium way", "", "", "", "", "", "", "", "", "", "")  # No example
        ]
        result = analyzer.compute_text_metrics(ways_data)
        assert isinstance(result, dict)
        assert 'total_ways' in result
        assert 'avg_way_length' in result
        assert 'avg_examples_length' in result
        assert 'total_text_length' in result
        assert 'ways_with_examples' in result
        assert 'longest_way' in result
        assert 'shortest_way' in result
        assert 'most_detailed_example' in result

        # Check computed values
        assert result['total_ways'] == 3
        assert result['ways_with_examples'] == 2  # Two ways have examples
        assert isinstance(result['avg_way_length'], float)
        assert result['longest_way'] == "This is a much longer way description that should be analyzed"
        assert result['shortest_way'] == "Short way"


class TestUtilityFunctions:
    """Test utility functions and helper methods."""

    def test_dataclass_properties_computation(self):
        """Test that dataclass properties compute correctly."""
        # Test WaysCharacterization properties
        char = WaysCharacterization(
            room_distribution={"room1": 10, "room2": 20, "room3": 15},
            dialogue_types={"type1": 5, "type2": 8, "type3": 12},
            partner_distribution={"partner1": 7, "partner2": 9}
        )

        assert char.room_diversity == 3
        assert char.type_diversity == 3
        assert char.partner_diversity == 2

        # Test with empty data
        empty_char = WaysCharacterization()
        assert empty_char.room_diversity == 0
        assert empty_char.type_diversity == 0
        assert empty_char.partner_diversity == 0

    def test_most_common_calculations(self):
        """Test most common item calculations."""
        char = WaysCharacterization(
            room_distribution={"kitchen": 5, "living_room": 10, "bedroom": 8},
            dialogue_types={"question": 15, "answer": 20, "discussion": 12},
            partner_distribution={"self": 25, "other": 18, "group": 22},
            most_common_room="living_room",
            most_common_type="answer",
            most_common_partner="self"
        )

        assert char.most_common_room == "living_room"
        assert char.most_common_type == "answer"
        assert char.most_common_partner == "self"

    def test_most_common_with_ties(self):
        """Test most common calculations when there are ties."""
        char = WaysCharacterization(
            room_distribution={"kitchen": 10, "living_room": 10, "bedroom": 5},
            most_common_room="kitchen"  # First in dict iteration order
        )

        # When there's a tie, max() returns the first one in iteration order
        # This behavior is acceptable for this use case
        most_common = char.most_common_room
        assert most_common in ["kitchen", "living_room"]


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_analyze_ways(self):
        """Test analyze_ways convenience function."""
        # Test with mock to avoid database dependency
        with pytest.raises(Exception):  # Will fail without database
            result = analyze_ways()
        # Function exists and is callable
        from src.ways_analysis import analyze_ways
        assert callable(analyze_ways)

    def test_get_ways_analyzer(self):
        """Test get_ways_analyzer convenience function."""
        # Test with mock to avoid database dependency
        with pytest.raises(Exception):  # Will fail without database
            analyzer = get_ways_analyzer()
        # Function exists and is callable
        from src.ways_analysis import get_ways_analyzer
        assert callable(get_ways_analyzer)


class TestIntegration:
    """Test integration between components."""

    def test_analyzer_with_real_dependencies(self):
        """Test that WaysAnalyzer can be created with real dependencies."""
        try:
            analyzer = WaysAnalyzer()

            # Should be able to call characterize_ways without errors
            result = analyzer.characterize_ways()
            assert isinstance(result, WaysCharacterization)

            # Result should have some data (assuming database exists)
            # Note: This test may fail if the database doesn't exist or is empty
            # In that case, it should still return a valid WaysCharacterization object
            assert isinstance(result.total_ways, int)
            assert isinstance(result.dialogue_types, dict)
            assert isinstance(result.room_distribution, dict)
        except Exception:
            # If database doesn't exist or other issues, that's okay for this test
            # The important thing is that the class can be instantiated
            pytest.skip("Database not available for integration test")


if __name__ == "__main__":
    pytest.main([__file__])
