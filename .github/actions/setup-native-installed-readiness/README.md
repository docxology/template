# Installed native readiness preparation

This hosted Ubuntu composite prepares the Source-declared tools and dependency
cache used by the installed original, independent reader and release handoff.
Call after a full checkout and source-fixture preparation. The caller provisions
`uv` and Python 3.14.4 first through the existing
[Python setup](../setup-python-env/README.md). Use this action in an owned hosted
workspace, before the cold operation starts its unchanged 14400-second budget.

The action warms locked Root development, wheel-build and native rendering
dependencies, reuses the existing Node/Mermaid/Chrome and document-tool actions,
and prepares LibreOffice, Calibre, Java, zbar and the Source-pinned EPUBCheck.
Browser math inputs are prepared or independently inspected as Source DATA.
Temporary cache-warming environments contain only Root-locked dependencies;
independent project locks are preserved.

The cold launcher subsequently builds and freezes all 25 project wheels plus the
4.0.1 SDK, selects a fresh installed runtime and independently admits actual
providers. Tool preparation or cached bytes alone establish no native or release
acceptance. Failures block the calling job.

See [AGENTS.md](AGENTS.md), the
[acceptance workflow](../../workflows/platform-required-acceptance.yml), and the
[cold launcher](../../../infrastructure/reporting/native_installed_launcher.py).
