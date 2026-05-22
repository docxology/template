# `tests/regression/pinned_values/` — ground-truth JSON

> One JSON file per project. Each file is the immutable record of
> every numerical manuscript claim for that project.

## File shape

```json
{
  "_provenance": {
    "<key>": {
      "commit": "<git SHA>",
      "date": "<ISO 8601>",
      "reason": "<why this value>",
      "script": "<command that produced it>"
    }
  },
  "<group>": {
    "<key>": <pinned value>
  }
}
```

## Files

One file per project — currently `template_code_project.json` and
`template_prose_project.json`. New projects add a new file using
the same shape.

## Discipline

**Never edit a value without a paired provenance entry.** A change
to a value without a `_provenance.<key>` update is the same as
editing the manuscript without justification — that pattern is
what this tier exists to prevent.

See [`../README.md`](../README.md) for the full philosophy.
