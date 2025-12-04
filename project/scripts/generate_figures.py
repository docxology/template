#!/usr/bin/env python3
"""Figure generation script for Ways of Figuring Things Out research.

Generates publication-quality figures for the ways analysis manuscript:
- ways_network.png: Network visualization of ways relationships
- room_hierarchy.png: Hierarchical visualization of the House of Knowledge
- type_distribution.png: Bar chart of dialogue type distributions

This script uses matplotlib with non-interactive backend for headless operation.
"""

import sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import numpy as np
from collections import defaultdict
try:
    import seaborn as sns
    sns.set_style("whitegrid")
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

# Add infrastructure to path for logging
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Add project src to path (same as db_setup.py)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from infrastructure.core.logging_utils import get_logger, log_operation, log_success
from database import WaysDatabase
from sql_queries import WaysSQLQueries
from models import Way

# Set up logger
logger = get_logger(__name__)


def generate_ways_network_figure(output_path: Path) -> None:
    """Generate network visualization of ways relationships.

    Args:
        output_path: Path to save the figure
    """
    logger.info("Generating ways network visualization...")

    # Initialize queries
    queries = WaysSQLQueries()

    # Get all ways data
    _, ways_data = queries.get_all_ways_sql()

    if not ways_data:
        logger.warning("No ways data available")
        return

    # Create network graph
    G = nx.Graph()

    # Add nodes with attributes
    dialogue_types = set()
    ways_dict = {}

    for row in ways_data:
        way_id = row[0]
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

        ways_dict[way_id] = way
        dialogue_types.add(way.dialoguetype)
        G.add_node(way_id)

    # Add edges based on relationships (simplified version)
    # Room-based edges: ways in same room
    room_ways = {}
    for way_id, way in ways_dict.items():
        if way.mene not in room_ways:
            room_ways[way.mene] = []
        room_ways[way.mene].append(way_id)

    for room, way_ids in room_ways.items():
        if len(way_ids) > 1:
            for i, way1_id in enumerate(way_ids):
                for j, way2_id in enumerate(way_ids):
                    if i < j:  # Avoid duplicate edges
                        G.add_edge(way1_id, way2_id, weight=1.0, edge_type='same_room')

    # Partner-based edges: ways with same dialogue partner
    partner_ways = {}
    for way_id, way in ways_dict.items():
        if way.dialoguewith not in partner_ways:
            partner_ways[way.dialoguewith] = []
        partner_ways[way.dialoguewith].append(way_id)

    for partner, way_ids in partner_ways.items():
        if len(way_ids) > 1:
            for i, way1_id in enumerate(way_ids):
                for j, way2_id in enumerate(way_ids):
                    if i < j and not G.has_edge(way1_id, way2_id):  # Avoid duplicate edges
                        G.add_edge(way1_id, way2_id, weight=0.8, edge_type='same_partner')

    # Type-based edges: ways with same dialogue type
    type_ways = {}
    for way_id, way in ways_dict.items():
        if way.dialoguetype not in type_ways:
            type_ways[way.dialoguetype] = []
        type_ways[way.dialoguetype].append(way_id)

    for dtype, way_ids in type_ways.items():
        if len(way_ids) > 1:
            for i, way1_id in enumerate(way_ids):
                for j, way2_id in enumerate(way_ids):
                    if i < j and not G.has_edge(way1_id, way2_id):  # Avoid duplicate edges
                        G.add_edge(way1_id, way2_id, weight=0.6, edge_type='same_type')

    if not G.nodes():
        logger.warning("No network nodes available")
        return

    # Create figure with high DPI for publication quality
    fig, ax = plt.subplots(figsize=(12, 10), dpi=300)

    # Create color mapping for dialogue types
    colors = plt.cm.tab10(np.linspace(0, 1, len(dialogue_types)))
    type_colors = dict(zip(sorted(dialogue_types), colors))

    # Assign colors to nodes
    node_colors = []
    for node_id in G.nodes():
        way = ways_dict.get(node_id)
        if way:
            node_colors.append(type_colors.get(way.dialoguetype, 'gray'))
        else:
            node_colors.append('gray')

    # Calculate node sizes based on degree centrality
    degrees = dict(G.degree())
    max_degree = max(degrees.values()) if degrees else 1
    node_sizes = [300 * (degrees[node] / max_degree) + 100 for node in G.nodes()]

    # Use spring layout for network visualization
    pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)

    # Draw the network
    nx.draw_networkx_nodes(G, pos,
                          node_color=node_colors,
                          node_size=node_sizes,
                          alpha=0.7, ax=ax)

    # Draw edges with varying thickness based on weight
    edge_weights = [G[u][v].get('weight', 1.0) for u, v in G.edges()]
    max_weight = max(edge_weights) if edge_weights else 1
    edge_widths = [2 * (w / max_weight) + 0.5 for w in edge_weights]

    nx.draw_networkx_edges(G, pos,
                          width=edge_widths,
                          alpha=0.3,
                          edge_color='gray', ax=ax)

    # Add legend
    legend_elements = [mpatches.Patch(color=color, label=dtype)
                      for dtype, color in type_colors.items()]
    ax.legend(handles=legend_elements, loc='upper right',
             title='Dialogue Types', fontsize=10)

    # Configure plot
    ax.set_title('Ways of Figuring Things Out Network', fontsize=16, fontweight='bold')
    ax.set_axis_off()

    # Save figure
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close(fig)

    log_success(f"Saved ways network figure: {output_path}", logger)


def generate_room_hierarchy_figure(output_path: Path) -> None:
    """Generate hierarchical visualization of the House of Knowledge.

    Args:
        output_path: Path to save the figure
    """
    logger.info("Generating room hierarchy visualization...")

    # Initialize queries
    queries = WaysSQLQueries()

    # Get room data
    _, rooms_data = queries.get_rooms_sql()
    _, room_count_data = queries.count_ways_by_room_sql()

    if not rooms_data or not room_count_data:
        logger.warning("No room data available")
        return

    # Create room lookup and counts
    room_counts = {row[0]: row[1] for row in room_count_data}  # room_short -> count
    room_lookup = {row[1]: row for row in rooms_data}  # santrumpa -> full row

    # Get room hierarchy (sorted by eilestvarka)
    rooms_sorted = sorted(rooms_data, key=lambda r: r[4])  # eilestvarka is index 4
    room_hierarchy = [row[1] for row in rooms_sorted]  # santrumpa

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 10), dpi=300)

    # Prepare data for visualization
    rooms = []
    way_counts = []
    room_names = []

    for room_short in room_hierarchy:
        if room_short in room_counts:
            count = room_counts[room_short]
            rooms.append(room_short)
            way_counts.append(count)

            # Get full room name
            room_row = room_lookup.get(room_short)
            full_name = room_row[2] if room_row else room_short  # savoka is index 2
            room_names.append(f"{room_short}: {full_name}")

    if not rooms:
        logger.warning("No room hierarchy data available")
        return

    # Create hierarchical bar chart
    y_pos = np.arange(len(rooms))
    bars = ax.barh(y_pos, way_counts, align='center', alpha=0.8)

    # Color bars by room type/category (simplified grouping)
    framework_colors = {
        'Believing': '#1f77b4',      # Blue
        'Caring': '#ff7f0e',         # Orange
        'Relative Learning': '#2ca02c', # Green
        'Other': '#7f7f7f'           # Gray
    }

    # Assign colors based on room short names (simplified logic)
    for i, room_short in enumerate(rooms):
        if room_short in ['B', 'B2', 'B3', 'B4', 'BB', 'BC']:
            color = framework_colors['Believing']
        elif room_short in ['1', '10', '20', '30', '31', '32']:
            color = framework_colors['Caring']
        elif room_short in ['C', 'C2', 'C3', 'C4', 'CB', 'CC']:
            color = framework_colors['Relative Learning']
        else:
            color = framework_colors['Other']
        bars[i].set_color(color)

    # Configure plot
    ax.set_yticks(y_pos)
    ax.set_yticklabels(room_names, fontsize=9)
    ax.set_xlabel('Number of Ways', fontsize=12)
    ax.set_title('House of Knowledge Room Hierarchy', fontsize=16, fontweight='bold')

    # Add value labels on bars
    for i, bar in enumerate(bars):
        width = bar.get_width()
        ax.text(width + 0.1, bar.get_y() + bar.get_height()/2,
               f'{int(width)}', ha='left', va='center', fontsize=8)

    # Add legend
    legend_elements = [mpatches.Patch(color=color, label=framework)
                      for framework, color in framework_colors.items()]
    ax.legend(handles=legend_elements, loc='lower right',
             title='Frameworks', fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close(fig)

    log_success(f"Saved room hierarchy figure: {output_path}", logger)


def generate_type_distribution_figure(output_path: Path) -> None:
    """Generate bar chart of dialogue type distributions.

    Args:
        output_path: Path to save the figure
    """
    logger.info("Generating dialogue type distribution visualization...")

    # Initialize queries
    queries = WaysSQLQueries()

    # Get dialogue type distribution
    _, type_data = queries.count_ways_by_type_sql()

    if not type_data:
        logger.warning("No dialogue type data available")
        return

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8), dpi=300)

    # Prepare data
    types = [row[0] for row in type_data]
    counts = [row[1] for row in type_data]

    # Sort by frequency (descending)
    sorted_indices = np.argsort(counts)[::-1]
    types = [types[i] for i in sorted_indices]
    counts = [counts[i] for i in sorted_indices]

    # Create bar chart
    bars = ax.bar(range(len(types)), counts, align='center', alpha=0.8,
                  color='#1f77b4', edgecolor='black', linewidth=0.5)

    # Configure plot
    ax.set_xticks(range(len(types)))
    ax.set_xticklabels(types, rotation=45, ha='right', fontsize=10)
    ax.set_ylabel('Number of Ways', fontsize=12)
    ax.set_title('Distribution of Ways by Dialogue Type', fontsize=16, fontweight='bold')

    # Add value labels on bars
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height + 0.5,
               f'{int(height)}', ha='center', va='bottom', fontsize=9)

    # Add grid for readability
    ax.grid(axis='y', alpha=0.3)
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close(fig)

    log_success(f"Saved type distribution figure: {output_path}", logger)


def generate_type_room_heatmap(output_path: Path) -> None:
    """Generate heatmap of dialogue type × room cross-tabulation.

    Args:
        output_path: Path to save the figure
    """
    logger.info("Generating type × room heatmap...")

    # Initialize queries
    queries = WaysSQLQueries()

    # Get cross-tabulation data
    _, cross_results = queries.cross_tabulate_type_room_sql()

    if not cross_results:
        logger.warning("No cross-tabulation data available")
        return

    # Build matrix
    type_room_matrix = defaultdict(lambda: defaultdict(int))
    all_types = set()
    all_rooms = set()

    for dtype, room, count in cross_results:
        type_room_matrix[dtype][room] = count
        all_types.add(dtype)
        all_rooms.add(room)

    all_types = sorted(all_types)
    all_rooms = sorted(all_rooms)

    # Create matrix
    matrix = np.zeros((len(all_types), len(all_rooms)))
    for i, dtype in enumerate(all_types):
        for j, room in enumerate(all_rooms):
            matrix[i, j] = type_room_matrix[dtype][room]

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 10), dpi=300)

    if HAS_SEABORN:
        sns.heatmap(matrix, annot=True, fmt='.0f', cmap='YlOrRd',
                   xticklabels=all_rooms, yticklabels=all_types,
                   cbar_kws={'label': 'Number of Ways'}, ax=ax)
    else:
        im = ax.imshow(matrix, aspect='auto', cmap='YlOrRd', interpolation='nearest')
        ax.set_xticks(range(len(all_rooms)))
        ax.set_xticklabels(all_rooms, rotation=45, ha='right')
        ax.set_yticks(range(len(all_types)))
        ax.set_yticklabels(all_types)
        plt.colorbar(im, ax=ax, label='Number of Ways')
        
        # Add text annotations
        for i in range(len(all_types)):
            for j in range(len(all_rooms)):
                if matrix[i, j] > 0:
                    ax.text(j, i, int(matrix[i, j]), ha='center', va='center',
                           color='white' if matrix[i, j] > matrix.max() / 2 else 'black')

    ax.set_xlabel('Room', fontsize=12)
    ax.set_ylabel('Dialogue Type', fontsize=12)
    ax.set_title('Dialogue Type × Room Cross-Tabulation', fontsize=16, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close(fig)

    log_success(f"Saved type × room heatmap: {output_path}", logger)


def generate_partner_wordcloud(output_path: Path) -> None:
    """Generate word cloud visualization of dialogue partners.

    Args:
        output_path: Path to save the figure
    """
    logger.info("Generating dialogue partner word cloud...")

    # Initialize database and queries
    queries = WaysSQLQueries()

    # Get partner distribution
    _, partner_results = queries.count_ways_by_partner_sql()

    if not partner_results:
        logger.warning("No partner data available")
        return

    # Create figure with text-based visualization (since wordcloud library may not be available)
    fig, ax = plt.subplots(figsize=(12, 10), dpi=300)

    # Sort partners by frequency
    partners = sorted(partner_results, key=lambda x: x[1], reverse=True)
    top_partners = partners[:30]  # Top 30

    # Create horizontal bar chart as word cloud alternative
    partner_names = [p[0][:40] for p in top_partners]  # Truncate long names
    frequencies = [p[1] for p in top_partners]

    y_pos = np.arange(len(partner_names))
    bars = ax.barh(y_pos, frequencies, align='center', alpha=0.8, color='steelblue')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(partner_names, fontsize=9)
    ax.set_xlabel('Frequency', fontsize=12)
    ax.set_title('Top Dialogue Partners (Word Cloud Style)', fontsize=16, fontweight='bold')
    ax.invert_yaxis()  # Top to bottom

    # Add value labels
    for i, (bar, freq) in enumerate(zip(bars, frequencies)):
        ax.text(freq + 0.1, bar.get_y() + bar.get_height()/2,
               f'{freq}', ha='left', va='center', fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close(fig)

    log_success(f"Saved partner word cloud: {output_path}", logger)


def generate_framework_treemap(output_path: Path) -> None:
    """Generate treemap visualization of framework hierarchy.

    Args:
        output_path: Path to save the figure
    """
    logger.info("Generating framework treemap...")

    # Initialize database and queries
    queries = WaysSQLQueries()

    # Get room distribution
    _, room_count_data = queries.count_ways_by_room_sql()
    _, rooms_data = queries.get_rooms_sql()

    if not room_count_data or not rooms_data:
        logger.warning("No room data available")
        return

    # Map rooms to frameworks
    room_lookup = {row[1]: row for row in rooms_data}  # santrumpa -> full row
    room_counts = {row[0]: row[1] for row in room_count_data}  # room_short -> count

    # Framework categories
    frameworks = {
        'Believing': ['B', 'B2', 'B3', 'B4', 'BB', 'BC'],
        'Caring': ['C', 'C2', 'C3', 'C4', 'CB', 'CC'],
        'Relative Learning': ['T', 'F', 'R', 'A'],
        'Absolute Learning': ['10', '20', '21', '30', '31', '32'],
        'Bridging': ['BB', 'BC', 'CB', 'CC'],
        'Other': []
    }

    # Calculate framework totals
    framework_totals = defaultdict(int)
    for framework, rooms in frameworks.items():
        for room in rooms:
            if room in room_counts:
                framework_totals[framework] += room_counts[room]

    # Create figure with nested bar chart (treemap alternative)
    fig, ax = plt.subplots(figsize=(14, 8), dpi=300)

    # Sort frameworks by total
    sorted_frameworks = sorted(framework_totals.items(), key=lambda x: x[1], reverse=True)
    framework_names = [f[0] for f in sorted_frameworks]
    framework_values = [f[1] for f in sorted_frameworks]

    # Color scheme
    colors = plt.cm.Set3(np.linspace(0, 1, len(framework_names)))

    bars = ax.barh(range(len(framework_names)), framework_values, align='center',
                  color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)

    ax.set_yticks(range(len(framework_names)))
    ax.set_yticklabels(framework_names, fontsize=11)
    ax.set_xlabel('Number of Ways', fontsize=12)
    ax.set_title('Framework Distribution (Treemap Style)', fontsize=16, fontweight='bold')
    ax.invert_yaxis()

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, framework_values)):
        ax.text(val + 0.5, bar.get_y() + bar.get_height()/2,
               f'{int(val)}', ha='left', va='center', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close(fig)

    log_success(f"Saved framework treemap: {output_path}", logger)


def generate_example_length_violin(output_path: Path) -> None:
    """Generate violin plot of example length distributions by category.

    Args:
        output_path: Path to save the figure
    """
    logger.info("Generating example length violin plot...")

    # Initialize database and queries
    queries = WaysSQLQueries()

    # Get ways with examples
    _, examples_results = queries.get_ways_with_examples_sql()

    if not examples_results:
        logger.warning("No examples data available")
        return

    # Organize by dialogue type
    type_lengths = defaultdict(list)
    for row in examples_results:
        # row format: (way_id, way_name, length, example_text)
        if len(row) >= 3:
            length = row[2]
            # Get dialogue type for this way
            way_id = row[0]
            _, way_data = queries.get_way_by_id_sql(way_id)
            if way_data:
                dtype = way_data[3]  # dialoguetype
                type_lengths[dtype].append(length)

    if not type_lengths:
        logger.warning("No example length data by type")
        return

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 8), dpi=300)

    # Get top types by count
    type_counts = {dtype: len(lengths) for dtype, lengths in type_lengths.items()}
    top_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    top_type_names = [t[0] for t in top_types]

    # Prepare data for plotting
    plot_data = []
    plot_labels = []
    for dtype in top_type_names:
        lengths = type_lengths[dtype]
        plot_data.append(lengths)
        plot_labels.append(f"{dtype}\n(n={len(lengths)})")

    if HAS_SEABORN:
        positions = range(1, len(plot_data) + 1)
        ax.violinplot(plot_data, positions=positions, showmeans=True)
        ax.set_xticks(positions)
        ax.set_xticklabels(plot_labels, rotation=45, ha='right', fontsize=9)
    else:
        # Fallback: box plot
        bp = ax.boxplot(plot_data, labels=plot_labels, patch_artist=True)
        for patch in bp['boxes']:
            patch.set_facecolor('lightblue')
            patch.set_alpha(0.7)

    ax.set_ylabel('Example Length (characters)', fontsize=12)
    ax.set_xlabel('Dialogue Type', fontsize=12)
    ax.set_title('Example Length Distribution by Dialogue Type', fontsize=16, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close(fig)

    log_success(f"Saved example length violin plot: {output_path}", logger)


def main():
    """Main figure generation function."""
    logger.info("=== GENERATING WAYS ANALYSIS FIGURES ===")

    # Ensure output directory exists
    figures_dir = project_root / "output" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    # Generate all figures
    try:
        with log_operation("Figure generation pipeline", logger):
            # 1. Ways network visualization
            ways_network_path = figures_dir / "ways_network.png"
            generate_ways_network_figure(ways_network_path)

            # 2. Room hierarchy visualization
            room_hierarchy_path = figures_dir / "room_hierarchy.png"
            generate_room_hierarchy_figure(room_hierarchy_path)

            # 3. Dialogue type distribution
            type_distribution_path = figures_dir / "type_distribution.png"
            generate_type_distribution_figure(type_distribution_path)

            # 4. Type × Room heatmap
            type_room_heatmap_path = figures_dir / "type_room_heatmap.png"
            generate_type_room_heatmap(type_room_heatmap_path)

            # 5. Partner word cloud
            partner_wordcloud_path = figures_dir / "partner_wordcloud.png"
            generate_partner_wordcloud(partner_wordcloud_path)

            # 6. Framework treemap
            framework_treemap_path = figures_dir / "framework_treemap.png"
            generate_framework_treemap(framework_treemap_path)

            # 7. Example length violin plot
            example_length_violin_path = figures_dir / "example_length_violin.png"
            generate_example_length_violin(example_length_violin_path)

        logger.info("All figures generated successfully!")
        logger.info(f"Output directory: {figures_dir}")

        # Verify files were created and have reasonable sizes
        generated_files = [
            ways_network_path,
            room_hierarchy_path,
            type_distribution_path,
            type_room_heatmap_path,
            partner_wordcloud_path,
            framework_treemap_path,
            example_length_violin_path
        ]

        all_valid = True
        for file_path in generated_files:
            if file_path.exists():
                size_kb = file_path.stat().st_size / 1024
                logger.info(f"✓ {file_path.name}: {size_kb:.1f} KB")
                if size_kb < 10:  # Less than 10KB might indicate issues
                    logger.warning(f"Warning: {file_path.name} is very small ({size_kb:.1f} KB)")
            else:
                logger.error(f"Missing: {file_path.name}")
                all_valid = False

        if all_valid:
            log_success("All figure files validated successfully", logger)
        else:
            logger.error("Some figure files are missing")
            return 1

    except Exception as e:
        logger.error(f"Error generating figures: {e}")
        logger.debug("Full traceback:", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
