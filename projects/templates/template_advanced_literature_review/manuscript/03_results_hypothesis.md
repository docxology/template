# Results: Hypotheses Explored

The template scores a configurable set of hypotheses about the topic. For this instance
{{N_HYPOTHESES}} hypotheses are declared in configuration; Table 7 lists them with their
scope and evidence score.

**Table 7. Hypotheses explored.**

{{HYPOTHESIS_TABLE}}

Evidence scores are produced by the optional, LLM-gated knowledge-graph stage. When
the knowledge-graph stage is skipped (no language model configured), scores read
*pending*. When the stage runs (as in this instance, with {{TOTAL_ASSERTIONS}}
assertions extracted via Ollama), scores are populated from citation-weighted
assertion extraction. The hypotheses, their names, and their scope are always reported
directly from configuration regardless of whether the LLM stage executed.

## Interpretation

Reported scores, when present, should be read as relative rankings rather than calibrated
probabilities: absolute magnitudes are inflated by publication bias and the linguistic
asymmetry of academic writing. A positive score indicates that the retrieved corpus
*talks about* the hypothesis in a supporting direction; a negative score indicates
contradicting evidence; a score near zero indicates either balanced evidence or
insufficient coverage.

The six hypotheses frame the evidence landscape for {{SEARCH_TERM_TITLE}}:

- **H1 (Wakefulness Efficacy)** — the clinical claim that modafinil reliably promotes
  wakefulness in sleep-disorder populations. This is the primary indication and the
  most-studied claim in the corpus.

- **H2 (Cognitive Enhancement)** — the claim that modafinil improves attention, working
  memory, and executive function, especially under sleep deprivation. This hypothesis
  drives the neuroenhancement literature and is the subject of significant public and
  scientific debate.

- **H3 (Low Abuse Liability)** — the safety claim that modafinil has lower abuse
  potential than classical psychostimulants. This is critical for regulatory
  classification and prescribing decisions.

- **H4 (Dopaminergic Mechanism)** — the pharmacological claim that modafinil acts
  substantially via dopamine-transporter inhibition rather than a purely novel mechanism.
  This hypothesis has mechanistic and translational implications.

- **H5 (Off-label Psychiatric Utility)** — the applied claim that modafinil is a useful
  adjunct for fatigue and cognition in psychiatric and neurological conditions, including
  depression, ADHD, and schizophrenia.

- **H6 (Tolerability)** — the safety claim that modafinil is generally well tolerated,
  with predominantly mild, transient adverse effects. This underpins its clinical
  acceptability relative to alternative wakefulness agents.

<!-- FIGURE: hypothesis_dashboard.png -->
![Hypothesis dashboard for {{SEARCH_TERM_TITLE}}. The dashboard summarizes the evidence scores across the {{N_HYPOTHESES}} configured hypotheses, showing the direction and magnitude of citation-weighted assertion evidence.](../output/figures/hypothesis_dashboard.png "Hypothesis Dashboard"){{#fig:hypothesis_dashboard}}
