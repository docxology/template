# Installed native readiness preparation

This hosted Ubuntu composite prepares the Source-declared tools and dependency
cache used by the installed original, independent reader and release handoff.
Call after a full checkout and source-fixture preparation. The caller provisions
`uv` and Python 3.14.4 first through the existing
[Python setup](../setup-python-env/README.md). Use this action in an owned hosted
workspace, before the cold operation starts. Complete native roles retain their
14400-second budget; the incomplete Code diagnostic retains its bounded
1800-second budget. Preparation does not establish that either operation will
finish.

The action warms locked Root development, wheel-build and native rendering
dependencies, reuses the existing Node/Mermaid/Chrome and document-tool actions,
and prepares LibreOffice, Calibre, Java, zbar and the Source-pinned EPUBCheck.
By default, it verifies that both formal exemplars declare Lean 4.35.0 and
prepares that compiler through the existing hash-pinned elan bootstrap before
full-suite replay. The validated `prepare-lean: 'false'` input is used only by
the Code diagnostic, whose enabled formats do not exercise Lean.
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
The documentation setup selects Node 24.22.0 LTS and installs the
Source-declared npm serializer. The current native Mermaid11 profile requires
actual Node 24 in both original version proofs and live loaded-library reports;
earlier Node 20 proofs cannot qualify this profile. Native
preparation checks every installed hidden-lock row against the unchanged
committed lock before provisioning the remaining tools. The actual native
operation repeats its own full dependency, byte and custody admission.

Complete original, reader and handoff roles subsequently build and freeze all
public project wheels plus the Source-declared SDK. The bounded Code diagnostic
builds its selected project and actual local providers plus the SDK. Each selects
a fresh installed runtime and independently admits actual providers. Tool preparation or cached bytes alone establish no native or release
acceptance. Failures block the calling job.

See [AGENTS.md](AGENTS.md), the
[acceptance workflow](../../workflows/platform-required-acceptance.yml), and the
[cold launcher](../../../infrastructure/reporting/native_installed_launcher.py).
