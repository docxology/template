# Review Remediation Plan — 2026-07-02

> Source: a multi-lens adversarial review of `docxology/template` at HEAD
> `890abb6a` (9 dimensions × read-only finders, each finding verified against
> HEAD). 43 findings confirmed, 3 refuted. This plan captures the items that
> need design or multi-step work; the safe, bounded fixes were applied in the
> same session (see **Shipped this session** below).
>
> Every open item carries an **Acceptance** line — a single tool-probe that
> flips it from open to done. Pick a row, satisfy its acceptance line(s), open
> a PR. Severity is *impact*, not convergence.

## Shipped this session (2026-07-02, [Unreleased])

These were confirmed defects fixed directly and verified (`./run.sh` health
gate went **FAIL → PASS 11/11**; regression tier 55/55; drift `--strict` exit 0):

- **CRITICAL — CI docs-lint RED on clean HEAD.** Four tracked exemplar `data/`
  dirs (`template_autoscientists`, `template_sia`, `template_template`,
  `template_textbook`) had `AGENTS.md` but no `README.md`, tripping the
  doc-pair rule. Added the four `README.md` siblings. `lint_docs --quiet` → 0.
- **CRITICAL — stale `docs/_generated/exemplar_roster.md`.** Committed doc
  showed `template_search_project` at 19 test files; real count is 24.
  Regenerated the roster + `template_manifest.json`. `--check` → OK.
- **CITATION.cff missing DOI** for `template_eda_notebook` and
  `template_methods_paper` (generator flagged the drift). Added the concept
  DOI to both; regenerated `publication_records.md` → in-sync.
- **Health CLI mypy gate** invoked the `mypy` console-script, which breaks when
  the venv is relocated; and the CLI swallowed all failure diagnostics.
  Switched the gate to `python -m mypy` (matches the bandit gate) and made
  `main()` print each failing gate's captured tail to stderr.
- **Drift gate `check_docs_hardcoded_counts` scanned untracked local dirs**
  (`projects/codomyrmex`), so `--strict` reddened off-CI. Now intersects the
  filesystem walk with `git ls-files` (falls back to prior behavior when git is
  unavailable). Added a no-mocks test with a real git repo. Restores CI parity.
- **Upload scripts' dead `_load_dotenv`.** Both `scripts/publish/upload_*.py`
  guarded a non-existent `infrastructure.core.config.dotenv` import behind a
  silent `except Exception: del exc`, so the duplicated inline parser always
  ran. Now delegate to the canonical
  `infrastructure.core.credentials.ensure_dotenv_loaded`.
- **Doc-drift corrections** across `CLAUDE.md`, `STATUS.md`, `CHANGELOG.md`,
  `TO-DO.md`, `docs/guides/getting-started.md`: regression tier is 15
  exemplars / 55 tests (was described as "scaffold-only / 3 tests / 10
  exemplars / 36 tests"); the `mypy --strict passes` claim replaced with an
  accurate CI-config statement; `run_matrix` needs `run.config` first; the
  "authoritative file list" overclaim softened; first-run command aligned
  across the two entry docs (core-only).

## Shipped 2026-07-02 (second pass — bounded, tested)

Implemented and verified the same day (full gate suite + full infra suite +
regression tier green): **R1** (CI `test-regression` job), **R2** (skills
discovery scoped to `projects/templates`), **R3** (`.agents/skills` lane
validation test), **R4** (bandit `exclude_dirs` gains `projects/ongoing`),
**R11** (OSF uploader threads `osf_node_id` for idempotency), **R12** (explicit
`<a id>` anchors on the two emoji AGENTS.md headings the README deep-links),
**R15** (pinned `uv` installer), **R16** (always-on LOW shell-injection bandit
sweep in CI), **R17** (B603 justification corrected to name the real control).
Detailed entries below are retained for provenance; their acceptance lines are
now satisfied. One follow-up requires a repo-admin action, not code: **add the
new `Regression Tier` check to branch-protection required checks** so the
"cannot merge until it passes" claim is literally enforced.

At that checkpoint, the remaining items (R5–R10, R13, R14, R18) were genuine
multi-step refactors or design changes, so each was reserved for focused work
rather than being bundled into one large push. The sections below record when
those items subsequently shipped.

## Shipped 2026-07-02 (third pass — the deferred refactors, via worktree-isolated workflow)

Implemented in 5 parallel worktree-isolated agents, reconciled + centrally
re-verified in the main loop, full infra suite green: **R5** (all `mypy --strict
infrastructure` errors fixed — 0 remaining — AND `infrastructure.orchestration.*`
removed from `ignore_errors` with CI-config mypy green), **R6** (helper dedup —
`lazy_session`/`iter_bundle_files` in a shared `_adapter_http`, numeric-cell
helpers single-homed, `read_json_object`/`load_yaml_mapping`/`relative_or_self`
in a new `infrastructure/core/files/serialization.py`; `secure_run._load_yaml_mapping`
deliberately kept — different error semantics), **R7** (operations catalog now
discovers single-file CLIs, 18→31 ops), **R8** (arXiv tarball pulls rendered
`.tex` + honest references-only framing), **R9** (all 15 repro manifests declare
a present output-artifact), **R13** (`_pdf_title_page.py` split 774→192-line
facade + 4 modules), **R14** (documentation-index gained 12 omitted docs),
**R18** (MCP `invoke_cli` capability tiering — mutating ops refused by default).

**R10 (benchmark determinism) attempted and REVERTED — now with a sharper open
spec.** The mechanical fix (remove wall-clock `execution_time` from the tracked
`performance_benchmark.json` so it is byte-reproducible) is downstream-coupled:
`projects/templates/template_code_project/src/manuscript_variables.py:301` reads
`execution_time` to populate `BENCHMARK_AVG_TIME`, rendered as "**{{...}} μs**"
in `manuscript/05_experimental_setup.md`. Removing the field makes the manuscript
render "N/A μs". So R10 cannot be a drive-by: the real question is *what should a
byte-reproducible exemplar present for an inherently wall-clock quantity* — either
(a) reword the manuscript so the μs figure is explicitly environment-dependent
and not a pinned reproducible fact, or (b) drop the numeric claim and describe
the benchmark qualitatively. Both are content decisions on a public exemplar,
left open for a maintainer. Acceptance unchanged; add: the manuscript must not
regress to "N/A μs".

## Shipped 2026-07-11 (R10 closure — deterministic benchmark boundary)

**R10** is now shipped. The code exemplar still executes and logs real
wall-clock timing as an untracked runtime diagnostic, while both tracked
benchmark reports serialize only deterministic inputs, objective values,
checks, and policy metadata. The canonical benchmark figure uses deterministic
work units and convergence iterations instead of host timing. Manuscript source
now states that boundary directly and no longer injects a microsecond value (or
an `N/A μs` fallback) as a reproducible fact. Regression coverage runs the JSON
report and PNG figure twice and asserts byte equality; the focused closure suite
passed 39 tests.

## Open — High

> R1 was shipped in the second pass above; retained for provenance. Nothing
> in this section is currently open.

### R1 · Wire the claim-binding regression tier into CI — ✅ SHIPPED
The 15-exemplar / 55-test regression tier is the repo's anti-fabrication
harness, but no CI job or pre-push hook runs it — `docs/maintenance/regression-testing.md`
asserts "the PR cannot merge until the test exists and passes," which is not
enforced. The infra CI job runs `tests/infra_tests/`, not `tests/`.
- **Scope**: add a `test-regression` job to `.github/workflows/ci.yml` running
  `uv run pytest tests/regression/ -q --no-cov`, tolerating a clean-checkout
  exit-5 (0 collected) so a future empty tier does not hard-fail; optionally
  mirror in a `pre-push` hook.
- **Acceptance**: `grep -n "tests/regression" .github/workflows/ci.yml` shows a
  real invocation (not just a comment); a PR that mutates a pinned value goes
  red in CI.

## Open — Medium

> All of R2–R9, R11, R12 were shipped in the second/third passes above (see
> `## Shipped 2026-07-02` sections), and R10 shipped in the 2026-07-11 closure
> pass. The detailed entries below are retained for provenance. No code item in
> this repo-wide R1–R18 list remains open; the branch-protection admin action
> noted above remains external to the repository.

### R2 · Scope skills discovery + `infrastructure.skills check` to tracked paths — ✅ SHIPPED
`infrastructure/skills/discovery.py` `DEFAULT_SKILL_SEARCH_ROOTS` includes a
bare `"projects"`, so `discover_skills` walks untracked local dirs
(`projects/codomyrmex` → ~270 private skill names) — the documented
`uv run python -m infrastructure.skills check` fails locally and any
manifest/index regeneration would bake private names into tracked public files.
Same class as the drift-gate fix already shipped, but the fix regenerates
`docs/_generated/skills_index.md`, `.cursor/skill_manifest.json`, and the MCP
`list_skills` surface, so it needs a careful multi-surface commit.
- **Acceptance**: on a checkout with a sibling untracked `projects/x`,
  `python -m infrastructure.skills check` exits 0 and the manifest contains
  zero non-tracked skill names (`git ls-files` intersection).

### R3 · Give the `.agents/skills` exemplar lane gate coverage — ✅ SHIPPED
The 15 `projects/templates/*/.agents/skills/*/SKILL.md` (the Hermes/agentskills
lane) are excluded from every discovery/validation surface; yesterday's
YAML-quoting regression in one of them would not have been caught. Do **not**
merge them into `infrastructure.skills` discovery (the two-lane split is
intentional, CLAUDE.md:159-166) — add a dedicated validation test.
- **Acceptance**: a new test parses every `projects/templates/*/.agents/skills/*/SKILL.md`
  frontmatter and asserts required keys + that referenced commands exist; it
  fails when a SKILL.md frontmatter is malformed.

### R4 · Bandit `exclude_dirs` denylist → tracked-scope — ✅ SHIPPED
`bandit.yaml` `exclude_dirs` is a hand-maintained name denylist that has already
drifted from `NON_RENDERED_SUBDIRS` (`projects/ongoing` missing), so the
pre-push security gate scans thousands of local-only files.
- **Scope**: (a) immediate — add `- "projects/ongoing"` to honor the stated
  sync contract; (b) structural — scope the pre-push/CI bandit scan to
  public/tracked paths instead of denylisting names.
- **Acceptance**: bandit run on a checkout with a sibling untracked project
  reports 0 findings from that project; `exclude_dirs` matches
  `NON_RENDERED_SUBDIRS` or the denylist is removed in favor of a tracked scope.

### R5 · mypy strict-typing debt (make the config honest and shrink it) — ✅ SHIPPED
The public source scope now passes the configured mypy policy with zero errors,
all package-wide `ignore_errors` overrides are removed, and the former baseline
file is deleted. The compatibility-named ratchet command now fails on any error.
- **Acceptance**: `uv run python scripts/gates/mypy_ratchet.py $(uv run python
  -m infrastructure.project.public_scope source-paths)` exits zero.

### R6 · De-duplicate verbatim helper bodies in infrastructure — ✅ SHIPPED
AST-hash scan found `_get_session` ×5 and `_iter_files` ×3 in publishing
adapters, 4 numeric-cell helpers copied between `evidence_registry.py` and
`evidence_registry_collectors.py`, plus `_rel` ×3, `_read_json_object` ×3,
`_load_yaml_mapping` ×2. Multi-module refactor touching the three-tree mirror.
- **Acceptance**: the duplicated bodies live in one shared module each; the
  AST-hash duplicate scan reports 0 for those names; all touched-module tests
  green and coverage floors held.

### R7 · Operations catalog + MCP reach single-file CLIs — ✅ SHIPPED
`operation_registry` treats a package as invocable iff it has `__main__.py`, so
documented single-file CLIs (`infrastructure.core.health`,
`infrastructure.project.public_scope`, `documentation.generate_glossary_cli`,
`reporting.release_readiness`) are absent from `list_operations` and refused by
MCP `invoke_cli` — contradicting the "every discovered capability reachable"
claim.
- **Acceptance**: `list_operations` includes the four single-file CLIs;
  `invoke_cli` accepts them; the capability-surfaces doc's reachability claim is
  true by probe.

### R8 · arXiv submission tarball completeness (or honest naming) — ✅ SHIPPED
`prepare_arxiv_submission` globs `.tex/.bib/.cls/.bst` from `manuscript/`, but
template manuscripts are Markdown compiled to `.tex` at render time, so the
tarball ships only `references.bib`. Not wired into any pipeline (tests only),
so nothing auto-ships it — but the README presents it as upload-ready.
- **Acceptance**: either the tarball includes the rendered `.tex` (built from
  `output/`) or the function/README renames it to a clearly-incomplete
  "references-only" artifact; a test asserts the tarball contents match the
  documented promise.

### R9 · Repro bundle declares real outputs for all 15 exemplars — ✅ SHIPPED
`scripts/runner/repro_bundle.py build` yields a manifest with **no** `output-artifact`
entries for 5/15 exemplars (`template_active_inference`,
`template_literature_meta_analysis`, and 3 others) — it "verifies" zero
artifacts.
- **Acceptance**: every public exemplar's repro manifest declares ≥1
  `output-artifact`; `... verify <manifest>` checks a non-empty artifact set.

### R10 · Deterministic benchmark artifact — ✅ SHIPPED
The canonical reproduce command rewrites
`template_code_project/output/reports/performance_benchmark.json` with
wall-clock timing + a human timestamp, so the tracked artifact cannot reproduce
byte-identically.
- **Acceptance**: re-running the reproduce command leaves the tracked JSON
  byte-identical (timings moved out of the tracked file, or timestamp pinned via
  the existing deterministic helper à la steganography).
- **Closure**: tracked benchmark JSON omits wall-clock and timestamp fields;
  runtime timing remains diagnostic-only, the manuscript makes no pinned
  microsecond claim, and two-run JSON/PNG byte-equality tests pass.

### R11 · OSF uploader idempotency (real-publish hardening) — ✅ SHIPPED
`upload_osf` builds `OSFConfig(title=...)` with no `node_id`, so every
`--commit` re-run creates a duplicate OSF node. (Bounded to the opt-in publish
path; safe-fix but deferred to the publishing-hardening batch.)
- **Acceptance**: thread `osf_node_id` end-to-end (`UploadTargets` →
  `upload_osf` → `_resolve_targets`); a second `--commit` updates the existing
  node; a dry-run test asserts the node id is passed through.

### R12 · README GitHub-anchor deep links — ✅ SHIPPED
README "Choose Your Path" links to `AGENTS.md#core-architecture` /
`#configuration-system`, but those headings are emoji-prefixed, so GitHub's
slugger produces different anchors and the links dangle. The repo renders on
GitHub (no mkdocs `attr_list`), so `{#custom-id}` is not a fix.
- **Acceptance**: links point at GitHub's real slugs (e.g.
  `#%EF%B8%8F-core-architecture` per GFM slugging) and resolve when clicked;
  ideally add an anchor check to `lint_docs`.

## Open — Low

> All of R13–R18 were shipped in the second/third passes above; retained for
> provenance. Nothing in this section is currently open.

### R13 · Split `infrastructure/rendering/_pdf_title_page.py` (774/800 lines) — ✅ SHIPPED
Largest Layer-1 module, 26 lines from the advisory WARN threshold. Pre-emptive;
no defect on HEAD.
- **Acceptance**: module < 700 lines after extracting a cohesive helper group;
  `module_line_count_check` still green; rendering tests + byte-stable output.

### R14 · `docs/documentation-index.md` completeness — ✅ SHIPPED
Index omits ~11 substantive tracked docs. The overclaim was softened this
session ("curated map"); optionally re-add the missing entries to restore it as
a near-complete inventory.
- **Acceptance**: the 11 named docs appear in the index, or the doc explicitly
  states its curation scope.

### R15 · Pin the `uv` bootstrap installer — ✅ SHIPPED
`scripts/shell/shell_bootstrap.sh` pipes an unpinned `https://astral.sh/uv/install.sh`
to `sh` automatically from `run.sh`/`secure_run.sh` — a floating remote installer
against the repo's pin-everything posture.
- **Acceptance**: the installer URL is version-pinned (e.g. `UV_VERSION`), or
  the auto-install prompts before piping remote script to a shell.

### R16 · Always-on shell-injection bandit sweep — ✅ SHIPPED
The MEDIUM+ bandit gate passes constant-string `shell=True` (B602/B604/B605 are
LOW); the LOW sweep is manual-only and excludes `projects/`.
- **Acceptance**: a `-t B602,B604,B605,B609 --severity-level low` pass over all
  three trees runs in the CI security job + pre-push hook.

### R17 · Correct the bandit B603 justification comment — ✅ SHIPPED
`bandit.yaml` B603 says run-varying inputs are "validated by
`infrastructure.core.security`." That module *does* exist (the review's
"module missing" evidence was refuted), but the argv-building call sites are
actually guarded by `shell=False` + `validate_project_slug`
(`infrastructure.orchestration.discovery`). Rewrite the comment to name the true
control. *(Deferred deliberately: the finding's core evidence was partially
wrong, so verify the real control per call site before editing.)*
- **Acceptance**: the B603 comment names the actual control and cites a real
  symbol that a grep confirms exists.

### R18 · MCP `invoke_cli` capability tiering — ✅ SHIPPED
`invoke_cli` exposes credentialed/paid/network-mutating CLIs with full env
inheritance and no read-only vs mutating tier. Design-level hardening for the
agent surface.
- **Acceptance**: `OperationDescriptor` carries an `effect` tier; `invoke_cli`
  refuses mutating/paid ops unless explicitly enabled; a test asserts a paid
  uploader CLI is refused by default.

## Refuted (recorded so they are not re-surfaced)

- "MCP serverInfo name/version stale vs pyproject" — the names differ by design
  (server identity vs package identity); not a defect.
- "Unified health CLI is CI-informational-only / decorative" — it returns a
  real non-zero exit on failure and is wired; framing refuted.
- "Opt-in `security_scan.py` fails on out-of-scope content" — reproduces, but
  it is opt-in and not a default gate; not a trust-anchor break.
