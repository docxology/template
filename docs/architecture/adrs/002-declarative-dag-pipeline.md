# ADR 002: Declarative DAG Pipeline

## Status

Accepted

## Context

The research project template runs a multi-stage pipeline (e.g., clean → test → analyze → render → validate → publish). Hardcoding stage order and dependencies in imperative code makes the pipeline rigid and hard to modify. Different projects may need different stage configurations.

## Decision

Define the pipeline as a **declarative DAG in YAML** (`pipeline.yaml`). Each stage declares its name, script, dependencies, and optional tags. The DAG executor validates the graph (no cycles) and runs stages in topological order.

### Key Benefits

- **Clarity:** DAG structure is human-readable in YAML
- **Flexibility:** Easy to insert new stages or change order
- **Extensibility:** Projects can override stage definitions
- **Reusability:** Same executor runs any DAG configuration

### Example — Default DAG (10 stages)

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

Running `--core-only` excludes stages with the `llm` tag (leaving eight core stages).

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
