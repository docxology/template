# tests/infra_tests/steganography/ - Steganography Tests

Tests for the steganography helpers in `infrastructure/steganography/`.

## Covered Behaviors

- overlay generation
- barcode payload formatting
- metadata injection
- hashing and integrity manifests
- encryption settings
- processor orchestration

## Run

```bash
uv run pytest tests/infra_tests/steganography/ -v
```

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../../README.md`](../../README.md)

## Repeat-call and failure-preservation controls

`test_processor.py` uses actual pypdf PDFs to inspect per-call embedded hashes,
source-alias refusal, legacy manifest naming, previous-output preservation and
password-encrypted provenance. `test_config.py` checks strict boolean opt-in.
`test_publication.py` exercises real destination/stage files, collisions,
no-overwrite admission and actual PDF parsing. `test_hashing.py` runs concurrent
manifest writers with unique atomic temporary files. Kmyth adapter controls use
missing providers and real filesystem publication; they do not simulate successful
TPM cryptography or authorize starting a daemon.
