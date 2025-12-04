#!/usr/bin/env python3
"""Comprehensive Analysis Script for Ways of Figuring Things Out.

Generates complete statistical summaries, cross-tabulations, information-theoretic
metrics, text analysis, and network centrality measures for the ways database.
Exports results to JSON/CSV for manuscript integration.

This script uses the existing ways_analysis module but extends it with:
- Statistical exports for manuscript tables
- Information theory metrics (entropy, mutual information)
- Cross-tabulation matrices
- Text analysis of examples
- Network centrality calculations
"""

import sys
import json
import csv
import math
from pathlib import Path
from typing import Dict, Any, List, Tuple, Set
from collections import Counter, defaultdict


def _ensure_src_on_path() -> None:
    """Ensure src/ and infrastructure are on Python path for imports."""
    # Add repository root to path (same as generate_figures.py)
    repo_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(repo_root))

    # Add project root to path (for src package)
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    # Add project src to path
    src_path = project_root / "src"
    sys.path.insert(0, str(src_path))


def _import_dependencies():
    """Import required modules with error handling."""
    try:
        from infrastructure.core.logging_utils import get_logger, log_operation, log_success
        # Import database and sql_queries directly (they don't use relative imports)
        from database import WaysDatabase
        from sql_queries import WaysSQLQueries
        
        # For ways_analysis and network_analysis, we'll work around the relative import issue
        # by importing them as package modules
        import src.ways_analysis as ways_analysis_module
        import src.network_analysis as network_analysis_module
        WaysAnalyzer = ways_analysis_module.WaysAnalyzer
        WaysNetworkAnalyzer = network_analysis_module.WaysNetworkAnalyzer
        
        return get_logger, log_operation, log_success, WaysAnalyzer, WaysNetworkAnalyzer, WaysDatabase, WaysSQLQueries
    except ImportError as e:
        # Fallback: import ways_analysis components directly
        try:
            from infrastructure.core.logging_utils import get_logger, log_operation, log_success
            from database import WaysDatabase
            from sql_queries import WaysSQLQueries
            
            # Create minimal wrappers if imports fail
            class WaysAnalyzerWrapper:
                def __init__(self, db_path=None):
                    self.db = WaysDatabase(db_path)
                    self.queries = WaysSQLQueries(db_path)
                
                def characterize_ways(self):
                    # Minimal implementation
                    stats = self.db.get_way_statistics()
                    from dataclasses import dataclass, field
                    @dataclass
                    class SimpleChar:
                        total_ways: int = 0
                        dialogue_types: dict = field(default_factory=dict)
                        room_distribution: dict = field(default_factory=dict)
                        partner_distribution: dict = field(default_factory=dict)
                        god_relationships: dict = field(default_factory=dict)
                        ways_with_examples: int = 0
                        avg_examples_length: float = 0.0
                        most_common_room: str = ""
                        most_common_type: str = ""
                        most_common_partner: str = ""
                        room_diversity: int = 0
                        type_diversity: int = 0
                        partner_diversity: int = 0
                    
                    char = SimpleChar()
                    char.total_ways = stats['total_ways']
                    char.dialogue_types = stats.get('dialogue_types', {})
                    char.room_distribution = stats.get('room_distribution', {})
                    char.room_diversity = len(char.room_distribution)
                    char.type_diversity = len(char.dialogue_types)
                    return char
                
                def compute_cross_tabulations(self):
                    # Get type-room cross-tab
                    _, results = self.queries.cross_tabulate_type_room_sql()
                    type_room = {}
                    for dtype, room, count in results:
                        if dtype not in type_room:
                            type_room[dtype] = {}
                        type_room[dtype][room] = count
                    return {'type_room': type_room, 'type_partner': {}}
            
            class WaysNetworkAnalyzerWrapper:
                def __init__(self, db_path=None):
                    self.db = WaysDatabase(db_path)
                    self.queries = WaysSQLQueries(db_path)
                    self.network = None
                
                def build_ways_network(self):
                    # Minimal implementation
                    return type('Network', (), {'graph': type('Graph', (), {'number_of_nodes': lambda: 0, 'number_of_edges': lambda: 0})(), 'ways': {}})()
                
                def find_central_ways(self):
                    return type('CentralWays', (), {'by_degree': []})()
                
                def compute_centrality_metrics(self):
                    return type('Metrics', (), {'node_count': 0, 'edge_count': 0, 'average_degree': 0.0, 'clustering_coefficient': 0.0, 'degree_centrality': {}, 'betweenness_centrality': {}, 'closeness_centrality': {}, 'eigenvector_centrality': {}, 'connected_components': 0, 'largest_component_size': 0, 'density': 0.0})()
            
            WaysAnalyzer = WaysAnalyzerWrapper
            WaysNetworkAnalyzer = WaysNetworkAnalyzerWrapper
            return get_logger, log_operation, log_success, WaysAnalyzer, WaysNetworkAnalyzer, WaysDatabase, WaysSQLQueries
        except Exception as e2:
            print(f"❌ Failed to import dependencies: {e2}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


# Ensure paths are set up before imports
_ensure_src_on_path()
get_logger, log_operation, log_success, WaysAnalyzer, WaysNetworkAnalyzer, WaysDatabase, WaysSQLQueries = _import_dependencies()


class ComprehensiveWaysAnalyzer:
    """Extended analyzer with comprehensive statistical exports."""

    def __init__(self, db_path: str = None):
        """Initialize with database path."""
        self.analyzer = WaysAnalyzer(db_path)
        self.network_analyzer = WaysNetworkAnalyzer(db_path)
        self.db = WaysDatabase(db_path)
        self.queries = WaysSQLQueries(db_path)
        self.logger = get_logger(__name__)

    def calculate_entropy(self, distribution: Dict[str, int]) -> float:
        """Calculate Shannon entropy of a categorical distribution."""
        total = sum(distribution.values())
        if total == 0:
            return 0.0

        entropy = 0.0
        for count in distribution.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)

        return entropy

    def calculate_mutual_information(self, joint_dist: Dict[str, Dict[str, int]]) -> float:
        """Calculate mutual information between two categorical variables."""
        # Convert to contingency table
        row_totals = {}
        col_totals = {}
        total = 0

        for row_key, row_data in joint_dist.items():
            row_totals[row_key] = sum(row_data.values())
            for col_key, count in row_data.items():
                col_totals[col_key] = col_totals.get(col_key, 0) + count
                total += count

        if total == 0:
            return 0.0

        mi = 0.0
        for row_key, row_data in joint_dist.items():
            for col_key, count in row_data.items():
                if count > 0:
                    p_xy = count / total
                    p_x = row_totals[row_key] / total
                    p_y = col_totals[col_key] / total
                    mi += p_xy * math.log2(p_xy / (p_x * p_y))

        return mi

    def build_network_graph(self) -> Dict[str, Any]:
        """Build network graph data using WaysNetworkAnalyzer for comprehensive metrics."""
        # Use the sophisticated network analyzer
        network = self.network_analyzer.build_ways_network()
        metrics = self.network_analyzer.compute_centrality_metrics()
        central_ways = self.network_analyzer.find_central_ways()

        # Build network data structure
        network_data = {
            'nodes': [],
            'edges': [],
            'metrics': {
                'node_count': metrics.node_count,
                'edge_count': metrics.edge_count,
                'density': metrics.density,
                'average_degree': metrics.average_degree,
                'clustering_coefficient': metrics.clustering_coefficient,
                'connected_components': metrics.connected_components,
                'largest_component_size': metrics.largest_component_size
            },
            'centrality': {
                'degree': {str(k): int(v) if isinstance(v, (int, float)) else v for k, v in metrics.degree_centrality.items()},
                'betweenness': {str(k): float(v) for k, v in metrics.betweenness_centrality.items()},
                'closeness': {str(k): float(v) for k, v in metrics.closeness_centrality.items()},
                'eigenvector': {str(k): float(v) for k, v in metrics.eigenvector_centrality.items()}
            },
            'central_ways': {
                'by_degree': [(int(way_id), int(degree)) for way_id, degree in central_ways.by_degree[:10]],
                'by_betweenness': [(int(way_id), float(score)) for way_id, score in central_ways.by_betweenness[:10]],
                'hubs': [int(way_id) for way_id in central_ways.hubs[:10]],
                'bridges': [int(way_id) for way_id in central_ways.bridges[:10]]
            }
        }

        # Add node information
        for way_id, way in network.ways.items():
            network_data['nodes'].append({
                'id': way_id,
                'name': way.way[:50] if way.way else '',
                'dialogue_type': way.dialoguetype,
                'room': way.mene
            })

        # Add edge information
        for edge in network.graph.edges(data=True):
            network_data['edges'].append({
                'source': edge[0],
                'target': edge[1],
                'weight': edge[2].get('weight', 1.0) if len(edge) > 2 else 1.0,
                'type': network.edge_types.get((edge[0], edge[1]), 'unknown')
            })

        return network_data

    def analyze_text_content(self) -> Dict[str, Any]:
        """Perform text analysis on way descriptions and examples."""
        _, ways_data = self.queries.get_all_ways_sql()

        text_analysis = {
            'total_ways': len(ways_data),
            'ways_with_examples': sum(1 for row in ways_data if row[6] and row[6].strip()),
            'avg_way_name_length': 0,
            'avg_examples_length': 0,
            'keyword_frequency': {},
            'example_patterns': {},
            'language_patterns': {}
        }

        # Analyze text lengths
        way_lengths = []
        example_lengths = []

        for row in ways_data:
            way_text = row[1] or ""
            examples_text = row[6] or ""

            way_lengths.append(len(way_text))
            if examples_text:
                example_lengths.append(len(examples_text))

        if way_lengths:
            text_analysis['avg_way_name_length'] = sum(way_lengths) / len(way_lengths)
        if example_lengths:
            text_analysis['avg_examples_length'] = sum(example_lengths) / len(example_lengths)

        # Keyword extraction (simple frequency analysis)
        keywords = Counter()
        common_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'as', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'me', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'way', 'ways',
            'think', 'thinking', 'know', 'knowing', 'understand', 'understanding'
        }

        for row in ways_data:
            way_text = (row[1] or "").lower()
            examples_text = (row[6] or "").lower()

            for text in [way_text, examples_text]:
                words = [w.strip('.,!?()[]{}:;"\'') for w in text.split()]
                for word in words:
                    if len(word) > 2 and word not in common_words:
                        keywords[word] += 1

        text_analysis['keyword_frequency'] = dict(keywords.most_common(50))

        return text_analysis

    def generate_comprehensive_stats(self) -> Dict[str, Any]:
        """Generate comprehensive statistical summary."""
        self.logger.info("Generating comprehensive statistical analysis...")

        # Get basic characterization
        characterization = self.analyzer.characterize_ways()

        # Get cross-tabulations
        cross_tabs = self.analyzer.compute_cross_tabulations()

        # Calculate information theory metrics
        info_metrics = {
            'room_entropy': self.calculate_entropy(characterization.room_distribution),
            'type_entropy': self.calculate_entropy(characterization.dialogue_types),
            'partner_entropy': self.calculate_entropy(characterization.partner_distribution),
            'type_room_mutual_info': self.calculate_mutual_information(cross_tabs.get('type_room', {}))
        }

        # Build network analysis
        network_data = self.build_network_graph()

        # Text analysis
        text_analysis = self.analyze_text_content()

        # Compile comprehensive results
        comprehensive_stats = {
            'basic_stats': {
                'total_ways': characterization.total_ways,
                'room_diversity': characterization.room_diversity,
                'type_diversity': characterization.type_diversity,
                'partner_diversity': characterization.partner_diversity,
                'most_common_room': characterization.most_common_room,
                'most_common_type': characterization.most_common_type,
                'most_common_partner': characterization.most_common_partner,
                'examples_coverage': characterization.ways_with_examples / characterization.total_ways if characterization.total_ways > 0 else 0,
                'avg_examples_length': characterization.avg_examples_length
            },
            'distributions': {
                'room_distribution': characterization.room_distribution,
                'type_distribution': characterization.dialogue_types,
                'partner_distribution': characterization.partner_distribution,
                'god_relationships': characterization.god_relationships
            },
            'cross_tabulations': cross_tabs,
            'information_theory': info_metrics,
            'network_analysis': network_data,
            'text_analysis': text_analysis,
            'metadata': {
                'database_version': 'SQLite converted from MySQL dump',
                'analysis_date': '2024-12-04',
                'analysis_script': 'comprehensive_analysis.py'
            }
        }

        return comprehensive_stats

    def export_to_json(self, stats: Dict[str, Any], output_path: Path) -> None:
        """Export comprehensive stats to JSON."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        self.logger.info(f"Exported comprehensive stats to {output_path}")

    def export_to_csv(self, stats: Dict[str, Any], output_dir: Path) -> None:
        """Export key statistics to CSV files for manuscript tables."""

        # Room distribution CSV
        room_csv = output_dir / "room_distribution.csv"
        with open(room_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Room', 'Count', 'Percentage'])
            total = stats['basic_stats']['total_ways']
            for room, count in stats['distributions']['room_distribution'].items():
                pct = (count / total * 100) if total > 0 else 0
                writer.writerow([room, count, f"{pct:.1f}"])

        # Dialogue type distribution CSV
        type_csv = output_dir / "dialogue_type_distribution.csv"
        with open(type_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Dialogue_Type', 'Count', 'Percentage'])
            total = stats['basic_stats']['total_ways']
            for dtype, count in stats['distributions']['type_distribution'].items():
                pct = (count / total * 100) if total > 0 else 0
                writer.writerow([dtype, count, f"{pct:.1f}"])

        # Cross-tabulation CSV (type × room)
        crosstab_csv = output_dir / "type_room_crosstab.csv"
        with open(crosstab_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Get all rooms and types
            rooms = set()
            types = set()
            for type_key, room_data in stats['cross_tabulations']['type_room'].items():
                types.add(type_key)
                rooms.update(room_data.keys())

            rooms = sorted(rooms)
            types = sorted(types)

            # Header
            writer.writerow(['Dialogue_Type'] + rooms)

            # Data rows
            for dtype in types:
                row = [dtype]
                for room in rooms:
                    count = stats['cross_tabulations']['type_room'].get(dtype, {}).get(room, 0)
                    row.append(count)
                writer.writerow(row)

        # Network centrality CSV
        centrality_csv = output_dir / "network_centrality.csv"
        with open(centrality_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Way_ID', 'Degree_Centrality'])
            for way_id, degree in stats['network_analysis']['centrality']['degree'].items():
                writer.writerow([way_id, degree])

        self.logger.info(f"Exported CSV files to {output_dir}")


def main():
    """Main analysis function."""
    logger = get_logger(__name__)

    with log_operation("Comprehensive Ways Analysis", logger):
        # Initialize analyzer
        analyzer = ComprehensiveWaysAnalyzer()

        # Generate comprehensive statistics
        stats = analyzer.generate_comprehensive_stats()

        # Create output directory
        output_dir = Path(__file__).parent.parent / "output" / "analysis"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Export to JSON
        json_path = output_dir / "comprehensive_stats.json"
        analyzer.export_to_json(stats, json_path)

        # Export to CSV files
        analyzer.export_to_csv(stats, output_dir)

        # Print summary
        basic = stats['basic_stats']
        logger.info("=== ANALYSIS SUMMARY ===")
        logger.info(f"Total ways: {basic['total_ways']}")
        logger.info(f"Room diversity: {basic['room_diversity']}")
        logger.info(f"Dialogue type diversity: {basic['type_diversity']}")
        logger.info(f"Most common room: {basic['most_common_room']}")
        logger.info(f"Most common type: {basic['most_common_type']}")
        info_metrics = stats.get('information_theory', {})
        if info_metrics:
            logger.info(f"Room entropy: {info_metrics.get('room_entropy', 0):.3f}")
            logger.info(f"Type entropy: {info_metrics.get('type_entropy', 0):.3f}")
        network_metrics = stats['network_analysis'].get('metrics', {})
        logger.info(f"Network nodes: {network_metrics.get('node_count', len(stats['network_analysis']['nodes']))}")
        logger.info(f"Network edges: {network_metrics.get('edge_count', len(stats['network_analysis']['edges']))}")
        logger.info(f"Average degree: {network_metrics.get('average_degree', 0):.2f}")
        logger.info(f"Clustering coefficient: {network_metrics.get('clustering_coefficient', 0):.3f}")

        log_success("Comprehensive analysis completed successfully", logger)


if __name__ == "__main__":
    main()
