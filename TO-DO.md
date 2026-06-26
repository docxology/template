# Repo TO-DO - active backlog

> **Design ethos:** modular, intelligent, functional, logged, tested, and
> documented. Real methods only; never mocks or fakes. Every release ships with
> green tests and accurate docs.

This file tracks live work after the `v3.4.0` release (latest published release:
`v3.4.0`, tagged 2026-06-12). Historical release detail belongs in
[`CHANGELOG.md`](CHANGELOG.md); generated counts and project rosters belong in
[`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md) and
[`docs/_generated/active_projects.md`](docs/_generated/active_projects.md).

---

## Live state snapshot

Refreshed on **2026-06-13** on branch `codex/template-exemplar-forkability`
after the forkability and verifier-first roadmap pass. Re-run the
commands in the **Source** column before copying any number into prose; live
counts belong in [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md), not
hard-coded here.

| Gate or surface | Current value | Source |
| --- | --- | --- |
| Package version | `3.4.0` | `pyproject.toml#[project].version` |
| Latest published release | `v3.4.0` (tagged + GitHub release published 2026-06-12; CHANGELOG `[3.4.0]` body) | `gh release list`, `git tag` |
| Public source scope | `infrastructure` plus nine public exemplar `src/` trees | `uv run python -m infrastructure.project.public_scope source-paths` |
| Public exemplars | `template_active_inference`, `template_autoresearch_project`, `template_autoscientists`, `template_code_project`, `template_newspaper`, `template_prose_project`, `template_sia`, `template_template`, `template_textbook` | [`docs/_generated/active_projects.md`](docs/_generated/active_projects.md) |
| Canonical generated facts | Importable infrastructure packages, infrastructure Python-module count, project-scope + publishing test collections, and per-exemplar coverage — all live-derived; do not hard-code here | [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md) (regenerate with `uv run python scripts/generate_counts.py --write`) |
| Open GitHub PRs | 0 open | `/opt/homebrew/bin/gh-axi pr list` |
| Docs lint status | links-only, consistency-only, and doc-pairs all clean (re-verified 2026-06-13) | `uv run python scripts/lint_docs.py --links-only --quiet --json`, `--consistency-only`, `--doc-pairs-only` |
| Mermaid lint status | clean with chunked batch rendering under the default total budget | `uv run python scripts/lint_docs.py --mermaid-only --quiet --json` |
| Release verification baseline | drift `--strict`, COUNTS/skills/exports gates, tracked-project/generated-artifact guards, docs-lint (links/consistency), reporting+evidence+repro suites (877), and the LLM suite (1244, live Ollama) all green at the v3.4.0 commit | `v3.4.0` release + local command history |

---

## Recently shipped

Keep this section short. Details live in release notes or archived audits.

- **AutoResearch reviewer-boundary closeout (2026-06-13, `[Unreleased]`):**
  closed `AR-REPORT-ERGONOMICS-1`, `AR-BENCHMARK-ERGONOMICS-1`, and
  `AR-SOURCE-LEDGER-2`. The loop now emits
  `output/data/autoresearch_evidence_overview.json`,
  `output/reports/autoresearch_evidence_overview.md`, and
  `output/data/benchmark_boundary.json`; the source-ledger contract validates
  ledger citekeys against BibTeX and manuscript citations, rejects invalid
  tiers/future dates, and prints offline age/tier summaries. Verified with
  `uv run pytest projects/templates/template_autoresearch_project/tests/ -q`
  (224 passed).
- **Template forkability + verifier roadmap pass (2026-06-13, `[Unreleased]`):**
  closed `TODO-REBASE-2` (live PR count is 0; active backlog restored instead of
  `_No open items_`), `REGRESSION-PIN-1` (the first real
  `template_code_project` regression pins now collect and pass with a mutation
  negative control), and `AI-VIZ-SPLIT-1` (`src/visualizations/figures.py`
  split into focused semantic and simulation modules while preserving the figure
  facade). `AI-SEMANTIC-FIXPOINT-1` is now closed: the shared fixed-point
  orchestrator drives manuscript variables, sheaf semantic outputs, and contract
  settlement; the selected fixed-point cluster passed 21 tests on 2026-06-13.
- **Generated-report web design (2026-06-12, `[Unreleased]`):** modernized the
  base HTML report/dashboard template (`infrastructure/reporting/html_templates.py`)
  with CSS design tokens, dark mode (`prefers-color-scheme`), WCAG-AA status
  contrast, fluid type, and a mobile breakpoint — template contract + deterministic
  output preserved (7 template + 875 reporting tests green).
- **Scoped-improvement sweep (2026-06-12, `[Unreleased]`):** closed all three
  freshly-scoped items. `WEBDESIGN-EXTEND-1` — extracted `html_templates.shared_css()`
  as the single design-token source; the pipeline report, interactive dashboard, and
  web renderer all now anchor to `--brand-1` + a `prefers-color-scheme` block (108
  tests). `LINKCHECK-PERF-1` — `link_audit_core` prunes excluded/gitignored dirs
  before descending + single-pass file reads (~15–28× faster; 303 link tests + a
  timed regression). `TEXLIVE-2026-BEAMER-1` — `latex_utils.compile_latex` tolerates
  the benign `\reserved@a` kernel warning when a valid PDF results (the beamer test
  now passes on TeX Live 2026; genuine failures still raise).

- **Backlog closeout + comprehensive review (2026-06-12):** closed `REPRO-VERIFY-1`
  (the repro bundle now fails closed on declared-but-absent outputs — a
  declared output absent at build rebases onto the project tree and `verify`
  returns `ok=False`; pinned by `tests/infra_tests/publishing/test_repro_bundle_absent_output.py`)
  and `EVIDENCE-CLAIM-1` (the claim-ledger candidate list gained an
  `output/data/*claims*.json` glob so the `template_autoresearch_project`
  exemplar's `autoresearch_claims.json` is ingested as claim nodes + `supports`
  edges; pinned by `test_ingest_claims_autoresearch_ledger_yields_nodes_and_supports`
  and `test_build_evidence_graph_ingests_real_autoresearch_ledger`). Shipped
  alongside a large multi-pass review (dead-code removal, `run.config` matrix
  runner, `SOURCE_DATE_EPOCH` determinism, the `canonical_facts.md`→`COUNTS.md`
  generator, exemplar-support-tier tagging, methods-plan gate, validation↔
  autoresearch decoupling, and an Ollama test-model fix). Full detail in
  [`CHANGELOG.md`](CHANGELOG.md).
- **Backlog sweep + RedTeam hardening (2026-06-08):** closed 6 backlog items —
  `PIPELINE-INCR-FLAG-1` (`--incremental` CLI flag on both entrypoints),
  `DASHBOARD-CLI-1` (release-readiness dashboard discoverable + subprocess test),
  `REPRO-MULTI-1` (`--all-public` multi-exemplar repro bundles),
  `PROSE-GATE-WIRE-1` (opt-in report-only prose gate in Stage 6, disabled =
  byte-identical), `SIA-HARNESS-2` (fixture/live separation tests + docs), and
  `LOG-SEP-CENTRAL-1` (33 banner literals routed through width constants + lint).
  Verified `TODO-REBASE-1`, `ARCH-CONFTEST-1`, and `AI-GATE-CACHE-1` already
  satisfied. A verifier-first RedTeam pass then fixed a real SIA fail-closed hole
  (`max_generations<1` returned a vacuous empty run) and closed five green-wash
  test gaps. Commits `33e5ca71`, `c8381d9a`. One out-of-scope finding logged as
  `REPRO-VERIFY-1`. `RELEASE-TAG-1` deferred (needs a clean tree + sign-off).
- **`v3.3.1` release train (2026-06-07):** completed Pandoc DOCX output (embed
  figures + resolve cross-references in `infrastructure/rendering/pipeline.py`),
  ran a deep per-exemplar quality pass across the eight tracked public templates,
  completed and cross-linked sidecar publication metadata for all nine public
  exemplars, and reconciled the generated project-scope collection count to 216.
  Full detail in [`CHANGELOG.md`](CHANGELOG.md).
- **`v3.3.0` release train (2026-06-07):** closed the three Medium backlog items
  (READFILE-SAFE-1, CI-MATRIX-DYNAMIC-1, LOG-CLEAN-1) and all five Major items
  (EVIDENCE-GRAPH-1, REPRO-BUNDLE-1, DASHBOARD-1, PLUGIN-STAGES-1,
  INCREMENTAL-PIPELINE-1) — the two pipeline-core features are opt-in/default-off.
  The shipped artifacts were re-verified on disk and under test on 2026-06-08
  (169 dedicated tests pass; no stubs). Full detail in
  [`CHANGELOG.md`](CHANGELOG.md). The genuine residual next-increments of these
  features are now tracked as new backlog items below (EVIDENCE-CLAIM-1,
  PIPELINE-INCR-FLAG-1, DASHBOARD-CLI-1, REPRO-MULTI-1, PROSE-GATE-WIRE-1).
- **Reference-existence + AI-writing infrastructure (2026-06-06):** new
  `infrastructure/reference/verification/` deterministic anti-hallucination gate
  (Crossref→OpenAlex/arXiv resolver, SQLite cache, offline-first) and
  `infrastructure/validation/content/ai_writing.py` AI-writing fingerprint
  detector (`validation.cli prose-quality`); wired into the `docs/prompts`
  workflows. Clean-room distillation of academic-research-skills ideas
  (CC-BY-NC-4.0); no code vendored.
- **Infra test parallelization (2026-06-06):** `pytest-xdist` + `-n auto` on the
  CI `test-infra` job cut each leg from ~892s to ~585s; suite verified
  parallel-safe; default `-v` dropped from `addopts`.
- **Docs accuracy sweep (2026-06-06):** audited `docs/` + every
  `infrastructure/*/{SKILL,README,AGENTS}.md`; corrected examples that cited
  methods/params/CLI flags/test paths that did not exist (every fixed command
  re-verified to resolve).
- **`v3.2.0` release train (2026-06-04):** DOCX/EPUB renderers + format toggles
  (FMT-BUNDLE-1), Active Inference validation spine v2 (AI-SPINE-V2),
  infrastructure coverage gaps rebaselined (COVERAGE-REBASE-1), GitHub
  supply-chain hardening (GH-PIN-1, GH-ACTIONLINT-1, GH-AUTOMERGE-1), and the
  XML parser policy (DEP-DEFUSEDXML-1). See [`CHANGELOG.md`](CHANGELOG.md).
- **`v3.1.0` release train:** SIA joined the public exemplar scope; Active
  Inference gained the first validation-spine tracks; docs signposting moved to
  `projects/templates/...`; public coverage orchestration was hardened. See
  [`CHANGELOG.md`](CHANGELOG.md).
- **Thermo-nuclear infra/docs audit (2026-06-08):** Waves A–E closed — doc contract,
  READFILE-SAFE-1 CLI, AGENTS v3.3 completeness, evidence-graph SUPPORTS/registry
  bridge, autoresearch validation split. Approve — see
  [`docs/audit/archived/thermo-nuclear-code-quality-2026-06-08.md`](docs/audit/archived/thermo-nuclear-code-quality-2026-06-08.md).
- **Thermo-nuclear remediation waves:** 2026-05-29 and 2026-05-30 blockers and
  branch deltas are closed. See
  [`docs/audit/archived/thermo-nuclear-code-quality-2026-05-29.md`](docs/audit/archived/thermo-nuclear-code-quality-2026-05-29.md)
  and
  [`docs/audit/archived/thermo-nuclear-code-quality-2026-05-30.md`](docs/audit/archived/thermo-nuclear-code-quality-2026-05-30.md).

---

## Active backlog

### PUB-PLATFORM-1 — Modular publishing adapters for sites and package distribution

- **Problem:** The publishing surface is currently split between Zenodo/GitHub DOI releases and a separate PyPI script path, while the broader site/app/content hosting targets are only documented.
- **Why it matters:** We need a single modular publishing story that can evolve from documentation into thin, testable adapters without coupling every host to the DOI workflow.
- **Smallest next step:** Add a template-level deployment registry and one thin adapter/test surface per target family, starting with PyPI/package publishing and static-site hosting.
- **Acceptance check:** The template docs point to a clear registry of first-class versus documented targets, and the codebase has a testable modular entry point for each supported publishing surface.
- **Out of scope:** Live credentials, destructive deploys, or service-specific wrappers that cannot be tested locally.

### AI-GATE-PERF-2 — Reduce active-inference gate runtime after correctness

- **Problem:** `template_active_inference` gate tests still have one heavy
  explicit roadmap/sheaf write path; clean-state fixed-point and gate setup now
  avoid redundant regeneration, but the full project suite still needs a
  durations-driven pass.
- **Why it matters:** slow gates discourage local verification and make future
  semantic changes harder to review.
- **Smallest next step:** complete the remaining project-local
  `MEDIUM-TEST-PERF-1` split with cheap source-only negative controls plus one
  end-to-end refresh characterization.
- **Acceptance check:** focused mutation tests still catch the known failure
  classes, `--durations=20` shows fewer redundant artifact refreshes, and the
  manuscript gate still passes.
- **Out of scope:** weakening coverage, skipping pymdp-backed evidence, or
  dropping the end-to-end refresh characterization.

---

## Known divergences from `CHANGELOG.md`

As of 2026-06-12 there are **no known divergences**: `pyproject.toml`,
`CHANGELOG.md`, and the published tag all agree at **`3.4.0`** (the prior
"`v3.3.1` bumped but not released" gap was resolved by cutting `v3.4.0`, which
folds the dated `[3.3.1]` entry and all post-`3.3.1` work into one published
release). The docs-lint (links/consistency/doc-pairs), drift, and canonical-facts
gates are clean.

If a new drift appears between [`CHANGELOG.md`](CHANGELOG.md), `TO-DO.md`,
generated facts, or `.github/workflows/ci.yml`, fix forward and record the
current source of truth here instead of rewriting shipped changelog entries.

---

## Conventions

- Backlog IDs are stable. Use them in commit messages when closing related
  work; do not silently reuse retired IDs for new work.
- **ID scheme:** `<AREA>-<SLUG>-<N>`, where `AREA` names the surface — `GH`
  (GitHub workflows/CI), `ARCH` (architecture/test rules), `LOG` (logging), `AI`
  (Active Inference exemplar), `SIA` (SIA exemplar), `DEP` (dependencies), `FMT`
  (rendering formats), `PIPELINE`/`DASHBOARD`/`REPRO`/`PROSE`/`EVIDENCE`
  (shipped-capability follow-ups), `COVERAGE`/`READFILE`/`CI-MATRIX` (named
  gates/patterns), and `TODO` (backlog hygiene itself). `N` is a monotonic
  counter within that area+slug.
- Every active item must include a problem, why it matters, smallest next step,
  acceptance check, and out-of-scope boundary.
- Completion requires evidence from a command, file diff, or generated artifact;
  do not check off items from intention. Before retiring an item, confirm its
  artifact exists on disk (and under test) this session — never from a commit
  message alone.
- Re-baseline measured facts instead of copying old numbers from this file.
- Keep private or rotating project names out of public docs; link to
  [`docs/_generated/active_projects.md`](docs/_generated/active_projects.md)
  for public scope.
- Preserve the no-mocks testing policy, project coverage floors, and generated
  artifact guard when closing backlog items.

## See also

- [`CHANGELOG.md`](CHANGELOG.md) - historical release notes
- [`docs/development/roadmap.md`](docs/development/roadmap.md) - release
  direction and long-horizon themes
- [`docs/development/coverage-gaps.md`](docs/development/coverage-gaps.md) -
  measured infrastructure coverage gaps
- [`.github/AGENTS.md`](.github/AGENTS.md) - CI gates and local parity commands
