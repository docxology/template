# Hashing and Manifests

Whenever the Secure Run pipeline executes on a manuscript PDF with hashing enabled, it calculates cryptographic hashes of the rendered source PDF and outputs them alongside the generated file.

## Cryptographic Operations

During the post-processing phase of `./secure_run.sh`, the system calculates two hashes for every PDF it processes:

1. `SHA-256`
2. `SHA-512`

> **Note:** The hash is calculated *before* the final steganographic metadata layers are injected, but *after* manuscript rendering occurs. The manifest therefore records the rendered source PDF bytes that the steganography step consumed, not a detached digital signature.

## Provenance Manifest

A `.hashes.json` manifest is written to the output directory immediately adjacent to the finalized PDFs. This file tracks the timestamp, document ID, configured hashes, source filename, source size, and Git commit when Git metadata is available. If Git metadata is unavailable, the manifest records that fact instead of inventing a commit.

If `projects/templates/template_code_project/output/pdf/template_code_project_combined.pdf` was processed, the engine will drop `template_code_project_combined.hashes.json` right next to it.

## Internal Binding

Because file names change, the pipeline reads the computed hash values and internally binds a serialized copy of the document ID and provenance payload directly into the `PDF XMP` metadata layer when metadata injection is enabled.

If an academic text is found later, you can inspect its internal metadata structure to find its `Doc-ID` and cross-reference the hashes against the adjacent `.hashes.json` manifest and the original rendered source PDF when available. This detects mismatch against the recorded source bytes; it is not a public-key signature scheme.


## See Also

- **[Security Index](README.md)** — Security policies and procedures
