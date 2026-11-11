# `tests/regression/pinned_values/` — declared quantitative baselines

One JSON file per project declaring bound claims in `../claim_bindings.json`.
Each file records those selected claims, tolerances and their provenance; it is
not an exhaustive inventory or independent validation of every manuscript claim.

## File shape

```json
{
  "_meta": {
    "schema_version": "1.1",
    "project_name": "<project>"
  },
  "_provenance": {
    "<key>": {
      "commit": "<git SHA>",
      "date": "<ISO 8601>",
      "reason": "<why this value>",
      "script": "<command that produced it>"
    }
  },
  "<key>": {
    "manuscript_section": "<file>.md / <section>",
    "claim_text": "<claim with the value token or rendered value>",
    "value": 1.0,
    "abs_tolerance": 0,
    "verifier_function": "<dotted source function>",
    "verifier_args": {"source": "<source artifact or config>"},
    "pinned_on": "YYYY-MM-DD",
    "pinned_by": "<name>",
    "pinned_at_commit": "<git SHA>"
  }
}
```

## Files

The current roster is `../claim_bindings.json`; only its `bound` projects require
pin files. Prose's current editorial measurements are not frozen numerical
baselines. Its separate source-integrity test checks current bibliography
resolution instead.

## Discipline

**Never edit a value without a paired provenance entry.** A change
to a value without a `_provenance.<key>` update is the same as
editing the manuscript without justification — that pattern is
what this tier exists to prevent.

See [`../README.md`](../README.md) for the full philosophy.
