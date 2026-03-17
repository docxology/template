## infrastructure/config/ — Repository Configuration

### Scope

Configuration files used by infrastructure components (repo-scoped defaults).

### Contents

| Path | Purpose |
| --- | --- |
| `.env.template` | Example environment variables (non-secret) |
| `secure_config.yaml` | Default secure/steganography configuration |

### Notes

- Project-level overrides typically live in `projects/{name}/manuscript/config.yaml`.
- Secrets should not be committed; use environment variables or secure stores.

### See also

- [`infrastructure/core/config_loader.py`](../core/config_loader.py)
- [`docs/operational/config/configuration.md`](../../docs/operational/config/configuration.md)
