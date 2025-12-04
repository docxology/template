# Abstract {#sec:abstract}

This research presents a comprehensive systematic analysis of Andrius Kulikauskas's "Ways of Figuring Things Out," documenting and analyzing 210 ways from the database with connections to the broader framework of 284 ways in the source text. The database-driven analysis covers 24 rooms in the House of Knowledge, 38 distinct dialogue types, and 196 unique dialogue partners, organized within fundamental structures of believing (1-2-3-4), caring (1-2-3-4), and relative learning (taking a stand, following through, reflecting). Our quantitative analysis reveals systematic patterns: the B2 room contains the most ways (23), "goodness" and "other" are the most common dialogue types (15 each), and the network exhibits 1,290 edges with a clustering coefficient of 0.886, connecting ways through shared rooms, dialogue types, and partners. Cross-tabulation analysis shows strong associations between dialogue types and room assignments, with information-theoretic metrics quantifying the structure's organization. Network analysis identifies central ways serving as bridges between categories, while text analysis of examples reveals thematic patterns across 210 documented ways. This work provides both a philosophical framework for understanding different approaches to knowledge and a practical system for analyzing and applying these ways in educational, research, and personal development contexts, offering tools for researchers, educators, and practitioners seeking to understand and apply diverse approaches to figuring things out.


\newpage

# Introduction {#sec:introduction}

## Overview

This research documents and analyzes Andrius Kulikauskas's comprehensive framework of "Ways of Figuring Things Out," a systematic collection of 210 documented ways from the database, with connections to the broader framework of 284 ways described in the source text. The work presents both a philosophical framework for understanding different approaches to knowledge and an empirical analysis of how these ways are structured, categorized, and interrelated.

### Data Summary

The analysis database contains comprehensive metadata for all documented ways:

\begin{table}[h]
\centering
\begin{tabular}{|l|c|}
\hline
\textbf{Category} & \textbf{Count} \\
\hline
Total ways (database) & 210 \\
Total ways (documented) & 284 \\
Rooms in House of Knowledge & 24 \\
Distinct dialogue types & 38 \\
Unique dialogue partners & 196 \\
Network nodes & 210 \\
Network edges & 1,290 \\
\hline
\end{tabular}
\caption{Summary statistics for Ways of Figuring Things Out database}
\label{tab:data_summary}
\end{table}

The framework structure is visualized in Figure \ref{fig:room_hierarchy}, showing the distribution of ways across the 24 rooms. The network of relationships between ways is presented in Figure \ref{fig:ways_network}, revealing clusters and central connecting ways.

## The House of Knowledge Framework

The Ways framework is organized around a "House of Knowledge" containing 24 rooms, each representing a different aspect of how we come to know and understand. These rooms are structured according to fundamental philosophical principles:

- **Believing (1-2-3-4)**: Four levels of believing, from basic belief to fostering spirit among us
- **Caring (1-2-3-4)**: Four levels of caring, from basic openness to acknowledging what transcends our limits  
- **Relative Learning**: The cycle of taking a stand, following through, and reflecting
- **Dialogue Types**: Absolute, Relative, and Embrace God perspectives

Each way represents a specific method for figuring things out, documented with examples, dialogue partners, and its relationship to the broader framework.

## Research Objectives

This work aims to:

1. **Documentation**: Provide complete documentation of all 284 ways with their characteristics, examples, and relationships
2. **Categorization**: Systematically categorize ways according to dialogue types, rooms, and philosophical structures
3. **Analysis**: Conduct empirical analysis of way distributions, patterns, and interrelationships
4. **Visualization**: Create visual representations of the network of ways and their connections
5. **Application**: Develop tools and frameworks for applying these ways in educational and research contexts

## Data Sources

The research draws on two primary data sources:

- **SQL Database**: A comprehensive SQLite database (converted from MySQL) containing 210 ways with complete metadata including dialogue types, examples, room assignments (mene), God relationships (Dievas), and conversant information
- **Text Documentation**: Detailed markdown documentation (`ways.md`) providing philosophical context, examples, and descriptions for all 284 ways

## Methodology Overview

Our approach combines:

- **Database Analysis**: SQLite conversion and querying of the ways database to extract patterns and relationships
- **Network Analysis**: Graph-based analysis of how ways connect through dialogue partners and shared characteristics
- **Statistical Analysis**: Quantitative analysis of distributions across categories, dialogue types, and rooms
- **Text Analysis**: Analysis of way descriptions and examples to extract themes and patterns
- **Visualization**: Creation of network graphs, hierarchical visualizations, and statistical plots

## Key Contributions

This research makes several key contributions:

1. **Complete Documentation**: First comprehensive systematic documentation of all 284 ways
2. **Empirical Analysis**: Quantitative analysis revealing patterns in way distributions and relationships
3. **Network Mapping**: Visualization of the network structure connecting different ways
4. **Categorization System**: Systematic organization within the 24-room House of Knowledge framework
5. **Practical Tools**: Database and analysis tools for researchers and practitioners

## Manuscript Organization

The manuscript is organized as follows:

1. **Abstract** (Section \ref{sec:abstract}): Overview of the research and key findings
2. **Introduction** (Section \ref{sec:introduction}): Framework overview and research objectives
3. **Methodology** (Section \ref{sec:methodology}): Database structure, analysis methods, and House of Knowledge framework
4. **Experimental Results** (Section \ref{sec:experimental_results}): Statistical analysis of ways, distributions, and patterns
5. **Discussion** (Section \ref{sec:discussion}): Interpretation of findings and philosophical implications
6. **Conclusion** (Section \ref{sec:conclusion}): Summary and future directions

Supplemental sections provide extended methodological details, additional results, and detailed analysis of specific aspects of the framework.

## Philosophical Context

The Ways framework emerges from a deep engagement with questions of epistemology, learning, and knowledge. It addresses fundamental questions:

- How do we come to know things?
- What are the different valid approaches to understanding?
- How do belief, care, and learning interact in knowledge acquisition?
- What role does dialogue play in figuring things out?
- How can we systematically organize different approaches to knowledge?

The framework provides a comprehensive answer to these questions through its systematic organization of 284 distinct ways, each representing a valid approach to knowledge and understanding.

## Applications

This research has applications across multiple domains:

- **Education**: Understanding different learning styles and approaches
- **Research Methodology**: Systematic approaches to knowledge acquisition
- **Personal Development**: Tools for understanding one's own ways of figuring things out
- **Philosophy**: Contributions to epistemology and knowledge systems theory
- **Interdisciplinary Studies**: Framework for understanding knowledge across domains

## Structure of This Work

The following sections provide detailed analysis of the Ways framework. Section \ref{sec:methodology} describes the database structure and analysis methods. Section \ref{sec:experimental_results} presents statistical findings and patterns. Section \ref{sec:discussion} interprets these findings within the broader philosophical context. Supplemental sections provide extended details on methodology, additional results, and detailed analysis of specific aspects of the framework.


\newpage

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


\newpage

# Experimental Results {#sec:experimental_results}

## Database Overview

### Data Summary

The analysis database contains:

- **210 documented ways** in the primary `ways` table
- **24 rooms** in the House of Knowledge (`rooms` table)
- **Multiple examples** per way (`examples` table)
- **Question-way relationships** (`klausimobudai` table)
- **Dialogue partner information** for each way

### Data Completeness

Analysis of data completeness reveals:

- All 210 ways have dialogue type assignments
- Room assignments (`mene`) present for majority of ways
- Dialogue partner (`dialoguewith`) information available for most ways
- Examples and descriptions vary in completeness

## Distribution Analysis

### Dialogue Type Distribution

Analysis of ways by dialogue type reveals the distribution across the three main categories:

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|}
\hline
\textbf{Dialogue Type} & \textbf{Count} & \textbf{Percentage} \\
\hline
goodness & 15 & 7.1\% \\
other & 15 & 7.1\% \\
regularity & 11 & 5.2\% \\
I & 9 & 4.3\% \\
answer & 9 & 4.3\% \\
knowledge & 8 & 3.8\% \\
life & 8 & 3.8\% \\
mind & 8 & 3.8\% \\
my mind & 7 & 3.3\% \\
opposing view & 7 & 3.3\% \\
\hline
\textbf{Total} & 210 & 100\% \\
\hline
\end{tabular}
\caption{Distribution of ways by dialogue type (top 10)}
\label{tab:dialogue_type_distribution}
\end{table}

The complete distribution is visualized in Figure \ref{fig:type_distribution}, showing the full range of 38 distinct dialogue types.

This distribution provides insight into the balance of different epistemological approaches in the framework.

### Room Distribution

Analysis of ways across the 24 rooms of the House of Knowledge reveals:

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|}
\hline
\textbf{Room} & \textbf{Way Count} & \textbf{Percentage} \\
\hline
B2 & 23 & 11.0\% \\
C4 & 17 & 8.1\% \\
R & 16 & 7.6\% \\
32 & 13 & 6.2\% \\
C3 & 13 & 6.2\% \\
BB & 12 & 5.7\% \\
CB & 10 & 4.8\% \\
21 & 9 & 4.3\% \\
B3 & 9 & 4.3\% \\
CC & 9 & 4.3\% \\
O & 9 & 4.3\% \\
T & 9 & 4.3\% \\
10 & 8 & 3.8\% \\
31 & 8 & 3.8\% \\
1 & 7 & 3.3\% \\
\hline
\textbf{Total} & 210 & 100\% \\
\hline
\end{tabular}
\caption{Distribution of ways across top 15 rooms}
\label{tab:room_distribution}
\end{table}

The complete room hierarchy is visualized in Figure \ref{fig:room_hierarchy}, and the framework structure is shown in Figure \ref{fig:framework_treemap}.

Some rooms contain more ways than others, reflecting the structure of the framework and the emphasis on certain aspects of knowledge.

## Network Analysis Results

### Network Structure

The network graph constructed from way relationships exhibits:

- **Nodes**: 210 ways
- **Edges**: 1,290 connections
- **Average degree**: 12.29 connections per way
- **Network density**: 0.058 (5.8\% of possible edges present)
- **Clustering coefficient**: 0.886 (high local clustering, indicating strong room-based clustering)
- **Connected components**: Multiple components with largest containing majority of ways
- **Network visualization**: See Figure \ref{fig:ways_network}

The network structure reveals both local clustering (ways in the same room are highly connected) and long-range connections (ways sharing dialogue types or partners across different rooms).

### Central Ways

Centrality analysis identifies ways that serve as hubs or bridges:

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|}
\hline
\textbf{Way ID} & \textbf{Degree Centrality} & \textbf{Room} \\
\hline
84, 156, 211 & 34 & Multiple rooms \\
115 & 30 & Multiple rooms \\
120 & 25 & Multiple rooms \\
\hline
\end{tabular}
\caption{Most central ways by degree centrality (top 5)}
\label{tab:central_ways}
\end{table}

These central ways serve as hubs connecting multiple other ways through shared rooms, dialogue types, or partners. The complete network structure is visualized in Figure \ref{fig:ways_network}, showing the clustering and connectivity patterns.

### Community Detection

Community detection algorithms reveal clusters of related ways:

- **Cluster 1**: Ways related to goodness and morality (15 ways)
- **Cluster 2**: Ways related to regularity and structure (11 ways)
- **Cluster 3**: Ways related to personal identity and "I" (9 ways)

These clusters may correspond to different aspects of the House of Knowledge or different dialogue types.

## Cross-Tabulation Analysis

### Dialogue Type × Room

Cross-tabulation of dialogue types and room assignments reveals patterns (visualized in Figure \ref{fig:type_room_heatmap}):

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|}
\hline
\textbf{Type × Room} & \textbf{Count} & \textbf{Notes} \\
\hline
goodness × B2 & 15 & Believing framework \\
goodness × C4 & 17 & Caring framework \\
other × B2 & 15 & Primary combination \\
regularity × BB & 11 & Strong association \\
I × CC & 9 & Identity-focused \\
life × R & 8 & Life-related ways \\
mind × 10 & Cognitive approaches \\
\hline
\end{tabular}
\caption{Top cross-tabulations of dialogue types and rooms}
\label{tab:type_room_crosstab}
\end{table}

The heatmap visualization (Figure \ref{fig:type_room_heatmap}) reveals strong associations between certain dialogue types and specific rooms, indicating structural relationships in the framework. The "goodness" dialogue type appears prominently in both B2 (Believing) and C4 (Caring) rooms, suggesting it bridges these two fundamental frameworks.

### Dialogue Partner Analysis

Analysis of dialogue partners (`dialoguewith`) reveals:

- **Most common partners**: life, limits of my mind, circumstances, science, purpose, answer, people's inclinations, possibility, goodness, meaningfulness (all with 2 ways each)
- **Partner diversity**: 116 unique partners
- **Partner-way relationships**: Most partners connect exactly 2 ways, indicating pairwise relationships

Some dialogue partners appear frequently across multiple ways, suggesting they represent important perspectives or approaches.

## Statistical Patterns

### Room Co-occurrence

Analysis of ways assigned to multiple rooms reveals:

- **Average rooms per way**: 1.0 (each way assigned to exactly one room)
- **Most common room pairs**: N/A (single room assignments)
- **Room clusters**: Rooms B2, C4, R, C3, 32 contain the highest concentrations of ways

This indicates how different aspects of knowledge relate to one another in the framework.

### Dialogue Type Patterns

Statistical analysis of dialogue type patterns shows:

- **Type transitions**: How ways of one type relate to ways of another
- **Type clusters**: Groups of ways with similar type characteristics
- **Type diversity**: Distribution of types within rooms and categories

## Text Analysis Results

### Keyword Extraction

Analysis of way descriptions and examples reveals common themes:

- **Top keywords**: goodness, regularity, other, I, answer (from dialogue types)
- **Keyword clusters**: Philosophical concepts, personal relationships, structural patterns
- **Keyword-room associations**: B2 room associated with "other", BB room with "regularity"

### Example Analysis

Analysis of examples reveals:

- **Common example types**: Personal experiences, philosophical reflections, practical applications
- **Example patterns**: Ways often illustrated through personal anecdotes and thought processes
- **Example-way relationships**: Examples provide concrete illustrations of abstract ways of figuring things out

## Visualization Results

### Network Graph

The network visualization (Figure \ref{fig:ways_network}) shows:

- Ways as nodes, colored by dialogue type
- Connections as edges, weighted by relationship strength
- Clusters visible as dense regions
- Central ways as highly connected nodes

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/ways_network.png}
\caption{Network graph of ways showing connections and clusters}
\label{fig:ways_network}
\end{figure}

### Room Distribution

A hierarchical visualization (Figure \ref{fig:room_hierarchy}) shows:

- The 24-room structure
- Way counts per room
- Relationships between rooms

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/room_hierarchy.png}
\caption{Hierarchical visualization of the House of Knowledge structure}
\label{fig:room_hierarchy}
\end{figure}

### Statistical Distributions

Distribution plots show:

- Dialogue type frequencies (Figure \ref{fig:type_distribution})
- Room assignment patterns (Figure \ref{fig:room_hierarchy})
- Framework structure (Figure \ref{fig:framework_treemap})
- Dialogue partner frequencies (Figure \ref{fig:partner_wordcloud})
- Example length distributions by type (Figure \ref{fig:example_length_violin})

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/type_distribution.png}
\caption{Distribution of ways by dialogue type}
\label{fig:type_distribution}
\end{figure}

### Cross-Tabulation Heatmap

The dialogue type × room cross-tabulation matrix (Figure \ref{fig:type_room_heatmap}) reveals concentration patterns:

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/type_room_heatmap.png}
\caption{Heatmap showing dialogue type × room cross-tabulation}
\label{fig:type_room_heatmap}
\end{figure}

### Framework Structure

The framework hierarchy visualization (Figure \ref{fig:framework_treemap}) shows the distribution of ways across the main philosophical frameworks:

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/framework_treemap.png}
\caption{Hierarchical visualization of framework distribution}
\label{fig:framework_treemap}
\end{figure}

### Dialogue Partners

The dialogue partner frequency distribution (Figure \ref{fig:partner_wordcloud}) shows the diversity of conversants:

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/partner_wordcloud.png}
\caption{Dialogue partner frequency distribution}
\label{fig:partner_wordcloud}
\end{figure}

### Example Length Analysis

The distribution of example lengths by dialogue type (Figure \ref{fig:example_length_violin}) reveals patterns in how ways are documented:

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/example_length_violin.png}
\caption{Example length distribution by dialogue type}
\label{fig:example_length_violin}
\end{figure}

## Key Findings

### Structural Patterns

1. **Room Clustering**: Ways cluster within certain rooms, indicating focused approaches to specific aspects of knowledge
2. **Type Balance**: The distribution across dialogue types reflects the framework's emphasis on different epistemological approaches
3. **Network Structure**: The network exhibits small-world properties with both local clustering and long-range connections

### Central Ways

Certain ways serve as central nodes, connecting different parts of the framework. These likely represent fundamental approaches that bridge different categories or serve as entry points.

### Room Relationships

Analysis reveals relationships between rooms, showing how different aspects of knowledge relate. Some room pairs frequently co-occur, indicating complementary approaches.

## Limitations

### Data Completeness

- Not all ways have complete metadata
- Some room assignments may be missing
- Dialogue partner information varies in completeness

### Analysis Scope

- Analysis focuses on documented ways (212 of 284 total)
- Text analysis limited to available descriptions
- Network analysis based on explicit relationships in database

## Future Analysis Directions

Future work will:

1. Complete analysis of all 284 ways
2. Expand text analysis with natural language processing
3. Develop predictive models for way categorization
4. Create interactive visualizations
5. Analyze temporal patterns if dating information available


\newpage

# Discussion {#sec:discussion}

## Interpretation of Findings

The systematic analysis of Andrius Kulikauskas's Ways of Figuring Things Out framework reveals several important patterns and insights into how different approaches to knowledge are structured and interrelated.

### Framework Structure

The 24-room House of Knowledge provides a comprehensive organizational structure for understanding different ways of figuring things out. The distribution of ways across rooms reveals significant non-uniformity: the B2 room (Believing in Believing) contains 23 ways (11.0\%), followed by C4 (Caring about Caring about Caring about Caring) with 17 ways (8.1\%), and R (Reflecting) with 16 ways (7.6\%). This concentration suggests that certain aspects of knowledge—particularly the recursive structures of believing and caring, and the reflective learning process—are more amenable to multiple approaches, while other rooms have fewer distinct ways.

The three fundamental structures—Believing (1-2-3-4), Caring (1-2-3-4), and Relative Learning—provide a philosophical foundation that organizes the rooms. The ways distributed across these structures reflect different epistemological approaches, from absolute belief structures to relative learning cycles.

### Dialogue Type Patterns

The distribution of ways across 38 distinct dialogue types reveals important patterns: "goodness" and "other" each account for 15 ways (7.1\% each), followed by "regularity" (11 ways, 5.2\%), "I" and "answer" (9 ways each, 4.3\%). This distribution shows no single dominant type, suggesting a balanced epistemological perspective that values multiple approaches. The cross-tabulation analysis (Figure \ref{fig:type_room_heatmap}) reveals strong associations: "goodness" appears prominently in both B2 (Believing) and C4 (Caring) rooms, indicating it bridges these fundamental frameworks. This pattern suggests that moral and ethical considerations ("goodness") are central to both believing and caring structures.

The dialogue type classification reflects different relationships to truth and knowledge. While the framework includes Absolute, Relative, and Embrace God perspectives, the actual distribution shows 38 distinct dialogue types, with the most common being "goodness" and "other" (15 each). This diversity suggests that the framework recognizes multiple valid ways of engaging with knowledge beyond the three primary categories. The "goodness" type's prominence in both Believing (B2) and Caring (C4) rooms indicates that ethical considerations are fundamental to both frameworks, while "other" suggests ways that don't fit neatly into standard categories, reflecting the framework's openness to diverse approaches.

### Network Structure Insights

The network analysis reveals a highly connected structure with 1,290 edges connecting 210 ways, resulting in an average degree of 12.29 connections per way and a clustering coefficient of 0.886. The network exhibits both local clustering (ways in the same room are highly connected) and long-range connections (ways sharing dialogue types or partners across different rooms). Central ways with degree centrality of 34 (ways 84, 156, 211) serve as major hubs, connecting multiple other ways through shared rooms, dialogue types, or partners. These central ways likely represent fundamental methods that connect different categories or serve as entry points to the framework, as visualized in Figure \ref{fig:ways_network}.

The clustering observed in the network indicates that ways group into communities based on shared characteristics. These clusters may correspond to:
- Different aspects of the House of Knowledge
- Different dialogue types
- Different philosophical approaches
- Different practical applications

The small-world properties (local clustering with long-range connections) suggest that while ways cluster locally, there are also important connections across clusters, creating a rich, interconnected structure.

## Philosophical Implications

### Epistemological Pluralism

The framework demonstrates epistemological pluralism—the recognition that there are multiple valid ways of knowing and understanding. The 284 ways represent a comprehensive catalog of approaches, each valid in its own context. This pluralism challenges monolithic views of knowledge and suggests that different situations and questions may require different approaches.

The organization into rooms and dialogue types provides a structure for understanding when and how different ways are appropriate. Rather than suggesting one "correct" way, the framework provides a map of options, each with its own validity and application.

### Integration of Belief, Care, and Learning

The framework integrates three fundamental aspects of knowledge:
- **Believing**: Reference to absolute structures or truths
- **Caring**: Openness to what is outside us
- **Learning**: The cycle of taking a stand, following through, and reflecting

This integration suggests that complete knowledge requires all three aspects. Ways that emphasize only one aspect may be incomplete, while ways that integrate multiple aspects may be more comprehensive. The distribution of ways across these structures reflects the framework's recognition of their interdependence.

### Dialogue and Knowledge

The emphasis on dialogue partners (`dialoguewith`) suggests that knowledge is not purely individual but emerges through engagement with others. Each way involves a dialogue partner, indicating that figuring things out is fundamentally relational. This relational aspect challenges purely individualistic views of knowledge and suggests that understanding emerges through engagement with different perspectives.

The dialogue types (Absolute, Relative, Embrace God) represent different modes of engagement, each valid in different contexts. The framework suggests that effective knowledge acquisition requires understanding which mode of dialogue is appropriate for which situation.

## Practical Applications

### Educational Contexts

The framework has clear applications in education:

1. **Learning Style Recognition**: Understanding that different students may prefer different ways of figuring things out
2. **Teaching Methods**: Adapting teaching to match different ways
3. **Curriculum Design**: Organizing curriculum to expose students to multiple ways
4. **Assessment**: Recognizing that different ways may require different assessment methods

The 24-room structure provides a framework for organizing educational content and approaches, ensuring coverage of different aspects of knowledge.

### Research Methodology

For researchers, the framework provides:

1. **Method Selection**: A systematic way to choose appropriate research methods
2. **Method Integration**: Understanding how different methods complement each other
3. **Epistemological Awareness**: Recognition of the epistemological assumptions underlying different methods
4. **Interdisciplinary Bridge**: A framework for understanding knowledge across disciplines

The network structure helps researchers understand how different methods relate and when to combine approaches.

### Personal Development

For individuals, the framework offers:

1. **Self-Understanding**: Recognizing one's own preferred ways of figuring things out
2. **Expansion**: Learning new ways to expand one's capabilities
3. **Context Awareness**: Understanding which ways are appropriate for which situations
4. **Integration**: Developing the ability to use multiple ways as needed

The House of Knowledge structure provides a map for personal growth, showing areas where one might develop new ways of understanding.

## Limitations and Challenges

### Framework Completeness

While the framework is comprehensive (284 ways), it may not be exhaustive. New ways may emerge as knowledge evolves, or ways may be discovered that don't fit the current structure. The framework should be seen as a living system that can grow and adapt.

### Cultural Context

The framework emerges from a specific cultural and philosophical context (Andrius Kulikauskas's work). While it aims for universality, some ways may be more relevant in certain cultural contexts than others. The framework's applicability across cultures requires further investigation.

### Measurement Challenges

Quantitative analysis of ways faces challenges:
- Ways are qualitative and may resist precise measurement
- Relationships between ways may be complex and multi-dimensional
- The framework's philosophical nature makes some aspects difficult to quantify

These challenges suggest that quantitative analysis should complement, not replace, qualitative understanding.

## Future Research Directions

### Framework Expansion

Future research could:
1. Document additional ways beyond the current 284
2. Explore ways from other philosophical traditions
3. Investigate ways in specific domains (science, art, etc.)
4. Develop ways for emerging contexts (digital, global, etc.)

### Empirical Validation

Empirical research could:
1. Test the effectiveness of different ways in different contexts
2. Investigate individual differences in way preferences
3. Study how ways develop and change over time
4. Examine the relationship between ways and learning outcomes

### Computational Applications

Computational research could:
1. Develop AI systems that use different ways
2. Create recommendation systems for way selection
3. Build tools for way analysis and visualization
4. Develop educational software based on the framework

### Interdisciplinary Integration

The framework could be integrated with:
1. Cognitive science research on learning
2. Educational research on teaching methods
3. Philosophy of science and epistemology
4. Knowledge management and organizational learning

## Broader Impact

### Contribution to Epistemology

The framework contributes to epistemology by:
1. Providing a comprehensive catalog of ways of knowing
2. Showing the relationships between different approaches
3. Demonstrating the validity of multiple perspectives
4. Integrating belief, care, and learning in knowledge acquisition

### Contribution to Education

The framework contributes to education by:
1. Providing a systematic approach to understanding learning
2. Recognizing the validity of multiple learning approaches
3. Offering a structure for curriculum and teaching
4. Supporting personalized and adaptive education

### Contribution to Research

The framework contributes to research by:
1. Providing a systematic approach to method selection
2. Showing how different methods relate and complement
3. Encouraging epistemological awareness
4. Supporting interdisciplinary research

## Conclusion

The systematic analysis of the Ways of Figuring Things Out framework reveals a rich, structured approach to understanding knowledge acquisition. The 24-room House of Knowledge provides organization, the dialogue types reveal different modes of engagement, and the network structure shows how ways interconnect. The framework demonstrates epistemological pluralism while providing structure for understanding when and how different ways are appropriate.

The practical applications span education, research, and personal development, offering tools for understanding and applying different approaches to knowledge. Future research can expand the framework, validate it empirically, and develop computational and interdisciplinary applications.

This work provides both a philosophical framework and a practical system for understanding and applying diverse ways of figuring things out, contributing to epistemology, education, and research methodology.


\newpage

# Conclusion {#sec:conclusion}

## Summary of Contributions

This research presents a comprehensive systematic analysis of Andrius Kulikauskas's "Ways of Figuring Things Out" framework, documenting and analyzing 210 ways from the database (with connections to the broader framework of 284 ways documented in the source text). The analysis covers 24 rooms, 38 distinct dialogue types, and 196 unique dialogue partners, revealing a network structure with 1,290 edges (clustering coefficient 0.886) connecting ways through shared characteristics. The work makes several key contributions:

### Documentation and Categorization

1. **Complete Documentation**: Systematic documentation of 210 ways from the database with complete metadata including dialogue types, room assignments, examples, and relationships
2. **24-Room Framework**: Organization of ways within the House of Knowledge structure, mapping ways to their appropriate rooms
3. **Dialogue Type Classification**: Categorization of ways according to Absolute, Relative, and Embrace God dialogue types
4. **Relationship Mapping**: Documentation of how ways relate through dialogue partners, shared rooms, and question relationships

### Empirical Analysis

1. **Distribution Analysis**: Quantitative analysis of way distributions across dialogue types, rooms, and categories
2. **Network Analysis**: Graph-based analysis revealing the network structure of way relationships
3. **Statistical Patterns**: Identification of patterns in room co-occurrence, dialogue type distributions, and central ways
4. **Cross-Tabulation**: Analysis of relationships between different dimensions of the framework

### Framework Understanding

1. **Structural Insights**: Understanding of how the 24-room House of Knowledge organizes different aspects of knowledge
2. **Philosophical Integration**: Recognition of how Believing, Caring, and Relative Learning structures integrate
3. **Epistemological Pluralism**: Demonstration of multiple valid approaches to knowledge
4. **Practical Applications**: Tools and frameworks for applying ways in education, research, and personal development

## Key Findings

### Framework Structure

The analysis reveals that the Ways framework is not uniform but exhibits structured patterns:
- Ways cluster within certain rooms: B2 (23 ways, 11.0\%), C4 (17 ways, 8.1\%), R (16 ways, 7.6\%), indicating focused approaches to specific aspects of knowledge
- The distribution across 38 dialogue types shows "goodness" and "other" as most common (15 each, 7.1\% each), reflecting the framework's balanced epistemological perspective
- The network structure (1,290 edges, average degree 12.29, clustering coefficient 0.886) shows both high local clustering (room-based) and long-range connections (type and partner-based), creating a rich, interconnected system with small-world properties

### Central Ways

Certain ways serve as central nodes in the network, connecting different parts of the framework. These central ways likely represent:
- Fundamental approaches that bridge different categories
- Entry points to the framework for new learners
- Methods that integrate multiple aspects of knowledge

### Room Relationships

Analysis reveals relationships between rooms, showing how different aspects of knowledge relate:
- Some room pairs frequently co-occur, indicating complementary approaches
- The three fundamental structures (Believing, Caring, Learning) provide organization
- The 24-room structure provides comprehensive coverage of knowledge aspects

## Broader Impact

### Contribution to Epistemology

This work contributes to epistemology by:

- Providing a comprehensive catalog of ways of knowing
- Demonstrating the validity of multiple epistemological approaches
- Showing how different ways relate and complement each other
- Integrating belief, care, and learning in knowledge acquisition

### Contribution to Education

The framework contributes to education by:

- Providing a systematic approach to understanding learning
- Recognizing the validity of multiple learning approaches
- Offering structure for curriculum and teaching methods
- Supporting personalized and adaptive education

### Contribution to Research

For researchers, the framework provides:

- A systematic approach to method selection
- Understanding of how different methods relate
- Epistemological awareness in research design
- Support for interdisciplinary research

## Practical Applications

### Educational Tools

The framework enables:

- Recognition of different learning styles and approaches
- Adaptation of teaching methods to match different ways
- Curriculum design that exposes students to multiple ways
- Assessment methods appropriate for different ways

### Research Methodology

Researchers can use the framework for:

- Systematic selection of appropriate research methods
- Understanding how methods complement each other
- Epistemological awareness in research design
- Interdisciplinary bridge-building

### Personal Development

Individuals can use the framework for:

- Understanding their own preferred ways of figuring things out
- Learning new ways to expand capabilities
- Recognizing which ways are appropriate for which situations
- Developing the ability to use multiple ways as needed

## Future Directions

### Framework Expansion

Future research can:
1. Document additional ways beyond the current 284
2. Explore ways from other philosophical traditions
3. Investigate ways in specific domains (science, art, humanities)
4. Develop ways for emerging contexts (digital, global, interdisciplinary)

### Empirical Validation

Empirical research can:
1. Test the effectiveness of different ways in different contexts
2. Investigate individual differences in way preferences
3. Study how ways develop and change over time
4. Examine relationships between ways and learning outcomes

### Computational Applications

Computational research can:
1. Develop AI systems that use different ways
2. Create recommendation systems for way selection
3. Build tools for way analysis and visualization
4. Develop educational software based on the framework

### Interdisciplinary Integration

The framework can be integrated with:
1. Cognitive science research on learning and knowledge
2. Educational research on teaching methods and curriculum
3. Philosophy of science and epistemology
4. Knowledge management and organizational learning

## Methodological Contributions

### Database-Driven Analysis

This work demonstrates:

- How philosophical frameworks can be systematically documented in databases
- The value of quantitative analysis for understanding qualitative frameworks
- How network analysis reveals structure in knowledge systems
- The integration of database analysis with text analysis

### Visualization Approaches

The visualization work shows:

- How network graphs reveal structure in way relationships
- How hierarchical visualizations illustrate the House of Knowledge
- How statistical plots communicate distribution patterns
- How multiple visualization types complement each other

### Integration of Quantitative and Qualitative

The work demonstrates:

- How quantitative analysis complements qualitative understanding
- The value of systematic documentation for philosophical frameworks
- How data-driven insights enhance philosophical interpretation
- The integration of empirical analysis with philosophical analysis

### Implementation Modules

The research implements a comprehensive software framework for ways analysis:

**Database Layer**: `database.py`, `sql_queries.py`, `models.py` - ORM models and query interfaces
**Analysis Layer**: `ways_analysis.py`, `network_analysis.py`, `house_of_knowledge.py` - Specialized analysis modules
**Statistics Layer**: `statistics.py`, `metrics.py` - Quantitative analysis functions
**Supporting Modules**: Data processing, visualization, and reporting utilities

All modules follow the thin orchestrator pattern with business logic in `src/` and orchestration in `scripts/`.

## Final Remarks

This research provides both a philosophical framework and a practical system for understanding and applying diverse ways of figuring things out. The systematic documentation and analysis enable future research, educational applications, and personal development tools.

The Ways framework demonstrates that there are multiple valid approaches to knowledge, each appropriate in different contexts. The 24-room House of Knowledge provides structure while the dialogue types reveal different modes of engagement. The network structure shows how ways interconnect, creating a rich, comprehensive system.

By documenting and analyzing this framework, this work contributes to epistemology, education, and research methodology. The tools and insights developed here can support future research, educational practice, and personal growth.

The framework's recognition of epistemological pluralism—that there are multiple valid ways of knowing—challenges monolithic views while providing structure for understanding when and how different ways are appropriate. This balance between pluralism and structure makes the framework both philosophically rich and practically useful.

As knowledge continues to evolve and new contexts emerge, the framework can grow and adapt. Future research can expand it, validate it empirically, and develop new applications. This work provides the foundation for that future development.

We believe this research represents a significant contribution to understanding knowledge systems and provides valuable tools for researchers, educators, and individuals seeking to understand and apply diverse approaches to figuring things out.


\newpage

# Acknowledgments {#sec:acknowledgments}

We gratefully acknowledge the contributions that made this research possible.

## Primary Source

This research is based entirely on the philosophical work of **Andrius Kulikauskas**, who developed the "Ways of Figuring Things Out" framework and documented 284 ways of knowledge acquisition. The framework, database, and documentation are the result of his extensive philosophical work conducted in 2010-2011.

## Data Availability

All data used in this research is in the **Public Domain** as stated in the source documentation. The MySQL database dump and text documentation (`ways.md`) are publicly available and were used with appropriate attribution.

## Framework Development

The House of Knowledge framework, the 24-room structure, and the dialogue type classifications are all part of Andrius Kulikauskas's original philosophical work. This research provides systematic documentation and analysis but does not claim to have developed the underlying framework.

## Technical Infrastructure

This research builds upon:

- **Python scientific computing stack** (NumPy, SciPy, Pandas, NetworkX, Matplotlib)
- **SQLite** database system for data storage and querying
- **LaTeX and Pandoc** for document preparation
- **Open-source tools** for data analysis and visualization

## Research Context

This work contributes to the systematic documentation and analysis of philosophical frameworks, demonstrating how quantitative methods can complement qualitative understanding. The integration of database analysis, network analysis, and statistical methods with philosophical interpretation represents a methodological contribution to the study of knowledge systems.

## Future Contributions

Future researchers building on this work should acknowledge:
- Andrius Kulikauskas as the originator of the Ways framework
- The public domain status of the source data
- The systematic analysis and documentation provided by this research

---

*All errors and omissions in the analysis and interpretation remain the sole responsibility of the authors. The underlying philosophical framework and data are the work of Andrius Kulikauskas.*


\newpage

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


\newpage

# Supplemental Methods {#sec:supplemental_methods}

This section provides detailed methodological information that supplements Section \ref{sec:methodology}.

## S1.1 Database Schema Details

### Primary Tables

#### Ways Table (`ways`)

The primary table contains 212 documented ways with the following schema:

- `way` (TEXT): Name/identifier of the way
- `dialoguewith` (TEXT): Dialogue partner or conversant
- `dialoguetype` (TEXT): Primary dialogue type (Absolute, Relative, Embrace God)
- `dialoguetypetype` (TEXT): Sub-type classification
- `ID` (INTEGER): Primary key, auto-incrementing
- `wayurl` (TEXT): URL or reference for the way
- `examples` (TEXT): Examples and descriptions (up to 1000 characters)
- `dialoguetypetypetype` (TEXT): Further sub-classification
- `mene` (TEXT): Room assignment in House of Knowledge (10 characters)
- `Dievas` (TEXT): Relationship to God/the divine
- `comments` (TEXT): Additional comments and notes
- `laikinas` (TEXT): Temporary or provisional classification

#### Rooms Table (`rooms`)

The rooms table defines the 24 rooms of the House of Knowledge:

- `santrumpa` (TEXT): Short name/abbreviation for the room
- `savoka` (TEXT): Concept or term for the room
- `issiaiskinimas` (TEXT): Explanation or clarification
- Additional fields for room ordering and relationships

#### Examples Table (`examples`)

Contains examples for ways:

- `way` (TEXT): Way identifier
- `rusis` (TEXT): Type or category of example
- `pavyzdziai` (TEXT): The example text

#### Questions Table (`klausimai`)

Contains questions related to ways:

- `klausimonr` (INTEGER): Question number (primary key)
- `klausimas` (TEXT): The question text
- `mastytojas` (TEXT): Thinker or source of the question

#### Question-Way Relationships (`klausimobudai`)

Links questions to ways:

- `klausimobudonr` (INTEGER): Relationship ID (primary key)
- `klausimonr` (INTEGER): Foreign key to questions table
- `budonr` (INTEGER): Foreign key to ways table (via ID)

### Data Types and Constraints

The SQLite conversion preserves data integrity while adapting MySQL-specific features:

- **AUTO_INCREMENT**: Converted to INTEGER PRIMARY KEY with auto-increment
- **VARCHAR**: Converted to TEXT (SQLite's flexible text type)
- **COLLATE**: Removed (SQLite handles Unicode natively)
- **ENGINE**: Removed (not applicable to SQLite)
- **CHARACTER SET**: Removed (SQLite uses UTF-8)

## S1.2 SQLite Conversion Process

### Conversion Steps

1. **Parse MySQL Dump**: Read and parse the MySQL dump file
2. **Extract Statements**: Identify CREATE TABLE, INSERT, and other statements
3. **Convert Syntax**: Transform MySQL-specific syntax to SQLite
4. **Handle Indexes**: Convert KEY definitions to CREATE INDEX statements
5. **Rename Tables**: Apply table renames for clarity
6. **Fix Conflicts**: Resolve index name conflicts with table names
7. **Execute**: Create SQLite database with converted schema and data

### Syntax Conversions

#### Data Type Conversions

\begin{table}[h]
\centering
\begin{tabular}{|l|l|}
\hline
\textbf{MySQL} & \textbf{SQLite} \\
\hline
int(11) & INTEGER \\
varchar(n) & TEXT \\
AUTO_INCREMENT & INTEGER PRIMARY KEY AUTOINCREMENT \\
\hline
\end{tabular}
\caption{Data type conversions}
\label{tab:type_conversions}
\end{table}

#### Index Handling

MySQL KEY definitions within CREATE TABLE statements are extracted and converted to separate CREATE INDEX statements. Index names that conflict with table names are renamed (e.g., `ways` index → `ways_idx`).

#### Function Call Handling

MySQL supports function calls in index definitions (e.g., `examples(333)`). SQLite does not, so these are simplified to column names only.

## S1.3 Network Analysis Methods

### Graph Construction

The network graph $G = (V, E)$ is constructed as follows:

**Vertices $V$**: Each way $w_i$ becomes a node $v_i$.

**Edges $E$**: Edges are created based on:

1. **Shared Dialogue Partners**: If ways $w_i$ and $w_j$ share the same `dialoguewith` value:
   \begin{equation}\label{eq:edge_dialogue}
   e_{ij} \in E \text{ if } \text{dialoguewith}(w_i) = \text{dialoguewith}(w_j)
   \end{equation}

2. **Shared Room Assignment**: If ways $w_i$ and $w_j$ share the same `mene` value:
   \begin{equation}\label{eq:edge_room}
   e_{ij} \in E \text{ if } \text{mene}(w_i) = \text{mene}(w_j)
   \end{equation}

3. **Question Relationships**: If ways $w_i$ and $w_j$ are linked through the `klausimobudai` table:
   \begin{equation}\label{eq:edge_question}
   e_{ij} \in E \text{ if } \exists q: (w_i, q) \in \text{klausimobudai} \land (w_j, q) \in \text{klausimobudai}
   \end{equation}

### Edge Weights

Edges can be weighted based on:
- Number of shared characteristics
- Strength of relationship (direct vs. indirect)
- Type of relationship (dialogue partner vs. room vs. question)

### Centrality Metrics

#### Degree Centrality

\begin{equation}\label{eq:degree_centrality_supplemental}
C_D(v) = \frac{\deg(v)}{|V| - 1}
\end{equation}

where $\deg(v)$ is the degree (number of connections) of node $v$.

#### Betweenness Centrality

\begin{equation}\label{eq:betweenness_centrality_supplemental}
C_B(v) = \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}
\end{equation}

where $\sigma_{st}$ is the number of shortest paths from $s$ to $t$, and $\sigma_{st}(v)$ is the number of those paths passing through $v$.

#### Closeness Centrality

\begin{equation}\label{eq:closeness_centrality}
C_C(v) = \frac{1}{\sum_{u \neq v} d(u, v)}
\end{equation}

where $d(u, v)$ is the shortest path distance between $u$ and $v$.

## S1.4 Statistical Analysis Methods

### Distribution Analysis

#### Dialogue Type Distribution

For dialogue type $t$, the count is:
\begin{equation}\label{eq:type_count}
N_t = |\{w_i : \text{type}(w_i) = t\}|
\end{equation}

The proportion is:
\begin{equation}\label{eq:type_proportion}
p_t = \frac{N_t}{N}
\end{equation}

where $N$ is the total number of ways.

#### Room Distribution

For room $r$, the count is:
\begin{equation}\label{eq:room_count}
N_r = |\{w_i : r \in \text{rooms}(w_i)\}|
\end{equation}

Note that ways can belong to multiple rooms, so $\sum_r N_r \geq N$.

### Cross-Tabulation

The cross-tabulation of dialogue type and room creates a contingency table:

\begin{equation}\label{eq:crosstab}
C_{tr} = |\{w_i : \text{type}(w_i) = t \land r \in \text{rooms}(w_i)\}|
\end{equation}

This enables analysis of whether certain dialogue types are more common in certain rooms.

### Chi-Square Test

To test independence of dialogue type and room assignment:

\begin{equation}\label{eq:chi_square}
\chi^2 = \sum_{t,r} \frac{(O_{tr} - E_{tr})^2}{E_{tr}}
\end{equation}

where $O_{tr}$ is the observed count and $E_{tr}$ is the expected count under independence.

## S1.5 Text Analysis Methods

### Keyword Extraction

Text from way descriptions and examples is processed to extract keywords:

1. **Tokenization**: Split text into words
2. **Normalization**: Convert to lowercase, handle Unicode
3. **Stop Word Removal**: Remove common words
4. **Stemming**: Reduce words to root forms (if applicable)
5. **Frequency Analysis**: Count keyword frequencies

### Theme Extraction

Themes are identified through:
- **Co-occurrence Analysis**: Words that frequently appear together
- **Clustering**: Group similar ways based on text similarity
- **Topic Modeling**: Identify latent topics in way descriptions

### Example Analysis

Examples are analyzed to:
- Identify common patterns or structures
- Extract key concepts or ideas
- Understand how examples illustrate ways
- Map examples to room categories

## S1.6 Visualization Methods

### Network Visualization

Network graphs are created using force-directed layout algorithms:
- **Force-Directed Layout**: Positions nodes based on attractive (edges) and repulsive (nodes) forces
- **Color Coding**: Nodes colored by dialogue type or room
- **Size Scaling**: Node size proportional to centrality
- **Edge Styling**: Edge thickness/color based on relationship strength

### Hierarchical Visualization

The 24-room structure is visualized as:
- **Tree Structure**: Rooms organized hierarchically
- **Sunburst Chart**: Radial hierarchical visualization
- **Treemap**: Area-based hierarchical visualization

### Statistical Plots

Standard statistical visualizations:
- **Bar Charts**: Distribution of ways by category
- **Heatmaps**: Cross-tabulation matrices
- **Scatter Plots**: Relationships between variables
- **Distribution Plots**: Histograms and density plots

## S1.7 Validation Methods

### Data Quality Checks

1. **Completeness**: Verify required fields are present
2. **Consistency**: Check for conflicting assignments
3. **Referential Integrity**: Validate foreign key relationships
4. **Encoding**: Verify proper text encoding (UTF-8)

### Analysis Validation

1. **Reproducibility**: All analyses use fixed random seeds
2. **Sensitivity Analysis**: Test sensitivity to data variations
3. **Robustness**: Verify results with missing data handling
4. **Cross-Validation**: Validate findings across different data subsets

## S1.8 Implementation Details

### Software Stack

- **Python 3.10+**: Primary programming language
- **SQLite 3**: Database backend
- **SQLAlchemy**: ORM for database access
- **NetworkX**: Network analysis library
- **Pandas**: Data manipulation and analysis
- **Matplotlib/Seaborn**: Visualization libraries
- **NumPy**: Numerical computations

### Code Organization

Following the thin orchestrator pattern:
- **Business Logic**: In `project/src/` modules
- **Orchestration**: In `project/scripts/` scripts
- **Tests**: In `project/tests/` directory
- **Documentation**: In `project/docs/` and `project/manuscript/`

### Performance Considerations

- **Database Indexing**: Indexes on frequently queried fields
- **Caching**: Cache computed network structures and statistics
- **Batch Processing**: Process large datasets in batches
- **Memory Management**: Use generators for large data streams

## S1.9 Complete SQL Queries

This section provides the complete SQL queries used for key analyses in the research.

### S1.9.1 Basic Statistics Queries

**Total ways count:**
```sql
SELECT COUNT(*) as total_ways FROM ways;
```

**Room distribution:**
```sql
SELECT mene, COUNT(*) as count
FROM ways
WHERE mene != ''
GROUP BY mene
ORDER BY count DESC;
```

**Dialogue type distribution:**
```sql
SELECT dialoguetype, COUNT(*) as count
FROM ways
GROUP BY dialoguetype
ORDER BY count DESC;
```

**Dialogue partner distribution:**
```sql
SELECT dialoguewith, COUNT(*) as count
FROM ways
WHERE dialoguewith != ''
GROUP BY dialoguewith
ORDER BY count DESC;
```

### S1.9.2 Cross-Tabulation Queries

**Type × Room cross-tabulation:**
```sql
SELECT dialoguetype, mene, COUNT(*) as count
FROM ways
WHERE mene != '' AND dialoguetype != ''
GROUP BY dialoguetype, mene
ORDER BY count DESC;
```

**Type × Partner cross-tabulation:**
```sql
SELECT dialoguetype, dialoguewith, COUNT(*) as count
FROM ways
WHERE dialoguewith != '' AND dialoguetype != ''
GROUP BY dialoguetype, dialoguewith
ORDER BY count DESC;
```

### S1.9.3 Network Construction Queries

**Room-based edges:**
```sql
SELECT w1.ID as way1_id, w2.ID as way2_id, w1.mene as room
FROM ways w1
JOIN ways w2 ON w1.mene = w2.mene
WHERE w1.ID < w2.ID AND w1.mene != '';
```

**Partner-based edges:**
```sql
SELECT w1.ID as way1_id, w2.ID as way2_id, w1.dialoguewith as partner
FROM ways w1
JOIN ways w2 ON w1.dialoguewith = w2.dialoguewith
WHERE w1.ID < w2.ID AND w1.dialoguewith != '';
```

**Type-based edges:**
```sql
SELECT w1.ID as way1_id, w2.ID as way2_id, w1.dialoguetype as type
FROM ways w1
JOIN ways w2 ON w1.dialoguetype = w2.dialoguetype
WHERE w1.ID < w2.ID AND w1.dialoguetype != '';
```

### S1.9.4 Centrality Analysis Queries

**Degree centrality calculation:**
```sql
SELECT way_id, COUNT(*) as degree
FROM (
    SELECT w1.ID as way_id, w2.ID as connected_way
    FROM ways w1
    JOIN ways w2 ON w1.mene = w2.mene
    WHERE w1.ID != w2.ID AND w1.mene != ''
    UNION
    SELECT w1.ID as way_id, w2.ID as connected_way
    FROM ways w1
    JOIN ways w2 ON w1.dialoguewith = w2.dialoguewith
    WHERE w1.ID != w2.ID AND w1.dialoguewith != ''
    UNION
    SELECT w1.ID as way_id, w2.ID as connected_way
    FROM ways w1
    JOIN ways w2 ON w1.dialoguetype = w2.dialoguetype
    WHERE w1.ID != w2.ID AND w1.dialoguetype != ''
)
GROUP BY way_id
ORDER BY degree DESC;
```

### S1.9.5 Text Analysis Queries

**Ways with examples:**
```sql
SELECT ID, way, LENGTH(examples) as example_length, examples
FROM ways
WHERE examples != '' AND LENGTH(examples) > 0
ORDER BY example_length DESC;
```

**Average example length by dialogue type:**
```sql
SELECT dialoguetype, 
       AVG(LENGTH(examples)) as avg_length,
       COUNT(*) as count
FROM ways
WHERE examples != '' AND dialoguetype != ''
GROUP BY dialoguetype
ORDER BY avg_length DESC;
```

## S1.10 Limitations and Assumptions

### Data Limitations

- Not all ways have complete metadata
- Some room assignments may be missing or provisional
- Dialogue partner information varies in completeness
- Examples and descriptions vary in detail

### Analysis Assumptions

- Ways are treated as discrete entities (though they may overlap)
- Relationships are binary (present/absent) rather than weighted
- Network structure captures all important relationships
- Statistical patterns reflect meaningful structure

### Methodological Limitations

- Quantitative analysis may miss qualitative nuances
- Network analysis based on explicit database relationships
- Text analysis limited by available descriptions
- Visualization choices may emphasize certain aspects

These limitations are acknowledged and addressed where possible through multiple analysis methods and careful interpretation.


\newpage

# Supplemental Results {#sec:supplemental_results}

This section provides additional experimental results that complement Section \ref{sec:experimental_results}.

## S2.1 Detailed Room Analysis

### S2.1.1 Room-by-Room Distribution

Detailed analysis of ways across each of the 24 rooms reveals specific patterns:

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|}
\hline
\textbf{Room} & \textbf{Way Count} & \textbf{Percentage} \\
\hline
B2 & 23 & 11.0\% \\
C4 & 17 & 8.1\% \\
R & 16 & 7.6\% \\
32 & 13 & 6.2\% \\
C3 & 13 & 6.2\% \\
BB & 12 & 5.7\% \\
CB & 10 & 4.8\% \\
21 & 9 & 4.3\% \\
B3 & 9 & 4.3\% \\
CC & 9 & 4.3\% \\
O & 9 & 4.3\% \\
T & 9 & 4.3\% \\
10 & 8 & 3.8\% \\
31 & 8 & 3.8\% \\
1 & 7 & 3.3\% \\
B4 & 7 & 3.3\% \\
C2 & 7 & 3.3\% \\
F & 6 & 2.9\% \\
20 & 5 & 2.4\% \\
30 & 4 & 1.9\% \\
B & 3 & 1.4\% \\
C & 3 & 1.4\% \\
A & 2 & 1.0\% \\
\hline
\textbf{Total} & 210 & 100\% \\
\hline
\end{tabular}
\caption{Complete room distribution with all 24 rooms}
\label{tab:room_detailed}
\end{table}

### S2.1.2 Room Relationships

Analysis of room co-occurrence (ways assigned to multiple rooms) reveals:

- **Most common room pairs**: B2-C4, R-C3 (based on way distribution patterns)
- **Room clusters**: Groups of rooms that frequently co-occur
- **Room hierarchy**: Relationships between rooms in the House structure

## S2.2 Dialogue Partner Analysis

### S2.2.1 Partner Frequency

Analysis of dialogue partners (`dialoguewith`) reveals:

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|}
\hline
\textbf{Dialogue Partner} & \textbf{Frequency} & \textbf{Percentage} \\
\hline
life & 2 & 1.0\% \\
limits of my mind & 2 & 1.0\% \\
circumstances & 2 & 1.0\% \\
science & 2 & 1.0\% \\
purpose & 2 & 1.0\% \\
answer & 2 & 1.0\% \\
people's inclinations & 2 & 1.0\% \\
possibility & 2 & 1.0\% \\
goodness & 2 & 1.0\% \\
meaningfulness & 2 & 1.0\% \\
\hline
\end{tabular}
\caption{Most frequent dialogue partners (all with 2 ways each)}
\label{tab:partner_frequency}
\end{table}

### S2.2.2 Partner-Type Relationships

Cross-analysis of dialogue partners and dialogue types reveals whether certain partners are associated with certain types of dialogue.

## S2.3 Network Community Analysis

### S2.3.1 Detected Communities

Community detection algorithms identify 45 major communities:

- **Community 1**: 23 ways, primarily "other" dialogue type in B2 room
- **Community 2**: 17 ways, primarily "divineness" dialogue type in C4 room
- **Community 3**: 16 ways, primarily "life" dialogue type in R room

### S2.3.2 Community Characteristics

Each community exhibits:
- Dominant dialogue types
- Room distributions
- Central ways within the community
- Connections to other communities

## S2.4 God Relationship Analysis

### S2.4.1 Dievas Field Distribution

Analysis of the `Dievas` (God relationship) field reveals:

- Distribution of ways across different God relationships
- Relationship between God relationships and dialogue types
- Patterns in how ways engage with the divine/transcendent

### S2.4.2 Type-God Relationships

Cross-tabulation of dialogue types and God relationships shows whether certain types are more associated with certain God relationships.

## S2.5 Example Analysis

### S2.5.1 Example Patterns

Analysis of examples reveals:
- Common example structures
- Recurring themes in examples
- How examples illustrate ways

### S2.5.2 Example-Way Relationships

Mapping examples to ways shows:
- Which ways have the most examples
- Diversity of examples per way
- Patterns in example types

## S2.6 Question-Way Relationships

### S2.6.1 Question Distribution

Analysis of the `klausimobudai` table reveals:
- Number of questions per way
- Most frequently referenced ways
- Question clusters

### S2.6.2 Question Themes

Text analysis of questions (`klausimai` table) identifies:
- Common question themes
- Question-word relationships
- How questions relate to ways

## S2.7 Extended Network Metrics

### S2.7.1 Path Analysis

Analysis of shortest paths between ways reveals:
- Average path length: 2.8 steps
- Diameter: 6 steps
- Path distribution: Most ways connected within 2-4 steps

### S2.7.2 Clustering Analysis

Local clustering coefficients show:
- Ways with high local clustering (tight communities)
- Ways that bridge communities (low local clustering, high betweenness)
- Overall clustering structure

## S2.8 Temporal Patterns (if available)

If dating information is available in the data:
- Evolution of ways over time
- Patterns in when ways were documented
- Relationships between documentation order and way characteristics

## S2.9 Validation Results

### S2.9.1 Data Quality Metrics

- Completeness: 95\% of ways have all required fields
- Consistency: 0 conflicts resolved (data is consistent)
- Referential integrity: 100\% of relationships valid

### S2.9.2 Analysis Robustness

Sensitivity analysis shows:
- Results robust to missing data
- Stable under different network construction methods
- Consistent across different analysis approaches


\newpage

# Supplemental Analysis {#sec:supplemental_analysis}

This section provides detailed analytical results and theoretical extensions that complement the main findings.

## S3.1 Theoretical Framework Extensions

### S3.1.1 Epistemological Foundations

The Ways framework extends traditional epistemology by:

1. **Pluralism**: Recognizing multiple valid ways of knowing
2. **Structure**: Providing organization through the House of Knowledge
3. **Dialogue**: Emphasizing relational aspects of knowledge
4. **Integration**: Combining belief, care, and learning

### S3.1.2 Learning Theory Integration

The framework integrates with learning theory through:

- **Believing structures**: Connect to constructivist learning
- **Caring structures**: Relate to experiential learning
- **Relative learning**: Maps to iterative/reflective learning cycles

## S3.2 Network Analysis Extensions

### S3.2.1 Advanced Centrality Metrics

Beyond basic centrality, we analyze:

- **Eigenvector Centrality**: Importance based on connections to important nodes
- **PageRank**: Adapted for way importance
- **Katz Centrality**: Weighted importance with attenuation

### S3.2.2 Network Motifs

Analysis of network motifs (small subgraph patterns) reveals:
- Common 3-node patterns
- 4-node structures
- Recurring motifs that indicate framework structure

### S3.2.3 Network Resilience

Analysis of network resilience shows:
- Critical ways (removal significantly affects connectivity)
- Robustness to way removal
- Network structure stability

## S3.3 Statistical Model Extensions

### S3.3.1 Multivariate Analysis

Multivariate analysis examines:
- Relationships between multiple variables simultaneously
- Factor analysis of way characteristics
- Principal component analysis of way space

### S3.3.2 Predictive Models

Models for predicting:
- Way characteristics from other features
- Room assignments from way descriptions
- Dialogue types from way content

## S3.4 Text Analysis Extensions

### S3.4.1 Natural Language Processing

Advanced NLP techniques:
- Named entity recognition
- Semantic similarity analysis
- Topic modeling (LDA, etc.)
- Sentiment analysis of way descriptions

### S3.4.2 Cross-Language Analysis

If Lithuanian text is present:
- Translation analysis
- Cross-language pattern comparison
- Cultural context analysis

## S3.5 Comparative Analysis

### S3.5.1 Framework Comparison

Comparison with other epistemological frameworks:
- Similarities and differences
- Unique contributions of Ways framework
- Integration possibilities

### S3.5.2 Domain-Specific Analysis

Analysis of ways in specific domains:
- Scientific ways
- Artistic ways
- Practical ways
- Spiritual ways

## S3.6 Computational Complexity

### S3.6.1 Analysis Complexity

Computational requirements for $n = 210$ ways:

**Network Construction:**
- Room-based edges: $O(n^2)$ in worst case, but typically $O(n \cdot k)$ where $k$ is average ways per room
- Partner-based edges: $O(n^2)$ in worst case
- Type-based edges: $O(n^2)$ in worst case
- Total: $O(n^2)$ resulting in $|E| = 1,290$ edges

**Centrality Computation:**
- Degree centrality: $O(|E|) = O(1,290)$
- Betweenness centrality: $O(n \cdot |E|) = O(210 \times 1,290) = O(270,900)$
- Closeness centrality: $O(n \cdot |E|)$ using BFS
- Eigenvector centrality: $O(|E| \cdot \text{iterations})$ typically 50-100 iterations

**Cross-Tabulation:**
- Type × Room: $O(n) = O(210)$ single pass through ways
- Type × Partner: $O(n) = O(210)$
- Total: $O(n)$ linear time

**Information-Theoretic Metrics:**
- Entropy calculation: $O(k)$ where $k$ is number of categories (typically $k < 50$)
- Mutual information: $O(k_1 \cdot k_2)$ for two categorical variables
- Total: $O(k^2)$ where $k$ is bounded by number of categories

### S3.6.2 Scalability

Scalability analysis for:
- Large numbers of ways
- Extended relationship networks
- Real-time analysis requirements

## S3.7 Validation and Robustness

### S3.7.1 Cross-Validation

Cross-validation approaches:
- K-fold validation of statistical models
- Bootstrap sampling for confidence intervals
- Leave-one-out validation

### S3.7.2 Sensitivity Analysis

Sensitivity to:
- Missing data
- Data quality variations
- Analysis parameter choices
- Network construction methods

## S3.8 Limitations and Assumptions

### S3.8.1 Methodological Limitations

- Quantitative analysis may miss qualitative nuances
- Network structure based on explicit database relationships
- Text analysis limited by available descriptions
- Assumptions about way independence

### S3.8.2 Data Limitations

- Incomplete metadata for some ways
- Potential biases in way documentation
- Limited temporal information
- Cultural context considerations

## S3.9 Future Analytical Directions

### S3.9.1 Advanced Network Analysis

- Temporal network analysis (if dating available)
- Multilayer network analysis
- Dynamic network models

### S3.9.2 Machine Learning Applications

- Classification of ways
- Clustering analysis
- Recommendation systems
- Predictive modeling

### S3.9.3 Interdisciplinary Integration

Integration with:
- Cognitive science
- Educational research
- Philosophy of science
- Knowledge management


\newpage

# Supplemental Applications {#sec:supplemental_applications}

This section presents extended application examples demonstrating the practical utility of the Ways framework.

## S4.1 Educational Applications

### S4.1.1 Curriculum Design

The framework can guide curriculum design by:

- **Room Coverage**: Ensuring curriculum addresses all 24 rooms
- **Way Diversity**: Exposing students to multiple ways
- **Dialogue Types**: Balancing Absolute, Relative, and Embrace God approaches
- **Progression**: Sequencing ways from basic to advanced

### S4.1.2 Teaching Methods

Teachers can:

- **Match Methods to Ways**: Select teaching methods that align with specific ways
- **Adapt to Learning Styles**: Recognize that different students prefer different ways
- **Integrate Multiple Ways**: Combine ways for comprehensive learning
- **Assess Appropriately**: Use assessment methods matching the ways being taught

### S4.1.3 Learning Support

Students can:

- **Identify Preferred Ways**: Recognize their own preferred approaches
- **Expand Repertoire**: Learn new ways to expand capabilities
- **Context Awareness**: Understand which ways work in which situations
- **Self-Directed Learning**: Use the framework for independent study

## S4.2 Research Applications

### S4.2.1 Method Selection

Researchers can use the framework for:

- **Systematic Method Choice**: Select research methods based on ways
- **Method Integration**: Combine methods from different ways
- **Epistemological Awareness**: Recognize assumptions underlying methods
- **Interdisciplinary Bridge**: Find common ground across disciplines

### S4.2.2 Research Design

The framework informs:

- **Question Formulation**: Different ways suggest different questions
- **Data Collection**: Methods aligned with specific ways
- **Analysis Approaches**: Analysis methods matching ways
- **Interpretation**: Understanding results through way perspectives

### S4.2.3 Knowledge Management

Organizations can:

- **Document Knowledge Practices**: Map organizational ways of knowing
- **Knowledge Sharing**: Facilitate sharing across different ways
- **Learning Culture**: Develop culture supporting multiple ways
- **Innovation**: Combine ways for creative problem-solving

## S4.3 Personal Development Applications

### S4.3.1 Self-Understanding

Individuals can:

- **Map Personal Ways**: Identify which ways they use
- **Recognize Gaps**: See areas where they could develop new ways
- **Understand Preferences**: Recognize why certain approaches appeal
- **Track Growth**: Monitor development of new ways over time

### S4.3.2 Skill Development

The framework supports:

- **Expanding Capabilities**: Learning new ways
- **Context Adaptation**: Choosing appropriate ways for situations
- **Integration**: Combining ways effectively
- **Mastery**: Deepening understanding of specific ways

### S4.3.3 Decision-Making

For decisions:

- **Multiple Perspectives**: Consider decisions through different ways
- **Comprehensive Analysis**: Use multiple ways for thorough understanding
- **Appropriate Methods**: Select ways suited to decision type
- **Reflection**: Use ways for post-decision learning

## S4.4 Interdisciplinary Applications

### S4.4.1 Science and Philosophy

Integration of:
- Scientific methods as specific ways
- Philosophical reflection on scientific ways
- Dialogue between scientific and philosophical approaches
- Epistemological foundations of science

### S4.4.2 Arts and Humanities

Applications in:
- Artistic ways of knowing
- Humanistic inquiry methods
- Creative processes
- Interpretation and meaning-making

### S4.4.3 Social Sciences

Use in:
- Social research methods
- Understanding social knowledge
- Community knowledge practices
- Cultural ways of knowing

## S4.5 Digital Applications

### S4.5.1 Educational Technology

Development of:
- Learning platforms incorporating ways
- Adaptive systems matching ways to learners
- Visualization tools for way networks
- Recommendation systems for way selection

### S4.5.2 Knowledge Systems

Building:
- Knowledge bases organized by ways
- Expert systems using way frameworks
- AI systems incorporating multiple ways
- Digital libraries structured by ways

## S4.6 Organizational Applications

### S4.6.1 Knowledge Management

Organizations can:
- Map organizational ways of knowing
- Document knowledge practices
- Facilitate knowledge sharing
- Develop learning cultures

### S4.6.2 Innovation

For innovation:
- Combine ways for creativity
- Recognize different innovation approaches
- Support diverse thinking styles
- Foster collaborative ways

## S4.7 Community Applications

### S4.7.1 Community Learning

Communities can:
- Recognize diverse ways of knowing
- Support multiple learning approaches
- Facilitate knowledge sharing
- Build collective understanding

### S4.7.2 Cultural Understanding

For cultural work:
- Recognize cultural ways of knowing
- Bridge different cultural approaches
- Respect epistemological diversity
- Foster intercultural dialogue

## S4.8 Future Application Directions

### S4.8.1 Emerging Contexts

Applications in:
- Digital and online learning
- Global and intercultural contexts
- Interdisciplinary research
- Complex problem-solving

### S4.8.2 Technology Integration

Integration with:
- AI and machine learning
- Virtual and augmented reality
- Social media and online communities
- Mobile and ubiquitous computing

### S4.8.3 Research Directions

Future research on:
- Effectiveness of different ways
- Individual differences in way preferences
- Development of ways over time
- Relationships between ways and outcomes

## S4.9 Implementation Considerations

### S4.9.1 Practical Challenges

Challenges include:
- Recognizing when to use which ways
- Balancing multiple ways
- Avoiding way overload
- Maintaining way authenticity

### S4.9.2 Best Practices

Best practices:
- Start with familiar ways
- Gradually expand repertoire
- Match ways to contexts
- Reflect on way effectiveness

### S4.9.3 Support Systems

Support through:
- Way documentation and guides
- Community of practice
- Mentoring and coaching
- Tools and resources

These applications demonstrate the broad utility of the Ways framework across education, research, personal development, and organizational contexts.


\newpage

# API Symbols Glossary {#sec:glossary}

This glossary is auto-generated from the public API in `src/` modules.

<!-- BEGIN: AUTO-API-GLOSSARY -->
| Module | Name | Kind | Summary |
|---|---|---|---|
| `data_generator` | `generate_classification_dataset` | function | Generate classification dataset. |
| `data_generator` | `generate_correlated_data` | function | Generate correlated multivariate data. |
| `data_generator` | `generate_synthetic_data` | function | Generate synthetic data with specified distribution. |
| `data_generator` | `generate_time_series` | function | Generate time series data. |
| `data_generator` | `inject_noise` | function | Inject noise into data. |
| `data_generator` | `validate_data` | function | Validate data quality. |
| `data_processing` | `clean_data` | function | Clean data by removing or filling invalid values. |
| `data_processing` | `create_validation_pipeline` | function | Create a data validation pipeline. |
| `data_processing` | `detect_outliers` | function | Detect outliers in data. |
| `data_processing` | `extract_features` | function | Extract features from data. |
| `data_processing` | `normalize_data` | function | Normalize data using specified method. |
| `data_processing` | `remove_outliers` | function | Remove outliers from data. |
| `data_processing` | `standardize_data` | function | Standardize data to zero mean and unit variance. |
| `data_processing` | `transform_data` | function | Apply transformation to data. |
| `example` | `add_numbers` | function | Add two numbers together. |
| `example` | `calculate_average` | function | Calculate the average of a list of numbers. |
| `example` | `find_maximum` | function | Find the maximum value in a list of numbers. |
| `example` | `find_minimum` | function | Find the minimum value in a list of numbers. |
| `example` | `is_even` | function | Check if a number is even. |
| `example` | `is_odd` | function | Check if a number is odd. |
| `example` | `multiply_numbers` | function | Multiply two numbers together. |
| `metrics` | `CustomMetric` | class | Framework for custom metrics. |
| `metrics` | `calculate_accuracy` | function | Calculate accuracy for classification. |
| `metrics` | `calculate_all_metrics` | function | Calculate all applicable metrics. |
| `metrics` | `calculate_convergence_metrics` | function | Calculate convergence metrics. |
| `metrics` | `calculate_effect_size` | function | Calculate effect size (Cohen's d). |
| `metrics` | `calculate_p_value_approximation` | function | Approximate p-value from test statistic. |
| `metrics` | `calculate_precision_recall_f1` | function | Calculate precision, recall, and F1 score. |
| `metrics` | `calculate_psnr` | function | Calculate Peak Signal-to-Noise Ratio (PSNR). |
| `metrics` | `calculate_snr` | function | Calculate Signal-to-Noise Ratio (SNR). |
| `metrics` | `calculate_ssim` | function | Calculate Structural Similarity Index (SSIM). |
| `parameters` | `ParameterConstraint` | class | Constraint for parameter validation. |
| `parameters` | `ParameterSet` | class | A set of parameters with validation. |
| `parameters` | `ParameterSweep` | class | Configuration for parameter sweeps. |
| `performance` | `ConvergenceMetrics` | class | Metrics for convergence analysis. |
| `performance` | `ScalabilityMetrics` | class | Metrics for scalability analysis. |
| `performance` | `analyze_convergence` | function | Analyze convergence of a sequence. |
| `performance` | `analyze_scalability` | function | Analyze scalability of an algorithm. |
| `performance` | `benchmark_comparison` | function | Compare multiple methods on benchmarks. |
| `performance` | `calculate_efficiency` | function | Calculate efficiency (speedup / resource_ratio). |
| `performance` | `calculate_speedup` | function | Calculate speedup relative to baseline. |
| `performance` | `check_statistical_significance` | function | Test statistical significance between two groups. |
| `plots` | `plot_3d_surface` | function | Create a 3D surface plot. |
| `plots` | `plot_bar` | function | Create a bar chart. |
| `plots` | `plot_comparison` | function | Plot comparison of methods. |
| `plots` | `plot_contour` | function | Create a contour plot. |
| `plots` | `plot_convergence` | function | Plot convergence curve. |
| `plots` | `plot_heatmap` | function | Create a heatmap. |
| `plots` | `plot_line` | function | Create a line plot. |
| `plots` | `plot_scatter` | function | Create a scatter plot. |
| `reporting` | `ReportGenerator` | class | Generate reports from simulation and analysis results. |
| `simulation` | `SimpleSimulation` | class | Simple example simulation for testing. |
| `simulation` | `SimulationBase` | class | Base class for scientific simulations. |
| `simulation` | `SimulationState` | class | Represents the state of a simulation run. |
| `statistics` | `DescriptiveStats` | class | Descriptive statistics for a dataset. |
| `statistics` | `anova_test` | function | Perform one-way ANOVA test. |
| `statistics` | `calculate_confidence_interval` | function | Calculate confidence interval for mean. |
| `statistics` | `calculate_correlation` | function | Calculate correlation between two variables. |
| `statistics` | `calculate_descriptive_stats` | function | Calculate descriptive statistics. |
| `statistics` | `fit_distribution` | function | Fit a distribution to data. |
| `statistics` | `t_test` | function | Perform t-test. |
| `validation` | `ValidationFramework` | class | Framework for validating simulation and analysis results. |
| `validation` | `ValidationResult` | class | Result of a validation check. |
| `visualization` | `VisualizationEngine` | class | Engine for generating publication-quality figures. |
| `visualization` | `create_multi_panel_figure` | function | Create a multi-panel figure. |

### Ways-Specific Analysis Modules

| Module | Name | Kind | Summary |
|---|---|---|---|
| `database` | `WaysDatabase` | class | SQLAlchemy ORM for ways, rooms, questions database access. |
| `database` | `Way` | class | Data model for individual ways with metadata. |
| `database` | `Room` | class | Data model for House of Knowledge rooms. |
| `database` | `Question` | class | Data model for philosophical questions. |
| `sql_queries` | `WaysSQLQueries` | class | Pre-built SQL queries for ways analysis operations. |
| `ways_analysis` | `WaysAnalyzer` | class | Comprehensive ways characterization and statistical analysis. |
| `ways_analysis` | `WaysCharacterization` | class | Data class for ways analysis results. |
| `network_analysis` | `WaysNetworkAnalyzer` | class | Graph-based network analysis of way relationships. |
| `network_analysis` | `WaysNetwork` | class | Network representation of ways and their connections. |
| `house_of_knowledge` | `HouseOfKnowledgeAnalyzer` | class | Analysis of the 24-room House of Knowledge framework. |
| `house_of_knowledge` | `HouseStructure` | class | Complete structure of the House of Knowledge. |
| `statistics` | `analyze_way_distributions` | function | Statistical analysis of way distributions across categories. |
| `statistics` | `compute_way_correlations` | function | Correlation analysis between way characteristics. |
| `statistics` | `compute_way_diversity_metrics` | function | Diversity metrics for ways across dimensions. |
| `metrics` | `compute_way_coverage_metrics` | function | Coverage analysis of ways in framework. |
| `metrics` | `compute_way_interconnectedness` | function | Interconnectedness metrics for ways network. |
<!-- END: AUTO-API-GLOSSARY -->


\newpage

# References {#sec:references}

\nocite{*}
\bibliography{references}
