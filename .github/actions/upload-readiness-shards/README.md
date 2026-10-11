# Bounded readiness transport upload

Uploads the exact checked index and deterministic shards retained by an owned
producer. Call after checkout and Python/uv environment setup. The action uses
the existing pinned upload-artifact action and the Source-owned
[transport checker](../../../infrastructure/reporting/native_workflow_transport.py).
Upload success establishes byte transport; authenticated producer and independent
reader admission remain required.

| Input | Contract |
| --- | --- |
| `repo-root` | Actual owned producer mirror containing retained logical bytes. |
| `directory` | Exact confined transport directory under that mirror. |
| `kind` | `native`, `candidate`, `failed-native`, `failed-reader` or `failed-handoff`. |

The checker binds the index to the exact repository, run and revision, verifies
all shard/member bytes and emits the primary name, shard count and prefixes.
One primary upload and at most 256 conditional ordinal uploads preserve the
64 MiB file/archive bounds, 8 MiB chunks, 32 MiB decoded inner shards, 200000-file
census and 8 GiB target limit. Missing or changed bytes refuse upload.

Native originals use `required-source-native-index` and
`required-source-native-shard-NNNN`. Complete candidates use
`platform-required-acceptance` and `platform-required-acceptance-shard-NNNN`.
Failure indexes and shards have separate `required-source-*-failure-*` names and
schema; they cannot satisfy native or candidate acceptance. The failed-handoff
kind is available to a caller but the release workflow has no separate uploader
for it.

See [AGENTS.md](AGENTS.md) and the
[acceptance workflow](../../workflows/platform-required-acceptance.yml).
