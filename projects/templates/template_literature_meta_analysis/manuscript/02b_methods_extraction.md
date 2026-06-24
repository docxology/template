# Full Text, Language, and Embeddings

Beyond bibliographic metadata, the pipeline mines the textual content of each record.

**Full text.** An open-access resolver maps each record to a downloadable PDF where one
exists (a known `pdf_url`, or an Unpaywall lookup by DOI), and an opt-in, network-gated
downloader fetches it to a deterministic path. Full-text availability is summarized
without requiring any download, so the offline default still reports coverage.

**Language and entities.** Titles, abstracts, and (when present) full text are tokenized
and reduced to keyphrases and named entities by offline, dependency-light extractors —
no mandatory LLM. Term-frequency statistics drive a TF-IDF representation over a
{{NUM_VOCAB_FEATURES}}-feature vocabulary.

**Embeddings.** Every title, abstract, and full text is embedded into a shared vector
space by a deterministic, offline method (TF-IDF followed by truncated SVD, i.e. latent
semantic analysis [@deerwester1990indexing]). The embedding is byte-stable across runs, supporting reproducible
similarity search, nearest-neighbour retrieval, clustering, and two-dimensional
projection. An optional transformer backend can be enabled for higher-fidelity
embeddings without changing the interface.
