"""Meta-analysis and visualization module.

Provides tools for analyzing publication trends, keyword evolution,
metadata visualization, and PCA analysis of paper texts.
"""
from infrastructure.literature.meta_analysis.aggregator import (
    DataAggregator,
    TemporalData,
    KeywordData,
    MetadataData,
    TextCorpus,
)
from infrastructure.literature.meta_analysis.temporal import (
    get_publication_trends,
    filter_by_year_range,
    analyze_publication_rate,
    create_publication_timeline_plot,
)
from infrastructure.literature.meta_analysis.keywords import (
    extract_keywords_over_time,
    detect_emerging_keywords,
    create_keyword_frequency_plot,
    create_keyword_evolution_plot,
)
from infrastructure.literature.meta_analysis.metadata import (
    create_venue_distribution_plot,
    create_author_contributions_plot,
    create_citation_distribution_plot,
    create_metadata_completeness_plot,
    calculate_completeness_stats,
    get_metadata_summary,
)
from infrastructure.literature.meta_analysis.pca import (
    extract_text_features,
    compute_pca,
    cluster_papers,
    create_pca_2d_plot,
    create_pca_3d_plot,
    export_pca_loadings,
)
from infrastructure.literature.meta_analysis.pca_loadings import (
    extract_pca_loadings,
    get_top_words_per_component,
    export_loadings_csv,
    export_loadings_json,
    export_loadings_summary_markdown,
    export_word_importance_rankings,
    export_all_loadings,
    create_loadings_visualizations,
)
from infrastructure.literature.meta_analysis.summary import (
    generate_summary_data,
    generate_text_summary,
    export_summary_json,
    generate_all_summaries,
)
from infrastructure.literature.meta_analysis.graphical_abstract import (
    create_single_page_abstract,
    create_multi_page_abstract,
    create_comprehensive_abstract,
)
from infrastructure.literature.meta_analysis.visualizations import (
    plot_pca_loadings_heatmap,
    plot_pca_loadings_barplot,
    plot_pca_biplot,
    plot_pca_word_vectors,
    plot_metadata_completeness,
)

__all__ = [
    # Aggregator
    "DataAggregator",
    "TemporalData",
    "KeywordData",
    "MetadataData",
    "TextCorpus",
    # Temporal analysis
    "get_publication_trends",
    "filter_by_year_range",
    "analyze_publication_rate",
    "create_publication_timeline_plot",
    # Keyword analysis
    "extract_keywords_over_time",
    "detect_emerging_keywords",
    "create_keyword_frequency_plot",
    "create_keyword_evolution_plot",
    # Metadata analysis
    "create_venue_distribution_plot",
    "create_author_contributions_plot",
    "create_citation_distribution_plot",
    "create_metadata_completeness_plot",
    "calculate_completeness_stats",
    "get_metadata_summary",
    # PCA analysis
    "extract_text_features",
    "compute_pca",
    "cluster_papers",
    "create_pca_2d_plot",
    "create_pca_3d_plot",
    "export_pca_loadings",
    # PCA loadings
    "extract_pca_loadings",
    "get_top_words_per_component",
    "export_loadings_csv",
    "export_loadings_json",
    "export_loadings_summary_markdown",
    "export_word_importance_rankings",
    "export_all_loadings",
    "create_loadings_visualizations",
    # Summary reports
    "generate_summary_data",
    "generate_text_summary",
    "export_summary_json",
    "generate_all_summaries",
    # Graphical abstracts
    "create_single_page_abstract",
    "create_multi_page_abstract",
    "create_comprehensive_abstract",
    # Visualization functions
    "plot_pca_loadings_heatmap",
    "plot_pca_loadings_barplot",
    "plot_pca_biplot",
    "plot_pca_word_vectors",
    "plot_metadata_completeness",
]


