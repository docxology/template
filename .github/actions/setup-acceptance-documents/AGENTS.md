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
preparation explicitly includes `texlive-plain-generic` for the actual `soul.sty`
provider. After platform package preparation, require successful `kpsewhich
soul.sty` resolution and an actual provider file; retain its path and SHA-256.
A package inventory or cached archive cannot replace that runtime lookup.

The Linux mirror guard accepts only the exact 144-byte runner mirror list or
its already preferred form, with the archive/Azure priorities exchanged. Require
root-owned, non-symlink regular files and an active signed Ubuntu Noble stanza
using that mirror list; retain bounded before/after logs. Replace only the known
mirror file atomically, preserving owner and mode. Keep all three URLs, fallbacks,
repository signatures, keyrings, packages and execution limits unchanged. Refuse
unknown or changing files/stanzas; do not rewrite other APT configuration.
