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
Pandoc/crossref, XeLaTeX, BibTeX, `pdftoppm`, and `pdffonts` executables. Call it
once per job before document tests; native mode runs the unchanged LaTeX
package validator with `python-executable` (default `.venv/bin/python`). The
common acceptance job selects `output/runtime-envs/3.14/bin/python`. A missing
interpreter or validator failure stops setup. The action does not bootstrap,
sync or reconcile Python, so each caller keeps its selected dependency groups;
 cached package files cannot replace actual
package installation, archive verification, or executable probes.

Only the official Pandoc, crossref and JuliaMono archives are cached under
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
