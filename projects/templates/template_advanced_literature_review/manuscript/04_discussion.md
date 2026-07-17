# Discussion

## Interpretation boundary

This pipeline describes the shape of a retrieved literature slice: its phase coverage,
metadata completeness, topic structure, citation links, and declared evidence. It does
not adjudicate scientific truth. Hypothesis scores, when available, summarize recorded
assertions and should be read as evidence-landscape signals rather than calibrated
probabilities.

## Retrieval and phase bias

Engine availability, query wording, rate limits, temporal boundaries, identifier
quality, and full-text access all shape the retained corpus. The retrieval report is the
authoritative account of source outcomes; counts must never be reverse-engineered from
the merged corpus. Phase overlap and cross-phase citation rates are descriptive checks,
not proof that phases are independent or exhaustive.

## Fixture and live modes

The offline path uses reserved synthetic identifiers and generated records. Fixture
outputs validate the machinery and its contracts only. A live review must replace the
fixture, retain source-level provenance, refresh the claim ledger, and obtain domain
review before reporting substantive findings. The manuscript therefore uses explicit
pending and fixture-derived states rather than silently promoting demonstration values.

## Limitations and extensions

- Keyword taxonomies can misclassify ambiguous records; changes belong in configuration
  and should be accompanied by a regenerated classification report.
- TF-IDF/SVD embeddings are lexical and deterministic; transformer-based alternatives
  require an explicit dependency and evaluation decision.
- LLM extraction is optional, model-sensitive, and not a substitute for source review.
- Full-text availability is a coverage measure, not a quality measure.
- Reproducibility claims require a clean double run and normalized artifact comparison.

These limitations are represented as method-stage and review-required findings so a
publication decision can distinguish deterministic failures from editorial judgment.
