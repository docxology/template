# Prompt: Reproducibility audit

## Purpose

A **copy-paste template** for proving a project is **deterministically
reproducible**: fixed seeds, regenerate-from-clean, and a byte/semantic diff
showing the committed manuscript numbers and figures match what the pipeline
actually produces. Complements
[`manuscript_claim_verification.md`](manuscript_claim_verification.md) (claim
truth) by focusing on *stability of the artifacts themselves*.

Use before tagging a release or depositing to Zenodo/arXiv, or whenever
"it worked on my machine" is suspected.

Measured gates live in
[`../_generated/canonical_facts.md`](../_generated/canonical_facts.md); pipeline
semantics in [`../../AGENTS.md`](../../AGENTS.md) and
[`../RUN_GUIDE.md`](../RUN_GUIDE.md).

## Copy-paste prompt

```
You are auditing reproducibility for project [name from
docs/_generated/active_projects.md].

Establish, with commands and raw output:

1. DETERMINISM — every analysis script uses a fixed RNG seed and MPLBACKEND=Agg;
   no wall-clock/hostname/path leaks into outputs. List any nondeterministic
   source (unseeded random, set iteration, dict ordering, timestamps in data).

2. REGENERATE FROM CLEAN — wipe working outputs, run the core pipeline, and
   regenerate manuscript variables. Capture exit status per stage.

3. DIFF — compare regenerated output/<name>/ and generated manuscript variables
   against what the manuscript text asserts. Any drift is a finding with
   expected vs. committed value. Numbers hand-typed into prose instead of
   sourced from the generated-variable mechanism are a finding even if equal.

4. DOUBLE-RUN STABILITY — run the regeneration twice; a clean tree between runs
   proves determinism. Any diff between run-1 and run-2 is a hard failure.

Then propose concrete fixes (seed injection, variable-ization of hard-typed
numbers, removing timestamp leakage). Keep projects/<name>/AGENTS.md and
README.md accurate about the regeneration command and disposable-output rule.
Do not edit files under output/ by hand. Do not invent coverage numbers — cite
pytest output or canonical_facts.md.
```

## Commands (reference)

Resolve `<project>` via
[`../_generated/active_projects.md`](../_generated/active_projects.md).

```bash
uv sync

# Regenerate from clean, capture per-stage status
uv run python scripts/execute_pipeline.py --project <project> --core-only
uv run python projects/<project>/scripts/z_generate_manuscript_variables.py

# Double-run determinism: tree must be identical between runs
git stash --include-untracked -- output/<project> 2>/dev/null || true
uv run python scripts/execute_pipeline.py --project <project> --core-only
git status --porcelain output/<project>            # expect: empty on a deterministic run

# Tests back the computational claims
uv run python scripts/01_run_tests.py --project <project>

# Source + render still valid after any fix
uv run python -m infrastructure.validation.cli prerender \
  projects/<project>/manuscript --repo-root .
uv run python -m infrastructure.validation.cli pdf output/<project>/pdf/
uv run python -m infrastructure.validation.cli integrity output/<project>/
```

## Checklist

### Pre-flight

- [ ] Project resolved from `_generated/active_projects.md`; `uv sync` clean.
- [ ] Baseline `git status` recorded before regeneration.

### During audit

- [ ] Every script seeds RNG and uses `MPLBACKEND=Agg`; no timestamp/path leaks.
- [ ] Core pipeline regenerated from clean; per-stage exit status captured.
- [ ] Double-run produces an identical tree (`git status --porcelain` empty).
- [ ] Manuscript numbers trace to generated variables, not hand-typed digits.

### Reporting

- [ ] Drift table: artifact | committed | regenerated | action.
- [ ] `projects/<n>/AGENTS.md` + `README.md` state the exact regeneration command.
- [ ] No `output/` file hand-edited; no invented coverage numbers.

## See also

- [`manuscript_claim_verification.md`](manuscript_claim_verification.md) — triple-check of claim truth.
- [`pipeline_debugging.md`](pipeline_debugging.md) — when a stage fails during regeneration.
- [`comprehensive_assessment.md`](comprehensive_assessment.md) — wider repo audit.
- [`README.md`](README.md) — prompt index.
