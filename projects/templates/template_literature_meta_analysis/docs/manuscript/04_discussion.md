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

The committed analysis corpus is a bounded retrieval snapshot. It predates the
deterministic per-engine retrieval report introduced by this template, so this paper
does not attribute record counts or success/failure states to individual engines by
reverse-engineering the merged corpus. New runs write those facts directly to
`output/data/retrieval_report.json`; a resumed legacy snapshot is explicitly labelled
`resume_without_prior_retrieval_report` rather than being given invented provenance.

The max-results cap of 1,000 per engine means the full literature is larger than the
retrieved corpus; the {{CORPUS_SIZE}} records represent a bounded sample rather than the
complete literature. The citation network resolution rate of
{{CITATION_RESOLUTION_PCT}}\% reflects this: many cited works lie outside the retrieved
slice. Increasing the cap or adding more engines would improve coverage but also
increase runtime and API load.

## Honest Defaults

The small corpus under `data/fixtures/` is synthetic (reserved test DOIs and generated
authors) and exists only for offline tests. It is not silently substituted for the
tracked analysis corpus. A user who regenerates empirical findings must run retrieval,
analysis, figures, and manuscript injection together and retain the resulting corpus and
retrieval report; fixture-only runs demonstrate machinery, not findings about
{{SEARCH_TERM}}.

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
  scores read *pending*; with Ollama configured (as in this run, with {{TOTAL_ASSERTIONS}}
  assertions extracted), scores are populated. The scoring is also sensitive to prompt
  design and model choice; the default `gemma3:4b` is a lightweight model suitable for
  demonstration but may miss nuanced assertions.

- **Abstract coverage is {{ABSTRACT_COVERAGE_PCT}}\%.** Text analytics operate only on
  the subset of records with abstracts, biasing topic models and embeddings toward
  well-indexed sources.

Each limitation is a configuration or dependency choice rather than a change to the core
architecture.
