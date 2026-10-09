# Readiness shard upload contract

[README.md](README.md) defines the three explicit inputs and supported transport
roles. The action runs the Source-owned DATA checker before invoking the existing
pinned upload-artifact action. It does not construct a Source context, runtime
provider grant or completed-original capability from an index.

Keep every ordinal shard path and conditional count aligned with the bounded
checker. Preserve all per-file/archive, decoded-byte, shard, member and whole
transport caps. Do not fall back to a first-page artifact census, overwrite a
conflicting index or infer acceptance from successful upload. Independent
collectors authenticate exact hosted producer, run, revision, artifact IDs,
digests, sizes and full bounded pagination before using retained bytes.

Keep failed evidence separately named and retain the genuine signed process
failure. The failure schema and role may never substitute for a native acceptance
index or complete candidate handoff. The original operation deadline is not
reset by diagnostic packing or upload.

Maintain the [parent action contract](../AGENTS.md), this doc pair and resolving
links. Action pins, caller permissions and Source acceptance predicates stay
under their existing contracts; run actionlint after action edits.
