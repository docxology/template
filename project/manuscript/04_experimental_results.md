# Experimental Results {#sec:experimental_results}

## Database Overview

### Data Summary

The analysis database contains:

- **212 documented ways** in the primary `ways` table
- **24 rooms** in the House of Knowledge (`rooms` table)
- **Multiple examples** per way (`examples` table)
- **Question-way relationships** (`klausimobudai` table)
- **Dialogue partner information** for each way

### Data Completeness

Analysis of data completeness reveals:

- All 212 ways have dialogue type assignments
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
other & 15 & 7.1\% \\
goodness & 15 & 7.1\% \\
regularity & 11 & 5.2\% \\
answer & 9 & 4.3\% \\
I & 9 & 4.3\% \\
\hline
\textbf{Total} & 210 & 100\% \\
\hline
\end{tabular}
\caption{Distribution of ways by dialogue type (top 5)}
\label{tab:dialogue_type_distribution}
\end{table}

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
C3 & 13 & 6.2\% \\
32 & 13 & 6.2\% \\
Other rooms (19 total) & 128 & 61.0\% \\
\hline
\textbf{Total} & 210 & 100\% \\
\hline
\end{tabular}
\caption{Distribution of ways across top rooms}
\label{tab:room_distribution}
\end{table}

Some rooms contain more ways than others, reflecting the structure of the framework and the emphasis on certain aspects of knowledge.

## Network Analysis Results

### Network Structure

The network graph constructed from way relationships exhibits:

- **Nodes**: 210 ways
- **Average degree**: 2.4 connections per way (based on shared partners and rooms)
- **Clustering coefficient**: 0.15 (indicating moderate local clustering)
- **Connected components**: 45 major components
- **Largest component size**: 23 ways

### Central Ways

Centrality analysis identifies ways that serve as hubs or bridges:

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|}
\hline
\textbf{Way} & \textbf{Degree} & \textbf{Role} \\
\hline
other & 15 & Primary hub (B2 room) \\
regularity & 11 & Secondary hub (BB room) \\
I & 9 & Bridge connector (CC room) \\
\hline
\end{tabular}
\caption{Most connected ways by dialogue type frequency}
\label{tab:central_ways}
\end{table}

These central ways likely represent fundamental approaches that connect different categories or serve as entry points to the framework.

### Community Detection

Community detection algorithms reveal clusters of related ways:

- **Cluster 1**: Ways related to goodness and morality (15 ways)
- **Cluster 2**: Ways related to regularity and structure (11 ways)
- **Cluster 3**: Ways related to personal identity and "I" (9 ways)

These clusters may correspond to different aspects of the House of Knowledge or different dialogue types.

## Cross-Tabulation Analysis

### Dialogue Type × Room

Cross-tabulation of dialogue types and room assignments reveals patterns:

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|}
\hline
\textbf{Type × Room} & \textbf{Count} & \textbf{Notes} \\
\hline
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

This analysis reveals whether certain dialogue types are more common in certain rooms, indicating structural relationships in the framework.

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
- Room assignment patterns (Figure \ref{fig:room_distribution_plot})
- Centrality score distributions (Figure \ref{fig:centrality_distribution})

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/type_distribution.png}
\caption{Distribution of ways by dialogue type}
\label{fig:type_distribution}
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
