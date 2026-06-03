# Appendix B — Notation and Symbols {#sec:appendix_notation}

<!-- chapter-metadata-badge -->
> Reference appendix · Symbol glossary for the worked models.

This appendix lists the symbols used by the worked formalisms in
[`src/textbook/models.py`](../../src/textbook/models.py). Keep it in sync with the
parameter tables (`{#tbl:...}`) in the chapters: every symbol that appears in an
equation `{#eq:...}` should have a row here.

## Conventions

- Scalars are italic lowercase (e.g. *r*, *t*); sets and spaces are uppercase.
- Subscript `0` denotes an initial value (e.g. *N*₀ at *t* = 0).
- Units are stated in SI / metric unless a chapter declares otherwise.

## Symbol Table

| Symbol | Name | Appears in | Units | Notes |
| --- | --- | --- | --- | --- |
| *t* | time / independent variable | all dynamic models | s (or chapter unit) | <!-- STUB --> |
| *N* | state quantity / population | `logistic_growth` | dimensionless | <!-- STUB --> |
| *N*₀ | initial state | `logistic_growth`, `exponential_decay` | dimensionless | <!-- STUB --> |
| *r* | intrinsic growth rate | `logistic_growth` | 1/time | <!-- STUB --> |
| *K* | carrying capacity | `logistic_growth` | dimensionless | <!-- STUB --> |
| *λ* (lambda) | decay constant | `exponential_decay`, `half_life` | 1/time | <!-- STUB --> |
| *t*½ | half-life | `half_life` | time | <!-- STUB --> |
| *V*max | maximum response | `saturating_response` | response unit | <!-- STUB --> |
| *K*ₘ | half-saturation constant | `saturating_response` | input unit | <!-- STUB --> |
| *x*, *y* | paired observations | `linear_fit` | data unit | <!-- STUB --> |
| *m*, *b* | slope, intercept | `linear_fit` | derived | <!-- STUB --> |
| *μ*, *σ* | mean, standard deviation | `descriptive_statistics` | data unit | <!-- STUB --> |

<!-- STUB: add project-specific symbols and any reused Greek letters here. -->

See also: [Appendix C — Mathematical Review](appendix_math_review.md).
