# Doctor module — agent reference

This document is the agent-facing companion to `SKILL.md` and
`README.md`. It is stable across versions; treat each section as a
contract.

## Calling sequence

Recommended flow for an agent diagnosing and repairing a checkout:

```bash
# 1. Run capabilities once to learn what's available.
uv run python -m infrastructure.doctor capabilities > /tmp/doctor_caps.json

# 2. Diagnose. Parse the JSON for findings + exit code.
uv run python -m infrastructure.doctor --json diagnose > /tmp/doctor_diag.json
EXIT=$?
# EXIT codes: 0 healthy, 1 warn, 2 error, 3 critical, 4 regression, 64 usage.

# 3. If anything actionable, dry-run a plan first.
uv run python -m infrastructure.doctor --json fix --plan > /tmp/doctor_plan.json

# 4. Apply at the appropriate therapy level.
uv run python -m infrastructure.doctor --json fix --apply > /tmp/doctor_applied.json

# 5. Inspect `applied[*].action_id` to undo selectively if needed.
uv run python -m infrastructure.doctor --json undo --action-id "<id>"
```

Every command writes JSON on stdout when `--json` is set, leaving
stderr free for progress/refusal messages. Exit codes are stable.

## JSON schema (stable)

`diagnose` and `fix` produce a top-level object:

```jsonc
{
  "findings": [{
    "code": "DOC301",
    "title": "...",
    "severity": "warn",                 // info | warn | error | critical
    "healthy": false,
    "description": "...",
    "evidence": { /* detector-specific */ },
    "repair_levels": [{
      "level": "conservative",          // conservative | moderate | radical
      "fix_id": "fix_clean_pycache",
      "description": "..."
    }]
  }],
  "applied":  [/* MutateRecord[] */],
  "skipped":  [/* FixPlan[] (e.g. from --plan) */],
  "failed":   [/* MutateRecord[] with applied=false and error set */],
  "overall_score":      87.4,           // 0–100
  "dimension_scores":   { "environment": 100.0, ... },
  "exit_code":          1
}
```

`MutateRecord` is also the line format of `.doctor/actions.jsonl`:

```jsonc
{
  "action_id": "20260510T161603Z_a3f1b9c2",
  "timestamp_utc": "2026-05-10T16:16:03+00:00",
  "fix_id": "fix_clean_pycache",
  "finding_code": "DOC301",
  "therapy": "conservative",
  "title": "Remove cache directory infrastructure/core/__pycache__",
  "backup_dir": ".doctor/backups/20260510T161603Z_a3f1b9c2",
  "pre_hashes":  { "/abs/path": "sha256-hex-or-'absent'" },
  "post_hashes": { "/abs/path": "sha256-hex-or-'absent'" },
  "affected_paths": ["/abs/path"],
  "reversible": true,
  "applied": true,
  "error": null
}
```

## Therapy levels — when to pick which

| Level         | When to apply                                                   |
| ------------- | --------------------------------------------------------------- |
| conservative  | Always safe. Caches, executable bits, missing local hook shims. |
| moderate      | Reproducible side effect (`uv sync`). Lockfile is restorable but the venv is not — fix is marked `reversible=false`. |
| radical       | Destructive but fully backed up. Deletes orphan output trees. Undo restores byte-for-byte. |

Agents should default to `--apply` (conservative only). Step up to
`--moderate` when `DOC402` (lockfile drift) is present, and to
`--aggressive` only when the user has confirmed orphan output directories
should be deleted.

## Refusals and how to read them

`mutate()` raises `DoctorSafetyError` (never a silent rewrite) for:

* path outside the repo,
* path inside `.doctor/`,
* unknown `action_kind` (programming error — fix the fixer),
* corrupt journal during `undo`,
* post-restore hash mismatch during `undo`.

The CLI converts these to `EXIT_CRITICAL (3)` with a stderr message.
Agents should treat them as **stop and ask** signals: they imply an
unexpected file changed under the doctor's feet, which is the exact
situation the safety contract is designed to refuse.

## Idempotence guarantees

* Detectors: two runs on the same tree produce findings with identical
  `(code, healthy, severity)` triples. Evidence may include path lists
  that are sorted but otherwise equal.
* Conservative fixers: re-applying a successfully-applied conservative
  fix is a no-op (the detector flips to `healthy=true` first).
* `undo` of a `undo` is not supported (`reversible=false` on the undo
  record). To redo, re-run the original fixer.

## Extending — quick reference

* New detector → add it to the matching concern module under
  `infrastructure/doctor/detectors/` (`tooling.py`, `layout.py`,
  `hygiene.py`, `state.py`), append it to the `DETECTORS` tuple in
  `infrastructure/doctor/detectors/registry.py`, allocate `DOC<NNN>` in
  the right band.
* New fixer → `infrastructure/doctor/fixers.py`, register in
  `FIXER_REGISTRY`, ensure the new `fix_id` appears in some
  `RepairLevel`.
* New action kind → register a handler via
  `infrastructure.doctor.safety.register_handler(kind, fn)`. The
  handler may only touch paths in `plan.affected_paths` and may raise
  any exception on failure.

## Cross-references

* `infrastructure/core/health.py` — CI gate runner (mypy, ruff,
  bandit, no-mocks). Complementary; doctor diagnoses local state and
  produces structured remediations.
* `scripts/health-check.sh` — bash pre-flight check. Overlap with
  `DOC1xx` family; the doctor's findings are richer and machine-readable.
* `infrastructure/validation/` — content validators (PDFs, markdown).
  Doctor does **not** validate output contents; that remains
  `validation`'s job. Doctor cares only about the conditions that
  govern whether a validation run can begin at all.
