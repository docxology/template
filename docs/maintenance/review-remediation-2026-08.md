# Review & Improvement Record — 2026-08-12

> Parallel-agent comprehensive review of `docxology/template` (infrastructure/,
> scripts/, docs/, and all 24 public exemplar projects), executed as Hermes herdr
> agents with strict disjoint file ownership, and released as **v3.7.0**.
>
> This record captures what was reviewed, what was changed, the verification
> evidence, and — most importantly — the reusable lessons and incidents from
> running a large parallel-agent campaign on this repo, so future sessions do
> not repeat the mistakes.

---

## 1. Scope & method

- **Auditor-first baseline.** Before dispatching any agent, the repo's own
  audit tooling was run in the parent session (`scripts/audit/*`,
  `scripts/docgen/*`, ruff, mypy, the regression tier). All were green at HEAD
  `e8c8cd68e`. This established ground truth in seconds and let agents focus on
  real gaps instead of re-deriving facts.
- **Phase 1 — three parallel herdr Hermes agents** with disjoint ownership:
  - `infra-perf` → `infrastructure/**`, `scripts/**`, `tests/infra_tests/**`
  - `exemplars` → `projects/**` (24 exemplar read-everything review)
  - `docs-tests` → `docs/**`, root signpost files, documentation/validation tests
- **Phase 2 — twenty-four per-exemplar agents**, one herdr tab per exemplar, each
  strictly confined to its own `projects/templates/<name>/**` tree.
- Each agent ran the repo's real verification commands and left its edits
  **uncommitted** for the parent to inspect, verify, and commit (no agent
  pushed).

---

## 2. What was found & changed

### Performance (P1)

- **Python 3.10 compat audit double-resolved every path.** `scan_python_310_compatibility`
  and `_display_path` each called `path.resolve()` per source file (~1000+),
  i.e. O(2N) filesystem syscalls. Under load in the release infra gate this
  caused `test_public_python_surface_is_python_310_compatible` to **time out**.
  Fixed by resolving each path exactly once in `_python_files_and_displays` and
  threading the pre-resolved relative display through. Public-surface suite now
  ~3.3s; a regression test pins repo-relative display paths.

### De-duplication (R6-class, shared-helper extraction — infra-internal only)

- `infrastructure/rendering/_output_text.py` → canonical `_process_output_text`,
  imported by docx/epub/mobi renderers (was duplicated in all three).
- `infrastructure/core/determinism.now_utc_iso` → canonical UTC-stamp helper;
  six duplicated `_now_utc`/`_now_utc_iso` bodies in publishing
  (static_site ×3, pypi upload, archival models, huggingface, osf) delegate to
  it; added to `__all__`.
- `infrastructure/validation/docs/consistency/_shared.blank_content` → canonical
  blanking helper shared by `blank_fences` and `cross_link_lint`.
- Removed two thin `_normalize_whitespace` wrapper methods (core `_validation`,
  llm `sanitization`) in favour of existing `normalize_whitespace`.
- `scripts/publish/upload_{gold_refinement,template_project}.py` → dropped
  duplicated `_load_dotenv` wrappers; delegate to
  `infrastructure.core.credentials.ensure_dotenv_loaded`.
- **Rule applied:** only infrastructure-internal duplication was de-duplicated.
  Cross-exemplar duplication (e.g. `template_advanced_literature_review` ↔
  `template_literature_meta_analysis`) is a *sanctioned standalone-safe mirror*,
  not a dedup target — unifying it would break the standalone contract.

### Thin orchestration

- Extracted `scripts/gates/status_freshness.py` parsing/findings logic into the
  new tested module `infrastructure/validation/status_freshness.py`; the gate is
  now a 23-line thin CLI. Fixed the forward reference in
  `scripts/docgen/status_evidence.py` to import `parse_status_rows` from the new
  module. Added function-level tests + README gate entry.

### Documentation

- Linked the archived `docs/maintenance/exemplar-backlog-history.md` from the
  maintenance hub and added two reachability regression tests
  (`tests/infra_tests/documentation/test_maintenance_doc_reachability.py`): the
  hub must link the archived record, and every tracked `.md` guide in
  `docs/maintenance/` must be linked from the hub.

### Per-exemplar improvements

- **template_textbook** — the exemplar's `test_contracts.py` carried two
  overlapping generations of tests plus broken **tuple-membership assertions**
  (`assert "<substr>" in (<tuple>)` checks element-equality, not substring),
  making the suite red, and a stale `REQUIRED_SECTION_HEADINGS` claim. Fixed:
  consolidated `test_contracts.py` (red → green; 232 tests total) <!-- noqa: drift-counts -->, corrected the
  4 tuple-membership assertions to per-element `any(...)` matching, added
  config-shape and audit negative-control tests, corrected the source-bound
  `claim_ledger.yaml` value (9 → 5, matching `constants.py`), documented the
  `contracts` module, fixed manuscript figure-path references (`../` → `../../`),
  and hardened `compare_config_shapes` (empty-vs-one-empty mapping-list drift)
  and `numeric_fact_receipt` (fail-closed receipt instead of raising).
- **template_literature_meta_analysis** — +296 lines tests-only <!-- noqa: drift-counts -->
  config-validation coverage (search engine toggles, hypothesis/sampling/llm/
  knowledge-graph/reproducibility/fulltext categories, `check_config_health`,
  load-error paths) plus `Corpus.summary()` and `filter_by_year` range-guard
  tests. All 1207 tests pass. <!-- noqa: drift-counts -->
- The other 22 exemplars were reviewed read-everything and found healthy (no
  stubs — all `pass`/`None`/`NotImplementedError` are documented fallbacks or
  intentional fail-loud gaps; suites green; docs consistent). No changes were
  warranted.

---

## 3. Verification evidence

Exact gates that were green at release (`v3.7.0`, `dfe673749`):

- `uv run ruff check infrastructure scripts tests/infra_tests docs` → All checks passed
- `uv run python -m infrastructure.project.public_scope source-paths | xargs uv run mypy` → no issues in 1536 files
- Combined touched infra suites → **2492 passed, 2 skipped, 44 deselected** <!-- noqa: drift-counts -->
- `uv run pytest tests/regression/ -q --no-cov --timeout=120` → 55 passed <!-- noqa: drift-counts -->
- `template_textbook` suite → 232 passed; `template_literature_meta_analysis` → 1207 passed <!-- noqa: drift-counts -->
- All audit gates: `check_public_template_contract --strict`, `check_template_drift --strict`,
  `check_tracked_all`, `check_tracked_generated_artifacts`, `check_tracked_secrets`,
  `check_claim_bindings`, `counts --check`, `verify_no_mocks` → exit 0
- `lint_docs` → 269 mermaid, 0 broken

**Note on the full infra gate:** an end-to-end `stage_01_test.py --infra-only
--profile release` run reports one persistent "failure" classified by the gate as
a known numerical-stability `RuntimeWarning: overflow encountered in exp` in
`test_stability.py` (documented in `STATUS.md`), plus an occasional LaTeX test
flake under extreme concurrent load (`test_compile_latex_recovers_from_truncated_first_pdf`,
which passes in isolation). Neither is a regression from this review.

---

## 4. Incidents & lessons (reusable)

These are the hard-won operational lessons from running a large parallel-agent
campaign on this repo. Future sessions should read this before dispatching.

### 4.1 Capture pre-existing uncommitted edits at session start (critical)

- A user had an uncommitted manual edit to
  `projects/templates/template_active_inference/manuscript/05_methods_analytical.md`.
  During Phase 1 an agent's `git restore <dir>` clobbered it.
- **Lesson:** before any agent writes, run `git status` and save a byte-exact copy
  of every pre-existing uncommitted diff. It is the only reliable recovery source.
  The edit was restored byte-identically from the session-start diff.
- **Mitigation that belongs in every brief:** a "do NOT touch `<file>`" line in
  *every* agent's brief (not just the owning agent's).

### 4.2 Verify every agent's self-report (never trust "done")

- The `template_textbook` agent reported complete while its suite was **red**
  (4 broken assertions). The orchestration skill's rule — *verify the
  self-report, don't trust it* — caught it. The parent must re-run the suite and
  read `git diff` for every agent.
- A child also reported "did NOT move `status_freshness`" when it in fact had,
  leaving a dangling import in `scripts/docgen/status_evidence.py`. Fixed by
  re-checking imports directly. **Always re-check imports myself.**

### 4.3 Halt an agent fleet decisively when it re-fires

- After Phase 2's first pass completed, the herdr server **re-fired the 24-agent
  fleet**. Multiple agents then collided on `template_textbook` (duplicate test
  names, `FileExistsError`, overlapping tuple-membership edits), making the suite
  red.
- `agent prompt /interrupt` and `/exit` were unreliable for stopping agents;
  `send-keys` Ctrl+C needed positional syntax that errored.
- **Effective halt:** terminate the hermes processes bound to the fleet panes via
  `kill <pid>` (identified by process start-time bucket), taking care **not** to
  kill the parent session or gateway. Then revert any partial/colliding working-tree
  edits to the last known-green committed state.
- **Lesson for the future:** once a per-exemplar pass returns green and is
  committed, stop the fleet (or disable agent re-fire) before starting any new
  work, so agents cannot edit an already-completed tree.

### 4.4 Ownership by subtree boundary is the safe parallelism shape

- 3 agents on one shared tree required cautious disjoint top-level partitions.
- For `projects/templates/*`, giving each exemplar its own tab+agent makes the
  filesystem boundary the ownership boundary — zero cross-boundary edits occurred
  across all 24 agents (verified: `git status` showed changes only under the
  owning exemplar's own tree).

### 4.5 Mechanical dispatch must be a script

- Creating N tabs, starting N agents, `/yolo` on N, submitting N briefs = 4N herdr
  calls. Script them with a `while read n pid` loop over a pane→name map. This
  saved many round-trips for the 24-agent fan-out.

### 4.6 herdr agent-name constraints

- Agent names are limited to 1–32 chars, `[a-z0-9_-]`. Long exemplar names
  (`template_advanced_literature_review` = 33 chars) fail `agent start` with
  `invalid_agent_name`. Use a short alias (e.g. `advlit`) and keep the full name
  in the brief. After the start loop, re-list and confirm N agents are present
  (a failed start leaves the pane at a bare shell prompt).

### 4.7 Model timeout under long reasoning

- The agent model occasionally hit a gateway idle-timeout
  (`Broken pipe` during a long thinking phase). Mitigation: raise the model's
  `stale_timeout_seconds` (e.g. 900) or use a faster model for pure review.

---

## 5. Release

- Version bumped **3.6.0 → 3.7.0** (`pyproject.toml`, `CITATION.cff`, `uv.lock`,
  `CHANGELOG.md`). `[Unreleased]` folded into `[3.7.0] - 2026-08-12`.
- Tag `v3.7.0` created and pushed; GitHub release created with notes.

---

## 6. Related

- [`review-remediation-2026-07.md`](review-remediation-2026-07.md) — the prior
  (July 2026) adversarial review record (43 findings confirmed, 3 refuted).
- [`regression-testing.md`](regression-testing.md) — the claim-binding regression
  tier that guards source-bound values like the textbook heading-count fix.
- [`release-boundary.md`](release-boundary.md) — why root `v3.x.y` tags and the
  standalone publication lane are distinct release surfaces.
