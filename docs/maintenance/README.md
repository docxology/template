# Maintenance — long-horizon viability guides

> Created 2026-05-20 as part of the multi-decade-viability hardening recommended by the World Threat Model run.
>
> These guides exist for one reason: this template repo is intended to be useful over a 10–50 year horizon, but its current toolchain (uv, ruff, mypy, Ollama, GitHub Actions, gemma3:4b) is overwhelmingly 2024–2026-vintage. The repo's *invariants* age well. Its *bindings* don't. These guides document how to migrate the bindings without losing the invariants.

## Contents

| Guide | Addresses | Created |
| --- | --- | --- |
| [`toolchain-migration.md`](toolchain-migration.md) | Pin the *interface* not the *tool* — how to swap uv, ruff, mypy, etc. without rewriting the repo | 2026-05-20 |
| [`regression-testing.md`](regression-testing.md) | Convert "90% coverage" hygiene into actual scientific-claim binding via pinned numerical outputs for figures/tables | 2026-05-20 |
| [`archival-targets.md`](archival-targets.md) | Insurance against Zenodo / arXiv / DOI vendor concentration via IPFS + Software Heritage parallel pins | 2026-05-20 |
| [`ci-local.md`](ci-local.md) | Local reproduction of the GitHub Actions matrix via `act` — defense against CI free-tier compression | 2026-05-20 |
| [`stage-10-executable-bundle.md`](stage-10-executable-bundle.md) | Design for a Stage 10 output (container + lockfile + agent-runnable manifest) alongside Stage 5 PDF — for the 2029+ executable-artifact world | 2026-05-20 |
| [`private-projects-repo.md`](private-projects-repo.md) | Sibling private repo lifecycle (`active/`, `passive/`, `archive/`) and symlink-sync contract for confidential projects | 2026-05-21; expanded 2026-05-24 |

## The thesis these guides share

The World Threat Model run identified that:

- The template's **architectural invariants** (thin orchestrator, two-layer, no-mocks, deterministic seeds, gitignore confidentiality enforcement) age extraordinarily well across all 11 horizons (6 months → 50 years).
- The template's **concrete bindings** (Python+uv+ruff+mypy+Ollama+gemma3:4b+GH Actions+LaTeX-PDF) decay starting ~3 years out and are archaeological by ~15 years.
- The gap between these two — "invariants that survive, bindings that don't" — is the **structural risk** the template carries.

These guides exist to close that gap by giving every binding a documented swap path. The goal is that, when (not if) `uv` is succeeded, `ruff` is succeeded, `gemma3:4b` is a museum piece, and `tlmgr install multirow cleveref` is a CVE-laden museum exhibit, a maintainer can swap each binding without rewriting the architectural commitments.

## Related

- [`MAINTAINERS.md`](../../MAINTAINERS.md) — who owns what
- [`STATUS.md`](../../STATUS.md) — per-subsystem heartbeat
- [`private-projects-repo.md`](private-projects-repo.md) — the implemented sibling private repo (active/passive/archive + lifecycle-link mechanism)
- [`AGENTS.md`](../../AGENTS.md) — full system manual
