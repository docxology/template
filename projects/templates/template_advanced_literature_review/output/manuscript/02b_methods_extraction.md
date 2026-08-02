# Full Text, Language, and Embeddings

Beyond bibliographic metadata, the pipeline mines the textual content of each record.
This stage bridges the gap between a bibliographic inventory and a semantic
understanding of the literature.

## Full-Text Availability

An open-access resolver maps each record to a downloadable PDF where one exists (a known
`pdf_url`, or an Unpaywall lookup by DOI), and an opt-in, network-gated downloader fetches
it to a deterministic path. Full-text availability is summarized without requiring any
download, so the offline default still reports coverage. For this run:

- **Abstract coverage**: 100.0\% of records (46 of
  46) carry an abstract; 0 records lack one.
- **Open-access status**: 43.5\% of records are open access (20 records);
  the remainder are closed or unknown.
- **PDF availability**: 43.5\% of records (20) have a direct
  PDF link; 20 have a publisher PDF, and 26 have
  no full-text source available.

The identifier coverage for this corpus is: 46 DOIs, 5
OpenAlex IDs, and 0 arXiv IDs. DOI coverage dominates and supports
cross-engine de-duplication.

## Language and Entity Extraction

Titles, abstracts, and (when present) full text are tokenized and reduced to keyphrases
and named entities by offline, dependency-light extractors — no mandatory LLM.
Term-frequency statistics drive a TF-IDF representation over a 137-feature
vocabulary. The most frequent terms in the corpus are: atmospheric, uncertainty, spectra, temperature, abundance, coverage, opacity, sources, analysis, assumptions, observed, retrievals, models, stellar, across, evaluated, retrieval, structure, composition, jwst. These terms
reflect the configured domain and the records retained by the retrieval and filtering
policy; fixture-derived terms are not evidence about the live field.

## Embeddings

Every title, abstract, and full text is embedded into a shared vector space by a
deterministic, offline method — TF-IDF followed by truncated SVD, i.e. latent semantic
analysis [@deerwester1990indexing]. The embedding dimensionality is 50 components (configurable
via `project_config.embeddings.n_components`), and the TF-IDF vocabulary is capped at
137 features (configurable via `project_config.embeddings.max_features`).
The embedding is byte-stable across runs: the same input text always yields identical
vectors, so the derived similarity matrix, nearest-neighbour lists, clusters, and
two-dimensional projection are all reproducible.

An optional transformer backend can be enabled by setting
`project_config.embeddings.method: transformer` (requires the `embeddings` extra), which
upgrades the embedding fidelity without changing the interface or downstream analysis.

The embeddings support semantic retrieval over the corpus and feed two visualizations:
a PCA two-dimensional projection ((Figure pca embeddings)) that maps the topical
geography of the literature, and a hierarchical clustering dendrogram
((Figure dendrogram)) that reveals the similarity structure of the document collection.
