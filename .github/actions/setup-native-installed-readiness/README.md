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
It verifies that both formal exemplars declare Lean 4.35.0 and prepares that
compiler through the existing hash-pinned elan bootstrap before full-suite replay.
The preceding source-fixture action supplies the authenticated TLC input.
The EPUBCheck reader uses the exact Temurin 21.0.12.1+1 Linux x64 JRE from the
SHA-pinned official Java setup action, with a fresh vendor download rather than
a preinstalled runtime selection. It nominates `JAVA_HOME/bin/java`, checks
Java and EPUBCheck, and binds their complete confined trees before the cold clock.
This self-contained runtime avoids distribution-managed links that escape a
system-installed Java tree and prevents PATH from selecting another JDK. The strict engine binder still rejects escaping links;
no runtime configuration, security file or bundle dependency is omitted.
Browser math inputs are prepared or independently inspected as Source DATA.
Temporary cache-warming environments contain only Root-locked dependencies;
independent project locks are preserved.
The documentation setup installs the Source-declared npm serializer. Native
preparation checks every installed hidden-lock row against the unchanged
committed lock before provisioning the remaining tools. The actual native
operation repeats its own full dependency, byte and custody admission.

The cold launcher subsequently builds and freezes all 25 project wheels plus the
4.0.1 SDK, selects a fresh installed runtime and independently admits actual
providers. Tool preparation or cached bytes alone establish no native or release
acceptance. Failures block the calling job.

See [AGENTS.md](AGENTS.md), the
[acceptance workflow](../../workflows/platform-required-acceptance.yml), and the
[cold launcher](../../../infrastructure/reporting/native_installed_launcher.py).
