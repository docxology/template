# Introduction

AutoResearch systems are most useful when their planning, evidence, evaluation,
and review surfaces remain inspectable. The recent pattern popularized by
bounded coding-agent research loops is simple: define a tractable objective,
try candidate changes under a budget, keep the result that improves the metric,
and leave a replayable trace of what happened [@karpathy_autoresearch_2026].
That pattern is powerful, but it is also easy to overstate. A public research
template should show how to run the loop without hiding cost, evidence, review,
or execution boundaries.

This project implements that safer version. The central task is a tiny
deterministic MNIST experiment: a local balanced subset of the handwritten-digit
database [@lecun_mnist_database], a nearest-centroid baseline, and a finite list
of neural-network candidates. The AutoResearch loop is responsible for
proposing candidate configurations, evaluating softmax, MLP, and tiny
patch-attention models against test accuracy, selecting the best result with
deterministic tie-breaking, and writing the evidence needed to review the
claim.

The contribution is not a new MNIST classifier. It is a template-level
demonstration of how bounded AutoResearch can be orchestrated through the same
lifecycle used for reproducible papers: tests run first, analysis writes
structured artifacts, rendering hydrates manuscript variables, validation checks
evidence and readiness, and copy stages publish final deliverables. The default
path makes no network calls, no LLM calls, executes no generated code, and never
treats a generated review packet as human approval.

# Related Work

Karpathy's `autoresearch` repository frames the motivating loop as a small
prompt-controlled system with a fixed budget, editable code surface, and
comparable metric [@karpathy_autoresearch_2026]. AI-agent benchmark guidance
argues that research-agent evaluations should disclose cost, reproducibility,
and robustness rather than report isolated successes [@kapoor_agents_matter].
MLAgentBench and MLE-bench similarly package machine-learning tasks as scored,
replayable environments with logs and grading outputs [@huang_mlagentbench_2023;
@chan_mle_bench_2024].

MNIST and LeNet remain useful here because they provide a compact historical
benchmark for small neural networks and handwriting recognition
[@lecun_gradient_1998; @lecun_mnist_database]. Vision Transformers introduce the
patch-token pattern for image classification at scale [@dosovitskiy_vit_2020];
this exemplar borrows only the patching and attention representation, then
shrinks it to a single fixed attention feature extractor with a trained softmax
head. MLPerf Tiny and OpenML motivate the benchmark discipline used here:
explicit task descriptions, fixed inputs, machine-readable run metadata, and
checkable metrics [@banbury_mlperf_tiny_2021; @vanschoren_openml_2014].
Machine-learning reproducibility checklists motivate reporting data, seeds,
model sizes, hyperparameters, and compute boundaries [@pineau_reproducibility_2020].

Other AutoResearch systems emphasize adjacent parts of the research lifecycle.
The AI Scientist assembles idea generation, experiments, manuscript writing, and
review, while warning that LLM-written code execution requires care
[@lu_aiscientist_2024]. STORM, PaperQA, and GPT Researcher focus on
citation-backed synthesis and source-grounded writing patterns
[@shao_storm_2024; @lala_paperqa_2023; @gpt_researcher_2026]. WorldBench maps
the broader lifecycle of AI-assisted research systems across creation, writing,
validation, and dissemination [@worldbench_auto_research_2026].

This exemplar adopts only the parts that are safe for a deterministic public
template: bounded candidates, explicit budgets, local evidence links, local
MNIST input data, benchmark-style scoring, and human review gates. It
deliberately defers live web research, runtime dataset downloads, autonomous
code execution, multi-agent swarms, evolutionary paper factories, and automated
publication.
