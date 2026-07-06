# Security Policy

## Reporting a vulnerability

**Do not open a public issue for security vulnerabilities.**

Use GitHub's private vulnerability reporting:
**[Report a vulnerability](https://github.com/docxology/template/security/advisories/new)**
(repository → *Security* → *Advisories* → *Report a vulnerability*).

If private reporting is unavailable, contact the maintainer through the
profile on the [`docxology`](https://github.com/docxology) GitHub account.

Please include: affected version/commit, reproduction steps, impact, and any
suggested remediation. You can expect an acknowledgement within a few days.

## Scope

This is a **public research-project template**. The security-relevant
surface is the **Layer-1 infrastructure** (`infrastructure/`), the
orchestration **scripts** (`scripts/`), and the CI/CD configuration
(`.github/workflows/`). Per-project trees under `projects/` outside the
public canonical exemplars are **local-only and never published** (enforced by
`scripts/audit/check_tracked_projects.py`); do not report issues about
non-published local project content here.

## Supported versions & hardening

The full policy — supported versions, the no-mocks/test-coverage gates,
Bandit (`bandit.yaml`) and `pip-audit` (blocking, with
`.github/pip-audit-ignore.txt`) scanning, secret handling, and steganographic
provenance — lives in
[`docs/development/security.md`](../docs/development/security.md). This file
is the GitHub-discoverable entry point; that document is the detail.
