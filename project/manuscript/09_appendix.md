# Appendix {#sec:appendix}

This appendix provides additional technical details supporting the main results.

## A. Database Schema Details

### A.1 Complete Table Schemas

#### Ways Table Schema

```sql
CREATE TABLE ways (
    way TEXT NOT NULL,
    dialoguewith TEXT NOT NULL,
    dialoguetype TEXT NOT NULL,
    dialoguetypetype TEXT NOT NULL,
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    wayurl TEXT NOT NULL,
    examples TEXT NOT NULL,
    dialoguetypetypetype TEXT NOT NULL,
    mene TEXT NOT NULL,
    Dievas TEXT NOT NULL,
    comments TEXT NOT NULL,
    laikinas TEXT NOT NULL
);
```

#### Rooms Table Schema

```sql
CREATE TABLE rooms (
    santrumpa TEXT NOT NULL PRIMARY KEY,
    savoka TEXT NOT NULL,
    issiaiskinimas TEXT NOT NULL,
    -- Additional fields for ordering and relationships
);
```

### A.2 Index Definitions

Key indexes for performance:

- Index on `way` for way lookups
- Index on `mene` for room-based queries
- Index on `dialoguetype` for type filtering
- Index on `dialoguewith` for partner analysis

## B. Network Analysis Algorithms

### B.1 Actual Network Metrics

The network analysis was performed using NetworkX on the complete ways database:

**Network Structure:**
- **Nodes**: 210 ways
- **Edges**: 1,290 connections
- **Average degree**: 12.29 connections per way
- **Network density**: 0.058 (5.8\% of possible edges present)
- **Clustering coefficient**: 0.886 (high local clustering)
- **Connected components**: Multiple components detected
- **Largest component**: Contains majority of ways

**Centrality Metrics:**
- **Degree centrality**: Range from 0.0 to 0.162 (way 84, 156, 211 with highest degree: 34)
- **Betweenness centrality**: Identifies bridge ways connecting different communities
- **Closeness centrality**: Measures average distance to all other ways
- **Eigenvector centrality**: Identifies ways connected to highly central ways

**Community Detection:**
- Modularity-based community detection reveals natural clusters
- Communities correspond to room assignments and dialogue types
- Largest communities align with most populated rooms (B2, C4, R)

### B.2 Graph Construction Implementation

The network is constructed using `WaysNetworkAnalyzer` with three edge types:

```python
from collections import defaultdict
import networkx as nx
from src.models import Way

def _build_ways_network(ways: List[Way]) -> nx.Graph:
    """Build network graph from ways data.
    
    Edges are created based on:
    1. Same room (weight=1.0, edge_type='same_room')
    2. Same dialogue partner (weight=0.8, edge_type='same_partner')
    3. Same dialogue type (weight=0.6, edge_type='same_type')
    """
    G = nx.Graph()
    
    # Add nodes with attributes
    for way in ways:
        G.add_node(way.id, 
                   way_text=way.way,
                   room=way.mene,
                   dialogue_type=way.dialoguetype,
                   dialogue_partner=way.dialoguewith)
    
    # Group ways by room
    room_ways = defaultdict(list)
    for way in ways:
        room_ways[way.mene].append(way.id)
    
    # Add room edges (highest weight)
    for room, way_ids in room_ways.items():
        if len(way_ids) > 1:
            for i, way1_id in enumerate(way_ids):
                for way2_id in way_ids[i+1:]:
                    G.add_edge(way1_id, way2_id, 
                              edge_type='same_room',
                              room=room,
                              weight=1.0)
    
    # Add partner edges (medium weight)
    partner_ways = defaultdict(list)
    for way in ways:
        partner_ways[way.dialoguewith].append(way.id)
    
    for partner, way_ids in partner_ways.items():
        if len(way_ids) > 1:
            for i, way1_id in enumerate(way_ids):
                for way2_id in way_ids[i+1:]:
                    if not G.has_edge(way1_id, way2_id):
                        G.add_edge(way1_id, way2_id,
                                  edge_type='same_partner',
                                  partner=partner,
                                  weight=0.8)
    
    # Add type edges (lowest weight)
    type_ways = defaultdict(list)
    for way in ways:
        type_ways[way.dialoguetype].append(way.id)
    
    for dtype, way_ids in type_ways.items():
        if len(way_ids) > 1:
            for i, way1_id in enumerate(way_ids):
                for way2_id in way_ids[i+1:]:
                    if not G.has_edge(way1_id, way2_id):
                        G.add_edge(way1_id, way2_id,
                                  edge_type='same_type',
                                  dialogue_type=dtype,
                                  weight=0.6)
    
    return G
```

### B.3 Centrality Computation

Centrality metrics are computed using NetworkX functions within `WaysNetworkAnalyzer.compute_centrality_metrics()`:

- `nx.degree_centrality(G)`: Normalized degree (0-1 range)
- `nx.betweenness_centrality(G)`: Bridge identification
- `nx.closeness_centrality(G)`: Average path length
- `nx.eigenvector_centrality(G, max_iter=1000)`: Influence propagation
- `nx.average_clustering(G)`: Local clustering coefficient

The implementation handles edge cases (disconnected graphs, single nodes) and returns a `NetworkMetrics` dataclass with all computed values.

## C. Statistical Analysis Formulas

### C.1 Distribution Metrics

For a categorical variable with $k$ categories:

\begin{equation}\label{eq:entropy_appendix}
H(X) = -\sum_{i=1}^{k} p_i \log_2(p_i)
\end{equation}

where $p_i$ is the proportion in category $i$.

### C.2 Association Measures

For cross-tabulation analysis:

\begin{equation}\label{eq:cramers_v}
V = \sqrt{\frac{\chi^2}{n \min(r-1, c-1)}}
\end{equation}

where $\chi^2$ is the chi-square statistic, $n$ is sample size, and $r$, $c$ are row and column counts.

## D. Visualization Specifications

### D.1 Network Visualization Parameters

- **Layout Algorithm**: Force-directed (Fruchterman-Reingold)
- **Node Size**: Proportional to centrality score
- **Node Color**: By dialogue type
- **Edge Width**: By relationship strength
- **Edge Color**: By relationship type

### D.2 Color Schemes

- **Dialogue Types**: 
  - Absolute: Blue shades
  - Relative: Green shades
  - Embrace God: Purple shades

- **Rooms**: Sequential color scheme for 24 rooms

## E. Data Processing Pipeline

### E.1 Database Initialization

```python
from src.database import WaysDatabase, initialize_database

def setup_ways_database(mysql_dump_path: str = None, 
                        sqlite_path: str = "project/db/ways.db") -> WaysDatabase:
    """Initialize SQLite database from MySQL dump or existing database.
    
    Args:
        mysql_dump_path: Path to MySQL dump file (optional)
        sqlite_path: Path to SQLite database file
        
    Returns:
        Initialized WaysDatabase instance
    """
    if mysql_dump_path:
        # Convert MySQL dump to SQLite
        initialize_database(mysql_dump_path, sqlite_path)
    
    # Return database connection
    db = WaysDatabase(sqlite_path)
    
    # Validate database integrity
    stats = db.get_way_statistics()
    assert stats['total_ways'] > 0, "Database must contain ways"
    
    return db
```

### E.2 Data Access and Querying

```python
from src.database import WaysDatabase
from src.sql_queries import WaysSQLQueries
from src.models import Way

def query_ways_data(db_path: str = "project/db/ways.db") -> Dict[str, Any]:
    """Query ways data using SQL queries module.
    
    Returns:
        Dictionary with ways, rooms, and statistics
    """
    db = WaysDatabase(db_path)
    queries = WaysSQLQueries(db_path)
    
    # Get all ways
    _, ways_data = queries.get_all_ways_sql()
    ways = [Way.from_sqlalchemy(row) for row in ways_data]
    
    # Get room distribution
    _, room_counts = queries.count_ways_by_room_sql()
    room_dist = {room: count for room, count in room_counts}
    
    # Get type distribution
    _, type_counts = queries.count_ways_by_type_sql()
    type_dist = {dtype: count for dtype, count in type_counts}
    
    # Get cross-tabulation
    _, crosstab = queries.cross_tabulate_type_room_sql()
    
    return {
        'ways': ways,
        'room_distribution': room_dist,
        'type_distribution': type_dist,
        'crosstab': crosstab,
        'total_ways': len(ways)
    }
```

### E.3 Analysis Script

The comprehensive analysis script integrates multiple analysis modules:

```python
from src.ways_analysis import WaysAnalyzer
from src.network_analysis import WaysNetworkAnalyzer
from src.database import WaysDatabase
from src.sql_queries import WaysSQLQueries

def analyze_ways_comprehensive(db_path: str = None) -> Dict[str, Any]:
    """Comprehensive analysis of ways database.
    
    Args:
        db_path: Optional path to SQLite database
        
    Returns:
        Dictionary containing all analysis results
    """
    # Initialize analyzers
    analyzer = WaysAnalyzer(db_path)
    network_analyzer = WaysNetworkAnalyzer(db_path)
    db = WaysDatabase(db_path)
    queries = WaysSQLQueries(db_path)
    
    # Distribution analysis
    characterization = analyzer.characterize_ways()
    type_dist = characterization.dialogue_types
    room_dist = characterization.room_distribution
    
    # Network analysis
    network = network_analyzer.build_ways_network()
    metrics = network_analyzer.compute_centrality_metrics()
    central_ways = network_analyzer.find_central_ways()
    
    # Statistical analysis
    _, crosstab_results = queries.cross_tabulate_type_room_sql()
    crosstab = {}
    for dtype, room, count in crosstab_results:
        if dtype not in crosstab:
            crosstab[dtype] = {}
        crosstab[dtype][room] = count
    
    return {
        'characterization': {
            'total_ways': characterization.total_ways,
            'room_diversity': characterization.room_diversity,
            'type_diversity': characterization.type_diversity,
            'most_common_room': characterization.most_common_room,
            'most_common_type': characterization.most_common_type
        },
        'network_metrics': {
            'node_count': metrics.node_count,
            'edge_count': metrics.edge_count,
            'density': metrics.density,
            'average_degree': metrics.average_degree,
            'clustering_coefficient': metrics.clustering_coefficient
        },
        'central_ways': {
            'by_degree': central_ways.by_degree[:10],
            'by_betweenness': central_ways.by_betweenness[:10]
        },
        'crosstab': crosstab
    }
```

## F. Validation Procedures

### F.1 Data Quality Checks

1. **Completeness Check**: Verify all required fields present
2. **Consistency Check**: Check for conflicting assignments
3. **Referential Integrity**: Validate foreign key relationships
4. **Encoding Check**: Verify UTF-8 encoding

### F.2 Analysis Validation

1. **Reproducibility**: Fixed random seeds, deterministic algorithms
2. **Sensitivity**: Test with missing data, parameter variations
3. **Robustness**: Verify results stable under different conditions
4. **Cross-Validation**: Validate findings across data subsets

## G. Computational Environment

### G.1 Software Versions

- Python 3.10+
- SQLite 3.x
- NetworkX 2.x+
- Pandas 1.x+
- Matplotlib 3.x+
- NumPy 1.x+

### G.2 Hardware Requirements

- Minimum: 4GB RAM, single core
- Recommended: 8GB+ RAM, multi-core
- Storage: ~100MB for database and outputs

## H. Additional Tables and Figures

### H.1 Extended Distribution Tables

#### Complete Room Distribution

The complete distribution of all 24 rooms in the House of Knowledge:

\begin{table}[h]
\centering
\small
\begin{tabular}{|l|c|c||l|c|c|}
\hline
\textbf{Room} & \textbf{Count} & \textbf{\%} & \textbf{Room} & \textbf{Count} & \textbf{\%} \\
\hline
B2 & 23 & 11.0\% & C2 & 7 & 3.3\% \\
C4 & 17 & 8.1\% & B4 & 7 & 3.3\% \\
R & 16 & 7.6\% & 1 & 7 & 3.3\% \\
32 & 13 & 6.2\% & F & 6 & 2.9\% \\
C3 & 13 & 6.2\% & 20 & 5 & 2.4\% \\
BB & 12 & 5.7\% & A & 4 & 1.9\% \\
CB & 10 & 4.8\% & 30 & 4 & 1.9\% \\
21 & 9 & 4.3\% & BC & 3 & 1.4\% \\
B3 & 9 & 4.3\% & B & 1 & 0.5\% \\
CC & 9 & 4.3\% & C & 1 & 0.5\% \\
O & 9 & 4.3\% & & & \\
T & 9 & 4.3\% & & & \\
10 & 8 & 3.8\% & & & \\
31 & 8 & 3.8\% & & & \\
\hline
\multicolumn{3}{|c||}{\textbf{Total}} & \multicolumn{3}{c|}{\textbf{210 (100\%)}} \\
\hline
\end{tabular}
\caption{Complete distribution of ways across all 24 rooms}
\label{tab:complete_room_distribution}
\end{table}

#### Complete Dialogue Type Distribution

The complete distribution of all 38 dialogue types (presented in two parts):

\begin{table}[h]
\centering
\small
\begin{tabular}{|l|c|c||l|c|c|}
\hline
\textbf{Type} & \textbf{Count} & \textbf{\%} & \textbf{Type} & \textbf{Count} & \textbf{\%} \\
\hline
goodness & 15 & 7.1\% & my mind & 7 & 3.3\% \\
other & 15 & 7.1\% & opposing view & 7 & 3.3\% \\
regularity & 11 & 5.2\% & unknown & 7 & 3.3\% \\
I & 9 & 4.3\% & conviction & 5 & 2.4\% \\
answer & 9 & 4.3\% & interlocutor & 5 & 2.4\% \\
knowledge & 8 & 3.8\% & my fate & 5 & 2.4\% \\
life & 8 & 3.8\% & my knowledge & 5 & 2.4\% \\
mind & 8 & 3.8\% & my purpose & 5 & 2.4\% \\
God & 6 & 2.9\% & wholeness & 5 & 2.4\% \\
divineness & 6 & 2.9\% & behavior & 4 & 1.9\% \\
purpose & 6 & 2.9\% & capability & 4 & 1.9\% \\
solution & 6 & 2.9\% & God's perspective & 4 & 1.9\% \\
God's perspective & 4 & 1.9\% & inspiration & 4 & 1.9\% \\
possibilities & 4 & 1.9\% & possibility & 4 & 1.9\% \\
self-check & 4 & 1.9\% & structure & 4 & 1.9\% \\
\hline
\end{tabular}
\caption{Dialogue type distribution (Part 1: Top 19 types)}
\label{tab:type_distribution_part1}
\end{table}

\begin{table}[h]
\centering
\small
\begin{tabular}{|l|c|c||l|c|c|}
\hline
\textbf{Type} & \textbf{Count} & \textbf{\%} & \textbf{Type} & \textbf{Count} & \textbf{\%} \\
\hline
conditionality & 3 & 1.4\% & invalidity & 2 & 1.0\% \\
example & 3 & 1.4\% & misfortune & 2 & 1.0\% \\
given & 3 & 1.4\% & phenomenon & 2 & 1.0\% \\
impossibility & 3 & 1.4\% & depths & 1 & 0.5\% \\
& & & infinity & 1 & 0.5\% \\
\hline
\multicolumn{3}{|c||}{\textbf{Total}} & \multicolumn{3}{c|}{\textbf{210 (100\%)}} \\
\hline
\end{tabular}
\caption{Dialogue type distribution (Part 2: Remaining 19 types)}
\label{tab:type_distribution_part2}
\end{table}

#### Top Cross-Tabulation Combinations

The most frequent dialogue type × room combinations:

\begin{table}[h]
\centering
\small
\begin{tabular}{|l|l|c|}
\hline
\textbf{Dialogue Type} & \textbf{Room} & \textbf{Count} \\
\hline
goodness & B2 & 3 \\
goodness & R & 3 \\
goodness & T & 2 \\
I & O & 9 \\
answer & 1 & 4 \\
answer & 32 & 2 \\
knowledge & CC & 8 \\
divineness & C4 & 6 \\
God & B2 & 5 \\
God's perspective & R & 4 \\
capability & B3 & 4 \\
inspiration & B4 & 4 \\
conviction & B3 & 5 \\
\hline
\end{tabular}
\caption{Top dialogue type × room combinations (count ≥ 2)}
\label{tab:top_crosstab}
\end{table}

### H.2 Extended Network Visualizations

#### Ways Network Visualization

Figure \ref{fig:ways_network} shows the complete network graph of 210 ways with 1,290 edges. The visualization uses a force-directed layout (Fruchterman-Reingold algorithm) with:
- **Node colors**: Coded by dialogue type (38 distinct types)
- **Node sizes**: Proportional to degree centrality
- **Edge types**: Three relationship types (same room: weight 1.0, same partner: weight 0.8, same type: weight 0.6)
- **Layout**: Optimized for visual clarity with community clustering visible

The network exhibits high clustering (coefficient: 0.886) indicating strong room-based communities. The largest connected component contains the majority of ways, with smaller isolated components representing specialized dialogue patterns.

#### Room Hierarchy Visualization

Figure \ref{fig:room_hierarchy} presents a hierarchical bar chart showing the distribution of ways across all 24 rooms. The visualization organizes rooms by their position in the House of Knowledge framework, revealing:
- **Most populated rooms**: B2 (23 ways), C4 (17 ways), R (16 ways)
- **Framework structure**: Clear patterns in believing (B-series) and caring (C-series) hierarchies
- **Relative learning rooms**: R (Reflecting), O (Obeying), T (Taking a Stand) show balanced distributions

#### Framework Treemap

Figure \ref{fig:framework_treemap} provides a treemap visualization of the framework structure, where:
- **Area**: Proportional to number of ways in each room
- **Color**: Indicates framework category (believing, caring, relative learning)
- **Hierarchy**: Shows nested relationships within the House of Knowledge

This visualization highlights the structural organization of the framework and the relative emphasis on different aspects of knowledge acquisition.

### H.3 Extended Statistical Plots

#### Dialogue Type Distribution

Figure \ref{fig:type_distribution} displays a bar chart of all 38 dialogue types ranked by frequency. The visualization shows:
- **Top types**: "goodness" and "other" (15 each, 7.1\%), "regularity" (11, 5.2\%)
- **Distribution pattern**: Long tail with many types having 1-4 occurrences
- **Balance**: Relatively even distribution across types, indicating diverse epistemological approaches

#### Type × Room Heatmap

Figure \ref{fig:type_room_heatmap} presents a heatmap of the cross-tabulation between dialogue types (rows) and rooms (columns). The visualization reveals:
- **Hotspots**: Strong associations between specific types and rooms (e.g., "I" × "O", "knowledge" × "CC")
- **Sparse regions**: Many type-room combinations have zero or low counts
- **Patterns**: Clustering of similar dialogue types in related rooms

This heatmap provides insight into how dialogue types are distributed across the House of Knowledge structure.

#### Dialogue Partner Word Cloud

Figure \ref{fig:partner_wordcloud} shows a word cloud visualization of dialogue partners, where:
- **Font size**: Proportional to frequency of partnership
- **196 unique partners**: Most partners appear only once or twice
- **Top partners**: "God's will", "God's wishes", "answer", "circumstances" (2 occurrences each)

The word cloud highlights the diversity of dialogue partners and the personalized nature of many ways.

#### Example Length Distribution

Figure \ref{fig:example_length_violin} displays a violin plot showing the distribution of example text lengths by dialogue type. The visualization shows:
- **Distribution shape**: Varies by dialogue type, with some types having longer examples
- **Average length**: 80.2 characters across all ways
- **Coverage**: All 210 ways have examples (100\% coverage)

This plot reveals patterns in how different dialogue types are exemplified and documented.

## I. Code Availability

All code for this research is available in the project repository:

- **Database Module**: `project/src/database.py`
- **Models**: `project/src/models.py`
- **Analysis Scripts**: `project/scripts/`
- **Tests**: `project/tests/`

The code follows the thin orchestrator pattern with business logic in `src/` modules and orchestration in `scripts/`.

## J. Data Availability

The source data (MySQL dump and `ways.md`) are in the public domain as stated in the original documentation. The converted SQLite database and analysis results are available upon request or through the project repository.

## K. Reproducibility

To reproduce the analyses:

1. Initialize database: `python scripts/db_setup.py`
2. Run analysis: `python scripts/analysis_pipeline.py`
3. Generate visualizations: `python scripts/generate_figures.py`
4. Build manuscript: `python scripts/03_render_pdf.py`

All random operations use fixed seeds for reproducibility.
