# tests - AGENTS.md

Use invented fixture segments only. Never add restricted source material.
Artifact tests must use unique synthetic canaries and assert both public JSON
files omit the canary while retaining only its SHA-256 evidence.

| Test file | Scope |
| --- | --- |
| `test_redaction.py` | Release-audit behavior: classification ceilings, redaction bounds, overlap rejection, orphan decisions, source-control coverage, residual-marker detection, mosaic-risk scoring, review gates, ledgers, and hash manifests. |
| `test_release_artifacts.py` | Typed fixture loading, malformed/missing input failures, canonical two-run JSON byte equality, source-canary non-disclosure, and real CLI execution. |
| `test_visuals_coverage.py` | Visual redaction styles, PDF background modes, variant-id enumeration, and negative controls over crafted files. |
| `test_visuals_proofs.py` | Proof-PDF generation and verification, including the 16-variant development matrix semantics and Kmyth requested/available matrix behavior. |
