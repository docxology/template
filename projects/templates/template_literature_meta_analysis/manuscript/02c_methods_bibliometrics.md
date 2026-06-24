# Bibliometric and Temporal Analysis

Descriptive statistics summarize the corpus along every available axis: counts by year,
venue, and author; citation-count distributions with a Gini coefficient of concentration;
and author productivity. Temporal analysis fits the publication time series, reporting a
compound annual growth rate of {{CAGR_PCT}}\% across {{YEAR_START}}--{{YEAR_END}} with a
peak in {{PEAK_YEAR}}.

Subfield classification assigns each record to one of {{N_SUBFIELDS}} configurable buckets
({{SUBFIELD_LIST}}) by priority-aware keyword matching; the taxonomy is defined entirely
in configuration. A TF-IDF term-weighting of titles and abstracts [@salton1988term]
feeds non-negative matrix factorization [@lee1999learning], implemented with scikit-learn
[@pedregosa2011scikit], which extracts {{NUM_TOPICS}} latent topics that cross-cut the
keyword taxonomy. The reporting follows established systematic-review practice
[@page2021prisma], with every figure and statistic traceable to a committed artifact.
