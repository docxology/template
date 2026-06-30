# Plans Documentation

## Overview

Technical guide for `docs/plans/` — repo-wide planning documents and phased correction directives.

## Current status

This directory is **intentionally empty**. Per-project plans live under `projects/{name}/docs/` (active) or `projects/archive/{name}/docs/` (historical). Historical repo-wide audit snapshots were retired from the public docs archive; use git history for dated point-in-time reports.

A project-specific review that previously lived here was relocated to its own (private) project repository during the May 2026 hardening pass.

## Key Conventions

- Drop new repo-wide plans here as `<topic>.md` with a date header.
- Project-specific plans belong under `projects/{name}/docs/`, not this directory.
- Once executed, move plans to the project tree or archive; do not leave completed work here.
- Active `projects/` names → [_generated/active_projects.md](../_generated/active_projects.md).

## See Also

- [README.md](README.md) — Quick navigation
- [../architecture/](../architecture/) — Architecture and ADRs
- [../guides/new-project-setup.md](../guides/new-project-setup.md) — New project setup checklist
- [../_generated/active_projects.md](../_generated/active_projects.md) — Current rendered public project roster
