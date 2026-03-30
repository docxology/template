---
name: infrastructure-config
description: Repository-scoped configuration for the template—environment variable templates and default secure/steganography YAML. Use when editing .env patterns, secure_config defaults, or cross-referencing project manuscript config overrides.
---

# Skill Descriptor — infrastructure/config

## Module Overview

Repo-scoped configuration defaults used by infrastructure modules.

## Capabilities

- **Environment template management**: `.env.template` provides non-secret example variables
- **Secure configuration**: `secure_config.yaml` defines default steganography/hashing/encryption settings

## Use Cases

1. **Loading repo configuration**: Use `infrastructure.core.config.loader` to read config values
2. **Secure pipeline defaults**: Reference `secure_config.yaml` for steganography settings
3. **Environment setup**: Copy `.env.template` to `.env` and fill in values

## Integration Points

- Referenced by `infrastructure/core/config_loader.py`
- Project-level overrides in `projects/{name}/manuscript/config.yaml`

## See Also

- [`docs/operational/config/configuration.md`](../../docs/operational/config/configuration.md)