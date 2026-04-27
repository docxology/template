# Hashing and Manifests

Whenever the Secure Run pipeline executes on a manuscript PDF, it automatically calculates cryptographic signatures of the file and outputs them alongside the generated file.

## Cryptographic Operations

During the post-processing phase of `./secure_run.sh`, the system calculates two checksums for every finalized PDF:

1. `SHA-256`
2. `SHA-512`

> **Note:** The hash is calculated *before* the final steganographic metadata layers are injected, but *after* the text rendering occurs. This ensures the hashes reflect the true content.

## Provenance Manifest

A `.hashes.json` manifest is written to the output directory immediately adjacent to the finalized PDFs. This file tracks the timestamp, doc-id, SHA-256 hash, and SHA-512 hash.

If `projects/code_project/output/pdf/code_project_combined.pdf` was processed, the engine will drop `code_project_combined.hashes.json` right next to it.

## Internal Binding

Because file names change, the pipeline reads the `.hashes.json` and internally binds a serialized copy of the document ID and cryptographic proof payload directly into the `PDF XMP` metadata layer.

If an academic text is found floating on a repository 5 years later, you can scrape its internal metadata structure to find its original generative `Doc-ID` and cross-reference its hashes inside the XMP dictionary to prove if its structural bytes have been altered since compilation.


## See Also

- **[Security Index](../security/README.md)** — Security policies and procedures
