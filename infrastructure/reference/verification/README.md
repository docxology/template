# reference/verification

Deterministic reference-existence verification — an anti-hallucination gate for
manuscript bibliographies.

## What it does

Parses a `.bib` file and, for every entry, decides one of:

| Status | Meaning | Blocks gate? |
| --- | --- | --- |
| `ok` | Resolved and metadata matches | no |
| `mismatch` | Resolved, but title/author/year disagree | **yes** |
| `fabricated` | Has a DOI/arXiv id that resolves to nothing | **yes** |
| `anachronism` | Cited (or indexed) year is after the as-of year | **yes** |
| `unverifiable` | No identifier and title search inconclusive | no (warn) |
| `unchecked` | Offline and not cached — never silently OK | no (warn) |

## Design

- **Offline-first.** Network is opt-in (`--live` / `allow_network=True`). Tests
  and CI run offline against a pre-seeded cache or `pytest-httpserver`.
- **Reuses search backends.** Crossref/arXiv field mapping comes from
  `infrastructure.search.literature`, so discovery and verification cannot drift.
- **Persistent SQLite cache.** Positive and negative resolutions are cached with
  a 90-day TTL.
- **No mocks.** HTTP paths are tested with `pytest-httpserver`; the offline path
  with a real temp SQLite file.

## Quick start

```bash
uv run python -m infrastructure.reference.verification verify \
    projects/templates/template_code_project/manuscript/references.bib --live --json
```

See [`SKILL.md`](SKILL.md) for the agent-facing descriptor and
[`AGENTS.md`](AGENTS.md) for contributor notes.
