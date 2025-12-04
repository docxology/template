#!/usr/bin/env python3
"""Script to collect actual data for manuscript updates."""

import sys
import os
from pathlib import Path

# Add project src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# Import required modules
from database import WaysDatabase
from sql_queries import WaysSQLQueries
from ways_analysis import WaysAnalyzer
from network_analysis import WaysNetworkAnalyzer
import networkx as nx

def main():
    print('=== DATA COLLECTION FOR MANUSCRIPT UPDATES ===')
    print()

    # Initialize database and analyzers
    db = WaysDatabase()
    queries = WaysSQLQueries()
    analyzer = WaysAnalyzer()
    network_analyzer = WaysNetworkAnalyzer()

    # 1. Get basic characterization
    print('1. Basic Characterization:')
    characterization = analyzer.characterize_ways()
    print(f'   Total ways: {characterization.total_ways}')
    print(f'   Dialogue types: {characterization.dialogue_types}')
    print(f'   Room distribution: {characterization.room_distribution}')
    print(f'   Partner distribution: {characterization.partner_distribution}')
    print()

    # 2. Get dialogue type distribution
    print('2. Dialogue Type Distribution:')
    _, results = queries.count_ways_by_type_sql()
    for row in results:
        print(f'   {row[0]}: {row[1]} ways')
    print()

    # 3. Get room distribution
    print('3. Room Distribution:')
    _, results = queries.count_ways_by_room_sql()
    for row in results:
        print(f'   {row[0]}: {row[1]} ways')
    print()

    # 4. Get partner frequencies (top 10)
    print('4. Top 10 Dialogue Partners:')
    _, results = queries.count_ways_by_partner_sql()
    for row in results[:10]:
        print(f'   {row[0]}: {row[1]} ways')
    print()

    # 5. Network metrics
    print('5. Network Metrics:')
    network = network_analyzer.build_ways_network()
    print(f'   Nodes: {network.graph.number_of_nodes()}')
    print(f'   Edges: {network.graph.number_of_edges()}')
    if network.graph.number_of_nodes() > 0:
        degrees = dict(network.graph.degree())
        avg_degree = sum(degrees.values()) / len(degrees)
        print(f'   Average degree: {avg_degree:.2f}')

        # Clustering coefficient
        if network.graph.number_of_edges() > 0:
            clustering = nx.average_clustering(network.graph)
            print(f'   Clustering coefficient: {clustering:.3f}')

        # Diameter (if connected)
        if nx.is_connected(network.graph):
            diameter = nx.diameter(network.graph)
            print(f'   Diameter: {diameter}')

        # Connected components
        components = list(nx.connected_components(network.graph))
        print(f'   Connected components: {len(components)}')
        if components:
            largest_component = max(components, key=len)
            print(f'   Largest component size: {len(largest_component)}')
    print()

    # 6. Central ways
    print('6. Central Ways (top 5 by degree):')
    central_ways = network_analyzer.find_central_ways()
    if central_ways.by_degree:
        for way_id, degree in central_ways.by_degree[:5]:
            way = network.ways.get(way_id)
            way_name = way.way[:50] + '...' if way and len(way.way) > 50 else way.way if way else 'Unknown'
            print(f'   Way {way_id}: {way_name} (degree: {degree})')
    print()

    # 7. Cross-tabulation data
    print('7. Dialogue Type × Room Cross-tabulation (sample):')
    # Get all ways with their type and room
    _, all_ways = queries.get_all_ways_sql()
    type_room_counts = {}
    for row in all_ways:
        way_type = row[3]  # dialoguetype
        room = row[8]      # mene
        key = (way_type, room)
        type_room_counts[key] = type_room_counts.get(key, 0) + 1

    # Print some examples
    for (way_type, room), count in list(type_room_counts.items())[:15]:
        print(f'   {way_type} × {room}: {count}')
    print()

    # 8. God relationships
    print('8. God Relationship Distribution (top 10):')
    _, results = queries.get_god_relationship_distribution_sql()
    for row in results[:10]:
        print(f'   {row[0]}: {row[1]} ways')
    print()

    print('=== DATA COLLECTION COMPLETE ===')

if __name__ == "__main__":
    main()
