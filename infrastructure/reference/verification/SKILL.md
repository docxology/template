---
name: reference-verification
description: Deterministic anti-hallucination gate for cited references. Resolves each entry in a manuscript .bib file against Crossref, OpenAlex, and arXiv; flags fabricated (identifier resolves to nothing), mismatched (title/author/year disagree), unverifiable (no identifier), unchecked (offline cache miss — never silently OK), and anachronistic (future-dated) citations. Offline-first with a persistent SQLite cache; live network resolution is opt-in. Use when verifying citation existence, auditing a references.bib before submission, or wiring a claim-verification / pipeline integrity gate.
---

# Skill Descriptor — infrastructure/reference/verification

## Module Overview

Given the references a manuscript *claims* to cite, prove (or disprove) that
each one exists and matches its cited metadata. This is the verification side of
the literature workflow; `infrastructure/search/literature` is the discovery
side.

## Capabilities

- **Resolve**: DOI → Crossref then OpenAlex (cross-index triangulation); arXiv
  id → arXiv API; bare title → Crossref title search with a similarity floor.
- **Classify** (deterministic): `ok`, `mismatch`, `fabricated`, `unverifiable`,
  `unchecked`, `anachronism`.
- **Offline-first**: with `allow_network=False` (default), consult only the
  SQLite cache and report `unchecked` on a miss — a skipped check never
  launders into a clean pass.
- **Persistent cache**: SQLite, 90-day TTL, stores negative results so
  "fabricated" is fast and stable.
- **Temporal integrity**: flag citations dated after the manuscript's as-of year.

## CLI

```bash
uv run python -m infrastructure.reference.verification verify references.bib
uv run python -m infrastructure.reference.verification verify references.bib --live --as-of-year 2026 --fail-on-issues
uv run python -m infrastructure.reference.verification verify references.bib --json
uv run python -m infrastructure.reference.verification cache-clear
```

## Python API

```python
from infrastructure.reference.verification import ReferenceResolver, ResolutionCache, verify_bibfile

resolver = ReferenceResolver(cache=ResolutionCache("cache.db"), allow_network=True)
report = verify_bibfile("references.bib", resolver, as_of_year=2026)
print(report.summary_line())
assert not report.has_blocking
```

## See Also

- [`resolver.py`](resolver.py) — DOI/arXiv/title resolution
- [`verifier.py`](verifier.py) — classification + temporal integrity
- [`cache.py`](cache.py) — persistent SQLite resolution cache
- [`infrastructure/search/literature/SKILL.md`](../../search/literature/SKILL.md) — discovery side
- [`docs/prompts/manuscript-claim-verification/SKILL.md`](../../../docs/prompts/manuscript-claim-verification/SKILL.md) — workflow that drives this gate

## Provenance

The status taxonomy and cross-index/temporal-integrity ideas are an original,
Apache-2.0 distillation of patterns from
[Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills)
(CC-BY-NC-4.0). No ARS code is vendored.
