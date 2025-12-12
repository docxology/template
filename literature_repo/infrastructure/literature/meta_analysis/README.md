# Meta-Analysis Module

Comprehensive analysis and visualization tools for literature libraries.

## Quick Start

```python
from infrastructure.literature.meta_analysis import (
    DataAggregator,
    create_publication_timeline_plot,
    create_keyword_frequency_plot,
    create_pca_2d_plot,
)

# Create aggregator
aggregator = DataAggregator()

# Publication timeline
create_publication_timeline_plot()

# Keyword analysis
from infrastructure.literature.meta_analysis import extract_keywords_over_time
keyword_data = extract_keywords_over_time()
create_keyword_frequency_plot(keyword_data, top_n=20)

# PCA analysis
create_pca_2d_plot(n_clusters=5)
```

## Features

### Temporal Analysis
- Publication trends by year
- Publication rate analysis
- Year-based filtering

### Keyword Analysis
- Keyword frequency over time
- Emerging keyword detection
- Keyword evolution visualization

### Metadata Visualization
- Venue distribution
- Author contributions
- Citation distribution

### PCA Analysis
- Text feature extraction (TF-IDF)
- Principal component analysis
- Paper clustering
- 2D and 3D visualizations

## Dependencies

- `matplotlib` - Plotting
- `numpy` - Numerical operations
- `scikit-learn` - PCA and clustering (optional, for PCA features)

## See Also

- [`AGENTS.md`](AGENTS.md) - Complete documentation
- [`../AGENTS.md`](../AGENTS.md) - Literature module overview


