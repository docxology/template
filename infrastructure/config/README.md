## `infrastructure/config/`

Repo-scoped **non-Python** configuration assets (templates, defaults). This directory intentionally contains **no Python code** — the Python configuration loaders live in [`infrastructure/core/config/`](../core/config/) (`loader.py`, `schema.py`, `formatting.py`, `queries.py`, `cli.py`).

If you are looking for `from infrastructure.config import ...`, you want `infrastructure.core.config` instead.

### Files

- **`.env.template`**: Example environment variables to copy into your own `.env` (do not commit secrets).
- **`secure_config.yaml`**: Default secure pipeline configuration (steganography/hashing/encryption).
- **`acceptance-source-fixtures.json`**: Exact official Requests/FastAPI selected archive members and committed synthetic-seed copy mappings, shared by fixture preparation and complete Source-body admission. Downloaded bodies remain part of source identity; the manifest grants no execution or acceptance evidence.

- **`root-case-policy.json` and derived `.part-NNNN.json` files**: Bounded, lossless source representation of the complete reviewed Root policy draft. Current collection and policy admission remain required; see [Root case policy](../../docs/development/root-case-policy.md).

### See also

- **Python config loaders**: [`infrastructure/core/config/`](../core/config/)
- **Configuration docs**: [`docs/operational/config/configuration.md`](../../docs/operational/config/configuration.md)
