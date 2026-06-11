# Repo TO-DO - active backlog

> **Design ethos:** modular, intelligent, functional, logged, tested, and
> documented. Real methods only; never mocks or fakes. Every release ships with
> green tests and accurate docs.

This file tracks live work after the `v3.3.1` version bump (latest published
release: `v3.3.0`; the `v3.3.1` tag is pending — see RELEASE-TAG-1). Historical
release detail belongs in [`CHANGELOG.md`](CHANGELOG.md); generated counts and
project rosters belong in
[`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md) and
[`docs/_generated/active_projects.md`](docs/_generated/active_projects.md).

---

## Live state snapshot

Refreshed on **2026-06-08** from the post-`v3.3.1`-version-bump state and local
inspection. Re-run the commands in the **Source** column before copying any
number into prose.

| Gate or surface | Current value | Source |
| --- | --- | --- |
| Package version | `3.3.1` | `pyproject.toml#[project].version` |
| Latest published release | `v3.3.0` (published 2026-06-07) — package is at `3.3.1` with a dated [`CHANGELOG.md`](CHANGELOG.md) `[3.3.1]` entry, but the `v3.3.1` git tag + GitHub release are **pending** (see RELEASE-TAG-1) | `/opt/homebrew/bin/gh-axi release list`, `git tag` |
| Public source scope | `infrastructure` plus nine public exemplar `src/` trees | `uv run python -m infrastructure.project.public_scope source-paths` |
| Public exemplars | `template_active_inference`, `template_autoresearch_project`, `template_autoscientists`, `template_code_project`, `template_newspaper`, `template_prose_project`, `template_sia`, `template_template`, `template_textbook` | [`docs/_generated/active_projects.md`](docs/_generated/active_projects.md) |
| Canonical generated facts | 20 importable infrastructure packages; 532 infrastructure Python modules; 216 project-scope infrastructure tests collected; nine exemplar coverage gates at or above 90 % | [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md) |
| Open GitHub PRs | 3 open: 1 Dependabot (`codecov-action` 6.0.1→7.0.0 #28) + 2 maintainer (#23 sheaf integrity gates, #14 infrastructure composability audit) | `/opt/homebrew/bin/gh-axi pr list` |
| Docs lint status | links-only, consistency-only, and doc-pairs all clean (re-verified 2026-06-08) | `uv run python scripts/lint_docs.py --links-only --quiet --json`, `--consistency-only`, `--doc-pairs-only` |
| Mermaid lint status | clean with chunked batch rendering under the default total budget | `uv run python scripts/lint_docs.py --mermaid-only --quiet --json` |
| Release verification baseline | public project tests, Active Inference focused gate, docs invariant suite, Ruff, format, mypy, drift, skills, exports, SIA validation, tracked-project/generated-artifact guards, and pre-push hooks passed | `v3.3.0` release notes and local command history |

---

## Recently shipped

Keep this section short. Details live in release notes or archived audits.

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

## Minor

### RELEASE-TAG-1 - Tag and publish v3.3.1

- **Problem:** `pyproject.toml` is at `3.3.1` and [`CHANGELOG.md`](CHANGELOG.md)
  carries a dated `[3.3.1]` entry, but no `v3.3.1` git tag or GitHub release
  exists — `git tag` and `/opt/homebrew/bin/gh-axi release list` both show
  `v3.3.0` as the latest. The release is half-completed: metadata bumped, tag and
  GitHub release not cut.
- **Why it matters:** a dated CHANGELOG entry with no tag misleads anyone who
  trusts "released" semantics; downstream tooling that resolves the latest tag
  (archival, DOI, repro-bundle) will pin `v3.3.0` while docs imply `v3.3.1`.
- **Smallest next step:** run the release verification baseline once more on a
  clean tree, then create the `v3.3.1` annotated tag and the matching GitHub
  release with the CHANGELOG `[3.3.1]` body.
- **Acceptance:** `git tag | rg -x 'v3\.3\.1'` returns the tag and
  `/opt/homebrew/bin/gh-axi release list | rg v3\.3\.1` shows the published
  release.
- **Out of scope:** bumping to a new version; re-tagging already-published
  releases.

---

## Medium

### REPRO-VERIFY-1 - Fail closed on declared-but-absent reproduction outputs

- **Problem:** `build_repro_bundle`/`collect_entries`
  (`infrastructure/publishing/repro_bundle.py`) hash each declared output
  artifact, but when a declared output is **absent at build time** it is baked
  into the manifest as `present: false`, and `verify_repro_bundle` then treats a
  still-absent entry as a match. On a fresh checkout (outputs are gitignored and
  not yet built) a bundle for an exemplar can therefore record most of its
  scientific outputs as `present: false` and still `verify` green — a bundle that
  "reproduces nothing" certifies as reproducible. Surfaced by the RedTeam pass on
  REPRO-MULTI-1 (the synthetic-exemplar tests always wrote their declared outputs,
  so the absent-output path was never exercised).
- **Why it matters:** the repro bundle's contract is "any missing file is a
  mismatch, never a silent pass." A declared output that is absent at both build
  and verify time is a silent pass that contradicts that contract and overstates
  reproducibility of the public deliverable.
- **Smallest next step:** distinguish build-time-absent **infra inputs** from
  build-time-absent **declared outputs**. A declared output the manifest claims
  should exist must either make `build` fail loudly (run the pipeline first) or be
  recorded so `verify` fails closed when it is still absent. Add a test that
  builds a bundle whose `artifact_manifest` declares a path absent on disk and
  asserts `build` refuses or `verify` returns `ok=False`.
- **Acceptance:** a bundle built for an exemplar with declared-but-absent outputs
  either refuses at build time or fails `verify`; a regression test pins it.
- **Out of scope:** changing the hash algorithm or the infra-input (`uv.lock`,
  `pyproject.toml`, `COUNTS.md`) handling; archival deposit.

---

## Major

### EVIDENCE-CLAIM-1 - Make the evidence-graph claim layer reachable for exemplars

- **Problem:** EVIDENCE-GRAPH-1 shipped a typed producer/consumer/validator/claim
  graph whose claim-ingest works **only** for a file literally named
  `claims.json` (`infrastructure/reporting/evidence_graph.py` searches
  `output/data/claims.json`, `manuscript/claims.json`, `claims.json`; the
  `test_ingest_claims_reads_real_ledger` test confirms ingest fires when that
  file exists). But no public exemplar writes `claims.json` to those paths — the
  `template_autoresearch_project` exemplar produces real claim data
  (`AutoResearchClaim` via `src/reports.py` / `src/writers/payloads.py`) under a
  different name — so every exemplar lands the "No claim ledger found" note with
  zero claim nodes and zero `supports` edges.
- **Why it matters:** the central value of the evidence graph — claims backed by
  artifacts — is unreachable for every project in the repo; the `supports`-edge
  layer is dead in practice on the one exemplar capable of populating it.
- **Smallest next step:** reconcile the claim-ledger contract end-to-end —
  either extend the candidate-path/format list so the autoresearch exemplar's
  emitted claim ledger is ingested, or have that exemplar emit a canonical
  `claims.json`; emit claim nodes + `supports` edges; add a test asserting the
  autoresearch exemplar yields non-empty claim nodes after analysis, keeping the
  existing empty-ledger note path for a project with no ledger.
- **Acceptance:** building the evidence graph for `template_autoresearch_project`
  yields a non-zero count of `claim` nodes (currently `0`), and the "No claim
  ledger found" note no longer appears for that project, verified by a test.
- **Out of scope:** generating claim ledgers for projects that do not produce
  one; changing the byte-stable JSON serialization contract.

---

## Known divergences from `CHANGELOG.md`

The pre-`2026-06-08` snapshot drift (version pinned to `3.3.0`, a phantom 5-PR
roster, and eight shipped items still listed as open backlog) was reconciled in
this refresh, and [`docs/development/roadmap.md`](docs/development/roadmap.md) was
synchronized to the same baseline. The docs-lint (links/consistency/doc-pairs),
drift, and canonical-facts gates are all clean as of 2026-06-08. One real
divergence remains tracked rather than silently hidden:

- **`v3.3.1` is bumped but not released.** `pyproject.toml` and the
  `CHANGELOG.md` `[3.3.1]` entry imply a 3.3.1 release, but no `v3.3.1` git tag /
  GitHub release exists (latest is `v3.3.0`). Tracked as **RELEASE-TAG-1**.

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
