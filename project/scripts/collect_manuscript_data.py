#!/usr/bin/env python3
"""Utility script to collect and display actual data for manuscript updates.

This script provides a quick way to inspect database statistics and network
metrics for manual data collection. For comprehensive analysis with exports,
use comprehensive_analysis.py instead.

This script is kept as a utility for quick data inspection and debugging.
"""

import sys
from pathlib import Path

# Add infrastructure and project src to path (same pattern as comprehensive_analysis.py)
def _ensure_src_on_path() -> None:
    """Ensure src/ is on Python path for imports."""
    repo_root = Path(__file__).parent.parent.parent
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"
    
    # Add repo root for infrastructure
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    # Add src for direct imports
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    # Add project root for src.ways_analysis imports
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

_ensure_src_on_path()

# Import infrastructure logging
from infrastructure.core.logging_utils import get_logger

# Import using the same pattern as comprehensive_analysis.py
def _import_dependencies():
    """Import required modules with error handling."""
    try:
        # Import database and sql_queries directly (they don't use relative imports)
        from database import WaysDatabase
        from sql_queries import WaysSQLQueries
        
        # For ways_analysis and network_analysis, import as package modules
        import src.ways_analysis as ways_analysis_module
        import src.network_analysis as network_analysis_module
        WaysAnalyzer = ways_analysis_module.WaysAnalyzer
        WaysNetworkAnalyzer = network_analysis_module.WaysNetworkAnalyzer
        
        import networkx as nx
        
        return WaysAnalyzer, WaysNetworkAnalyzer, WaysDatabase, WaysSQLQueries, nx
    except ImportError as e:
        get_logger(__name__).error(f"Failed to import dependencies: {e}")
        raise

WaysAnalyzer, WaysNetworkAnalyzer, WaysDatabase, WaysSQLQueries, nx = _import_dependencies()
logger = get_logger(__name__)


def main():
    """Main data collection function."""
    logger.info('=== DATA COLLECTION FOR MANUSCRIPT UPDATES ===')

    # Initialize database and analyzers
    db = WaysDatabase()
    queries = WaysSQLQueries()
    analyzer = WaysAnalyzer()
    network_analyzer = WaysNetworkAnalyzer()

    # 1. Get basic characterization
    logger.info('1. Basic Characterization:')
    characterization = analyzer.characterize_ways()
    logger.info(f'   Total ways: {characterization.total_ways}')
    logger.info(f'   Room diversity: {characterization.room_diversity}')
    logger.info(f'   Type diversity: {characterization.type_diversity}')
    logger.info(f'   Partner diversity: {characterization.partner_diversity}')
    logger.info(f'   Most common room: {characterization.most_common_room}')
    logger.info(f'   Most common type: {characterization.most_common_type}')
    logger.info('')

    # 2. Get dialogue type distribution
    logger.info('2. Dialogue Type Distribution (top 10):')
    _, results = queries.count_ways_by_type_sql()
    for row in results[:10]:
        logger.info(f'   {row[0]}: {row[1]} ways')
    logger.info('')

    # 3. Get room distribution
    logger.info('3. Room Distribution (top 15):')
    _, results = queries.count_ways_by_room_sql()
    for row in results[:15]:
        logger.info(f'   {row[0]}: {row[1]} ways')
    logger.info('')

    # 4. Get partner frequencies (top 10)
    logger.info('4. Top 10 Dialogue Partners:')
    _, results = queries.count_ways_by_partner_sql()
    for row in results[:10]:
        logger.info(f'   {row[0]}: {row[1]} ways')
    logger.info('')

    # 5. Network metrics
    logger.info('5. Network Metrics:')
    network = network_analyzer.build_ways_network()
    metrics = network_analyzer.compute_centrality_metrics()
    
    logger.info(f'   Nodes: {metrics.node_count}')
    logger.info(f'   Edges: {metrics.edge_count}')
    logger.info(f'   Average degree: {metrics.average_degree:.2f}')
    logger.info(f'   Density: {metrics.density:.4f}')
    logger.info(f'   Clustering coefficient: {metrics.clustering_coefficient:.3f}')
    logger.info(f'   Connected components: {metrics.connected_components}')
    logger.info(f'   Largest component size: {metrics.largest_component_size}')
    
    # Diameter (if connected)
    if nx.is_connected(network.graph):
        diameter = nx.diameter(network.graph)
        logger.info(f'   Diameter: {diameter}')
    logger.info('')

    # 6. Central ways
    logger.info('6. Central Ways (top 5 by degree):')
    central_ways = network_analyzer.find_central_ways()
    if central_ways.by_degree:
        for way_id, degree in central_ways.by_degree[:5]:
            way = network.ways.get(way_id)
            way_name = way.way[:50] + '...' if way and len(way.way) > 50 else way.way if way else 'Unknown'
            logger.info(f'   Way {way_id}: {way_name} (degree: {degree})')
    logger.info('')

    # 7. Cross-tabulation data
    logger.info('7. Dialogue Type × Room Cross-tabulation (top 15):')
    _, cross_results = queries.cross_tabulate_type_room_sql()
    for dtype, room, count in cross_results[:15]:
        logger.info(f'   {dtype} × {room}: {count}')
    logger.info('')

    # 8. God relationships
    logger.info('8. God Relationship Distribution (top 10):')
    _, results = queries.get_god_relationship_distribution_sql()
    for row in results[:10]:
        logger.info(f'   {row[0]}: {row[1]} ways')
    logger.info('')

    logger.info('=== DATA COLLECTION COMPLETE ===')


if __name__ == "__main__":
    main()
