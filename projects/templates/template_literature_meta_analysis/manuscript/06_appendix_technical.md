# Appendix B: Technical Notes

**Determinism.** All stochastic steps use fixed seeds. The fixture corpus, TF-IDF/SVD
embeddings, and topic factorization are byte-stable across runs. Graph centrality scores
are rounded to a fixed precision and ranked with a node-id tiebreaker so that
floating-point non-associativity in iterative solvers cannot perturb the reported
rankings. Record identity uses a content digest (not a salted hash) so de-duplication and
corpus byte-stability hold across processes.

**Data model.** Each record is a `Paper` with title, abstract, authors, year, venue,
citation count, references, identifiers (DOI / arXiv / Semantic Scholar / OpenAlex), and
optional full-text provenance. The canonical identifier hierarchy governs de-duplication
and citation resolution.

**Configuration surface.** A single `manuscript/config.yaml` controls the search term,
per-engine query and keyword sets, engine enable toggles, subfield taxonomy, hypotheses,
full-text and embedding options, and paper metadata. This run drew on
{{N_ENGINES}} engines, a {{N_SUBFIELDS}}-bucket taxonomy, and {{N_HYPOTHESES}} hypotheses.

**Artifacts.** Intermediate and final outputs (`corpus.jsonl`, analysis JSON, figures,
the rendered manuscript) live under `output/` and are disposable and regenerable.
