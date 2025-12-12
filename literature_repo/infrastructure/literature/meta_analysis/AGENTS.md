# Meta-Analysis Module - Complete Documentation

## Purpose

The meta-analysis module provides comprehensive analysis and visualization tools for literature libraries, including temporal trends, keyword evolution, metadata visualization, and PCA analysis.

## Components

### DataAggregator (aggregator.py)

Aggregates library data for analysis.

**Key Methods:**
- `aggregate_library_data()` - Collect all library entries
- `prepare_temporal_data()` - Year-based aggregation
- `prepare_keyword_data()` - Keyword extraction and aggregation
- `prepare_metadata_data()` - Metadata aggregation
- `prepare_text_corpus()` - Text corpus for PCA

### Temporal Analysis (temporal.py)

Publication year analysis and trends.

**Key Functions:**
- `get_publication_trends()` - Get publication trends
- `filter_by_year_range()` - Filter by year range
- `analyze_publication_rate()` - Analyze publication rate
- `create_publication_timeline_plot()` - Create timeline plot

### Keyword Analysis (keywords.py)

Keyword evolution and frequency analysis.

**Key Functions:**
- `extract_keywords_over_time()` - Extract keywords
- `detect_emerging_keywords()` - Detect trending keywords
- `create_keyword_frequency_plot()` - Frequency plot
- `create_keyword_evolution_plot()` - Evolution plot

### Metadata Visualization (metadata.py)

Metadata visualization and statistics.

**Key Functions:**
- `create_venue_distribution_plot()` - Venue distribution
- `create_author_contributions_plot()` - Author contributions
- `create_citation_distribution_plot()` - Citation distribution
- `get_metadata_summary()` - Summary statistics

### PCA Analysis (pca.py)

Principal component analysis of paper texts.

**Key Functions:**
- `extract_text_features()` - TF-IDF feature extraction
- `compute_pca()` - Principal component analysis
- `cluster_papers()` - K-means clustering
- `create_pca_2d_plot()` - 2D visualization
- `create_pca_3d_plot()` - 3D visualization

### Visualizations (visualizations.py)

Plotting utilities for all visualizations.

**Key Functions:**
- `plot_publications_by_year()` - Year-based plot
- `plot_keyword_frequency()` - Keyword frequency
- `plot_venue_distribution()` - Venue distribution
- `plot_pca_2d()` - 2D PCA plot
- `plot_pca_3d()` - 3D PCA plot
- `save_plot()` - Save plot to file

## Usage Examples

### Temporal Analysis

```python
from infrastructure.literature.meta_analysis import (
    DataAggregator,
    create_publication_timeline_plot
)

aggregator = DataAggregator()
create_publication_timeline_plot()
```

### Keyword Analysis

```python
from infrastructure.literature.meta_analysis import (
    extract_keywords_over_time,
    create_keyword_frequency_plot
)

keyword_data = extract_keywords_over_time(min_frequency=3)
create_keyword_frequency_plot(keyword_data, top_n=20)
```

### PCA Analysis

```python
from infrastructure.literature.meta_analysis import create_pca_2d_plot

create_pca_2d_plot(n_clusters=5)
```

## Dependencies

- `matplotlib` - Plotting
- `numpy` - Numerical operations
- `scikit-learn` - PCA and clustering (optional, for PCA features)

## See Also

- [`README.md`](README.md) - Quick reference
- [`../AGENTS.md`](../AGENTS.md) - Literature module overview


