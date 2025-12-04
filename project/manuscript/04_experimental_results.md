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
