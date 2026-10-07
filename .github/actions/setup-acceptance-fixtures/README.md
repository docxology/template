# Acceptance source fixtures

Materializes identical prerequisite bytes on every isolated hosted producer,
collector and release reader. Call after checkout, including the pinned submodule,
and before any acceptance source snapshot. Official Requests/FastAPI archives use
immutable commits, exact lengths and SHA-256; only library source and its license
are extracted. The official TLC jar is authenticated by its source-owned hash and selected from
owned external storage through `TEMPLATE_FORMAL_TLC_JAR`; it is not authored source.
The genuine committed time-series seed is copied without host-dependent numerical
regeneration. Preparation failure blocks the observation.

See [AGENTS.md](AGENTS.md) and the [seed fixture](../../../tests/fixtures/timeseries_seed/README.md).
