```{=latex}
\thispagestyle{empty}
\setlength{\parskip}{0pt}
\setlength{\itemsep}{0pt}
\begin{samepage}
\scriptsize
```

```{=latex}
\section*{BEGINNING OF TRANSMISSION}\label{beginning-of-transmission}
```

**State:** unpublished / pending pairing

```{=latex}
\subsubsection*{Release metadata}
```

- **Title:** Bounded AutoResearch for a Tiny Reproducible Machine-Learning Task
- **Version:** 0.2
- **DOI:** 10.5281/zenodo.20417016
- **GitHub:** docxology/template_autoresearch_project
- **Zenodo:** https://zenodo.org/records/20417016
- **SHA-256:** `5a2e9988c32cf22445e16039baba422044ee529c5c19eba38dcef9d89f2cd5f8`
- **SHA-512:** `5751b777a0b795ed7b98443e9b2e41cdbee0fe68260c40a9131ea0fae71d95325061e8a56534326739f9e35937695df683d8a80bafd5fe9fb13a8f1d2c149a89`

**Pairing:** pending — unresolved:
- ✗ GitHub release URL: `pending`

![Integrity QR strip](../figures/transmission_integrity_strip.png){width=98%}

```{=latex}
\subsubsection*{Transmission manifest}
```

```
title=Bounded AutoResearch for a Tiny Reproducible Mac
version=0.2 doi=10.5281/zenodo.20417016
sha256=5a2e9988c32cf224… manifest={"t":"Bounded AutoResearch for","v":"0.2","d":"10.5281/zenodo.20417016","s":"5a2e9988c32cf224"}
```

Structured manifest: `../data/transmission_manifest.json`

![Publication pairing flow](../figures/transmission_pairing.png){width=35%}

**Stego:** off | overlays text | barcodes on | XMP on | manifest on → `./secure_run.sh`

```{=latex}
\end{samepage}
\newpage
```


<!-- BEGINNING OF TRANSMISSION -->



```{=latex}
\newpage
```


# Abstract {#sec:abstract}

This paper presents `Deterministic bounded AutoResearch for a small MNIST neural-network task`, a public template exemplar that
turns an AutoResearch loop into ordinary reproducible research infrastructure.
The case study is intentionally small but concrete: `2000` training
and `500` test images from `MNIST handwritten digit database` are evaluated by the
bounded `small MNIST neural-network classification` loop. The run evaluates
`4` of `5` proposed candidates,
including `Tiny patch-attention classifier`, selects
`exp-mlp-tanh-64` (`MLP`,
`50890` parameters), and improves `test_accuracy` from
`82.6%` to `89.4%`
(`6.8%` absolute change). The validated diagnostic layer reports
macro F1 `89.4%`, bootstrap accuracy interval
`86.4% to 92.0%`, Brier score `0.161`,
negative log likelihood `0.361`, top-2 accuracy
`95.6%`, and exact McNemar p-value `0.000`.
The same pipeline writes proposal, candidate, run, review, benchmark, evidence,
figure, confusion-matrix, statistical-summary, probability-quality, and
security-integrity artifacts from declared output contracts; uses
`0` LLM calls at USD `0.00` cost; and records
`7` configured stages, `6` supported
local-artifact claims, and `78` required artifacts.
The local security attestation status is `passed`,
with `0` checksum mismatch(es). The final
readiness status is `passed`, with review gates deferred to a
human rather than self-approved by the generated run.



```{=latex}
\newpage
```


# Introduction {#sec:introduction}

## Bounded Research As Infrastructure {#sec:bounded-research-infrastructure}

AutoResearch systems are most useful when their planning, evidence, evaluation,
and review surfaces remain inspectable. The recent pattern popularized by
bounded coding-agent research loops is simple: define a tractable objective,
try candidate changes under a budget, keep the result that improves the metric,
and leave a replayable trace of what happened [@karpathy_autoresearch_2026].
That pattern is powerful, but it is also easy to overstate. A public research
template should show how to run the loop without hiding cost, evidence, review,
or execution boundaries.

## Exemplar Task {#sec:exemplar-task}

This project implements that safer version. The central task is
`small MNIST neural-network classification`: `MNIST handwritten digit database` from the handwritten-digit database
[@lecun_mnist_database], a `nearest-centroid` baseline, and a
finite list of candidate model families (`MLP, nearest-centroid, softmax regression, tiny patch-attention`). The
AutoResearch loop is responsible for proposing candidate configurations,
evaluating them against `test_accuracy`, selecting the best result with
deterministic tie-breaking, and writing the evidence needed to review the
claim.

## Contribution And Boundary {#sec:contribution-boundary}

The contribution is not a new `MNIST` classifier. It is a
template-level demonstration of how bounded AutoResearch can be orchestrated
through the same lifecycle used for reproducible papers: tests run first,
analysis writes structured artifacts, rendering hydrates manuscript variables,
validation checks evidence and readiness, and copy stages publish final
deliverables. The default path makes no network calls, no LLM calls, executes
no generated code, and never treats a generated review packet as human
approval. The methods in @sec:methodology define that boundary, and the results
in @sec:results report only what the validated artifacts support.

## Process Organization Motif {#sec:process-organization-motif}

The exemplar also treats research orchestration itself as a first-class
research object. In that limited operational sense, "research for research's
sake" means that programs, ledgers, evidence registries, validation gates, and
manuscript hydration do more than report a result: they maintain the conditions
under which the next research step can be inspected, replayed, criticized, and
extended. This is a process analogy, not a moral claim that software is an end
in itself or a biological claim that the template is alive.

## Related Work And Current Trends {#sec:related-work}

### Information Overload And Machine-Readable Science {#sec:information-overload-machine-readable-science}

The current AutoResearch literature is driven by a practical bottleneck:
scientific output is growing faster than document-centered review and synthesis
can absorb. Recent science-of-science evidence complicates any simple
productivity story: AI-augmented scientists can publish and be cited more often,
but the same adoption pattern can narrow the collective range of topics and
interactions in science [@hao_ai_tools_focus_2026]. This is a 2026 Nature result,
not a 2024 analysis, and it motivates governance rather than celebration.

One response is to make literature synthesis more source governed.
OpenScholar uses retrieval-augmented generation over a large scientific passage
store and reports citation accuracy improvements on literature synthesis tasks
[@asai_openscholar_2026]. PaperQA2 similarly evaluates literature-search agents
against expert scientific tasks and emphasizes cited answers, contradiction
detection, and factuality [@skarlinski_paperqa2_2024]. STORM, PaperQA, and GPT
Researcher are adjacent source-grounded writing systems that motivate this
project's insistence on citation-backed claims and visible evidence surfaces
[@shao_storm_2024; @lala_paperqa_2023; @gpt_researcher_2026]. The common lesson
is that automated writing is not enough: claims must remain tied to inspectable
sources, artifacts, and evaluation records.

### Structured Distillation And Conceptual Knowledge Substrates {#sec:structured-distillation-knowledge-substrates}

The Discovery Engine proposes a more structural answer to the same overload
problem. It distills publications into source-linked knowledge artifacts,
organizes those artifacts under a conceptual schema, encodes them into a
high-dimensional Conceptual Tensor, and unrolls that tensor into graph and
vector views for agent navigation [@baulin_discovery_engine_2025]. This project
does not construct a Conceptual Nexus Model or claim domain-scale literature
synthesis. It adopts a much smaller analogue: outputs, ledgers, evidence
registries, figure records, and hydrated manuscript variables are file-backed
objects whose provenance can be checked before publication.

The representational background is broader than one framework. FAIR principles
argue for data that are findable, accessible, interoperable, and reusable by
people and machines [@wilkinson2016fair]. RO-Crate and Workflow Run RO-Crate
package research artifacts and computational executions with linked-data
metadata [@soiland_reyes2022rocrate; @soiland_reyes2024workflow_run_rocrate].
Hyperdimensional computing and vector symbolic architectures provide one route
for robust high-dimensional symbolic-subsymbolic representations
[@heddes_hdc_2024], while tensor factorization methods such as TuckER and
mixed-geometry tensor factorization show how multi-relational knowledge graphs
can be completed and queried as structured tensors
[@balazevic_tucker_2019; @yusupov_mixed_geometry_2025]. The local contribution
here is not a new knowledge representation method; it is an executable template
that makes a small research workflow compatible with that machine-readable
direction.

### End-To-End AutoResearch Systems {#sec:end-to-end-autoresearch-systems}

The most ambitious AutoResearch systems now aim at the entire scientific
lifecycle. The AI Scientist assembles idea generation, experiment execution,
paper writing, and automated review [@lu_aiscientist_2024], and its Nature
version reports an end-to-end AI research pipeline whose generated manuscript
passed a workshop peer-review round [@lu_ai_scientist_nature_2026].
AI Scientist-v2 removes more hand-authored scaffolding and uses agentic tree
search for broader hypothesis exploration [@yamada_ai_scientist_v2_2025].
FutureHouse's platform exposes specialized scientific agents for literature
search, deep review, novelty checking, and chemistry planning
[@futurehouse_platform_2025], while Robin integrates literature and data-analysis
agents in a lab-in-the-loop discovery workflow [@ghareeb_robin_2026].

Survey work is already separating reliable assistance from risky autonomy.
The AI for Auto-Research roadmap describes the full lifecycle from creation to
dissemination, but stresses that novelty, research-level implementation, and
judgment remain fragile under automation [@kong_ai_auto_research_2026].
EXHYTE frames discovery as an iterative Exploration, Hypothesis generation, and
Testing loop, clarifying where current systems are mature and where closed-loop
autonomy remains thin [@hasib_exhyte_2025]. This exemplar therefore takes the
opposite stance from full autonomy: it implements a bounded local loop whose
candidate space, data, cost, outputs, and review gates can be audited.

### Autoformalization And Verification {#sec:autoformalization-verification}

Autoformalization supplies a different kind of boundary: instead of only asking
whether generated text is plausible, it asks whether an informal statement can
be translated into a form that a proof assistant or compiler can check.
AlphaProof shows the power of reinforcement learning over formal mathematical
proof search [@hubert_alphaproof_2025]. Process-driven autoformalization in
Lean uses compiler feedback as a precise signal for improving translations
from natural-language mathematics to formal statements and proofs
[@lu_process_driven_autoformalization_2024]. APOLLO turns Lean feedback into an
iterative proof-repair workflow in which generated proofs are decomposed,
patched, and reverified [@apollo_lean_collaboration_2025].

This project does not perform theorem proving, proof repair, or formal
mathematical verification. It borrows the architectural lesson: generated
research artifacts should be checked by deterministic tools with explicit error
surfaces. Here those tools are test suites, schema checks, evidence registries,
render validation, source hygiene greps, and review packets rather than Lean,
Isabelle, or Coq.

### ML For ML And Evolutionary Algorithm Discovery {#sec:ml-for-ml-evolutionary-discovery}

ML-for-ML systems optimize models, code, or algorithms with search loops that are
themselves subject to evaluation. Karpathy's `autoresearch` repository frames a
minimal version of this pattern as a prompt-controlled system with a fixed
budget, editable code surface, and comparable metric
[@karpathy_autoresearch_2026]. MLAgentBench and MLE-bench package machine
learning tasks as scored, replayable environments with logs and grading outputs
[@huang_mlagentbench_2023; @chan_mle_bench_2024].

At a larger scale, AlphaEvolve couples language-model proposals to evolutionary
program search and automated evaluators, producing algorithmic improvements in
mathematics and computing [@romera_paredes_alphaevolve_2025]. DeepEvolve adds
external retrieval, multi-file code editing, and debugging to the same basic
proposal-implementation-evaluation loop [@deepevolve_2025]. This manuscript's
candidate search is intentionally smaller: a finite list of configured model
families is evaluated against `test_accuracy`, with deterministic selection
and recorded deferrals rather than unbounded code mutation.

### Agentic Science, Graph Retrieval, And Epistemic Foraging {#sec:agentic-science-graph-retrieval}

Agentic science surveys describe systems that move from tool use toward
scientific agency across perception, knowledge representation, planning,
experimentation, analysis, and communication [@wei_agentic_science_2025;
@gridach_agentic_science_2025]. GraphRAG work adds structured retrieval to that
picture: graph construction and graph-aware retrieval can support multi-hop
reasoning, but benchmarks also show that knowledge-graph RAG remains brittle
when relevant knowledge is incomplete [@graphrag_bench_2026;
@brink_kg_rag_2026]. Active-inference perspectives make a similar design demand
in different language: scientific agents need persistent uncertainty-aware
memory, causal models, counterfactual exploration, deterministic validation, and
human judgment as an architectural component [@active_inference_science_2025].

This exemplar uses those ideas as constraints, not as capabilities it already
possesses. It does not run live literature mining, autonomous proof search,
external agent swarms, graph-based hypothesis hunting, or self-approval.
Instead it exposes bounded candidates, explicit budgets, local evidence links,
local `MNIST` input data, benchmark-style scoring, source-linked
figures, manuscript hydration, and human review gates. That is the intended
safe baseline for a public template.

### Benchmark, Documentation, And Process Analogies {#sec:benchmark-documentation-process-analogies}

`MNIST` and LeNet remain useful here because they provide a
compact historical benchmark for small neural networks and handwriting
recognition [@lecun_gradient_1998; @lecun_mnist_database]. Vision Transformers
introduce the patch-token pattern for image classification at scale
[@dosovitskiy_vit_2020]; this exemplar borrows only the patching and attention
representation through `Tiny patch-attention classifier`, then keeps the
implementation inside the configured candidate budget. MLPerf Tiny and OpenML
motivate explicit task descriptions, fixed inputs, machine-readable run
metadata, and checkable metrics [@banbury_mlperf_tiny_2021;
@vanschoren_openml_2014]. Machine-learning reproducibility checklists motivate
reporting data, seeds, model sizes, hyperparameters, and compute boundaries
[@pineau_reproducibility_2020].

Dataset and model documentation work further informs the safe boundary.
Datasheets for Datasets motivate explicit reporting of dataset motivation,
composition, collection, and recommended use [@gebru2021datasheets]. Model Cards
motivate structured reporting of model context, intended use, evaluation
procedure, and limitations [@mitchell2019model_cards]. The diagnostic layer
follows the same conservative reporting posture: calibration is treated as
separate from accuracy [@guo2017calibration], binomial accuracy intervals use
Wilson-style score intervals [@wilson1927probable_inference], matched classifier
comparison is summarized through paired discordance
[@dietterich1998statistical_tests], deterministic bootstrap intervals are local
resampling diagnostics [@efron1993bootstrap], and probability quality is
reported with Brier score, negative log likelihood, and chance-corrected
agreement [@brier1950verification; @cohen1960coefficient].

The process language is borrowed cautiously from teleology and theoretical
biology. Kant's account of organized beings treats a natural purpose as a whole
whose parts and whole mutually condition one another
[@ginsborg_kant_aesthetics_teleology]. Autopoiesis characterizes living systems
through self-producing organization [@varela_autopoiesis_1974], and later work
connects Kantian natural purpose to autopoietic individuality
[@weber_varela_life_after_kant_2002]. Moreno and Mossio's account of biological
autonomy emphasizes organizational closure and self-maintenance
[@moreno_mossio_biological_autonomy_2015]. This paper uses those ideas only as
disciplined analogies for configured scientific workflows whose artifacts help
reproduce, constrain, and evaluate subsequent artifacts.

Security and supply-chain references enter with the same restraint. NIST's
zero-trust architecture treats verification as explicit and continuous rather
than inherited from a trusted perimeter [@nist_sp800_207_zero_trust]. The NIST
Secure Software Development Framework emphasizes repeatable practices for
reducing software vulnerability risk [@nist_sp800_218_ssdf]. SLSA frames
software-artifact provenance and supply-chain integrity as a graded assurance
problem [@slsa_spec_latest], while MITRE ATT&CK T1195 names supply-chain
compromise as a concrete adversary technique [@mitre_attack_t1195]. This
exemplar borrows those frameworks as disciplined analogies for local research
artifact integrity: checksums, inventories, review gates, and explicit
non-claims, not production deployment certification.



```{=latex}
\newpage
```


# Methodology {#sec:methodology}

The loop is implemented through the project source surface summarized by the
validated run artifacts. The project scripts remain thin dispatchers; reusable
behavior writes `output/data/autoresearch_loop.json`, `output/data/ml_task_results.json`,
`../figures/figure_registry.json`, `output/data/autoresearch_phase_ledger.json`, and
`output/data/manuscript_variable_provenance.json`.

## Task And Data {#sec:task-data}

The task is `small MNIST neural-network classification`. The default configuration loads
`data/mnist_small.npz`, with provenance in `data/mnist_small_provenance.json`, and uses
seed `20260525`. The subset contains `2000` training images
and `500` test images, with `10` classes present
in both splits and image shape `28 by 28`. The provenance artifact
records upstream source-file hashes, the subset seed, class counts, and the
compressed subset hash. The default pipeline never downloads data at runtime.
The train and test splits contain `200` and
`50` examples per class, respectively. The registered
class-balance diagnostic is @fig:mnist_class_balance, and the
dataset contact sheet is @fig:mnist_subset_contact_sheet.

![Train and test class counts from output/data/ml_class_balance.json; the local fixture contains 2000 train and 500 test examples across 10 classes. Generation method: Grouped train/test class-count bars from the local MNIST fixture. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/mnist_class_balance.png){#fig:mnist_class_balance width="0.78\textwidth"}

| Split | Class | Count | Fraction |
| --- | --- | --- | --- |
| train | 0 | 200 | 10.0% |
| train | 1 | 200 | 10.0% |
| train | 2 | 200 | 10.0% |
| train | 3 | 200 | 10.0% |
| train | 4 | 200 | 10.0% |
| train | 5 | 200 | 10.0% |
| train | 6 | 200 | 10.0% |
| train | 7 | 200 | 10.0% |
| train | 8 | 200 | 10.0% |
| train | 9 | 200 | 10.0% |
| test | 0 | 50 | 10.0% |
| test | 1 | 50 | 10.0% |
| test | 2 | 50 | 10.0% |
| test | 3 | 50 | 10.0% |
| test | 4 | 50 | 10.0% |
| test | 5 | 50 | 10.0% |
| test | 6 | 50 | 10.0% |
| test | 7 | 50 | 10.0% |
| test | 8 | 50 | 10.0% |
| test | 9 | 50 | 10.0% |

: Local fixture class-balance table from `output/data/ml_class_balance.json`; counts describe the offline fixture used by this run. {#tbl:class-balance}

![Deterministic class-balanced contact sheet for MNIST handwritten digit database from data/mnist_small.npz and data/mnist_small_provenance.json; the figure documents the local subset used by the offline run. Generation method: Class-balanced contact sheet from fixed local MNIST arrays. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/mnist_subset_contact_sheet.png){#fig:mnist_subset_contact_sheet width="0.78\textwidth"}

The baseline is `nearest_centroid_baseline` (`nearest-centroid`). The bounded
candidate set is configured by the task artifact and covers
`MLP, nearest-centroid, softmax regression, tiny patch-attention`, including `Tiny patch-attention classifier` and at
least one deferred proposal. The transformer-style candidate borrows the
patch-token representation for comparison while staying inside the configured
iteration budget. This is intentionally a small configured model, not a claim
about full-scale image-transformer performance.

## Bounded Loop {#sec:bounded-loop}

The run follows `7` configured stages:

- Resolve the human-authored program, project topic, and research questions.
- Build an `AutoResearchPlan` from the domain profile, experiment plan, and
  pipeline DAG.
- Validate exact stage-gate names declared in `autoresearch.yaml`.
- Evaluate the configured `MNIST` candidate set up to the
  configured iteration budget.
- Generate claims only from configured questions and local artifact paths.
- Write data, reports, figures, benchmark scores, and review packets under the
  declared output contract.
- Run strict AutoResearch readiness validation and write readiness reports.

Candidates are declared in the proposal ledger and resolved from the task
configuration for execution. Each executable candidate declares a model type,
seed, training schedule, and model-specific parameters. The configured training
policy includes learning-rate decay `0.995` and gradient
clipping norm `5`, both recorded from the validated task
run rather than described as a free-form manuscript setting. The loop evaluates
at most `4` configured iterations, selects the highest
`test_accuracy`, and breaks ties by lower parameter count and identifier.
Candidates outside the budget are recorded as deferred; the run-derived status
summary is `accepted: 1, deferred: 1, rejected: 3`.

The closure is concrete and file-backed. `output/data/research_program.json`
constrains proposals; proposal records feed the bounded evaluation; evaluation
writes `output/data/ml_candidate_ledger.json` and `output/data/run_ledger.json`; ledgers support
artifact-linked claims; claims hydrate the manuscript through
`output/data/manuscript_variables.json`; readiness validation writes
`output/reports/autoresearch_readiness.json`; loop settlement is recorded in
`output/data/autoresearch_phase_ledger.json`; and review state is captured in
`output/data/review_decisions.json`. The loop therefore maintains an inspectable
research process around a small metric result without making the process
self-approving or opaque.

The concrete closure is intentionally close to research-object and workflow-run
provenance practice. The artifact manifest lists generated objects and checksums;
the figure registry binds captions to source artifacts; the variable provenance
sidecar records the source pointer for each injected token or table; and the
review packet keeps human decisions outside generated approval. This is a
minimal local analogue of machine-readable provenance rather than a claim of
full research-object packaging.

The generated schema manifest at `output/data/autoresearch_schema_manifest.json`
records `29` schema-versioned governance
payload(s) plus documented generic-table exemptions. The local research-object
manifest at `output/data/research_object_manifest.json` packages observed project paths,
hashes, the evidence registry, the source ledger, the schema manifest, and the
manual approval state. It is deliberately named a local research-object
manifest, not RO-Crate or SLSA compliance.

## Safety Controls {#sec:safety-controls}

The default autonomy level is `proposal_only`. The run ledger records
`0` LLM calls and USD `0.00` cost. The edit
allowlist is restricted to the public project source and manuscript surfaces,
plus the task configuration file, and the pipeline never executes
generated code. Review gates are emitted with deferred decisions so that
validation can confirm the gates exist without pretending that the machine
approved publication.

Publication approval is a non-generated input. The run may read
`human_review.yaml` and copy its state into review payloads, but generated
readiness cannot set publication approval by itself; the default local review
state remains `false`.

Disclosure: `AI-assisted AutoResearch` status is declared for this exemplar
because it models machine-produced plans, ledgers, reports, and manuscript
variables as review inputs rather than autonomous approval.

## Adversarial And Supply-Chain Controls {#sec:adversarial-supply-chain-controls}

The security layer is configured as `local_deterministic` with network
policy `default_offline`, integrity algorithm
`sha256`, external signing
`false`, and framework labels
`STRIDE, MITRE_ATT&CK_T1195`. Its scope is `Local research-artifact integrity evidence for this deterministic public exemplar`. These
values are generated from `output/data/autoresearch_security_profile.json`; the default
run remains offline and deterministic.

The local threat model covers `7` asset(s),
`7` threat row(s), and
`7` control row(s). The security artifacts are written
to `output/data/autoresearch_threat_model.json`,
`output/data/autoresearch_supply_chain_inventory.json`,
`output/data/autoresearch_integrity_attestation.json`, and
`output/reports/autoresearch_security_review.md`. The control-matrix figure is
@fig:autoresearch_security_control_matrix. The table and figure are generated from
the threat model and inventory, not manually maintained.

![Local security-control matrix from output/data/autoresearch_threat_model.json; controls map NIST, SLSA, and ATT&CK-inspired safeguards to deterministic evidence surfaces without claiming production security certification. Generation method: structured control matrix with separate control, evidence, framework, and status columns. Generation method: Structured control matrix from local threat-model controls. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/autoresearch_security_control_matrix.png){#fig:autoresearch_security_control_matrix width="0.84\textwidth"}

| Security artifact | Path | Summary |
| --- | --- | --- |
| profile | [security profile](../data/autoresearch_security_profile.json) | local_deterministic |
| threat model | [threat model](../data/autoresearch_threat_model.json) | default_offline |
| inventory | [supply inventory](../data/autoresearch_supply_chain_inventory.json) | 14 inputs |
| inventory export | [inventory export](../data/autoresearch_inventory_export.json) | local non-SBOM export |
| attestation | [integrity attestation](../data/autoresearch_integrity_attestation.json) | passed |
| review | [security review](../reports/autoresearch_security_review.md) | human review input |

: Local security artifacts generated for the bounded AutoResearch run. {#tbl:security-artifacts}

\begingroup\footnotesize
| Threat | STRIDE | ATT&CK | Scenario | Residual risk |
| --- | --- | --- | --- | --- |
| dataset tamper | Tampering | T1195 | A local fixture could be replaced or edited before analysis. | Residual risk remains if a reviewer ignores checksum drift. |
| config drift | Tampering | T1195.001 | Task settings could silently change candidate scope, budgets, or diag... | Configuration review is still a human responsibility. |
| source edit | Elevation of privilege | T1195.001 | Source changes could bypass the thin-script and no-generated-code bou... | The default run does not perform full static application security tes... |
| output tamper | Repudiation | T1195.002 | Generated reports or figures could be edited after analysis but befor... | Local checksum evidence is not externally signed. |
| manuscript injection | Information disclosure | T1195.002 | Manual prose could hard-code run facts that bypass validated variables. | Stable scholarly prose and citekeys remain manually authored. |
| self approval | Spoofing | T1195 | Generated review packets could be mistaken for human publication appr... | Publication remains outside the automated loop. |
| build assumption | Denial of service | T1195.003 | A local or CI build context could omit checks or run stale generated... | The exemplar does not sign build logs or isolate runners. |

: Threat-model rows from `output/data/autoresearch_threat_model.json`; ATT&CK labels scope supply-chain compromise analogies. {#tbl:security-threat-model}
\endgroup

## Positioning Against Autonomous Science Systems {#sec:positioning-autonomous-science}

The implementation should be read as a bounded local analogue of current
AutoResearch trends, not as a miniature autonomous scientist. Artifact
manifests, evidence registries, review gates, and manuscript hydration provide
machine-readable governance surfaces for one offline project run. They do not
perform autonomous literature mining, proof search, live agent orchestration,
runtime dataset expansion, self-modifying code search, or self-approval of
publication claims.

## Evidence And Scoring {#sec:evidence-scoring}

The experiment writes `output/data/ml_task_results.json`, `output/data/ml_candidate_ledger.json`,
`output/data/ml_confusion_matrix.csv`, `output/data/ml_training_history.csv`,
`output/data/ml_error_examples.json`, `output/data/ml_prediction_records.json`,
`output/data/ml_classification_diagnostics.json`, `output/data/ml_candidate_intervals.json`,
`output/data/ml_class_balance.json`, `output/data/ml_calibration_report.json`,
`output/data/ml_calibration_bin_intervals.json`, `output/data/ml_robustness_report.json`,
`output/data/ml_probability_diagnostics.json`, `output/data/ml_bootstrap_intervals.json`,
`output/data/ml_paired_comparison.json`, `output/data/ml_candidate_rank_stability.json`,
`output/data/ml_statistical_summary.json`, `output/data/ml_training_diagnostics.json`,
`output/reports/ml_benchmark_score.json`, `output/data/figure_quality_report.json`, and
registered figures through
`../figures/figure_registry.json`. The diagnostic payloads preserve probabilities,
confidence and margin summaries, class metrics, calibration bins,
confusion-pair summaries, train/test gaps, deterministic no-retrain
perturbation scores, bootstrap intervals, paired baseline comparison,
rank-stability frequencies, calibration-bin Wilson intervals, selective
accuracy thresholds, Brier score, negative log likelihood, top-2 accuracy,
probability-quality comparisons, learning-rate traces, best-epoch markers,
final learning rates, and train-test gap summaries without serializing model
weights. The benchmark score combines metric
improvement, budget compliance, offline execution, transformer-candidate
coverage, and candidate-selection status. Manuscript variables are hydrated from
these artifacts, and readiness validation checks `output/reports/evidence_registry.json`,
`output/reports/artifact_manifest.json`, method ledgers, review gates, benchmark outputs,
the phase ledger, figure-quality report, and AI-assisted disclosure before
rendering is treated as ready for review.
The generated tables and figure blocks used in @sec:results are sourced through
`output/data/manuscript_variable_provenance.json` and `output/data/manuscript_figure_blocks.json`, so captions,
artifact tables, and run-derived result statements share the same validated
artifact base.

The figure registry also carries the method contract for each visualization:
source artifact, generated file, rendering method, and claim boundary. The
rendered method table below is generated from that registry rather than
maintained manually.

\begingroup\footnotesize
| Figure | Source | Method | Scope |
| --- | --- | --- | --- |
| @fig:autoresearch_candidate_lifecycle | [candidate ledger](../data/ml_candidate_ledger.json) | Candidate lifecycle status-count bar chart. | Lifecycle counts describe bounded orchestration, not autonomous approval. |
| @fig:autoresearch_closure_flow | [loop](../data/autoresearch_loop.json) | File-backed process-flow diagram from final loop state. | The workflow is file-backed and inspectable but not self-approving. |
| @fig:autoresearch_integrity_chain | [integrity attestation](../data/autoresearch_integrity_attestation.json) | Local checksum attestation chain with checked, missing, and mismatch counts. | Integrity checks are local SHA-256 observations and are not externally signed provenance. |
| @fig:autoresearch_security_control_matrix | [threat model](../data/autoresearch_threat_model.json) | Structured control matrix from local threat-model controls. | Controls are local research-artifact safeguards, not production security certification. |
| @fig:autoresearch_stage_matrix | [loop](../data/autoresearch_loop.json) | Horizontal count summary from final loop metrics. | Readiness artifacts summarize local validation only; publication approval is human. |
| @fig:ml_bootstrap_intervals | [bootstrap intervals](../data/ml_bootstrap_intervals.json) | Horizontal percentile-bootstrap interval plot. | Bootstrap intervals summarize local test-set resampling only. |
| @fig:ml_calibration_reliability | [calibration report](../data/ml_calibration_report.json) | Reliability curve with confidence-bin support histogram. | Calibration values describe the fixed local split only. |
| @fig:ml_candidate_rank_stability | [candidate rank stability](../data/ml_candidate_rank_stability.json) | Bootstrap top-rank frequency and mean-rank comparison. | Rank stability describes local resampling behavior, not model-selection certainty. |
| @fig:ml_candidate_scores | [candidate intervals](../data/ml_candidate_intervals.json) | Lollipop accuracy comparison with Wilson interval error bars and direct labels. | Scores apply only to the fixed local subset and configured candidates. |
| @fig:ml_classification_metrics_heatmap | [class diagnostics](../data/ml_classification_diagnostics.json) | Per-class precision, recall, and F1 heatmap. | Class metrics diagnose this run only and are not full-dataset estimates. |
| @fig:ml_complexity_accuracy | [task results](../data/ml_task_results.json) | Log-parameter scatter plot against held-out accuracy. | The plot compares this bounded candidate set and does not infer a scaling law. |
| @fig:ml_confusion_matrix | [confusion matrix](../data/ml_confusion_matrix.csv) | Row-normalized heatmap with cell counts and row percentages. | Confusion counts diagnose this run only and do not imply full-dataset generalization. |
| @fig:ml_confusion_pairs | [class diagnostics](../data/ml_classification_diagnostics.json) | Ranked off-diagonal confusion-pair bars with true-class error rates. | Pair counts identify local error cases and are not a general taxonomy. |
| @fig:ml_generalization_gap | [class diagnostics](../data/ml_classification_diagnostics.json) | Grouped train/test accuracy and loss bars by evaluated candidate. | Gaps are local bounded-loop diagnostics, not convergence guarantees. |
| @fig:ml_learning_curves | [training history](../data/ml_training_history.csv) | Epoch-level held-out accuracy lines with accepted best-epoch marker. | Learning curves diagnose configured training only, not convergence in general. |
| @fig:ml_paired_correctness | [paired comparison](../data/ml_paired_comparison.json) | Matched accepted-versus-baseline correctness heatmap. | Matched comparison is limited to the fixed local test split. |
| @fig:ml_per_class_accuracy | [confusion matrix](../data/ml_confusion_matrix.csv) | Per-class accuracy bars computed from the confusion matrix diagonal. | Per-class values diagnose this local split only and do not certify robustness. |
| @fig:ml_probability_margin_distribution | [probability diagnostics](../data/ml_probability_diagnostics.json) | Confidence and margin histograms split by correctness. | Distributions are descriptive diagnostics for the fixed local test split. |
| @fig:ml_probability_quality | [statistical summary](../data/ml_statistical_summary.json) | Brier score and negative-log-likelihood bar comparison. | Probability-quality metrics compare the configured evaluated candidates only. |
| @fig:ml_robustness_matrix | [robustness report](../data/ml_robustness_report.json) | Candidate-by-transform accuracy heatmap for deterministic perturbations. | Deterministic perturbations are a smoke test and do not certify robustness. |
| @fig:ml_selective_accuracy | [statistical summary](../data/ml_statistical_summary.json) | Confidence-threshold coverage and selective-accuracy line chart. | Selective accuracy describes thresholded predictions on the fixed local split only. |
| @fig:ml_training_dynamics | [training diagnostics](../data/ml_training_diagnostics.json) | Final and best-epoch accuracy bars plus train-test gap bars. | Training dynamics diagnose this configured deterministic run only. |
| @fig:mnist_class_balance | [class balance](../data/ml_class_balance.json) | Grouped train/test class-count bars from the local MNIST fixture. | Class counts describe the local fixed fixture and are not population statistics. |
| @fig:mnist_error_examples | [error examples](../data/ml_error_examples.json) | Deterministic grid of the first accepted-candidate misclassifications. | Examples are qualitative diagnostics for this run, not an error taxonomy. |
| @fig:mnist_subset_contact_sheet | [small](../../data/mnist_small.npz) | Class-balanced contact sheet from fixed local MNIST arrays. | The sheet illustrates the local fixed subset and is not a statistical sample claim. |

: Registry-backed figure methods from [`figure_registry.json`](../figures/figure_registry.json); full validation hooks, alt text, and claim boundaries remain in the registry. {#tbl:figure-methods}
\endgroup



```{=latex}
\newpage
```


# Results {#sec:results}

## Candidate Outcome {#sec:candidate-outcome}

The generated loop selected `exp-mlp-tanh-64`
(`One-hidden-layer tanh MLP`, `MLP`) after evaluating
`4` candidate(s) from a proposed set of
`5`. The `nearest_centroid_baseline`
(`nearest-centroid`) baseline reached `82.6%`
`test_accuracy`, while the selected candidate reached `89.4%`, an
absolute change of `6.8%`. The selected model has
`50890` parameters. The transformer-candidate evaluated
flag is `true`, and the candidate budget exhausted flag is
`true`, which means the ledger records
`1` deferred proposal(s) rather than expanding the run
automatically.

The benchmark score is `1`. That score is not a model-quality
claim by itself; it is a compact grading artifact for the methods contract:
metric improvement, budget compliance, offline execution, and selected-candidate
recording. Rank-stability diagnostics report that the selected candidate is top
ranked in `72.5%` of deterministic bootstrap
resamples, with runner-up `exp-mlp-relu-32`. The candidate
score figure is registered as
@fig:ml_candidate_scores, the confusion matrix as
@fig:ml_confusion_matrix, the per-class diagnostic as
@fig:ml_per_class_accuracy, the learning curves as
@fig:ml_learning_curves, the complexity diagnostic as
@fig:ml_complexity_accuracy, the selected-candidate error examples as
@fig:mnist_error_examples, the candidate lifecycle diagnostic as
@fig:autoresearch_candidate_lifecycle, rank stability as
@fig:ml_candidate_rank_stability, the training-dynamics diagnostic as
@fig:ml_training_dynamics, the final readiness matrix as
@fig:autoresearch_stage_matrix, and the process closure as
@fig:autoresearch_closure_flow.

| Candidate | Status | Correct/test | Accuracy | Wilson 95% interval |
| --- | --- | --- | --- | --- |
| baseline | baseline | 413/500 | 82.6% | 79.0% to 85.7% |
| softmax linear | rejected | 441/500 | 88.2% | 85.1% to 90.7% |
| mlp relu 32 | rejected | 443/500 | 88.6% | 85.5% to 91.1% |
| tiny patch attention | rejected | 152/500 | 30.4% | 26.5% to 34.6% |
| mlp tanh 64 | accepted | 447/500 | 89.4% | 86.4% to 91.8% |

: Candidate accuracy intervals from `output/data/ml_candidate_intervals.json`; intervals describe the fixed local test split. {#tbl:candidate-intervals}

| Candidate | Observed rank | Top-rank frequency | Mean rank | Accuracy |
| --- | --- | --- | --- | --- |
| softmax linear | 3 | 4.2% | 2.554 | 88.2% |
| mlp relu 32 | 2 | 23.3% | 2.130 | 88.6% |
| tiny patch attention | 4 | 0.0% | 4.000 | 30.4% |
| mlp tanh 64 | 1 | 72.5% | 1.316 | 89.4% |

: Candidate rank-stability table from `output/data/ml_candidate_rank_stability.json`; frequencies are deterministic local bootstrap summaries. {#tbl:candidate-rank-stability}

## Run-Derived Figures {#sec:run-derived-figures}

![Held-out accuracy with Wilson intervals for the baseline and evaluated candidates from output/data/ml_candidate_intervals.json; accepted candidate exp-mlp-tanh-64 improves accuracy from 82.6% to 89.4% on the fixed subset, with deferred proposals kept in the candidate ledger. Generation method: Lollipop accuracy comparison with Wilson interval error bars and direct labels. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_candidate_scores.png){#fig:ml_candidate_scores width="0.8\textwidth"}

![Rank-stability summary for exp-mlp-tanh-64 from output/data/ml_candidate_rank_stability.json; deterministic local bootstrap resampling shows how often each evaluated candidate ranks first under the fixed test split. Generation method: Bootstrap top-rank frequency and mean-rank comparison. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_candidate_rank_stability.png){#fig:ml_candidate_rank_stability width="0.82\textwidth"}

![Accepted-candidate confusion matrix for exp-mlp-tanh-64 on the fixed MNIST handwritten digit database test split, sourced from output/data/ml_confusion_matrix.csv; it diagnoses the selected run, not general full-dataset performance. Generation method: Row-normalized heatmap with cell counts and row percentages. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_confusion_matrix.png){#fig:ml_confusion_matrix width="0.72\textwidth"}

![Per-class accuracy for exp-mlp-tanh-64, computed from output/data/ml_confusion_matrix.csv; variation across digits is a run diagnostic for the fixed local test split. Generation method: Per-class accuracy bars computed from the confusion matrix diagonal. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_per_class_accuracy.png){#fig:ml_per_class_accuracy width="0.78\textwidth"}

## Training And Error Diagnostics {#sec:training-error-diagnostics}

![Epoch-level held-out accuracy curves for evaluated candidates from output/data/ml_training_history.csv; the accepted curve is visually emphasized for exp-mlp-tanh-64. Generation method: Epoch-level held-out accuracy lines with accepted best-epoch marker. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_learning_curves.png){#fig:ml_learning_curves width="0.82\textwidth"}

![Configured-training dynamics for evaluated candidates from output/data/ml_training_diagnostics.json; exp-mlp-tanh-64 is highlighted while best-epoch markers and train-test gaps remain bounded to the local run. Generation method: Final and best-epoch accuracy bars plus train-test gap bars. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_training_dynamics.png){#fig:ml_training_dynamics width="0.84\textwidth"}

![Parameter-count versus held-out accuracy for the baseline and evaluated candidates from output/data/ml_task_results.json; the accepted candidate is highlighted without claiming a general scaling law. Generation method: Log-parameter scatter plot against held-out accuracy. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_complexity_accuracy.png){#fig:ml_complexity_accuracy width="0.78\textwidth"}

![First accepted-candidate error examples for exp-mlp-tanh-64, sourced from output/data/ml_error_examples.json and data/mnist_small.npz; these images support qualitative diagnosis only. Generation method: Deterministic grid of the first accepted-candidate misclassifications. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/mnist_error_examples.png){#fig:mnist_error_examples width="0.82\textwidth"}

![Candidate lifecycle ledger from output/data/ml_candidate_ledger.json: 4 evaluated out of 5 proposed candidates, with deferred proposals kept visible instead of executed automatically. Generation method: Candidate lifecycle status-count bar chart. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/autoresearch_candidate_lifecycle.png){#fig:autoresearch_candidate_lifecycle width="0.78\textwidth"}

The selected candidate's best held-out epoch is `14`, its
final learning rate is `0.144`, its train-loss
reduction is `4.161`, and its final train-test accuracy
gap is `7.0%`. These values come from the configured
training diagnostics rather than from a manually maintained result summary.

| Candidate | Status | Best epoch | Best test accuracy | Final test accuracy | Train-test gap | Loss reduction | Final learning rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| softmax linear | rejected | 17 | 89.4% | 88.2% | 5.9% | 2.917 | 0.273 |
| mlp relu 32 | rejected | 21 | 90.0% | 88.6% | 8.5% | 4.341 | 0.178 |
| tiny patch attention | rejected | 24 | 30.4% | 30.4% | -1.8% | 0.165 | 0.214 |
| mlp tanh 64 | accepted | 14 | 90.0% | 89.4% | 7.0% | 4.161 | 0.144 |

: Configured-training diagnostics from `output/data/ml_training_diagnostics.json`. {#tbl:training-diagnostics}

## Diagnostic Analysis {#sec:diagnostic-analysis}

The selected candidate macro F1 is `89.4%`, with a held-out
accuracy interval of `86.4% to 91.8%`. Probability diagnostics
report expected calibration error `2.9%` and
`11` high-confidence error(s). The top
non-diagonal confusion pair is `4 -> 9 (4)`, and the minimum
selected-candidate accuracy across deterministic robustness transforms is
`80.0%`. These values are descriptive diagnostics for the
validated local run, not external benchmark claims.

### Classification And Error Structure {#sec:classification-error-structure}

The class-level and error-pattern diagnostics are intentionally visual-first:
@fig:ml_calibration_reliability checks confidence calibration,
@fig:ml_classification_metrics_heatmap separates precision, recall, and F1 by
digit, and @fig:ml_confusion_pairs ranks the non-diagonal confusions
that most shape the selected-candidate error profile. The accompanying tables
preserve the same values for audit and downstream comparison.

![Reliability curve for exp-mlp-tanh-64 from output/data/ml_calibration_report.json; expected calibration error and bin counts summarize the accepted candidate on the fixed local test split. Generation method: Reliability curve with confidence-bin support histogram. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_calibration_reliability.png){#fig:ml_calibration_reliability width="0.82\textwidth"}

![Per-class precision, recall, and F1 for exp-mlp-tanh-64, sourced from output/data/ml_classification_diagnostics.json; metrics are scoped to the local test split. Generation method: Per-class precision, recall, and F1 heatmap. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_classification_metrics_heatmap.png){#fig:ml_classification_metrics_heatmap width="0.76\textwidth"}

![Top non-diagonal confusion pairs for exp-mlp-tanh-64, sourced from output/data/ml_classification_diagnostics.json; the bars highlight which local digit pairs account for accepted-candidate errors. Generation method: Ranked off-diagonal confusion-pair bars with true-class error rates. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_confusion_pairs.png){#fig:ml_confusion_pairs width="0.82\textwidth"}

| Class | Precision | Recall | F1 | Support |
| --- | --- | --- | --- | --- |
| 0 | 94.1% | 96.0% | 95.0% | 50 |
| 1 | 98.0% | 98.0% | 98.0% | 50 |
| 2 | 90.7% | 78.0% | 83.9% | 50 |
| 3 | 90.0% | 90.0% | 90.0% | 50 |
| 4 | 83.6% | 92.0% | 87.6% | 50 |
| 5 | 86.3% | 88.0% | 87.1% | 50 |
| 6 | 97.8% | 88.0% | 92.6% | 50 |
| 7 | 88.7% | 94.0% | 91.3% | 50 |
| 8 | 79.6% | 78.0% | 78.8% | 50 |
| 9 | 86.8% | 92.0% | 89.3% | 50 |

: Accepted-candidate class diagnostics from `output/data/ml_classification_diagnostics.json`. {#tbl:classification-diagnostics}

| Confidence bin | Count | Accuracy | Mean confidence | Gap |
| --- | --- | --- | --- | --- |
| 0-0.1 | 0 | 0.0% | 0.0% | 0.0% |
| 0.1-0.2 | 0 | 0.0% | 0.0% | 0.0% |
| 0.2-0.3 | 3 | 0.0% | 27.2% | 27.2% |
| 0.3-0.4 | 4 | 75.0% | 35.0% | 40.0% |
| 0.4-0.5 | 21 | 42.9% | 45.7% | 2.9% |
| 0.5-0.6 | 28 | 67.9% | 55.4% | 12.5% |
| 0.6-0.7 | 24 | 66.7% | 65.0% | 1.7% |
| 0.7-0.8 | 28 | 67.9% | 75.6% | 7.7% |
| 0.8-0.9 | 53 | 90.6% | 85.8% | 4.8% |
| 0.9-1 | 339 | 98.2% | 97.4% | 0.8% |

: Calibration bins from `output/data/ml_calibration_report.json`. {#tbl:calibration-bins}

| Confidence bin | Count | Correct | Accuracy | Wilson 95% | Empty |
| --- | --- | --- | --- | --- | --- |
| 0-0.1 | 0 | 0 | 0.0% | 0.0% to 0.0% | True |
| 0.1-0.2 | 0 | 0 | 0.0% | 0.0% to 0.0% | True |
| 0.2-0.3 | 3 | 0 | 0.0% | 0.0% to 56.2% | False |
| 0.3-0.4 | 4 | 3 | 75.0% | 30.1% to 95.4% | False |
| 0.4-0.5 | 21 | 9 | 42.9% | 24.5% to 63.5% | False |
| 0.5-0.6 | 28 | 19 | 67.9% | 49.3% to 82.1% | False |
| 0.6-0.7 | 24 | 16 | 66.7% | 46.7% to 82.0% | False |
| 0.7-0.8 | 28 | 19 | 67.9% | 49.3% to 82.1% | False |
| 0.8-0.9 | 53 | 48 | 90.6% | 79.7% to 95.9% | False |
| 0.9-1 | 339 | 333 | 98.2% | 96.2% to 99.2% | False |

: Calibration-bin Wilson intervals from `output/data/ml_calibration_bin_intervals.json`; empty bins are reported explicitly. {#tbl:calibration-bin-intervals}

| Pair | Count | True-class error rate |
| --- | --- | --- |
| 4 -> 9 | 4 | 8.0% |
| 8 -> 5 | 4 | 8.0% |
| 2 -> 4 | 3 | 6.0% |
| 2 -> 7 | 3 | 6.0% |
| 5 -> 8 | 3 | 6.0% |
| 6 -> 4 | 3 | 6.0% |
| 2 -> 8 | 2 | 4.0% |
| 3 -> 2 | 2 | 4.0% |
| 3 -> 8 | 2 | 4.0% |
| 5 -> 3 | 2 | 4.0% |

: Top non-diagonal confusion pairs from `output/data/ml_classification_diagnostics.json`. {#tbl:confusion-pairs}

### Uncertainty, Generalization, And Perturbation {#sec:uncertainty-generalization-perturbation}

Additional uncertainty and matched-comparison diagnostics report bootstrap
accuracy interval `86.4% to 92.0%`, bootstrap macro-F1 interval
`86.5% to 91.9%`, paired net accuracy gain
`6.8%`, exact McNemar p-value `0.000`, mean
correct-prediction confidence `90.9%`, mean error
confidence `63.1%`, and `22` low-margin
selected-candidate prediction(s). These diagnostics are generated from the
fixed local test split and are reported as run evidence, not as population-level
certification.

@fig:ml_generalization_gap compares train and test behavior,
@fig:ml_robustness_matrix shows deterministic no-retrain perturbation
results, @fig:ml_probability_margin_distribution summarizes confidence and margin
distributions, @fig:ml_bootstrap_intervals shows local resampling
intervals, and @fig:ml_paired_correctness exposes the matched
selected-versus-baseline correctness table used by the paired comparison.

![Train/test accuracy and loss for evaluated candidates from output/data/ml_classification_diagnostics.json; the plot exposes local generalization gaps without claiming full-dataset behavior. Generation method: Grouped train/test accuracy and loss bars by evaluated candidate. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_generalization_gap.png){#fig:ml_generalization_gap width="0.82\textwidth"}

![Accuracy for evaluated candidates under identity, one-pixel shifts, and low contrast from output/data/ml_robustness_report.json; the deterministic transforms provide a bounded smoke test only. Generation method: Candidate-by-transform accuracy heatmap for deterministic perturbations. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_robustness_matrix.png){#fig:ml_robustness_matrix width="0.84\textwidth"}

![Confidence and prediction-margin histograms for exp-mlp-tanh-64 from output/data/ml_probability_diagnostics.json; the figure separates correct and incorrect local test predictions. Generation method: Confidence and margin histograms split by correctness. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_probability_margin_distribution.png){#fig:ml_probability_margin_distribution width="0.82\textwidth"}

![Deterministic percentile-bootstrap intervals for exp-mlp-tanh-64 from output/data/ml_bootstrap_intervals.json; the intervals summarize local sampling variation for accuracy and macro F1. Generation method: Horizontal percentile-bootstrap interval plot. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_bootstrap_intervals.png){#fig:ml_bootstrap_intervals width="0.78\textwidth"}

![Matched correctness comparison between exp-mlp-tanh-64 and the nearest_centroid_baseline baseline from output/data/ml_paired_comparison.json; discordant cells support the paired test summary. Generation method: Matched accepted-versus-baseline correctness heatmap. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_paired_correctness.png){#fig:ml_paired_correctness width="0.66\textwidth"}

| Candidate | Transform | Accuracy | Samples |
| --- | --- | --- | --- |
| softmax linear | identity | 88.2% | 500 |
| softmax linear | shift_right_1 | 81.4% | 500 |
| softmax linear | shift_down_1 | 78.6% | 500 |
| softmax linear | low_contrast_0_85 | 88.0% | 500 |
| mlp relu 32 | identity | 88.6% | 500 |
| mlp relu 32 | shift_right_1 | 82.4% | 500 |
| mlp relu 32 | shift_down_1 | 80.2% | 500 |
| mlp relu 32 | low_contrast_0_85 | 88.2% | 500 |
| tiny patch attention | identity | 30.4% | 500 |
| tiny patch attention | shift_right_1 | 29.8% | 500 |
| tiny patch attention | shift_down_1 | 25.8% | 500 |
| tiny patch attention | low_contrast_0_85 | 24.6% | 500 |
| mlp tanh 64 | identity | 89.4% | 500 |
| mlp tanh 64 | shift_right_1 | 83.2% | 500 |
| mlp tanh 64 | shift_down_1 | 80.0% | 500 |
| mlp tanh 64 | low_contrast_0_85 | 89.8% | 500 |

: Deterministic no-retrain robustness smoke test from `output/data/ml_robustness_report.json`. {#tbl:robustness-scores}

| Statistic | Value |
| --- | --- |
| Mean confidence | 87.9% |
| Mean correct confidence | 90.9% |
| Mean error confidence | 63.1% |
| Mean margin | 80.2% |
| Mean correct margin | 84.9% |
| Mean error margin | 40.3% |
| Low-margin count | 22 |

: Accepted-candidate probability diagnostics from `output/data/ml_probability_diagnostics.json`. {#tbl:probability-diagnostics}

| Metric | Observed | CI low | CI high | Resample mean |
| --- | --- | --- | --- | --- |
| accuracy | 89.4% | 86.4% | 92.0% | 89.4% |
| macro F1 | 89.4% | 86.5% | 91.9% | 89.3% |

: Deterministic percentile-bootstrap intervals from `output/data/ml_bootstrap_intervals.json`. {#tbl:bootstrap-intervals}

| Matched comparison statistic | Value |
| --- | --- |
| Both correct | 403 |
| Accepted only correct | 44 |
| Baseline only correct | 10 |
| Both wrong | 43 |
| Discordant examples | 54 |
| Exact McNemar p | 0.000 |
| Net accuracy gain | 6.8% |

: Accepted-candidate versus baseline paired comparison from `output/data/ml_paired_comparison.json`. {#tbl:paired-comparison}

### Probability Quality And Selective Prediction {#sec:probability-quality-selective-prediction}

Probability-quality diagnostics report Brier score `0.161`,
negative log likelihood `0.361`, top-2 accuracy
`95.6%`, and Cohen kappa `0.882` for the
selected candidate. At the highest configured confidence threshold, retained
coverage is `67.8%` and selective accuracy is
`98.2%`.

The selective-prediction view in @fig:ml_selective_accuracy reports the
configured confidence-threshold trade-off: retaining fewer predictions can raise
selective accuracy, but the coverage table keeps that trade-off explicit. The
candidate probability-quality comparison in @fig:ml_probability_quality
keeps accuracy separate from proper-score behavior, so the selected candidate is
not treated as automatically best on every diagnostic axis.

![Confidence-threshold trade-off for exp-mlp-tanh-64 from output/data/ml_statistical_summary.json; the plot compares retained coverage, selective accuracy, and the unthresholded accepted-candidate accuracy on the fixed local split. Generation method: Confidence-threshold coverage and selective-accuracy line chart. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_selective_accuracy.png){#fig:ml_selective_accuracy width="0.76\textwidth"}

![Brier score and negative log likelihood for evaluated candidates from output/data/ml_statistical_summary.json; lower values indicate better probability quality within the configured local run, and the accepted candidate is highlighted. Generation method: Brier score and negative-log-likelihood bar comparison. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/ml_probability_quality.png){#fig:ml_probability_quality width="0.82\textwidth"}

| Statistic | Value |
| --- | --- |
| Accuracy | 89.4% |
| Balanced accuracy | 89.4% |
| Macro F1 | 89.4% |
| Top-2 accuracy | 95.6% |
| Cohen kappa | 0.882 |
| Brier score | 0.161 |
| Negative log likelihood | 0.361 |
| Expected calibration error | 2.9% |

: Accepted-candidate statistical summary from `output/data/ml_statistical_summary.json`. {#tbl:statistical-summary}

| Confidence threshold | Coverage | Selective accuracy | Retained | Errors |
| --- | --- | --- | --- | --- |
| 50.0% | 94.4% | 92.2% | 472 | 37 |
| 60.0% | 88.8% | 93.7% | 444 | 28 |
| 70.0% | 84.0% | 95.2% | 420 | 20 |
| 80.0% | 78.4% | 97.2% | 392 | 11 |
| 90.0% | 67.8% | 98.2% | 339 | 6 |

: Selective-accuracy threshold table from `output/data/ml_statistical_summary.json`. {#tbl:selective-accuracy}

| Candidate | Accuracy | Top-2 accuracy | Brier | NLL | Mean confidence |
| --- | --- | --- | --- | --- | --- |
| softmax linear | 88.2% | 95.8% | 0.173 | 0.390 | 85.1% |
| mlp relu 32 | 88.6% | 95.6% | 0.164 | 0.380 | 89.9% |
| tiny patch attention | 30.4% | 46.6% | 0.873 | 2.179 | 13.1% |
| mlp tanh 64 | 89.4% | 95.6% | 0.161 | 0.361 | 87.9% |

: Candidate probability-quality table from `output/data/ml_statistical_summary.json`. {#tbl:probability-quality}

## Candidate Ledger {#sec:candidate-ledger}

| Candidate | Model | Status | Test accuracy | Parameters |
| --- | --- | --- | --- | --- |
| baseline | nearest-centroid | baseline | 82.6% | 7840 |
| softmax linear | softmax regression | rejected | 88.2% | 7850 |
| mlp relu 32 | MLP | rejected | 88.6% | 25450 |
| tiny patch attention | tiny patch-attention | rejected | 30.4% | 5994 |
| mlp tanh 64 | MLP | accepted | 89.4% | 50890 |
| mlp relu 64 deferred | MLP | deferred | N/A | 0 |

: Candidate lifecycle ledger from `output/data/ml_candidate_ledger.json`. {#tbl:ml-candidate-ledger}

The candidate-selection audit separates the objective ranking from descriptive
diagnostics. It records the configured metric, Wilson interval, probability
quality, parameter count, and deterministic tie-break context for each
evaluated candidate. The diagnostic-boundary table states what each generated
surface supports and what it does not support.

| Rank | Candidate | Status | Accuracy | Wilson 95% | Brier | NLL | Parameters |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | mlp tanh 64 | accepted | 89.4% | 86.4% to 91.8% | 0.161 | 0.361 | 50890 |
| 2 | mlp relu 32 | rejected | 88.6% | 85.5% to 91.1% | 0.164 | 0.380 | 25450 |
| 3 | softmax linear | rejected | 88.2% | 85.1% to 90.7% | 0.173 | 0.390 | 7850 |
| 4 | tiny patch attention | rejected | 30.4% | 26.5% to 34.6% | 0.873 | 2.179 | 5994 |

: Candidate-selection audit from `output/data/ml_candidate_selection_audit.json`; the objective metric ranks candidates, while probability diagnostics and parameter counts audit the chosen tie-break context. {#tbl:candidate-selection-audit}

\begingroup\footnotesize
| Surface | Source | Method | Supports | Does not support |
| --- | --- | --- | --- | --- |
| objective selection | [task results](../data/ml_task_results.json) | rank evaluated candidates by configured held-out metric and deterministic tie... | accepted-candidate selection within this fixed local task | full MNIST state-of-the-art, external benchmark leadership, or universal mode... |
| descriptive diagnostics | [class diagnostics](../data/ml_classification_diagnostics.json) | per-class metrics, calibration, probability quality, and paired comparison | local error analysis and uncertainty description | population-level certification or deployment readiness |
| robustness smoke test | [robustness report](../data/ml_robustness_report.json) | deterministic no-retrain transforms applied to the fixed test split | small perturbation smoke-test evidence | adversarial robustness or distribution-shift robustness |
| artifact integrity | [integrity attestation](../data/autoresearch_integrity_attestation.json) | local SHA-256 checks over declared inputs and generated artifacts | local artifact integrity evidence for the run | external signing, production SLSA compliance, or runtime intrusion detection |
| review governance | [review decisions](../data/review_decisions.json) | deferred generated review decisions with human review required | readiness for human review | machine self-approval or publication acceptance |

: Diagnostic claim-boundary table from `output/data/ml_diagnostic_boundary.json`. {#tbl:diagnostic-boundary}
\endgroup

## Readiness And Review Artifacts {#sec:readiness-review-artifacts}

The broader AutoResearch run writes the reproducibility, benchmark, review, and
manuscript-hydration surfaces summarized below. The schema manifest records
`29` schema-versioned governance payload(s), and
the local research-object manifest records `81`
observed artifact record(s) with checksums and approval state
`false`. The phase ledger records
`3` settlement pass(es), while the
figure-quality report covers `25` registered
figure(s) with validity `false`.

![Validated AutoResearch run with 7 stages, 6 supported claims, and 78 required artifacts from output/data/autoresearch_loop.json; the count summarizes readiness artifacts, not human approval. Generation method: Horizontal count summary from final loop metrics. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/autoresearch_stage_matrix.png){#fig:autoresearch_stage_matrix width="0.8\textwidth"}

![File-backed AutoResearch closure from program through review, with 6 supported claims and readiness passed; review remains a deferred human decision and the provenance path remains inspectable. Generation method: File-backed process-flow diagram from final loop state. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/autoresearch_closure_flow.png){#fig:autoresearch_closure_flow width="0.95\textwidth"}

| Artifact | Role | Bytes |
| --- | --- | --- |
| output/data/autoresearch_claims.json | Loop artifact | 1766 |
| output/data/autoresearch_integrity_attestation.json | Security evidence | 21905 |
| output/data/autoresearch_inventory_export.json | Security evidence | 19464 |
| output/data/autoresearch_loop.json | Loop artifact | 15901 |
| output/data/autoresearch_phase_ledger.json | Run or candidate ledger | 3779 |
| output/data/autoresearch_plan.json | Loop artifact | 17222 |
| output/data/autoresearch_review_packet.json | Review packet | 16020 |
| output/data/autoresearch_schema_manifest.json | Loop artifact | 6959 |
| output/data/autoresearch_security_profile.json | Security evidence | 1537 |
| output/data/autoresearch_stage_matrix.csv | Loop artifact | 749 |
| output/data/autoresearch_supply_chain_inventory.json | Security evidence | 20683 |
| output/data/autoresearch_threat_model.json | Security evidence | 6370 |
| output/data/benchmark_scores.json | Benchmark grading | 621 |
| output/data/figure_quality_report.json | Loop artifact | 16040 |
| output/data/figure_style.json | Loop artifact | 1117 |
| output/data/idea_ledger.json | Run or candidate ledger | 5113 |
| output/data/manuscript_figure_blocks.json | Manuscript hydration | 13062 |
| output/data/manuscript_variable_provenance.json | Manuscript hydration | 30625 |
| output/data/manuscript_variables.json | Manuscript hydration | 54579 |
| output/data/ml_bootstrap_intervals.json | Loop artifact | 615 |
| output/data/ml_calibration_bin_intervals.json | Loop artifact | 2879 |
| output/data/ml_calibration_report.json | Loop artifact | 2201 |
| output/data/ml_candidate_intervals.json | Loop artifact | 1577 |
| output/data/ml_candidate_ledger.json | Run or candidate ledger | 570872 |
| output/data/ml_candidate_rank_stability.json | Loop artifact | 3135 |
| output/data/ml_candidate_selection_audit.json | Loop artifact | 2145 |
| output/data/ml_class_balance.json | Loop artifact | 2393 |
| output/data/ml_classification_diagnostics.json | Loop artifact | 4246 |
| output/data/ml_confusion_matrix.csv | Loop artifact | 271 |
| output/data/ml_diagnostic_boundary.json | Loop artifact | 2064 |
| output/data/ml_error_examples.json | Loop artifact | 989 |
| output/data/ml_paired_comparison.json | Loop artifact | 470 |
| output/data/ml_prediction_records.json | Loop artifact | 989913 |
| output/data/ml_probability_diagnostics.json | Loop artifact | 3045 |
| output/data/ml_robustness_report.json | Loop artifact | 3758 |
| output/data/ml_statistical_summary.json | Loop artifact | 3032 |
| output/data/ml_task_results.json | Loop artifact | 703566 |
| output/data/ml_training_diagnostics.json | Loop artifact | 2968 |
| output/data/ml_training_history.csv | Loop artifact | 6775 |
| output/data/mnist_task_config.json | Loop artifact | 3926 |
| output/data/research_object_manifest.json | Loop artifact | 20107 |
| output/data/research_program.json | Loop artifact | 935 |
| output/data/review_decisions.json | Review packet | 669 |
| output/data/run_ledger.json | Run or candidate ledger | 328 |
| ../figures/autoresearch_candidate_lifecycle.png | Generated figure | 28053 |
| ../figures/autoresearch_closure_flow.png | Generated figure | 40410 |
| ../figures/autoresearch_integrity_chain.png | Generated figure | 46980 |
| ../figures/autoresearch_security_control_matrix.png | Generated figure | 86574 |
| ../figures/ml_bootstrap_intervals.png | Generated figure | 21834 |
| ../figures/ml_calibration_reliability.png | Generated figure | 73889 |
| ../figures/ml_candidate_rank_stability.png | Generated figure | 43692 |
| ../figures/ml_candidate_scores.png | Generated figure | 59953 |
| ../figures/ml_classification_metrics_heatmap.png | Generated figure | 55092 |
| ../figures/ml_complexity_accuracy.png | Generated figure | 35135 |
| ../figures/ml_confusion_matrix.png | Generated figure | 65820 |
| ../figures/ml_confusion_pairs.png | Generated figure | 33982 |
| ../figures/ml_generalization_gap.png | Generated figure | 48512 |
| ../figures/ml_learning_curves.png | Generated figure | 59258 |
| ../figures/ml_paired_correctness.png | Generated figure | 43309 |
| ../figures/ml_per_class_accuracy.png | Generated figure | 34800 |
| ../figures/ml_probability_margin_distribution.png | Generated figure | 41754 |
| ../figures/ml_probability_quality.png | Generated figure | 38071 |
| ../figures/ml_robustness_matrix.png | Generated figure | 51332 |
| ../figures/ml_selective_accuracy.png | Generated figure | 48274 |
| ../figures/ml_training_dynamics.png | Generated figure | 51004 |
| ../figures/mnist_class_balance.png | Generated figure | 27059 |
| ../figures/mnist_error_examples.png | Generated figure | 28431 |
| ../figures/mnist_subset_contact_sheet.png | Generated figure | 23617 |
| output/reports/autoresearch_loop.json | Loop artifact | 15901 |
| output/reports/autoresearch_review_packet.md | Review packet | 912 |
| output/reports/autoresearch_security_review.md | Review packet | 1104 |
| output/reports/autoresearch_summary.md | Loop artifact | 255 |
| output/reports/benchmark_readiness_smoke.json | Benchmark grading | 778 |
| output/reports/ml_benchmark_score.json | Benchmark grading | 382 |
| output/reports/ml_experiment_report.md | Loop artifact | 1687 |

: Generated artifact manifest from `output/reports/artifact_manifest.json`. {#tbl:autoresearch-loop}

| Gate | Required | Decision | Rationale |
| --- | --- | --- | --- |
| proposal_review | True | deferred | Decision is read from human_review.yaml when present; generated readiness is not approval. |
| evidence_review | True | deferred | Decision is read from human_review.yaml when present; generated readiness is not approval. |

: Review-gate decisions from `output/data/review_decisions.json`. {#tbl:review-gates}

| Benchmark task | Status | Score | Grading output |
| --- | --- | --- | --- |
| readiness-smoke | graded | 1 | output/reports/benchmark_readiness_smoke.json |
| ml-loop-score | graded | 1 | output/reports/ml_benchmark_score.json |

: Benchmark grading table from `output/data/benchmark_scores.json`. {#tbl:benchmark-scores}

| Phase | Order | Group | Observed artifacts | Description |
| --- | --- | --- | --- | --- |
| intrinsic readiness | 1 | readiness | 3 | validate configured project-intrinsic contracts |
| core artifacts | 2 | loop | 0 | write plan, stage matrix, and provisional loop outputs |
| evidence registry | 3 | evidence | 2 | write local evidence registry |
| ml task | 4 | ml | 54 | run fixed-seed bounded candidate evaluation |
| method contract | 5 | governance | 3 | write program, idea, run, review, and benchmark ledgers |
| provisional payloads | 6 | settlement | 12 | refresh loop payloads before extrinsic validation |
| security artifacts | 7 | security | 10 | write local security and integrity evidence |
| final visuals | 8 | figures | 54 | write final registry-backed figures |
| manuscript hydration | 9 | manuscript | 9 | write variables, provenance, and figure blocks |
| readiness manifest | 10 | settlement | 12 | refresh checksum manifest before extrinsic validation |
| schema manifest | 11 | schema | 2 | write generated JSON schema-version manifest |
| research object manifest | 12 | packaging | 2 | write local research-object manifest |
| extrinsic readiness | 13 | readiness | 3 | validate generated artifacts and extrinsic contracts |
| final schema manifest | 14 | schema | 2 | refresh schema manifest after final payload updates |
| final research object manifest | 15 | packaging | 2 | refresh local research-object manifest |
| artifact manifest | 16 | settlement | 12 | write final artifact checksum manifest |

: Deterministic phase ledger from `output/data/autoresearch_phase_ledger.json`; settlement order is not an autonomy claim. {#tbl:phase-ledger}

| Figure | Pixels | Variance | Source exists | Nonblank |
| --- | --- | --- | --- | --- |
| fig:autoresearch_candidate_lifecycle | 1184x480 | 0.083 | True | True |
| fig:autoresearch_closure_flow | 1664x448 | 0.015 | True | True |
| fig:autoresearch_integrity_chain | 1440x734 | 0.040 | True | True |
| fig:autoresearch_security_control_matrix | 1470x734 | 0.014 | True | True |
| fig:autoresearch_stage_matrix | 1120x416 | 0.080 | True | True |
| fig:ml_bootstrap_intervals | 1152x448 | 0.009 | True | True |
| fig:ml_calibration_reliability | 1152x832 | 0.015 | True | True |
| fig:ml_candidate_rank_stability | 1408x608 | 0.053 | True | True |
| fig:ml_candidate_scores | 1376x688 | 0.013 | True | True |
| fig:ml_classification_metrics_heatmap | 928x832 | 0.092 | True | True |
| fig:ml_complexity_accuracy | 1120x608 | 0.010 | True | True |
| fig:ml_confusion_matrix | 896x768 | 0.046 | True | True |
| fig:ml_confusion_pairs | 1152x576 | 0.129 | True | True |
| fig:ml_generalization_gap | 1184x864 | 0.059 | True | True |
| fig:ml_learning_curves | 1216x608 | 0.018 | True | True |
| fig:ml_paired_correctness | 768x672 | 0.075 | True | True |
| fig:ml_per_class_accuracy | 1152x512 | 0.098 | True | True |
| fig:ml_probability_margin_distribution | 1184x864 | 0.024 | True | True |
| fig:ml_probability_quality | 1344x608 | 0.046 | True | True |
| fig:ml_robustness_matrix | 1280x608 | 0.073 | True | True |
| fig:ml_selective_accuracy | 1088x608 | 0.016 | True | True |
| fig:ml_training_dynamics | 1408x608 | 0.072 | True | True |
| fig:mnist_class_balance | 1216x544 | 0.071 | True | True |
| fig:mnist_error_examples | 1280x734 | 0.234 | True | True |
| fig:mnist_subset_contact_sheet | 1216x544 | 0.228 | True | True |

: Figure-quality checks from `output/data/figure_quality_report.json`; 25 registered figure(s) were checked. {#tbl:figure-quality}

## Security Readiness And Integrity Evidence {#sec:security-readiness-integrity}

The local security profile reports attestation status
`passed` after checking
`77` file record(s), with
`0` missing record(s) and
`0` checksum mismatch(es). The inventory
contains `14` input record(s) and
`66` generated-artifact record(s). The
integrity-chain figure is @fig:autoresearch_integrity_chain. These values support
local artifact-integrity claims only; they do not claim external signing,
production SLSA compliance, or runtime security monitoring.

![Local integrity chain from output/data/autoresearch_integrity_attestation.json; checksums summarize the observed run artifacts and remain unsigned local evidence. Generation method: Local checksum attestation chain with checked, missing, and mismatch counts. Registry metadata records the generation method, source artifact, and claim boundary for validation.](../figures/autoresearch_integrity_chain.png){#fig:autoresearch_integrity_chain width="0.84\textwidth"}

| Integrity field | Value |
| --- | --- |
| status | passed |
| algorithm | sha256 |
| checked files | 77 |
| missing files | 0 |
| checksum mismatches | 0 |
| external signature | False |

: Integrity-attestation summary from `output/data/autoresearch_integrity_attestation.json`. {#tbl:security-integrity}

## Manuscript Hydration Provenance {#sec:manuscript-hydration-provenance}

The final run supports `6` manuscript-facing claim(s)
and checks `78` required artifact(s). The rendered
manuscript uses injected variables from generated data payloads, so the abstract
and results track the latest analysis run rather than hard-coded counts. The
final readiness status is `passed`; generated review decisions are
recorded as deferred for human review rather than as self-approval.

| Source artifact | Injected variables or fragments |
| --- | --- |
| output/data/autoresearch_integrity_attestation.json | 5 |
| output/data/autoresearch_loop.json | 55 |
| output/data/autoresearch_phase_ledger.json | 2 |
| output/data/autoresearch_schema_manifest.json | 1 |
| output/data/autoresearch_security_profile.json | 6 |
| output/data/autoresearch_supply_chain_inventory.json | 3 |
| output/data/autoresearch_threat_model.json | 4 |
| output/data/benchmark_scores.json | 1 |
| output/data/figure_quality_report.json | 3 |
| output/data/manuscript_variable_provenance.json | 1 |
| output/data/ml_bootstrap_intervals.json | 3 |
| output/data/ml_calibration_bin_intervals.json | 1 |
| output/data/ml_calibration_report.json | 3 |
| output/data/ml_candidate_intervals.json | 1 |
| output/data/ml_candidate_ledger.json | 1 |
| output/data/ml_candidate_rank_stability.json | 3 |
| output/data/ml_candidate_selection_audit.json | 1 |
| output/data/ml_class_balance.json | 3 |
| output/data/ml_classification_diagnostics.json | 5 |
| output/data/ml_diagnostic_boundary.json | 1 |
| output/data/ml_paired_comparison.json | 3 |
| output/data/ml_probability_diagnostics.json | 4 |
| output/data/ml_robustness_report.json | 2 |
| output/data/ml_statistical_summary.json | 9 |
| output/data/ml_task_results.json | 39 |
| output/data/ml_training_diagnostics.json | 7 |
| output/data/research_object_manifest.json | 2 |
| output/data/review_decisions.json | 1 |
| ../figures/figure_registry.json | 51 |
| output/reports/artifact_manifest.json | 1 |

: Variable provenance summary from `output/data/manuscript_variable_provenance.json`. {#tbl:variable-provenance}



```{=latex}
\newpage
```


# Conclusion {#sec:conclusion}

`template_autoresearch_project` shows how a tractable AutoResearch task can be represented as
reproducible template infrastructure. The `small MNIST neural-network classification` experiment is small
by design, but it exercises the method surfaces that matter for a public
default: a declared research program, local input-data provenance, bounded
candidate families (`MLP, nearest-centroid, softmax regression, tiny patch-attention`), objective scoring, budget and
cost ledgers, evidence-linked claims, generated figures, benchmark grading,
manuscript-variable hydration, loop-settlement ledgers, figure-quality checks,
validation, local integrity attestation (`passed`),
and human review gates.

The broader field is converging across five related trends. Autoresearch systems
seek end-to-end automation of ideation, experiment execution, writing, and
review. Autoformalization pushes informal claims toward machine-checkable
representations. ML-for-ML systems use search, evaluation, and evolutionary code
loops to improve algorithms. Agentic science composes retrieval, planning,
experimentation, and communication into higher-autonomy workflows. Structured
knowledge synthesis supplies the substrate that all of those systems need:
source-linked artifacts, knowledge graphs, tensors, vector spaces, and
uncertainty-aware memories that can be navigated without losing provenance.

This exemplar makes a deliberately narrower contribution. It does not mine the
live literature, construct a Conceptual Nexus Model, search for Lean proofs,
mutate arbitrary code, coordinate external agents, or approve its own paper.
Instead it demonstrates governance infrastructure for automated research
workflows: every important claim is hydrated from run artifacts, every generated
figure is registry-bound and locally checked for source and pixel integrity,
every budget and candidate decision is recorded, and review state remains
outside generated self-approval. The security layer adds local inventory and
checksum evidence while keeping external signing and production deployment
claims out of scope.

The durable product is therefore not only the `MNIST` metric.
It is a reproducible research process whose data, claims, captions, figures,
review gates, and manuscript variables can be reviewed, rerun, and extended. As
more ambitious automated-science systems mature, this kind of offline,
deterministic, evidence-governed baseline remains useful because it preserves the
part of scientific automation that should not be optional: inspectable
provenance, explicit limits, and human-governed publication judgment.



```{=latex}
\newpage
```


# References

References are managed in `references.bib`.



```{=latex}
\newpage
```


```{=latex}
% transmission-end-bookend
\clearpage
\thispagestyle{empty}
\setlength{\parskip}{0pt}
\setlength{\itemsep}{0pt}
\begin{samepage}
\scriptsize
```

```{=latex}
\section*{END OF TRANSMISSION}\label{end-of-transmission}
```

**Release:** v0.2 · DOI `10.5281/zenodo.20417016` · SHA-256 `5a2e9988c32c…` · pairing pending

![Integrity QR strip](../figures/transmission_integrity_strip.png){width=88%}

**Prior:** _No prior releases._

```{=latex}
\end{samepage}
```


<!-- END OF TRANSMISSION -->
