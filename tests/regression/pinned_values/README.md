# `tests/regression/pinned_values/` — ground-truth JSON

> One JSON file per project. Each file is the immutable record of
> every numerical manuscript claim for that project.

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

One file per project — currently `template_code_project.json` has live pins and
`template_prose_project.json` remains scaffolded. New projects add a new file
using the same shape.

## Discipline

**Never edit a value without a paired provenance entry.** A change
to a value without a `_provenance.<key>` update is the same as
editing the manuscript without justification — that pattern is
what this tier exists to prevent.

See [`../README.md`](../README.md) for the full philosophy.
