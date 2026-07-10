# scripts - template_redacted_report

Use monorepo pipeline scripts from the repository root for normal test/render stages.

`generate_dev_variants.py` creates the development proof matrix for every redaction style and PDF background combination. By default it also runs the template steganography/provenance post-processor on every proof PDF and writes `output/dev/redaction_variants/variant_matrix.json`.

```bash
uv run python projects/templates/template_redacted_report/scripts/generate_dev_variants.py
```

If Kmyth is built under `infrastructure/steganography/kmyth/bin`, generation records Kmyth availability and `.ski` sidecar counts in the matrix. Use `--kmyth-binary-dir` to select a specific build, `--no-kmyth` to skip TPM sealing requests, and `--require-kmyth` to make missing tools or seal failures fatal.

Verify the rendered matrix after generation:

```bash
uv run python projects/templates/template_redacted_report/scripts/verify_dev_variants.py --render-smoke
```

The verifier enforces the stable `redaction_on_background.pdf`, `redaction_on_background_steganography.pdf`, and `redaction_on_background.hashes.json` filenames for all 16 visual combinations, checks matrix hashes, opens every PDF, and optionally rasterizes page 1 of every PDF with Poppler. After a TPM backend is configured, add `--require-kmyth-sidecars` to require both `.ski` sidecars for every variant.
