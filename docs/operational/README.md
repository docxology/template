# ⚙️ Operational Documentation

> Build, configuration, logging, troubleshooting, reporting, and error handling guides

**Quick Reference:** [Build System](build/build-system.md) | [Troubleshooting](troubleshooting/) | [Logging](logging/) | [Configuration](config/configuration.md)

## Directory Structure

| Sub-directory | Purpose | Key Files |
|---------------|---------|-----------|
| [`build/`](build/) | Build pipeline, CI/CD, dependencies | build-system.md, ci-cd-integration.md, dependency-management.md |
| [`config/`](config/) | Configuration, checkpoints, performance | configuration.md, checkpoint-resume.md, performance-optimization.md |
| [`logging/`](logging/) | Logging system (Python, Bash, patterns) | README.md (full guide), python-logging.md, bash-logging.md |
| [`troubleshooting/`](troubleshooting/) | Issue resolution and recovery | README.md (flowchart), common-errors.md, llm-review.md |

## Top-Level Guides

| Guide | Description |
|-------|-------------|
| [reporting-guide.md](reporting-guide.md) | Pipeline reporting system and report interpretation |
| [error-handling-guide.md](error-handling-guide.md) | Error handling patterns and custom exceptions |

## Quick Navigation

| Need | Go to |
|------|-------|
| Build pipeline details | [build/build-system.md](build/build-system.md) |
| CI/CD setup | [build/ci-cd-integration.md](build/ci-cd-integration.md) |
| Fix a build error | [troubleshooting/](troubleshooting/) |
| Configure logging | [logging/](logging/) |
| System configuration | [config/configuration.md](config/configuration.md) |
| Resume a failed pipeline | [config/checkpoint-resume.md](config/checkpoint-resume.md) |
| Optimize performance | [config/performance-optimization.md](config/performance-optimization.md) |

## See Also

- [Architecture](../core/architecture.md) — System design overview
- [Common Workflows](../reference/common-workflows.md) — Step-by-step recipes
- [FAQ](../reference/faq.md) — Common questions
