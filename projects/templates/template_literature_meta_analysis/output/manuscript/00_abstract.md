# Abstract

Manual synthesis cannot keep pace with a fast-growing research literature, and ad-hoc
reviews bind no evidence to a reproducible pipeline. We present a configurable,
reproducible meta-analysis framework that takes a single search term and produces a
complete quantitative portrait of its literature. For this instance the term is
**Modafinil**. The pipeline dispatches across 7 literature
engines (arXiv, OpenAlex, Semantic Scholar, Crossref, PubMed, SovietRxiv, and ChinaRxiv), each degrading gracefully to a skipped source when an API
key or the network is unavailable, then merges and de-duplicates records by a canonical
identifier hierarchy (DOI $>$ arXiv ID $>$ Semantic Scholar ID $>$ OpenAlex ID $>$ title
digest) into a corpus of $N = 2302$ records spanning 2000--2026
(26 years). Records are classified into a configurable 6-bucket
subfield taxonomy (Clinical Sleep, Cognition, Pharmacology, Psychiatry, Safety, and Neuroscience); the largest subfield is **Clinical Sleep**
(64.3\% of the classified corpus). The corpus grows at a compound annual
rate of 3.45\% (mean year-over-year growth 6.3\%, doubling time
11.3 years), peaking in 2025 with 112 records.

Non-negative matrix factorization extracts 5 latent topics over a
500-feature vocabulary, offline deterministic embeddings place every
title, abstract, and (when available) full text in a shared vector space, and
citation-network analysis exposes the corpus's internal structure (8,772
intra-corpus edges across 2204 nodes, 1377 communities,
graph density 0.18\%). Of 38,802 total outgoing
references, 22.6\% resolve to another record inside the corpus.
Abstract coverage stands at 55.5\%, open-access status is known for
14.4\% of records, and 40.9\% have a direct PDF link. An optional,
LLM-gated knowledge-graph stage scores the 6 hypotheses explored against
the evidence. This run produced 18 publication-quality figures.

Every domain-specific value in this manuscript — the search term, keyword set, engine
roster, subfield taxonomy, and hypotheses — is injected from a single configuration file
and the pipeline's own outputs; re-targeting the configuration re-targets the entire
paper. The result is a reusable architecture for *living literature reviews*:
continuously re-runnable, evidence-bound syntheses for any topic.

**Keywords:** modafinil, meta-analysis, literature retrieval, bibliometrics, record de-duplication, full-text mining, document embeddings, citation network, topic modeling, entity extraction, wakefulness, cognitive enhancement, reproducible research
