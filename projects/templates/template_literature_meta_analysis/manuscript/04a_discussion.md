# Discussion

## What the Template Is, and Is Not

The pipeline measures the *shape* of a literature — its size, growth, subfield
composition, topical structure, citation geometry, and the hypotheses a field frames. It
does not adjudicate scientific truth. The optional hypothesis scores summarize how the
retrieved corpus *talks about* each claim, weighted by citation influence; they are an
evidence-landscape instrument, not a verdict.

The {{NUM_TOPICS}} topics extracted by NMF provide a data-driven complement to the
keyword-based subfield taxonomy. Where the taxonomy assigns each paper to a single bucket,
the topics reveal overlapping thematic structure: a paper on modafinil's cognitive effects
in ADHD patients belongs to the "Psychiatry" subfield but also loads on the "Cognitive
Enhancement" and "ADHD Treatment" topics. This multi-resolution view is more informative
than either approach alone.

## Engine Coverage and Bias

For this live run, the corpus is dominated by OpenAlex (1,000 records) and Crossref
(1,000 records), with PubMed contributing 986 records and arXiv contributing 1.
Semantic Scholar was rate-limited (HTTP 429) and returned zero records — a known
limitation of its unauthenticated API tier. SovietRxiv and ChinaRxiv returned zero
records for the modafinil query, which is expected given their coverage domains.

The max-results cap of 1,000 per engine means the full literature is larger than the
retrieved corpus; the {{CORPUS_SIZE}} records represent a bounded sample rather than the
complete literature. The citation network resolution rate of
{{CITATION_RESOLUTION_PCT}}\% reflects this: many cited works lie outside the retrieved
slice. Increasing the cap or adding more engines would improve coverage but also
increase runtime and API load.

## Honest Defaults

The committed seed corpus is synthetic (reserved test DOIs, generated authors) so that
the whole pipeline runs offline and byte-identically. Its numbers demonstrate the
machinery; they are not empirical findings about {{SEARCH_TERM}}. Real claims require a
live retrieval run with regenerated figures, reports, and manuscript variables — as
produced in this instance.

## Limitations and Extensions

Several limitations bound the interpretation of results:

- **Coverage is bounded by the enabled engines and the query.** The max-results cap
  truncates each engine's contribution. Semantic Scholar's rate limiting excluded a
  major source; a Semantic Scholar API key would resolve this.

- **Subfield classification is keyword-based** and only as good as the configured
  taxonomy. Ambiguous papers may be misclassified; a classifier based on embeddings or
  supervised learning could improve accuracy.

- **The default embeddings are lexical** (TF-IDF/SVD). They capture term co-occurrence
  but not semantic similarity; a transformer backend (`embeddings` extra) would improve
  the quality of nearest-neighbour retrieval and clustering.

- **Hypothesis scoring depends on an external language model.** Without Ollama running,
  scores read *pending*. The scoring is also sensitive to prompt design and model
  choice; the default `gemma3:4b` is a lightweight model suitable for demonstration but
  may miss nuanced assertions.

- **Abstract coverage is {{ABSTRACT_COVERAGE_PCT}}\%.** Text analytics operate only on
  the subset of records with abstracts, biasing topic models and embeddings toward
  well-indexed sources.

Each limitation is a configuration or dependency choice rather than a change to the core
architecture.
