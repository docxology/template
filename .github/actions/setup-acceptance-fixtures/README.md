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

The official TLC jar is authenticated by its source-owned hash and selected from
owned external storage through `TEMPLATE_FORMAL_TLC_JAR`; it is not authored source.
The genuine committed time-series seed is copied without host-dependent numerical
regeneration. Preparation failure blocks the observation. The legacy shallow-clone
downloader is a local exploration tool; its mutable HEAD and `.git` metadata do
not satisfy this fixed fixture contract.

See [AGENTS.md](AGENTS.md) and the [seed fixture](../../../tests/fixtures/timeseries_seed/README.md).
