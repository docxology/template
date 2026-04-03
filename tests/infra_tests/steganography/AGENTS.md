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
