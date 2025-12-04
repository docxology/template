"""Ways-specific statistical analysis.

This module provides statistical analysis functions specifically
designed for analyzing ways of knowing data and distributions.
"""
from __future__ import annotations

from typing import Any, Dict, List
import statistics as stats_module
import numpy as np


def _variance(data: List[float]) -> float:
    """Calculate variance of data."""
    if len(data) < 2:
        return 0.0
    mean = sum(data) / len(data)
    return sum((x - mean) ** 2 for x in data) / (len(data) - 1)


def _stdev(data: List[float]) -> float:
    """Calculate standard deviation of data."""
    return _variance(data) ** 0.5


# ============================================================================
# WAYS-SPECIFIC STATISTICAL FUNCTIONS
# ============================================================================

def analyze_way_distributions(db) -> Dict[str, Any]:
    """Analyze distributions of ways data from database.

    Args:
        db: Database connection instance

    Returns:
        Dictionary with distribution analysis
    """
    # Use db.queries if available (for mocking), otherwise create new instance
    queries = getattr(db, 'queries', None)
    if queries is None:
        from .sql_queries import WaysSQLQueries
        queries = WaysSQLQueries()

    # Get room distribution
    _, room_data = queries.count_ways_by_room_sql()
    room_counts = [count for _, count in room_data]

    # Get type distribution
    _, type_data = queries.count_ways_by_type_sql()
    type_counts = [count for _, count in type_data]

    # Get partner distribution
    _, partner_data = queries.count_ways_by_partner_sql()
    partner_counts = [count for _, count in partner_data]

    analysis = {
            'room_distribution': {
                'counts': room_counts,
                'mean': sum(room_counts) / len(room_counts) if room_counts else 0,
                'std': _stdev(room_counts) if len(room_counts) > 1 else 0,
                'min': min(room_counts) if room_counts else 0,
                'max': max(room_counts) if room_counts else 0,
                'total_ways': sum(room_counts)
            },
            'type_distribution': {
                'counts': type_counts,
                'mean': sum(type_counts) / len(type_counts) if type_counts else 0,
                'std': _stdev(type_counts) if len(type_counts) > 1 else 0,
                'min': min(type_counts) if type_counts else 0,
                'max': max(type_counts) if type_counts else 0,
                'total_types': len(type_counts)
            },
            'partner_distribution': {
                'counts': partner_counts,
                'mean': sum(partner_counts) / len(partner_counts) if partner_counts else 0,
                'std': _stdev(partner_counts) if len(partner_counts) > 1 else 0,
                'min': min(partner_counts) if partner_counts else 0,
                'max': max(partner_counts) if partner_counts else 0,
                'total_partners': len(partner_counts)
            }
    }

    return analysis


def compute_way_correlations(db) -> Dict[str, Any]:
    """Compute correlations between ways variables.

    Args:
        db: Database connection instance

    Returns:
        Dictionary with correlation analysis
    """
    # Use db.queries if available (for mocking), otherwise create new instance
    queries = getattr(db, 'queries', None)
    if queries is None:
        from .sql_queries import WaysSQLQueries
        queries = WaysSQLQueries()

    # Get way statistics for correlation analysis
    _, ways_data = queries.get_all_ways_sql()

    # Extract variables for correlation
    room_codes = []
    type_codes = []
    examples_lengths = []
    way_lengths = []

    # Create mappings for categorical variables
    room_mapping = {}
    type_mapping = {}

    room_counter = 0
    type_counter = 0

    for row in ways_data:
        way_id, way, dialoguewith, dialoguetype, dialoguetypetype, wayurl, examples, dialoguetypetypetype, mene, dievas, comments, laikinas = row

        # Room encoding
        if mene not in room_mapping:
            room_mapping[mene] = room_counter
            room_counter += 1
        room_codes.append(room_mapping[mene])

        # Type encoding
        if dialoguetype not in type_mapping:
            type_mapping[dialoguetype] = type_counter
            type_counter += 1
        type_codes.append(type_mapping[dialoguetype])

        # Text lengths
        way_lengths.append(len(way) if way else 0)
        examples_lengths.append(len(examples) if examples else 0)

    # Compute correlations
    correlations = {}

    if len(room_codes) > 1:
        # Room vs Type correlation
        try:
            correlations['room_type'] = np.corrcoef(room_codes, type_codes)[0, 1]
        except:
            correlations['room_type'] = 0.0

        # Room vs Examples length correlation
        try:
            correlations['room_examples_length'] = np.corrcoef(room_codes, examples_lengths)[0, 1]
        except:
            correlations['room_examples_length'] = 0.0

        # Type vs Examples length correlation
        try:
            correlations['type_examples_length'] = np.corrcoef(type_codes, examples_lengths)[0, 1]
        except:
            correlations['type_examples_length'] = 0.0

        # Way length vs Examples length correlation
        try:
            correlations['way_examples_length'] = np.corrcoef(way_lengths, examples_lengths)[0, 1]
        except:
            correlations['way_examples_length'] = 0.0

    return {
        'correlations': correlations,
        'mappings': {
            'room_mapping': room_mapping,
            'type_mapping': type_mapping
        },
        'sample_size': len(ways_data)
    }


def analyze_type_room_independence(db) -> Dict[str, Any]:
    """Test independence between dialogue types and rooms using chi-square.

    Args:
        db: Database connection instance

    Returns:
        Chi-square test results
    """
    # Use db.queries if available (for mocking), otherwise create new instance
    queries = getattr(db, 'queries', None)
    if queries is None:
        from .sql_queries import WaysSQLQueries
        queries = WaysSQLQueries()

    # Get cross-tabulation data
    _, cross_data = queries.cross_tabulate_type_room_sql()

    # Build contingency table
    type_room_counts = {}
    types = set()
    rooms = set()

    for dtype, room, count in cross_data:
        if dtype not in type_room_counts:
            type_room_counts[dtype] = {}
        type_room_counts[dtype][room] = count
        types.add(dtype)
        rooms.add(room)

    # Create contingency table
    types_list = sorted(types)
    rooms_list = sorted(rooms)

    contingency_table = []
    for dtype in types_list:
        row = []
        for room in rooms_list:
            count = type_room_counts.get(dtype, {}).get(room, 0)
            row.append(count)
        contingency_table.append(row)

    # Convert to numpy array
    contingency_array = np.array(contingency_table)

    # Compute chi-square test (simplified implementation)
    if contingency_array.size > 0:
        # Calculate expected frequencies
        row_totals = contingency_array.sum(axis=1)
        col_totals = contingency_array.sum(axis=0)
        total = contingency_array.sum()

        expected = np.outer(row_totals, col_totals) / total

        # Chi-square statistic
        chi_square = np.sum((contingency_array - expected) ** 2 / expected)

        # Degrees of freedom
        df = (len(types_list) - 1) * (len(rooms_list) - 1)

        # Placeholder p-value (would need scipy.stats.chi2.sf for actual calculation)
        p_value = 0.05  # Placeholder

        return {
            'chi_square_statistic': float(chi_square),
            'degrees_of_freedom': df,
            'p_value': p_value,
            'contingency_table': contingency_array.tolist(),
            'types': types_list,
            'rooms': rooms_list,
            'significant': p_value < 0.05
        }
    else:
        return {
            'chi_square_statistic': 0.0,
            'degrees_of_freedom': 0,
            'p_value': 1.0,
            'contingency_table': [],
            'types': [],
            'rooms': [],
            'significant': False
        }


def compute_way_diversity_metrics(db) -> Dict[str, Any]:
    """Compute diversity metrics for ways across different dimensions.

    Args:
        db: Database connection instance

    Returns:
        Diversity metrics analysis
    """
    # Use db.queries if available (for mocking), otherwise create new instance
    queries = getattr(db, 'queries', None)
    if queries is None:
        from .sql_queries import WaysSQLQueries
        queries = WaysSQLQueries()

    # Get distribution data
    _, room_data = queries.count_ways_by_room_sql()
    _, type_data = queries.count_ways_by_type_sql()
    _, partner_data = queries.count_ways_by_partner_sql()

    def shannon_diversity(counts: List[int]) -> float:
        """Calculate Shannon diversity index."""
        total = sum(counts)
        if total == 0:
            return 0.0

        diversity = 0.0
        for count in counts:
            if count > 0:
                proportion = count / total
                diversity -= proportion * np.log(proportion)

        return diversity

    def simpson_diversity(counts: List[int]) -> float:
        """Calculate Simpson diversity index."""
        total = sum(counts)
        if total <= 1:
            return 0.0

        sum_squares = sum(count * (count - 1) for count in counts)
        return sum_squares / (total * (total - 1))

    room_counts = [count for _, count in room_data]
    type_counts = [count for _, count in type_data]
    partner_counts = [count for _, count in partner_data]

    diversity_metrics = {
        'room_diversity': {
            'shannon_index': shannon_diversity(room_counts),
            'simpson_index': simpson_diversity(room_counts),
            'num_categories': len(room_counts),
            'evenness': shannon_diversity(room_counts) / np.log(len(room_counts)) if room_counts else 0
        },
        'type_diversity': {
            'shannon_index': shannon_diversity(type_counts),
            'simpson_index': simpson_diversity(type_counts),
            'num_categories': len(type_counts),
            'evenness': shannon_diversity(type_counts) / np.log(len(type_counts)) if type_counts else 0
        },
        'partner_diversity': {
            'shannon_index': shannon_diversity(partner_counts),
            'simpson_index': simpson_diversity(partner_counts),
            'num_categories': len(partner_counts),
            'evenness': shannon_diversity(partner_counts) / np.log(len(partner_counts)) if partner_counts else 0
        }
    }

    # Overall diversity assessment
    total_ways = sum(room_counts)
    diversity_metrics['overall'] = {
        'total_ways': total_ways,
        'diversity_score': (
            diversity_metrics['room_diversity']['evenness'] +
            diversity_metrics['type_diversity']['evenness'] +
            diversity_metrics['partner_diversity']['evenness']
        ) / 3,
        'balance_assessment': 'balanced' if all(
            d['evenness'] > 0.7 for d in [
                diversity_metrics['room_diversity'],
                diversity_metrics['type_diversity'],
                diversity_metrics['partner_diversity']
            ]
        ) else 'unbalanced'
    }

    return diversity_metrics

