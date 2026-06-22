# AutoResearch Readiness

Deterministic planning and readiness validation for research projects.

This module adapts design ideas reviewed from
[aiming-lab/AutoResearchClaw](https://github.com/aiming-lab/AutoResearchClaw)
at commit `b5804c5fa0acecc01f56bdf52995e11bb74474cc`: explicit research
plans, stage/gate contracts, human-review policy, evidence-grounded claims,
artifact readiness reports, and run lessons. It does not implement an
autonomous idea-to-paper runner.

It also adapts measurement-discipline patterns reviewed from
[trotsky1997/autoresearch-cli](https://github.com/trotsky1997/autoresearch-cli):
metrics must come from execution, review outcomes should be explicit, and
baseline/best/noise/confidence reporting should be file-backed. The autonomous
no-human loop, lifecycle hooks, and git commit/revert behavior are intentionally
not part of this module.

## Public API

The full exported surface is defined by `__all__` in
`infrastructure/autoresearch/__init__.py` (authoritative):

```python
from infrastructure.autoresearch import (
    AutoResearchConfig,
    AutoResearchIssue,
    AutoResearchPlan,
    AutoResearchReport,
    AutoResearchStage,
    BenchmarkTask,
    BudgetPolicy,
    EXTRINSIC_QUALITY_CHECKS,
    EvidenceLink,
    ExperimentCandidate,
    INTRINSIC_QUALITY_CHECKS,
    ResearchIdea,
    ResearchProgram,
    ReviewGate,
    RunLedger,
    SecurityProfile,
    ValidationPhase,
    build_autoresearch_plan,
    load_autoresearch_config,
    mad_confidence,
    metric_unit_from_name,
    parse_metric_lines,
    parse_string_sequence,
    validate_autoresearch_plan,
    write_autoresearch_report,
)
```

`validate_autoresearch_plan(plan, project_root, phase="all")` accepts
`phase="intrinsic"` or `phase="extrinsic"` to validate pre-write structure or
post-write artifact surfaces separately.

The module composes existing template surfaces:

- `domain_profile.yaml`
- `experiment_plan.yaml`
- `pipeline.yaml`
- `output/reports/evidence_registry.json`
- `output/reports/artifact_manifest.json`
- thin-orchestrator drift checks
- bounded method ledgers: `research_program.json`, `idea_ledger.json`,
  `run_ledger.json`, `review_decisions.json`, and `benchmark_scores.json`

For benchmark stdout or similar command output, `parse_metric_lines(output)`
extracts only exact `METRIC name=value` lines into finite floats and rejects
malformed or duplicate metric evidence. `metric_unit_from_name(name)` provides
display units for conventional suffixes such as `_ms`, `_pct`, `_usd`, and
`_bytes`. `mad_confidence(values, baseline, best)` reports absolute improvement
over the median absolute deviation noise floor, returning `None` when noise is
not estimable.

## Configuration

Projects may add `autoresearch.yaml`:

```yaml
enabled: true
strict: true
topic: "Deterministic readiness"
autonomy_level: proposal_only
budget:
  max_iterations: 3
  max_wall_clock_minutes: 20
  max_llm_calls: 0
  max_cost_usd: 0.0
edit_allowlist:
  - projects/templates/template_autoresearch_project/src/
metric_direction: maximize
acceptance_policy: "Accepted ideas require evidence links and human review."
quality_checks:
  - domain_profile
  - experiment_plan
  - pipeline_contracts
  - evidence_registry
  - artifact_manifest
  - thin_orchestrators
  - method_contracts
  - review_gates
  - benchmark_tasks
  - ai_disclosure
  - security_profile
security_profile:
  enabled: true
  mode: local_deterministic
  integrity_algorithm: sha256
  network_policy: default_offline
  external_signing: false
  threat_model_frameworks: []
source_manifests:
  - output/reports/source_manifest.json
stage_gates:
  - Project Analysis
  - Output Validation
review_gates:
  - name: proposal_review
    required: true
benchmark_tasks:
  - id: readiness-smoke
    description: "Confirm readiness artifacts exist."
    grading_output: output/reports/benchmark_readiness_smoke.json
disclosure_required: true
disclosure_text: "AI-assisted AutoResearch"
required_artifacts:
  - output/data/result.csv
```

`stage_gates` entries must exactly match stage names in `pipeline.yaml`.
Unknown quality checks fail validation. In non-strict mode, readiness defects
that are not configuration errors are warnings. The extended method checks are
file-backed only: they validate allowlists, evidence-linked accepted ideas,
budget stop reasons, human review decisions, benchmark grading outputs, and
configured AI-assisted disclosure text or its manuscript injection token.

The optional `security_profile` mapping declares the deterministic security
posture used by the `security_profile` quality check: `enabled` (bool),
`mode` (`local_deterministic`), `integrity_algorithm` (`sha256`),
`network_policy` (`default_offline`), `external_signing` (bool), and
`threat_model_frameworks` (list of strings). `source_manifests` is a list of
file paths to source-manifest artifacts the plan tracks.

## CLI

```bash
uv run python -m infrastructure.autoresearch.cli plan --project templates/template_autoresearch_project
uv run python -m infrastructure.autoresearch.cli validate --project templates/template_code_project --fail-on-issues
uv run python -m infrastructure.autoresearch.cli review-packet --project templates/template_autoresearch_project
uv run python -m infrastructure.autoresearch.cli summarize --project templates/template_autoresearch_project
uv run python -m infrastructure.autoresearch.cli benchmark --project templates/template_autoresearch_project
```

Reports are written to:

- `projects/{project}/output/reports/autoresearch_readiness.json`
- `projects/{project}/output/reports/autoresearch_readiness.md`
