"""Comprehensive tests for models.py module.

Tests dataclass definitions, enums, and conversion functions for the ways of
figuring things out philosophical framework.
"""

import pytest
from unittest.mock import Mock

from src.models import (
    DialogueType, DialogueTypeType, Way, Room, Question, Example,
    WaysStatistics, HouseOfKnowledge, way_from_sqlalchemy,
    room_from_sqlalchemy, question_from_sqlalchemy, example_from_sqlalchemy
)


class TestWayDataclass:
    """Test Way dataclass functionality."""

    def test_way_initialization(self):
        """Test Way dataclass basic initialization."""
        way = Way(
            id=1,
            way="Test way of figuring things out",
            dialoguewith="Partner",
            dialoguetype="Absolute",
            dialoguetypetype="Self",
            wayurl="http://example.com",
            examples="Example text here",
            dialoguetypetypetype="Direct",
            mene="B",
            dievas="Creator",
            comments="Test comment",
            laikinas="Temporary"
        )

        assert way.id == 1
        assert way.way == "Test way of figuring things out"
        assert way.dialoguewith == "Partner"
        assert way.dialoguetype == "Absolute"
        assert way.mene == "B"
        assert way.room is None  # Default value

    def test_way_dialogue_type_enum(self):
        """Test dialogue_type_enum property."""
        # Valid dialogue type
        way = Way(
            id=1, way="Test", dialoguewith="Partner",
            dialoguetype="Absolute", dialoguetypetype="Self",
            wayurl="", examples="", dialoguetypetypetype="",
            mene="B", dievas="", comments="", laikinas=""
        )
        assert way.dialogue_type_enum == DialogueType.ABSOLUTE

        # Invalid dialogue type
        way_invalid = Way(
            id=1, way="Test", dialoguewith="Partner",
            dialoguetype="Invalid", dialoguetypetype="Self",
            wayurl="", examples="", dialoguetypetypetype="",
            mene="B", dievas="", comments="", laikinas=""
        )
        assert way_invalid.dialogue_type_enum is None

    def test_way_dialogue_type_type_enum(self):
        """Test dialogue_type_type_enum property."""
        # Valid sub-type
        way = Way(
            id=1, way="Test", dialoguewith="Partner",
            dialoguetype="Absolute", dialoguetypetype="Self",
            wayurl="", examples="", dialoguetypetypetype="",
            mene="B", dievas="", comments="", laikinas=""
        )
        assert way.dialogue_type_type_enum == DialogueTypeType.SELF

        # Invalid sub-type
        way_invalid = Way(
            id=1, way="Test", dialoguewith="Partner",
            dialoguetype="Absolute", dialoguetypetype="Invalid",
            wayurl="", examples="", dialoguetypetypetype="",
            mene="B", dievas="", comments="", laikinas=""
        )
        assert way_invalid.dialogue_type_type_enum is None

    def test_way_room_short_property(self):
        """Test room_short property."""
        way = Way(
            id=1, way="Test", dialoguewith="Partner",
            dialoguetype="Absolute", dialoguetypetype="Self",
            wayurl="", examples="", dialoguetypetypetype="",
            mene="B2", dievas="", comments="", laikinas=""
        )
        assert way.room_short == "B2"

    def test_way_has_examples_property(self):
        """Test has_examples property."""
        # With examples
        way_with = Way(
            id=1, way="Test", dialoguewith="Partner",
            dialoguetype="Absolute", dialoguetypetype="Self",
            wayurl="", examples="Some example text", dialoguetypetypetype="",
            mene="B", dievas="", comments="", laikinas=""
        )
        assert way_with.has_examples is True

        # Without examples
        way_without = Way(
            id=1, way="Test", dialoguewith="Partner",
            dialoguetype="Absolute", dialoguetypetype="Self",
            wayurl="", examples="", dialoguetypetypetype="",
            mene="B", dievas="", comments="", laikinas=""
        )
        assert way_without.has_examples is False

        # With whitespace-only examples
        way_whitespace = Way(
            id=1, way="Test", dialoguewith="Partner",
            dialoguetype="Absolute", dialoguetypetype="Self",
            wayurl="", examples="   ", dialoguetypetypetype="",
            mene="B", dievas="", comments="", laikinas=""
        )
        assert way_whitespace.has_examples is False

    def test_way_repr(self):
        """Test Way __repr__ method."""
        way = Way(
            id=1, way="This is a very long way description that should be truncated",
            dialoguewith="Partner", dialoguetype="Absolute", dialoguetypetype="Self",
            wayurl="", examples="", dialoguetypetypetype="",
            mene="B", dievas="", comments="", laikinas=""
        )
        repr_str = repr(way)
        assert "Way(id=1," in repr_str
        assert "way='This is a very long way descri..." in repr_str
        assert "room='B'" in repr_str


class TestRoomDataclass:
    """Test Room dataclass functionality."""

    def test_room_initialization(self):
        """Test Room dataclass basic initialization."""
        room = Room(
            numeris=1,
            santrumpa="B",
            savoka="Believing",
            issiaiskinimas="Basic belief",
            eilestvarka=1,
            laipsnis=1,
            sparnas=1,
            rusis="Primary",
            pasnekovas="Self",
            dievas="Creator",
            pastabos="Notes",
            label="B"
        )

        assert room.numeris == 1
        assert room.santrumpa == "B"
        assert room.savoka == "Believing"
        assert room.eilestvarka == 1
        assert room.ways == []  # Default value

    def test_room_properties(self):
        """Test all Room property methods."""
        room = Room(
            numeris=1,
            santrumpa="B",
            savoka="Believing",
            issiaiskinimas="Basic belief",
            eilestvarka=1,
            laipsnis=1,
            sparnas=1,
            rusis="Primary",
            pasnekovas="Self",
            dievas="Creator",
            pastabos="Notes",
            label="B"
        )

        assert room.short_name == "B"
        assert room.concept_name == "Believing"
        assert room.explanation == "Basic belief"
        assert room.order == 1
        assert room.level == 1
        assert room.wing == 1
        assert room.room_type == "Primary"
        assert room.conversant == "Self"
        assert room.god_aspect == "Creator"
        assert room.notes == "Notes"

    def test_room_repr(self):
        """Test Room __repr__ method."""
        room = Room(
            numeris=1,
            santrumpa="B",
            savoka="Believing",
            issiaiskinimas="Basic belief",
            eilestvarka=1,
            laipsnis=1,
            sparnas=1,
            rusis="Primary",
            pasnekovas="Self",
            dievas="Creator",
            pastabos="Notes",
            label="B"
        )
        repr_str = repr(room)
        assert "Room(1: 'B' - Believing)" in repr_str


class TestQuestionDataclass:
    """Test Question dataclass functionality."""

    def test_question_initialization(self):
        """Test Question dataclass basic initialization."""
        question = Question(
            klausimonr=1,
            klausimas="What is knowledge?",
            mastytojas="Thinker",
            svetaine="http://example.com",
            pasisakymas="Knowledge is understanding",
            patarimas="Seek wisdom",
            menes="B"
        )

        assert question.klausimonr == 1
        assert question.klausimas == "What is knowledge?"
        assert question.menes == "B"
        assert question.ways == []  # Default value

    def test_question_properties(self):
        """Test all Question property methods."""
        question = Question(
            klausimonr=1,
            klausimas="What is knowledge?",
            mastytojas="Thinker",
            svetaine="http://example.com",
            pasisakymas="Knowledge is understanding",
            patarimas="Seek wisdom",
            menes="B"
        )

        assert question.question_number == 1
        assert question.question == "What is knowledge?"
        assert question.thinker == "Thinker"
        assert question.website == "http://example.com"
        assert question.statement == "Knowledge is understanding"
        assert question.advice == "Seek wisdom"
        assert question.room == "B"

    def test_question_repr(self):
        """Test Question __repr__ method."""
        question = Question(
            klausimonr=1,
            klausimas="What is knowledge? This is a very long question that should be truncated",
            mastytojas="Thinker",
            svetaine="http://example.com",
            pasisakymas="Knowledge is understanding",
            patarimas="Seek wisdom",
            menes="B"
        )
        repr_str = repr(question)
        assert "Question(1: 'What is knowledge? This is a very long question th..." in repr_str


class TestExampleDataclass:
    """Test Example dataclass functionality."""

    def test_example_initialization(self):
        """Test Example dataclass basic initialization."""
        example = Example(
            id=1,
            way="Test way",
            rusis="Personal",
            pavyzdziai="Example text"
        )

        assert example.id == 1
        assert example.way == "Test way"
        assert example.rusis == "Personal"
        assert example.pavyzdziai == "Example text"

    def test_example_properties(self):
        """Test all Example property methods."""
        example = Example(
            id=1,
            way="Test way",
            rusis="Personal",
            pavyzdziai="Example text"
        )

        assert example.way_name == "Test way"
        assert example.category == "Personal"
        assert example.example_text == "Example text"

    def test_example_repr(self):
        """Test Example __repr__ method."""
        example = Example(
            id=1,
            way="This is a very long way name that should be truncated",
            rusis="Personal",
            pavyzdziai="Example text"
        )
        repr_str = repr(example)
        assert "Example('This is a very long way name t..." in repr_str
        assert "Personal)" in repr_str


class TestWaysStatistics:
    """Test WaysStatistics dataclass."""

    def test_statistics_initialization(self):
        """Test WaysStatistics basic initialization."""
        stats = WaysStatistics(
            total_ways=100,
            dialogue_type_counts={"Absolute": 50, "Relative": 30},
            room_counts={"B": 20, "B2": 15},
            ways_with_examples=75,
            average_examples_length=250.5
        )

        assert stats.total_ways == 100
        assert stats.dialogue_type_counts == {"Absolute": 50, "Relative": 30}
        assert stats.room_counts == {"B": 20, "B2": 15}
        assert stats.ways_with_examples == 75
        assert stats.average_examples_length == 250.5

    def test_most_common_dialogue_type(self):
        """Test most_common_dialogue_type property."""
        stats = WaysStatistics(
            dialogue_type_counts={"Absolute": 50, "Relative": 30, "Embrace God": 20}
        )
        assert stats.most_common_dialogue_type == "Absolute"

        # Empty stats
        empty_stats = WaysStatistics()
        assert empty_stats.most_common_dialogue_type is None

    def test_most_populated_room(self):
        """Test most_populated_room property."""
        stats = WaysStatistics(
            room_counts={"B": 20, "B2": 15, "B3": 25}
        )
        assert stats.most_populated_room == "B3"

        # Empty stats
        empty_stats = WaysStatistics()
        assert empty_stats.most_populated_room is None


class TestHouseOfKnowledge:
    """Test HouseOfKnowledge dataclass."""

    def test_house_initialization(self):
        """Test HouseOfKnowledge basic initialization."""
        house = HouseOfKnowledge(
            rooms=[],
            ways=[]
        )

        assert house.rooms == []
        assert house.ways == []
        assert house.total_rooms == 0
        assert house.total_ways == 0

    def test_house_with_data(self):
        """Test HouseOfKnowledge with sample data."""
        room = Room(1, "B", "Believing", "Basic belief", 1, 1, 1, "Primary", "Self", "Creator", "Notes", "B")
        way = Way(1, "Test way", "Partner", "Absolute", "Self", "", "Example", "", "B", "", "", "")

        house = HouseOfKnowledge(
            rooms=[room],
            ways=[way]
        )

        assert house.total_rooms == 1
        assert house.total_ways == 1

    def test_get_room_by_short(self):
        """Test get_room_by_short method."""
        room1 = Room(1, "B", "Believing", "Basic belief", 1, 1, 1, "Primary", "Self", "Creator", "Notes", "B")
        room2 = Room(2, "B2", "Believing 2", "Advanced belief", 2, 2, 1, "Secondary", "Other", "Sustainer", "Notes", "B2")

        house = HouseOfKnowledge(
            rooms=[room1, room2],
            ways=[]
        )

        assert house.get_room_by_short("B") == room1
        assert house.get_room_by_short("B2") == room2
        assert house.get_room_by_short("Nonexistent") is None

    def test_get_ways_in_room(self):
        """Test get_ways_in_room method."""
        way1 = Way(1, "Way 1", "Partner", "Absolute", "Self", "", "Example", "", "B", "", "", "")
        way2 = Way(2, "Way 2", "Partner", "Absolute", "Self", "", "Example", "", "B", "", "", "")
        way3 = Way(3, "Way 3", "Partner", "Absolute", "Self", "", "Example", "", "B2", "", "", "")

        house = HouseOfKnowledge(
            rooms=[],
            ways=[way1, way2, way3]
        )

        b_ways = house.get_ways_in_room("B")
        b2_ways = house.get_ways_in_room("B2")

        assert len(b_ways) == 2
        assert len(b2_ways) == 1
        assert way1 in b_ways
        assert way2 in b_ways
        assert way3 in b2_ways

    def test_get_ways_by_dialogue_type(self):
        """Test get_ways_by_dialogue_type method."""
        way1 = Way(1, "Way 1", "Partner", "Absolute", "Self", "", "Example", "", "B", "", "", "")
        way2 = Way(2, "Way 2", "Partner", "Relative", "Self", "", "Example", "", "B", "", "", "")
        way3 = Way(3, "Way 3", "Partner", "Absolute", "Self", "", "Example", "", "B2", "", "", "")

        house = HouseOfKnowledge(
            rooms=[],
            ways=[way1, way2, way3]
        )

        absolute_ways = house.get_ways_by_dialogue_type("Absolute")
        relative_ways = house.get_ways_by_dialogue_type("Relative")

        assert len(absolute_ways) == 2
        assert len(relative_ways) == 1
        assert way1 in absolute_ways
        assert way3 in absolute_ways
        assert way2 in relative_ways

    def test_get_statistics(self):
        """Test get_statistics method."""
        way1 = Way(1, "Way 1", "Partner A", "Absolute", "Self", "", "Example 1", "", "B", "", "", "")
        way2 = Way(2, "Way 2", "Partner B", "Relative", "Other", "", "Example 2", "", "B2", "", "", "")

        house = HouseOfKnowledge(
            rooms=[],
            ways=[way1, way2]
        )

        stats = house.get_statistics()

        assert isinstance(stats, WaysStatistics)
        assert stats.total_ways == 2
        assert stats.dialogue_type_counts == {"Absolute": 1, "Relative": 1}
        assert stats.room_counts == {"B": 1, "B2": 1}
        assert stats.ways_with_examples == 2
        assert stats.average_examples_length == (len("Example 1") + len("Example 2")) / 2


class TestConversionFunctions:
    """Test SQLAlchemy conversion functions."""

    def test_way_from_sqlalchemy(self):
        """Test way_from_sqlalchemy conversion."""
        # Mock SQLAlchemy Way object
        mock_sql_way = Mock()
        mock_sql_way.id = 1
        mock_sql_way.way = "Test way"
        mock_sql_way.dialoguewith = "Partner"
        mock_sql_way.dialoguetype = "Absolute"
        mock_sql_way.dialoguetypetype = "Self"
        mock_sql_way.wayurl = "http://example.com"
        mock_sql_way.examples = "Example text"
        mock_sql_way.dialoguetypetypetype = "Direct"
        mock_sql_way.mene = "B"
        mock_sql_way.dievas = "Creator"
        mock_sql_way.comments = "Comment"
        mock_sql_way.laikinas = "Temporary"

        way = way_from_sqlalchemy(mock_sql_way)

        assert isinstance(way, Way)
        assert way.id == 1
        assert way.way == "Test way"
        assert way.mene == "B"

    def test_room_from_sqlalchemy(self):
        """Test room_from_sqlalchemy conversion."""
        mock_sql_room = Mock()
        mock_sql_room.numeris = 1
        mock_sql_room.santrumpa = "B"
        mock_sql_room.savoka = "Believing"
        mock_sql_room.issiaiskinimas = "Basic belief"
        mock_sql_room.eilestvarka = 1
        mock_sql_room.laipsnis = 1
        mock_sql_room.sparnas = 1
        mock_sql_room.rusis = "Primary"
        mock_sql_room.pasnekovas = "Self"
        mock_sql_room.dievas = "Creator"
        mock_sql_room.pastabos = "Notes"
        mock_sql_room.label = "B"

        room = room_from_sqlalchemy(mock_sql_room)

        assert isinstance(room, Room)
        assert room.numeris == 1
        assert room.santrumpa == "B"
        assert room.savoka == "Believing"

    def test_question_from_sqlalchemy(self):
        """Test question_from_sqlalchemy conversion."""
        mock_sql_question = Mock()
        mock_sql_question.klausimonr = 1
        mock_sql_question.klausimas = "What is knowledge?"
        mock_sql_question.mastytojas = "Thinker"
        mock_sql_question.svetaine = "http://example.com"
        mock_sql_question.pasisakymas = "Knowledge is understanding"
        mock_sql_question.patarimas = "Seek wisdom"
        mock_sql_question.menes = "B"

        question = question_from_sqlalchemy(mock_sql_question)

        assert isinstance(question, Question)
        assert question.klausimonr == 1
        assert question.klausimas == "What is knowledge?"
        assert question.menes == "B"

    def test_example_from_sqlalchemy(self):
        """Test example_from_sqlalchemy conversion."""
        mock_sql_example = Mock()
        mock_sql_example.id = 1
        mock_sql_example.way = "Test way"
        mock_sql_example.rusis = "Personal"
        mock_sql_example.pavyzdziai = "Example text"

        example = example_from_sqlalchemy(mock_sql_example)

        assert isinstance(example, Example)
        assert example.id == 1
        assert example.way == "Test way"
        assert example.rusis == "Personal"


class TestEnums:
    """Test enum classes."""

    def test_dialogue_type_enum(self):
        """Test DialogueType enum values."""
        assert DialogueType.ABSOLUTE.value == "Absolute"
        assert DialogueType.RELATIVE.value == "Relative"
        assert DialogueType.EMBRACE_GOD.value == "Embrace God"

        # Test all values
        assert len(DialogueType) == 3

    def test_dialogue_type_type_enum(self):
        """Test DialogueTypeType enum values."""
        assert DialogueTypeType.SELF.value == "Self"
        assert DialogueTypeType.OTHER.value == "Other"
        assert DialogueTypeType.PERSON.value == "Person"
        assert DialogueTypeType.STRUCTURE.value == "Structure"
        assert DialogueTypeType.BRIDGE.value == "Bridge"
        assert DialogueTypeType.TAKING_A_STAND.value == "Take a stand"
        assert DialogueTypeType.FOLLOW_THROUGH.value == "Follow through"
        assert DialogueTypeType.REFLECT.value == "Reflect"

        # Test all values
        assert len(DialogueTypeType) == 8


class TestModelIntegration:
    """Test model integration and relationships."""

    def test_way_room_relationship(self):
        """Test that Way can reference Room."""
        room = Room(1, "B", "Believing", "Basic belief", 1, 1, 1, "Primary", "Self", "Creator", "Notes", "B")
        way = Way(1, "Test way", "Partner", "Absolute", "Self", "", "Example", "", "B", "", "", "")

        # In the dataclass, room is initially None but can be set
        way.room = room
        assert way.room == room
        assert way.room.santrumpa == "B"

    def test_question_ways_relationship(self):
        """Test Question-ways relationship."""
        way = Way(1, "Test way", "Partner", "Absolute", "Self", "", "Example", "", "B", "", "", "")
        question = Question(1, "What is knowledge?", "Thinker", "http://example.com",
                          "Knowledge is understanding", "Seek wisdom", "B")

        # Ways list starts empty and can be populated
        question.ways.append(way)
        assert len(question.ways) == 1
        assert question.ways[0] == way

    def test_room_ways_relationship(self):
        """Test Room-ways relationship."""
        way = Way(1, "Test way", "Partner", "Absolute", "Self", "", "Example", "", "B", "", "", "")
        room = Room(1, "B", "Believing", "Basic belief", 1, 1, 1, "Primary", "Self", "Creator", "Notes", "B")

        # Ways list starts empty and can be populated
        room.ways.append(way)
        assert len(room.ways) == 1
        assert room.ways[0] == way

    def test_house_model_comprehensive(self):
        """Test comprehensive HouseOfKnowledge model."""
        # Create sample data
        room1 = Room(1, "B", "Believing", "Basic belief", 1, 1, 1, "Primary", "Self", "Creator", "Notes", "B")
        room2 = Room(2, "B2", "Believing 2", "Advanced belief", 2, 2, 1, "Secondary", "Other", "Sustainer", "Notes", "B2")

        way1 = Way(1, "Way 1", "Partner A", "Absolute", "Self", "", "Example 1", "", "B", "", "", "")
        way2 = Way(2, "Way 2", "Partner B", "Relative", "Other", "", "Example 2", "", "B", "", "", "")
        way3 = Way(3, "Way 3", "Partner A", "Absolute", "Self", "", "Example 3", "", "B2", "", "", "")

        house = HouseOfKnowledge(
            rooms=[room1, room2],
            ways=[way1, way2, way3]
        )

        # Test comprehensive functionality
        assert house.total_rooms == 2
        assert house.total_ways == 3

        # Test room lookup
        assert house.get_room_by_short("B") == room1
        assert house.get_room_by_short("B2") == room2

        # Test way filtering
        b_ways = house.get_ways_in_room("B")
        b2_ways = house.get_ways_in_room("B2")
        assert len(b_ways) == 2  # way1, way2
        assert len(b2_ways) == 1  # way3

        absolute_ways = house.get_ways_by_dialogue_type("Absolute")
        relative_ways = house.get_ways_by_dialogue_type("Relative")
        assert len(absolute_ways) == 2  # way1, way3
        assert len(relative_ways) == 1  # way2

        # Test statistics
        stats = house.get_statistics()
        assert stats.total_ways == 3
        assert stats.dialogue_type_counts["Absolute"] == 2
        assert stats.room_counts["B"] == 2


if __name__ == "__main__":
    pytest.main([__file__])
