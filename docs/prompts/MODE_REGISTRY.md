# Template Workflow Mode Registry

Single reference for workflow-skill modes under `docs/prompts/`.

This registry is an original template-native mode map. It adapts the idea of an
explicit mode registry from
[Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills)
without copying ARS prompt content, schemas, or scripts.

## Metadata Vocabulary

| Field | Meaning |
| --- | --- |
| `metadata.version` | Skill contract version for routing and evals |
| `metadata.last_updated` | Date the skill contract was last reviewed |
| `metadata.status` | `active`, `experimental`, or `deprecated` |
| `metadata.data_access_level` | `raw`, `redacted`, or `verified_only` |
| `metadata.task_type` | `open-ended` or `outcome-gradable` |
| `metadata.modes` | Closed list of supported mode names for the skill |
| `metadata.related_skills` | Adjacent template skills used for handoff |

## Academic Workflows

| Skill | Mode | Oversight | Output | Handoff |
| --- | --- | --- | --- | --- |
| `template-deep-research` | `guided` | Very high | Research question, scope, search terms | `template-academic-paper` |
| `template-deep-research` | `full` | High | Research brief, corpus table, source notes | `template-literature-synthesis` |
| `template-deep-research` | `quick` | Medium | Short brief with caveats | none |
| `template-deep-research` | `lit-review` | Medium | Per-paper notes and thematic synthesis | `template-academic-paper` |
| `template-deep-research` | `fact-check` | Medium | Claim-by-claim verification report | `template-manuscript-claim-verification` |
| `template-deep-research` | `systematic-review` | High | Protocol, criteria, screening counts | `template-academic-paper` |
| `template-academic-paper` | `plan` | Very high | Section plan and evidence map | `template-deep-research` or draft |
| `template-academic-paper` | `outline` | High | Detailed outline and material gaps | draft |
| `template-academic-paper` | `full` | High | Source-layer manuscript draft | `template-manuscript-claim-verification` |
| `template-academic-paper` | `revision` | High | Revised manuscript and response notes | `template-academic-paper-reviewer` |
| `template-academic-paper` | `format` | Medium | Render-safe formatting changes | `template-validation-quality` |
| `template-academic-paper` | `citation-check` | Medium | Citation audit and repairs | `template-validation-quality` |
| `template-academic-paper` | `prose-quality` | Medium | AI-writing fingerprint scan results | finalization |
| `template-academic-paper` | `disclosure` | Medium | AI-use disclosure grounded in evidence | finalization |
| `template-academic-paper-reviewer` | `full` | High | Read-only review package | `template-academic-paper` |
| `template-academic-paper-reviewer` | `quick` | Low | Triage review | `template-academic-paper` |
| `template-academic-paper-reviewer` | `methodology-focus` | Medium | Methods and reproducibility critique | `template-academic-paper` |
| `template-academic-paper-reviewer` | `re-review` | Medium | Revision traceability matrix | `template-academic-pipeline` |
| `template-academic-paper-reviewer` | `calibration` | Medium | Rubric calibration caveats | reviewer setup |
| `template-academic-pipeline` | `full` | Very high | Research-to-publication stage status | all academic skills |
| `template-academic-pipeline` | `existing-paper` | High | Integrity-first review path | `template-academic-paper-reviewer` |
| `template-academic-pipeline` | `reviewer-comments` | High | Revision and re-review plan | `template-academic-paper` |
| `template-academic-pipeline` | `finalize` | High | Readiness report and validation gates | release workflow |

## Existing Template Workflows

| Skill | Modes | Primary handoff |
| --- | --- | --- |
| `template-workflows` | `router` | selected child skill |
| `template-comprehensive-assessment` | `full-audit` | validation, claim verification, reproducibility |
| `template-pipeline-debugging` | `stage-triage`, `resume` | validation or reproducibility |
| `template-reproducibility-audit` | `double-run`, `release-readiness` | claim verification |
| `template-manuscript-claim-verification` | `claim-inventory`, `pre-submission`, `reference-existence` | academic paper or validation |
| `template-manuscript-cross-references` | `registry-audit` | validation |
| `template-manuscript-creation` | `scaffold`, `from-brief` | academic paper |
| `template-literature-synthesis` | `per-paper`, `corpus`, `gap-analysis` | academic paper |
| `template-validation-quality` | `prerender`, `markdown`, `pdf`, `integrity` | pipeline/debugging |
| `template-methods-orchestration` | `audit`, `plan`, `repair` | validation, claim verification, reproducibility |
| `template-code-development` | `implementation` | tests |
| `template-test-creation` | `pytest`, `coverage` | code development |
| `template-feature-addition` | `end-to-end` | code, tests, docs |
| `template-refactoring` | `behavior-preserving` | tests |
| `template-infrastructure-module` | `package` | code, tests, docs |
| `template-documentation-creation` | `author-docs` | comprehensive assessment |
| `template-agentic-use` | `inventory`, `route`, `harden`, `external-review` | template-workflows, infrastructure-skills; Steward OS, AutoResearch CLI, LEANN, and similar references remain attributed and non-vendored/non-installed by default |

## Provenance Discipline

- Use the evidence registry, claim ledgers, artifact manifests, snapshots,
  validation reports, and generated manuscript variables for paper-facing claims.
- Treat `data_access_level: verified_only` skills as consumers of checked
  artifacts; they should not introduce new factual claims without routing back to
  a raw or redacted upstream skill.
- Benchmark or skill-eval claims should disclose sample size, scoring method,
  caveats, and whether results are self-scored.
