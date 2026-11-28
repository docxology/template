# Publishing Scripts — Agent Guide

This document describes how autonomous agents (Hermes, CI/CD systems) should interact with the `scripts/publish/` tooling.

## Purpose

These scripts coordinate manuscript distribution, local package checks, and
explicit sandbox publication. Prepare the locked environment for the selected
operation and keep publication credentials in the process environment.
[Publishing commands](README.md#pypi-package-checks)

## Scripts

### sync_standalone_mirrors.py

Dry-run standalone synchronization uses exact canonical source exports by
default. `--install-projection` explicitly enables versioned Git provider pins;
Advanced additionally requires a prepared canonical `--meta-provider` checkout
and its existing full `--meta-commit`. Both options must be supplied together.
`--commit` authorizes the actual commit/push path; existing destination,
source-removal review, retained evidence, and source custody gates still apply.
Local projection admission is separate from public provider retrieval and
isolated installation acceptance. See
[`standalone-install-projection.md`](../../docs/guides/standalone-install-projection.md).

### Local package preview

Use `PyPIAdapter.publish(..., dry_run=True)` with an empty credential environment.
The command returns original wheel and source distribution digests from a
private build. Use this path for local verification and credential-free CI.
[Local build preview](README.md#local-build-preview)

### test_pypi.py

This command makes an actual TestPyPI transfer. Require explicit approval for
that operation and supply `TEST_PYPI_API_TOKEN` through the process environment.
The CLI checks prepared tools, admits the build, retrieves the exact published
bytes, and performs isolated installed verification. Use the separately
reviewed release contract for production promotion.
[TestPyPI sandbox transfer](README.md#testpypi-sandbox-transfer)

### verify_install.py

Supply the retained wheel and its original admission digest through `--wheel`
and `--sha256`. Keep the prepared locked dependencies for its offline installed
verification. The result describes that wheel and runtime.
[Exact wheel installation check](README.md#exact-wheel-installation-check)

## File Locations

- `infrastructure/publishing/pypi_release.py` — TestPyPI build/upload helpers (imported by script below)
- [`test_pypi.py`](test_pypi.py) — explicit TestPyPI transfer and installed verification
- [`verify_install.py`](verify_install.py) — offline verification of an admitted wheel
- `scripts/publish/README.md` — Human-readable usage guide

## Related

- Root-level `AGENTS.md` — Repository-wide agent conventions
- `pyproject.toml` — Package metadata, optional dependencies, and extras definition
- `README.md` — Public-facing installation and usage documentation
