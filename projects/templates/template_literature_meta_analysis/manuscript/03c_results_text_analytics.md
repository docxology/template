# Results: Language, Topics, and Embeddings

Text analysis operates over titles, abstracts, and (when available) full text. A TF-IDF
representation over a {{NUM_VOCAB_FEATURES}}-feature vocabulary feeds non-negative matrix
factorization, which extracts {{NUM_TOPICS}} latent topics cross-cutting the subfield
taxonomy. Keyphrase and named-entity extraction surface the recurring concepts of the
literature without any language model.

Offline deterministic embeddings (TF-IDF followed by truncated SVD) place every document
in a shared vector space. Embedding the same text twice yields identical vectors, so the
derived similarity matrix, nearest-neighbour lists, clusters, and two-dimensional
projection are all reproducible. These embeddings support semantic retrieval over the
corpus and the visual map of the literature's topical geography.
