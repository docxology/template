# setup-acceptance-documents contract

This composite action only orchestrates preparation of official document prerequisites.
Do not call it on a shared workstation. It uses fresh `RUNNER_TEMP` storage
and the disposable hosted runner's user font/tool directories. Third-party
archives and model blobs must retain their exact source-pinned hashes and lengths.

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

Cache only official archives, with OS, architecture, validated mode and source
identity in the key. Validate exact length and SHA-256 again before every use;
cached data cannot supply test outcomes or acceptance.

Run `actionlint` after edits and retain genuine failed preparation diagnostics.
See [README.md](README.md) for usage.

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
