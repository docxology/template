# Test Fixtures

## Overview

Technical guide for `tests/fixtures/` — shared test fixture data consumed by the template repository's test suites.

## Directory Structure

```mermaid
flowchart LR
    F[tests/fixtures]
    F --> RC[real_codebases]
    F --> PP[private_project/cogant]

    classDef d fill:#0f172a,stroke:#0f172a,color:#fff
    class F,RC,PP d
```

## Key Conventions

- Fixtures are populated by scripts in [`scripts/fixtures/`](../../scripts/fixtures/).
- `real_codebases/` contains sparse-checkout clones (only source subdirectories) — **do not edit** these; regenerate with `python scripts/fixtures/download_real_codebases.py`. Required when running tests marked `external_fixture`.
- `private_project/cogant/` is **git-tracked** — minimal COGANT audit/coverage scripts and manuscript fragment used when `projects/working/cogant/` is absent.
- `real_codebases/` and `timeseries/` are download-generated (see setup scripts below); they are not committed and must be created locally before running tests that need them.
- The committed [timeseries seed](timeseries_seed/README.md) supplies exact generated benchmark bytes to hosted acceptance and release readers; it is not empirical data.
- Timeseries fixtures are stored at `tests/fixtures/timeseries/` (created by `scripts/fixtures/download_timeseries_benchmarks.py`).

## See Also

- [README.md](README.md) — Quick navigation
- [`real_codebases/AGENTS.md`](real_codebases/AGENTS.md) — Real codebase fixture docs
- [`../../scripts/fixtures/AGENTS.md`](../../scripts/fixtures/AGENTS.md) — Fixture download scripts
- [`../AGENTS.md`](../AGENTS.md) — Test suite documentation

## Retained literature access-challenge DATA

`literature-client-challenge.txt` contains the exact 3,038-byte HTML response
retained from a Nature PDF URL, SHA-256
`32ed63159c77e21ee19ca1b9aa3213ccf0218eb59539560b132a8e68ef0e18ea`.
Real loopback HTTP workers replay these bytes to check explicit browser-challenge
unavailability and incomplete-signature refusal. Tests do not execute its scripts;
this fixture supplies neither article full text nor external-provider acceptance.
