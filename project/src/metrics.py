"""Ways-specific metrics calculation.

This module provides metrics specifically designed for analyzing
ways of knowing coverage, completeness, balance, and interconnectedness.
"""
from __future__ import annotations

from typing import Any, Dict


# ============================================================================
# WAYS-SPECIFIC METRICS FUNCTIONS
# ============================================================================

def compute_way_coverage_metrics(db) -> Dict[str, Any]:
    """Compute coverage metrics for ways across rooms and frameworks.

    Args:
        db: Database connection instance

    Returns:
        Coverage metrics analysis
    """
    # Use db.queries if available (for mocking), otherwise create new instance
    queries = getattr(db, 'queries', None)
    if queries is None:
        from .sql_queries import WaysSQLQueries
        queries = WaysSQLQueries()

    # Get room statistics
    _, room_stats = queries.get_room_statistics_sql()
    _, room_counts = queries.count_ways_by_room_sql()

    total_ways = sum(count for _, count in room_counts)
    occupied_rooms = sum(1 for _, count in room_counts if count > 0)

    # Calculate coverage metrics
    coverage_metrics = {
        'overall_coverage': {
            'total_ways': total_ways,
            'occupied_rooms': occupied_rooms,
            'total_rooms': len(room_stats),
            'room_coverage_ratio': occupied_rooms / len(room_stats) if room_stats else 0,
            'ways_per_room_avg': total_ways / occupied_rooms if occupied_rooms > 0 else 0
        },
        'room_coverage': {}
    }

    # Individual room coverage
    for row in room_stats:
        room_short = row[0]
        way_count = row[2]
        coverage_metrics['room_coverage'][room_short] = {
            'ways': way_count,
            'coverage_ratio': way_count / total_ways if total_ways > 0 else 0,
            'relative_to_avg': way_count / coverage_metrics['overall_coverage']['ways_per_room_avg'] if coverage_metrics['overall_coverage']['ways_per_room_avg'] > 0 else 0
        }

    return coverage_metrics


def compute_framework_completeness(db) -> Dict[str, Any]:
    """Compute completeness metrics for philosophical frameworks.

    Args:
        db: Database connection instance

    Returns:
        Framework completeness analysis
    """
    from .house_of_knowledge import HouseOfKnowledgeAnalyzer
    analyzer = HouseOfKnowledgeAnalyzer()

    framework_stats = analyzer.get_framework_statistics()

    completeness_metrics = {}

    for framework_name, stats in framework_stats.items():
        if framework_name == 'house_overall':
            continue

        completeness_metrics[framework_name] = {
            'total_ways': stats['total_ways'],
            'room_coverage': stats['room_coverage'],
            'balance_score': stats['balance_score'],
            'type_diversity': stats['type_diversity'],
            'completeness_score': (
                stats['room_coverage'] * 0.4 +
                min(stats['balance_score'], 1.0) * 0.3 +
                min(stats['type_diversity'] / 10, 1.0) * 0.3
            ),
            'room_details': stats['room_details']
        }

    # Overall completeness
    framework_completeness_scores = [m['completeness_score'] for m in completeness_metrics.values()]
    completeness_metrics['overall'] = {
        'avg_completeness': sum(framework_completeness_scores) / len(framework_completeness_scores) if framework_completeness_scores else 0,
        'frameworks_analyzed': len(completeness_metrics),
        'most_complete': max(completeness_metrics.keys(), key=lambda k: completeness_metrics[k]['completeness_score']) if completeness_metrics else None,
        'least_complete': min(completeness_metrics.keys(), key=lambda k: completeness_metrics[k]['completeness_score']) if completeness_metrics else None
    }

    return completeness_metrics


def compute_way_interconnectedness(db) -> Dict[str, Any]:
    """Compute interconnectedness metrics for ways network.

    Args:
        db: Database connection instance

    Returns:
        Network interconnectedness analysis
    """
    from .network_analysis import WaysNetworkAnalyzer
    analyzer = WaysNetworkAnalyzer()

    network = analyzer.build_ways_network()
    metrics = analyzer.compute_centrality_metrics()
    communities = analyzer.detect_communities()

    interconnectedness = {
        'network_structure': {
            'nodes': metrics.node_count,
            'edges': metrics.edge_count,
            'density': metrics.density,
            'avg_degree': metrics.average_degree,
            'connected_components': metrics.connected_components,
            'largest_component_ratio': metrics.largest_component_size / metrics.node_count if metrics.node_count > 0 else 0
        },
        'centrality_measures': {
            'degree_centralization': 0.0,  # Would need full calculation
            'betweenness_centralization': 0.0,
            'closeness_centralization': 0.0
        },
        'community_structure': {
            'communities': len(communities.communities),
            'modularity': communities.modularity,
            'largest_community': max(communities.community_sizes) if communities.community_sizes else 0,
            'community_balance': len([c for c in communities.community_sizes if c > 1]) / len(communities.community_sizes) if communities.community_sizes else 0
        },
        'interconnectedness_score': (
            metrics.density * 0.3 +
            (1.0 / metrics.connected_components if metrics.connected_components > 0 else 1.0) * 0.3 +
            communities.modularity * 0.4
        )
    }

    return interconnectedness


def compute_room_balance_metrics(db) -> Dict[str, Any]:
    """Compute balance metrics across rooms in the House of Knowledge.

    Args:
        db: Database connection instance

    Returns:
        Room balance analysis
    """
    # Use db.queries if available (for mocking), otherwise create new instance
    queries = getattr(db, 'queries', None)
    if queries is None:
        from .sql_queries import WaysSQLQueries
        queries = WaysSQLQueries()

    # Get room statistics
    _, room_stats = queries.get_room_statistics_sql()

    balance_metrics = {
        'room_distribution': {},
        'balance_analysis': {}
    }

    # Extract way counts per room
    way_counts = []
    room_names = []

    for row in room_stats:
        room_short = row[0]
        way_count = row[2]
        way_counts.append(way_count)
        room_names.append(room_short)

        balance_metrics['room_distribution'][room_short] = {
            'ways': way_count,
            'relative_weight': 0.0  # Will calculate below
        }

        # Calculate balance metrics
        if way_counts:
            total_ways = sum(way_counts)
            mean_ways = sum(way_counts) / len(way_counts)

        # Calculate relative weights
        for i, room in enumerate(room_names):
            weight = way_counts[i] / total_ways if total_ways > 0 else 0
            balance_metrics['room_distribution'][room]['relative_weight'] = weight

        # Overall balance analysis
        if len(way_counts) > 1:
            variance = sum((x - mean_ways) ** 2 for x in way_counts) / (len(way_counts) - 1)
            std_dev = variance ** 0.5
            cv = std_dev / mean_ways if mean_ways > 0 else 0  # Coefficient of variation

            balance_metrics['balance_analysis'] = {
                'mean_ways_per_room': mean_ways,
                'variance': variance,
                'std_deviation': std_dev,
                'coefficient_of_variation': cv,
                'balance_score': 1.0 / (1.0 + cv),  # Higher score = more balanced
                'assessment': 'well_balanced' if cv < 0.3 else 'moderately_balanced' if cv < 0.6 else 'unbalanced'
            }
        else:
            balance_metrics['balance_analysis'] = {
                'mean_ways_per_room': mean_ways,
                'variance': 0,
                'std_deviation': 0,
                'coefficient_of_variation': 0,
                'balance_score': 1.0,
                'assessment': 'single_room'
            }

        # Identify outliers
        balance_metrics['outliers'] = {
            'high_outliers': [room for room, data in balance_metrics['room_distribution'].items()
                            if data['ways'] > mean_ways + 2 * balance_metrics['balance_analysis']['std_deviation']],
            'low_outliers': [room for room, data in balance_metrics['room_distribution'].items()
                           if data['ways'] < mean_ways - 2 * balance_metrics['balance_analysis']['std_deviation']]
        }

    return balance_metrics

