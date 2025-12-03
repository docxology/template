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

### B.1 Graph Construction Pseudocode

```python
def construct_network(ways):
    G = nx.Graph()
    
    # Add nodes
    for way in ways:
        G.add_node(way.id, **way.attributes)
    
    # Add edges based on shared characteristics
    for i, way1 in enumerate(ways):
        for way2 in ways[i+1:]:
            if share_dialogue_partner(way1, way2):
                G.add_edge(way1.id, way2.id, type='dialogue')
            if share_room(way1, way2):
                G.add_edge(way1.id, way2.id, type='room')
            if share_question(way1, way2):
                G.add_edge(way1.id, way2.id, type='question')
    
    return G
```

### B.2 Centrality Computation

Centrality metrics computed using NetworkX:

- `nx.degree_centrality(G)`: Degree centrality
- `nx.betweenness_centrality(G)`: Betweenness centrality
- `nx.closeness_centrality(G)`: Closeness centrality
- `nx.eigenvector_centrality(G)`: Eigenvector centrality

## C. Statistical Analysis Formulas

### C.1 Distribution Metrics

For a categorical variable with $k$ categories:

\begin{equation}\label{eq:entropy}
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

### E.1 Extraction Script

```python
def extract_ways_data(db_path):
    db = WaysDatabase(db_path)
    ways = db.get_all_ways()
    return ways
```

### E.2 Transformation Script

```python
def transform_ways(ways):
    normalized = []
    for way in ways:
        normalized.append({
            'id': way.id,
            'name': normalize_name(way.way),
            'type': way.dialoguetype,
            'room': way.mene,
            # ... other fields
        })
    return normalized
```

### E.3 Analysis Script

```python
def analyze_ways(ways):
    # Distribution analysis
    type_dist = count_by_type(ways)
    room_dist = count_by_room(ways)
    
    # Network analysis
    G = construct_network(ways)
    centrality = compute_centrality(G)
    
    # Statistical analysis
    crosstab = cross_tabulate(ways, 'type', 'room')
    
    return {
        'distributions': {'type': type_dist, 'room': room_dist},
        'network': G,
        'centrality': centrality,
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

[Additional detailed distribution tables would appear here]

### H.2 Extended Network Visualizations

[Additional network visualizations would appear here]

### H.3 Extended Statistical Plots

[Additional statistical plots would appear here]

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
