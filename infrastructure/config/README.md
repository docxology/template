## `infrastructure/config/`

Repo-scoped **non-Python** configuration assets (templates, defaults). This directory intentionally contains **no Python code** — the Python configuration loaders live in [`infrastructure/core/config/`](../core/config/) (`loader.py`, `schema.py`, `formatting.py`, `queries.py`, `cli.py`).

If you are looking for `from infrastructure.config import ...`, you want `infrastructure.core.config` instead.

### Files

- **`.env.template`**: Example environment variables to copy into your own `.env` (do not commit secrets).
- **`secure_config.yaml`**: Default secure pipeline configuration (steganography/hashing/encryption).

### See also

- **Python config loaders**: [`infrastructure/core/config/`](../core/config/)
- **Configuration docs**: [`docs/operational/config/configuration.md`](../../docs/operational/config/configuration.md)
