# setup-acceptance-documents contract

This composite action orchestrates Source-pinned document prerequisites.
Do not call it on a shared workstation. It uses fresh `RUNNER_TEMP` storage
and the disposable hosted runner's user font/tool directories. Official assets
retain exact Source-pinned compressed hashes and lengths; Linux document builds
retain exact Source-pinned executable bodies and immutable compiler/dependency inputs.

The model action binds an unoccupied loopback port, disables cloud operations
and implicit model acquisition, and records its owned daemon PID and birth.
Every caller of that action must perform identity-checked process-group cleanup
in an `always()` step. No shared service may be stopped or replaced.

`mode` defaults to `native`. Validate exactly `native` or `converter` before
cache restoration, download or setup. Pandoc/crossref verification is
unconditional; native package and JuliaMono preparation are conditioned only on
that validated output. Genuine acceptance callers use native preparation;
routine infrastructure smoke selects converter and separately prepares its
declared readers and TeX. Ordinary project cells explicitly select native for EDA and
converter elsewhere, according to their actual source-declared tests.

Cache only complete document/font/TeX archives, with OS, architecture, validated
mode, manifest and preparation source identities in the key. macOS document
archives retain exact official compressed length/SHA-256 pins. Linux archives
contain one unchanged executable member whose complete body must equal the
Source manifest's binary length/SHA-256; compression and worker JSON are not
authenticity. Validate bounded physical archives and members before every use.
Cached data cannot supply test outcomes or acceptance.

Run `actionlint` after edits and retain genuine failed preparation diagnostics.
See [README.md](README.md) for usage.

The single pin source is `infrastructure/config/native-document-providers.json`,
interpreted by the pure closed-union `native_document_provider_contracts` API.
Do not duplicate platform archive pins in shell. Linux x86_64 uses the held,
hash-pinned Root recipe, complete freeze and tracked compiler patch against the
immutable upstream commit and haskell.nix/Hackage lock. The v3 closed manifest
authenticates all three held inputs before acquisition or build. Root retains
GHC 9.12.2 and project-wide `-fobject-determinism`; its real rebuilt `ghc-pkg`
canonicalizes package-cache serialization by installed unit ID. Keep the
standard compiler dependency metadata, `ghc.package` binding and both executable
`keepConfigFiles` settings from the qualified recipe. Do not sort linker flags,
rewrite cache bytes or substitute a fake command. Upstream's GHC 9.8.4 declaration
and original freeze remain separately authenticated, not rewritten.
`native_document_preparation` evaluates private copies of the held inputs and
checks actual source NAR, compiler/plan/provider paths, recursive derivations,
resolved freeze, completed build and verified runtime closure.
Resolve Nix symlinks to actual executable bodies; match the whole Source pin and
use the shared `native_document_elf.require_glibc_executable` eligibility check.
Never patch a binary to create loader observations, substitute a wrapper,
downgrade a version, or admit the static official Linux release.

If Nix is absent, use the reviewed Ubuntu mirror guard and bounded signed Noble
`nix-bin`/`nix-setup-systemd` packages, not an unpinned remote installer. Initialize
the local store; sudo preparation does not depend on systemd daemon/socket startup.
Keep signature verification and only the reviewed NixOS, IOG and crossref Cachix
caches without flake-supplied settings. Retain the Nix output GC root in a
separate private runtime directory, never inside the public tool asset tree:
the isolated execution profile must keep refusing escaping links. Retain the
full installed runtime closure, not just copies of the two binaries.
Preparation command/derivation/body records explicitly grant no native authority;
Original/Current Source, full body correspondence and every existing native
loader/map/memory/lifecycle/readback requirement remain mandatory.

Linux callers in either mode, and all native callers, must first prepare their selected locked Python environment.
`python-executable` defaults to `.venv/bin/python`; common acceptance explicitly
selects its prepared `output/runtime-envs/3.14/bin/python`. The helper's
`--prepared-python PATH` mode preserves that environment, checks actual CPython
support, and runs the unchanged LaTeX package validator with it. It performs no
Python bootstrap, dependency sync or implicit reconciliation. Missing runtime,
native tools, packages or failed validation remain failures. Linux native
preparation selects the upstream plain-generic collection for the actual `soul.sty`
provider. After platform package preparation, require successful `kpsewhich
soul.sty` resolution and an actual provider file; retain its path and SHA-256.
A package inventory or cached archive cannot replace that runtime lookup.

The Linux mirror guard uses the action-owned `ubuntu_apt_mirrors.py` policy.
Admit only its exact original three-row ASCII serialization or the corresponding
extended form: Azure or a reviewed standard commercial EC2 regional Ubuntu host,
followed by the fixed HTTPS archive and security rows, then lower-priority
reviewed `us-east-1`, `us-west-2` and `eu-west-1` EC2 fallbacks not duplicating
the current primary. The finite region set is source reviewed; unknown regions,
URLs, paths, whitespace, extra rows and priority arrangements are refused. Allow
only original or already preferred archive/primary priorities and derive the
maximum read size from all accepted original and extended byte forms. Do not
infer a hosted file's complete bytes or hash from its size or selected hostname.

Require root-owned, non-symlink regular files and an active signed Ubuntu Noble
stanza using that mirror list; retain bounded before/after logs. Replace only the
known mirror file atomically, preserving owner and mode. Keep the three primary
URLs, repository signatures, keyrings, packages and execution limits unchanged;
append only the reviewed regional fallbacks. Refuse unknown or changing
files/stanzas; do not rewrite other APT configuration. Run permanent byte-policy
tests without host APT access and use a separate disposable Linux root-file
control for filesystem behavior.
Native reader/font APT commands and CI's routine/contract APT consumers retain
the same one-retry, 20-second HTTP/HTTPS connection/idle bounds, allowing the
reviewed mirror fallbacks to run without extending the owning job deadline.

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
