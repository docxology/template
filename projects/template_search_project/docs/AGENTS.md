# template_search_project/docs — Agent guide

## Purpose

Project-local documentation that sits next to code: quickstart, architecture, output layout, and troubleshooting. Repo-wide literature docs live under [`docs/modules/`](../../../docs/modules/) and [`docs/guides/`](../../../docs/guides/).

## Contents

| File | Role |
|------|------|
| [`quickstart.md`](quickstart.md) | Minimal commands and expectations |
| [`architecture.md`](architecture.md) | Data flow and module boundaries |
| [`output_conventions.md`](output_conventions.md) | Paths under `output/` |
| [`troubleshooting.md`](troubleshooting.md) | Common failures |

## Contracts

- Prefer linking to [`../manuscript/config.yaml`](../manuscript/config.yaml) as the single configuration reference.
- Paths in docs assume execution from repository root (`template/`) unless stated otherwise.

## See also

- [`../AGENTS.md`](../AGENTS.md) — project overview
- [`README.md`](README.md) — doc index
