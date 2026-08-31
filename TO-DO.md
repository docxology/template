# Repo TO-DO — future cross-cutting work

> **Design ethos:** modular, intelligent, functional, logged, tested, and
> documented. Real methods only; never mocks or fakes. Every release ships with
> green tests, source-bound evidence, and accurate documentation.

This is the root repository backlog and contains future work only: cross-cutting
infrastructure, CI, documentation, release, security, and reproducibility
improvements. Completed work is preserved in [`CHANGELOG.md`](CHANGELOG.md) or
the dated maintenance records; generated facts remain owned by their
generators; exemplar-specific work belongs in the relevant public
`projects/templates/*/TODO.md`.

Every active row has a stable ID and the complete contract
`ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control`.
Active work is decomposed into Minor or Medium slices. A missing owner,
external receipt, or optional tool is a blocker, never an implicit success.

## Live baseline and constraints

The public roster is authoritative in
[`docs/_generated/active_projects.md`](docs/_generated/active_projects.md), and
measured facts are authoritative in
[`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md). Re-derive them before
editing this file or closing a row.

The deterministic default is offline and one-process-per-project. Network,
LLM, live-data, container, formal-tool, raster, and publication paths are
explicitly opt-in and fail closed when unavailable. Private sidecars,
rotating projects, branch protection, CODEOWNERS review, and owner-authorized
promotion are outside the evidence a local checkout can establish.

## Active root backlog

These are the prioritized scoped improvements and remaining root-level actions, classified by Minor, Medium, and Major categories.

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ERG-ENTRY-DOCS-2026-08-31` | completed | Minor | none | 2026-08-31 agent-ergonomics passes: orientation-ladder status/next-action links added to START_HERE.md (duplicate orientation blocks consolidated), AGENTS.md doc map, docs/documentation-index.md. See docs/audit/REVIEW_LOG_2026-08-31.md. | docs/audit/REVIEW_LOG_2026-08-31.md | `grep -c STATUS.md START_HERE.md AGENTS.md docs/documentation-index.md` | broken relative link or missing section must fail lint_docs |
| `DOC-LINKS-STANDARDIZE-MIN-1` | completed | Minor | Documentation links, frontmatter schema | Standardize workflow skill frontmatter metadata and fix documentation links / CLI option descriptions. | verified documentation and metadata manifest | `uv run python -m infrastructure.skills check-contracts` | missing or malformed metadata fields must fail contract check |
| `INFRA-MODULES-ENHANCE-MED-1` | completed | Medium | Doctor, Validation, Search, Reference modules | Enhance infrastructure doctor detectors (DOC204 bib/preamble check), search cache query normalization, and reference resolver resilience. | enhanced infra test suite | `uv run pytest tests/infra_tests/doctor tests/infra_tests/search tests/infra_tests/reference -v` | invalid cache payload or broken bibtex must be rejected |
| `PROVENANCE-DAG-HARDEN-MAJ-1` | completed | Medium | Provenance DAG models and store | Implement unified provenance DAG graph integrity validator and cycle / missing reference checks with full CLI interface. | provenance validation test suite | `uv run pytest tests/infra_tests/provenance -v` | circular or dangling edges must fail validation |
| `AUTORESEARCH-ORCHESTRATION-MAJ-1` | completed | Medium | AutoResearch engine, planner, reports | Add AutoResearch multi-phase pipeline orchestration engine with structured phase transitions, budget enforcement, and run ledger logging. | autoresearch orchestration test suite | `uv run pytest tests/infra_tests/autoresearch -v` | budget exhaustion or unapproved publication gates must halt loop |
| `MANUSCRIPT-RENDER-OPTIMIZE-MAJ-1` | completed | Medium | Rendering manager, cache, composition | Add modular manuscript section caching and parallel format dispatch options to optimize multi-format rendering passes. | rendering benchmark report | `uv run pytest tests/infra_tests/rendering -v` | corrupted cache or missing required sections must fail render |
| `EXECUTABLE-BUNDLE-MAJ-1` | completed | Medium | Immutable bundle verifier, pinned runtime, isolated container | Closed 2026-08-26: full offline-container verification receipt attached (`docs/audit/executable-bundle-offline-receipt-2026-08-26.md`). Image `template-bundle-vendored:2026-08-26` (id `58c35a2d1675`) built from the regenerated bundle with the vendored `infrastructure/` payload (see `EXECUTABLE-BUNDLE-MAJ-2`); under `--network none` the project suite passes for real (242 passed, exit 0) and full-pipeline compose services fail closed with the explicit `UNAVAILABLE-DEPENDENCY RECEIPT` (exit 3). Build needs >= 4 GiB VM memory on colima. | offline-container verification receipt | `uv run python scripts/runner/bundle_executable.py --project templates/template_code_project` | changed payload, missing lock, private symlink, path escape, or unavailable container must fail/record blocked |
| `CLEAN-CHECKOUT-MAJ-1` | blocked-external | Medium | Local disposable rehearsal and hosted Linux runner | Run two deterministic hosted-Linux rehearsals and attach the owner/platform receipt; local generated render output is restored only inside the disposable clone after path-boundary validation. | clean-checkout rehearsal receipt | `uv run python scripts/maintenance/release_rehearsal.py --execute --receipt /tmp/template-clean-checkout.json` | non-generated mutation, dirty final tree, changed revision, or unequal deterministic runs must fail |
| `DOC-ENTRY-ORIENT-LADDER-MIN-2` | completed | Minor | Root entry docs, `docs/_generated/` generators | 2026-08-31 agent-ergonomics pass: added a "Current state (verify, don't trust)" orientation block to `START_HERE.md` linking STATUS.md, TO-DO.md, and generated fact surfaces (previously a cold agent reading only START_HERE could not find status or backlog). | edited START_HERE.md in git history | `grep -c 'STATUS.md' START_HERE.md` (>=2) | entry doc without a status/backlog pointer must be flagged by future cold-start audits |
| `ARCHIVAL-TRACKER-MIN-1` | blocked-external | Medium | Credential-free provider evidence and current public roster | Refresh the archival tracker only from current queue/browse evidence and record accepted, pending, verified, unavailable, rate-limited, and excluded states with as-of dates. | archival tracking receipt | `uv run python scripts/runner/archive_publication.py --project templates/template_code_project --providers software_heritage` | missing credential/provider or standalone bundle must never report a completed deposit |
| `SECURITY-OWNERSHIP-1` | blocked-external | Medium | Administrator branch-protection and CODEOWNERS receipt | Obtain administrator evidence for required checks, review, force-push protection, and sensitive-path review; local health must remain distinct from authority. | administrator authority receipt | `uv run python scripts/gates/security_scan.py` | repository files or a green local run must not imply remote protection |
| `SECURITY-PRIVATE-PROMOTION-1` | blocked-external | Medium | Owner authorization, redaction, and export evidence | Obtain an owner-approved private-sidecar promotion record before any promotion; keep the public tree and generated receipts free of private paths and content. | owner promotion receipt | `uv run python scripts/audit/check_tracked_all.py` | private path, sidecar content, credential, or unredacted export must fail public guards |
| `DOC-STARTHERE-LINT-TIMEOUT-MED-1` | completed | Minor | `scripts/audit/lint_docs.py` scoped-mode support | Closed 2026-08-31: `--paths` scoped mode added to `scripts/audit/lint_docs.py` / `infrastructure.validation.docs.lint_runner.run_docs_lint` / `doc_roots` (fail-closed on missing or repo-escaping paths; real tests in `tests/infra_tests/validation/docs/test_lint_runner.py`). Usage: `uv run python scripts/audit/lint_docs.py --paths README.md START_HERE.md docs/ --links-only --json`. | scoped tests + this row | `uv run pytest tests/infra_tests/validation/docs/test_lint_runner.py -q --no-cov --timeout=120` | lint that silently skips paths must fail the run |
| `DOC-ROOT-SCRATCH-HYGIENE-MIN-1` | completed | Minor | Root scratch artifacts | Closed 2026-08-31 (agent-ergonomics round-2 lane): all untracked root scratch artifacts (`sidecar_*` x19, `.laneD_results.json`, `.tmp_prune/`, `skillarum-docs/`) moved to local-only gitignored `_agent_erg_archive_2026-08-31/` (`skillarum-docs/` preserved intact, 12 MB). No tracked doc references any moved path; docs lint re-verified green on entry docs. | archived scratch out of root | `ls sidecar_* .laneD_results.json .tmp_prune skillarum-docs 2>/dev/null` returns nothing | root scratch present after archive must fail this check |
| `DOC-ENTRY-ORIENT-MIN-1` | completed | Minor | START_HERE.md entry doc | 2026-08-31 agent-ergonomics pass: START_HERE.md lacked pointers to STATUS.md (current state) and TO-DO.md (next actions); orientation block added at top. | edited START_HERE.md | `python3 scripts/audit/lint_docs.py --json --repo-root .` or manual link check | entry doc must not claim status or backlog facts from memory |
| `AGENT-ERG-ORIENT-LADDER-MIN-1` | completed | Minor | Entry docs (`START_HERE.md`, `README.md`, `AGENTS.md`) | 2026-08-31 agent-ergonomics pass: cold-start orientation ladder verified — START_HERE.md carries a current-state block (STATUS.md health ledger) and next-work row (TO-DO.md backlog); README.md "Choose Your Path" links the cold-start path; AGENTS.md references STATUS.md and TO-DO.md as canonical. All verified live this session. | this row + START_HERE.md diff | `grep -c "TO-DO.md" START_HERE.md README.md AGENTS.md` | entry doc without current-state/next-work pointers must fail this grep |
| `AGENT-ERG-AUDIT-FILES-MED-1` | completed | Medium | Root `AUDIT_2026-08-30*.md` (4 untracked files) | Root-level dated audit reports conflicted with `docs/audit/AGENTS.md` policy. Closed 2026-08-31: a sibling fleet lane moved the four files to `docs/audit/` (with a dated note in `docs/audit/AGENTS.md`); acceptance re-verified this session — no `AUDIT_2026-08-30*.md` at root. | this row | `ls AUDIT_2026-08-30.md 2>/dev/null; echo "exit:$?"` | root-level dated audit report present must fail this check |
| `AGENT-ERG-COUNTS-PROVENANCE-MED-1` | completed | Medium | `scripts/docgen/counts.py` coverage-provenance refresh | counts.py --check reports stale coverage provenance after each coverage measurement (observed 2026-08-31; cf. commits 1dd67aee8, 15045e302). Fold `uv run python scripts/docgen/counts.py --refresh-coverage-provenance --write` into the documented post-measurement step so --check does not require an ad-hoc fix each time. | refreshed docs/_generated/coverage_snapshot.json Closed 2026-08-31 (agent-ergonomics round 2): ran `--refresh-coverage-provenance --write` to completion on the external-drive checkout (~25 min, background); `--check` then reported COUNTS.md OK in sync. Documented in REVIEW_LOG_2026-08-31.md. | `uv run python scripts/docgen/counts.py --check` | stale provenance must fail --check (current behavior) |
| `AGENT-ERG-ROOT-REPORTS-MED-2` | completed | Medium | Root `_FLEET_REPORT_2026-08-30.md` and `REVIEW_LOG_2026-08-31.md` | 2026-08-31 round-2 agent-ergonomics pass: the two tracked root-level dated lane reports violated the docs/audit/AGENTS.md root-hygiene policy (root Markdown is long-lived docs only). Moved via git mv to docs/audit/ with a dated archival note in docs/audit/AGENTS.md; TO-DO row ERG-ENTRY-DOCS-2026-08-31 evidence link updated to the new path. Verified live this session: no dated-report Markdown remains at repo root. | this row plus docs/audit/AGENTS.md archival note | `git ls-files` filtered for names starting `_FLEET_REPORT` or `REVIEW_LOG` (must print nothing; a piped grep cannot appear inside a markdown table cell) — plus `ls _FLEET_REPORT_2026-08-30.md REVIEW_LOG_2026-08-31.md 2>/dev/null` (must be empty) | a tracked root-level dated report file must fail this check |

## Verification order

Run the bounded deterministic gates before any optional authority or provider
work:

```bash
uv run pytest tests/infra_tests/documentation/ tests/infra_tests/publishing/ -q --no-cov --timeout=120
uv run pytest tests/regression/ -q --no-cov --timeout=120
uv run python scripts/audit/check_backlog.py --strict
uv run python scripts/docgen/counts.py --check
uv run python scripts/audit/check_claim_bindings.py --json
uv run python scripts/audit/check_public_template_contract.py --strict
uv run python scripts/audit/check_template_drift.py --strict
uv run python scripts/audit/check_tracked_all.py
uv run python scripts/audit/check_tracked_generated_artifacts.py
uv run python scripts/audit/check_tracked_secrets.py
```

Then run the isolated public matrix, infrastructure coverage gate, Ruff,
mypy, Bandit, no-mocks, generated-document, manuscript/render, and
accessibility checks. Optional paths must emit `skipped` or `blocked` receipts
when their tools or external authority are unavailable.

## Backlog operating rules

- Re-derive measured facts instead of copying old counts into prose.
- Keep private or rotating project names out of public docs; use the generated roster.
- Prefer real files, subprocesses, deterministic fixtures, and negative controls.
- Keep business logic in `infrastructure/` or project `src/`; scripts remain thin orchestrators.
- Preserve project coverage floors, confidentiality, generated-artifact guards,
  provenance boundaries, and explicit optional-tool skips.
- When an item is complete, move its dated evidence to the changelog or review
  record and remove it from this file in the same change.

## Fleet additions (2026-08-31 agent-ergonomics pass)

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ERG-WALLCLOCK-MED-1` | completed | Minor | `docs/guides/startup-and-setup.md` | Update the "Wall-clock time: 2-5 minutes" claim (line ~117) to match the quiet-machine measurement and add the external-drive/concurrent-load caveat already recorded in `docs/audit/AUDIT_2026-08-30.md` (44+ min measured under load). Closed 2026-08-31: both `START_HERE.md` and `docs/guides/startup-and-setup.md` now carry the quiet-machine figure plus the measured 44+ min external-drive/load caveat. | corrected guide text | `grep -n "minutes" docs/guides/startup-and-setup.md` | a wall-clock claim without a stated measurement context must not appear in entry docs |
| `ERG-SIDECAR-SCRATCH-MIN-1` | completed | Minor | Root-level `sidecar_*` scratch | Closed 2026-08-31 (agent-ergonomics round-2 lane): all 19 `sidecar_*` scratch scripts/logs archived to local-only gitignored `_agent_erg_archive_2026-08-31/`; owner may delete permanently at will. | archived scratch | `ls sidecar_* 2>/dev/null` returns nothing | a root-level scratch script that no doc references must not persist past its task |
