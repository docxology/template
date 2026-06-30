# Abstract {#sec:abstract}

This paper describes a small, tested **domain language for specifying
controlled methods** — the **methods-paper exemplar** of the
[Research Project Template](https://github.com/docxology/template). Unlike a
results paper, this manuscript's subject is the methodology itself: a
controlled vocabulary, a unit system with dimensional safety, four staged
validation gates, and a deterministic compiler, implemented in
`projects/templates/template_methods_paper/src/methods_dsl/` and described
section by section in [@sec:methodology]. The domain language's vocabulary is
informed by BPL (Biology Programming Language,
[@bpl2026]), an upstream reference that encodes laboratory protocols as
programs with biology-native types, staged validation, and deterministic
compilation; this exemplar generalizes BPL's intent vocabulary and pipeline
shape from wet-lab protocols to any controlled procedure.

A `Method` is a name, a set of typed parameters and resources, and an
ordered, dependent set of steps — constructed directly as frozen Python
dataclasses (`src/methods_dsl/model.py`) rather than parsed from new text
syntax. Every `Quantity` carries a unit that resolves to one of
{{DSL_UNIT_COUNT}} controlled units across six dimensions, and every step
names one of {{DSL_STEP_KIND_COUNT}} controlled-vocabulary intents
(`src/methods_dsl/vocabulary.py`), executable on one of {{DSL_TARGET_COUNT}}
backends. {{DSL_GATE_COUNT}} staged gates — structural, semantic, plan, and
target — validate a method before `compile_method`
(`src/methods_dsl/compiler.py`) deterministically schedules it with Kahn's
algorithm [@kahn1962topological] and hashes the canonical plan with SHA-256.

We demonstrate the language on {{EXAMPLE_METHOD_COUNT}} worked example
methods spanning both domains BPL's design targets and the domains it
generalizes to: a manual wet-lab preparation
(`PBSPreparation`, {{PBS_STEP_COUNT}} steps, target `{{PBS_TARGET}}`,
plan hash `{{PBS_PLAN_HASH}}`) and an automated instrument-calibration
procedure (`SensorCalibrationSweep`, {{CALIBRATION_STEP_COUNT}} steps,
target `{{CALIBRATION_TARGET}}`, plan hash `{{CALIBRATION_PLAN_HASH}}`).
Live re-compilation determinism check: **{{DETERMINISM_CHECK}}**. Across both
methods, {{TOTAL_GATES_PASSED}} of {{TOTAL_GATES_RUN}} staged-gate
evaluations pass. A demonstration provenance hash-chain
(`src/methods_dsl/trust.py`) of length {{TRUST_CHAIN_LENGTH}} verifies as
**{{TRUST_CHAIN_VERIFIED}}**.

Contributions are **methodological** and **architectural**. On the methods
side, we show that a controlled vocabulary expressed as typed dataclasses —
not a parsed grammar — is sufficient to reproduce BPL's core safety
properties (dimensional safety, staged validation, deterministic
compilation) at a scope appropriate for a template exemplar. On the
architecture side, the DSL is covered above the 90% project gate by a
zero-mock test suite, generates {{ARTIFACT_TOTAL}} artifacts
({{ARTIFACT_FIGURES}} figures, {{ARTIFACT_DATA_FILES}} data files,
{{ARTIFACT_REPORTS}} reports) per pipeline run, and injects reproducibility
metadata (configuration hash `{{CONFIG_HASH}}`, build timestamp
`{{GENERATION_TIMESTAMP}}`) into [@sec:reproducibility].

**Keywords:** {{CONFIG_KEYWORDS}}
