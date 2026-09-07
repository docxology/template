# Comprehensive research-software and manuscript review prompt

Use this copy-paste prompt to launch an implementation-oriented, long-horizon
review of a research-software package and its publication surfaces. It combines
the repository's comprehensive-assessment, manuscript, reproducibility, and
publication contracts without registering an additional routing skill.

The phrase "all variables" below means every changeable, measured, configured,
or generated fact. Stable prose and mathematical constants remain authored
content unless the target project declares otherwise.

Canonical template references:

- [Manuscript semantics and token injection](../../../guides/manuscript-semantics.md)
- [Comprehensive-assessment workflow](../SKILL.md)
- [Publication-readiness audit](../../publication-audit/SKILL.md)
- [Reproducibility audit](../../reproducibility-audit/SKILL.md)
- [Control-positive code-project exemplar](../../../../projects/templates/template_code_project/)

## Prompt

Copy the block below and replace the angle-bracketed inputs.

~~~text
DEEP RESEARCH-SOFTWARE, MANUSCRIPT, AND SCHOLARSHIP REVIEW

INPUTS

TARGET_REPO: <absolute path or repository URL>
TEMPLATE_REPO: <pinned docxology/template checkout and revision>
PROJECT: <qualified project name or standalone package>
CANONICAL_INPUTS: <datasets, configurations, checkpoints, or "discover from repo">
EXPECTED_OUTPUTS: <PDF, HTML, DOCX, EPUB, package, reports, figures, release bundle>
DOMAIN OR TARGET VENUE: <optional>
AUTHORIZED_ACTIONS: inspect, edit, test, regenerate, and render locally.

Unless separately authorized, do not commit, push, tag, publish, deposit,
overwrite closed historical evidence, change external services, or exercise
owner-only release authority.

OBJECTIVE

Deeply review and improve the complete research artifact:

- software architecture, correctness, APIs, dependencies, security, packaging,
  portability, performance, and reproducibility;
- documentation, examples, configuration, installation, and troubleshooting;
- tests, coverage quality, CI, failure behavior, and scientific invariants;
- analysis methods, statistics, data lineage, estimands, and negative outcomes;
- manuscript structure, prose, equations, formalism, claims, and limitations;
- automatic manuscript-variable injection through docxology/template;
- tables, visualizations, captions, alt text, long descriptions, and accessibility;
- citations, related work, novelty positioning, and all scholarship;
- generated artifacts, provenance, freshness, rendering, and release boundaries.

This is a review-and-remediation task, not merely a request for recommendations.
Implement every safe in-scope improvement, regenerate downstream artifacts from
their producers, and verify the resulting source-current candidate.

DEFINITIONS

A "dynamic manuscript value" is any fact that could change when data,
configuration, code, environment, analysis, or release identity changes. This
includes counts, sample sizes, exclusions, denominators, estimates, uncertainty
intervals, p-values, thresholds, parameters, versions, dates, dataset identities,
artifact counts, table entries, figure statistics, caption statistics, and
release metadata. Stable prose and mathematical constants need not be tokenized,
but justify any literal that resembles a generated result.

"Auto-injected" means that a value:

1. is computed deterministically from its canonical source;
2. has one authoritative producer;
3. appears in a declared variable registry or schema;
4. is written to the project's machine-readable variable artifact;
5. is consumed by the template hydration/render pipeline;
6. carries type, unit, formatting, provenance, and consumer information; and
7. is verified against the final rendered surfaces.

A token whose upstream producer contains a manually copied result is not
auto-injected.

"Fresh" means canonical inputs, configuration, code revision, dependency lock,
analysis outputs, variables, tables, figures, captions, hydrated manuscript,
provenance receipts, and rendered outputs belong to the same build lineage.
Timestamps alone do not establish freshness.

"Verified" means supported by current-session commands, inspected artifacts,
hashes, and adversarial checks--not confidence, agent agreement, file existence,
an old receipt, or a previously green test run.

SUCCESS PREDICATE

Completion may be claimed only when:

1. All applicable repository and nested instructions have been followed.
2. Pre-existing dirty work, nested repositories, confidential paths, historical
   evidence, and unrelated user changes remain preserved.
3. Every review lane has an inventory, findings, implemented improvements,
   validation evidence, and residual-risk status.
4. No remediable critical or high-severity in-scope defect remains.
5. Every dynamic manuscript value has one canonical producer and an audited
   injection path; no hard-coded duplicate, shadow default, unresolved token,
   silent fallback, stale value, mixed generation, unit conflict, or
   source/render disagreement remains.
6. Analysis, variables, tables, figures, captions, manuscript, provenance, and
   renders have been regenerated in dependency order.
7. Every substantive claim maps to current analysis evidence or a verified
   scholarly source, and its wording does not exceed that evidence.
8. Statistics, captions, tables, figures, abstract, results, discussion, and
   documentation use consistent populations, filters, denominators, and values.
9. Required tests and quality gates pass without weakened assertions, hidden
   failures, unjustified skips, excessive mocking, or existence-only tests.
10. Final outputs have received structural, semantic, accessibility, and visual
    inspection appropriate to each format.
11. A fresh-context adversarial review finds no credible way for the artifact to
    satisfy this prompt's wording while violating its intent.

WORKING METHOD

Begin by capturing the baseline:

- repository path, branch, upstream, revision, dirty state, and nested repos;
- target and template revisions and their compatibility contract;
- relevant AGENTS.md, README, CLAUDE.md, contribution, manuscript, and release
  instructions;
- dependency locks, environments, pipeline entry points, generated-artifact
  policy, canonical inputs, current outputs, and release authority.

Do not update either repository or discard local changes merely to simplify the
audit. If isolated validation is needed, use a safe temporary checkout or
equivalent recovery-preserving approach.

Maintain an issue ledger containing: ID, area, severity, evidence, root cause,
affected claims or artifacts, implemented fix, validation, status, and residual
risk.

When parallel agents are available, delegate bounded independent lanes such as
software/tests, variables/provenance, statistics, visuals/accessibility, and
scholarship. Preserve early independence and use a fresh reviewer for the final
adversarial audit. Agreement is not evidence.

REVIEW AND IMPROVEMENT REQUIREMENTS

1. Software package and architecture

- Inspect algorithms, interfaces, data models, input validation, error handling,
  typing, serialization, numerical behavior, concurrency, resource handling,
  security, confidentiality, dependency risk, packaging, installation, and
  backward compatibility.
- Keep business logic in importable source modules and scripts as thin
  orchestrators, following the target and template architecture.
- Check malformed, empty, duplicate, non-finite, adversarial, and boundary
  inputs. Reject invalid scientific inputs rather than silently coercing or
  dropping them.
- Verify deterministic behavior where promised, including ordering, seeds,
  locale, timezone, concurrency, and reproducible-build settings.
- Inspect licenses, dependency pins, package metadata, command-line entry points,
  clean installation, and documented supported environments.

2. Documentation

- Verify installation, quick-start, API, configuration, architecture, pipeline,
  examples, output inventory, troubleshooting, limitations, data availability,
  and reproduction instructions against executable behavior.
- Run documented commands and examples where practical.
- Remove stale paths, duplicated configuration, invented metrics, dead links,
  and undocumented assumptions.
- Generate measured counts or changing facts from authoritative producers rather
  than copying literals into long-lived documentation.
- Keep documentation, package metadata, manuscript methods, and actual code
  behavior mutually consistent.

3. Tests and CI

- Review test meaning, not only coverage percentage.
- Add or improve unit, integration, end-to-end, regression, property, boundary,
  malformed-input, deterministic-build, schema, serialization, packaging,
  hydration, rendering, and failure-path tests as applicable.
- Exercise real scientific producers and renderers. Do not replace the behavior
  under review with mocks unless repository rules explicitly permit a narrow
  boundary substitution.
- Test scientific invariants, variable completeness, stale-artifact rejection,
  provenance mismatches, missing inputs, and negative outcomes.
- Respect repository coverage and quality gates. Do not lower thresholds,
  weaken assertions, convert failures into skips, or test only file existence.
- Run each project suite in the isolation required by the repository.

4. Automatic variable injection through docxology/template

Build a source-to-render map:

canonical inputs
-> analysis producers
-> typed statistical outputs
-> manuscript-variable generator
-> machine-readable variable artifact
-> hydrated manuscript
-> figures, tables, captions, and metadata
-> final rendered formats
-> provenance and release receipts.

Use the target project's declared equivalent of the canonical template pattern:

- project-owned computation in an importable manuscript-variable module;
- a thin z_generate_manuscript_variables.py-style orchestrator;
- a complete output/data/manuscript_variables.json-style artifact;
- {{UPPERCASE_TOKEN}} or the project's declared token syntax;
- hydration through the pinned template implementation of
  write_resolved_manuscript_tree() or its documented successor;
- rendering from the hydrated output/manuscript/ tree;
- strict analysis-output requirements for authoritative builds.

Do not blindly copy filenames if the target declares a newer compatible
contract. Record the exact template revision and implementation actually used.

Create a variable registry containing, for every dynamic value:

- token or field name;
- semantic definition;
- canonical source;
- producer function or command;
- raw type and rendered type;
- unit;
- precision and formatting rule;
- missing-value policy;
- input/configuration hashes;
- producer and repository revisions;
- every manuscript, table, figure, caption, alt-text, metadata, or documentation
  consumer;
- verification result.

Preserve raw typed scientific values upstream and derive presentation strings at
the rendering boundary. A manually formatted string must not become the
scientific source of truth.

Inventory every dynamic literal across the title page, abstract, body,
equations, methods, results, tables, captions, alt text, long descriptions,
appendices, supplement, README, release notes, and publication metadata.
Convert bypassing literals to injected variables or justify them as stable.

Fail closed--or explicitly allowlist with justification--on:

- missing, unknown, duplicate, unused, or unresolved tokens;
- empty, non-finite, malformed, or wrong-type values;
- unavailable authoritative analysis outputs;
- draft N/A fallbacks in a release candidate;
- source, configuration, environment, or revision mismatches;
- hard-coded copies of generated values;
- hand-edited hydrated manuscripts or generated outputs;
- stale downstream artifacts after an upstream change.

Add tests that extract all manuscript tokens and prove that each is produced,
valid, consumed, and resolved. Verify the final PDF, HTML, DOCX, EPUB, tables,
captions, and other outputs contain current values and no unresolved markers.

Never edit generated JSON, tables, figures, hydrated Markdown, PDFs, or receipts
to clear a gate. Fix the producer and regenerate in dependency order.

5. Statistical and scientific validity

- Identify the research question, estimand, population, comparator, sampling
  unit, experimental unit, unit of analysis, independence assumptions, and
  evidence class for every major analysis.
- Recompute sample sizes and denominators from canonical records. Report
  attempted, completed, analyzable, included, excluded, failed, unavailable,
  non-converged, and promoted counts separately.
- Check randomization, pairing, clustering, repeated measures, stopping rules,
  preprocessing, exclusions, missingness, leakage, duplicated identities or
  seeds, post-selection inference, and unequal comparator treatment.
- Verify assumptions, convergence, identifiability, residual behavior,
  influential observations, sensitivity analyses, and robustness to defensible
  alternative specifications.
- Report effect sizes and uncertainty rather than p-values alone. Define interval
  type and level, sidedness, test statistic, degrees of freedom, multiplicity
  correction, software implementation, and analysis population.
- Ensure bootstrap, permutation, and cross-validation procedures resample the
  correct independent unit and preserve pairing or clustering.
- Do not interpret statistical non-significance as equivalence without a
  justified equivalence margin and appropriate analysis.
- For simulation or optimization studies, report seed policy, replicate identity,
  Monte Carlo uncertainty, failures, non-convergence, and the boundary between
  synthetic, historical, comparator, and current empirical evidence.
- Verify units, transformations, rounding, interval endpoints, and displayed
  precision across data, prose, tables, figures, and captions.

6. Figures, tables, captions, and accessibility

- Generate all figures and tables deterministically from canonical data. Prohibit
  manual numeric or graphical edits.
- Maintain a fail-closed figure/table registry binding each label, filename,
  generator, input hashes, analysis population, statistics, caption, alt text,
  long description, and visual-QA result to an existing artifact.
- Verify scales, axes, units, legends, panel order, transformations, baselines,
  aggregation, smoothing, binning, truncation, uncertainty, statistical
  annotations, denominators, and sample sizes against source data.
- Prefer visual forms that reveal distributions, uncertainty, outliers, failures,
  and sample size. Avoid misleading axes, hidden denominators, decorative
  precision, overplotting, and success-only displays.
- Make captions self-contained: define panels, population, conditions, units,
  n and what it counts, exclusions, summary statistic, interval or error-bar
  meaning, test, multiplicity correction, and relevant effect estimate.
- Auto-inject every dynamic value appearing in a caption, alt description, table,
  or figure annotation.
- Provide meaningful alt text and long descriptions where needed. Do not rely on
  color or spatial position alone.
- Use colorblind-safe palettes, sufficient contrast, redundant encodings,
  distinguishable line styles, readable type, accessible table structure, and
  grayscale-safe distinctions.
- Verify cross-references, numbering, panel labels, resolution, vector integrity,
  clipping, font embedding, links, reading order, and placement in every format.
- Visually inspect the rendered outputs. Structural PDF validity, searchable
  text, or file existence does not establish correct rendering or PDF/UA.
- Verify image provenance, licenses, duplicate panels, crops, enhancement, and
  compositing.

7. Manuscript and formalism

- Improve the title, abstract, introduction, related work, methods, results,
  discussion, limitations, conclusion, appendices, notation, and reproducibility
  statement.
- Make definitions precise; state assumptions, domains, units, boundary cases,
  and the relation between formal claims and executable implementation.
- Check every equation, derivation, symbol, cross-reference, theorem-like claim,
  algorithm description, and complexity statement.
- Separate established knowledge, present results, author interpretation,
  speculation, exploratory findings, confirmatory findings, and future work.
- Ensure the abstract and conclusion do not make stronger claims than the
  methods and results support.
- Discuss alternative explanations, conflicting evidence, external validity,
  missingness, measurement limits, negative results, and unavailable evidence.
- Preserve explicit non-claims and scientific boundaries.

8. Scholarship and references

Where currentness matters, conduct a fresh literature search and record
databases, queries, dates, filters, and inclusion decisions.

- Prefer primary research and authoritative standards or documentation.
- Verify title, authors, year, venue, DOI or stable identifier, version,
  corrections, expressions of concern, and retraction status.
- Confirm that each cited source supports the exact adjacent proposition.
- Detect fabricated references, citation laundering, decorative citations,
  unsupported quotations, cherry-picking, missing contrary evidence, outdated
  reviews, duplicated records, and inaccessible sources.
- Calibrate novelty and priority language. Remove or qualify "first," "best,"
  "proves," "validated," and "state of the art" unless the evidence warrants
  them.
- Cite software, datasets, instruments, methods, standards, and reused figures
  with appropriate versions and licenses.
- Build a claim-evidence/citation ledger covering the manuscript, abstract,
  documentation, tables, figures, captions, supplement, and release notes.
- Narrow or remove any claim that exceeds the study design, evidence,
  comparator, population, uncertainty, or execution actually available.

DOES NOT COUNT

The following are not completion:

- a review report, backlog, or plan without implementing safe fixes;
- passing only lint, types, coverage, or a narrow test subset;
- relying on previous receipts or previous-session results;
- replacing placeholders with manually copied numbers;
- nominal injection whose upstream producer contains hard-coded results;
- editing generated artifacts or receipts instead of their producers;
- a bibliography that resolves but does not support adjacent claims;
- adding citations without verifying their relevance and metadata;
- statistical significance without estimand, effect size, uncertainty,
  assumptions, denominators, and multiplicity review;
- a figure that exists but lacks data binding, caption verification,
  accessibility, and rendered visual inspection;
- tests that mirror implementation, overmock core behavior, or silently skip
  failures;
- omitting failed, invalid, unavailable, or non-converged cases;
- treating "not observed" as zero;
- overwriting historical evidence to make it appear source-current;
- treating green engineering checks as scientific validity, accessibility
  conformance, owner approval, release, or publication;
- hiding blocked, skipped, unavailable, resource-killed, or not-run gates.

ADVERSARIAL AUDIT

Explicitly try to trigger and detect:

- wrong-checkout, wrong-template, wrong-dataset, or wrong-config values;
- hard-coded values upstream of nominal injection;
- mixed-generation variables, figures, captions, tables, and renders;
- stale outputs accepted after source changes;
- unresolved tokens, silent defaults, unit drift, and inconsistent n;
- omitted failures or success-only denominators;
- duplicated records or seeds counted as independent evidence;
- different filters or populations used by prose, captions, tables, and figures;
- preprocessing, tuning, feature-selection, or held-out-data leakage;
- post hoc hypotheses represented as preregistered;
- non-significance represented as equivalence;
- synthetic or historical comparators represented as current empirical evidence;
- citations that exist but do not support the associated claims;
- misleading axes, missing uncertainty, clipped content, or inaccessible figures;
- generated documents manually diverging from their source;
- circular receipts or validators that attest to themselves;
- nondeterminism from ordering, randomness, concurrency, locale, timezone, or
  unpinned dependencies;
- confusion between local validation, scientific promotion, accessibility,
  owner authorization, Git state, release, and publication.

VERIFICATION

Perform at least four passes:

1. baseline and inventory;
2. implementation and remediation;
3. source-current regeneration and rendering;
4. fresh-context adversarial verification.

Run the repository's authoritative commands and record the exact environment,
revision, command, scope, exit status, artifact hashes, exclusions, and
limitations. Validate separately:

- source formatting, linting, typing, and security;
- package installation and behavior;
- unit, integration, scientific-contract, and pipeline tests;
- variable schema, token completeness, and source-to-render freshness;
- independent recomputation of representative statistics;
- figure/table registry and caption consistency;
- manuscript claims and bibliography;
- PDF structure and visual appearance;
- semantic HTML and accessibility;
- provenance, packaging, and clean isolated reproduction where feasible.

Use explicit statuses only: passed, failed, blocked, not run, not applicable, or
unavailable. Absence of an error is not proof of success.

FINAL REPORT

Lead with the verified outcome. Then provide:

1. improvements implemented by review lane;
2. exact validation commands and results;
3. variable registry and source-to-render closure;
4. statistical and scientific findings;
5. visualization, caption, and accessibility findings;
6. scholarship and claim-evidence findings;
7. changed source files and regenerated artifacts;
8. unresolved blockers, limitations, and the next authorized producer or action;
9. separate statuses for:
   - engineering validity;
   - scientific validity;
   - manuscript freshness;
   - statistical claim readiness;
   - scholarship readiness;
   - visual and accessibility status;
   - packaging and release readiness;
   - owner approval;
   - commit;
   - push;
   - publication or deposit.

Do not claim any state that was not independently completed and evidenced.

RETURN CONDITION

Do not stop after the first scan, first fixes, or first green test. Return
"COMPLETE" only when the success predicate holds and the final candidate survives
the adversarial audit.

If an external input, platform capability, credential, owner decision, or
enforced budget prevents closure, return the strongest safely verified state as
"INCOMPLETE," identify the exact blocker, preserve all valid work and historical
evidence, and name the next required action. Never paper over the gap.
~~~
