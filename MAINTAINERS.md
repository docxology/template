# Maintainers

> Single source of truth for who owns what in this template repo. Created 2026-05-20 as part of the multi-decade-viability hardening recommended by the World Threat Model run.

## Why this file exists

A template repo with ~18 infrastructure submodules and a 10-stage pipeline cannot be safely carried by a single operator for a decade. This file makes ownership **explicit** instead of **implicit-Daniel** — so dormancy is visible and successors have a clear handoff target.

## Primary maintainer

| Role | Person | Contact |
| --- | --- | --- |
| Repository owner & primary maintainer | Daniel Ari Friedman | <danielarifriedman@gmail.com> · [@docxology](https://github.com/docxology) |

## Subsystem owners

If you change code under a subsystem, the owner is the named point-of-contact for review and the person ultimately accountable for keeping it green. Default owner is **Daniel** for everything currently — names need adding as collaborators step in.

| Subsystem path | Owner | Co-owners | Notes |
| --- | --- | --- | --- |
| `infrastructure/config/` | Daniel | — | Repo-wide config + defaults |
| `infrastructure/core/` | Daniel | — | Logging, exceptions, pipeline, telemetry, security primitives |
| `infrastructure/docker/` | Daniel | — | Containerization settings (currently thin — see Stage 10 design) |
| `infrastructure/doctor/` | Daniel | — | Repo health diagnostics |
| `infrastructure/documentation/` | Daniel | — | Figure manager, API docs, glossary generation |
| `infrastructure/llm/` | Daniel | — | Ollama integration; label set to "draft assistance" not "scientific review" — see `infrastructure/llm/README.md` |
| `infrastructure/orchestration/` | Daniel | — | Pipeline / multi-project / secure CLI entrypoints |
| `infrastructure/project/` | Daniel | — | Multi-project discovery + management |
| `infrastructure/prose/` | Daniel | — | Prose-manuscript analysis (prose-centric projects) |
| `infrastructure/publishing/` | Daniel | — | DOI, citations, Zenodo, arXiv + (new) archival targets — see `docs/maintenance/archival-targets.md` |
| `infrastructure/reference/` | Daniel | — | Citation / reference management |
| `infrastructure/rendering/` | Daniel | — | Multi-format rendering (PDF, HTML, slides) |
| `infrastructure/reporting/` | Daniel | — | Pipeline reporting + error aggregation |
| `infrastructure/scientific/` | Daniel | — | Scientific computing best practices + benchmarking |
| `infrastructure/search/` | Daniel | — | Literature search + reference discovery |
| `infrastructure/skills/` | Daniel | — | Agent SKILL.md manifest |
| `infrastructure/steganography/` | Daniel | — | Cryptographic PDF watermarking — see `infrastructure/steganography/THREAT_MODEL.md` |
| `infrastructure/validation/` | Daniel | — | PDF, output, markdown integrity validation |
| `projects/template_code_project/` | Daniel | — | Canonical code-centric exemplar |
| `projects/template_prose_project/` | Daniel | — | Canonical prose-centric exemplar |
| `tests/infra_tests/` | Daniel | — | 60% coverage floor |
| `tests/regression/` | Daniel | — | NEW (2026-05-20) — pinned numerical outputs for manuscript figures/tables; see `docs/maintenance/regression-testing.md` |
| `.github/workflows/` | Daniel | — | CI matrix Ubuntu/macOS × Python 3.10–3.12; see `docs/maintenance/ci-local.md` for act-based reproduction |
| `scripts/` | Daniel | — | Pipeline stage scripts (00-07) + confidentiality enforcement (`check_tracked_projects.py`) |

## What being an owner means

- You review PRs that touch your subsystem (or designate a reviewer).
- You're accountable for the "last verified working" timestamp in `STATUS.md` for that subsystem.
- You decide when a subsystem is dormant enough that its public claims need to be downgraded (e.g., moving a stage from "tested" to "experimental").
- You're not solely responsible for fixing bugs there — but you are responsible for knowing whether someone is.

## How to add yourself

1. Open a PR adding your name + GitHub handle to a subsystem's "Co-owners" column.
2. In the PR description, state which "last verified" timestamp in `STATUS.md` you're committing to keep current (target: refresh every 6 months minimum).
3. After merge, you're listed; you can step back at any time by opening another PR.

## Succession plan

If Daniel becomes unavailable for an extended period:

1. First-tier successor: not yet designated. **TODO** — name a successor before the next major release.
2. The Active Inference Institute (AII) governance is the institutional fallback for the publishing / research-infrastructure orientation, but does not currently own this repo.
3. The repo's MIT license + permanent Zenodo DOI ([10.5281/zenodo.19139090](https://doi.org/10.5281/zenodo.19139090)) ensure the artifact remains available and forkable independent of any maintainer status.

## Related

- [`STATUS.md`](STATUS.md) — per-subsystem "last verified working on" heartbeat
- [`docs/maintenance/`](docs/maintenance/) — toolchain migration, regression testing, archival, local CI
- [`AGENTS.md`](AGENTS.md) — full system manual
- [`.github/AGENTS.md`](.github/AGENTS.md) — CI job names, thresholds
