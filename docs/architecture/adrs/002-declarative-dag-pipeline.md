# ADR 002: Declarative DAG Pipeline

## Status

Accepted

## Context

The research project template runs a multi-stage pipeline (e.g., clean → test → analyze → render → validate → publish). Hardcoding stage order and dependencies in imperative code makes the pipeline rigid and hard to modify. Different projects may need different stage configurations.

## Decision

Define the pipeline as a **declarative DAG in YAML** (`pipeline.yaml`). Each stage declares its name, script, dependencies, and optional tags. The DAG executor validates the graph (no cycles) and runs stages in topological order.

Current declarations also require a unique stable lowercase `key` and exactly
one executable `script` or `method`. Scripts use explicit repository-relative
Python paths. Prose method descriptions belong in `contract.definition_of_done`.
Unknown fields, unknown original dependencies, duplicate identities, and YAML
type coercions fail validation. Sequence fields use lists, boolean flags use
booleans, retry counts are non-negative integers, and hook timeouts are positive
integers. Explicit filtering retains a receipt of removed dependency edges.

Project plugins use the same declaration parser and require an explicit output,
acceptance, and failure-code contract. Plugin names and keys cannot replace core
identities; a failed merge leaves the original DAG unchanged.

### Key Benefits

- **Clarity:** DAG structure is human-readable in YAML
- **Flexibility:** Easy to insert new stages or change order
- **Extensibility:** Projects can override stage definitions
- **Reusability:** Same executor runs any DAG configuration

### Example — Original default selection (10 stages)

This example records the core+LLM selection when the ADR was accepted; it is
not the live stage inventory. The accepted decision is the YAML-owned DAG, not
a fixed stage count. Current execution defaults to the offline `--mode core`
selection; `--mode live` explicitly enables model-assisted stages. Use the generated table in
[`docs/RUN_GUIDE.md`](../../RUN_GUIDE.md#core-pipeline-stages--executive-reporting)
for current names, dependencies, tags, and failure modes.

```yaml
stages:
  - name: Clean Output Directories
    method: _run_clean_outputs
    tags: [core, clean]
  - name: Environment Setup
    script: scripts/pipeline/stage_00_setup.py
    depends_on: [Clean Output Directories]
    tags: [core]
  - name: Infrastructure Tests
    script: scripts/pipeline/stage_01_test.py
    args: [--infra-only, --verbose, --infra-scope, pipeline-smoke]
    depends_on: [Environment Setup]
    tags: [core, tests]
  - name: Project Tests
    script: scripts/pipeline/stage_01_test.py
    args: [--project-only, --verbose]
    depends_on: [Environment Setup]
    tags: [core, tests]
  - name: Project Analysis
    script: scripts/pipeline/stage_02_analysis.py
    depends_on: [Project Tests]
    tags: [core]
  - name: PDF Rendering
    script: scripts/pipeline/stage_03_render.py
    depends_on: [Project Analysis]
    tags: [core]
  - name: Output Validation
    script: scripts/pipeline/stage_04_validate.py
    depends_on: [PDF Rendering]
    tags: [core]
  - name: LLM Scientific Review
    script: scripts/pipeline/stage_06_llm_review.py
    args: [--reviews-only]
    allow_skip: true
    depends_on: [Output Validation]
    tags: [llm]
  - name: LLM Translations
    script: scripts/pipeline/stage_06_llm_review.py
    args: [--translations-only]
    allow_skip: true
    depends_on: [Output Validation]
    tags: [llm]
  - name: Copy Outputs
    script: scripts/pipeline/stage_05_copy.py
    depends_on: [Output Validation]
    tags: [core]
```

In this recorded selection, `--core-only` excludes the two `llm` stages and
leaves eight core stages. New opt-in stages have since been added to the live
YAML without changing the architectural decision.

## Consequences

### Positive

- Pipeline structure is visible and auditable at a glance
- Adding a stage requires only a YAML entry
- Cycle detection is automatic (validated during DAG construction)

### Negative

- YAML syntax errors possible (but caught early at load time)
- Circular dependency risk exists (validated during DAG construction)

## References

- [`infrastructure/core/pipeline/dag.py`](../../../infrastructure/core/pipeline/dag.py) — DAG engine
- [`infrastructure/core/pipeline/pipeline.yaml`](../../../infrastructure/core/pipeline/pipeline.yaml) — Default definition
- [`infrastructure/core/AGENTS.md`](../../../infrastructure/core/AGENTS.md) — Pipeline module docs
- [`docs/RUN_GUIDE.md`](../../RUN_GUIDE.md) — User-facing stage guide
- [`core/workflow.md`](../../core/workflow.md) — Workflow explanation
