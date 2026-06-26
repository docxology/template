# Results: Hypotheses Explored

The template scores a configurable set of hypotheses about the topic. For this instance
6 hypotheses are declared in configuration; Table 7 lists them with their
scope and evidence score.

**Table 7. Hypotheses explored.**

| ID | Hypothesis | Scope | Evidence score |
| --- | --- | --- | --- |
| H1 | Wakefulness Efficacy | clinical | +0.00 |
| H2 | Cognitive Enhancement | cognitive | +0.00 |
| H3 | Low Abuse Liability | safety | +0.00 |
| H4 | Dopaminergic Mechanism | pharmacological | +0.00 |
| H5 | Off-label Psychiatric Utility | applied | +0.00 |
| H6 | Tolerability | safety | +0.00 |

Evidence scores are produced by the optional, LLM-gated knowledge-graph stage. In the
offline default run that stage does not execute, so scores read *pending* — the
hypotheses, their names, and their scope are nonetheless reported directly from
configuration. A live run with a language model available populates the scores from
citation-weighted assertion extraction.

## Interpretation

Reported scores, when present, should be read as relative rankings rather than calibrated
probabilities: absolute magnitudes are inflated by publication bias and the linguistic
asymmetry of academic writing. A positive score indicates that the retrieved corpus
*talks about* the hypothesis in a supporting direction; a negative score indicates
contradicting evidence; a score near zero indicates either balanced evidence or
insufficient coverage.

The six hypotheses frame the evidence landscape for Modafinil:

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
![Hypothesis dashboard for Modafinil. The dashboard summarizes the evidence scores across the 6 configured hypotheses, showing the direction and magnitude of citation-weighted assertion evidence.](figures/hypothesis_dashboard.png "Hypothesis Dashboard"){{#fig:hypothesis_dashboard}}
