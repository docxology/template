# Manuscript Notes

## Source files

| File | Role |
| --- | --- |
| `config.yaml` | Live paper metadata, thresholds, and publication fields |
| `config.yaml.example` | Fork-safe placeholder template |
| `source_ledger.yaml` | Offline scholarly source contract (citekeys, tiers, checked dates) |
| `layer_contract.yaml` | Manuscript layer and tokenization contract |
| `references.bib` | Curated bibliography (read-only in the exemplar) |
| `preamble.md`, `0*_*.md`, `99_references.md` | Numbered IMRAD sections |

## Tokenization contract

Do not hard-code generated loop counts or ML metrics in numbered prose. Add
variables in `src/manuscript/manuscript_tokens_core.py` or
`src/manuscript/manuscript_tokens_ml.py` (facade: `src/manuscript_variables.py`)
and verify coverage in `tests/test_manuscript_variables.py`.

Strict tokenization means hydration fails on raw accepted-candidate IDs, metric
values, dataset/model labels, artifact paths, or registry captions left in
numbered sections. Figure blocks must come from the registry-backed sidecars
written during loop hydration.

The manuscript artifact table lists only reviewed upstream analysis and
evidence paths plus their roles; unknown paths are omitted by default. Exact
bytes and the complete inventory, including manuscript-derived render, release,
receipt, and transitive binder artifacts, remain authoritative only in
`output/reports/artifact_manifest.json`. Embedding downstream rows or any byte
counts would make a newly enabled format, transmission bookend, changed render,
or binder update alter the Results section and create a one-generation feedback
loop.

## Validation

- Source ledger: `scripts/check_source_ledger.py` and `tests/test_source_ledger.py`
- Token coverage: `tests/test_manuscript_variables.py`
- Tables vs ledgers: `tests/test_manuscript_tables.py`
- Prerender: `uv run python -m infrastructure.validation.cli prerender manuscript --repo-root ../../..`
