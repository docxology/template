# Scope and Related Work {#sec:scope}

## What this exemplar claims

- The five AutoScientists coordination mechanisms [@gao2026autoscientists] are re-implemented faithfully enough to be **individually ablatable**, and each is independently tested.
- Under a **matched sequential experiment budget**, coordinated teams reach the same clean optimum as a single-thread baseline (advantage $= 0.0000$).
- **Noise-band confirmation** produces a measurable, reproducible reduction in accepted evaluation noise (a $\sim 13\times$ smaller reported-vs-clean gap on this objective).
- The **dead-end registry** produces a measurable, reproducible search-hygiene gain: consulted by the proposer, it cuts redundant re-probes of retired directions from $36$ to $0$ and halts the search at $36$ of $60$ experiments, with the clean optimum unchanged.
- The **language-model proposer is a clean plug-in seam**: a live Hermes agent can replace the deterministic proposer without changing the coordination loop.

## What this exemplar does *not* claim

- **No speedup.** Because coordinated teams partition one budget rather than adding parallel compute, this testbed is not evidence that coordination is faster or reaches better solutions. It is constructed so that no such claim would be honest, and the measured advantage is zero.
- **No generalization of the magnitudes.** The $\sim 13\times$ noise-reduction figure, the $36 \to 0$ redundancy reduction, and the null effect of effect-size ranking and reorganization on every measured quantity are properties of *this* synthetic objective, budget, and deterministic proposer. They illustrate the measurement, not a universal constant.
- **No agentic-quality claim.** The live Hermes path demonstrates that the seam works, not that an LLM proposer outperforms the rule-based one.

## Relationship to AutoScientists

The original system [@gao2026autoscientists] runs real language-model agent teams on real, expensive scientific tasks and reports end-to-end performance. This exemplar deliberately strips that to a deterministic core so the *mechanisms* can be attributed and the noise behavior measured in isolation. It is a complement — a microscope on the coordination primitives — not a reproduction of the full system or its empirical results.

## Related context

The confirmation mechanism is an application of standard effect-size and standard-error reasoning [@cohen1988statistical] to online acceptance decisions. The dead-end registry, effect-size ranking, and reorganization are coordination heuristics whose lineage runs through population- and restart-based search [@whitley2001overview]; the contribution here is not the heuristics but their honest, ablatable measurement. The broader setting — teams of language-model agents pursuing a long-running objective — sits within the rapidly growing literature on LLM-based autonomous agents [@wang2023survey]. Throughout, the emphasis on regenerable figures, fixed seeds, and a tested core follows the reproducible-research tradition [@peng2011reproducible].
