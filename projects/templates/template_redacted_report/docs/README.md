# docs - README.md

Design decisions and verification notes for the `template_redacted_report`
exemplar. The root contract is [`../AGENTS.md`](../AGENTS.md).

## Design decisions

### Text-free public projections

`output/reports/redaction_audit.json` and `output/data/release_ledger.json`
are the only source-owned public JSON writers (`src/redacted_report/artifacts.py`).
The comprehensive sanitized packet exists in memory only. Public artifacts may
carry sanitized metadata and SHA-256 digests, never source spans, review
rationales, or reviewer identities. A canary test proves the source text never
reaches the serialized bytes.

### Volatile numbers are bound, not hand-maintained

Measured values in the manuscript's results table are re-derived from a fresh
canonical audit run by `tests/test_manuscript_binding.py`, which also fails
closed if the audit or ledger `schema_version` changes. Edit the fixture or the
engine, then update the prose table to the newly measured values.

### Deterministic figures

`src/redacted_report/figures.py` renders the two declared figure types
(`domain_profile.yaml` `figure_types`) with matplotlib. Determinism requires:
fixed `svg.hashsalt`, no randomness, fixed canvas/palette, and stripping the
live `<dc:date>` SVG metadata line. `tests/test_figures.py` asserts the
tracked `output/figures/` evidence equals a fresh build byte-for-byte.

### Organization-specific policies

`declared_release_policies()` exposes four invented adapters
(intelligence, law-enforcement, public-records, health-privacy) over the same
audit engine. The canonical pipeline stays on `intelligence_release_review`;
forks select their own policy for their own cleared fixtures.

## Verification workflow

```bash
uv run pytest projects/templates/template_redacted_report/tests \
  --cov=projects/templates/template_redacted_report/src --cov-fail-under=90
uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_redacted_report
uv run python scripts/pipeline/stage_03_render.py --project templates/template_redacted_report
uv run python scripts/pipeline/stage_04_validate.py --project templates/template_redacted_report
uv run python scripts/audit/check_template_drift.py --project templates/template_redacted_report --strict
```

## Boundary rules

- Invented fixtures only; no restricted source material, targeting,
  collection, evasion, or surveillance operational guidance.
- Never hand-edit `output/`; regenerate from source through Stages 02-05.
- The Kmyth TPM path (swtpm proxy, FlushContext patch) is optional and
  hardware-dependent; tracked dev evidence ships without `.ski` sidecars by
  `.gitignore` design.
