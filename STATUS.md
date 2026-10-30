# Subsystem Status

> Per-subsystem heartbeat. Each row records the **last time the subsystem was manually verified end-to-end** by a maintainer (not just "tests pass" — the gates can be wrong; see `MEMORY` lessons and `docs/maintenance/regression-testing.md`).
>
> Refresh target: every 6 months. Anything older than **183 days** should be treated as potentially dormant.

**Last updated:** 2026-10-28
**Maintained by:** Daniel Ari Friedman (see [MAINTAINERS.md](MAINTAINERS.md))

The last-verified dates below belong to the preserved pre-Platform-4 checks.
Current commands name the replacement interface; their presence does not
claim a fresh run. Exact previous rows are retained in
[verification history](docs/maintenance/subsystem-status-history.md).

## Verification ledger

| ID | Subsystem | Last verified | Verified by | Verification scope | Command | Receipt | Mode | Health |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| STATUS-PIPELINE-1 | Pipeline orchestration (`infrastructure/orchestration/`) | 2026-05-21 | Daniel | Last accepted pre-Platform-4 check retained unchanged in [history](docs/maintenance/subsystem-status-history.md). Fresh candidate acceptance remains required. | `./run.sh --pipeline --project templates/template_code_project --mode core --skip-infra` | docs/_generated/status_evidence.json | manual | 🟡 Platform 4 acceptance pending |
| STATUS-TEST-RUNNER-1 | Test runner (`scripts/pipeline/stage_01_test.py`, `tests/infra_tests/`) | 2026-08-09 | Daniel (agent session) | Last accepted pre-Platform-4 check retained unchanged in [history](docs/maintenance/subsystem-status-history.md). Fresh candidate acceptance remains required. | `uv run python scripts/pipeline/stage_01_test.py --infra-only --profile release` | docs/_generated/status_evidence.json | automated | 🟡 Platform 4 acceptance pending |
| STATUS-PDF-RENDER-1 | PDF rendering (`infrastructure/rendering/`) | 2026-05-21 | Daniel | Last accepted pre-Platform-4 check retained unchanged in [history](docs/maintenance/subsystem-status-history.md). Fresh candidate acceptance remains required. | `uv run python scripts/pipeline/stage_03_render.py --project templates/template_code_project` | docs/_generated/status_evidence.json | manual | 🟡 Platform 4 acceptance pending |
| STATUS-OUTPUT-VALIDATION-1 | Output validation (`infrastructure/validation/`) | 2026-05-21 | Daniel | Last accepted pre-Platform-4 check retained unchanged in [history](docs/maintenance/subsystem-status-history.md). Fresh candidate acceptance remains required. | `uv run python scripts/pipeline/stage_04_validate.py --project templates/template_code_project` | docs/_generated/status_evidence.json | automated | 🟡 Platform 4 acceptance pending |
| STATUS-LLM-1 | Local draft-assistance stages (`infrastructure/llm/`) | 2026-07-01 | Daniel (agent session) | Last accepted pre-Platform-4 check retained unchanged in [history](docs/maintenance/subsystem-status-history.md). Fresh candidate acceptance remains required. | `uv run pytest tests/infra_tests/llm -m requires_ollama -q` | docs/_generated/status_evidence.json | optional-tool | 🟡 Platform 4 acceptance pending |
| STATUS-STEGANOGRAPHY-1 | Steganography (`infrastructure/steganography/`) | 2026-05-21 | Daniel | Last accepted pre-Platform-4 check retained unchanged in [history](docs/maintenance/subsystem-status-history.md). Fresh candidate acceptance remains required. | `STEGANOGRAPHY_DETERMINISTIC=1 ./secure_run.sh --steganography-only --project template_code_project` | docs/_generated/status_evidence.json | manual | 🟡 Platform 4 acceptance pending |
| STATUS-PUBLISHING-1 | Publishing (`infrastructure/publishing/`) | 2026-07-01 | Daniel (agent session) | Last accepted pre-Platform-4 check retained unchanged in [history](docs/maintenance/subsystem-status-history.md). Fresh candidate acceptance remains required. | `uv run python scripts/runner/archive_publication.py --project templates/template_code_project --providers software_heritage` | docs/_generated/status_evidence.json | external | 🟡 Platform 4 acceptance pending |
| STATUS-CONFIDENTIALITY-1 | Confidentiality invariant (`scripts/audit/check_tracked_all.py` + `.gitignore` + pre-push + symlink boundary) | 2026-05-21 | Daniel | Last accepted pre-Platform-4 check retained unchanged in [history](docs/maintenance/subsystem-status-history.md). Fresh candidate acceptance remains required. | `uv run python scripts/audit/check_tracked_all.py` | docs/_generated/status_evidence.json | automated | 🟡 Platform 4 acceptance pending |
| STATUS-DISCOVERY-1 | Multi-project discovery (`infrastructure/project/discovery.py`) | 2026-05-20 | Daniel | Last accepted pre-Platform-4 check retained unchanged in [history](docs/maintenance/subsystem-status-history.md). Fresh candidate acceptance remains required. | `uv run python scripts/docgen/active_projects.py --check` | docs/_generated/status_evidence.json | automated | 🟡 Platform 4 acceptance pending |
| STATUS-SECURE-RUN-1 | Secure-run subcommand (`secure_run.sh`, `infrastructure.orchestration secure`) | 2026-05-21 | Daniel | Last accepted pre-Platform-4 check retained unchanged in [history](docs/maintenance/subsystem-status-history.md). Fresh candidate acceptance remains required. | `STEGANOGRAPHY_DETERMINISTIC=1 ./secure_run.sh --steganography-only --project template_code_project` | docs/_generated/status_evidence.json | manual | 🟡 Platform 4 acceptance pending |
| STATUS-CI-MATRIX-1 | CI matrix (`.github/workflows/ci.yml`) | 2026-09-28 | Codex (agent session) | Python 3.14–3.15 source and installed-package matrices are declared for Platform 4. Earlier hosted receipts remain in history; an exact-revision hosted acceptance run is still required. | `uv run python scripts/audit/check_public_template_contract.py --strict` | docs/_generated/status_evidence.json | external | 🟡 Platform 4 acceptance pending |
| STATUS-DOCUMENTATION-1 | Documentation index and generated docs (`docs/`) | 2026-07-22 | Daniel (agent session) | Last accepted pre-Platform-4 check retained unchanged in [history](docs/maintenance/subsystem-status-history.md). Fresh candidate acceptance remains required. | `uv run python scripts/docgen/counts.py --check` | docs/_generated/status_evidence.json | automated | 🟡 Platform 4 acceptance pending |
| STATUS-ROOT-RELEASE-1 | Root release boundary (`pyproject.toml`, tags, GitHub releases, `CHANGELOG.md`) | 2026-10-28 | Codex (agent session) | Root 4.4.1 is the current release intent. Root metadata, locks and all public exemplar compatibility bindings declare 4.4.1. Hosted required acceptance on main `8227dc8e805ea0f950125b974abf226cdeb7419d` failed on 2026-10-30: Root policy admission was stale, project runtime hydration failed on Python 3.15, and native rendering selected the installed SDK directory; installed/export verification completed before the runtime failure. The latest published root release is v3.8.0. Earlier 4.x preparations remain unpublished. The version command checks metadata, provider, tag and changelog consistency; a new tag and release separately require exact-revision hosted acceptance and the authenticated evidence handoff. | `uv run --no-sync --offline python -m infrastructure.publishing.root_release_contract --tag v4.4.1` | docs/_generated/status_evidence.json | manual | 🟡 Publication pending; hosted acceptance required |
| STATUS-SKILLS-1 | Skills manifest (`infrastructure/skills/`) | 2026-07-15 | Daniel (agent session) | Last accepted pre-Platform-4 check retained unchanged in [history](docs/maintenance/subsystem-status-history.md). Fresh candidate acceptance remains required. | `uv run python -m infrastructure.skills check` | docs/_generated/status_evidence.json | automated | 🟡 Platform 4 acceptance pending |
| STATUS-REGRESSION-1 | Regression tests (`tests/regression/`) | 2026-07-15 | Daniel (agent session) | Last accepted pre-Platform-4 check retained unchanged in [history](docs/maintenance/subsystem-status-history.md). Fresh candidate acceptance remains required. | `uv run pytest tests/regression/ -q --no-cov --timeout=120` | docs/_generated/status_evidence.json | external | 🟡 Platform 4 acceptance pending |
| STATUS-AUTORESEARCH-1 | AutoResearch exemplar (`projects/templates/template_autoresearch_project/`) | 2026-06-13 | Codex | Last accepted pre-Platform-4 check retained unchanged in [history](docs/maintenance/subsystem-status-history.md). Fresh candidate acceptance remains required. | `uv run pytest projects/templates/template_autoresearch_project/tests -q --no-cov --timeout=120` | docs/_generated/status_evidence.json | automated | 🟡 Platform 4 acceptance pending |
| STATUS-RENDER-RECOVERY-1 | Rendering internals, checkpoint recovery, and local exports | 2026-09-05 | Codex | Last accepted pre-Platform-4 check retained unchanged in [history](docs/maintenance/subsystem-status-history.md). Fresh candidate acceptance remains required. | `uv run pytest tests/infra_tests/rendering/test_slides_accessibility.py -m slow -q --no-cov --timeout=120` | docs/_generated/status_evidence.json | automated | 🟡 Platform 4 acceptance pending |

## Health legend

- 🟢 **healthy** — last verified ≤ 6 months ago; gates green; no known structural issue
- 🟡 **verify next refresh** — last verified > 6 months ago (or never), or has a known follow-up; not currently failing
- 🔴 **action needed** — known structural issue or scaffold pending fleshing-out; do not assume it Just Works
- ⚪ **archived/dormant** — explicitly retired; do not rely on

## How to refresh a row

1. Run the subsystem's verification step end-to-end (not just "tests pass" — see [`docs/maintenance/regression-testing.md`](docs/maintenance/regression-testing.md) on why test-green is not the same as subsystem-verified).
2. Update the "Last verified" date, your name, and the verification scope (be specific — "ran `./run.sh --pipeline --project templates/<name> --mode core` and PDF rendered cleanly" beats "checked it").
3. Set the health emoji.
4. Commit the change; CI checks that the table is well-formed.

## Why this matters at multi-decade horizons

A template repo claiming reproducibility / agent-accessible-science / public-template viability across 10+ years cannot reasonably make those claims without **visible dormancy**. Untracked subsystems decay silently. This file is the cheapest insurance — one row updated per quarter is enough to keep the claim honest.

## Related

- [MAINTAINERS.md](MAINTAINERS.md) — who owns what
- [docs/maintenance/](docs/maintenance/) — toolchain migration, regression testing, archival, local CI
- [AGENTS.md](AGENTS.md) — full system manual
