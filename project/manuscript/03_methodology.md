# Methodology {#sec:methodology}

## Database Structure and Conversion

### Source Data

The research draws on a MySQL database dump containing 11 tables documenting Andrius Kulikauskas's Ways of Figuring Things Out framework. The primary data table `ways` contains 210 documented ways with the following key fields (see Table \ref{tab:ways_schema}):

- `way`: The name/identifier of the way
- `dialoguewith`: The dialogue partner or conversant
- `dialoguetype`: The type of dialogue (Absolute, Relative, Embrace God)
- `dialoguetypetype`: Sub-type classification
- `mene`: Room assignment in the House of Knowledge (24 rooms)
- `Dievas`: Relationship to God/the divine
- `examples`: Examples and descriptions
- `comments`: Additional comments and notes

\begin{table}[h]
\centering
\begin{tabular}{|l|l|}
\hline
\textbf{Field} & \textbf{Description} \\
\hline
\texttt{way} & The name/identifier of the way \\
\texttt{dialoguewith} & The dialogue partner or conversant \\
\texttt{dialoguetype} & The type of dialogue (Absolute, Relative, Embrace God) \\
\texttt{dialoguetypetype} & Sub-type classification \\
\texttt{mene} & Room assignment in the House of Knowledge (24 rooms) \\
\texttt{Dievas} & Relationship to God/the divine \\
\texttt{examples} & Examples and descriptions \\
\texttt{comments} & Additional comments and notes \\
\hline
\end{tabular}
\caption{Key fields in the \texttt{ways} table schema}
\label{tab:ways_schema}
\end{table}

### SQLite Conversion

For analysis and portability, the MySQL dump was converted to SQLite format. The conversion process:

1. **Schema Conversion**: MySQL-specific syntax (AUTO_INCREMENT, ENGINE, COLLATE) converted to SQLite-compatible syntax
2. **Table Renaming**: Tables renamed for clarity (`20100422ways` → `ways`, `menes` → `rooms`, etc.)
3. **Index Handling**: Index names adjusted to avoid conflicts with table names (SQLite restriction)
4. **Data Preservation**: All data preserved during conversion with proper encoding handling

The resulting SQLite database (`db/ways.db`) provides a portable, queryable format for analysis. The complete database schema is documented in Section \ref{sec:appendix} (Appendix A).

### Implementation Modules

The analysis is implemented using several specialized modules in `project/src/`:

- **`database.py`**: SQLAlchemy ORM models for Ways, Rooms, Questions, and database access
- **`sql_queries.py`**: Pre-built SQL queries for common analysis operations
- **`ways_analysis.py`**: High-level ways characterization and analysis functions
- **`network_analysis.py`**: Graph-based network analysis of way relationships
- **`house_of_knowledge.py`**: Analysis of the 24-room House of Knowledge framework
- **`statistics.py`**: Statistical analysis functions including `analyze_way_distributions()`, `compute_way_correlations()`, `compute_way_diversity_metrics()`
- **`metrics.py`**: Performance metrics including `compute_way_coverage_metrics()`, `compute_way_interconnectedness()`
- **`models.py`**: Data classes and enums for type-safe data handling

## House of Knowledge Framework

### 24-Room Structure

The Ways framework organizes knowledge into 24 rooms within the "House of Knowledge." Each room represents a different aspect of how we come to know and understand:

\begin{equation}\label{eq:house_structure}
\text{House of Knowledge} = \{\text{Room}_1, \text{Room}_2, \ldots, \text{Room}_{24}\}
\end{equation}

The rooms are organized according to three fundamental structures:

1. **Believing (1-2-3-4)**: Four levels of belief structure
2. **Caring (1-2-3-4)**: Four levels of care structure  
3. **Relative Learning**: The cycle of taking a stand, following through, and reflecting

### Room Categories

Each way is assigned to one or more rooms via the `mene` field, creating a mapping:

\begin{equation}\label{eq:way_room_mapping}
\text{Way}_i \mapsto \{\text{Room}_j : \text{Way}_i \text{ belongs to Room}_j\}
\end{equation}

This mapping enables analysis of how ways cluster within rooms and how rooms relate to one another.

## Dialogue Type Classification

### Three Main Types

Ways are classified according to three primary dialogue types:

1. **Absolute**: Ways that reference absolute truth or structure
2. **Relative**: Ways that engage with relative perspectives
3. **Embrace God**: Ways that explicitly engage with the divine or transcendent

The distribution of ways across dialogue types provides insight into the balance of different epistemological approaches in the framework.

### Dialogue Type Analysis

For each way $w_i$, we extract:

\begin{equation}\label{eq:dialogue_type}
\text{Type}(w_i) \in \{\text{Absolute}, \text{Relative}, \text{Embrace God}\}
\end{equation}

This classification enables statistical analysis of type distributions and relationships.

## Network Analysis Methodology

### Graph Construction

We construct a weighted network graph $G = (V, E, w)$ where:

- **Vertices $V$**: Each way $w_i$ is a node $v_i \in V$, with $|V| = 210$
- **Edges $E$**: Connections between ways based on:
  - Shared dialogue partners (`dialoguewith`): $e_{ij} \in E$ if $\text{dialoguewith}(w_i) = \text{dialoguewith}(w_j)$
  - Shared room assignments (`mene`): $e_{ij} \in E$ if $\text{mene}(w_i) = \text{mene}(w_j)$
  - Similar dialogue types: $e_{ij} \in E$ if $\text{dialoguetype}(w_i) = \text{dialoguetype}(w_j)$
  - Question relationships (`klausimobudai` table): $e_{ij} \in E$ if $\exists q: (w_i, q) \in Q \land (w_j, q) \in Q$
- **Edge weights $w$**: $w(e_{ij}) \in \{0.6, 0.8, 1.0\}$ based on relationship type (type, partner, room respectively)

The resulting network contains $|E| = 1,290$ edges connecting the 210 ways.

### Centrality Metrics

We compute several centrality metrics to identify important ways:

**Degree Centrality:**
\begin{equation}\label{eq:degree_centrality}
C_D(v) = \frac{\deg(v)}{|V| - 1}
\end{equation}

**Betweenness Centrality:**
\begin{equation}\label{eq:betweenness_centrality}
C_B(v) = \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}
\end{equation}

where $\sigma_{st}$ is the number of shortest paths from $s$ to $t$, and $\sigma_{st}(v)$ is the number of those paths passing through $v$.

**Clustering Coefficient:**
\begin{equation}\label{eq:clustering}
C_C(v) = \frac{2e_v}{k_v(k_v - 1)}
\end{equation}

where $e_v$ is the number of edges between neighbors of $v$, and $k_v$ is the degree of $v$.

## Statistical Analysis Methods

### Distribution Analysis

We analyze the distribution of ways across:

1. **Dialogue Types**: Count and percentage by type, with 38 distinct types observed
2. **Rooms**: Distribution across 24 rooms, with B2 containing the most ways (23)
3. **Dialogue Partners**: Frequency of conversants, with 196 unique partners
4. **God Relationships**: Distribution of `Dievas` values

### Information-Theoretic Metrics

We compute Shannon entropy to quantify the diversity of distributions:

\begin{equation}\label{eq:entropy}
H(X) = -\sum_{i=1}^{k} p_i \log_2(p_i)
\end{equation}

where $p_i$ is the proportion in category $i$ and $k$ is the number of categories.

**Mutual Information** between dialogue types and rooms:

\begin{equation}\label{eq:mutual_info}
I(X;Y) = \sum_{x,y} p(x,y) \log_2 \frac{p(x,y)}{p(x)p(y)}
\end{equation}

This quantifies the strength of association between dialogue types and room assignments.

### Cross-Tabulation

Cross-tabulation analysis examines relationships between:

- Dialogue type × Room assignment (visualized in Figure \ref{fig:type_room_heatmap})
- Dialogue type × Dialogue partner
- Room × God relationship

This reveals patterns in how different dimensions of the framework relate, with the cross-tabulation matrix showing concentrations of ways at specific type-room intersections.

## Text Analysis

### Way Descriptions

For ways with text descriptions in `ways.md`, we perform:

1. **Keyword Extraction**: Identify key terms and concepts
2. **Theme Analysis**: Extract recurring themes
3. **Example Analysis**: Analyze examples to understand way applications
4. **Relationship Extraction**: Identify references to other ways or concepts

### Philosophical Structure Analysis

Text analysis also examines:

- How ways relate to the believing/caring/learning structures
- References to the House of Knowledge framework
- Connections to broader philosophical concepts

## Data Processing Pipeline

### Extraction

1. **Database Query**: Extract ways data from SQLite database
2. **Text Parsing**: Parse `ways.md` for additional context
3. **Relationship Extraction**: Build network from relationship tables

### Transformation

1. **Normalization**: Standardize way names and categories
2. **Encoding**: Handle Lithuanian/English text encoding
3. **Cleaning**: Remove duplicates and handle missing data

### Analysis

1. **Statistical Computation**: Calculate distributions and metrics
2. **Network Construction**: Build graph structures
3. **Visualization Generation**: Create plots and network diagrams

## Validation Framework

### Data Quality Checks

1. **Completeness**: Verify all ways have required fields
2. **Consistency**: Check for conflicting assignments
3. **Referential Integrity**: Validate room and relationship references

### Analysis Validation

1. **Reproducibility**: Ensure analyses are reproducible
2. **Sensitivity**: Test sensitivity to data variations
3. **Robustness**: Verify results are robust to missing data

## SQL Query Examples

Key analyses are performed using SQL queries against the SQLite database. Example queries include:

**Dialogue Type Distribution:**
```sql
SELECT dialoguetype, COUNT(*) as count
FROM ways
GROUP BY dialoguetype
ORDER BY count DESC;
```

**Room-Way Cross-Tabulation:**
```sql
SELECT dialoguetype, mene, COUNT(*) as count
FROM ways
WHERE mene != '' AND dialoguetype != ''
GROUP BY dialoguetype, mene
ORDER BY count DESC;
```

**Network Edge Construction (Room-based):**
```sql
SELECT w1.ID as way1_id, w2.ID as way2_id
FROM ways w1
JOIN ways w2 ON w1.mene = w2.mene
WHERE w1.ID < w2.ID AND w1.mene != '';
```

**Central Ways Identification:**
```sql
SELECT way, COUNT(*) as connection_count
FROM (
    SELECT w1.way, w2.ID
    FROM ways w1
    JOIN ways w2 ON w1.mene = w2.mene
    WHERE w1.ID != w2.ID AND w1.mene != ''
    UNION
    SELECT w1.way, w2.ID
    FROM ways w1
    JOIN ways w2 ON w1.dialoguewith = w2.dialoguewith
    WHERE w1.ID != w2.ID AND w1.dialoguewith != ''
)
GROUP BY way
ORDER BY connection_count DESC
LIMIT 10;
```

## Implementation

The analysis is implemented using several specialized Python modules:

### Core Analysis Modules
- **`database.py`**: SQLAlchemy ORM with `WaysDatabase` class for database access
- **`sql_queries.py`**: `WaysSQLQueries` class with pre-built analysis queries
- **`ways_analysis.py`**: `WaysAnalyzer` class for comprehensive ways characterization
- **`network_analysis.py`**: `WaysNetworkAnalyzer` class for graph-based relationship analysis
- **`house_of_knowledge.py`**: Framework analysis for the 24-room House of Knowledge
- **`statistics.py`**: Statistical functions including `analyze_way_distributions()`, `compute_way_correlations()`
- **`metrics.py`**: Performance metrics including `compute_way_coverage_metrics()`, `compute_way_interconnectedness()`

### Infrastructure
- **Python 3.10+**: Primary analysis language
- **SQLite**: Database backend via SQLAlchemy ORM
- **NetworkX**: Network analysis and graph algorithms
- **Matplotlib/Seaborn**: Statistical visualization and plotting
- **NumPy/Pandas**: Numerical computing and data manipulation

All code follows the thin orchestrator pattern, with business logic in `project/src/` modules and orchestration in `project/scripts/`.

## Ethical Considerations

This research documents and analyzes publicly available philosophical work by Andrius Kulikauskas. All data is in the public domain as stated in the source documentation. The analysis respects the original philosophical framework while providing systematic documentation and quantitative insights.
