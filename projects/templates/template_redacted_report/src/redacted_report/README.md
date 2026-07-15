# redacted_report package

Audits redaction decisions, classification ceilings, source controls, taxonomy normalization, sanitized release packets, source-safe ledgers, segment hashes, reviewer gates, paragraph tables, and mosaic risk.

`artifacts.py` turns `data/example_segments.json` into typed domain records,
builds the comprehensive packet in memory under the declared intelligence
policy, and exports a text-free audit plus hashed ledger. The serializer uses
sorted-key JSON with a final newline for byte-deterministic reruns.

`visuals.py` is the public visualization façade and owns report-level figure
composition. `_proof_renderer.py` contains the focused proof-PDF renderer and
segment/redaction drawing primitives, avoiding a monolithic rendering module.
