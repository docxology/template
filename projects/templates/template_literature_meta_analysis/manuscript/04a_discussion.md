# Discussion

**What the template is, and is not.** The pipeline measures the *shape* of a literature —
its size, growth, subfield composition, topical structure, citation geometry, and the
hypotheses a field frames. It does not adjudicate scientific truth. The optional
hypothesis scores summarize how the retrieved corpus *talks about* each claim, weighted by
citation influence; they are an evidence-landscape instrument, not a verdict.

**Honest defaults.** The committed seed corpus is synthetic (reserved test DOIs, generated
authors) so that the whole pipeline runs offline and byte-identically. Its numbers
demonstrate the machinery; they are not empirical findings about {{SEARCH_TERM_TITLE}}.
Real claims require a live retrieval run with regenerated figures, reports, and manuscript
variables.

**Limitations and extensions.** Coverage is bounded by the enabled engines and the query;
subfield classification is keyword-based and only as good as the configured taxonomy; the
default embeddings are lexical (TF-IDF/SVD) and can be upgraded to a transformer backend;
and hypothesis scoring depends on an external language model. Each is a configuration or
dependency choice rather than a change to the core architecture.
