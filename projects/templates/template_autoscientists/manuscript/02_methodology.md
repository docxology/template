# Methodology {#sec:methodology}

The testbed is a single coordination loop over a fixed budget of experiments. Each mechanism is an independent module so it can be tested and ablated in isolation; the loop wires them together. All logic lives in `src/`; the analysis scripts only orchestrate, plot, and write.

## The synthetic objective

The objective stands in for the expensive, stochastic evaluation a real run would optimize (a validation score, a correlation, a loss). It is a pure function of `(params, seed)`: identical inputs always yield identical outputs, which is what makes the whole exemplar reproducible.

For a parameter vector $x \in \mathbb{R}^d$ with optimum at the origin, the **clean** (noise-free) value is

$$
f(x) = -\sum_{i=1}^{d} \left[ x_i^2 + \rho\,\bigl(1 - \cos(2\pi x_i)\bigr) \right],
$$

a smooth global peak at $x = 0$ (where $f = 0$) minus shallow cosine ripples of amplitude $\rho$ that create deceptive local optima along each axis. Higher is better. A single noisy **observation** adds a seeded, zero-centred perturbation:

$$
\tilde{f}(x, s) = f(x) + \varepsilon(x, s), \qquad |\varepsilon| \le \sigma_{\text{noise}},
$$

where $\varepsilon(x, s)$ is derived deterministically from a hash of the rounded $x$ and the seed $s$. Re-evaluating the same point under a *different* seed gives a different draw (modelling run-to-run variance); the same seed always reproduces the same value. We use $d = 4$, ripple $\rho = 0.15$, and noise scale $\sigma_{\text{noise}} = 0.02$.

## Shared state

The deterministic core mirrors the AutoScientists shared state: an immutable **champion** record $p^\*$ (parameters, metric, originating experiment index) plus an append-only **experiment log** $L$ of structured outcomes. Recording an outcome appends it to $L$ and promotes the champion only when the outcome *improved* — i.e. it was confirmed and beat the incumbent. The champion metric is the value plotted against experiment count.

## The five mechanisms

The shared state above underpins all five: every mechanism reads from or writes to the champion record and the experiment log. The five *active* coordination mechanisms layered on top of it are noise-band confirmation, the dead-end registry, effect-size ranking, stagnation-driven reorganization, and team partitioning. (The abstract and README count shared state itself as the first of the headline five and fold team partitioning into reorganization; the two groupings cover the same machinery — this section names the coordination *acts*, those entry points name the standing primitive.)

**Noise-band confirmation.** Because a single observed gain may be noise, a candidate is confirmed only when its mean metric over several seeds exceeds the incumbent by more than an empirical noise band. For seeds $S$ and per-evaluation noise $\sigma_{\text{noise}}$, the band is $\sigma \cdot \sigma_{\text{noise}} / \sqrt{|S|}$ standard errors of the mean (default $\sigma = 2$), so it shrinks as more seeds are averaged. A candidate is confirmed iff its mean-over-seeds delta exceeds the band. This estimator is domain-agnostic; a synchronized generic copy lives at `infrastructure.scientific.confirmation` for reuse.

**Dead-end registry.** A registry $D$ keyed by `(axis, direction)` tracks consecutive non-improving experiments. A direction is *retired* after it fails to improve the champion `threshold` times in a row (default $3$); a confirmed improvement clears the streak. Agents consult $D$ before proposing so exhausted directions are not re-explored. An axis is *fully retired* only when both its increase and decrease directions are retired.

**Effect-size ranking.** The analyst role prioritizes directions with large observed effects. We estimate each axis's effect size as the mean absolute metric delta observed for it in $L$, then order axes by descending effect — with the deliberate twist that **untried axes sort first**, so under-explored directions are probed before the search exploits known-large-effect axes. Ties break by axis index for determinism.

**Stagnation-driven reorganization.** A detector fires when the champion has not improved within a window of recent experiments (default $10$). On firing, teams are re-partitioned around the currently most-promising live axes, dropping fully-retired ones.

**Team partitioning.** Live axes are dealt round-robin across `num_teams` teams (default $3$) so each team works a complementary slice of the ranked directions. Crucially, the teams share one budget: experiment $t$ is taken by team $t \bmod \text{num\_teams}$.

## The coordination loop

```
for each experiment in the budget:
    pick the next team and its live (non-retired) axes
    proposer proposes the next (axis, signed step) from shared state
    evaluate the candidate; if confirmation is on, average over seeds and test the band
    record the outcome; promote the champion if it improved
    update the dead-end registry
    if reorganization is on and the search is stagnant, re-partition teams
```

Every mechanism is gated by a boolean in `SearchConfig`. With all *structural* coordination toggles off and a single team — confirmation stays on, so the baseline is itself noise-honest (@sec:setup) — the loop reduces exactly to the single-thread baseline, which is what makes the ablation a clean subtraction.

## The proposer seam

The loop depends only on a `Proposer` protocol — `propose(state, axes, proposer_id, avoid=frozenset()) -> Proposal`, where `avoid` is the dead-end registry's retired `(axis, direction)` pairs so a faithful proposer steers clear of them. Two *real* implementations are provided (no mocks):

- **`DeterministicProposer`** — a rule-based policy that probes the next assigned axis in the direction that most recently improved it, defaulting toward the origin. It drives every rendered figure and test.
- **`HermesProposer`** — renders the shared state to a prompt, asks a Hermes model (served by Ollama) for the next `(axis, step, rationale)` as JSON, and parses the reply, rejecting any axis outside the assigned set. Its infrastructure-LLM import is lazy, so the deterministic core tests and renders with no Ollama dependency.

Swapping one for the other is the only change needed to turn the deterministic reference run into a live agentic one.
