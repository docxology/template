# Appendices

End-matter reference material for the textbook. These files are ordinary
markdown chapters that carry an `{#sec:...}` label and follow the same
crossref/citation/glossary conventions as the main chapters.

## What lives here

| File | Label | Purpose |
| --- | --- | --- |
| [`appendix_authoring_guide.md`](appendix_authoring_guide.md) | `sec:appendix_authoring_guide` | How to fill the stubs and grow the book — **read first** |
| [`appendix_notation.md`](appendix_notation.md) | `sec:appendix_notation` | Symbol table for the worked models |
| [`appendix_math_review.md`](appendix_math_review.md) | `sec:appendix_math_review` | Just-enough math, tied to `src/textbook/models.py` |
| [`appendix_index.md`](appendix_index.md) | `sec:appendix_index` | Generated index of key terms (placeholder) |

The master glossary [`../glossary.md`](../glossary.md) is also included as a
reference appendix (Appendix D).

## Ordering is data-driven

The order and display titles come from the single source of truth,
[`../config.yaml`](../config.yaml), under `appendices.reference`. The current
sequence is:

```text
A — appendix_authoring_guide.md   (sec:appendix_authoring_guide)
B — appendix_notation.md          (sec:appendix_notation)
C — appendix_math_review.md       (sec:appendix_math_review)
D — glossary.md                   (master glossary)
E — appendix_index.md             (sec:appendix_index)
```

To add, remove, or reorder an appendix, edit `appendices.reference` in
`config.yaml` — never renumber by hand. Toggle whole groups with
`include_reference`, `include_labs`, and `include_questions`.

See the sibling READMEs for the [labs convention](../labs/README.md) and the
[question-bank convention](../questions/README.md).
