# Deviation register {#sec:deviations}

A registered report must state, explicitly, every way the executed analysis
departed from the frozen plan. This template treats that register as a
first-class artifact: `build_deviation_ledger` produces one row per executed
outcome and model, classifying each as `ok` (registered), `warning` (an
unregistered element carried with a documented rationale), or `error` (an
unregistered element with no rationale). `compare_analysis_to_registration`
downgrades a documented model change from `error` to `warning` and refuses to
accept any deviation whose `rationale` is empty.

## Demonstration deviations

To exercise the machinery, the demonstration executes a deliberately
plan-divergent analysis: it adds a `secondary_score` endpoint and swaps the
registered `permutation_test` for a `linear_model`, each accompanied by a
rationale. The resulting ledger is:

| Order | Kind | Target | Registered | Documented | Severity |
| --- | --- | --- | --- | --- | --- |
| 0 | outcome | `primary_score` | yes | — | `ok` |
| 1 | outcome | `secondary_score` | no | yes | `warning` |
| 2 | model | `linear_model` | no | yes | `warning` |

Because both departures are documented, the review packet remains valid: it
reports `primary_score` as the only confirmatory outcome, `secondary_score` as
exploratory, and an integrity score of `0.9` (a single `0.10` warning penalty
against a perfect plan). Had either deviation lacked a rationale, the same code
would have raised a blocking `deviation_without_rationale` or `unregistered_outcome`
error, and the packet would be invalid. [@fig:deviation_timeline] plots this
register along the registered-to-executed axis.

![Preregistration-versus-executed deviation ledger timeline, rendered by `plot_deviation_timeline` from `build_deviation_ledger` and `deviation_timeline`. Each marker is a ledger row coloured by severity: the registered `primary_score` outcome is green (`ok`), while the added `secondary_score` endpoint and the `linear_model` substitution are amber (`warning`, documented deviations). No marker is red because every departure carries a rationale. An undocumented departure would appear in red and invalidate the review packet.](figures/deviation_timeline.png){#fig:deviation_timeline}

## Reading the register

The register is the mechanism that keeps [Section @sec:results] honest: the
confirmatory claim is restricted to the registered `primary_score` outcome, and
the exploratory `secondary_score` endpoint is visible, labelled, and excluded
from confirmatory interpretation. Forks should extend this ledger — never edit
the frozen registration — whenever the executed analysis must diverge from plan.
