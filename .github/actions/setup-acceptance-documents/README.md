# setup-acceptance-documents

Prepares Source-pinned document prerequisites on an isolated GitHub-hosted runner.
Call after checkout and the caller's locked Python dependency sync. The `mode`
input accepts exactly `native` (the default) or `converter`, validated before
cache restoration or setup. Both modes prepare Pandoc 3.11 and crossref v0.3.25a
with their unchanged JSON API. Native mode additionally prepares TeX, native
readers and JuliaMono. Routine infrastructure smoke selects converter and
prepares its declared readers and TeX separately; ordinary project tests request
native for EDA and converter for the other capability-matrix cells.

[`infrastructure/config/native-document-providers.json`](../../../infrastructure/config/native-document-providers.json)
is the single pin source. macOS retains the exact official release archives,
lengths, SHA-256 digests and selected executable members. Linux x86_64 builds
the upstream
[`pandoc-with-crossref` flake at the immutable reviewed commit](https://github.com/lierdakil/pandoc-crossref/tree/e6c2ae3418dcf63f974802f8b7c105ebc299706c):
its locked haskell.nix/Hackage inputs, GHC 9.8.4 and complete Cabal freeze select
the compiler and dependencies, never an unpinned host GHC or latest package set.
The strict shared parser rejects unsupported hosts and malformed fields in any
manifest branch; there is no official-static-Linux or version fallback.

Linux first uses the caller's prepared Python to validate the signed Ubuntu
mirror source and prefer its reviewed official HTTPS archive. Only recognized
mirror-list priorities change; URLs, fallback mirrors, package trust and bounded
APT attempts remain unchanged. If Nix is absent, the action installs Ubuntu
Noble's signed `nix-bin` and `nix-setup-systemd` packages, not a remote shell
installer. Noninteractive sudo uses an initialized local store and isolated build
users on this disposable runner; no systemd daemon/socket startup is required.
Only the reviewed signed NixOS, IOG and crossref Cachix caches are selected;
flake-supplied configuration and the optional undo.it cache are not accepted.

The Source preparation CLI checks the actual source revision and complete NAR,
lock/freeze byte digests, compiler declaration, evaluated derivation and output,
recursive compiler/dependency derivations, completed build and verified runtime
closure. Each actual executable must match its Source-declared whole-body
SHA-256 and length and have a real installed glibc ELF `PT_INTERP`; no binary
instrumentation or wrapper is substituted. Canonical single-member `tar.xz`
archives retain those unchanged binaries. Compression bytes and build JSON are
transport/provenance, not authenticity: the pinned executable body is authoritative.
The Nix output GC root and full runtime closure remain installed for execution.
Preparation failures block observation and never certify an acceptance gate.

In native mode, the action prepares pinned Pandoc and crossref before the shared system-dependency
audit, then installs the complete Linux TeX/reader package union in one step or
prepares BasicTeX and native readers on macOS. Both platforms probe the selected
Pandoc/crossref, XeLaTeX, BibTeX, `pdftoppm`, and `pdffonts` executables. Linux
selects the upstream plain-generic collection, which supplies `soul.sty` for the
selected Pandoc highlighting preamble. Both platforms resolve `soul.sty` with
`kpsewhich`, require its actual file, and record its provider path and SHA-256
before document tests. Call it
once per job before document tests; native mode runs the unchanged LaTeX
package validator with `python-executable` (default `.venv/bin/python`). The
common acceptance job selects `output/runtime-envs/3.14/bin/python`. Every Linux
caller and every native caller must provide this already locked executable.
Only converter-only macOS may use its already installed stdlib `python3` when
that executable is absent. No route bootstraps, syncs or reconciles Python.
A missing required interpreter or validator failure stops setup.

The archive cache contains only the official macOS document, JuliaMono and
frozen TeX archives, plus the complete Source-built Linux document archives.
Its key binds OS, architecture, validated mode, manifest and preparation sources.
Every reuse checks complete bounded physical archive bytes and its selected
member: official archives retain their exact compressed SHA-256/length; Linux
members must equal the exact Source binary pins. Corruption blocks preparation.
Extracted tools, runtime Nix closure, TeX trees, fonts, environments, build
receipts and test outcomes are not cached as acceptance results.

`native_document_preparation` retains command stdout/signed exits, frozen
inputs, recursive derivations, runtime closure and actual selected/prepared
paths in the fresh preparation directory. Its
`document-provider-provenance.json` is explicitly preparation-only with
`runtime_acceptance: false`; native TeX provenance includes that record.
Neither provenance nor a cache hit replaces the genuine Original/Current
process, archive/body, loader, map, memory, lifecycle and readback admissions.

Converter preparation supports the ordinary tests that require Pandoc and
crossref; it cannot provide evidence for native-format acceptance. No test,
coverage threshold or required acceptance gate is removed. The effect on runtime
and hosted cost must be measured after genuine execution.

See [AGENTS.md](AGENTS.md) for ownership and cleanup requirements.

## Frozen Linux TeX and tagged-PDF capability

Native Linux preparation installs one upstream TeX Live 2025 final tree from
the [official historical repository](https://www.tug.org/texlive/acquire.html#past).
The installer dated 2026-03-01 and repository database retain exact Source-pinned
lengths and SHA-256 digests. The installer verifies its package downloads from
that frozen repository; a closing database hash check rejects repository drift.
The selected basic, LaTeX, LuaTeX, XeTeX, scientific, bibliography, recommended
font and plain-generic collections replace the former Debian TeX package union.
Documentation and package sources are excluded, and installation has a 2,400-second
bound with 30 seconds for termination. All TeX executables select that same tree
on PATH. Converter mode and the prepared Python environment remain unchanged.

This coherent snapshot includes the LaTeX tagging interface documented by the
[LaTeX project](https://www.latex-project.org/publications/2025-UFi-FMi-TUB-tb143fischer-tagging25.pdf).
Do not transplant current packages into the older Debian engine or substitute
a mutable current CTAN repository. A selected version, successful installer,
package inventory or cache never establishes native capability: the real tagged
PDF test must execute and pass without skips on the exact candidate Source.

Native preparation records actual executable versions, resolved paths, hashes,
and resolved LaTeX/tagpdf/metadata provider hashes in
`$RUNNER_TEMP/template-acceptance-document-provenance.json`. The focused probe
retains that record with its original wrapper streams. Genuine setup failures,
test skips and failed original exits remain failures.
