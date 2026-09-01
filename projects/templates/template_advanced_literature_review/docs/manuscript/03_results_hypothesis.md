# Results: Hypotheses and Evidence

The configuration declares {{N_HYPOTHESES}} hypotheses about exoplanet atmospheric
research. Their names, scopes, relevant phases, and scores are emitted from the
knowledge-graph artifacts rather than typed into the manuscript.

{{HYPOTHESIS_TABLE}}

Scores are descriptive evidence summaries, not calibrated probabilities or causal
effects. If the knowledge-graph stage is disabled, if a live language model is not
available, or if the corpus is synthetic, the result remains **pending** or
**fixture-derived**. A pending score is an honest absence of measurement; it is not a
zero and must not be interpreted as support or contradiction.

## Configured questions

- **H1: JWST atmospheric characterization.** What evidence is reported for improved
  characterization in the JWST-relevant phase?
- **H2: Molecular diversity detection.** Which molecules are reported, with what
  uncertainty and source provenance?
- **H3: Cross-method consistency.** Do independently described observational methods
  report compatible properties under the configured review scope?
- **H4: Theoretical-observational agreement.** How are model predictions compared with
  observed spectroscopic features?

These are review questions, not conclusions. Claim-level interpretation requires the
claim ledger, source tier, freshness, and domain review. A fixture run can test schema,
phase linkage, and serializer behavior, but cannot establish any of these hypotheses.
