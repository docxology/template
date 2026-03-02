# Operational Documentation

## Overview

Technical guide for `docs/operational/` — operational procedures, build configuration, logging, troubleshooting, and system maintenance.

## Directory Structure

```
docs/operational/
├── AGENTS.md                       # This guide
├── README.md                       # Quick reference
├── reporting-guide.md              # Reporting system guide
├── error-handling-guide.md         # Error handling patterns
├── build/                          # Build pipeline & CI/CD
│   ├── build-system.md
│   ├── build-history.md
│   ├── ci-cd-integration.md
│   └── dependency-management.md
├── config/                         # Configuration & performance
│   ├── configuration.md
│   ├── checkpoint-resume.md
│   └── performance-optimization.md
├── logging/                        # Logging system guides
│   ├── README.md (comprehensive guide)
│   ├── python-logging.md
│   ├── bash-logging.md
│   └── logging-patterns.md
└── troubleshooting/                # Troubleshooting guides
    ├── README.md (flowchart + systematic approach)
    ├── common-errors.md
    ├── build-tools.md
    ├── test-failures.md
    ├── environment-setup.md
    ├── recovery-procedures.md
    └── llm-review.md
```

## Key Conventions

- **Build files** → `build/` sub-folder (pipeline, CI/CD, deps)
- **Config files** → `config/` sub-folder (settings, checkpoints, perf)
- **Logging** → `logging/README.md` is the comprehensive entry point
- **Troubleshooting** → `troubleshooting/README.md` has the diagnostic flowchart
- All guides include cross-references to related documentation

## Quick Commands

```bash
# Full pipeline
uv run python scripts/execute_pipeline.py --core-only

# Individual stages
uv run python scripts/00_setup_environment.py
uv run python scripts/01_run_tests.py
uv run python scripts/03_render_pdf.py

# Debug with verbose logging
LOG_LEVEL=0 uv run python scripts/03_render_pdf.py
```

## See Also

- [README.md](README.md) — Quick navigation
- [docs/AGENTS.md](../AGENTS.md) — System-wide documentation guide
- [documentation-index.md](../documentation-index.md) — Full index
