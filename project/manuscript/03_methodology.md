# Methodology {#sec:methodology}

## Database Structure and Conversion

### Source Data

The research draws on a MySQL database dump containing 11 tables documenting Andrius Kulikauskas's Ways of Figuring Things Out framework. The primary data table `20100422ways` contains 212 documented ways with the following key fields:

- `way`: The name/identifier of the way
- `dialoguewith`: The dialogue partner or conversant
- `dialoguetype`: The type of dialogue (Absolute, Relative, Embrace God)
- `dialoguetypetype`: Sub-type classification
- `mene`: Room assignment in the House of Knowledge (24 rooms)
- `Dievas`: Relationship to God/the divine
- `examples`: Examples and descriptions
- `comments`: Additional comments and notes

### SQLite Conversion

For analysis and portability, the MySQL dump was converted to SQLite format. The conversion process:

1. **Schema Conversion**: MySQL-specific syntax (AUTO_INCREMENT, ENGINE, COLLATE) converted to SQLite-compatible syntax
2. **Table Renaming**: Tables renamed for clarity (`20100422ways` → `ways`, `menes` → `rooms`, etc.)
3. **Index Handling**: Index names adjusted to avoid conflicts with table names (SQLite restriction)
4. **Data Preservation**: All data preserved during conversion with proper encoding handling

The resulting SQLite database (`db/ways.db`) provides a portable, queryable format for analysis.

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

We construct a network graph $G = (V, E)$ where:

- **Vertices $V$**: Each way is a node
- **Edges $E$**: Connections between ways based on:
  - Shared dialogue partners (`dialoguewith`)
  - Shared room assignments (`mene`)
  - Similar dialogue types
  - Question relationships (`klausimobudai` table)

### Centrality Metrics

We compute several centrality metrics to identify important ways:

\begin{equation}\label{eq:centrality}
C(v) = \frac{\text{Number of connections}}{\text{Total possible connections}}
\end{equation}

This identifies ways that serve as bridges or hubs in the network.

## Statistical Analysis Methods

### Distribution Analysis

We analyze the distribution of ways across:

1. **Dialogue Types**: Count and percentage by type
2. **Rooms**: Distribution across 24 rooms
3. **Dialogue Partners**: Frequency of conversants
4. **God Relationships**: Distribution of `Dievas` values

### Cross-Tabulation

Cross-tabulation analysis examines relationships between:

- Dialogue type × Room assignment
- Dialogue type × Dialogue partner
- Room × God relationship

This reveals patterns in how different dimensions of the framework relate.

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

## Implementation

The analysis is implemented using:

- **Python**: Primary analysis language
- **SQLite**: Database backend
- **NetworkX**: Network analysis library
- **Matplotlib/Seaborn**: Visualization libraries
- **Pandas**: Data manipulation and analysis

All code follows the thin orchestrator pattern, with business logic in `project/src/` modules and orchestration in `project/scripts/`.

## Ethical Considerations

This research documents and analyzes publicly available philosophical work by Andrius Kulikauskas. All data is in the public domain as stated in the source documentation. The analysis respects the original philosophical framework while providing systematic documentation and quantitative insights.
