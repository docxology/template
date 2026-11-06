# tests/infra_tests/steganography/ - Steganography Test Documentation

## Purpose

The `tests/infra_tests/steganography/` directory validates PDF watermarking, metadata, barcode generation, hashing, encryption configuration, and processor orchestration.

## Standards

- Use real PDF and file artifacts where the behavior depends on them.
- Keep tests deterministic.
- Prefer direct inspection of generated outputs over mocks.

## Covered Modules

- overlay helpers
- barcode helpers
- metadata helpers
- hashing helpers
- encryption helpers
- processor entry points

## See Also

- [`README.md`](README.md)
- [`../../AGENTS.md`](../../AGENTS.md)

## Repeat-call and failure-preservation controls

`test_processor.py` uses actual pypdf PDFs to inspect per-call embedded hashes,
source-alias refusal, legacy manifest naming, previous-output preservation and
password-encrypted provenance. `test_config.py` checks strict boolean opt-in.
`test_publication.py` exercises real destination/stage files, collisions,
no-overwrite admission and actual PDF parsing. `test_hashing.py` runs concurrent
manifest writers with unique atomic temporary files. Kmyth adapter controls use
missing providers and real filesystem publication; they do not simulate successful
TPM cryptography or authorize starting a daemon.
