# Gate Scripts

Pipeline gate scripts for template.

## Gates

- `gate_cache` — Validates and populates the cache
- `security_scan` — Runs security scanning (bandit, safety, pip-audit)
- `plugin_export_check` — Verifies plugin exports

## Running

```bash
# Run all gates
./run.sh gates

# Dry-run (skip actual changes)
./run.sh gates --dry-run
```
