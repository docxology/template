# Acceptance source fixtures

Materializes identical prerequisite bytes on every isolated hosted producer,
collector and release reader. Call after checkout, including the pinned submodule,
and before any acceptance source snapshot. The stdlib producer works with the
preinstalled Python before environment setup. Its committed
[`acceptance-source-fixtures.json`](../../../infrastructure/config/acceptance-source-fixtures.json)
is the shared declaration for preparation and Source admission: exact official
archive identities, library/license member bytes and directories, plus runtime
destinations copied from actual committed synthetic seeds. Existing targets,
symlink ancestors, corrupt archives and unexpected selected members refuse
preparation. Source readers retain these bodies in their full source inventory
and independently authenticate each binding; preparation cannot grant acceptance.

The official TLC jar uses the single literal `TLC_URL`/`TLC_BYTES`/`TLC_SHA256`
tuple in [`template_formal.tool_acceptance`](../../../projects/templates/template_formal/src/template_formal/tool_acceptance.py).
This action and the optional hardening preparation read and validate those
top-level literals with preinstalled `python3 -S` and stdlib `ast`; they do not
import the project or SDK. Invalid, missing, duplicate or dynamic pins stop the
shell before acquisition. Both preparation routes authenticate the complete
selected size and SHA-256 before exporting `TEMPLATE_FORMAL_TLC_JAR` from owned
external storage. Tool bytes are not authored source.

The current tuple was independently matched to official asset 635357747 on
2026-10-13 UTC: 4,501,961 bytes from commit
`5737c4758703f9fc4ef4ce1ff5dd912fe37d78d3`, identified by its manifest as TLC 2.0
(2026-10-13). The `v1.8.0` URL is a mutable locator; a replacement must fail the
exact byte guards until its full binding and genuine model controls are reviewed.
The genuine committed time-series seed is copied without host-dependent numerical
regeneration. Preparation failure blocks the observation. The legacy shallow-clone
downloader is a local exploration tool; its mutable HEAD and `.git` metadata do
not satisfy this fixed fixture contract.

See [AGENTS.md](AGENTS.md) and the [seed fixture](../../../tests/fixtures/timeseries_seed/README.md).
