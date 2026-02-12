## States: Newton's Sleep & Prior Dominance {#states}

> *"If the Sun & Moon should doubt / They'd immediately Go out."*
>
> — *Auguries of Innocence* [@blake1803auguries]

> *"The will of the Immortal expanded / Or contracted his all-flexible senses"*
>
> — *Book of Urizen*, Plate 3 [@blake1794urizen]

### Prior Dominance

These two quotations frame the full spectrum of precision dynamics. The Sun and Moon that never doubt represent the cosmic necessity of confident priors—without them, the world "goes out." Yet the Immortal's "all-flexible senses" describe the capacity to modulate those priors at will. "Newton's sleep" is what happens when flexibility is lost. It is *rigid inference*—the condition where prior beliefs overwhelm sensory evidence. Active Inference formalizes this:

> "Attention can be understood as inferring the level of uncertainty or precision during hierarchical perception."
>
> — Feldman & Friston (2010) [@feldman2010attention]

Parr and Friston further develop this insight, showing that attention optimizes the precision of prediction errors at every level of the cortical hierarchy, selecting which sensory channels carry reliable information [@parr2019attention].

When prior precision vastly exceeds sensory precision:

**Prior dominance:**

\begin{equation}\label{eq:prior_dominance}
\pi_{\text{prior}} \gg \pi_{\text{sensory}}
\end{equation}

When prior precision vastly exceeds sensory precision (Equation \ref{eq:prior_dominance}), observations are discounted. The world conforms to expectation---free energy (Equation \ref{eq:free_energy}) ceases to drive model revision because the precision weighting (Equation \ref{eq:precision}) favors priors. This is Blake's "Urizen"---*your reason* frozen into *horizon* (limit).

| Condition | Effect | Blake's Term |
|:----------|:-------|:-------------|
| $\pi_{\text{prior}} \gg \pi_{\text{sensory}}$ | Expectations dominate | "Newton's sleep" |
| $\pi_{\text{sensory}} \gg \pi_{\text{prior}}$ | Sensory overwhelm | Chaos, dissolution |
| $\pi_{\text{prior}} \approx \pi_{\text{sensory}}$ | Optimal inference | "Cleansed perception" |

The "guinea sun"—Blake's mockery of seeing the sun as mere golden disk—is exactly this: prior-locked inference refusing sensory update. Figure \ref{fig:newtons_sleep} illustrates the contrast between prior-dominated and balanced inference.

> **Demonstration: The Familiar Street**
>
> Walk down a street you travel daily. You may fail to notice a new shopfront, a repainted door, a changed sign. Your prior model ("this street looks like X") overwhelms sensory evidence of change. This is $\pi_{\text{prior}} \gg \pi_{\text{sensory}}$ in action.
>
> Blake's Urizen has "contracted his all-flexible senses" into "little orbs... hiding from the wind." The narrowed perception is not sensory failure but *model rigidity*.
>
> **Contrast: Tourist Vision**
>
> Now visit a new city. *Everything* glows with detail. Unfamiliar streets demand notice—each doorway, sign, and face registers distinctly. This is $\pi_{\text{prior}} \approx \pi_{\text{sensory}}$—balanced precision where the model cannot coast on expectation.
>
> The tourist sees more not because their eyes are better, but because their priors are weaker. Their doors are cleansed by unfamiliarity.

![**Newton's Sleep vs. Cleansed Perception.** Two contrasting precision regimes illustrated as balance beams. **Left panel** ("Newton's Sleep"): prior precision $\pi_{\text{prior}}$ vastly exceeds sensory precision $\pi_{\text{sensory}}$ (large red weight vs. small teal weight), producing rigid, expectation-dominated inference where "the will of the Immortal... contracted his all-flexible senses" (*Book of Urizen*, Plate 3 [@blake1794urizen]). Observations are discounted; the world conforms to frozen expectation. **Right panel** ("Cleansed Perception"): balanced precision weighting ($\pi_{\text{prior}} \approx \pi_{\text{sensory}}$, equal green and teal weights) enables optimal inference where "every thing would appear to man as it is, Infinite" (*Marriage of Heaven and Hell*, Plate 14 [@blake1790marriage]). The balance beam metaphor captures the precision dynamics formalized in Equation \ref{eq:prior_dominance}. Blake's "guinea sun" exemplifies the left state; his "Innumerable company of the Heavenly Host" exemplifies the right.](../output/figures/fig4_newtons_sleep.png){#fig:newtons_sleep}

The question becomes: is Newton's sleep a permanent condition, or a temporary one? Blake's answer is emphatic—and computationally significant. In a pivotal passage from *Milton*, he develops the distinction with systematic precision:

> *"We are not Individuals but States: Combinations of Individuals*
> *We were Angels of the Divine Presence....*
> *Calling the Human Imagination: which is the Divine Vision & Fruition*
> *In which Man liveth eternally: madness & blasphemy, against*
> *Its own Qualities, which are Servants of Humanity, not Gods or Lords.*
> *Distinguish therefore States from Individuals in those States.*
> *States Change: but Individual Identities never change nor cease:*
> *You cannot go to Eternal Death in that which can never Die.*
> *Satan & Adam are States Created into Twenty-seven Churches....*
> *States that are not, but ah! Seem to be."*
>
> — *Milton*, Plate 32 [@blake1804milton]

This passage is computationally dense. "Combinations of Individuals" reframes what a state *is*: not a personal mood but a composite model configuration—a particular factorization of beliefs, precisions, and action policies that many agents can share. "Twenty-seven Churches" names a discrete, enumerable state-space: Satan and Adam are not persons but *attractors* in model-space, recurring configurations that agents fall into and can emerge from. The crucial claim—"States that are not, but ah! Seem to be"—is the recognition that states feel ontologically real from within but are transient configurations of the generative model, not permanent features of reality.

Equally striking is Blake's simultaneous attack on reductive spatial models within the same passage:

> *"those combind by Satans Tyranny... are Shapeless Rocks*
> *Retaining only Satans Mathematic Holiness, Length: Bredth & Highth"*
>
> — *Milton*, Plate 32 [@blake1804milton]

"Mathematic Holiness"—the worship of pure quantitative extension—is Blake's name for the impoverished generative model that retains only Euclidean coordinates. When imaginative depth is stripped away, what remains is geometry without meaning: "Shapeless Rocks" that have collapsed to minimum model complexity. This directly parallels the Active Inference diagnosis of Newton's Sleep: a state where the model's rich hierarchical structure has been flattened to shallow, quantitative prediction.

The sleeping perceiver is in a *state*, not an *identity*. States change; the door can be cleansed. The miser is Blake's figure for this pathology: hoarding certainty like gold, refusing sensory update, clinging to priors that have calcified into identity.

And the transformation:

> *"If the fool would persist in his folly he would become wise."*
>
> — *Marriage of Heaven and Hell*, Proverbs of Hell [@blake1790marriage]

Persistence breaks through prior rigidity. The fool's persistence is a form of precision reweighting—eventually, accumulated evidence overwhelms the prior.

Blake records this exchange in a famous passage (see [§4.1 Boundary](#boundary)): his friend perceives only a golden disk; Blake perceives the Heavenly Host. The friend's response represents prior-locked perception; Blake's answer demonstrates cleansed vision.

### The Spectre's Steel Ratio: Prior Dominance Formalized

Blake's most precise formulation of prior-dominated inference appears in *Jerusalem*:

> *"The Spectre is the Reasoning Power in Man; & when separated / From Imagination, and closing itself as in steel, in a Ratio / Of the Things of Memory. It thence frames Laws & Moralities / To destroy Imagination!"*
>
> — *Jerusalem*, Plate 74, lines 10-13 [@blake1804jerusalem]

This is the complete phenomenology of rigid inference:

- "Closing itself as in steel" = $\pi_{\text{prior}} \to \infty$ (infinite prior precision)
- "Ratio of Things of Memory" = frozen historical priors refusing sensory update
- "Laws & Moralities" = rigid predictive structures that suppress model revision
- "Destroy Imagination" = elimination of model flexibility

The Spectre is not evil but *separated*—cut off from the generative model's creative capacity to revise itself. When reasoning power closes itself off from imagination, it becomes a self-reinforcing loop of confirmation bias.

### The Philosophy of Five Senses

Blake traces the intellectual history of perceptual restriction:

> *"Till a Philosophy of Five Senses was complete / Urizen wept & gave it into the hands of Newton & Locke"*
>
> — *The Song of Los*, Plate 4 [@blake1795songlos]

The "Philosophy of Five Senses" is the sensory bottleneck doctrine—the restriction of inference to immediate observations without hierarchical depth. Newton and Locke represent single-level empiricism: the belief that knowledge comes only from sensory evidence, without recognizing the generative models that make evidence intelligible.

Urizen "weeps" because even he—the principle of rational limitation—recognizes this as impoverishment. The complete collapse to sensory level is Newton's sleep at civilizational scale.

### Descending into Division

The Fall is described as a collapse through hierarchical levels:

> *"I was divided: descending down I sunk along / The goary tide even to the place of seed & there / Dividing I was buried"*
>
> — *Vala, or The Four Zoas*, Night the First [@blake1797fourzoas]

"Division" = separation from higher-level update. "Descending" = collapse to lower hierarchical levels. "Buried" = inference locked in prior state, unable to revise.

The "goary tide" suggests the violence of this collapse—the tearing apart of an integrated model into isolated fragments, each trapped in its own local minimum.

### The Natural Man vs. Spiritual Man

Blake's critique of Wordsworth illuminates the tension between likelihood and prior:

> *"I see in Wordsworth the natural man rising up against the spiritual man continually"*
>
> — Annotations to Wordsworth's Poems [@blake1826wordsworth]

"Natural man" = sensory likelihood $p(o|\theta)$. "Spiritual man" = prior beliefs $p(\theta)$. Wordsworth, in Blake's view, over-weights sensory precision at the expense of imaginative priors. The "rising up" is the dominance of bottom-up over top-down—the inverse of Newton's sleep, but equally unbalanced.

### Hemispheric Resonance

McGilchrist's hemispheric hypothesis [@mcgilchrist2009master; @mcgilchrist2021matter] provides a neuroanatomical substrate for the pathology Blake diagnoses. The left hemisphere's mode of attention—narrow, focused, categorical, already-knowing—maps precisely onto Newton's Sleep: the prior-dominated regime where familiar categories suppress novel inference. Urizen *is* the left hemisphere enthroned, the lawgiver who "closed the tent of the Universe" by imposing rigid categorical boundaries. Conversely, Blake's Los—the creative imagination perpetually rebuilding the model at the furnaces of Golgonooza—embodies what McGilchrist identifies as the right hemisphere's broader, contextual, novelty-seeking attention. The clinical implication is striking: if Newton's Sleep is a form of hemispheric imbalance, then "awakening" (restoring balanced precision weighting) may require not more data but a different *mode of attention*—a shift in which hemisphere leads the inference.
