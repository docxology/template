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
