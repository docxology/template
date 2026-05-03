# Logrotate Configuration

> Log rotation configs for pipeline and agent logs

**Quick Reference:** [template](template) | [Rotation Script](../../docs/operations/scripts/rotate-logs.sh)

## Contents

| File | Description |
|------|-------------|
| [`template`](template) | Logrotate rules for `~/.template/logs/*.log` |

## Installation (Optional)

```bash
# System-wide install
sudo cp infrastructure/logrotate.d/template /etc/logrotate.d/

# Test (dry-run)
logrotate -d /etc/logrotate.d/template
```

## See Also

- [Maintenance Procedures](../../docs/operations/maintenance.md) — Full maintenance docs
- [Rotation Script](../../docs/operations/scripts/rotate-logs.sh) — Manual log rotation
