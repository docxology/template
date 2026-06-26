# Abstract

Manual synthesis cannot keep pace with a fast-growing research literature, and ad-hoc
reviews bind no evidence to a reproducible pipeline. We present a configurable,
reproducible meta-analysis framework that takes a single search term and produces a
complete quantitative portrait of its literature. For this instance the term is
**{{SEARCH_TERM_TITLE}}**. The pipeline dispatches across {{N_ENGINES}} literature
engines ({{ENGINE_LIST}}), each degrading gracefully to a skipped source when an API
key or the network is unavailable, then merges and de-duplicates records by a canonical
identifier hierarchy (DOI $>$ arXiv ID $>$ Semantic Scholar ID $>$ OpenAlex ID $>$ title
digest) into a corpus of $N = {{CORPUS_SIZE}}$ records spanning {{YEAR_START}}--{{YEAR_END}}
({{YEAR_SPAN}} years). Records are classified into a configurable {{N_SUBFIELDS}}-bucket
subfield taxonomy ({{SUBFIELD_LIST}}); the largest subfield is **{{TOP_SUBFIELD}}**
({{TOP_SUBFIELD_PCT}}\% of the classified corpus). The corpus grows at a compound annual
rate of {{CAGR_PCT}}\% (mean year-over-year growth {{MEAN_YOY_GROWTH_PCT}}\%, doubling time
{{DOUBLING_TIME}} years), peaking in {{PEAK_YEAR}} with {{PEAK_YEAR_PUBS}} records.

Non-negative matrix factorization extracts {{NUM_TOPICS}} latent topics over a
{{NUM_VOCAB_FEATURES}}-feature vocabulary, offline deterministic embeddings place every
title, abstract, and (when available) full text in a shared vector space, and
citation-network analysis exposes the corpus's internal structure ({{CITATION_EDGES}}
intra-corpus edges across {{CITATION_NODES}} nodes, {{CITATION_COMMUNITIES}} communities,
graph density {{CITATION_DENSITY_PCT}}\%). Of {{CITATION_TOTAL_REFS}} total outgoing
references, {{CITATION_RESOLUTION_PCT}}\% resolve to another record inside the corpus.
Abstract coverage stands at {{ABSTRACT_COVERAGE_PCT}}\%, open-access status is known for
{{OA_PCT}}\% of records, and {{PDF_AVAIL_PCT}}\% have a direct PDF link. An optional,
LLM-gated knowledge-graph stage scores the {{N_HYPOTHESES}} hypotheses explored against
the evidence. This run produced {{NUM_FIGURES}} publication-quality figures.

Every domain-specific value in this manuscript — the search term, keyword set, engine
roster, subfield taxonomy, and hypotheses — is injected from a single configuration file
and the pipeline's own outputs; re-targeting the configuration re-targets the entire
paper. The result is a reusable architecture for *living literature reviews*:
continuously re-runnable, evidence-bound syntheses for any topic.

**Keywords:** {{KEYWORDS_LIST}}
