# Human-authored research program

This human-authored research program constrains the exemplar to a bounded,
proposal-only AutoResearch loop over a small fixed-seed MNIST digit
classification task. The loop may propose a finite set of neural-network
configurations, evaluate softmax, MLP, and tiny patch-attention candidates
against a nearest-centroid baseline, keep the best result by a declared metric,
and write ledgers, review packets, benchmark status, and evidence-linked claims.
It does not execute generated code or approve its own manuscript claims.

The program adopts deterministic methods from current auto-research systems:
small prompt-controlled loops, explicit budgets, file-backed proposals,
source-backed synthesis, benchmark-style scoring, and human review gates. In
this public default, those methods are represented by deterministic local files,
a vendored small MNIST subset, and a numpy-only neural-network search, not by
live web research, external model calls, or runtime dataset downloads.
Autonomous code execution, multi-agent swarms, evolutionary paper factories,
and fully automated publication are deferred to explicit opt-in future work.
