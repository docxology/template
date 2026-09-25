# Evidence Validation Standards

## Overview

How run-derived claims become acceptable evidence in this repository. Distilled
(in spirit, not code — MIT) from OpenResearch's orx-evidence contract: a claim
that originates from an executed run is only as good as the log that backs it.
These rules apply to pipeline runs, per-project analysis scripts, benchmark
sweeps, and any agent-authored "it passed" assertion.

## The Invariants

### 1. Run logs are the evidence channel

A run-derived claim is acceptable **only if** the log for that run:

- **Identifies the variant** under test (project, parameter vector, model,
  config profile — enough to distinguish it from any sibling run).
- **Echoes the effective config** actually applied (not the intended config:
  the resolved values after defaults, env vars, and overrides).
- **Prints the final metrics/summary** (the numbers the claim rests on, with
  denominators and units where relevant).

A log missing any of the three does not license a claim. Silence is not
evidence.

### 2. Exit status is not a result

Never accept a run-derived claim from run status alone. `exit 0` means the
process terminated cleanly — it says nothing about what the process computed.
"Script completed" is not "hypothesis confirmed." A run claim must cite the
logged metrics (Invariant 1), not the return code.

### 3. Truncated output is not evidence of absence

A killed or short log (timeout, crash, partial capture, tail-only buffer)
cannot be used to **refute** a claim. Absence of metrics in a truncated log is
absence of evidence, not evidence of absence. If a log is incomplete, the only
valid statements are "unverified" and "re-run."

## Enforcement Surfaces in This Repository

| Invariant | Enforced (hard gate) | Advisory (convention) |
| --------- | -------------------- | --------------------- |
| 1 — logs identify variant, config, metrics | `tests/regression/` pinned-value tests re-derive every quantitative manuscript claim from real re-computation on CI; a claim whose supporting artifact is missing fails the gate | `data/claim_ledger.yaml` conventions (see `projects/templates/template_active_inference/data/claim_ledger.yaml`): each claim entry binds `statement`, `path`, `section`, and an `evidence` predicate — write ledger entries with the same variant/config/metric completeness a log would need |
| 2 — exit status is not a result | `infrastructure/scientific/confirmation.py` (`confirm_improvement`): a candidate is accepted only when the multi-seed mean exceeds the baseline by more than the noise band — process success never enters the acceptance test; `infrastructure/validation/` output checks reject reports that lack metric content | `tests/regression/AGENTS.md` "Updating a pinned value" requires `_provenance` entries (commit SHA, date, reason, invocation) — the provenance record, not the test exit code, is the claim's receipt |
| 3 — truncated output is not evidence of absence | Not machine-enforced; reviewers and agents must treat incomplete logs as `unverified` | Any claim citing a partial log must be marked unverified and re-run; do not downgrade a pinned value based on a truncated capture |

Where "Advisory" is the only surface, treat the rule as blocking-by-convention:
violations are review failures even though no gate fires.

## Usage Patterns

- Citing a result? Quote the log lines showing variant + effective config +
  final summary, or link the ledger/pinned-value artifact that encodes them.
- Accepting an improvement? Run `confirm_improvement` with multiple seeds and
  report `candidate_mean`, `baseline_metric`, `delta`, and `noise_band` — the
  `Confirmation.confirmed` flag, not the run's exit code, is the acceptance.
- Recording a new claim? Add a `claim_ledger.yaml` entry whose `evidence`
  predicate is machine-checkable, and keep the statement worded to exactly
  what the evidence can support.

## See Also

- [`testing_standards.md`](testing_standards.md) - Testing patterns and the no-mocks policy backing these gates
- [`reporting.md`](reporting.md) - Reporting standards: metrics with denominators, failures with categories
- [`../../tests/regression/AGENTS.md`](../../tests/regression/AGENTS.md) - Pinned-value regression tier
- [`../../infrastructure/scientific/confirmation.py`](../../infrastructure/scientific/confirmation.py) - Noise-band confirmation
