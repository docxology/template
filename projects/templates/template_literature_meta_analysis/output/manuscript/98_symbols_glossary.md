# Glossary

| Term | Meaning |
| --- | --- |
| **Record / Paper** | A single bibliographic entry with metadata and identifiers. |
| **Canonical identifier** | The highest-priority available ID (DOI $>$ arXiv $>$ Semantic Scholar $>$ OpenAlex $>$ title digest) used for de-duplication and citation resolution. |
| **Engine** | An independent literature source adapter (arXiv, OpenAlex, Semantic Scholar, Crossref, PubMed, SovietRxiv, ChinaRxiv, Europe PMC, and bioRxiv/medRxiv) with a uniform search interface and graceful skip-on-failure. |
| **Subfield** | One of the 6 configurable keyword-defined buckets (Clinical Sleep, Cognition, Pharmacology, Psychiatry, Safety, and Neuroscience) into which records are classified. |
| **Topic** | A latent theme from non-negative matrix factorization over the TF-IDF representation. |
| **Embedding** | A deterministic offline vector (TF-IDF $\rightarrow$ truncated SVD) for a title, abstract, or full text. |
| **Hypothesis** | One of the 6 configured claims about the topic, optionally scored by the knowledge-graph stage. |
| **Assertion** | A directional (supports / contradicts / neutral) statement extracted from a record against a hypothesis, with a confidence score. |
| **Nanopublication** | An RDF-serialized assertion plus its provenance. |
| **CAGR** | Compound annual growth rate of publication volume (5.48\% for this corpus). |
| **Living literature review** | A synthesis that can be re-executed as the field evolves, with every number regenerable. |
