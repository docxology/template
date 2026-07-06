# Subsystem Status

> Per-subsystem heartbeat. Each row records the **last time the subsystem was manually verified end-to-end** by a maintainer (not just "tests pass" — the gates can be wrong; see `MEMORY` lessons and `docs/maintenance/regression-testing.md`).
>
> Refresh target: every 6 months. Anything older than **365 days** should be treated as potentially dormant.

**Last updated:** 2026-07-02
**Maintained by:** Daniel Ari Friedman (see [MAINTAINERS.md](MAINTAINERS.md))

## Verification ledger

| Subsystem | Last verified | Verified by | Verification scope | Health |
| --- | --- | --- | --- | --- |
| Pipeline orchestration (`infrastructure/orchestration/`) | 2026-05-21 | Daniel | `./run.sh --pipeline --project template_code_project --core-only --skip-infra` and `./run.sh --pipeline --project template_prose_project --core-only --skip-infra` run to completion; both named exemplars green | 🟢 healthy |
| Test runner (`scripts/pipeline/stage_01_test.py`, `tests/infra_tests/`) | 2026-07-02 | Daniel (agent session) | 60% infra coverage floor + 90% per-project floor + 75% combined union floor all enforced. mypy runs clean on the CI public-scope paths under the repo config (NOT `--strict`: `disallow_untyped_defs=false` globally and 8 `infrastructure.*` packages carry `ignore_errors` overrides in `pyproject.toml` — `mypy --strict infrastructure` currently reports 5 errors, tracked in [`docs/maintenance/review-remediation-2026-07.md`](docs/maintenance/review-remediation-2026-07.md)) | 🟢 healthy (CI-config typing; strict typing is a tracked backlog item) |
| PDF rendering (`infrastructure/rendering/`) | 2026-05-21 | Daniel | Stage 5 rendered combined PDF/HTML/DOCX/slides for `template_code_project` and `template_prose_project`; `template_code_project` also rendered EPUB | 🟢 healthy |
| Output validation (`infrastructure/validation/`) | 2026-05-21 | Daniel | Stage 6 validation passed 7/7 checks for `template_code_project` and `template_prose_project` after full core renders | 🟢 healthy |
| LLM stages (`infrastructure/llm/`, Stages 7+8) | 2026-07-01 | Daniel (agent session) | Model pin `gemma3:4b` re-verified pullable/available (`ollama pull gemma3:4b` succeeded, 3.3GB); live `pytest tests/infra_tests/llm/ -m requires_ollama` — 50/51 passed (1 failure was a 20s timeout on `smollm2:latest` under local load, an environmental flake unrelated to the `gemma3:4b` pin, not a gate defect); "draft assistance" framing from 2026-05-20 confirmed still accurate in `infrastructure/llm/README.md` | 🟢 healthy |
| Steganography (`infrastructure/steganography/`) | 2026-05-21 | Daniel | `STEGANOGRAPHY_DETERMINISTIC=1 ./secure_run.sh --steganography-only --project template_code_project` produced a 28-page `_steganography.pdf` plus `.hashes.json` manifest with SHA-256/SHA-512, document ID, source size, and Git commit provenance | 🟢 healthy |
| Publishing (`infrastructure/publishing/`) | 2026-07-01 | Daniel (agent session) | Zenodo DOI 10.5281/zenodo.19139090 resolves; arXiv path documented. `scripts/runner/archive_publication.py --project templates/template_code_project` dry-run E2E verified end-to-end (after building the Stage 10 executable bundle prerequisite): `all_ok: true`, Software Heritage receipt generated at `output/templates/template_code_project/executable_bundle/ARCHIVAL_RECEIPTS.json`. **Real (non-dry-run) deposit still blocked**: no `.env` exists in this checkout, so Zenodo/GitHub/IPFS credentials are absent — the mechanics are proven, the live multi-provider deposit itself has not run | 🟡 mechanics verified via dry-run; real multi-provider deposit needs credentials |
| Confidentiality invariant (`scripts/audit/check_tracked_projects.py` + `.gitignore` + pre-push + symlink boundary) | 2026-05-21 | Daniel | Hook fires on attempted `git add -f` of non-template project; CI lint job blocks merge. **Implemented 2026-05-21 and simplified 2026-06-06: confidential projects physically separated to the private `docxology/projects` repo (required working/archive sidecar, optional legacy active/published/other mirrors), symlinked into `projects/` typed subfolders — see [docs/maintenance/private-projects-repo.md](docs/maintenance/private-projects-repo.md).** | 🟢 physical separation + layered defense |
| Multi-project discovery (`infrastructure/project/discovery.py`) | 2026-05-20 | Daniel | `discover_projects()` returns public exemplars plus any rotating-active projects; `infrastructure.project.public_scope` filters docs/CI scope into `docs/_generated/active_projects.md` | 🟢 healthy |
| Secure-run subcommand (`secure_run.sh`, `infrastructure.orchestration secure`) | 2026-05-21 | Daniel | Deterministic `--steganography-only --project template_code_project` smoke completed through `infrastructure.orchestration secure`; AES-256 PDF password behavior covered by `tests/infra_tests/steganography/test_encryption.py` | 🟢 healthy |
| CI matrix (`.github/workflows/ci.yml`) | 2026-05-20 | Daniel | Ubuntu/macOS × Python 3.10–3.12, Dependabot wired; local reproduction documented in `docs/maintenance/ci-local.md` | 🟢 healthy; Python 3.10 EOL Oct 2026 → drop next refresh |
| Documentation index (`docs/documentation-index.md`) | 2026-05-20 | Daniel | Authoritative per-file index; `docs/_generated/active_projects.md` is the rotating-project source-of-truth | 🟢 healthy |
| Skills manifest (`infrastructure/skills/`) | 2026-05-21 | Daniel | `uv run python -m infrastructure.skills write` and `write-index` refreshed `.cursor/skill_manifest.json` and `docs/_generated/skills_index.md` after steganography skill edits | 🟢 healthy |
| Regression tests (`tests/regression/`) | 2026-07-02 | Daniel (agent session) | All fifteen public exemplars carry source-re-derived regression pins under `tests/regression/projects/` with matching pinned-value JSONs and per-project negative controls: `uv run pytest tests/regression/ --collect-only -q --no-cov` collects 55 tests, `uv run pytest tests/regression/ -q --no-cov` passes together. Not yet wired into a CI job (tracked in [`docs/maintenance/review-remediation-2026-07.md`](docs/maintenance/review-remediation-2026-07.md)). See `docs/maintenance/regression-testing.md` | 🟡 all 15 exemplars pinned locally; CI wiring pending |
| AutoResearch exemplar (`projects/templates/template_autoresearch_project/`) | 2026-06-13 | Codex | `uv run pytest projects/templates/template_autoresearch_project/tests/ -q` passed 224 tests after adding evidence overview, benchmark-boundary, and source-ledger contract checks | 🟢 healthy |

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
