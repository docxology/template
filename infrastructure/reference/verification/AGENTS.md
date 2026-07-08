# AGENTS — reference/verification

## Layering

- Depends on `infrastructure.search.literature` (backends, `Paper`,
  `HttpClient`) and `infrastructure.reference.citation` (bib parsing) and
  `infrastructure.core.text_slug` (surname extraction). Do not import upward
  from `projects/` or `scripts/`.
- This is generic infrastructure: no project-specific logic.

## Models (`models.py`)

- `VerificationStatus` — enum of per-reference outcomes (`ok`, `mismatch`,
  `fabricated`, `unverifiable`, `unchecked`, `anachronism`); `BLOCKING_STATUSES`
  is the frozenset that fails a gate by default (`fabricated` / `mismatch` /
  `anachronism`).
- `ReferenceVerdict` — one reference's result (`citation_key`, `status`,
  `detail`, `doi`, `arxiv_id`, `resolved_via`, `title_similarity`, `issues`)
  with `is_ok` / `is_blocking` properties and `to_dict()`.
- `VerificationReport` — aggregate over every verdict; `counts()`, `blocking` /
  `has_blocking`, `to_dict()`, and `summary_line()`.

## Invariants

- **Offline never passes silently.** With `allow_network=False` and a cache
  miss, the verdict MUST be `unchecked`, never `ok`. Preserve this — it is the
  honesty contract (mirrors the repo rule "missing tools report skipped, not
  clean").
- **Negative caching is intentional.** A looked-up-but-not-found identifier is
  cached as a negative result so the `fabricated` signal is fast and stable.
- **Determinism.** Title similarity uses `difflib.SequenceMatcher` over
  normalized titles — no randomness, no network in the comparison path.
- **No mocks in tests.** Use `pytest-httpserver` for Crossref/OpenAlex/arXiv and
  a real temp SQLite file for the cache.

## Extending

- New index backend: add a `_resolve_*` branch in `ReferenceResolver`, return a
  normalized `Paper`, and pass `source=` so the cache records provenance.
- New status: add to `VerificationStatus`, decide membership in
  `BLOCKING_STATUSES`, and add a classification branch in `verify_entry`.

## Tests

`tests/infra_tests/reference/verification/` — cover each status (offline
unchecked, cached hit, fabricated, mismatch, anachronism, title resolution) with
no mocks.
