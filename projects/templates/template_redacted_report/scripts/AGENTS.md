# scripts - AGENTS.md

Keep scripts thin and delegate release-audit logic to `src/redacted_report/`.

| Script | Role |
| --- | --- |
| `01_generate_release_artifacts.py` | The only normal Stage 02 entrypoint (allowlisted in `manuscript/config.yaml` → `analysis.scripts`). Loads `data/example_segments.json` through the typed `redacted_report.artifacts` contract and writes deterministic, text-free `output/reports/redaction_audit.json` and `output/data/release_ledger.json`. |
| `generate_dev_variants.py` | Explicit opt-in: builds the 4×4 development proof PDF matrix (optionally with steganography and Kmyth TPM sidecars) under `output/dev/redaction_variants/`. Not part of the normal Stage 02 order. |
| `verify_dev_variants.py` | Explicit opt-in: verifies generated proof PDFs, hash manifests, and the variant matrix (optionally rasterizing with pdftoppm or requiring Kmyth sidecars). |

Development visual generation and verification remain explicit commands; only
`01_generate_release_artifacts.py` runs in the normal pipeline.
