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

Refreshed on **2026-06-12** after the comprehensive review + merge (Phase A–G,
Q1–Q5, and the thermo-nuclear v2 remediation are now on `main`). Re-run the
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
| Open GitHub PRs | 3 open: 1 Dependabot (`codecov-action` 6.0.1→7.0.0 #28) + 2 maintainer (#23 sheaf integrity gates, #14 infrastructure composability audit) | `/opt/homebrew/bin/gh-axi pr list` |
| Docs lint status | links-only, consistency-only, and doc-pairs all clean (re-verified 2026-06-08) | `uv run python scripts/lint_docs.py --links-only --quiet --json`, `--consistency-only`, `--doc-pairs-only` |
| Mermaid lint status | clean with chunked batch rendering under the default total budget | `uv run python scripts/lint_docs.py --mermaid-only --quiet --json` |
| Release verification baseline | drift `--strict`, COUNTS/skills/exports gates, tracked-project/generated-artifact guards, docs-lint (links/consistency), reporting+evidence+repro suites (877), and the LLM suite (1244, live Ollama) all green at the v3.4.0 commit | `v3.4.0` release + local command history |

---

## Recently shipped

Keep this section short. Details live in release notes or archived audits.

- **Generated-report web design (2026-06-12, `[Unreleased]`):** modernized the
  base HTML report/dashboard template (`infrastructure/reporting/html_templates.py`)
  with CSS design tokens, dark mode (`prefers-color-scheme`), WCAG-AA status
  contrast, fluid type, and a mobile breakpoint — template contract + deterministic
  output preserved (7 template + 875 reporting tests green). Follow-up to unify the
  remaining HTML surfaces is tracked as `WEBDESIGN-EXTEND-1`.

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

`RELEASE-TAG-1`, `REPRO-VERIFY-1`, and `EVIDENCE-CLAIM-1` were closed in the
2026-06-12 sweep (see **Recently shipped**). The following next-increments were
scoped from this session's review and the two environment-dependent local test
failures observed against TeX Live 2026.

### Minor

#### WEBDESIGN-EXTEND-1 - Unify the design system across all generated HTML surfaces

- **Problem:** the modernized design tokens + dark mode now live only in
  `infrastructure/reporting/html_templates.py` (the base report/dashboard
  template). The other HTML emitters — `infrastructure/reporting/_interactive_html.py`,
  `pipeline_html.py`, and `infrastructure/rendering/web_renderer.py` (manuscript
  HTML) — still carry their own ad-hoc inline styles, so the surfaces look
  inconsistent and only one supports `prefers-color-scheme`.
- **Why it matters:** a research template's web deliverables should read as one
  product; duplicated CSS also drifts (a token change must be made in N places).
- **Smallest next step:** extract the `:root` token block + dark-mode overrides
  into a single shared helper (e.g. `html_templates.shared_css()`), have the
  interactive-dashboard and web-renderer emitters consume it, and assert in a
  test that each rendered surface contains the `--brand-1` token and a
  `prefers-color-scheme` block.
- **Acceptance:** the interactive dashboard and web-rendered manuscript both
  reference the shared token block (one source of truth), verified by a test;
  rendered output stays deterministic.
- **Out of scope:** introducing a CSS build step, web fonts, or JS frameworks.

### Medium

#### LINKCHECK-PERF-1 - Make the doc link-audit fast on large checkouts

- **Problem:** `infrastructure/validation/integrity/link_audit_core.py` (driven by
  `scripts/audit_filepaths.py` and `tests/infra_tests/validation/test_check_links.py::TestMainFunction::test_main_returns_exit_code`)
  walks the whole repo resolving every link target with `Path.resolve()`. On this
  tree it exceeds the 10s per-test timeout (and the 120s mermaid-batch budget),
  so the test times out locally even though it passes in CI.
- **Why it matters:** a gate that times out locally erodes trust and hides real
  regressions behind "it's just slow"; contributors skip it.
- **Smallest next step:** prune the walk (skip `.git/`, `.venv/`, `node_modules/`,
  `output/`, `__pycache__/` before descending), memoize `realpath` per directory,
  and cap the per-call work; add a timed test asserting a full audit of a
  scaffolded large tree completes well under the budget.
- **Acceptance:** `test_main_returns_exit_code` completes under its timeout on a
  full checkout; the audit still finds the same broken links it does today
  (pinned by an unchanged correctness test).
- **Out of scope:** changing what counts as a broken link.

#### TEXLIVE-2026-BEAMER-1 - Tolerate the TeX Live 2026 beamer `\reserved@a` kernel warning

- **Problem:** under TeX Live 2026, `infrastructure/rendering/slides_renderer._render_beamer_with_paths`
  raises `CompilationError` because xelatex exits 1 on `! Illegal parameter number
  in definition of \reserved@a` (a LaTeX-kernel vs system-beamer incompatibility,
  not repo code) — even though a **valid PDF is produced** (`pdf_exists=True,
  pdf_structure_valid=True`). `test_render_beamer_with_resource_paths` fails
  locally on TeX Live 2026; CI's pinned TeX passes.
- **Why it matters:** the renderer treats a valid-PDF-with-nonzero-exit as a hard
  failure, so newer TeX distributions break beamer rendering for contributors
  despite a correct artifact.
- **Smallest next step:** when xelatex exits non-zero but the PDF exists and is
  structurally valid, downgrade the *known* `\reserved@a` "Illegal parameter
  number" signature to a logged warning (not a `CompilationError`); keep failing
  hard on a missing/corrupt PDF. Add a regression test feeding a captured TeX log
  with that signature + a valid PDF and asserting it does not raise.
- **Acceptance:** beamer rendering succeeds (warns, returns the PDF) on TeX Live
  2026 when the only error is the `\reserved@a` signature and the PDF is valid;
  genuine compile failures (no PDF / invalid structure) still raise.
- **Out of scope:** pinning a TeX distribution; suppressing arbitrary LaTeX errors.

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
