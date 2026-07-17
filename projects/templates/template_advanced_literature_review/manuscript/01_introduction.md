# Introduction

Rapidly changing fields require literature reviews that preserve the distinction
between what was searched, what was retrieved, what was assessed, and what can be
claimed. A single broad query hides phase-specific coverage and makes it difficult to
explain how records entered a synthesis. This project treats a literature review as a
reproducible data pipeline: configuration defines the review design, source adapters
acquire records, analysis modules produce evidence artifacts, and rendering turns
those artifacts into an auditable manuscript.

The reporting surface follows the spirit of systematic-review transparency
[@page2021prisma] without implying that the bundled fixture satisfies a domain
protocol. A live review must define eligibility criteria, search dates, source
coverage, screening procedures, and a domain-appropriate synthesis plan before its
results are interpreted.

The bundled configuration targets **{{SEARCH_TERM_TITLE}}**. It defines three ordered
phases for foundational methods, JWST-era observations, and molecular detection. The
phase labels are configuration, not conclusions: a live review must justify its
boundaries and update its claim ledger when the domain or search strategy changes.

## Research Questions

1. **Coverage and retrieval.** Which engines, queries, filters, and identifiers
   contributed records to each phase, and where are the known coverage limits?
2. **Structure.** How do subfields, topics, authors, venues, and citation links vary
   across the configured phases?
3. **Evidence.** Which claims are supported by source-backed records, which remain
   pending, and which are only properties of the synthetic fixture?
4. **Reproducibility.** Can a clean run regenerate the data, figures, reports, and
   manuscript without unexplained differences?

## Scope and contribution

The project contributes a reusable workflow rather than a domain conclusion. Retrieval
and de-duplication preserve source observations; full-text assessment records access
status; bibliometrics and graph construction expose descriptive structure; and the
claim ledger separates fixture, configured, and source-backed statements. Subjective
editorial, scientific, and visual judgments remain explicit review items even when all
deterministic gates pass.

Every generated number in the rendered manuscript must come from an artifact listed in
the manifest and be traceable to the relevant method stage. Missing, stale, or
misclassified evidence is a release finding, not a value to be filled by hand.
