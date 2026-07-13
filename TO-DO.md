# Repo TO-DO - active backlog

> **Design ethos:** modular, intelligent, functional, logged, tested, and
> documented. Real methods only; never mocks or fakes. Every release ships with
> green tests and accurate docs.

This file tracks **only upcoming, scoped work**. Shipped work and historical
detail live in [`CHANGELOG.md`](CHANGELOG.md); generated counts and project
rosters live in [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md) and
[`docs/_generated/active_projects.md`](docs/_generated/active_projects.md).

---

## Active backlog

### REVIEW-2026-07-02 — Multi-lens review remediation backlog

- **Source:** a 9-dimension adversarial review (43 findings confirmed
  against HEAD, 3 refuted). Safe bounded fixes shipped the same session.
- **Detailed items (R1–R18)** with per-item acceptance lines live in
  [`docs/maintenance/review-remediation-2026-07.md`](docs/maintenance/review-remediation-2026-07.md).
  Current detailed status: **R1–R18 shipped** across the remediation and R10
  closure passes. One external repo-admin follow-up remains: require the
  `Regression Tier` check in branch protection so the CI enforcement claim is
  literal.

### SECURITY-2026-07-09 — Threat-model and ownership-map follow-ups

- **Source:** repo-grounded threat model and ownership map in
  [`template-threat-model.md`](template-threat-model.md) with generated ownership
  artifacts under `security-analysis/ownership-map/`.
- **SECURITY-OWNERSHIP-1:** Problem: sensitive categories have bus factor 1
  across CI/CD, credentials, publishing, guards, rendering, LLM/search, and
  provenance/crypto. Why it matters: a compromised or unavailable single owner
  can bottleneck high-risk review. Smallest next step: add a formal
  sensitive-area owner map and required-review policy. Acceptance: rerun the
  ownership map and either show two named reviewers for each sensitive tag or a
  documented sole-owner exception. Out of scope: rewriting git history.
- **SECURITY-CODEOWNERS-1:** Problem: `.github/CODEOWNERS` has a safe catch-all
  but its explicit template roster does not mirror `PUBLIC_PROJECT_NAMES`. Why it
  matters: exemplar ownership intent drifts as templates are added. Smallest next
  step: generate the template stanza or add a parity check. Acceptance: a command
  fails when a public template lacks the intended CODEOWNERS coverage. Out of
  scope: changing GitHub team membership.
- **SECURITY-PUBLISH-1:** Problem: publish/archive/upload commands can perform
  real deposits with env or local credentials once dry-run is disabled. Why it
  matters: a wrong payload can become public and hard to retract. Smallest next
  step: add a publish preflight that emits a redacted payload manifest, redacted
  credential-source summary, and local-only path refusal. Acceptance: non-dry-run
  publish refuses any local-only project/resource path and records the exact
  public files to upload. Out of scope: provider API redesign.
- **SECURITY-ASKOS-PROMOTION-1:** Problem: `projects/ongoing/askos/TODO.md` still lists
  JWT, policy, redaction, vault, route-handler, MCP, and export-test gaps. Why it
  matters: those are control-plane risks if AskOS enters active/public/deployed
  scope. Smallest next step: add an AskOS promotion checklist/gate. Acceptance:
  AskOS cannot be promoted without closing or explicitly risk-accepting those
  security TODOs. Out of scope: implementing AskOS auth inside this template pass.

### AI-GATE-PERF-2 — Reduce active-inference gate runtime after correctness

- **Problem:** `template_active_inference` gate tests had a heavy explicit
  roadmap/sheaf write path whose *first* invocation in a process took ~250s.
- **Status:** correctness/timeout blocker closed (2026-07-01) — a
  `pytest_sessionstart` pre-warm hook fixed the cascade; two O(N×M) redundant
  file-read bottlenecks fixed. Full non-long-running suite passes under the
  real 120s per-test timeout.
- **Remaining (open):** the `--durations=20` profiling pass itself (to look
  for further redundant artifact refreshes beyond the two fixed) and the
  project-local `MEDIUM-TEST-PERF-1` split (cheap source-only negative
  controls plus one end-to-end refresh characterization) are still open. This
  item closed the *correctness/timeout* blocker, not the full perf-tuning
  scope.

### TEST-STANDIN-DEBT-1 — Replace semantic monkeypatch stand-ins

- **Problem:** the enforced no-mocks check is a lexical mock-framework gate,
  not proof that every test exercises a real dependency. The live
  `uv run python scripts/audit/verify_no_mocks.py --inventory` scan on
  2026-07-13 measured **378 dependency replacements** (`setattr`/`setitem` and
  deletion variants), alongside 254 environment-isolation operations, 0
  import-path operations, and 2 other scope operations in the live public test
  scope.
- **Why it matters:** replacing internal callables, clients, clocks, or modules
  can make a test validate a stand-in rather than the production integration
  even though no prohibited mocking framework is imported.
- **Smallest next step:** migrate the highest-risk dependency replacements to
  constructor/transport injection, localhost services, real subprocesses, or
  deterministic clocks, and re-run the inventory after each bounded batch.
  CI now fails if the inventory grows beyond 378; every migration lowers that
  ceiling until the strict zero-debt mode can replace the ratchet.
- **Acceptance:**
  `uv run python scripts/audit/verify_no_mocks.py --inventory --fail-on-dependency-replacement`
  exits 0 with `dependency_replacement: 0`; only then may CI enable that strict
  inventory flag.
- **Out of scope:** pretending the current debt is already resolved, silently
  gating CI on a known-red count, or classifying ordinary
  `setenv`/`delenv`/`chdir` isolation as dependency replacement.

---

## Known divergences from `CHANGELOG.md`

As of 2026-06-27, `pyproject.toml` and the latest GitHub release agree at
**`3.5.1`** / **`v3.5.1`**. `CHANGELOG.md` still carries current work under
`[Unreleased]` rather than a `3.5.x` heading; confirm release-note reconciliation
before claiming changelog parity. The docs-lint links/consistency/doc-pairs gates
were rerun for the contributor-strategy docs pass and reported unrelated active
lane failures; full release-readiness gates were not rerun against the dirty
local tree.

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
