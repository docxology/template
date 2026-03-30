# AGENTS: `security/` — Security & Provenance Documentation

Technical specification for the security documentation directory.

## File Inventory

| File | Purpose |
|------|---------|
| `README.md` | Overview with navigation links |
| `steganography.md` | Alpha-channel watermarking and QR code injection |
| `hashing_and_manifests.md` | SHA-256/512 hashing and manifest generation |
| `secure_execution.md` | `secure_run.sh` orchestration and threat model |

## Key Concepts

- **Four steganographic layers**: PDF metadata, cryptographic hash, alpha-channel overlay, QR code
- **Tamper detection**: SHA-256 comparison against stored manifest hashes
- **Threat model**: Unauthorized redistribution, content tampering, provenance forgery

## See Also

- [_generated/active_projects.md](../_generated/active_projects.md) — Active `projects/` names (steganography runs per discovery)
- [guides/new-project-setup.md](../guides/new-project-setup.md) — How security integrates with pipeline
- [Root AGENTS.md](../../AGENTS.md) — System-level documentation
