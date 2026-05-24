# Plans Documentation

## Overview

Technical guide for `docs/plans/` — repo-wide planning documents and phased correction directives.

## Current status

This directory is **intentionally empty**. Per-project plans live under `projects/{name}/docs/` (active) or `projects_archive/{name}/docs/` (historical). Repo-wide audit snapshots live under [`../audit/archived/`](../audit/archived/) with `-YYYY-MM-DD.md` suffixes.

The previous tenant (`act_inf_metaanalysis_v2_comprehensive_review.md`) was moved to [`../audit/archived/act_inf_metaanalysis_v2_comprehensive_review-2026-04-26.md`](../audit/archived/act_inf_metaanalysis_v2_comprehensive_review-2026-04-26.md) in the May 2026 hardening pass.

## Key Conventions

- Drop new repo-wide plans here as `<topic>.md` with a date header.
- Project-specific plans belong under `projects/{name}/docs/`, not this directory.
- Once executed, move plans to the project tree or archive; do not leave completed work here.
- Active `projects/` names → [_generated/active_projects.md](../_generated/active_projects.md).

## See Also

- [README.md](README.md) — Quick navigation
- [../architecture/](../architecture/) — Architecture and ADRs
- [../guides/new-project-setup.md](../guides/new-project-setup.md) — New project setup checklist
- [../audit/archived/](../audit/archived/) — Dated audit and review snapshots
