# Statistics Methodology Guide

`colony/stats.py` is stdlib-only — no numpy/scipy anywhere in this
project's `pyproject.toml` or source. Every function is ordinary,
exactly-checkable arithmetic, hand-verified in
[`tests/colony/test_colony_stats_unit.py`](../tests/colony/test_colony_stats_unit.py)
against expectations computed independently of the function under test.

## The five functions in `colony/stats.py`

| Function | What it computes | Why it exists |
| --- | --- | --- |
| [`wilson_score_interval`](../src/template_formal/colony/stats.py) | Closed-form Wilson score confidence interval for a binomial proportion, using `statistics.NormalDist().inv_cdf` for the exact critical value (not a hardcoded `1.96`). | Turns "N trials, R converged" into a statistically honest claim about the *true* rate, not a point estimate that could be one batch's coincidence. Stays well-behaved near `phat` close to 0 or 1 — exactly the regime a high-convergence claim lives in. |
| [`consensus_tick_summary`](../src/template_formal/colony/stats.py) | Mean/median/stdev/p25/p50/p75/p90 over a batch of converged trials' consensus ticks. Returns `Err(EmptySummaryError(...))` on zero converged trials rather than letting `statistics.mean` raise. | Descriptive statistics for the histogram figure ([`colony/visualization.py`](../src/template_formal/colony/visualization.py)) and manuscript prose. |
| [`pearson_r`](../src/template_formal/colony/stats.py) | Hand-derived Pearson correlation coefficient; returns `0.0` (documented, not a silent NaN) when either series has zero variance. | Used as one deliberately weak, exploratory check (see below) — never as a hard-bound claim. |
| [`fisher_exact_test_two_sided`](../src/template_formal/colony/stats.py) | Two-sided Fisher's exact test via `math.comb`-only hypergeometric computation — the correct small-sample test when one group sits at or near the `0%`/`100%` boundary, where a normal-approximation two-proportion test is known to misbehave. | Added specifically to correctly test a pairwise comparison that touches the `100%` boundary (see Experiment A below) — the same boundary pathology `wilson_score_interval` itself was hardened against. |
| [`cochran_armitage_trend_test`](../src/template_formal/colony/stats.py) | Two-sided Cochran–Armitage test for a linear trend in a binary proportion across `k >= 2` ordered groups (`statistics.NormalDist().cdf` for the closed-form p-value, no scipy). Returns `(0.0, 1.0)` — no detectable trend — when the pooled response is constant (all-failure or all-success), rather than dividing by zero. | Answers the *whole-sweep* ordered-trend question that a pairwise `fisher_exact_test_two_sided` comparison cannot: is there a single, whole-sequence linear association between an ordered parameter (`decay`, preference-range width) and convergence probability? Applied to both sweeps in Experiment D below. |

`wilson_score_interval` is the load-bearing one: every experiment below
reports a rate *and* its Wilson 95% interval, never a bare point estimate.

## The pre-registered-hypothesis discipline

`tests/colony/test_colony_experiments_extended.py` runs eight real, seeded
experiments (lettered A-H in the module's own section-comment headers,
literally `a` through `h`), each following the same discipline: **state
the hypothesis and its falsification criterion in a comment block before
the test that produces the result**, then report the real, unrounded
numbers. This mirrors what
[`tests/colony/test_colony_convergence_statistics.py`](../tests/colony/test_colony_convergence_statistics.py)
already does for its own N=150 claim ($H_0$: true convergence rate
$\le 0.8$, rejected iff the real Wilson 95% lower bound exceeds $0.8$).
Experiments A-C were the original three; D-H were added afterward, each
closing a specific gap a prior round's cross-vendor audit or RedTeam pass
found in the original three (see each experiment's own subsection below
for which gap it closes).

### Experiment A — decay-rate sensitivity (ISC-87)

**$H_0$** (stated before the run): convergence rate is monotonically
non-decreasing in `decay` over `{0.10, 0.30, 0.46, 0.60, 0.80, 1.00}` at
the calibrated baseline (8 agents, 2 locations, 30 ticks,
$\sigma_{\text{sense}}=0.5$, preference range $(8,12)$). Falsified by any
pair where a larger decay scores a lower rate.

**Real result** (`n=60` per value, `seed_base=0`):

| decay | successes/n | rate | Wilson 95% CI |
|---|---|---|---|
| 0.10 | 0/60 | 0.0000 | (0.0000, 0.0602) |
| 0.30 | 0/60 | 0.0000 | (0.0000, 0.0602) |
| 0.46 | 56/60 | 0.9333 | (0.8407, 0.9738) |
| 0.60 | 60/60 | 1.0000 | (0.9398, 1.0000) |
| 0.80 | 60/60 | 1.0000 | (0.9398, 1.0000) |
| 1.00 | 56/60 | 0.9333 | (0.8407, 0.9738) |

$H_0$ is rejected: a sharp threshold (near-zero below `decay≈0.35`,
plateau at `0.6-0.8`), not a smooth trend, plus a measurable count drop at
`1.00` versus `0.60`/`0.80`. **Precision correction, applied after a
second cross-vendor pass:** the whole non-monotonicity finding rests on
one pairwise gap ($60/60$ vs $56/60$) whose Wilson intervals overlap
heavily — `fisher_exact_test_two_sided` on that one pair gives two-sided
$p=0.1187$, not significant at $\alpha=0.05$. The manuscript relocates the
decline's evidentiary weight to the shape of a wider, non-regression-gated
13-point exploratory sweep and cross-seed replication, not to this one
boundary-adjacent pairwise test — see
[`manuscript/05_results_discussion.md`](../manuscript/05_results_discussion.md)
for the full, precisely-hedged account. This is the concrete lesson: a
pairwise comparison touching a `0%`/`100%` boundary needs
`fisher_exact_test_two_sided`, not a normal-approximation test, exactly as
`wilson_score_interval` itself needed hardening at that same boundary.

### Experiment B — real mechanism vs. random-choice null model (ISC-88)

**$H_0$**: the real stigmergic mechanism's convergence rate is no higher
than `colony/nullmodel.py`'s `run_null_model_trial` (each agent picks
`random.Random(seed).choice(locations)` per tick — no `Agent`, no
`BeliefState`, no field). Falsified by the real mechanism's Wilson lower
bound failing to exceed the null model's Wilson upper bound.

**Real result** ($N=150$ each, identical seed sequence `seed_base=0`):

| harness | successes/N | rate | Wilson 95% CI |
|---|---|---|---|
| real mechanism | 140/150 | 0.9333 | (0.8816, 0.9634) |
| null model | 1/150 | 0.0067 | (0.0012, 0.0368) |

Decisively rejected: the intervals do not overlap. The null model's own
rate ($1/150$) is cross-checked against a back-of-envelope expected count
($150 \times 2 \times (1/2)^8 \approx 1.2$) as a sanity check that the
baseline behaves as an uninformed random choice should, not as an
accidentally-biased one.

### Experiment C — heterogeneity-magnitude sweep (ISC-89)

**$H_0$**: convergence rate is monotonically non-increasing in the width
of `preference_mean_range` over tight $(9,11)$, medium $(8,12)$ (the
calibrated baseline), wide $(5,15)$, very-wide $(2,18)$. Falsified by any
pair where a wider range scores a higher rate.

**Real result** (`n=60` per condition, `seed_base=0`):

| condition | range | width | successes/n | rate | Wilson 95% CI |
|---|---|---|---|---|---|
| tight | $(9,11)$ | 2.0 | 60/60 | 1.0000 | (0.9398, 1.0000) |
| medium | $(8,12)$ | 4.0 | 56/60 | 0.9333 | (0.8407, 0.9738) |
| wide | $(5,15)$ | 10.0 | 15/60 | 0.2500 | (0.1578, 0.3723) |
| very-wide | $(2,18)$ | 16.0 | 2/60 | 0.0333 | (0.0092, 0.1136) |

$H_0$ survives: strictly decreasing at every step, with the sharpest drop
(`medium → wide`, ~70 points) showing degradation is sharp, not gradual.

### Experiment D — whole-sweep ordered-trend test via `cochran_armitage_trend_test` (ISC-102)

**$H_0$** (decay sweep): convergence probability is constant across the
ordered decay set (no linear trend). **$H_0$** (heterogeneity sweep):
likewise across the ordered widths. Falsified by $|Z|$ exceeding the
two-sided $\alpha=0.05$ critical value. Reuses the existing sweep
fixtures verbatim — zero new trial runs — feeding each sweep's already-collected
$(n_i, r_i, x_i)$ into the closed-form statistic.

**Real result:** decay sweep $Z=+14.5684$ ($p<10^{-10}$); heterogeneity
sweep $Z=-12.7559$ ($p<10^{-10}$). Both $H_0$s decisively rejected.

**Honesty note, stated before the test and guarded by a dedicated
test** (`test_cochran_armitage_positive_decay_trend_does_not_erase_the_local_nonmonotonic_dip`):
a significant Cochran–Armitage $Z$ answers a *different* question than the
pairwise Fisher test in Experiment A — it is evidence of a broad,
whole-sequence linear association, and is **not** evidence against the
already-documented *local* non-monotonic dip (60/60 at decay
$\{0.60,0.80\}$ vs 56/60 at decay $1.00$, Fisher $p=0.1187$). Both
statistics are reported; neither supersedes the other. This is also the
basis for the manuscript's explicit no-multiple-comparisons-correction
justification (ISC-110): each sweep's primary claim rests on one
pre-specified omnibus test, not a scan of pairwise comparisons for the
smallest $p$-value.

### Experiment E — heterogeneity sweep, independent replication at `seed_base=7000` (ISC-103)

**$H_0$** (pessimistic, stated before computing): the strict ordering
tight > medium > wide > very-wide found at `seed_base=0` is a coincidence
of that seed block and will not reproduce at a disjoint block sharing zero
seeds. Falsified by the identical sweep at `seed_base=7000` reproducing the
strict ordering.

**Real result** (`n=60` per condition): tight 60/60, medium 54/60, wide
14/60, very-wide 5/60 — different exact counts from the `seed_base=0` run
(60/60, 56/60, 15/60, 2/60), as expected for a different seed block, but
the identical strict ordering. $H_0$ rejected: this converts what was
previously only an ungated prose spot-check into a gated regression test
(`test_heterogeneity_strict_ordering_replicates_at_a_disjoint_seed_base`).

### Experiment F — decay sweep, independent replication at `seed_base=1000` (ISC-107)

**$H_0$** (pessimistic, stated before computing): the threshold-then-
plateau-then-decline shape found at `seed_base=0` (near-zero at decay
$\{0.10,0.30\}$, a plateau at $\{0.60,0.80\}$, a measurable decline at
$1.00$) is a coincidence of that seed block. Falsified by the identical
sweep at `seed_base=1000` reproducing the same qualitative shape.

**Real result** (`n=60` per value): $0/60, 0/60, 58/60, 60/60, 60/60,
53/60$ at decay $\{0.10, 0.30, 0.46, 0.60, 0.80, 1.00\}$ — different exact
counts from `seed_base=0`'s $\{0,0,56,60,60,56\}$, but the same
qualitative shape. $H_0$ rejected: the exact decline magnitude is
explicitly *not* claimed to reproduce (53/60 here vs. 56/60 at
`seed_base=0`) — only the shape is. This is the same seed base
(`1000`) the manuscript's honesty-hedges paragraph already named as an
informal spot-check; a `seed_base=5000` spot-check remains an ungated,
informal note only.

### Experiment G — zero-deposit ablation, closes Experiment B's stigmergy-attribution confound (ISC-108)

Experiment B's real-vs-null comparison (140/150 vs 1/150) cannot alone
attribute the gap to the pheromone/stigmergic channel specifically versus
general noise-robustness of the free-energy decision rule, because the
null model has no `Agent`/`BeliefState`/decision-loop machinery at all —
a structurally different code path, not a controlled ablation.

**$H_0$** (stated before computing): the real mechanism with
`deposit_amount=0.0` (full `Agent`/`BeliefState`/free-energy decision loop,
but the pheromone field never receives a deposit) converges no better than
the null model. Falsified by the zero-deposit condition's Wilson lower
bound exceeding the null model's Wilson upper bound.

**Real result** ($N=150$, `seed_base=0`, reusing Experiment B's own
`null_outcomes` fixture for an apples-to-apples comparison): zero-deposit
$0/150$ (Wilson $(0.0000, 0.0250)$) vs null $1/150$ (Wilson $(0.0012,
0.0368)$) — $H_0$ **survives** (is not falsified). A second, confirmatory
comparison against the full mechanism (140/150, Wilson $(0.8816, 0.9634)$)
shows the full mechanism's lower bound clears the zero-deposit condition's
upper bound by a wide margin. Since `deposit_amount` is the only input
changed between the full-mechanism and zero-deposit conditions, this is
real, controlled evidence that the real mechanism's advantage over chance
(Experiment B) is attributable specifically to the pheromone/stigmergic
channel, not to some deposit-independent property of the free-energy
decision rule. Confirms `ColonyTrialConfig.__post_init__` has no guard on
`deposit_amount` (unlike `decay`/`sensing_noise_std`/`preference_variance`)
— `0.0` constructs without error, checked directly rather than assumed.

Scope, honestly stated: run only at the calibrated baseline and only at
`seed_base=0` (no cross-seed-base replication), and does not characterize
the dose-response curve between `deposit_amount=0.0` and `1.0`. It also
does not close the separate, pre-existing confound at the extreme positive
control (`decay=0.97`/`sensing_noise_std=4.0` in
`test_colony_convergence_statistics.py`) — that configuration still has no
`deposit_amount=0` ablation of its own.

### Experiment H — `sensed_concentration_cap` ablation of Experiment A's mechanistic account (ISC-109)

Experiment A's prose offered a mechanistic account for why low decay fails
to converge (both candidates' sensed concentrations grow past the
preference range in lockstep, collapsing the free-energy KL term's
discriminating signal toward the sensing-noise floor) — explicitly flagged
as trace-inspection inference, not a dedicated ablation. This experiment
builds that ablation.

`ColonyTrialConfig.sensed_concentration_cap: float | None = None` (new
field, default-`None` and fully behavior-preserving for every other test in
this suite — confirmed by the full pre-existing `decay_sweep_points`
fixture reproducing identical pinned counts) clips `field.sense(location)`
to at most the cap *before* the sensing-noise term is added — a
saturating-sensor model, not reduced noise. Validated in `__post_init__`
(`> 0.0` when set, mirroring `decay`/`sensing_noise_std`/
`preference_variance`'s guard discipline). Cap value `13.0` chosen
deliberately: only $1.0$ above the preference range's ceiling ($12$, two
sensing-noise standard deviations at $\sigma=0.5$) — high enough that
ordinary within-range sensing is unaffected, low enough to bound exactly
the runaway growth the hypothesis names. An exploratory, ungated probe
(not quoted as a result) confirmed the effect holds essentially unchanged
for any cap in $[12.5, 14.0]$ and fades out by cap $=20.0$ — $13.0$ is
representative, not cherry-picked.

**$H_0$** (stated before computing): capping sensed concentration does not
improve convergence at low decay (decay $\{0.10, 0.30\}$) relative to the
uncapped baseline (0/60 at both). Falsified by the capped condition's
successes clearly exceeding 0/60 at both values.

**Real result** (`n=60` per value, `seed_base=0`): capped (cap$=13.0$)
scores $60/60$ (Wilson $(0.9398, 1.0000)$) at both decay $0.10$ and
$0.30$, versus the uncapped baseline's $0/60$ (Wilson $(0.0000, 0.0602)$)
at both — non-overlapping intervals. $H_0$ **rejected**: this is real
evidence, not merely trace-inspection inference, that the hypothesized
mechanism is at least *sufficient* to explain the low-decay failure. Scope,
honestly stated: this shows sufficiency, not necessity (some other
untested intervention might also work via a different path), and does not
itself instrument the KL term directly — it corroborates the account's
gross behavioral prediction.

### What's explicitly *not* shown

All eight experiments hold `num_agents=8`, two `locations`, `num_ticks=30`
fixed — none of the results is evidence about other colony sizes, location
counts, or tick horizons. Cross-seed-base robustness for the heterogeneity
and decay sweeps is now a **gated regression test** (Experiments E and F
above), not merely an ungated prose spot-check — but the exact `successes`
counts pinned in Experiments A-C remain `seed_base=0`-specific, and the
decay sweep's additional `seed_base=5000` spot-check remains an informal,
ungated note. The mechanistic account offered for Experiment A's threshold
is now backed by a dedicated ablation (Experiment H) showing the
hypothesized mechanism is *sufficient* to explain the failure — not that it
is *necessary*, and not a direct instrumentation of the KL term itself.
Experiment G closes the stigmergy-attribution confound in Experiment B at
the calibrated baseline only, at `seed_base=0` only, without characterizing
the `deposit_amount` dose-response curve, and without touching the
separate, still-open confound at the extreme positive-control
configuration in `test_colony_convergence_statistics.py`. No explicit
multiple-comparisons correction (Bonferroni/Holm) is applied across either
sweep's points — justified, not silently omitted (see Experiment D's
honesty note above and ISC-110 in `ISA.md`).

## Adding a new experiment, following the same discipline

1. **State $H_0$ and its falsification criterion in a comment block, before
   writing the code that produces the result.** Not after — this is the
   entire point of "pre-registered."
2. **Reuse existing infrastructure, don't fork it.** `run_colony_trial`
   (real mechanism), `run_null_model_trial` (baseline), and
   `run_parameter_sweep` (generic sweep over any real `ColonyTrialConfig`
   field except `seed`) already cover "vary one real parameter, get real
   Wilson-bounded rates per value." A new experiment should call one of
   these, not hand-roll a new trial loop.
3. **Pin the exact numbers as a regression-guard test**, following
   `test_decay_sweep_real_numbers_match_the_calibrated_run`'s pattern:
   assert the exact `successes` count at each value/condition (fully
   deterministic given the seed sequence — never `pytest.approx` on the
   headline pinned numbers, only on secondary cross-checks like
   `test_heterogeneity_sweep_medium_condition_matches_the_main_statistical_test`).
4. **Report a rate with its Wilson interval, never a bare point estimate.**
   If the finding's evidentiary weight rests on one pairwise comparison
   near a `0%`/`100%` boundary, use `fisher_exact_test_two_sided`, not a
   normal-approximation test — that is exactly the mistake Experiment A's
   own prose made on its first pass and had to correct.
5. **State what's *not* shown**, matching the "Honesty hedges" pattern in
   `manuscript/05_results_discussion.md` — which fixed parameters this
   experiment doesn't vary, and whether any exploratory (non-regression-gated)
   robustness checks were run at other seed bases.
6. **If the manuscript quotes a specific number from this experiment
   (a $p$-value, a Wilson bound), bind the test to the fixture that
   generates it, not to a hand-typed literal in a different test file.**
   ISC-104 (RedTeam finding, round 6) caught exactly this gap: a unit test
   in `test_colony_stats_unit.py` pinned the manuscript's quoted decay-dip
   Fisher $p$-value from hardcoded integer literals `(60, 60, 56, 60)`,
   completely disconnected from `decay_sweep_points` — the fixture that
   actually produces those numbers. A future re-tuning of the calibrated
   baseline could have silently drifted the sweep's real counts while the
   frozen literal (and the manuscript prose quoting it) stayed stale and
   unflagged. Fixed by
   `test_fisher_exact_on_the_decay_dip_is_computed_from_the_sweep_fixture_not_a_frozen_literal`,
   which recomputes the same $p$-value directly from `decay_sweep_points`'
   own `successes` counts — if the sweep's real numbers ever change, this
   is the test that breaks.
7. **Add the ISC.** Per the [project `AGENTS.md`](../AGENTS.md)'s Protocol
   for AI Agents: append a new `ISC-N` to `ISA.md` before writing the test,
   so the manuscript has a stable identifier to cite.
