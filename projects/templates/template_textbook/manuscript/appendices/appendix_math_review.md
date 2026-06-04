# Appendix C — Mathematical Review {#sec:appendix_math_review}

<!-- chapter-metadata-badge -->
> Reference appendix · Just-enough mathematics for the worked models.

A brief refresher on the mathematics the book relies on. Each section ties
directly to a function in [`src/textbook/models.py`](../../src/textbook/models.py)
so you can move from formula to tested code without a gap. Replace the stubs with
the depth your audience needs.

## Functions and Variables

<!-- STUB --> A function maps an input to an output; here state quantities
depend on a [**variable**](../glossary.md#gl:variable) such as time, tuned by
[**parameters**](../glossary.md#gl:parameter). See `normalize_unit_interval` for
rescaling inputs to [0, 1].

## Growth and Decay

<!-- STUB --> Logistic growth (`logistic_growth`) rises then saturates at the
carrying capacity *K*; exponential decay (`exponential_decay`) falls by a fixed
fraction per unit time, summarised by the half-life *t*½ (`half_life`). These are
the canonical examples of [**dynamics**](../glossary.md#gl:dynamics).

## Saturating Responses

<!-- STUB --> The saturating (Michaelis–Menten-style) response
(`saturating_response`) climbs toward *V*max with half-maximum at *K*ₘ — a
recurring shape whenever a resource or signal becomes limiting near a
[**threshold**](../glossary.md#gl:threshold).

## Linear Fits

<!-- STUB --> Least-squares fitting (`linear_fit`) returns a slope *m* and
intercept *b* for paired data, the simplest way to summarise a trend before
reaching for a richer [**model**](../glossary.md#gl:model).

## Basic Statistics

<!-- STUB --> Descriptive statistics (`descriptive_statistics`) report the mean
*μ* and standard deviation *σ* — the first numbers to compute on any
[**observable**](../glossary.md#gl:observable) before inference.

<!-- STUB: add worked numeric examples or exercises tied to each function. -->

See also: [Appendix B — Notation](appendix_notation.md) and the
[Authoring Guide](appendix_authoring_guide.md).
