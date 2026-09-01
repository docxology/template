# Introduction {#sec:introduction}

## Motivation

Long-running scientific experimentation — tuning a model, searching a design space, optimizing a noisy objective over many trials — has become a target for multi-agent language-model systems. *AutoScientists* [@gao2026autoscientists] frames this as a coordination problem: several agent teams share a running record of what has been tried, retire directions that repeatedly fail, prioritize directions with large observed effects, confirm claimed improvements against evaluation noise, and reorganize when progress stalls. These are appealing ideas, but they are easy to *describe* and hard to *attribute*: when a coordinated system performs well, which mechanism deserves the credit, and how much of an apparent gain is simply noise?

This exemplar exists to make those questions answerable on a small, fully reproducible artifact. It is one of a family of research-project templates in this repository, each pairing a tested computational core with a rendered manuscript. Here the core is a deterministic re-implementation of the AutoScientists coordination mechanisms, and the manuscript is an honest report of what they do.

## An honest framing

It is tempting to advertise multi-agent coordination as "faster" or "better" search. We deliberately do not. The decisive design choice in this testbed is that **coordinated teams partition the same sequential experiment budget as the baseline**; they do not add parallel compute. Splitting a fixed budget across teams is a *constraint*, not extra horsepower. Under such a matched budget there is no mechanism by which dividing the work can beat doing it in one undivided thread on the final metric — and our results confirm that the clean-metric advantage of coordination over the baseline is exactly zero.

What remains, and what is genuinely worth demonstrating, are two benefits that the matched budget does *not* foreclose: **robustness to evaluation noise** and **search hygiene**. The objective is stochastic: every evaluation adds a seeded perturbation, so an observed "improvement" may be a lucky draw rather than a real gain. We therefore track two quantities throughout:

- the **reported metric** — the value the search believes its champion achieves, computed from noisy observations; and
- the **clean metric** — the noise-free ground-truth value at the champion's parameters, available to us only because the objective is synthetic.

A configuration that accepts noise-inflated champions will show a large reported-minus-clean gap. Noise-band confirmation is precisely the mechanism that closes that gap, and the testbed measures by how much. Separately, we track how the budget is *spent*: the dead-end registry, consulted by the proposer, lets the search avoid re-probing directions already known to fail and halt once they are exhausted. Neither benefit is a speedup — they change how good the reported answer is and how much of the budget is wasted, not how good the clean answer is.

## Contributions

1. **A deterministic, ablatable reference** for the five AutoScientists coordination mechanisms, with every mechanism switchable via a single configuration object so its contribution can be isolated.
2. **An honest matched-budget comparison** of coordinated teams against a single-thread baseline that reports the actual numbers and makes no speedup claim.
3. **A reported-vs-clean noise-robustness measurement** that quantifies the value of noise-band confirmation as a roughly order-of-magnitude reduction in accepted noise.
4. **A search-hygiene measurement** that quantifies the dead-end registry as a reduction of redundant re-probes from $36$ to $0$ and an early halt at $36$ of $60$ experiments, with the clean optimum unchanged.
5. **A language-model plug-in seam** (`Proposer` protocol) that lets a live Hermes agent replace the deterministic proposer without modifying the coordination loop, exercised by an opt-in `requires_ollama` test.

The remainder of the paper specifies the mechanisms (@sec:methodology), reports the matched-budget comparison and the per-mechanism ablation with the numbers our scripts actually produce (@sec:results), states the scope and limits of those claims (@sec:scope), and documents reproduction (@sec:reproducibility).
