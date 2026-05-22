# Subsystem Status

> Per-subsystem heartbeat. Each row records the **last time the subsystem was manually verified end-to-end** by a maintainer (not just "tests pass" — the gates can be wrong; see `MEMORY` lessons and `docs/maintenance/regression-testing.md`).
>
> Refresh target: every 6 months. Anything older than **365 days** should be treated as potentially dormant.

**Last updated:** 2026-05-20
**Maintained by:** Daniel Ari Friedman (see [MAINTAINERS.md](MAINTAINERS.md))

## Verification ledger

| Subsystem | Last verified | Verified by | Verification scope | Health |
| --- | --- | --- | --- | --- |
| Pipeline orchestration (`infrastructure/orchestration/`) | 2026-05-20 | Daniel | `./run.sh --pipeline --project template_code_project --core-only` runs to completion; both exemplars green | 🟢 healthy |
| Test runner (`scripts/01_run_tests.py`, `tests/infra_tests/`) | 2026-05-20 | Daniel | 60% infra coverage floor + 90% per-project floor + 75% combined union floor all enforced; mypy --strict passes per memory (2026-05-20) | 🟢 healthy |
| PDF rendering (`infrastructure/rendering/`) | — | Daniel | Stage 5 ships PDFs on both exemplars; `tlmgr` deps documented in `docs/operational/troubleshooting/` | 🟡 verify next refresh |
| Output validation (`infrastructure/validation/`) | — | Daniel | Stage 6 validation CLI runs on PDFs and markdown | 🟡 verify next refresh |
| LLM stages (`infrastructure/llm/`, Stages 7+8) | — | Daniel | Ollama `gemma3:4b` integration tested manually; reframed 2026-05-20 as "draft assistance" not "scientific review" — see `infrastructure/llm/README.md` | 🟡 model pin needs review at next refresh |
| Steganography (`infrastructure/steganography/`) | — | Daniel | Threat model published 2026-05-20 — see `infrastructure/steganography/THREAT_MODEL.md`. Defaults to off for public exemplars. | 🟡 verify watermark survives PDF re-render at next refresh |
| Publishing (`infrastructure/publishing/`) | — | Daniel | Zenodo DOI 10.5281/zenodo.19139090 resolves; arXiv path documented. Archival-target redundancy (IPFS, Software Heritage) added 2026-05-20 — see `docs/maintenance/archival-targets.md` | 🟡 archival-redundancy targets need first end-to-end run |
| Confidentiality invariant (`scripts/check_tracked_projects.py` + `.gitignore` + pre-push + symlink boundary) | 2026-05-21 | Daniel | Hook fires on attempted `git add -f` of non-template project; CI lint job blocks merge. **Implemented 2026-05-21: confidential projects physically separated to the private `docxology/projects` repo (active/passive/archive), symlinked into `projects/` for render — see [docs/maintenance/private-projects-repo.md](docs/maintenance/private-projects-repo.md). git refuses to stage content "beyond a symbolic link."** | 🟢 physical separation + layered defense |
| Multi-project discovery (`infrastructure/project/discovery.py`) | 2026-05-20 | Daniel | `discover_projects()` returns the two canonical exemplars + any rotating-active projects; output drives `docs/_generated/active_projects.md` | 🟢 healthy |
| Secure-run subcommand (`secure_run.sh`, `infrastructure.orchestration secure`) | — | Daniel | `--steganography-only --project {name}` works on canonical exemplars | 🟡 verify next refresh |
| CI matrix (`.github/workflows/ci.yml`) | 2026-05-20 | Daniel | Ubuntu/macOS × Python 3.10–3.12, Dependabot wired; local reproduction documented in `docs/maintenance/ci-local.md` | 🟢 healthy; Python 3.10 EOL Oct 2026 → drop next refresh |
| Documentation index (`docs/documentation-index.md`) | 2026-05-20 | Daniel | Authoritative per-file index; `docs/_generated/active_projects.md` is the rotating-project source-of-truth | 🟢 healthy |
| Skills manifest (`infrastructure/skills/`) | — | Daniel | `uv run python -m infrastructure.skills write` generates `.cursor/skill_manifest.json` | 🟡 verify next refresh |
| Regression tests (`tests/regression/`) | 2026-05-20 | Daniel | **NEW** — scaffold added 2026-05-20. Per-figure / per-table pinned numerical outputs. See `docs/maintenance/regression-testing.md` | 🔴 scaffold only; no pinned cases yet |

## Health legend

- 🟢 **healthy** — last verified ≤ 6 months ago; gates green; no known structural issue
- 🟡 **verify next refresh** — last verified > 6 months ago (or never), or has a known follow-up; not currently failing
- 🔴 **action needed** — known structural issue or scaffold pending fleshing-out; do not assume it Just Works
- ⚪ **archived/dormant** — explicitly retired; do not rely on

## How to refresh a row

1. Run the subsystem's verification step end-to-end (not just "tests pass" — see [`docs/maintenance/regression-testing.md`](docs/maintenance/regression-testing.md) on why test-green is not the same as subsystem-verified).
2. Update the "Last verified" date, your name, and the verification scope (be specific — "ran `./run.sh --pipeline --project X --core-only` and PDF rendered cleanly" beats "checked it").
3. Set the health emoji.
4. Commit the change; CI checks that the table is well-formed.

## Why this matters at multi-decade horizons

A template repo claiming reproducibility / agent-accessible-science / public-template viability across 10+ years cannot reasonably make those claims without **visible dormancy**. Untracked subsystems decay silently. This file is the cheapest insurance — one row updated per quarter is enough to keep the claim honest.

## Related

- [MAINTAINERS.md](MAINTAINERS.md) — who owns what
- [docs/maintenance/](docs/maintenance/) — toolchain migration, regression testing, archival, local CI
- [AGENTS.md](AGENTS.md) — full system manual
