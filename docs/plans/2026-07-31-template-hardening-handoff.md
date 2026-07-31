# Template Infrastructure Hardening Handoff

**Date:** 2026-07-31
**Repository:** `https://github.com/docxology/template.git`
**Published base commit:** `2dc88a7f6e740717b259b189c0cca10c5d24f501`
**Branch state at handoff:** `main == origin/main`, clean worktree
**Continuation posture:** GO for review and extension; NO-GO for claiming a fully release-green public matrix

## Session intent

Continue the comprehensive infrastructure and public `template_*` exemplar
review that produced commit `2dc88a7`. The next agent should verify the
published state, inspect the hardening changes against their contracts, close
the remaining release blockers where safely possible, and preserve evidence for
every conclusion.

This is a public repository. Do not import private or rotating project trees,
commit local sidecars, weaken coverage floors, relabel generated snapshots as
stage provenance, or claim a release gate passed when a project lane failed.

## What was completed

### Boundary and path hardening

- `infrastructure/core/project_paths.py`
  - Added `validate_project_name()` for absolute-path, traversal, empty-part,
    drive-prefix, and NUL rejection.
  - Confined intermediate project resolution under `projects/` while retaining
    the intentional managed leaf-symlink lifecycle contract.
- `infrastructure/core/script_discovery.py`
  - Configured analysis scripts are now confined to the resolved project
    `scripts/` tree and reject traversal and external symlink escapes.
- `infrastructure/core/files/cleanup.py` and `cleanup_root.py`
  - Cleanup refuses symlinked output roots and validates project names.
- `scripts/pipeline/stage_05_copy.py`
  - Low-level project arguments are validated before output paths are built.

### Runtime and secure execution

- `infrastructure/core/runtime/_python_env.py`
  - Added `validate_analysis_script_path()`.
  - Fixed explicit empty environment handling.
  - Redacts credential-like environment variables by default; live analysis
    integrations require `ANALYSIS_ALLOW_SECRETS=1`.
- `infrastructure/core/analysis_pipeline.py`
  - Rejects analysis scripts outside the project boundary as a failed stage.
- `infrastructure/orchestration/secure_run.py`
  - Secure mode loads malformed project configuration strictly.
  - Project settings cannot disable secure hashing or manifests.
  - Explicit no-PDF requests fail; an all-target no-op also fails.
  - A secure processor must create a distinct output PDF and fresh hash
    evidence.
- `infrastructure/rendering/config.py` and
  `infrastructure/publishing/transmission_bookends.py`
  - Format/bookend toggles require native YAML booleans; quoted boolean values
    fail closed.

### Pipeline, artifact, and validation hardening

- Empty pipeline plans and empty executor results now fail instead of being
  treated as vacuous success.
- `scripts/pipeline/stage_02_analysis.py` returns failure when output
  verification fails.
- `infrastructure/validation/output/pipeline.py` promotes artifact,
  provenance, evidence, figure-registry, and project-design failures to
  blocking status; only explicitly advisory checks remain warnings.
- `infrastructure/core/pipeline/artifacts.py` and
  `infrastructure/project/git_guards.py` reject hidden atomic-write leftovers
  and empty public output payloads.
- Removed the interrupted active-inference artifacts:
  - `projects/templates/template_active_inference/output/.fingerprint_cache.sha256`
  - `projects/templates/template_active_inference/output/figures/.theorem_traceability_graph.097k3qip.png`
  - `projects/templates/template_active_inference/output/figures/.theorem_traceability_graph.2fum24_t.png`
- Refreshed the active-inference method inventory and artifact manifest.

### CI, supply chain, and documentation

- Added `scripts/audit/check_tracked_secrets.py`, scanning every tracked text
  blob for high-confidence GitHub, AWS, OpenAI, and private-key material while
  reporting only path/line/type evidence.
- Wired the secret scan into CI and the pre-push guard.
- Pinned and checksum-verified actionlint and elan installers; pinned uv
  installer paths.
- Aligned `template_template` with the repository Python 3.10 floor and
  regenerated its standalone lockfile.
- Updated pipeline contracts, runtime/security documentation, generated counts,
  changelog, and the open-only root backlog in `TO-DO.md`.

## Verification evidence

The following evidence was collected before and after publication:

- Full infrastructure suite: `9,586 passed, 2 skipped`.
- Regression suite: `55 passed, 1 warning`.
- Exact pre-push hook: `12 passed` plus generated-artifact, secret,
  confidentiality, no-mocks, and stand-in checks.
- Published-commit health gate: passed with `clean_checkout: true`, Ruff,
  Ruff-format, Bandit, no-mocks, confidentiality, generated-artifact, drift,
  docs, roster, publication-record, methods-plan, public-capability, and
  architecture checks all green.
- Published-commit mypy: zero errors across `1,476` source files.
- Source-only strict publication audit: all 24 public projects passed with
  zero findings.
- Git verification after push:
  - `HEAD == origin/main == 2dc88a7f6e740717b259b189c0cca10c5d24f501`
  - `git rev-list --left-right --count main...origin/main` -> `0 0`
  - target worktree -> clean

## Known blockers and decisions

### `PUBLIC-MATRIX-1` remains open

The bounded serial public matrix covered all 24 canonical exemplars. Twenty-
three lanes passed their declared project floors. The
`template_active_inference` lane ran 683 passing tests, 1 skipped test, and 51
deselected tests, but measured `89.35%` against its declared `90%` floor. The
combined matrix coverage was `94.47%`.

Do not lower the active-inference floor or convert the lane to advisory status.
The next review should inspect the quick-profile marker selection and add
real, no-mock tests for uncovered behavior, especially the direct recompute and
sheaf-track paths. Re-run the single lane before re-running the full matrix:

```bash
uv run python scripts/pipeline/stage_01_test.py \
  --project templates/template_active_inference \
  --project-only \
  --profile quick \
  --project-workers serial
```

### `RENDERED-PROVENANCE-1` remains open

The strict source-only publication audit passes, but the rendered strict audit
returns 24 review-required findings with diagnostic code
`METHODS.STAGE_PROVENANCE_UNAVAILABLE`. The current artifact manifests are
integrity snapshots with `stage_name: current-output-snapshot`; they are not
stage-level lineage.

This distinction is intentional. Do not rewrite the manifests to claim
provenance that was not produced. Either run the canonical `PipelineExecutor`
stages for each public exemplar and retain their true stage manifests, or add a
truthful source/config/output fingerprint bridge and a corresponding release
validator. Review output churn carefully after any pipeline run.

### Other open backlog rows

The current canonical backlog is in `TO-DO.md`:

- `CONFIG-FAIL-CLOSED-1`: strict release token/source-layout/freshness checks.
- `PROJECT-EXECUTION-BOUNDARY-1`: complete symlink and subprocess/network
  policy.
- `SECURE-RUN-1`: isolated subprocess/process-group cleanup boundary.
- `SECRET-SCAN-1`: staged-diff scanning and credential-rotation handoff.
- `PUBLIC-CAPABILITY-PARITY-1`: observed capability manifest per exemplar.
- `RELEASE-METADATA-1`: credential-free external metadata receipts and
  remaining installer/branch-protection review.
- `MODULARITY-1`: split the three advisory modules over 800 lines without
  breaking public imports.

## Ordered continuation checklist

1. Fetch first and prove the starting branch state:

   ```bash
   git fetch --prune origin
   git rev-list --left-right --count main...origin/main
   git status --short --branch
   ```

2. Read `AGENTS.md`, `TO-DO.md`, this handoff, and the relevant local
   `AGENTS.md` files before editing. Keep all changes inside this public
   repository and preserve unrelated parent-worktree changes.

3. Re-run the active-inference lane with `--profile quick`, inspect the
   term-missing report, and add targeted behavior tests rather than changing
   the floor or hiding source from coverage.

4. Design and implement a deterministic public-matrix receipt containing the
   roster revision, command/profile, per-project declared floor, exit status,
   timeout status, coverage result, and output-isolation result. Add a negative
   control for a missing project result and a coverage-floor failure.

5. Resolve rendered provenance truthfully. Prefer real stage manifests and
   source/config/output fingerprints over inferred or relabeled lineage.

6. Run the strict rendered audit and inspect every changed output. Remove only
   known disposable test churn; never use broad reset or checkout commands.

7. Run the focused and repository gates:

   ```bash
   uv run pytest tests/regression/ --no-cov --timeout=120 -q
   uv run pre-commit run pre-push-quick --hook-stage pre-push --all-files
   uv run python -m infrastructure.core.health --json --quiet --workers 4
   uv run python -m infrastructure.validation.cli publication-audit --all-public --strict --format json
   uv run python -m infrastructure.validation.cli publication-audit --all-public --rendered --strict --format json
   ```

8. Run `git diff --check`, inspect the complete staged diff, commit
   intentionally, push `main`, fetch again, and prove equal local/remote SHAs
   plus a clean target worktree.

## Handoff acceptance probes

A receiving agent should be able to answer these without re-deriving the prior
session:

- What exact commit is published? `2dc88a7f6e740717b259b189c0cca10c5d24f501`.
- Is the target clean and synchronized? Yes, at handoff; verify again before
  editing.
- Which public lane prevents a zero-failure release? `template_active_inference`
  at `89.35%` versus `90%`.
- Why does rendered publication still require review? Current manifests are
  integrity snapshots, not stage-level provenance.
- Which root file is authoritative for remaining work? `TO-DO.md`.
- What must never be done? Lower the floor, fabricate provenance, commit
  private sidecars, or overwrite unrelated parent-worktree changes.
