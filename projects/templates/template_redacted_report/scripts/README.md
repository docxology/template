# scripts - template_redacted_report

Use monorepo pipeline scripts from the repository root for normal test/render stages.

## Canonical Stage 02 analysis

`manuscript/config.yaml` allowlists one normal analysis entrypoint:

```bash
uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_redacted_report
```

This runs `01_generate_release_artifacts.py`, a thin wrapper around
`redacted_report.write_release_artifacts()`. It reads
`data/example_segments.json` and writes only
`output/reports/redaction_audit.json` and
`output/data/release_ledger.json`. Both files are canonical JSON and exclude
source text. Run the script directly with `--input` and `--output-root` only for
fixture testing or a standalone fork.

## Development visual matrix

`generate_dev_variants.py` creates the development proof matrix for every redaction style and PDF background combination. By default it also runs the template steganography/provenance post-processor on every proof PDF and writes `output/dev/redaction_variants/variant_matrix.json`.

```bash
uv run python projects/templates/template_redacted_report/scripts/generate_dev_variants.py
```

Kmyth TPM sidecar sealing is optional and disabled by default. Use `--with-kmyth` to request sealing with tools on `PATH`, `--kmyth-binary-dir infrastructure/steganography/kmyth/bin` to pin the bundled build, or `--require-kmyth` when missing tools or failed sealing should block generation.

Verify the rendered matrix after generation:

```bash
uv run python projects/templates/template_redacted_report/scripts/verify_dev_variants.py --render-smoke
```

The verifier enforces the stable `redaction_on_background.pdf`, `redaction_on_background_steganography.pdf`, and `redaction_on_background.hashes.json` filenames for all 16 visual combinations, checks matrix hashes, opens every PDF, and optionally rasterizes page 1 of every PDF with Poppler. For Kmyth-enabled runs, add `--require-kmyth-sidecars` to require both `.ski` sidecars for every variant.
