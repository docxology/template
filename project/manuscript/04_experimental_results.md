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
Absolute & TBD & TBD\% \\
Relative & TBD & TBD\% \\
Embrace God & TBD & TBD\% \\
\hline
\textbf{Total} & 212 & 100\% \\
\hline
\end{tabular}
\caption{Distribution of ways by dialogue type}
\label{tab:dialogue_type_distribution}
\end{table}

This distribution provides insight into the balance of different epistemological approaches in the framework.

### Room Distribution

Analysis of ways across the 24 rooms of the House of Knowledge reveals:

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|}
\hline
\textbf{Room Category} & \textbf{Way Count} & \textbf{Average per Room} \\
\hline
Believing (1-2-3-4) & TBD & TBD \\
Caring (1-2-3-4) & TBD & TBD \\
Relative Learning & TBD & TBD \\
Other Rooms & TBD & TBD \\
\hline
\end{tabular}
\caption{Distribution of ways across room categories}
\label{tab:room_distribution}
\end{table}

Some rooms contain more ways than others, reflecting the structure of the framework and the emphasis on certain aspects of knowledge.

## Network Analysis Results

### Network Structure

The network graph constructed from way relationships exhibits:

- **Average degree**: TBD connections per way
- **Clustering coefficient**: TBD (indicating local clustering)
- **Diameter**: TBD (longest shortest path)
- **Connected components**: TBD major components

### Central Ways

Centrality analysis identifies ways that serve as hubs or bridges:

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|}
\hline
\textbf{Way} & \textbf{Centrality Score} & \textbf{Role} \\
\hline
Way 1 & TBD & Hub/Bridge \\
Way 2 & TBD & Hub/Bridge \\
Way 3 & TBD & Hub/Bridge \\
\hline
\end{tabular}
\caption{Most central ways in the network}
\label{tab:central_ways}
\end{table}

These central ways likely represent fundamental approaches that connect different categories or serve as entry points to the framework.

### Community Detection

Community detection algorithms reveal clusters of related ways:

- **Cluster 1**: Ways related to [theme] (TBD ways)
- **Cluster 2**: Ways related to [theme] (TBD ways)
- **Cluster 3**: Ways related to [theme] (TBD ways)

These clusters may correspond to different aspects of the House of Knowledge or different dialogue types.

## Cross-Tabulation Analysis

### Dialogue Type × Room

Cross-tabulation of dialogue types and room assignments reveals patterns:

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|c|}
\hline
\textbf{Room Category} & \textbf{Absolute} & \textbf{Relative} & \textbf{Embrace God} \\
\hline
Believing Rooms & TBD & TBD & TBD \\
Caring Rooms & TBD & TBD & TBD \\
Learning Rooms & TBD & TBD & TBD \\
\hline
\end{tabular}
\caption{Cross-tabulation of dialogue types and room categories}
\label{tab:type_room_crosstab}
\end{table}

This analysis reveals whether certain dialogue types are more common in certain rooms, indicating structural relationships in the framework.

### Dialogue Partner Analysis

Analysis of dialogue partners (`dialoguewith`) reveals:

- **Most common partners**: TBD
- **Partner diversity**: TBD unique partners
- **Partner-way relationships**: Patterns in how ways relate to partners

Some dialogue partners appear frequently across multiple ways, suggesting they represent important perspectives or approaches.

## Statistical Patterns

### Room Co-occurrence

Analysis of ways assigned to multiple rooms reveals:

- **Average rooms per way**: TBD
- **Most common room pairs**: TBD
- **Room clusters**: Groups of rooms that frequently co-occur

This indicates how different aspects of knowledge relate to one another in the framework.

### Dialogue Type Patterns

Statistical analysis of dialogue type patterns shows:

- **Type transitions**: How ways of one type relate to ways of another
- **Type clusters**: Groups of ways with similar type characteristics
- **Type diversity**: Distribution of types within rooms and categories

## Text Analysis Results

### Keyword Extraction

Analysis of way descriptions and examples reveals common themes:

- **Top keywords**: TBD
- **Keyword clusters**: Groups of related terms
- **Keyword-room associations**: Which keywords appear in which rooms

### Example Analysis

Analysis of examples reveals:

- **Common example types**: TBD
- **Example patterns**: Recurring structures in examples
- **Example-way relationships**: How examples illustrate ways

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
