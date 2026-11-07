# setup-acceptance-documents

Prepares official document prerequisites on the isolated GitHub-hosted acceptance runner.
Call after checkout and the caller's locked Python dependency sync. The `mode` input accepts exactly `native`
(the default) or `converter` and is validated before cache restoration or setup.
Both modes prepare exact pinned Pandoc and crossref. Native mode additionally
prepares TeX, native readers and JuliaMono; full acceptance retains this default.
Routine infrastructure smoke selects converter and prepares its declared readers
and TeX separately. Ordinary project tests request native mode for EDA
and converter mode for the other capability-matrix cells.

On Linux, the existing Pandoc step in both modes uses the caller's prepared
Python, after archive verification, to validate the
signed Ubuntu mirror source and prefer its existing official HTTPS archive.
Only the recognized mirror-list priorities change; URLs, fallback mirrors,
package trust, package selection and execution limits remain unchanged.
Unexpected files or source declarations stop preparation. This changes the
preferred transport route; its effect on transfer time requires actual execution.

Fixed release archives are admitted by
exact byte length and SHA-256 before extraction or execution. Preparation
failures block the observation; they cannot certify an acceptance gate.

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
common acceptance job selects `output/runtime-envs/3.14/bin/python`. A missing
interpreter or validator failure stops setup. The action does not bootstrap,
sync or reconcile Python, so each caller keeps its selected dependency groups;
 cached package files cannot replace actual
package installation, archive verification, or executable probes.

Only the official Pandoc, crossref, JuliaMono, frozen TeX installer and database archives are cached under
`RUNNER_TEMP`, keyed by operating system, architecture, validated mode and the
action's declared source hash. Every restored or freshly downloaded archive must pass its exact
byte-length and SHA-256 checks before extraction or executable probes. Corruption
blocks preparation; a cache hit never supplies an acceptance result. Extracted
tools, TeX trees, fonts, environments and test results are not cached here.

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
