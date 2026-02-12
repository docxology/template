# Backup and Recovery Guide

> **Strategies and procedures** for backing up and recovering projects

**Quick Reference:** [Common Workflows](../reference/common-workflows.md) | [Troubleshooting Guide](../operational/troubleshooting-guide.md) | [Version Control](../best-practices/version-control.md)

This guide provides strategies for backing up your research projects and recovering from data loss or corruption.

## Overview

Effective backup and recovery strategies are essential for protecting your research work. This guide covers backup methods, recovery procedures, and best practices for data preservation.

## Backup Strategies

### Git-Based Backup

**Primary backup method:**

**Local Git:**
```bash
# Regular commits
git add .
git commit -m "Backup: $(date +%Y%m%d)"

# Push to remote
git push origin main
```

**Multiple Remotes:**
```bash
# Add backup remote
git remote add backup https://github.com/username/backup-repo.git

# Push to backup
git push backup main
```

**Benefits:**
- Version history
- Automatic backup on push
- Easy recovery
- Cross-platform

### File System Backup

**Manual backups:**
```bash
# Create backup archive
tar -czf backup_$(date +%Y%m%d).tar.gz \
    src/ tests/ scripts/ manuscript/ docs/

# Exclude output (regenerable)
tar -czf backup_$(date +%Y%m%d).tar.gz \
    --exclude=output/ \
    --exclude=.venv/ \
    --exclude=__pycache__/ \
    .
```

**Automated backups:**
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="$HOME/backups/research-projects"
PROJECT_DIR="$(pwd)"
BACKUP_NAME="$(basename $PROJECT_DIR)_$(date +%Y%m%d_%H%M%S).tar.gz"

mkdir -p "$BACKUP_DIR"

tar -czf "$BACKUP_DIR/$BACKUP_NAME" \
    --exclude=output/ \
    --exclude=.venv/ \
    --exclude=__pycache__/ \
    --exclude=.pytest_cache/ \
    .

echo "Backup created: $BACKUP_DIR/$BACKUP_NAME"
```

### Cloud Backup

**Cloud storage options:**
- GitHub (git repository)
- Dropbox/Google Drive (file sync)
- AWS S3 (automated backups)
- Backblaze (continuous backup)

**GitHub backup:**
```bash
# Push to GitHub
git push origin main

# GitHub provides:
# - Version history
# - Automatic backup
# - Remote storage
# - Collaboration
```

### Selective Backup

**What to backup:**
- ✅ Source code (`src/`)
- ✅ Tests (`tests/`)
- ✅ Scripts (`scripts/`)
- ✅ Manuscript (`manuscript/`)
- ✅ Documentation (`docs/`)
- ✅ Configuration (`pyproject.toml`, `.env`)
- ❌ Output files (`output/` - regenerable)
- ❌ Virtual environment (`.venv/` - regenerable)
- ❌ Cache files (`.pytest_cache/` - regenerable)

## Recovery Procedures

### Recovery

**From Git repository:**
```bash
# Clone repository
git clone https://github.com/username/project.git
cd project

# Restore dependencies
uv sync

# Rebuild outputs
python3 scripts/execute_pipeline.py --core-only
```

**From backup archive:**
```bash
# Extract backup
tar -xzf backup_20250101.tar.gz

# Restore dependencies
uv sync

# Rebuild outputs
python3 scripts/execute_pipeline.py --core-only
```

### Partial Recovery

**Recover specific files:**
```bash
# From Git
git checkout HEAD -- path/to/file

# From backup
tar -xzf backup.tar.gz path/to/file

# From specific commit
git checkout <commit-hash> -- path/to/file
```

### Recovery from Corruption

**If files are corrupted:**
```bash
# Check Git status
git status

# Identify corrupted files
git diff

# Restore from last commit
git checkout HEAD -- corrupted-file.py

# Or restore from specific commit
git checkout <good-commit-hash> -- corrupted-file.py
```

## Data Preservation

### Critical Data

**Ensure these are backed up:**
1. **Source code** - All `src/` modules
2. **Tests** - test suite
3. **Manuscript** - All markdown files
4. **Configuration** - `pyproject.toml`, environment variables
5. **Custom scripts** - Project-specific scripts

### Regenerable Data

**These can be regenerated:**
- Output PDFs (from markdown)
- Generated figures (from scripts)
- Data files (from analysis)
- Virtual environment (from dependencies)

**But consider backing up:**
- Final PDF outputs (for archival)
- Important figures (for reference)
- Key data files (for reproducibility)

## Disaster Recovery

### System Failure

**Recovery steps:**
1. **Restore from backup** - Latest backup archive
2. **Clone from Git** - Latest repository state
3. **Restore dependencies** - `uv sync`
4. **Rebuild outputs** - `python3 scripts/execute_pipeline.py --core-only`
5. **Validate** - Run tests, check outputs

### Partial Data Loss

**Recovery steps:**
1. **Identify lost files** - Compare with backup
2. **Restore selectively** - From backup or Git
3. **Verify integrity** - Check file hashes
4. **Test functionality** - Run tests
5. **Rebuild if needed** - Regenerate outputs

### Corruption Recovery

**If files are corrupted:**
1. **Identify corruption** - Check file integrity
2. **Restore from backup** - Latest known good
3. **Verify restoration** - Check file contents
4. **Test functionality** - Ensure everything works
5. **Document issue** - Note what happened

## Backup Best Practices

### Frequency

**Recommended backup schedule:**
- **Commits** - After each significant change
- **Git push** - Daily or more frequently
- **File backups** - Weekly or monthly
- **Cloud sync** - Continuous (if configured)

### Automation

**Automated backup script:**
```bash
#!/bin/bash
# auto-backup.sh

# Daily backup
BACKUP_DIR="$HOME/backups"
PROJECT_DIR="$(pwd)"
DATE=$(date +%Y%m%d)

# Git backup
git add .
git commit -m "Auto-backup: $DATE" || true
git push origin main || true

# File backup
tar -czf "$BACKUP_DIR/backup_$DATE.tar.gz" \
    --exclude=output/ \
    --exclude=.venv/ \
    .

# Clean old backups (keep last 30 days)
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +30 -delete
```

**Schedule with cron:**
```bash
# Add to crontab
0 2 * * * /path/to/auto-backup.sh
```

### Verification

**Verify backups:**
```bash
# Check backup integrity
tar -tzf backup.tar.gz > /dev/null && echo "Backup OK" || echo "Backup corrupted"

# Test restoration
mkdir test_restore
cd test_restore
tar -xzf ../backup.tar.gz
uv sync
python3 scripts/execute_pipeline.py --core-only
```

## Recovery Checklists

### Before Recovery

- [ ] Identify what needs recovery
- [ ] Locate backup or Git repository
- [ ] Verify backup integrity
- [ ] Plan recovery steps
- [ ] Backup current state (if any)

### During Recovery

- [ ] Restore files systematically
- [ ] Verify each step
- [ ] Test after restoration
- [ ] Document recovery process
- [ ] Note any issues

### After Recovery

- [ ] Verify all files restored
- [ ] Run test suite
- [ ] Build outputs
- [ ] Validate functionality
- [ ] Update backups

## Prevention Strategies

### Regular Backups

**Establish routine:**
- Commit frequently
- Push to remote regularly
- Create file backups periodically
- Test backup restoration

### Version Control

**Use Git effectively:**
- Commit after each change
- Push to remote frequently
- Use branches for experiments
- Tag important versions

### Documentation

**Document your work:**
- Keep notes in commits
- Document important decisions
- Maintain changelog
- Record configuration changes

## Summary

Backup and recovery best practices:

1. **Multiple backups** - Git, files, cloud
2. **Regular schedule** - Automated when possible
3. **Verification** - Test backup integrity
4. **Recovery procedures** - Documented and tested
5. **Prevention** - Regular backups, version control

**Key principles:**
- Backup before major changes
- Test recovery procedures
- Keep multiple backup copies
- Document backup strategy
- Automate when possible

For more information, see:
- [Version Control](../best-practices/version-control.md) - Git workflows
- [Troubleshooting Guide](../operational/troubleshooting-guide.md) - Recovery troubleshooting
- [Common Workflows](../reference/common-workflows.md) - Backup workflows

---

**Related Documentation:**
- [Version Control](../best-practices/version-control.md) - Git backup strategies
- [Troubleshooting Guide](../operational/troubleshooting-guide.md) - Recovery procedures
- [Common Workflows](../reference/common-workflows.md) - Backup workflows


