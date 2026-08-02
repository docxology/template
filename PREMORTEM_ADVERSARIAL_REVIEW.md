# Premortem + Devil's Advocate Review — `docxology/template`

**Target**: `https://github.com/docxology/template`
**Method**: `sat.premortem_analysis` + `sat.devils_advocacy`
**Reviewer**: Hermes Agent (autonomous adversarial review)
**Date**: 2026-07-31
**Confidence**: High (claims bound to file:line evidence in the checkout under review)

---

## Part 1 — Premortem (assume the project FAILED spectacularly)

The template shipped a v3.6.0 "reproducible generative research" release. Six
weeks later it failed catastrophically. Working backward from the smoking crater,
these are the most plausible causes — each ranked by **plausibility × impact**,
with a leading indicator and a file:line evidence anchor.

### Cause A — "Zero-failure release gate" shipped with a known-failing lane  (Critical)

The "zero-failure release gate" claim is contradicted by the repo's own TO-DO.
`TO-DO.md:69` (`PUBLIC-MATRIX-1`) states verbatim:

> "The public matrix is not yet a single zero-failure release gate: 23 lanes
> passed, while `template_active_inference` measured 89.35% against its 90%
> floor; the run also exposed test-generated output churn."

The 90% project coverage floor is enforced in CI `test-project` jobs
(`.github/workflows/ci.yml:466-472` → `stage_01_test.py --project ... --project-only`),
and `template_active_inference` (78 test files) is the largest exemplar.
The release workflow (`.github/workflows/release.yml:69-76`) runs the
public-capability manifest and the rendered publication audit — but the per-project
coverage gate is **not** re-run in the release workflow; it only runs in the
continuous `test-project` matrix, which is gated behind `verify-no-mocks`, not
behind the tag push. A release tag can be cut on a commit whose `test-project`
matrix hasn't run for that exact SHA.

- **Plausibility × impact**: High × Critical
- **Leading indicator**: a tag `vX.Y.Z` passes `release.yml` while the last
  `test-project(template_active_inference, 3.10)` lane on that commit was red.
- **Mitigation**: make `test-project` (or a `--receipt` public matrix) a
  required `needs:` of the release job, not just a continuous gate.

### Cause B — Determinism is asserted, not proven, in CI  (High)

The pipeline YAML and artifacts module talk extensively about determinism
(`infrastructure/core/pipeline/artifacts.py:51`, `incremental.py`, `run_matrix.py`),
and `SOURCE_DATE_EPOCH` is honored when set (`artifacts.py:304`). But a
repo-wide grep of `.github/workflows/` and `.github/actions/` for
`SOURCE_DATE_EPOCH` returns **zero hits**. CI never pins the clock. The
artifact manifest omits wall-clock timestamps *if* `SOURCE_DATE_EPOCH` is set
(`artifacts.py:304`), but nothing in the CI env sets it. PDF rendering via
pandoc/xelatex embeds timestamps from the runner clock; LaTeX `\today` and
PDF `/CreationDate` will vary run-to-run on the same commit.

- **Plausibility × impact**: High × High (any "reproducible byte-for-byte" claim
  is false on PDFs without `SOURCE_DATE_EPOCH` + a reproducible TeX build).
- **Leading indicator**: two `--core-only` runs on the same commit produce
  PDFs with different `/CreationDate` or different `.log` intermediates.
- **Mitigation**: export `SOURCE_DATE_EPOCH` in the composite setup action and
  add a rendered-output snapshot-diff test that fails on byte drift.

### Cause C — "No mocks or fakes" is a lexical gate, not a semantic proof  (High)

The no-mocks policy is enforced by `scripts/audit/verify_no_mocks.py` (22 lines),
which delegates to `infrastructure/validation/output/no_mock_audit.py` and
`no_mock_enforcer.py` (524 lines). The enforcer's own docstring
(`no_mock_enforcer.py:24-30`) is explicit:

> "The lexical gate deliberately does **not** claim that a clean result proves
> all tests exercise real dependencies. `pytest.monkeypatch` is a distinct token
> from `patch` and is therefore outside that gate."

CI (`ci.yml:250-253`) separately enforces `--max-dependency-replacements 0` on
the semantic inventory. That catches `monkeypatch.setattr`/`setitem`. But it does
**not** catch: dependency-free hand-rolled stubs (a test that defines `class
FakeOptimizer` with the same interface), real-data fixtures that are
hand-authored constants, or `conftest.py` path manipulation that imports a
different implementation. The "No mocks or fakes" claim is lexically true but
semantically weaker than the README implies (`README.md:525`: "No mocks — tests
use real data, real files").

- **Plausibility × impact**: Medium × High (the claim overpromises; a reviewer
  who trusts it may not audit hand-rolled fakes).
- **Leading indicator**: a `test_*.py` defines a `class _FakeX` or returns
  hand-written JSON as if it were computed; the lexical gate stays green.
- **Mitigation**: add a hand-rolled-fake heuristic (class names matching
  `Fake*`/`Stub*`/`Dummy*` in test files) to the advisory inventory.

### Cause D — "Generated artifacts guard" has a 50MB blind spot and a content budget  (Medium-High)

The generated-artifact guard (`scripts/audit/check_tracked_generated_artifacts.py`,
56 lines) checks three things via `git_guards.py`: tracked generated artifacts,
local home-path leaks, and **budget findings**
(`public_template_output_budget_findings`, line 28). Per `README.md:250`:
"Public output files above 50 MB remain excluded by the generated-artifact
guard." Files just under 50MB that are legitimately generated (e.g. a large
rendered PDF or a bundled dataset) are tracked and not flagged. Conversely, the
guard relies on a path allowlist; a new exemplar that writes to an
non-allowlisted `output/` subtree could silently be ignored by the budget check
while still being git-tracked.

- **Plausibility × impact**: Medium × Medium (a too-large or stale tracked
  binary rots in git history; or a generated file slips past the allowlist).
- **Leading indicator**: `git ls-files projects/templates/*/output/ | xargs du`
  shows a file approaching 50MB; or a new exemplar's output is tracked but
  absent from the allowlist in `git_guards.py`.
- **Mitigation**: make the budget check fail-closed on *any* tracked binary
  in `output/` whose source isn't regenerable in a clean checkout, regardless
  of size.

### Cause E — `pytest-httpserver` is a real network mock, admitted but under-stated  (Medium)

`README.md:525` claims "No mocks — tests use real data, real files,
`pytest-httpserver` for HTTP." But `pytest-httpserver` *is* an in-process mock
HTTP server — it serves canned responses. The no-mocks policy explicitly
permits `monkeypatch` for "test-server URLs" (`tests/AGENTS.md`). This is a
reasonable engineering choice, but the README's "No mocks or fakes" headline
is contradicted by its own footnote. The lexical gate won't catch it
(`pytest-httpserver` isn't in `_FORBIDDEN_IMPORT_ROOTS`,
`no_mock_enforcer.py:53`).

- **Plausibility × impact**: Low × Medium (reputational: a careful reader spots
  the contradiction and discounts the whole claim).
- **Leading indicator**: a PR review or academic referee flags the
  `pytest-httpserver` exception.
- **Mitigation**: reword the README claim to "No unit-level mock frameworks;
  HTTP boundaries use an in-process test server."

### Cause F — "Bounded public matrix" is built but the receipt isn't wired into CI  (High)

The public-matrix receipt module exists
(`infrastructure/core/public_matrix_receipt.py`, 192 lines) and its validator
fails closed on missing projects, timeouts, coverage failures, and output drift.
But a grep of `.github/workflows/ci.yml` for `receipt` or `public_matrix`
returns **zero hits**. The receipt module is shipped but not invoked in CI.
`TO-DO.md:69`: "a full matrix run with `--receipt` is the remaining step."
So the "bounded public matrix with per-project coverage floors" is enforced
only by the per-project `test-project` jobs (which don't write a receipt),
and the deterministic receipt that would prove a single zero-failure run is
dormant.

- **Plausibility × impact**: High × High (the receipt was the artifact meant to
  *prove* the matrix passed; without it, "matrix passed" is a CI dashboard
  assertion, not a checkable, content-addressed receipt).
- **Leading indicator**: a release ships; no `rendered_provenance.json` or
  `public_matrix_receipt.json` exists for that tag.
- **Mitigation**: wire `--receipt` into the release workflow and require the
  receipt's `digest()` in the release notes.

### Cause G — External artifacts (Zenodo, IPFS, HuggingFace) are asserted, not checked  (Medium-High)

`template_code_project/manuscript/config.yaml` declares
`published_artifacts` with 8 live URLs (IPFS pinata, HuggingFace, OSF, PyPI,
Netlify, GitHub Pages, Software Heritage, Zenodo). Sixteen config files across
exemplars carry `published_artifacts`. The publication audit
(`infrastructure/validation/publication/`) checks structure, provenance, and
rendered snapshots, but a grep for `http`/`requests`/`urllib`/`GET` in the
publication checks returns no liveness verifier. `TO-DO.md:76`
(`RELEASE-METADATA-1`): "DOI/GitHub metadata freshness, installer pinning, live
branch protection not fully provable by repo-only gates." So "published
artifacts" can be dead links and the release gate stays green.

- **Plausibility × impact**: Medium × High (a reader follows a DOI or IPFS
  link in a published manuscript and hits a 404; the repo's own gate never
  flagged it).
- **Leading indicator**: `curl -I` on a `published_artifacts` URL returns 404
  while CI is green.
- **Mitigation**: add a credential-free HEAD-check step (allowed to fail with
  an operator blocker) to the release workflow.

### Cause H — "Thin orchestrator" drift is detected but not enforced as a hard gate in PR CI  (Medium)

`infrastructure/project/drift/orchestrator.py` enforces AST thin-orchestrator
rules, and `scripts/audit/check_template_drift.py --strict` exists. But in
`ci.yml`, the `lint` job (lines 124-184) does not run `check_template_drift.py`.
It runs Ruff, mypy, `__all__` audit, tracked-artifact/secret/confidentiality
guards, publication audit, and the module line-count gate. The thin-orchestrator
drift check is invoked in pre-commit hooks (`AGENTS.md`) and documented as a
"thin-orchestrator gate" in `README.md:28`, but it is **not** in the CI lint
job. A contributor who skips pre-commit (or whose editor doesn't fire it) can
land algorithm-in-script drift that CI won't catch.

- **Plausibility × impact**: Medium × Medium (architecture erosion).
- **Leading indicator**: a `scripts/*.py` grows real business logic; CI stays
  green; `check_template_drift.py --strict` only catches it locally.
- **Mitigation**: add `check_template_drift.py --strict` to the CI `lint` job.

### Cause I — Regression tier tolerates exit 5 (no tests collected) as success  (Medium)

The regression tier (`ci.yml:391-414`) runs `pytest tests/regression/` and
explicitly tolerates exit code 5 ("no tests collected on a clean scaffold is
treated as success"). The regression `manifest.json` lists 16 required test
files and `minimum_collected_tests: 55`. But the tolerance means: if a refactor
accidentally breaks test collection (import error → pytest exits 5 on some
files), CI passes as long as *any* test collected. The manifest's
`required_test_files` are not enforced as a hard "all must collect" gate in the
CI step — the step runs plain `pytest tests/regression/ -q`.

- **Plausibility × impact**: Medium × Medium (a silent collection regression
  erodes claim-binding coverage).
- **Leading indicator**: `pytest tests/regression/ --collect-only` count drops
  below 55 but CI stays green because exit 5 is tolerated.
- **Mitigation**: assert the collected count ≥ `manifest.minimum_collected_tests`
  and that every `required_test_files` entry was collected.

### Cause J — `template_active_inference` cross-version matrix is the long pole, and it's fragile  (Medium)

`ci.yml:429` sets `timeout-minutes: 60` for `test-project` because
"active_inference on py3.10 has exceeded 45 min on loaded runners." The
exemplar has 78 test files. The CI matrix (`public_capabilities.py:47`) is
`("3.10", "3.12")` — only two Python versions per project. The 3.10 lane for
the largest exemplar is the most likely to flake (timeout, OOM, runner
contention). `fail-fast: false` (`ci.yml:439`) means one slow lane won't cancel
others, but a timeout is a hard red. If the 3.10 lane flakes on a release
commit, the release workflow doesn't depend on `test-project` (Cause A), so the
release ships regardless.

- **Plausibility × impact**: Medium × Medium.
- **Leading indicator**: `test-project(template_active_inference, 3.10)` is red
  on the release commit; release tag passes.
- **Mitigation**: same as Cause A — gate the release on the matrix.

---

## Part 2 — Devil's Advocate (strongest principled case AGAINST each claim)

For each headline claim, I mount the strongest good-faith counter-case, then
give the robustness verdict.

### Claim 1: "Deterministic outputs from version-controlled inputs"

**Counter-case**: Determinism is a *property of the pipeline design*, not a
*proven property of the outputs*. Evidence:
- `SOURCE_DATE_EPOCH` is honored (`artifacts.py:304`) but **never set in CI**
  (grep of `.github/workflows/` = 0). PDF `/CreationDate`, LaTeX `\today`,
  pandoc metadata, and log timestamps are wall-clock-dependent.
- The artifact manifest excludes "transient TeX/log files"
  (`infrastructure/core/pipeline/AGENTS.md`, artifacts.py docstring) from
  hashing — so the *provenance* is deterministic, but the *primary deliverable*
  (PDF) is not byte-stable.
- `incremental.py` (content-hash stage skipping) is **default-off**
  (`IncrementalConfig(enabled=False)`, `pipeline/AGENTS.md`). So the default
  pipeline does not even attempt input-hash determinism.
- The `run_matrix.py` module is deterministic-by-construction *given a
  `run.config`*, but no `run.config` is checked into CI; it's an opt-in runner.

The claim is true for: JSON ledgers, manifest digests, coverage receipts
(`public_matrix_receipt.py:94` `digest()`), and source-derived variables
injected via `manuscript_variables.json`. It is **not** proven for rendered PDFs
or any artifact touched by the system clock.

**Robustness verdict**: Claim **partially survives**. Reword to "Deterministic
*metadata and ledgers*; rendered PDFs are deterministic only when
`SOURCE_DATE_EPOCH` is pinned (currently a local-only step)."

### Claim 2: "Reproducible research lifecycle"

**Counter-case**: The lifecycle is reproducible *in principle* but the repo
cannot prove a stranger can reproduce it:
- `README.md:262-268` gives the reproduce commands, but step 2 (`uv sync`)
  requires a network-bound `uv.lock` resolve; `UV_FROZEN=true` is set in CI
  (`ci.yml:23`) but not in the documented reproduce snippet.
- The `release.yml` doesn't re-run the project test matrix (Cause A), so
  "reproducible" at release time means "source contract + capability manifest +
  rendered publication audit pass" — not "tests pass on a clean machine."
- Externally hosted evidence (IPFS, HuggingFace, OSF, Netlify) is declared in
  configs but never liveness-checked (Cause G). If any rots, reproduction
  *appears* to work from the repo but the canonical artifacts are unreachable.

**Robustness verdict**: Claim **survives weakly**. The *machinery* for
reproducibility (lock file, pipeline DAG, receipt, manifest) is real. But the
*guarantee* is conditional on an operator pinning `SOURCE_DATE_EPOCH`,
re-running the test matrix on the release tag, and keeping external mirrors
alive — none of which is enforced by repo-only gates.

### Claim 3: "No mocks or fakes"

**Counter-case**: The enforcer's own docstring disclaims the strong reading
(`no_mock_enforcer.py:24-30`). The gate proves *lexical absence* of
`unittest.mock`/`pytest_mock`/`patch`/`MagicMock`. It explicitly does not
prove tests exercise real dependencies. `README.md:525` itself admits
`pytest-httpserver` (a mock HTTP server). `tests/AGENTS.md` permits
`monkeypatch` for env, cwd, import paths, and test-server URLs. The semantic
inventory (`--max-dependency-replacements 0`, `ci.yml:250-253`) catches
`monkeypatch.setattr`/`setitem` but not hand-rolled `Fake*` classes or
hard-coded "expected" JSON fixtures that stand in for computed results.

**Robustness verdict**: Claim **fails as worded**. The honest claim is
"No prohibited mock-framework imports; dependency-replacement via
`monkeypatch` held at zero; hand-rolled fakes are not lexically detected."

### Claim 4: "Generated artifacts guard"

**Counter-case**: The guard (`check_tracked_generated_artifacts.py`, 56 lines)
is a thin CLI over three `git_guards.py` functions. It's wired into CI lint
(`ci.yml:163`). But:
- It has a **50MB blind spot** (`README.md:250`).
- It relies on a path allowlist in `git_guards.py` (505 lines); a new exemplar
  writing outside the allowlist is silently unchecked.
- It checks for "machine-local home paths" and "credential-like secret
  material" in tracked outputs — but these are pattern-matchers, not
  content-identity checks. A tracked PDF that is byte-identical to a
  regenerated one passes even if the *source* that produced it is gone.

**Robustness verdict**: Claim **survives narrowly**. The guard catches gross
violations (tracked `.pipeline/` state, logs, local paths, secrets). It does not
and cannot prove tracked outputs are *regenerable* — only that they are on the
allowlist and under budget.

### Claim 5: "Bounded public matrix with per-project coverage floors"

**Counter-case**: The matrix is real (48 lanes = 24 projects × py3.10/3.12,
`public_capabilities.py:47`, `ci.yml:443`). Per-project floors are enforced
in-process by `stage_01_test.py --project` (`ci.yml:466-472`). But:
- The **receipt** that would prove a single bounded run is **not wired into CI**
  (Cause F). `TO-DO.md:69` admits this is the "remaining step."
- `template_active_inference` measured **89.35% against a 90% floor**
  (`TO-DO.md:26-27`) as of the last matrix run. The "bounded matrix" currently
  has one known-failing lane. The TO-DO marks it SHIPPED (receipt module) but
  "90% floor pending gate rebuild."
- The matrix is **ubuntu-only** for projects (`ci.yml:421`); macOS breadth is
  only in `test-infra` (5 cells). "Bounded" is true; "comprehensive" is not.

**Robustness verdict**: Claim **fails as stated** ("bounded public matrix with
per-project coverage floors" implies all floors are met; one is not, and the
receipt isn't running).

### Claim 6: "Zero-failure release gate"

**Counter-case**: This is the weakest claim. The release workflow
(`release.yml`) runs: root release contract, public capability manifest (static
structure, no tests), export smoke, rendered publication audit, and `uv build`
+ `twine check`. It does **not** run:
- The `test-project` matrix (per-project 90% floors).
- The `test-infra` matrix (60% infra floor).
- The `test-regression` tier (claim-binding pins).
- The `verify-no-mocks` gate.
- The `public_matrix_receipt`.
The "release gate" is a *static contract + build* gate, not a *zero-failure
test* gate. `TO-DO.md:69` explicitly says the public matrix "is not yet a
single zero-failure release gate."

**Robustness verdict**: Claim **fails**. The release gate is "zero-failure on
static contracts and build," not "zero-failure on tests." Any prose claiming the
latter is unsupported by `release.yml`.

---

## Part 3 — Assumption breaks (most dangerous if they occur)

| # | Assumption | What breaks if false | Evidence it may be false |
|---|------------|---------------------|---------------------------|
| 1 | CI test matrix ran on the exact release tag | "Zero-failure release" claim | `release.yml` has no `needs: test-project` |
| 2 | `SOURCE_DATE_EPOCH` is pinned for renders | "Deterministic outputs" claim | Not set in any workflow |
| 3 | External mirrors (Zenodo, IPFS, HF) stay alive | "Reproducible lifecycle" claim | No liveness check in any gate |
| 4 | `check_template_drift.py --strict` runs in PR CI | "Thin orchestrator" claim | Not in `ci.yml` lint job |
| 5 | `pytest-httpserver` is "not a mock" | "No mocks or fakes" claim | README footnote contradicts headline |
| 6 | The 50MB output budget catches all oversized generated files | "Generated artifacts guard" | `README.md:250` admits the exclusion |
| 7 | Regression tier collects all required tests | Claim-binding pins | Exit 5 tolerated as success (`ci.yml:414` context) |
| 8 | `public_matrix_receipt` proves the matrix passed | "Bounded public matrix" | Not invoked in CI (`ci.yml` grep = 0) |

---

## Part 4 — Next discriminating checks (to raise confidence)

1. **Run the public matrix with `--receipt` on HEAD** and check whether
   `template_active_inference` still measures under 90%. (Resolves Claim 5/6.)
2. **Run two `--core-only` pipelines on the same commit** with and without
   `SOURCE_DATE_EPOCH` pinned; diff the output PDFs byte-for-byte. (Resolves
   Claim 1.)
3. **Grep test files for `class .*Fake|class .*Stub|class .*Dummy`** and audit
   whether any substitute for a real dependency. (Resolves Claim 3.)
4. **Add `check_template_drift.py --strict` to the CI lint job** and run on
   HEAD; report any findings. (Resolves Cause H.)
5. **HEAD-check the 8 `published_artifacts` URLs** in
   `template_code_project/manuscript/config.yaml`. (Resolves Cause G.)
6. **Collect `tests/regression/` with `--collect-only`** and compare the count
   to `manifest.minimum_collected_tests` (55). (Resolves Cause I.)

---

## Summary (for the parent agent)

**What I did**: Read AGENTS.md, README.md, TO-DO.md, CHANGELOG.md, ci.yml,
release.yml, pipeline.yaml, public_capabilities.py, no_mock_enforcer.py,
public_matrix_receipt.py, check_tracked_generated_artifacts.py, regression
manifest, exemplar layouts; ran targeted greps for every claim's enforcement
evidence.

**Headline findings** (file:line anchored):
- **"Zero-failure release gate" is unsupported** — `release.yml:64-76` runs
  static contracts + build, not the test matrix; `TO-DO.md:69` admits the
  matrix "is not yet a single zero-failure release gate."
- **"Deterministic outputs" is unproven for PDFs** — `SOURCE_DATE_EPOCH` is
  honored (`artifacts.py:304`) but never set in CI (grep = 0); incremental
  mode is default-off.
- **"No mocks or fakes" overpromises** — the enforcer's own docstring
  (`no_mock_enforcer.py:24-30`) disclaims the strong reading; `pytest-httpserver`
  is a mock server; hand-rolled fakes are undetected.
- **"Bounded public matrix" has a known-failing lane** —
  `template_active_inference` at 89.35% vs 90% floor (`TO-DO.md:26-27`); the
  receipt module exists but is **not wired into CI** (grep of ci.yml = 0).
- **"Generated artifacts guard" has a 50MB blind spot** (`README.md:250`) and
  relies on an allowlist (`git_guards.py`).
- **Thin-orchestrator drift check is not in CI lint** — `ci.yml:124-184` omits
  `check_template_drift.py --strict`.
- **External artifact URLs are never liveness-checked** — 16 config files
  declare `published_artifacts`; no gate fetches them.
- **Regression tier tolerates exit 5** (no tests collected) as success
  (`ci.yml:414` + `manifest.json` `minimum_collected_tests: 55`).

**Files created**: `PREMORTEM_ADVERSARIAL_REVIEW.md` (this file) at the template
root.

**Issues encountered**: None. All evidence is from the live checkout.
