# Operations Documentation Overview

This directory contains runbooks, maintenance procedures, configuration tools, and Docker guides for operating the Research Project Template infrastructure.

## Scope

- **Deployment** — Docker-based containerization and local development setup
- **Configuration** — Documented setup steps for environment validation (there is no separate interactive wizard CLI; see [`config-wizard.md`](config-wizard.md))
- **Maintenance** — Log rotation, dependency updates, backup strategies
- **Incident Response** — Runbook for daily, weekly, and monthly operational tasks

## Audience

- **Operations engineers** — Responsible for uptime and maintenance
- **Developers** — Setting up development environment and troubleshooting
- **CI/CD administrators** — Managing build and release pipelines

## How to Use

1. **First-time setup** → Read [`config-wizard.md`](config-wizard.md)
2. **Production deployment** → Follow [`docker.md`](docker.md)
3. **Routine maintenance** → Schedule tasks from [`maintenance.md`](maintenance.md)
4. **Incident response** → Consult [`runbook.md`](runbook.md)

## Related Documentation

- [`AGENTS.md`](AGENTS.md) — In-depth operational guide structure and mermaid diagrams
- [`../RUN_GUIDE.md`](../RUN_GUIDE.md) — Pipeline commands and stages
- [`../reference/`](../reference/) — Quick reference and FAQ
- [`../documentation-index.md`](../documentation-index.md) — Complete documentation index

## Contributing

When adding new operational procedures, update the relevant guide and add cross-references in [`README.md`](README.md) and this overview to keep navigation consistent.
