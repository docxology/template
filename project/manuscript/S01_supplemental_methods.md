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

\begin{equation}\label{eq:degree_centrality}
C_D(v) = \frac{\deg(v)}{|V| - 1}
\end{equation}

where $\deg(v)$ is the degree (number of connections) of node $v$.

#### Betweenness Centrality

\begin{equation}\label{eq:betweenness_centrality}
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

## S1.9 Limitations and Assumptions

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
