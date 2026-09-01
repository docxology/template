# Optional Knowledge-Graph Layer

An optional, **LLM-gated** stage lifts the corpus from bibliometrics to hypothesis-level
evidence. For each eligible record, a local language model (Ollama, default model
`gemma3:4b`) extracts structured *assertions*. Each assertion encodes a direction
(supports, contradicts, or neutral), a confidence score, and a short natural-language
justification against one of the {{N_HYPOTHESES}} hypotheses declared in configuration.
Assertions are serialized as
RDF-compatible nanopublications [@kuhn2016decentralized] and scored by a
citation-weighted evidence function.

## Assertion Model

Each assertion $a$ encodes:

- **Direction**: $\text{supports}$, $\text{contradicts}$, or $\text{neutral}$ with respect to a hypothesis $H$
- **Confidence**: a score $c_a \in [0, 1]$ from the LLM
- **Citation weight**: $\log(1 + n_{\text{cites}})$, where $n_{\text{cites}}$ is the
  citation count of the asserting paper

The evidence score for hypothesis $H$ is:

$$
\text{score}(H) = \frac{\sum_{a \in A(H)^+} c_a \cdot \log(1 + n_{\text{cites}}(a)) -
\sum_{a \in A(H)^-} c_a \cdot \log(1 + n_{\text{cites}}(a))}
{\sum_{a \in A(H)} c_a \cdot \log(1 + n_{\text{cites}}(a))}
$$

where $A(H)^+$ is the set of supporting assertions and $A(H)^-$ the contradicting ones.
The score ranges from $-1$ (all evidence contradicts) to $+1$ (all evidence supports).

## Incremental Extraction

Assertion extraction is **incremental and resumable**: assertions are appended to
`nanopublications.jsonl` at configurable checkpoint intervals (default: 50 papers). On
restart, already-processed papers are skipped automatically, so a long extraction run
that is interrupted can resume without re-processing. The `--clear-assertions` flag
discards previous results for a fresh start.

## Gating and Defaults

This stage is optional and gated by language-model availability. With no language model
configured, the hypothesis evidence scores read *pending*. When Ollama is explicitly
configured and the extraction stage completes, scores are populated from the recorded,
citation-weighted assertions. The hypotheses themselves, including their names and
scope, come from configuration and are reported regardless of whether scoring has run.

The hypotheses explored in this instance are: {{HYPOTHESIS_LIST}}.
