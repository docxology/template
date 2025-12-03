"""Ways of Figuring Things Out - Comprehensive Analysis Module.

This module provides domain-specific analysis functions for Andrius Kulikauskas's
philosophical framework of ways of figuring things out. It replaces the generic
example.py module with focused analysis of the 284 ways, 24 rooms, and
dialogue patterns in the House of Knowledge.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter, defaultdict
import statistics
from pathlib import Path

from .database import WaysDatabase
from .sql_queries import WaysSQLQueries


@dataclass
class WaysCharacterization:
    """Complete characterization of ways data."""
    total_ways: int = 0
    dialogue_types: Dict[str, int] = field(default_factory=dict)
    room_distribution: Dict[str, int] = field(default_factory=dict)
    partner_distribution: Dict[str, int] = field(default_factory=dict)
    god_relationships: Dict[str, int] = field(default_factory=dict)
    ways_with_examples: int = 0
    avg_examples_length: float = 0.0
    most_common_room: str = ""
    most_common_type: str = ""
    most_common_partner: str = ""

    @property
    def room_diversity(self) -> int:
        """Number of different rooms used."""
        return len(self.room_distribution)

    @property
    def type_diversity(self) -> int:
        """Number of different dialogue types."""
        return len(self.dialogue_types)

    @property
    def partner_diversity(self) -> int:
        """Number of different dialogue partners."""
        return len(self.partner_distribution)


@dataclass
class DialogueTypeAnalysis:
    """Analysis of dialogue types and their patterns."""
    type_distribution: Dict[str, int] = field(default_factory=dict)
    type_by_room: Dict[str, Dict[str, int]] = field(default_factory=dict)
    room_by_type: Dict[str, Dict[str, int]] = field(default_factory=dict)
    type_characteristics: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class RoomAnalysis:
    """Analysis of rooms in the House of Knowledge."""
    room_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    room_hierarchy: List[str] = field(default_factory=list)
    room_cooccurrences: Dict[str, List[str]] = field(default_factory=dict)
    room_connectivity: Dict[str, int] = field(default_factory=dict)


@dataclass
class PartnerAnalysis:
    """Analysis of dialogue partners."""
    partner_distribution: Dict[str, int] = field(default_factory=dict)
    partner_room_patterns: Dict[str, Dict[str, int]] = field(default_factory=dict)
    partner_type_patterns: Dict[str, Dict[str, int]] = field(default_factory=dict)
    partner_network: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class GodRelationshipAnalysis:
    """Analysis of God relationships in ways."""
    relationship_distribution: Dict[str, int] = field(default_factory=dict)
    relationship_by_room: Dict[str, Dict[str, int]] = field(default_factory=dict)
    relationship_by_type: Dict[str, Dict[str, int]] = field(default_factory=dict)
    divine_perspectives: List[str] = field(default_factory=list)


@dataclass
class ExamplesAnalysis:
    """Analysis of examples in ways."""
    total_with_examples: int = 0
    total_without_examples: int = 0
    avg_length: float = 0.0
    length_distribution: Dict[str, int] = field(default_factory=dict)
    keyword_patterns: Dict[str, int] = field(default_factory=dict)
    example_types: Dict[str, int] = field(default_factory=dict)


class WaysAnalyzer:
    """Main analyzer for ways of figuring things out."""

    def __init__(self, db_path: str = None):
        """Initialize analyzer with database connection."""
        self.db = WaysDatabase(db_path)
        self.queries = WaysSQLQueries(db_path)

    def characterize_ways(self) -> WaysCharacterization:
        """Complete characterization of all ways."""
        # Get basic statistics
        stats = self.db.get_way_statistics()

        characterization = WaysCharacterization(
            total_ways=stats['total_ways'],
            dialogue_types=stats['dialogue_types'],
            room_distribution=stats['room_distribution']
        )

        # Get partner distribution
        _, partner_results = self.queries.count_ways_by_partner_sql()
        characterization.partner_distribution = {row[0]: row[1] for row in partner_results}

        # Get God relationships
        _, god_results = self.queries.get_god_relationship_distribution_sql()
        characterization.god_relationships = {row[0]: row[1] for row in god_results}

        # Get examples statistics
        _, examples_results = self.queries.get_ways_with_examples_sql()
        characterization.ways_with_examples = len(examples_results)
        if examples_results:
            lengths = [row[2] for row in examples_results]
            characterization.avg_examples_length = statistics.mean(lengths)

        # Find most common categories
        if characterization.room_distribution:
            characterization.most_common_room = max(
                characterization.room_distribution.items(),
                key=lambda x: x[1]
            )[0]

        if characterization.dialogue_types:
            characterization.most_common_type = max(
                characterization.dialogue_types.items(),
                key=lambda x: x[1]
            )[0]

        if characterization.partner_distribution:
            characterization.most_common_partner = max(
                characterization.partner_distribution.items(),
                key=lambda x: x[1]
            )[0]

        return characterization

    def analyze_dialogue_types(self) -> DialogueTypeAnalysis:
        """Analyze dialogue types and their patterns."""
        analysis = DialogueTypeAnalysis()

        # Get type distribution
        _, type_results = self.queries.count_ways_by_type_sql()
        analysis.type_distribution = {row[0]: row[1] for row in type_results}

        # Get cross-tabulations
        _, cross_results = self.queries.cross_tabulate_type_room_sql()

        # Build type-by-room and room-by-type matrices
        for dtype, room, count in cross_results:
            if dtype not in analysis.type_by_room:
                analysis.type_by_room[dtype] = {}
            analysis.type_by_room[dtype][room] = count

            if room not in analysis.room_by_type:
                analysis.room_by_type[room] = {}
            analysis.room_by_type[room][dtype] = count

        # Analyze type characteristics
        for dtype in analysis.type_distribution.keys():
            ways_in_type = []
            query, results = self.queries.get_ways_by_dialogue_type_sql(dtype)
            for row in results:
                ways_in_type.append({
                    'id': row[0],
                    'way': row[1],
                    'room': row[8],
                    'examples_length': len(row[6]) if row[6] else 0
                })

            if ways_in_type:
                analysis.type_characteristics[dtype] = {
                    'count': len(ways_in_type),
                    'avg_examples_length': statistics.mean(w['examples_length'] for w in ways_in_type),
                    'room_diversity': len(set(w['room'] for w in ways_in_type)),
                    'rooms': list(set(w['room'] for w in ways_in_type))
                }

        return analysis

    def analyze_room_distribution(self) -> RoomAnalysis:
        """Analyze rooms in the House of Knowledge."""
        analysis = RoomAnalysis()

        # Get room statistics
        _, room_stats_results = self.queries.get_room_statistics_sql()
        for row in room_stats_results:
            room_short = row[0]
            analysis.room_stats[room_short] = {
                'full_name': row[1],
                'way_count': row[2],
                'avg_way_length': row[3] or 0,
                'avg_examples_length': row[4] or 0
            }

        # Get room hierarchy (assuming ordered by eilestvarka)
        _, rooms_results = self.queries.get_rooms_sql()
        analysis.room_hierarchy = [row[1] for row in rooms_results]  # santrumpa

        # Analyze room connectivity (ways in same room = connected)
        for room in analysis.room_stats.keys():
            connected_rooms = []
            # For now, rooms are not directly connected (ways belong to single rooms)
            # This could be extended to analyze room relationships
            analysis.room_cooccurrences[room] = connected_rooms
            analysis.room_connectivity[room] = len(connected_rooms)

        return analysis

    def analyze_dialogue_partners(self) -> PartnerAnalysis:
        """Analyze dialogue partners."""
        analysis = PartnerAnalysis()

        # Get partner distribution
        _, partner_results = self.queries.count_ways_by_partner_sql()
        analysis.partner_distribution = {row[0]: row[1] for row in partner_results}

        # Get partner-room patterns
        _, partner_room_results = self.queries.get_partner_room_relationships_sql()
        for partner, room, count in partner_room_results:
            if partner not in analysis.partner_room_patterns:
                analysis.partner_room_patterns[partner] = {}
            analysis.partner_room_patterns[partner][room] = count

        # Get partner-type patterns
        _, partner_type_results = self.queries.cross_tabulate_type_partner_sql()
        for dtype, partner, count in partner_type_results:
            if partner not in analysis.partner_type_patterns:
                analysis.partner_type_patterns[partner] = {}
            analysis.partner_type_patterns[partner][dtype] = count

        # Build partner network (partners connected through same dialogue types)
        for partner1 in analysis.partner_distribution.keys():
            connected_partners = []
            for partner2 in analysis.partner_distribution.keys():
                if partner1 != partner2:
                    # Check if they share dialogue types
                    types1 = set(analysis.partner_type_patterns.get(partner1, {}).keys())
                    types2 = set(analysis.partner_type_patterns.get(partner2, {}).keys())
                    if types1 & types2:  # Intersection
                        connected_partners.append(partner2)
            analysis.partner_network[partner1] = connected_partners

        return analysis

    def analyze_god_relationships(self) -> GodRelationshipAnalysis:
        """Analyze God relationships in ways."""
        analysis = GodRelationshipAnalysis()

        # Get relationship distribution
        _, god_results = self.queries.get_god_relationship_distribution_sql()
        analysis.relationship_distribution = {row[0]: row[1] for row in god_results}

        # Analyze relationships by room and type
        query, ways_results = self.queries.get_all_ways_sql()
        for row in ways_results:
            way_id, way, dialoguewith, dialoguetype, dialoguetypetype, wayurl, examples, dialoguetypetypetype, mene, dievas, comments, laikinas = row

            if dievas:
                # By room
                if mene not in analysis.relationship_by_room:
                    analysis.relationship_by_room[mene] = {}
                analysis.relationship_by_room[mene][dievas] = \
                    analysis.relationship_by_room[mene].get(dievas, 0) + 1

                # By type
                if dialoguetype not in analysis.relationship_by_type:
                    analysis.relationship_by_type[dialoguetype] = {}
                analysis.relationship_by_type[dialoguetype][dievas] = \
                    analysis.relationship_by_type[dialoguetype].get(dievas, 0) + 1

        # Identify divine perspectives (unique God relationships)
        analysis.divine_perspectives = list(analysis.relationship_distribution.keys())

        return analysis

    def analyze_examples(self) -> ExamplesAnalysis:
        """Analyze examples in ways."""
        analysis = ExamplesAnalysis()

        _, examples_results = self.queries.get_ways_with_examples_sql()

        analysis.total_with_examples = len(examples_results)
        analysis.total_without_examples = self.db.get_way_statistics()['total_ways'] - analysis.total_with_examples

        if examples_results:
            lengths = [row[2] for row in examples_results]
            analysis.avg_length = statistics.mean(lengths)

            # Length distribution
            for length in lengths:
                if length < 100:
                    category = "short"
                elif length < 500:
                    category = "medium"
                else:
                    category = "long"
                analysis.length_distribution[category] = \
                    analysis.length_distribution.get(category, 0) + 1

        # Analyze keyword patterns (simplified)
        keywords = ['God', 'Jesus', 'life', 'love', 'truth', 'way', 'think', 'know', 'understand']
        for keyword in keywords:
            count = 0
            for row in examples_results:
                example_text = row[3] if len(row) > 3 else ""
                if keyword.lower() in example_text.lower():
                    count += 1
            analysis.keyword_patterns[keyword] = count

        return analysis

    def compute_way_statistics(self) -> Dict[str, Any]:
        """Compute comprehensive statistics about ways."""
        characterization = self.characterize_ways()

        return {
            'total_ways': characterization.total_ways,
            'room_diversity': characterization.room_diversity,
            'type_diversity': characterization.type_diversity,
            'partner_diversity': characterization.partner_diversity,
            'most_common_room': characterization.most_common_room,
            'most_common_type': characterization.most_common_type,
            'most_common_partner': characterization.most_common_partner,
            'examples_coverage': characterization.ways_with_examples / characterization.total_ways,
            'avg_examples_length': characterization.avg_examples_length,
            'room_distribution': characterization.room_distribution,
            'type_distribution': characterization.dialogue_types,
            'partner_distribution': characterization.partner_distribution
        }

    def compute_room_statistics(self) -> Dict[str, Any]:
        """Compute statistics per room."""
        room_analysis = self.analyze_room_distribution()

        stats = {}
        for room_short, room_data in room_analysis.room_stats.items():
            stats[room_short] = {
                'full_name': room_data['full_name'],
                'way_count': room_data['way_count'],
                'avg_way_length': room_data['avg_way_length'],
                'avg_examples_length': room_data['avg_examples_length'],
                'connectivity': room_analysis.room_connectivity.get(room_short, 0)
            }

        return stats

    def compute_type_statistics(self) -> Dict[str, Any]:
        """Compute statistics per dialogue type."""
        type_analysis = self.analyze_dialogue_types()

        stats = {}
        for dtype, characteristics in type_analysis.type_characteristics.items():
            stats[dtype] = {
                'count': characteristics['count'],
                'avg_examples_length': characteristics['avg_examples_length'],
                'room_diversity': characteristics['room_diversity'],
                'rooms': characteristics['rooms']
            }

        return stats

    def compute_cross_tabulations(self) -> Dict[str, Any]:
        """Compute all cross-tabulations."""
        # Type × Room
        _, type_room_results = self.queries.cross_tabulate_type_room_sql()
        type_room = {}
        for dtype, room, count in type_room_results:
            if dtype not in type_room:
                type_room[dtype] = {}
            type_room[dtype][room] = count

        # Type × Partner
        _, type_partner_results = self.queries.cross_tabulate_type_partner_sql()
        type_partner = {}
        for dtype, partner, count in type_partner_results:
            if dtype not in type_partner:
                type_partner[dtype] = {}
            type_partner[dtype][partner] = count

        return {
            'type_room': type_room,
            'type_partner': type_partner
        }

    def extract_keywords(self, ways: List[Tuple]) -> Dict[str, int]:
        """Extract keywords from way descriptions."""
        keywords = defaultdict(int)

        common_words = {
            'way', 'ways', 'think', 'thinking', 'know', 'knowledge', 'understand',
            'understanding', 'see', 'look', 'find', 'search', 'learn', 'learning',
            'question', 'answer', 'ask', 'tell', 'show', 'make', 'take', 'give',
            'come', 'go', 'get', 'put', 'set', 'work', 'life', 'live', 'love',
            'truth', 'true', 'good', 'bad', 'right', 'wrong', 'god', 'jesus',
            'christ', 'spirit', 'soul', 'heart', 'mind', 'thought', 'feel',
            'feeling', 'sense', 'time', 'place', 'thing', 'things', 'people',
            'person', 'world', 'part', 'whole', 'one', 'two', 'three', 'four',
            'first', 'second', 'third', 'last', 'new', 'old', 'big', 'small'
        }

        for way_row in ways:
            way_text = way_row[1].lower()  # way column
            words = way_text.split()

            for word in words:
                # Clean word
                word = word.strip('.,!?()[]{}:;"\'')
                if len(word) > 2 and word not in common_words:
                    keywords[word] += 1

        # Return top keywords
        return dict(sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:20])

    def analyze_example_patterns(self, examples: List[Tuple]) -> Dict[str, Any]:
        """Analyze patterns in examples."""
        patterns = {
            'total_examples': len(examples),
            'avg_length': 0,
            'length_ranges': {'short': 0, 'medium': 0, 'long': 0},
            'contains_questions': 0,
            'contains_god': 0,
            'contains_jesus': 0,
            'personal_experience': 0,
            'abstract_concepts': 0
        }

        if examples:
            lengths = []
            for row in examples:
                if len(row) > 3:
                    example_text = row[3]
                    lengths.append(len(example_text))

                    # Pattern analysis
                    text_lower = example_text.lower()
                    if '?' in example_text:
                        patterns['contains_questions'] += 1
                    if 'god' in text_lower:
                        patterns['contains_god'] += 1
                    if 'jesus' in text_lower:
                        patterns['contains_jesus'] += 1
                    if any(word in text_lower for word in ['i', 'my', 'me', 'we', 'our']):
                        patterns['personal_experience'] += 1
                    if any(word in text_lower for word in ['truth', 'love', 'knowledge', 'understanding', 'way']):
                        patterns['abstract_concepts'] += 1

            if lengths:
                patterns['avg_length'] = statistics.mean(lengths)

                for length in lengths:
                    if length < 100:
                        patterns['length_ranges']['short'] += 1
                    elif length < 500:
                        patterns['length_ranges']['medium'] += 1
                    else:
                        patterns['length_ranges']['long'] += 1

        return patterns

    def compute_text_metrics(self, ways: List[Tuple]) -> Dict[str, Any]:
        """Compute text metrics for ways."""
        metrics = {
            'total_ways': len(ways),
            'avg_way_length': 0,
            'avg_examples_length': 0,
            'total_text_length': 0,
            'ways_with_examples': 0,
            'longest_way': '',
            'shortest_way': '',
            'most_detailed_example': ''
        }

        way_lengths = []
        example_lengths = []

        for row in ways:
            way_text = row[1]  # way column
            examples_text = row[6] if row[6] else ""  # examples column

            way_lengths.append(len(way_text))

            if examples_text:
                metrics['ways_with_examples'] += 1
                example_lengths.append(len(examples_text))
                metrics['total_text_length'] += len(way_text) + len(examples_text)

                # Track most detailed example
                if len(examples_text) > len(metrics.get('most_detailed_example', '')):
                    metrics['most_detailed_example'] = examples_text[:100] + "..."
            else:
                metrics['total_text_length'] += len(way_text)

        if way_lengths:
            metrics['avg_way_length'] = statistics.mean(way_lengths)

        if example_lengths:
            metrics['avg_examples_length'] = statistics.mean(example_lengths)

        # Find longest/shortest ways
        if ways:
            ways_with_lengths = [(row[1], len(row[1])) for row in ways]
            ways_with_lengths.sort(key=lambda x: x[1])

            metrics['shortest_way'] = ways_with_lengths[0][0]
            metrics['longest_way'] = ways_with_lengths[-1][0]

        return metrics


# Convenience functions
def analyze_ways(db_path: str = None) -> WaysCharacterization:
    """Convenience function for complete ways analysis."""
    analyzer = WaysAnalyzer(db_path)
    return analyzer.characterize_ways()


def get_ways_analyzer(db_path: str = None) -> WaysAnalyzer:
    """Get configured ways analyzer."""
    return WaysAnalyzer(db_path)
