# AUDIT — 2026-08-30 — lane report (health-gate + exemplar drift lane)

Lane: scoped audit-and-improve lane (herdr fleet; the lane that ran 2026-08-30 14:41-18:30 PDT)
Repo: /Users/4d/Documents/GitHub/template (symlink -> /Volumes/external_drive/Git/template), branch main @ ecdab23db
Note: the generic filename AUDIT_2026-08-30.md was concurrently claimed by a sibling lane's report; this lane's report lives here to avoid clobbering it.

## Session context (verified)

- Working tree was ALREADY dirty before this lane's work: 51 dirty paths (in-flight sibling refactor centralizing manuscript-config path resolution via infrastructure.core.project_paths.resolve_manuscript_config_path, plus untracked template_formal AGENTS.md files). This lane did NOT commit and did NOT touch those files.
- Concurrent sibling gates were live: two other stage_01_test.py --infra-scope pipeline-smoke processes (PIDs 27747, 37098) on this same repo, a docxology coverage gate, a MetaInformAnt suite — all on one external drive (load 6-9 on 14 cores, ~8500 disk tps). A sibling lane was also concurrently repairing templates/template_textbook while this lane audited.
- Mid-session a sibling lane overwrote the generic-name audit file; both reports are preserved under distinct names.

## Findings

### Critical

F1. infrastructure/core/health.py crashes (unhandled TimeoutExpired) when git is slow — the unified health gate is unusable on this checkout under load.
- Evidence: infrastructure/core/health.py:164-185 (_repository_state) runs git rev-parse HEAD and git status --porcelain with timeout=30 and no TimeoutExpired handling; call site at health.py:327.
- Verified live: uv run python -m infrastructure.core.health died with a subprocess.TimeoutExpired traceback on git status --porcelain (>30s) on this repo. Direct latency measurement during this audit: git status --porcelain --untracked-files=no took 116.6s under fleet load (rev-parse HEAD: 0.6s) — the untracked-file scan the gate actually runs is slower still, so the 30s timeout is the common case here, not a tail risk.
- Impact: the aggregate quality gate advertised in AGENTS.md cannot run on slow-volume/loaded checkouts — fail-crash instead of fail-soft.

F2. Fleet hazard: three simultaneous pipeline-smoke stages on one checkout (verified above). Not a code defect; recorded because it invalidates naive red/green gate reads and directly causes F1. Recommendation: serialize repo-wide gates across herdr lanes (repo-level lock or lane scheduling).

### Major

F3. Gate runtimes under contention are extreme (baseline measurement): pipeline-smoke took 2649.6s (~44 min) in this session's concurrent fleet run; single foreground pytest invocations exceeded 420s. Environmental; any CI/agent design assuming minutes-scale local gates breaks here.

F4. infrastructure/core/health_benchmark.py:264 uses timeout=30 for its own git probing (same pattern as F1). Not exercised live (requires clean checkout); flagged by inspection. Same fix class if touched; left unmodified to keep this lane's diff minimal.

### Minor

F5. Root .coverage, coverage-infra.xml, htmlcov/ present — verified gitignored (absent from git status). Hygiene only.

F6. TODO/FIXME scan — no unresolved code-level TODO/FIXME markers in infrastructure/ Python source (lexical scan matched only doc/contract filenames); root TO-DO.md is contract-formatted with stable IDs; 4 rows correctly marked blocked-external.

## Fixes applied by this lane (all verified; nothing committed)

FIX-1 (F1): infrastructure/core/health.py — wrapped the _repository_state(repo_root) call site in try/except subprocess.TimeoutExpired -> commit_before, clean_before = None, None, with an explanatory comment. Provenance is reported unknown instead of the health report dying. Necessity verified by direct measurement (F1: 116.6s tracked-only status vs 30s timeout). Verified: uv run ruff check infrastructure/core/health.py -> All checks passed (before and after); uv run ruff format --check -> already formatted. mypy was started but did not finish under contention; the edit is type-neutral.

FIX-2 (drift, template_pitch_deck): 5 strict-drift warnings -> 0.
- docs/AGENTS.md:6 and docs/README.md:40 broken ../manuscript/AGENTS.md links corrected to manuscript/AGENTS.md (this exemplar keeps its manuscript under docs/manuscript/).
- docs/manuscript/00_abstract.md:14 and docs/manuscript/03_content_and_validation.md:5 ../../template_template/ corrected to ../../../template_template/ (both targets verified to resolve to the real sibling exemplar).
- Stale PUBLISHING-STATUS block in README.md regenerated with the repo's own generator: uv run python -m infrastructure.publishing.status_report --project projects/templates/template_pitch_deck --write -> "Updated publishing-status block". (The regeneration interacted with an in-flight sibling rename manuscript/ -> docs/manuscript/ also present in the tree; the block reflects current config and passed the final drift run.)

FIX-3 (drift, template_textbook): repaired the ../../../docs/ dead-link cluster in docs/manuscript/questions/part_{I,II,III}/{AGENTS,README}.md (6 files; links now point at the project README, target verified). A sibling lane was concurrently repairing the same exemplar's remaining ~34 shallow-link warnings; this lane stopped editing that project on collision detection to avoid double-edits, and claims only its own 6-file fix.

## Gate results — before/after

Before:
- python -m infrastructure.core.health -> crash (subprocess.TimeoutExpired traceback). Root cause fixed by FIX-1.
- check_template_drift.py --strict (full) -> 5 [warn] on template_pitch_deck + 40 [warn] on template_textbook.
- Stage 01 pipeline-smoke baseline: completed in 2649.6s under 3-way sibling contention, 1 failure — test_discover_projects_finds_templates hit a pytest-timeout mid tomllib.load (disk starvation), an environmental timeout, not an assertion failure.

After (scoped, post-fix):
- ruff on infrastructure/core/health.py: PASS.
- Scoped strict drift: [warn] count templates/template_pitch_deck = 0; templates/template_textbook = 0 (grep -c over the two --project runs; /tmp/final_drift.txt).
- Full audit-gate sweep (ran to completion): check_tracked_all -> projects/fonds/tools/rules all clean; verify_no_mocks --inventory -> dependency_replacement 0, status clear (415 imports classified); check_tracked_secrets -> no high-confidence credentials in tracked files; check_tracked_generated_artifacts -> no violations.
- Smoke not re-run post-fix: FIX-1/FIX-2/FIX-3 change no pipeline-test selection, and the fleet remained saturated; honest verdict is "same selection, ruff-verified edits, drift gate green for the repaired exemplar" rather than a claimed smoke re-pass.

## Honesty notes

- mypy on the edited health.py: not verified this session (timed out under load); edit is type-neutral.
- FIX-1 is verified by necessity measurement + ruff, not by a quiet-window health-gate run.
- template_textbook's full 40-warning cleanup was NOT this lane's work beyond the 6-file cluster; sibling lane owns the rest.
- Nothing committed; nothing pushed; sibling diffs untouched. Files changed by this lane: infrastructure/core/health.py; template_pitch_deck docs/AGENTS.md, docs/README.md, docs/manuscript/00_abstract.md, docs/manuscript/03_content_and_validation.md, README.md (regenerated block); template_textbook docs/manuscript/questions/part_{I,II,III}/{AGENTS,README}.md; plus this audit file.
