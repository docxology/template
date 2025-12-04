"""Data models for Ways of Figuring Things Out research.

Provides dataclass definitions and type-safe interfaces for working with
ways, rooms, questions, and other entities in the philosophical framework.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class DialogueType(Enum):
    """Dialogue types in the ways framework."""
    ABSOLUTE = "Absolute"
    RELATIVE = "Relative"
    EMBRACE_GOD = "Embrace God"


class DialogueTypeType(Enum):
    """Sub-types of dialogue."""
    SELF = "Self"
    OTHER = "Other"
    PERSON = "Person"
    STRUCTURE = "Structure"
    BRIDGE = "Bridge"
    TAKING_A_STAND = "Take a stand"
    FOLLOW_THROUGH = "Follow through"
    REFLECT = "Reflect"


@dataclass
class Way:
    """A way of figuring things out.

    Represents one of Andrius Kulikauskas's 284 ways of figuring things out,
    including its dialogue context, examples, and philosophical categorization.
    """
    id: int
    way: str
    dialoguewith: str
    dialoguetype: str
    dialoguetypetype: str
    wayurl: str
    examples: str
    dialoguetypetypetype: str
    mene: str  # Room short name
    dievas: str  # God relationship
    comments: str
    laikinas: str

    # Derived properties
    room: Optional['Room'] = field(default=None, init=False)

    @property
    def dialogue_type_enum(self) -> Optional[DialogueType]:
        """Get dialogue type as enum."""
        try:
            return DialogueType(self.dialoguetype)
        except ValueError:
            return None

    @property
    def dialogue_type_type_enum(self) -> Optional[DialogueTypeType]:
        """Get dialogue sub-type as enum."""
        try:
            return DialogueTypeType(self.dialoguetypetype)
        except ValueError:
            return None

    @property
    def room_short(self) -> str:
        """Get room short name."""
        return self.mene

    @property
    def has_examples(self) -> bool:
        """Check if way has examples."""
        return bool(self.examples.strip())

    def __repr__(self) -> str:
        return f"Way(id={self.id}, way='{self.way[:30]}...', room='{self.mene}')"


@dataclass
class Room:
    """A room in the House of Knowledge.

    Represents one of the 24 rooms in Andrius's philosophical framework,
    each representing a different aspect of knowing and being.
    """
    numeris: int
    santrumpa: str  # Short name
    savoka: str     # Concept name
    issiaiskinimas: str  # Explanation
    eilestvarka: int    # Order
    laipsnis: int       # Level
    sparnas: int        # Wing
    rusis: str         # Type
    pasnekovas: str    # Conversant
    dievas: str        # God aspect
    pastabos: str      # Notes
    label: str

    # Derived properties
    ways: List[Way] = field(default_factory=list, init=False)

    @property
    def short_name(self) -> str:
        """Get short name."""
        return self.santrumpa

    @property
    def concept_name(self) -> str:
        """Get concept name."""
        return self.savoka

    @property
    def explanation(self) -> str:
        """Get explanation."""
        return self.issiaiskinimas

    @property
    def order(self) -> int:
        """Get ordering number."""
        return self.eilestvarka

    @property
    def level(self) -> int:
        """Get level in hierarchy."""
        return self.laipsnis

    @property
    def wing(self) -> int:
        """Get wing (left/right in house structure)."""
        return self.sparnas

    @property
    def room_type(self) -> str:
        """Get room type."""
        return self.rusis

    @property
    def conversant(self) -> str:
        """Get the conversant (who is being addressed)."""
        return self.pasnekovas

    @property
    def god_aspect(self) -> str:
        """Get the aspect of God represented."""
        return self.dievas

    @property
    def notes(self) -> str:
        """Get additional notes."""
        return self.pastabos

    def __repr__(self) -> str:
        return f"Room({self.numeris}: '{self.santrumpa}' - {self.savoka})"


@dataclass
class Question:
    """A question in the philosophical framework.

    Represents questions that people ask, along with answers and advice.
    """
    klausimonr: int
    klausimas: str
    mastytojas: str
    svetaine: str
    pasisakymas: str
    patarimas: str
    menes: str

    # Derived properties
    ways: List[Way] = field(default_factory=list, init=False)

    @property
    def question_number(self) -> int:
        """Get question number."""
        return self.klausimonr

    @property
    def question(self) -> str:
        """Get the question text."""
        return self.klausimas

    @property
    def thinker(self) -> str:
        """Get the thinker who asked the question."""
        return self.mastytojas

    @property
    def website(self) -> str:
        """Get associated website."""
        return self.svetaine

    @property
    def statement(self) -> str:
        """Get the statement/response."""
        return self.pasisakymas

    @property
    def advice(self) -> str:
        """Get the advice given."""
        return self.patarimas

    @property
    def room(self) -> str:
        """Get associated room."""
        return self.menes

    def __repr__(self) -> str:
        return f"Question({self.klausimonr}: '{self.klausimas[:50]}...')"


@dataclass
class Example:
    """An example from the philosophical framework.

    Represents categorized examples of ways in practice.
    """
    id: int
    way: str
    rusis: str
    pavyzdziai: str

    @property
    def way_name(self) -> str:
        """Get way name."""
        return self.way

    @property
    def category(self) -> str:
        """Get category/type."""
        return self.rusis

    @property
    def example_text(self) -> str:
        """Get example text."""
        return self.pavyzdziai

    def __repr__(self) -> str:
        return f"Example('{self.way[:30]}...' - {self.rusis})"


@dataclass
class WaysStatistics:
    """Statistics about the ways collection."""
    total_ways: int = 0
    dialogue_type_counts: Dict[str, int] = field(default_factory=dict)
    room_counts: Dict[str, int] = field(default_factory=dict)
    ways_with_examples: int = 0
    average_examples_length: float = 0.0

    @property
    def most_common_dialogue_type(self) -> Optional[str]:
        """Get most common dialogue type."""
        if not self.dialogue_type_counts:
            return None
        return max(self.dialogue_type_counts.items(), key=lambda x: x[1])[0]

    @property
    def most_populated_room(self) -> Optional[str]:
        """Get room with most ways."""
        if not self.room_counts:
            return None
        return max(self.room_counts.items(), key=lambda x: x[1])[0]


@dataclass
class HouseOfKnowledge:
    """Complete representation of the House of Knowledge."""
    rooms: List[Room] = field(default_factory=list)
    ways: List[Way] = field(default_factory=list)

    def get_room_by_short(self, short_name: str) -> Optional[Room]:
        """Get room by short name."""
        for room in self.rooms:
            if room.santrumpa == short_name:
                return room
        return None

    def get_ways_in_room(self, room_short: str) -> List[Way]:
        """Get all ways in a specific room."""
        return [way for way in self.ways if way.mene == room_short]

    def get_ways_by_dialogue_type(self, dialogue_type: str) -> List[Way]:
        """Get ways by dialogue type."""
        return [way for way in self.ways if way.dialoguetype == dialogue_type]

    def get_statistics(self) -> WaysStatistics:
        """Compute statistics about the house."""
        stats = WaysStatistics()
        stats.total_ways = len(self.ways)

        # Dialogue type counts
        for way in self.ways:
            stats.dialogue_type_counts[way.dialoguetype] = \
                stats.dialogue_type_counts.get(way.dialoguetype, 0) + 1

        # Room counts
        for way in self.ways:
            stats.room_counts[way.mene] = \
                stats.room_counts.get(way.mene, 0) + 1

        # Examples statistics
        ways_with_examples = [w for w in self.ways if w.has_examples]
        stats.ways_with_examples = len(ways_with_examples)
        if ways_with_examples:
            total_length = sum(len(w.examples) for w in ways_with_examples)
            stats.average_examples_length = total_length / len(ways_with_examples)

        return stats

    @property
    def total_rooms(self) -> int:
        """Get total number of rooms."""
        return len(self.rooms)

    @property
    def total_ways(self) -> int:
        """Get total number of ways."""
        return len(self.ways)


# Utility functions for converting between SQLAlchemy models and dataclasses
def way_from_sqlalchemy(sql_way) -> Way:
    """Convert SQLAlchemy Way model to dataclass."""
    return Way(
        id=sql_way.id,
        way=sql_way.way,
        dialoguewith=sql_way.dialoguewith,
        dialoguetype=sql_way.dialoguetype,
        dialoguetypetype=sql_way.dialoguetypetype,
        wayurl=sql_way.wayurl,
        examples=sql_way.examples,
        dialoguetypetypetype=sql_way.dialoguetypetypetype,
        mene=sql_way.mene,
        dievas=sql_way.dievas,
        comments=sql_way.comments,
        laikinas=sql_way.laikinas
    )


def room_from_sqlalchemy(sql_room) -> Room:
    """Convert SQLAlchemy Room model to dataclass."""
    return Room(
        numeris=sql_room.numeris,
        santrumpa=sql_room.santrumpa,
        savoka=sql_room.savoka,
        issiaiskinimas=sql_room.issiaiskinimas,
        eilestvarka=sql_room.eilestvarka,
        laipsnis=sql_room.laipsnis,
        sparnas=sql_room.sparnas,
        rusis=sql_room.rusis,
        pasnekovas=sql_room.pasnekovas,
        dievas=sql_room.dievas,
        pastabos=sql_room.pastabos,
        label=sql_room.label
    )


def question_from_sqlalchemy(sql_question) -> Question:
    """Convert SQLAlchemy Question model to dataclass."""
    return Question(
        klausimonr=sql_question.klausimonr,
        klausimas=sql_question.klausimas,
        mastytojas=sql_question.mastytojas,
        svetaine=sql_question.svetaine,
        pasisakymas=sql_question.pasisakymas,
        patarimas=sql_question.patarimas,
        menes=sql_question.menes
    )


def example_from_sqlalchemy(sql_example) -> Example:
    """Convert SQLAlchemy Example model to dataclass."""
    return Example(
        id=sql_example.id,
        way=sql_example.way,
        rusis=sql_example.rusis,
        pavyzdziai=sql_example.pavyzdziai
    )


