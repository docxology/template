"""House of Knowledge Analysis Module.

This module implements analysis of Andrius Kulikauskas's House of Knowledge,
a philosophical framework with 24 rooms representing different aspects of
knowing and being. Replaces the generic simulation.py module with domain-specific
analysis of the House structure, room relationships, and philosophical frameworks.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import statistics
from pathlib import Path

from .database import WaysDatabase
from .sql_queries import WaysSQLQueries
from .models import Room, Way, HouseOfKnowledge


@dataclass
class HouseStructure:
    """Complete structure of the House of Knowledge."""
    rooms: List[Room] = field(default_factory=list)
    ways: List[Way] = field(default_factory=list)
    room_hierarchy: List[str] = field(default_factory=list)  # Ordered by eilestvarka
    room_levels: Dict[int, List[str]] = field(default_factory=dict)  # Rooms by level
    room_wings: Dict[int, List[str]] = field(default_factory=dict)  # Rooms by wing
    framework_structure: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoomRelationships:
    """Analysis of relationships between rooms."""
    adjacency_matrix: Dict[str, Dict[str, float]] = field(default_factory=dict)
    room_clusters: Dict[str, List[str]] = field(default_factory=dict)
    hierarchical_relationships: Dict[str, List[str]] = field(default_factory=dict)
    framework_connections: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class FrameworkAnalysis:
    """Analysis of philosophical frameworks within the House."""
    believing_structure: Dict[str, Any] = field(default_factory=dict)
    caring_structure: Dict[str, Any] = field(default_factory=dict)
    relative_learning: Dict[str, Any] = field(default_factory=dict)
    framework_completeness: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HouseStatistics:
    """Statistical analysis of the House."""
    total_rooms: int = 0
    total_ways: int = 0
    ways_per_room: Dict[str, int] = field(default_factory=dict)
    room_coverage: float = 0.0
    framework_balance: Dict[str, Any] = field(default_factory=dict)
    structural_integrity: Dict[str, Any] = field(default_factory=dict)


class HouseOfKnowledgeAnalyzer:
    """Analyzer for the House of Knowledge philosophical framework."""

    def __init__(self, db_path: str = None):
        """Initialize analyzer with database connection."""
        self.db = WaysDatabase(db_path)
        self.queries = WaysSQLQueries(db_path)
        self.house = self._load_house_structure()

    def _load_house_structure(self) -> HouseStructure:
        """Load complete House structure from database."""
        structure = HouseStructure()

        # Load rooms
        _, rooms_data = self.queries.get_rooms_sql()
        for row in rooms_data:
            room = Room(
                numeris=row[0],
                santrumpa=row[1],
                savoka=row[2],
                issiaiskinimas=row[3],
                eilestvarka=row[4],
                laipsnis=row[5],
                sparnas=row[6],
                rusis=row[7],
                pasnekovas=row[8],
                dievas=row[9],
                pastabos=row[10],
                label=row[11]
            )
            structure.rooms.append(room)

        # Load ways
        _, ways_data = self.queries.get_all_ways_sql()
        for row in ways_data:
            way = Way(
                id=row[0],
                way=row[1],
                dialoguewith=row[2],
                dialoguetype=row[3],
                dialoguetypetype=row[4],
                wayurl=row[5],
                examples=row[6],
                dialoguetypetypetype=row[7],
                mene=row[8],
                dievas=row[9],
                comments=row[10],
                laikinas=row[11]
            )
            structure.ways.append(way)

        # Build hierarchy
        structure.room_hierarchy = [room.santrumpa for room in
                                   sorted(structure.rooms, key=lambda r: r.eilestvarka)]

        # Group by levels and wings
        for room in structure.rooms:
            if room.laipsnis not in structure.room_levels:
                structure.room_levels[room.laipsnis] = []
            structure.room_levels[room.laipsnis].append(room.santrumpa)

            if room.sparnas not in structure.room_wings:
                structure.room_wings[room.sparnas] = []
            structure.room_wings[room.sparnas].append(room.santrumpa)

        # Analyze framework structure
        structure.framework_structure = self._analyze_framework_structure(structure)

        return structure

    def _analyze_framework_structure(self, structure: HouseStructure) -> Dict[str, Any]:
        """Analyze the structural organization of the House."""
        framework = {}

        # Identify the four main frameworks based on room patterns
        # This is based on Andrius's organization of the 24 rooms

        # Believing structure (rooms 1-4: B, B2, B3, B4)
        framework['believing'] = {
            'rooms': ['B', 'B2', 'B3', 'B4'],
            'theme': 'Faith and belief',
            'levels': [1, 2, 3, 4]
        }

        # Caring structure (rooms 5-8: 1, 10, 20, 30)
        framework['caring'] = {
            'rooms': ['1', '10', '20', '30'],
            'theme': 'Love and care',
            'levels': [1, 2, 3, 4]
        }

        # Knowing structure (rooms 9-12: 21, 31, 2, 3)
        framework['knowing'] = {
            'rooms': ['21', '31', '2', '3'],
            'theme': 'Knowledge and understanding',
            'levels': [1, 2, 3, 4]
        }

        # Making structure (rooms 13-16: 32, R, F, T)
        framework['making'] = {
            'rooms': ['32', 'R', 'F', 'T'],
            'theme': 'Creation and action',
            'levels': [1, 2, 3, 4]
        }

        return framework

    def get_house_structure(self) -> HouseStructure:
        """Get complete House structure."""
        return self.house

    def analyze_room_relationships(self) -> RoomRelationships:
        """Analyze relationships between rooms."""
        relationships = RoomRelationships()

        # Build adjacency matrix based on shared ways
        # Rooms are connected if they have ways with similar characteristics
        all_rooms = [room.santrumpa for room in self.house.rooms]

        # Initialize adjacency matrix
        for room1 in all_rooms:
            relationships.adjacency_matrix[room1] = {}
            for room2 in all_rooms:
                relationships.adjacency_matrix[room1][room2] = 0.0

        # Analyze connections through ways
        for way in self.house.ways:
            room = way.mene

            # Connect rooms that share dialogue types
            type_ways = [w for w in self.house.ways if w.dialoguetype == way.dialoguetype and w.mene != room]
            for connected_way in type_ways:
                connected_room = connected_way.mene
                relationships.adjacency_matrix[room][connected_room] += 1.0
                relationships.adjacency_matrix[connected_room][room] += 1.0

            # Connect rooms that share dialogue partners
            partner_ways = [w for w in self.house.ways if w.dialoguewith == way.dialoguewith and w.mene != room]
            for connected_way in partner_ways:
                connected_room = connected_way.mene
                relationships.adjacency_matrix[room][connected_room] += 0.5
                relationships.adjacency_matrix[connected_room][room] += 0.5

        # Normalize adjacency matrix
        for room1 in all_rooms:
            total_connections = sum(relationships.adjacency_matrix[room1].values())
            if total_connections > 0:
                for room2 in all_rooms:
                    relationships.adjacency_matrix[room1][room2] /= total_connections

        # Identify room clusters (simplified: group by wing)
        for wing, rooms in self.house.room_wings.items():
            relationships.room_clusters[f"wing_{wing}"] = rooms

        # Hierarchical relationships (based on levels)
        for level, rooms in self.house.room_levels.items():
            relationships.hierarchical_relationships[f"level_{level}"] = rooms

        # Framework connections
        for framework_name, framework_data in self.house.framework_structure.items():
            relationships.framework_connections[framework_name] = framework_data['rooms']

        return relationships

    def get_room_hierarchy(self) -> List[str]:
        """Get rooms in hierarchical order."""
        return self.house.room_hierarchy.copy()

    def analyze_room_cooccurrence(self) -> Dict[str, List[str]]:
        """Analyze which rooms have ways in common (currently single room per way)."""
        # Since each way belongs to only one room, cooccurrence is currently empty
        # This could be extended if ways could belong to multiple rooms
        cooccurrences = {}

        for room in self.house.room_hierarchy:
            cooccurrences[room] = []  # No cooccurrences currently

        return cooccurrences

    def analyze_believing_structure(self) -> Dict[str, Any]:
        """Analyze the Believing structure (rooms B, B2, B3, B4)."""
        believing_rooms = ['B', 'B2', 'B3', 'B4']
        return self._analyze_framework(believing_rooms, "Believing")

    def analyze_caring_structure(self) -> Dict[str, Any]:
        """Analyze the Caring structure (rooms 1, 10, 20, 30)."""
        caring_rooms = ['1', '10', '20', '30']
        return self._analyze_framework(caring_rooms, "Caring")

    def analyze_relative_learning(self) -> Dict[str, Any]:
        """Analyze the Relative Learning cycle."""
        # Relative learning involves rooms R, F, T in relation to each other
        relative_rooms = ['R', 'F', 'T']
        return self._analyze_framework(relative_rooms, "Relative Learning")

    def _analyze_framework(self, room_codes: List[str], framework_name: str) -> Dict[str, Any]:
        """Analyze a specific philosophical framework."""
        analysis = {
            'name': framework_name,
            'rooms': room_codes,
            'room_details': {},
            'total_ways': 0,
            'type_distribution': {},
            'partner_distribution': {},
            'structural_integrity': {}
        }

        for room_code in room_codes:
            room_ways = [w for w in self.house.ways if w.mene == room_code]
            analysis['room_details'][room_code] = {
                'way_count': len(room_ways),
                'types': list(set(w.dialoguetype for w in room_ways)),
                'partners': list(set(w.dialoguewith for w in room_ways))
            }
            analysis['total_ways'] += len(room_ways)

            # Aggregate distributions
            for way in room_ways:
                analysis['type_distribution'][way.dialoguetype] = \
                    analysis['type_distribution'].get(way.dialoguetype, 0) + 1
                analysis['partner_distribution'][way.dialoguewith] = \
                    analysis['partner_distribution'].get(way.dialoguewith, 0) + 1

        # Analyze structural integrity
        analysis['structural_integrity'] = {
            'room_coverage': len([r for r in room_codes if analysis['room_details'][r]['way_count'] > 0]) / len(room_codes),
            'type_diversity': len(analysis['type_distribution']),
            'partner_diversity': len(analysis['partner_distribution']),
            'balance_score': self._calculate_balance_score(analysis)
        }

        return analysis

    def _calculate_balance_score(self, framework_analysis: Dict[str, Any]) -> float:
        """Calculate balance score for a framework."""
        room_counts = [details['way_count'] for details in framework_analysis['room_details'].values()]
        if not room_counts or sum(room_counts) == 0:
            return 0.0

        # Balance is based on even distribution of ways across rooms
        avg_ways = sum(room_counts) / len(room_counts) if room_counts else 0
        if avg_ways == 0:
            return 0.0

        # Calculate variance manually
        variance = sum((x - avg_ways) ** 2 for x in room_counts) / (len(room_counts) - 1) if len(room_counts) > 1 else 0
        balance_score = 1.0 / (1.0 + variance / (avg_ways ** 2))

        return balance_score

    def get_framework_statistics(self) -> Dict[str, Any]:
        """Get comprehensive framework statistics."""
        framework_stats = {}

        # Analyze all frameworks
        frameworks = {
            'believing': self.analyze_believing_structure(),
            'caring': self.analyze_caring_structure(),
            'relative_learning': self.analyze_relative_learning()
        }

        for name, analysis in frameworks.items():
            framework_stats[name] = {
                'total_ways': analysis['total_ways'],
                'room_coverage': analysis['structural_integrity']['room_coverage'],
                'type_diversity': analysis['structural_integrity']['type_diversity'],
                'balance_score': analysis['structural_integrity']['balance_score'],
                'room_details': analysis['room_details']
            }

        # Overall House statistics
        framework_stats['house_overall'] = {
            'total_rooms': len(self.house.rooms),
            'total_ways': len(self.house.ways),
            'frameworks_analyzed': len(frameworks),
            'avg_ways_per_room': len(self.house.ways) / len(self.house.rooms) if self.house.rooms else 0,
            'room_coverage': len([r for r in self.house.room_hierarchy
                                if any(w.mene == r for w in self.house.ways)]) / len(self.house.room_hierarchy)
        }

        return framework_stats

    def get_house_statistics(self) -> HouseStatistics:
        """Get comprehensive House statistics."""
        house_stats = HouseStatistics(
            total_rooms=len(self.house.rooms),
            total_ways=len(self.house.ways)
        )

        # Ways per room
        for room in self.house.room_hierarchy:
            house_stats.ways_per_room[room] = len([w for w in self.house.ways if w.mene == room])

        # Room coverage
        occupied_rooms = sum(1 for count in house_stats.ways_per_room.values() if count > 0)
        house_stats.room_coverage = occupied_rooms / house_stats.total_rooms if house_stats.total_rooms > 0 else 0

        # Framework balance
        framework_stats = self.get_framework_statistics()
        house_stats.framework_balance = {
            name: analysis['balance_score']
            for name, analysis in framework_stats.items()
            if name != 'house_overall'
        }

        # Structural integrity
        house_stats.structural_integrity = {
            'all_rooms_have_ways': all(count > 0 for count in house_stats.ways_per_room.values()),
            'balanced_distribution': self._assess_distribution_balance(house_stats.ways_per_room),
            'framework_integrity': self._assess_framework_integrity(framework_stats)
        }

        return house_stats

    def _assess_distribution_balance(self, ways_per_room: Dict[str, int]) -> Dict[str, Any]:
        """Assess how balanced the way distribution is across rooms."""
        counts = list(ways_per_room.values())
        if not counts:
            return {'balanced': False, 'variance': 0, 'assessment': 'no_data'}

        mean_count = sum(counts) / len(counts) if counts else 0
        if len(counts) > 1:
            variance = sum((x - mean_count) ** 2 for x in counts) / (len(counts) - 1)
            std_dev = variance ** 0.5
        else:
            variance = 0
            std_dev = 0

        # Assess balance
        cv = std_dev / mean_count if mean_count > 0 else 0  # Coefficient of variation
        balanced = cv < 0.5  # Less than 50% variation

        assessment = 'balanced' if balanced else 'unbalanced'
        if cv > 1.0:
            assessment = 'highly_unbalanced'

        return {
            'balanced': balanced,
            'mean_ways_per_room': mean_count,
            'variance': variance,
            'std_dev': std_dev,
            'coefficient_of_variation': cv,
            'assessment': assessment
        }

    def _assess_framework_integrity(self, framework_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the integrity of philosophical frameworks."""
        integrity = {}

        for framework_name, framework_data in framework_stats.items():
            if framework_name == 'house_overall':
                continue

            integrity[framework_name] = {
                'has_ways': framework_data['total_ways'] > 0,
                'room_coverage': framework_data['room_coverage'],
                'balance_score': framework_data['balance_score'],
                'type_diversity': framework_data['type_diversity'],
                'overall_integrity': (
                    framework_data['room_coverage'] * 0.4 +
                    min(framework_data['balance_score'], 1.0) * 0.4 +
                    min(framework_data['type_diversity'] / 10, 1.0) * 0.2
                )
            }

        return integrity

    def get_room_by_short(self, short_name: str) -> Optional[Room]:
        """Get room by short name."""
        for room in self.house.rooms:
            if room.santrumpa == short_name:
                return room
        return None

    def get_ways_in_room(self, room_short: str) -> List[Way]:
        """Get all ways in a specific room."""
        return [way for way in self.house.ways if way.mene == room_short]

    def get_ways_by_dialogue_type(self, dialogue_type: str) -> List[Way]:
        """Get ways by dialogue type."""
        return [way for way in self.house.ways if way.dialoguetype == dialogue_type]

    def create_house_model(self) -> HouseOfKnowledge:
        """Create HouseOfKnowledge model instance."""
        return HouseOfKnowledge(
            rooms=self.house.rooms.copy(),
            ways=self.house.ways.copy()
        )


# Convenience functions
def analyze_house(db_path: str = None) -> HouseStatistics:
    """Convenience function for complete House analysis."""
    analyzer = HouseOfKnowledgeAnalyzer(db_path)
    return analyzer.get_house_statistics()


def get_house_analyzer(db_path: str = None) -> HouseOfKnowledgeAnalyzer:
    """Get configured House analyzer."""
    return HouseOfKnowledgeAnalyzer(db_path)
