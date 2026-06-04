# Maintenance — agent guide

> Companion to [`README.md`](README.md). What agents need to know when
> touching the long-horizon viability guides.

## Purpose

`docs/maintenance/` documents how to keep the template's *architectural
invariants* (thin orchestrator, two-layer, no-mocks, deterministic seeds,
confidentiality enforcement) intact across the inevitable churn of its
*concrete bindings* (uv, ruff, mypy, Ollama, gemma3:4b, GitHub Actions,
LaTeX). These docs are decade-scale planning, not day-of operations.

## Files in this directory

| File | Topic |
| --- | --- |
| [`README.md`](README.md) | Reader entrypoint + index |
| [`toolchain-migration.md`](toolchain-migration.md) | How to swap uv/ruff/mypy without rewriting the repo |
| [`regression-testing.md`](regression-testing.md) | Pinned numerical outputs for figures/tables — binds science to code |
| [`archival-targets.md`](archival-targets.md) | IPFS + Software Heritage parallel pins for DOI/Zenodo independence |
| [`ci-local.md`](ci-local.md) | Local reproduction of GH Actions via `act` |
| [`stage-10-executable-bundle.md`](stage-10-executable-bundle.md) | Container + lockfile + agent-runnable manifest design |
| [`private-projects-repo.md`](private-projects-repo.md) | Sibling private repo lifecycle + symlink-sync contract |
| [`local-only-template-exemplars.md`](local-only-template-exemplars.md) | LOCAL_ONLY_TEMPLATE_NAMES and promoting an exemplar to the public set |

## When to edit

- **Yes:** the documented migration path is wrong; a new threat horizon
  changes the priority order; a referenced tool changes its interface.
- **No:** routine tool-version bumps (those go in `pyproject.toml`,
  `.github/workflows/`, or release notes — not these guides).

## When NOT to delete

These guides intentionally document state that *does not yet exist on disk*
(Stage 10 bundle, archival mirrors, swap paths). Deleting them because
"not implemented yet" defeats the purpose — they exist precisely to keep
the decade-scale plan visible.

## Related

- [`../../MAINTAINERS.md`](../../MAINTAINERS.md) — subsystem owners
- [`../../STATUS.md`](../../STATUS.md) — per-subsystem heartbeat
- [`private-projects-repo.md`](private-projects-repo.md) — implemented sibling private repo + lifecycle-link mechanism
- [`../../AGENTS.md`](../../AGENTS.md) — full system manual
