# redacted_report - AGENTS.md

Keep the package deterministic and safety-focused. It validates release packets; it does not provide operational collection guidance.

`artifacts.py` is the only source-owned public JSON writer. Preserve its strict
loader and text-free projection: source segment text may be processed in memory
but must never appear in `redaction_audit.json` or `release_ledger.json`.

Keep report-level orchestration in `visuals.py` and proof-PDF drawing internals
in `_proof_renderer.py`; preserve the façade re-exports during the compatibility
window.
