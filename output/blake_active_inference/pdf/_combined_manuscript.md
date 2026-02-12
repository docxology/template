---
csl: apa.csl
geometry: margin=1in
---

\newpage

# Thematic Atlas

*"What is now proved was once only imagined."* — Blake

Here, eight concordances are (sk)etched between Blake's prophetic vision and the mathematics of Active Inference.

## Table of Contents by Theme

| Section | Blake's Vision | Active Inference | Key Quotation |
|:--------|:---------------|:-----------------|:--------------|
| [Boundary](04a_boundary.md) | Doors of Perception | Markov Blanket | "If the doors of perception were cleansed..." |
| [Vision](04b_vision.md) | Fourfold Vision | Hierarchical Processing | "Now I a fourfold vision see..." |
| [States](04c_states.md) | Newton's Sleep | Prior Dominance | "Single vision & Newton's sleep!" |
| [Imagination](04d_imagination.md) | Human Existence | Generative Model | "Imagination is Human Existence itself" |
| [Time](04e_time.md) | Eternity in Hour | Temporal Horizons | "Hold... Eternity in an hour" |
| [Space](04f_space.md) | World in Grain | Spatial Inference | "To see a World in a Grain of Sand" |
| [Action](04g_action.md) | Cleansing | Free Energy Minimization | "every thing would appear... as it is: infinite" |
| [Collectives](04h_collectives.md) | Building Jerusalem | Shared & Factorized Models | "Till we have built Jerusalem..." |

\tableofcontents
\newpage



```{=latex}
\newpage
```


# Abstract: The Prophetic Synthesis

Looking at the sun, William Blake saw an innumerable company of the heavenly host where Newton's heirs saw only a golden coin. "If the doors of perception were cleansed," Blake wrote, "every thing would appear to man as it is: infinite." This paper argues that Blake's prophetic vocabulary, far from being merely poetic, constitutes an anticipatory phenomenological insight into the cognitive architecture that Active Inference now formalizes mathematically. Blake's "doors" are statistical boundaries separating self from world; his "Newton's sleep" is the pathology of rigid priors crushing sensory evidence; his "fourfold vision" maps onto hierarchical precision-weighting across processing depths; his insistence that "Imagination is the Human Existence itself" anticipates the insight that selfhood is constituted by the generative model. These are not retrospective metaphors imposed on a Romantic poet, but convergent descriptions of the same perceptual territory, arrived at through radically different methods two centuries apart. We approach this convergence in the spirit of Hesse's Glass Bead Game: not as proof that one tradition vindicates or completes the other, but as a synthetic juxtaposition of Art and Science—two moves in the same ancient, ongoing game of making sense of sense-making.

Through close reading of *The Marriage of Heaven and Hell*, *Milton*, *Jerusalem*, and other works, we trace eight structural correspondences between Blake's perceptual philosophy and the Active Inference framework: Boundary, Vision, States, Imagination, Time, Space, Action, and Collectives—the last encompassing Blake's Four Zoas as a factorized model of collective mind. Each correspondence begins with Blake's phenomenological fire—his exact words, his illuminated images—and follows the mathematical shadow that Active Inference casts across the same ground: Markov blankets, hierarchical generative models, precision dynamics, temporal depth, spatial inference, free energy minimization, and multi-agent coordination. The formalism developed by the Active Inference community provides mathematical precision, yet we resist treating it as a finished edifice; the framework is better understood as one contemporary articulation of principles that Blake, and traditions before him, grasped through other means. The synthesis contributes to both lineages: Blake scholarship gains formal grounding of insights long dismissed as mystical enthusiasm; cognitive science gains phenomenological depth, historical precedent, and the humbling recognition that its discoveries may be rediscoveries after all. The doors of perception have always been thresholds of prediction—Blake's visions and the equations point towards the same boundary, and the conversation between them remains open evermore.

Epistemic status: "delighted with the enjoyments" of AI which "look like torment and insanity". Take all syntax and semantics with a "grain of sand". For my personal limitations and typographical errors I plead "Mutual Forgiveness of each Vice".

**Keywords:** Active Inference · William Blake · Free Energy Principle · Predictive Processing · Markov Blanket · Generative Model · Philosophy of Mind · Romanticism · Glass Bead Game



```{=latex}
\newpage
```


# Introduction: The Threshold {#introduction}

> *"If the doors of perception were cleansed every thing would appear to man as it is: infinite. For man has closed himself up, till he sees all things thro' narrow chinks of his cavern."*
>
> — Blake, *Marriage of Heaven and Hell*, Plate 14 [@blake1790marriage]

## The Threshold {#threshold}

Between perceiver and perceived lies a boundary. Blake called it a door. In causal inference, that boundary may be called a blanket. The exoteric syntax differs; the esoteric semantics does not.

William Blake (1757–1827) composed his prophetic works during the consolidation of Newtonian mechanism—the reduction of cosmos to clockwork, of vision to optics, of mind to matter arranged [@raine1968blake]. His response was not retreat into mysticism but a vigorous *expansion*: a fourfold epistemology that could contain Newton's single vision while transcending it.

The Active Inference framework, developed by a growing community of researchers worldwide, offers a formal complement to Blake's insights. The free energy principle formalizes how self-organizing systems maintain existence by minimizing prediction error [@friston2010free]. Perception and action unite in a single imperative—to reduce the gap between expectation and evidence.

This paper explores how Blake's intuitions and Active Inference's equations resonate. The former prophesied; the latter formalizes. We do not claim that Blake was a proto-Bayesian statistician, nor that Active Inference is a "Blakean" science, but rather that both systems grapple with the same fundamental problem: how a bounded agent maintains its existence and makes sense of an infinite world. We offer a *synthetic juxtapositional intelligence*—placing the poet's vision alongside the physicist's variables to reveal the structural identity of their insights.

The spirit of this enterprise owes something to Hesse's *Glass Bead Game*: an abstract synthesis of all arts and sciences, where the player discovers hidden affinities between seemingly unrelated disciplines [@hesse1943glass]. Like Hesse's Castalian scholars, we do not seek to reduce one tradition to the other, but to illuminate the structural resonances that emerge when both are held in the same contemplative field.

This synthesis arrives at a moment of convergence. On one side, predictive processing and active inference are being applied with increasing sophistication to aesthetics and literary engagement—most notably in the 2024 *Philosophical Transactions of the Royal Society B* theme issue on art and predictive processing [@vandecruys2024order], and in Kukkonen's work modeling literary experience through prediction error [@kukkonen2020probability]. On the other, cognitive approaches to Romanticism are deepening: Savarese's *Romanticism's Other Minds* [@savarese2020romanticism] reveals a "prehistory of cognitive approaches to literature" within the Romantic tradition itself. Our paper sits at the intersection of these two currents, offering what neither can alone: the formal mathematics that makes the poetic claim testable, and the phenomenological richness that makes the formalism legible.

## The Correspondences {#correspondences}

Eight thematic correspondences anchor our synthesis (see [Thematic Atlas](#tbl-themes)):

| Theme | Blake's Term | Active Inference Term |
|:------|:-------------|:----------------------|
| **Boundary** | Doors of Perception | Markov Blanket |
| **Vision** | Fourfold Vision | Hierarchical Processing |
| **States** | Newton's Sleep | Prior Dominance |
| **Imagination** | Human Existence | Generative Model |
| **Time** | Eternity in an Hour | Temporal Horizons |
| **Space** | World in a Grain of Sand | Spatial Inference |
| **Action** | Cleansing | Free Energy Minimization |
| **Collectives** | Building Jerusalem | Shared Generative Models |

: Thematic Atlas: Structural correspondences between Blake's visionary phenomenology and Active Inference. {#tbl-themes}

> *"May God us keep / From Single vision & Newton's sleep!"*
>
> — Blake, Letter to Butts, November 1802 [@blake1802butts]

## Method {#method}

We proceed now through three main movements:

- **§2**: Related scholarship: Blake and cognition, Romanticism and neuroscience, situating our contribution
- **§3**: Theoretical Foundations: free energy, Markov blankets, precision
- **§4**: Synthesis: eight themed correspondences with equations and figures

Each theme in our synthesis ([Thematic Atlas](#tbl-themes)) begins with Blake's fire, then traces its mathematical shadow. The conclusion ([§5–6](#implications)) draws implications for philosophy of mind, cognitive science, and creativity, while engaging counter-arguments and acknowledging limitations.



```{=latex}
\newpage
```


# Related Work: Scholarship & Context {#related-work}

*Situating the correspondence within existing scholarship.*

## Blake and Embodied Cognition

The mapping between Romantic poetry and cognitive science has precursors. Three pillars of Blake scholarship make our formal mapping possible. Northrop Frye's *Fearful Symmetry* [@frye1947fearful] established the systematic reading of Blake's symbolism as a coherent intellectual structure rather than private mythology. S. Foster Damon's *A Blake Dictionary* [@damon1988blake] provides the essential lexicon of Blake's symbolic system, establishing the correspondences among his mythological figures that a formal mapping requires. Peter Ackroyd's definitive biography [@ackroyd1995blake] demonstrates how Blake's visionary epistemology was inseparable from his lived practice as engraver, printer, and painter—an embodied creativity that resists reduction to disembodied ideas.

From the cognitive science side, two works converge on the same insight. Mark Johnson's *The Body in the Mind* [@johnson1987body] argues that abstract thought is grounded in embodied image schemas—exactly the kind of perceptual-motor structures that Active Inference formalizes as generative models. Lakoff and Johnson's *Metaphors We Live By* [@lakoff1980metaphors] demonstrated that conceptual structure is metaphorical and embodied, not abstract and propositional.

Blake anticipated both traditions by two centuries. His insistence that "Man has no Body distinct from his Soul" (MHH Plate 4) is not metaphor but proto-enactivism: the body is not a container for mind but the very medium of inference.

## Hemispheric Lateralization

Iain McGilchrist's *The Master and His Emissary* [@mcgilchrist2009master] proposes that the left hemisphere prioritizes narrow, focused, already-known categories while the right hemisphere attends to the broad, contextual, and novel. This lateralization maps suggestively onto Blake's mythology: Urizen (left hemisphere)---the lawgiver who "closed the tent of the Universe," imposing rigid categories---versus Los/Urthona (right hemisphere)---the creative imagination that builds Golgonooza, perpetually open to new form. McGilchrist's thesis that Western civilization has progressively over-valued left-hemispheric cognition parallels Blake's diagnosis of "Newton's sleep" as civilizational pathology.

McGilchrist's magisterial follow-up, *The Matter with Things* [@mcgilchrist2021matter], deepens this analysis with direct engagement with Blake. McGilchrist treats imagination not as mere fantasy but as a "key faculty" for revealing reality---echoing Blake's own elevation of imagination above reason. The dynamic tension of Blake's *Marriage of Heaven and Hell*, where "contraries" generate movement toward deeper consciousness, exemplifies what McGilchrist identifies as the right hemisphere's mode of understanding: holding opposites in creative tension rather than collapsing them into categories.

## Romanticism and the Science of Mind

Alan Richardson's *British Romanticism and the Science of the Mind* [@richardson2001british] documents how Romantic poets engaged seriously with contemporary brain science, not as opponents but as creative interlocutors. Richardson shows that the Romantic critique of mechanism was not anti-scientific but proto-cognitive---anticipating embodied, situated, and enactive approaches. Our paper extends Richardson's historical argument by providing the formal bridge: Active Inference supplies the mathematics that connects Blake's phenomenological observations to contemporary computational neuroscience.

## Neuroaesthetics

The emerging field of neuroaesthetics investigates how art engages perceptual and cognitive systems. Ramachandran and Hirstein [@ramachandran1999science] proposed that art exploits principles of perceptual processing---peak shift, isolation, and grouping. In Active Inference terms, art offers generative models that resolve free energy in novel ways, restructuring the viewer's predictions. Blake's illuminated books---integrating visual, verbal, and material elements into composite artworks---represent an extreme case: each plate offers not merely an aesthetic experience but a complete alternative generative model for perception.

## Social Neuroscience and Joint Improvisation

Recent work in social neuroscience and art therapy emphasizes the role of joint improvisation in synchronizing neural states. Mikhailova and Friedman's "Partner Pen Play in Parallel" (PPPiP) [@mikhailova2018partner] proposes that simultaneous, non-verbal co-creation on a shared surface facilitates "controlled novelty" and inter-brain synchrony. This practice operationalizes the Active Inference account of communication not merely as signal transmission but as the mutual alignment of generative models. Just as Blake's "fourfold vision" integrates diverse faculties, PPPiP demonstrates how shared aesthetic action can construct a "collective self-evidencing" dynamic, where the relationship itself becomes the agent minimizing surprise.

## Psychedelics and the Predictive Mind

Aldous Huxley's *The Doors of Perception* [@huxley1954doors]---its very title drawn from Blake---proposed that psychedelic experience reveals perception ordinarily filtered by the brain's "reducing valve." Carhart-Harris and Friston's REBUS model [@carthartharris2019rebus] formalized this intuition, showing that psychedelics reduce the precision of high-level priors. Safron and colleagues' ALBUS framework [@safron2025albus] now extends REBUS into a comprehensive account: psychedelics can both relax beliefs and strengthen them, producing the full spectrum of altered states from prior dissolution to intensified meaning-making. This is Blake's "cleansing" rendered computational---the doors of perception swing open when prior dynamics shift, allowing sensory evidence to reshape the model. The continuity from Blake through Huxley to ALBUS illustrates how the same phenomenological insight has been rediscovered across centuries and progressively formalized.

## Northrop Frye's Systematic Blake

Frye's *Fearful Symmetry* [@frye1947fearful] remains the foundational systematic treatment of Blake's mythology. Frye demonstrated that Blake's prophetic books constitute a coherent cosmological system, not isolated flights of fancy. Our paper depends on Frye's insight that Blake's symbolism is systematic---without that systematicity, the structural correspondences with Active Inference would dissolve into vague analogy. Where Frye mapped Blake's system as literary criticism, we map it as cognitive architecture.

## Comparative Systems: Blake and Fuller

While Frye elucidated the internal coherence of Blake's system, recent comparative work highlights Blake's role as a system-*builder* akin to modern comprehensivists. Friedman's study of Blake and Buckminster Fuller [@friedman2023blake] juxtaposes Blake's mythopoetic architecture with the Synergetics of Fuller and Ed J Applewhite. Both thinkers confronted the "single vision" of their respective eras---Newtonian mechanics for Blake, specialization and technocracy for Fuller---by constructing comprehensive, fourfold (or tetrahedral) epistemologies. This comparison underscores that Blake's "system" was not a static dogma but a dynamic *tool for thought*, designed to prevent enslavement by another's system.

## Phenomenological Traditions

The phenomenological tradition provides crucial methodological precedent. Merleau-Ponty's *Phenomenology of Perception* [@merleau1962phenomenology] argues that perception is fundamentally embodied---the body is not an object among objects but the condition of objecthood itself. This directly parallels Active Inference's claim that the Markov blanket *constitutes* the distinction between agent and environment. Blake's rejection of Cartesian dualism---"Man has no Body distinct from his Soul"---anticipates Merleau-Ponty's overcoming of the mind-body problem through embodied intentionality.

Husserl's concept of intentionality---that consciousness is always *consciousness of* something---prefigures the Active Inference insight that inference is always inference *about* hidden states. The noematic content (what is intended) depends on the noetic act (how it is intended), just as the posterior depends on how priors and likelihoods are weighted. Blake's "As a man is, so he sees" expresses this dependency of object on mode of perception.

## Extended Mind and 4E Cognition

Clark and Chalmers' "Extended Mind" thesis [@clark1998extended] argues that cognitive processes extend beyond the skull into environmental structures. This resonates with Blake's insistence that imagination is not a private mental faculty but participates in a cosmic creativity: "Man is All Imagination God is Man \& exists in us \& we in him." The recursive embedding---existing in each other---describes precisely the nested Markov blankets that enable multi-agent coordination.

The broader 4E cognition movement (embodied, embedded, enacted, extended) provides contemporary articulation of Blake's critique of disembodied reason. Varela, Thompson, and Rosch's *The Embodied Mind* [@varela1991embodied] argues for the inseparability of cognition from sensorimotor engagement---exactly Blake's claim that "Energy is Eternal Delight" and that perception requires active participation, not passive reception.

## Affect Theory and Precision Weighting

Contemporary affect theory illuminates the role of precision in shaping inference. Damasio's somatic marker hypothesis [@damasio1994descartes] proposes that emotional states guide decision-making by tagging options with bodily valence---a form of affective precision weighting. Blake's Luvah (passion) and his claim that "thought alone can make monsters, but the affections cannot" anticipates this: pure reasoning unmoored from bodily affect produces biologically non-viable conclusions.

Precision weighting in Active Inference formalizes what matters: high precision signals "attend to this." Affect theory recognizes that mattering is not cognitive but visceral---we *feel* significance before we reason about it. Blake's repeated insistence on passion, energy, and delight as constitutive of vision (not decorative enhancements) aligns with this affective grounding of inference.

## Predictive Processing and Aesthetic Experience

The application of predictive processing to aesthetics has matured rapidly. The 2024 *Philosophical Transactions of the Royal Society B* theme issue on art, aesthetics, and predictive processing [@vandecruys2024order] represents a watershed: for the first time, a major scientific journal dedicated an entire volume to exploring how the brain's predictive architecture shapes aesthetic engagement. Van de Cruys, Bervoets, and Moors argue that aesthetic experience arises from the interplay of order and change---precisely the dynamic Blake dramatized as the "Marriage of Heaven and Hell," where reason (order) and energy (change) are both "necessary to Human existence."

Kukkonen's *Probability Designs* [@kukkonen2020probability] extends predictive processing to literary engagement, modeling how readers generate predictions, encounter surprise, and update their models during narrative comprehension. This work provides methodological precedent for our approach: if predictive processing can illuminate how readers engage with novels, it can equally illuminate how Blake's prophetic structures engage the perceptual system.

## Consciousness as Controlled Hallucination

Anil Seth's *Being You* [@seth2021being] advances the thesis that all perception is a form of "controlled hallucination"---the brain's best guess about the causes of sensory signals, constrained but never determined by incoming evidence. This language---perception as active construction rather than passive reception---resonates strikingly with Blake's insistence that we see "through" the eye, not "with" it. Where Seth's framework emphasizes the constructive, model-dependent nature of all experience, Blake had already proclaimed: "A fool sees not the same tree that a wise man sees" (*Marriage of Heaven and Hell*, Plate 7). Both thinkers deny the Enlightenment premise that perception is simply the imprint of an external world on a passive receiver.

## Cognitive Romanticism

A new field is coalescing at the intersection of Romantic literary studies and cognitive science. Savarese's *Romanticism's Other Minds* [@savarese2020romanticism] reassesses early relationships between Romantic poetry and scientific thought, uncovering a "prehistory of cognitive approaches to literature" within the Romantic tradition itself. The Romantic poets---Wordsworth, Coleridge, Shelley, and Blake---were not merely literary figures but active theorists of mind, perception, and social cognition. Our paper extends this tradition by providing what the Romantics lacked: the formal apparatus to make their deepest intuitions computationally precise.

## Cultural Affordances and Shared Models

Veissière and colleagues [@veissiere2020thinking] apply Active Inference to cultural cognition, arguing that shared generative models---"thinking through other minds"---constitute the mechanism of cultural transmission and niche construction. Their framework treats culture not as a static repository of information but as a living system of shared priors, jointly updated through epistemic foraging and cooperative action. This directly informs our reading of Blake's Jerusalem: the city is not merely a utopian vision but a formally specifiable shared generative niche, constructed and maintained through the "Mental Fight" of collective inference.

## Our Contribution

Prior scholarship has noted resonances between Romantic thought and cognitive science at the level of general themes (embodiment, creativity, the limits of mechanism). Our paper is the first to provide *specific formal mappings* between Blake's prophetic system and the mathematical apparatus of Active Inference. We move beyond analogy to structural correspondence: identifying not merely thematic overlap but shared topology (the Markov blanket as Blake's door), shared dynamics (free energy minimization as cleansing), and shared architecture (hierarchical generative models as fourfold vision). This synthesis arrives at a moment when both fields---predictive processing aesthetics and cognitive Romanticism---are independently converging on the same questions. Our contribution is to continue work on that bridge (or at least point towards the gap to be respected!).



```{=latex}
\newpage
```


# Theoretical Foundations {#theory}

*The mathematics of self.* This section reviews the formal apparatus of the Free Energy Principle and Active Inference. We present the core formalisms—variational free energy, Markov blankets, hierarchical generative models, precision weighting, prediction error, expected free energy, and multi-agent extensions—that the subsequent synthesis will bring into structural alignment with Blake's prophetic phenomenology.

## The Free Energy Principle {#fep}

Self-organizing systems persist by minimizing surprise (realism), or at least can be viewed as if they do (instrumentalism). Friston's Free Energy Principle (FEP) formalizes this imperative [@friston2010free; @friston2006free], now comprehensively synthesized in Parr, Pezzulo, and Friston's canonical textbook [@parr2022active].

**Variational free energy** provides a tractable upper bound on surprise (negative log model evidence):

\begin{equation}\label{eq:free_energy}
F = \mathbb{E}_q[\ln q(\theta) - \ln p(o, \theta)]
\end{equation}

where $o$ denotes observations, $\theta$ denotes hidden states (causes), $q(\theta)$ is a variational density encoding the agent's beliefs, and $p(o, \theta)$ is the generative model specifying how hidden states produce observations.

**Decomposition** reveals the relationship between free energy, divergence, and surprise:

\begin{equation}\label{eq:fe_decomposition}
F = D_{KL}[q(\theta) \| p(\theta | o)] - \ln p(o)
\end{equation}

Since KL-divergence is non-negative, free energy upper-bounds surprise:

\begin{equation}\label{eq:surprise_bound}
F \geq -\ln p(o)
\end{equation}

This bound is tight when $q(\theta) = p(\theta | o)$, i.e., when the agent's beliefs equal the true posterior. Minimizing $F$ thus serves two functions simultaneously: it makes beliefs more accurate (reducing the divergence term) and implicitly minimizes surprise (the model evidence term).

### Minimization Pathways

Two complementary pathways reduce free energy (Equation \ref{eq:free_energy}):

1. **Perceptual inference** — Update beliefs $q(\theta)$ toward the true posterior $p(\theta | o)$. This is changing mind to fit world.
2. **Active inference** — Select actions $a$ that sample observations $o$ consistent with predictions. This is changing world to fit mind.

Both pathways reduce the same objective. The agent that updates its beliefs *and* acts on the world is performing complete free energy minimization.

### Expected Free Energy and Policy Selection

Agents must also select among possible courses of action (policies $\pi$). The **expected free energy** $G(\pi)$ evaluates policies by their anticipated consequences:

\begin{equation}\label{eq:expected_free_energy}
G(\pi) = -\mathbb{E}_{\tilde{q}}[\ln p(o_\tau | C)] + \mathbb{E}_{\tilde{q}}[D_{KL}[q(\theta_\tau | o_\tau, \pi) \| q(\theta_\tau | \pi)]]
\end{equation}

where $C$ encodes preferred observations (prior preferences), and $\tilde{q}$ denotes the predictive density under the policy. The first term drives the agent toward outcomes it prefers; the second drives it to resolve uncertainty about hidden states. Optimal policies minimize $G(\pi)$, balancing exploitation (pragmatic value) against exploration (epistemic value) [@dacosta2020active; @parr2022active].

This decomposition is central to the synthesis that follows: it formally separates the *habitual* from the *curious*, the routine from the exploratory—categories that recur throughout the humanistic tradition under different names.

## The Markov Blanket {#blanket}

The Markov blanket defines the statistical boundary of any autonomous system, partitioning states into internal, external, and blanket (interface) components [@friston2019markov; @kirchhoff2018markov].

**Conditional independence:**

\begin{equation}\label{eq:conditional_independence}
p(\mu | \eta, B) = p(\mu | B)
\end{equation}

Internal states $\mu$ are conditionally independent of external states $\eta$ given blanket states $B$. The blanket comprises two complementary channels:

| Component | Symbol | Flow Direction | Role |
| :---------- | :------- | :--------------- | :----- |
| Sensory states | $s$ | World $\to$ Self | Carry observations |
| Active states | $a$ | Self $\to$ World | Carry interventions |
| **Blanket** | $B = \{s, a\}$ | Bidirectional | The statistical interface |

Every self-organizing system—from cell to organism to social group—possesses a Markov blanket. The blanket is constitutive: without it, there is no distinction between system and environment, hence no inference. The topology of this partition—what is inside, what is outside, what mediates—determines the scope and character of an agent's engagement with its world.

### Nested Blankets and Multi-Scale Organization

Markov blankets nest recursively: cells within organs, organs within organisms, organisms within social groups. Each scale defines its own internal/external partition and performs its own inference [@kirchhoff2018markov; @ramstead2018answering]. This nesting is not merely a descriptive convenience but a formal property of hierarchical self-organization.

## Hierarchical Generative Models {#hierarchy}

Generative models are typically layered, with each level predicting the activity of the level below [@clark2016surfing; @hohwy2013predictive].

**Hierarchical factorization:**

\begin{equation}\label{eq:hierarchical_model}
p(o, \theta) = p(o | \theta_1) \prod_{i=1}^{n-1} p(\theta_i | \theta_{i+1}) \cdot p(\theta_n)
\end{equation}

At the lowest level, $\theta_1$ generates observations through the likelihood $p(o | \theta_1)$. Each higher level $\theta_{i+1}$ provides the prior context for the level below. The deepest level $\theta_n$ encodes the most abstract, slowly varying regularities of the environment.

This architecture has several key properties:

- **Abstraction increases with depth.** Low levels encode fast sensory features; high levels encode slow contextual structure.
- **Temporal scale separation.** Higher levels change more slowly, providing a stable context for faster dynamics below [@kiebel2008hierarchy; @friston2017deep].
- **Bidirectional message passing.** Top-down predictions and bottom-up prediction errors flow through the hierarchy, settling jointly to minimize free energy.

The depth of the hierarchy determines the scope of patterns the model can represent—from local texture to global meaning.

### Model Evidence and Complexity

The marginal likelihood (model evidence) quantifies how well a generative model accounts for observations:

\begin{equation}\label{eq:model_evidence}
\ln p(o) = \mathbb{E}_{q}[\ln p(o | \theta)] - D_{KL}[q(\theta) \| p(\theta)]
\end{equation}

Good models maximize accuracy while minimizing complexity—a formal instantiation of Occam's razor. Overly simple models are inaccurate; overly complex models overfit. The free energy bound (Equation \ref{eq:surprise_bound}) ensures that minimizing $F$ implicitly maximizes model evidence, favoring parsimonious yet accurate explanations.

**Model comparison:**

\begin{equation}\label{eq:model_complexity}
F_{\text{simple}} \gg F_{\text{rich}}
\end{equation}

A model of insufficient depth incurs high free energy because it cannot account for the hierarchical structure of observations. A richer model, one with appropriate depth and structure, achieves lower free energy by capturing regularities that the shallow model misses (though a larger model may have other tradeoffs or penalization terms applied, balancing the tendency to inflate the number of parameters).

## Precision {#precision}

Precision is the inverse variance of a probability distribution—a measure of confidence or reliability:

\begin{equation}\label{eq:precision}
\pi = \sigma^{-1}
\end{equation}

In hierarchical inference, precision weights determine how strongly each level of the hierarchy influences the overall posterior. Two sources of precision compete at every level:

- **Prior precision** ($\pi_{\text{prior}}$): confidence in top-down predictions
- **Sensory precision** ($\pi_{\text{sensory}}$): confidence in bottom-up evidence

Their balance determines the character of inference:

| Regime | Condition | Perceptual Effect |
| :------- | :---------- | :------------------ |
| Prior-dominated | $\pi_{\text{prior}} \gg \pi_{\text{sensory}}$ | Expectations override evidence; hallucination-like states |
| Sensory-dominated | $\pi_{\text{sensory}} \gg \pi_{\text{prior}}$ | Sensory flooding; loss of contextual interpretation |
| Balanced | $\pi_{\text{prior}} \approx \pi_{\text{sensory}}$ | Optimal inference; accurate and contextually rich perception |

Attention, in this framework, is the optimization of precision—the process by which the brain infers the reliability of its own prediction errors and weights them accordingly [@feldman2010attention; @parr2019attention].

### Precision Dynamics and Pathology

When prior precision becomes extreme:

**Prior dominance:**

\begin{equation}\label{eq:prior_dominance}
\pi_{\text{prior}} \gg \pi_{\text{sensory}}
\end{equation}

the agent's beliefs become insensitive to new evidence. The generative model ceases to update, and perception rigidifies. Conversely, when sensory precision vastly exceeds prior precision, the agent is overwhelmed by unstructured input, unable to extract meaning. Pathological states—from delusions to anxiety disorders—can be understood as failures of precision optimization [@adams2013computational].

## Prediction Error and Message Passing {#error}

At each level of the hierarchy, the brain computes prediction error—the discrepancy between what was expected and what was observed:

\begin{equation}\label{eq:prediction_error}
\varepsilon_i = o_i - g_i(\theta_{i+1})
\end{equation}

where $g_i(\cdot)$ is the generative function mapping higher-level states to predicted observations at level $i$. Errors ascend the hierarchy; predictions descend. The system settles when $\varepsilon \rightarrow 0$ across all levels—when predictions match observations at every scale.

Each error signal (Equation \ref{eq:prediction_error}) propagates through the hierarchy defined in Equation \ref{eq:hierarchical_model}, weighted by the precision (Equation \ref{eq:precision}) assigned to that level. High-precision errors demand model revision; low-precision errors are discounted. This **precision-weighted prediction error** is the fundamental currency of hierarchical inference.

The bidirectional cascade of predictions and errors constitutes perception itself: a continuous, iterative process of generating hypotheses, testing them against evidence, and revising. Action enters when the system changes the world to reduce prediction error rather than changing beliefs.

## Temporal Depth {#temporal-depth}

Generative models can extend across time, encoding dependencies between successive observations:

**Temporal hierarchy:**

\begin{equation}\label{eq:temporal_hierarchy}
p(o_{1:T}, \theta) = \prod_{t=1}^{T} p(o_t | \theta_t) \cdot p(\theta_t | \theta_{t-1})
\end{equation}

Higher levels of the hierarchy encode slower dynamics, providing a context for the faster fluctuations below. The lowest levels track moment-to-moment sensory input; intermediate levels integrate over seconds to minutes; the deepest levels encode regularities persisting across hours, years, or longer [@kiebel2008hierarchy; @friston2017deep].

The **temporal depth** of a model determines how far into the past and future its predictions extend. A shallow model is reactive, bound to immediate stimulus; a deep model integrates broad temporal context into present inference. Extending temporal depth imposes computational cost but enables the agent to detect and exploit regularities that span long durations.

## Multi-Agent Inference {#multi-agent}

Active Inference extends naturally to systems of coupled agents, each bounded by its own Markov blanket but sharing statistical structure:

**Multi-agent coordination:**

\begin{equation}\label{eq:multi_agent}
p(o, \theta) = \prod_{i=1}^{N} p(o_i | \theta_i) \cdot p(\theta_i | \theta_{\text{shared}}) \cdot p(\theta_{\text{shared}})
\end{equation}

Multiple agents share a common prior $\theta_{\text{shared}}$—the cultural, institutional, or ecological generative model that aligns their individual inferences. Communication between agents can be formalized as generalized synchronization, where coupled systems entrain their internal dynamics to infer each other's hidden states [@friston2015duet; @veissiere2020thinking].

### Mean-Field Factorization

When the joint posterior over all hidden states is intractable, variational inference approximates it by assuming independence between factors:

**Mean-field approximation:**

\begin{equation}\label{eq:mean_field}
q(\theta) \approx \prod_{k=1}^{K} q(\theta_k)
\end{equation}

This factorization makes computation tractable but introduces coordination costs: correlations between components are lost. The quality of inference depends on how well the factorization structure matches the true dependencies in the generative model. Structured variational families that preserve key correlations improve upon the fully factorized approximation.

This formalized understanding of collective intelligence provides the necessary bridge to the aesthetic domain. If culture is a shared generative model, then art is the engineering of that model—a "cognitive" intervention that reshapes the priors of the collective.

## Cognitive Art and the Fourfold

The integration of Active Inference with broad-scale historical and aesthetic systems suggests a "cognitive art"---a practice of mind that is both rigorous and generative. Friedman's recent work on "Cognitive Art & Science" [@friedman2025cognitive] proposes a fourfold schema for intelligence that maps directly onto the Blakean/Fristonian synthesis. This framework distinguishes between the "Low Road" ($2 \rightarrow 3$) of explanatory modeling---fitting data to priors---and the "High Road" ($4 \rightarrow 3$) of anticipatory wisdom---shaping the niche to afford new forms of life. Blake's rejection of "Single Vision" (pure 2nd-ness) in favor of "Fourfold Vision" (integrated 1st, 2nd, 3rd, and 4th-ness) prefigures the move from mere error minimization to the active construction of a "wise" sensorimotor niche.

## Summary of Formal Apparatus

The following table collects the core equations and their roles in the synthesis that follows:

| Equation | Name | Role in Synthesis (§4) |
| :------ | :------- | :----------------------- |
| \ref{eq:free_energy} | Variational Free Energy | Objective function for perception and action |
| \ref{eq:fe_decomposition} | FEP Decomposition | Relation of divergence and surprise |
| \ref{eq:surprise_bound} | Surprise Bound | Evidence lower bound (ELBO) logic |
| \ref{eq:expected_free_energy} | Expected Free Energy | Policy selection (exploration/exploitation) |
| \ref{eq:conditional_independence} | Conditional Independence | Markov blanket as statistical boundary |
| \ref{eq:hierarchical_model} | Hierarchical Factorization | Depth of generative model |
| \ref{eq:model_evidence} | Model Evidence | Accuracy–Complexity trade-off |
| \ref{eq:model_complexity} | Model Comparison | Necessity of hierarchical depth |
| \ref{eq:precision} | Precision | Confidence weighting |
| \ref{eq:prior_dominance} | Prior Dominance | Pathological rigidity |
| \ref{eq:prediction_error} | Prediction Error | Bidirectional message passing |
| \ref{eq:temporal_hierarchy} | Temporal Hierarchy | Depth of temporal prediction |
| \ref{eq:multi_agent} | Multi-Agent Coordination | Shared priors and collective inference |
| \ref{eq:mean_field} | Mean-Field Approximation | Factorized variational inference |

Each of these formalisms will be brought into structural alignment with a specific aspect of Blake's prophetic phenomenology in the sections that follow.



```{=latex}
\newpage
```


# Synthesis: Eight Themes of Vision {#synthesis}

Hold your hand in front of your face. The boundary between your skin and the surrounding air is your Markov blanket—the statistical interface through which all inference flows. Blake called this the "door of perception." Two names for the same structure, separated by two centuries of intellectual history.

In what follows, we trace eight such structural identities between Blake's prophetic vision and the Active Inference framework, each demonstrated through specific perceptual scenarios that ground abstract formalism in lived experience. Each theme begins with Blake's fire—his phenomenological observation, expressed in the language of prophecy and illuminated printing—and then traces its mathematical shadow in the equations, architectures, and dynamics of computational neuroscience. The correspondences are not approximate analogies but precise structural mappings: shared topology (the Markov blanket as Blake's door), shared dynamics (free energy minimization as the cleansing of perception), shared architecture (hierarchical generative models as fourfold vision), and shared pathology (prior dominance as Newton's sleep). Figure \ref{fig:atlas} provides an overview of these eight thematic correspondences arranged as a visual atlas.

![**Thematic Atlas.** Eight structural correspondences between Blake's prophetic vision (left column) and Active Inference formalism (right column), connected by bidirectional arcs indicating the nature of each mapping. Themes span boundary topology (Doors/Markov Blanket), processing hierarchy (Fourfold Vision/Hierarchical Models), cognitive rigidity (Newton's Sleep/Prior Dominance), agent identity (Imagination/Generative Model), temporal depth (Eternity in Hour/Temporal Horizons), spatial inference (World in Grain/Scale Invariance), optimization (Cleansing/Free Energy Minimization), and collective coordination with modular cognition (Jerusalem & Zoas/Shared & Factorized Models). Color-coding groups related themes; each correspondence is developed in a dedicated subsection below.](../output/figures/fig0_thematic_atlas.png){#fig:atlas}

| Theme | Blake | Friston | Identity |
|:------|:------|:--------|:---------|
| [Boundary](04a_boundary.md) | Doors of Perception | Markov Blanket | Interface topology |
| [Vision](04b_vision.md) | Fourfold Vision | Hierarchical Model | Processing depth |
| [States](04c_states.md) | Newton's Sleep | Prior Dominance | Cognitive rigidity |
| [Imagination](04d_imagination.md) | Human Existence | Generative Model | Agent identity |
| [Time](04e_time.md) | Eternity in Hour | Temporal Horizons | Prediction depth |
| [Space](04f_space.md) | World in Grain | Spatial Hierarchy | Evidence integration |
| [Action](04g_action.md) | Cleansing | Free Energy Minimization | Optimization |
| [Collectives](04h_collectives.md) | Building Jerusalem / Four Mighty Ones | Shared & Factorized Models | Multi-agent coordination |



```{=latex}
\newpage
```


## Boundary: The Doors of Perception {#boundary}

> *"The cherub with his flaming sword is hereby commanded to leave his guard at the tree of life, and when he does, the whole creation will be consumed and appear infinite and holy, whereas it now appears finite and corrupt."*
>
> — *Marriage of Heaven and Hell*, Plate 14 [@blake1790marriage]

### The Markov Blanket

The cherub's flaming sword is the guardian of a boundary---the partition between accessible and inaccessible states. Blake's "door" is Friston's *boundary*—the statistical partition separating internal from external states:

> "The Markov blanket defines what is inside vs. outside any autonomous system—the statistical partition separating internal from external states."
>
> — Kirchhoff et al. (2018) [@kirchhoff2018markov]

This IS Blake's "door"—the boundary that mediates all contact between self and world. The blanket is constitutive, not optional.

| Blanket Component | Symbol | Blake's Image |
|:------------------|:-------|:--------------|
| External states | $\eta$ | "the Infinite" beyond |
| Sensory states | $s$ | Inflow through doors |
| Active states | $a$ | Outflow through doors |
| Internal states | $\mu$ | The perceiver in the "cavern" |
| Blanket | $B$ | "The doors of perception" |

This conditional independence structure (Equation \ref{eq:conditional_independence}) means that the blanket mediates all contact. Internal states access external states *only* through the interface. The doors are not optional---they are constitutive.

Blake's "cavern" is not metaphor but *phenomenology*: the subjective space of one whose doors are narrowed. The "chinks" are the impoverished sensory channels of a rigid generative model.

Blake articulated this boundary condition repeatedly. The bounded itself produces suffering:

> *"The Bounded is loathed by its possessor. The same dull round, even of a Universe, would soon become a Mill with complicated wheels."*
>
> — *There is No Natural Religion*, Series B [@blake1788natural]

Yet energy is the fundamental currency crossing the boundary:

> *"Energy is the only life and is from the Body and Reason is the bound or outward circumference of Energy. Energy is Eternal Delight."*
>
> — *Marriage of Heaven and Hell*, Plate 4 [@blake1790marriage]

Blake identifies Reason as the "bound"---the circumference or blanket edge that delimits the system. Energy, by contrast, is the vital flow that crosses this boundary. From this distinction follows his foundational claim about the nature of perception:

> *"Man's Perceptions are not bounded by Organs of Perception; he perceives more than Sense (tho' ever so acute) can discover."*
>
> — *There is No Natural Religion*, Series B [@blake1788natural]

The Markov blanket is necessary but not sufficient. The door mediates; cleansing transforms how it mediates. Figure \ref{fig:doors} illustrates this statistical boundary and its Blakean phenomenology.

> **Demonstration: The Sunrise**
>
> Blake famously contrasted two ways of seeing the sun:
>
> *"When the sun rises, do you not see a round disk of fire somewhat like a guinea? O no, no, I see an Innumerable company of the Heavenly Host crying, 'Holy, Holy, Holy.'"*
>
> Both observers share the same Markov blanket—the same sensory channels, the same visual cortex. What differs is how the door mediates:
>
> | Component | Friend's Experience | Blake's Experience |
> |:----------|:--------------------|:-------------------|
> | **Sensory states** ($s$) | Photons → "round, golden, ~30° altitude" | Same photons → rich associative cascade |
> | **Internal states** ($\mu$) | Minimal categorical prediction: "sun" | Full generative model: cosmic meaning |
> | **Active states** ($a$) | Glance, categorize, move on | Sustained attention, devotional engagement |
>
> **Same door. Different cleansing.** The friend's perception is not wrong—but it is shallow. Blake's perception engages deeper layers of the generative model. Both are valid inferences; one draws on vastly more model depth.

### Boundary Constitution: Naming Creates Separation

Blake understood that boundaries are *constituted*, not given. The act of naming creates the inside/outside distinction:

> *"they gave to it a Space & namd the Space Ulro"*
>
> — *Vala, or The Four Zoas*, Night the First [@blake1797fourzoas, E303]

The Markov blanket is not discovered but *constituted*. "Naming the Space" IS boundary formation. Ulro—Blake's realm of materialist limitation—comes into being through the act of partition.

### The Abyss as KL-Divergence

When Urizen separates from Ahania (his emanation, his feminine counterpart), Blake describes the resulting gap in terms that directly anticipate information-theoretic distance:

> *"Ahania (so name his parted soul)... how wide the Abyss Between Ahania and thee!"*
>
> — *The Book of Ahania*, Chapter III [@blake1795ahania]

This "Abyss" evokes information-theoretic distance—the separation between states that should be unified. Blake's mythic language of partition anticipates what Active Inference formalizes as divergence between distributions. The "parted soul" represents a split generative model; the wider the Abyss, the greater the separation.

### Forged Boundaries

The blanket is not simply given and absolute, but *constructed*:

> *"He forg'd nets of iron around"*
>
> — *The Book of Ahania* [@blake1795ahania]

"Forging" emphasizes the active construction and identification of boundary conditions. The Markov blanket is manufactured materially and mentally. This has profound implications: what is forged can be reforged, and what is identified can be mis- and re-identified.

### Body as Blanket Interface

Blake's most direct statement of embodied cognition anticipates the blanket formalism:

> *"Man has no Body distinct from his Soul for that calld Body is a portion of Soul discernd by the five Senses, the chief inlets of Soul in this age"*
>
> — *Marriage of Heaven and Hell*, Plate 4 [@blake1790marriage]

"Inlets" = sensory states $s$. The body IS how mind interfaces with world—not a separate substance but the blanket itself. No ontological separation exists; only the functional partition of the blanket.

### Imagination's Outline vs. Nature's Dissolution

Blake's late work makes explicit the distinction between raw data and model structure:

> *"Nature has no Outline: but Imagination has. Nature has no Tune: but Imagination has. Nature has no Supernatural & dissolves: Imagination is Eternity"*
>
> — *The Ghost of Abel*, Plate 1 [@blake1822abel]

Nature (observations $o$) is unstructured flow. Imagination (the generative model $p(o, \theta)$) provides boundaries, form, temporal structure ("Tune"). The model is more real than the data because it is what makes data *intelligible*. Without the model's outline, perception dissolves into chaos.

### Contemporary Resonance: From Blake Through Huxley to ALBUS

The lineage from Blake's "Doors" to contemporary neuroscience runs through a single remarkable chain. Aldous Huxley borrowed Blake's phrase for *The Doors of Perception* [@huxley1954doors], proposing that the brain operates as a "reducing valve" filtering the totality of experience into manageable form. Carhart-Harris and Friston's REBUS model [@carthartharris2019rebus] formalized this intuition by showing that psychedelics relax the precision of high-level priors. Safron and colleagues' ALBUS framework [@safron2025albus] now extends this account: psychedelics do not merely relax beliefs (REBUS) but can also strengthen them (SEBUS), producing a richer taxonomy of altered states—from the dissolution of rigid priors to the intensification of meaning-making. The result encompasses Blake's "cleansing"—not the destruction of the boundary but the recalibration of its precision weighting, allowing prediction error to propagate more freely up the hierarchy. What Blake described as seeing "every thing... as it is: infinite" corresponds to a state of altered prior dynamics where sensory evidence reshapes inference rather than being suppressed by entrenched expectations. This is not metaphor: it is the same computational operation described in different vocabularies across three centuries.

![**The Doors of Perception as Markov Blanket.** The statistical boundary ($B = \{s, a\}$) partitions external states $\eta$ ("the Infinite") from internal states $\mu$ ("the Cavern") through two complementary channels: sensory states $s$ mediating world-to-self flow (observation, perception) and active states $a$ mediating self-to-world flow (action, decision). This implements Blake's phenomenology from *The Marriage of Heaven and Hell*, Plate 14: "If the doors of perception were cleansed every thing would appear to man as it is, Infinite. For man has closed himself up, till he sees all things thro' narrow chinks of his cavern" [@blake1790marriage]. The blanket is constitutive---not an optional filter but the necessary interface through which all inference occurs. Cleansing the doors corresponds to optimizing the model's precision weighting (Equation \ref{eq:conditional_independence}), not to eliminating the boundary itself.](../output/figures/fig1_doors_of_perception.png){#fig:doors}



```{=latex}
\newpage
```


## Vision: The Fourfold Hierarchy {#vision}

> *"The great City of Golgonooza: fourfold toward the north / And toward the south fourfold, & fourfold toward the east & west / Each within other toward the four points"*
>
> — *Jerusalem*, Plate 12 [@blake1804jerusalem]

### Hierarchical Generative Models

Golgonooza---Blake's city of art, built by the imagination---provides the architectural metaphor for hierarchical inference: fourfold in every direction, each level nested within the others. The predictive brain generates perception actively:

> "The brain is revealed as an active, generative organ: one that continually predicts its own current sensory states, using those predictions to explain away the incoming sensory signal."
>
> — [@clark2013whatever]

This bidirectional cascade IS perception—errors ascend, predictions descend:

> "Feedback connections from a higher- to a lower-order visual cortical area carry predictions of lower-level neural activities, whereas the feedforward connections carry the residual errors between the predictions and the actual lower-level activities."
>
> — [@rao1999predictive]

Four levels of perception correspond to four depths of the generative hierarchy:

| Blake Level | Symbol | Cognitive Mode | Processing |
|:------------|:-------|:---------------|:-----------|
| **Single** (Ulro) | $\theta_1$ | Quantitative | Sensory features |
| **Twofold** (Generation) | $\theta_2$ | Emotional | Affective encoding |
| **Threefold** (Beulah) | $\theta_3$ | Imaginative | Symbolic integration |
| **Fourfold** (Jerusalem) | $\theta_4$ | Unified | Complete model engagement |

**Fourfold hierarchical factorization:**

\begin{equation}\label{eq:fourfold_hierarchy}
p(o, \theta_{1:4}) = p(o | \theta_1) \prod_{i=1}^{3} p(\theta_i | \theta_{i+1}) \cdot p(\theta_4)
\end{equation}

Fourfold vision engages all levels of the hierarchy (Equation \ref{eq:fourfold_hierarchy}; see Figure \ref{fig:fourfold}). Single vision collapses to $\theta_1$ alone, reducing the general hierarchical model (Equation \ref{eq:hierarchical_model}) to a single layer. The hierarchy is not ornament---it is the architecture of meaning.

Blake grasped this hierarchical principle:

> *"The Eye sees more than the Heart knows."*
>
> — *Visions of the Daughters of Albion*, title page [@blake1793visions]

Even the lower level (eye/sensation) accesses more than higher cognition (heart/understanding) can process. The crooked roads of genius circumvent linear reasoning:

> *"Improvement makes strait roads; but the crooked roads without Improvement are roads of Genius."*
>
> — *Marriage of Heaven and Hell*, Proverbs of Hell [@blake1790marriage]

Hierarchy need not mean rigid order—the genius finds shortcuts through visionary compression. Worton's analysis of Blake's intertextuality reveals that these "crooked roads" function as radical reconfigurations of existing models, not mere deviations from linearity [@worton1982blake].

### Golgonooza: The Architecture of the Generative Model

Blake's mythic city Golgonooza—the city of art, built by Los the imagination—provides a structural diagram of hierarchical inference. Recall the passage quoted at the opening of this section: "fourfold toward the north / And toward the south fourfold, & fourfold toward the east & west / Each within other toward the four points."

Four directions = four hierarchical levels. "Each within other" = nested structure. Golgonooza IS the generative model's architecture—a city that is simultaneously spatial and cognitive, built from the material of imagination itself.

The fourfold structure extends in all dimensions: north/south/east/west map to the Four Zoas (Urthona/Urizen/Luvah/Tharmas), each representing a distinct mode of inference. The city is not static but perpetually under construction—Los labors at the furnaces, continually rebuilding the model.

### Organs of Perception as Model-Dependent

Blake makes explicit that perception is not passive reception but active model-dependent construction:

> *"Creating Space, Creating Time... such was the variation of Time & Space, which vary according as the Organs of Perception vary"*
>
> — *Jerusalem*, Plate 98 [@blake1804jerusalem]

Space and time are not objective containers but generative model outputs. Different models produce different space-times. The "Organs of Perception" are not fixed biological apparatus but the structure of inference itself—and this structure can vary.

This anticipates the Active Inference insight that even basic phenomenal properties like spatial extent and temporal duration are inferred, not given. The model creates the coordinate system within which observations are interpreted.

Anil Seth's contemporary formulation crystallizes this point: all perception is a "controlled hallucination"—the brain's best guess about the causes of sensory signals, constrained but not determined by incoming evidence [@seth2021being]. Blake's fourfold vision is, in these terms, a taxonomy of hallucination depths: single vision is a shallow, rigid hallucination dominated by sensory constraint; fourfold vision is a deep, flexible hallucination where the generative model's own creative structure participates fully in what is perceived. The "fool" and the "wise man" who see different trees are running different models on the same data—and both perceptions are, in Seth's precise sense, controlled hallucinations.

Blake was acutely aware that deeper vision is not merely unseen but actively *pathologized* by the regime of single vision. In *Milton*, he names this suppression directly:

> *"Calling the Human Imagination: which is the Divine Vision & Fruition*
> *In which Man liveth eternally: madness & blasphemy, against*
> *Its own Qualities, which are Servants of Humanity, not Gods or Lords."*
>
> — *Milton*, Plate 32 [@blake1804milton]

"Madness & blasphemy" is the diagnostic frame that prior-dominated inference applies to perception that exceeds its own model. From within Newton's Sleep, fourfold vision looks pathological precisely because the shallow model cannot represent the hierarchical depth that makes it possible—it can only classify what it cannot compute as error, delusion, or transgression. Blake's counter-move is to insist that imagination's "Qualities" are "Servants of Humanity, not Gods or Lords": the deeper levels of the generative model serve the agent's self-evidencing; they are not external authorities but functional capacities. This anticipates contemporary debates in psychedelic neuroscience, where expanded perceptual states—once dismissed as mere hallucination—are increasingly recognized as alternative precision regimes with their own epistemic validity [@carthartharris2019rebus].

![**The Fourfold Vision Hierarchy.** Blake's four perceptual levels mapped to corresponding depths of the Active Inference hierarchical generative model (Equation \ref{eq:fourfold_hierarchy}). **Single Vision** (Ulro, $\theta_1$, gray): quantitative sensory registration---"Newton's sleep," seeing a rose as cells and chemistry. **Twofold Vision** (Generation, $\theta_2$, blue): emotional-intellectual engagement---perceiving beauty, desire, and symbolic meaning. **Threefold Vision** (Beulah, $\theta_3$, purple): imaginative synthesis---"soft Beulah's night," where contraries reconcile in art and myth. **Fourfold Vision** (Jerusalem, $\theta_4$, gold): full hierarchical integration---"supreme delight," unified engagement of all model depths. Left column: Blake's phenomenological descriptions; right column: Active Inference processing levels. Ascending arrows indicate increasing hierarchical depth and precision integration. Source: Letter to Thomas Butts, 22 November 1802 [@blake1802butts].](../output/figures/fig2_fourfold_vision.png){#fig:fourfold}



```{=latex}
\newpage
```


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



```{=latex}
\newpage
```


## Imagination: The Generative Model {#imagination-synthesis}

> *"Man is All Imagination God is Man & exists in us & we in him"*
>
> — Annotations to Berkeley's *Siris* [@blake1820berkeley]

### The Generative Model as Self

Blake's claim is radical and recursive: not merely that imagination constitutes human existence, but that the relationship between agent and model is one of mutual entailment---"exists in us & we in him." The generative model does not belong to an agent; the generative model *is* the agent. Active Inference formalizes this:

> "Consciousness is nothing more than inference about my future; namely, the self-evidencing consequences of what I could do."
>
> — [@friston2018self]

The self as process, not entity:

> "The self is the result of an ongoing predictive process within a generative model that is centered onto the organism."
>
> — [@limanowski2013minimal]

And the body as probabilistically "most likely to be me":

> "One's own body is the one which has the highest probability of being 'me' as other objects are probabilistically less likely to evoke the same sensory inputs."
>
> — [@apps2014free]

**Agent identity:**

\begin{equation}\label{eq:agent_identity}
\text{Self} \equiv p(o, \theta)
\end{equation}

The generative model defines:

- What counts as inside/outside (blanket structure)
- What states are expected (prior beliefs)
- What observations mean (likelihood mapping)
- What actions are available (policy repertoire)

Without model, no agent. The self *is* the generative model (Equation \ref{eq:agent_identity}), bounded by its Markov blanket (Equation \ref{eq:conditional_independence}). Seth's "cybernetic Bayesian brain" makes this explicit: selfhood arises from the brain's predictive model of its own body, a "controlled hallucination" grounded in interoceptive and proprioceptive inference [@seth2014cybernetic]. Blake saw this two centuries earlier: "As a man is, so he sees." The internal structure determines external appearance.

> **Demonstration: Who Is Seeing?**
>
> Close your eyes. Imagine a red rose—its color, curve, scent.
>
> Now ask: *who* is imagining? You might answer "I am." But look closer. The generative model that produces "rose" *is* the entity doing the imagining. There is no homunculus watching the mental screen; the screen is the seer.
>
> Blake: "Man is All Imagination God is Man & exists in us & we in him."
>
> The recursive "in us / we in him" captures the autopoietic loop: the model models itself modeling. No agent exists beneath the model. The model *is* the agent.

Blake's embodied vision:

> *"The Eternal Body of Man is The Imagination, that is, God himself, The Divine Body."*
>
> — Annotation to Laocoon [@blake1826laocoon]

> *"Mental Things are alone Real; what is call'd Corporeal Nobody knows of its Dwelling Place; it is in Fallacy & its Existence an Imposture."*
>
> — *Vision of the Last Judgment* [@blake1810judgment]

And the constitutive claim:

> *"As a man is, so he sees. As the Eye is formed, such are its Powers."*
>
> — Letter to Dr. Trusler, 23 August 1799 [@blake1799trusler]

The generative model shapes what can be perceived. The "formed Eye" is the structure of inference itself.

> *"The world of imagination is the world of eternity."*
>
> — *Vision of the Last Judgment* [@blake1810judgment]

### Man Is All Imagination: Autopoiesis and Self-Modeling

The recursive structure of Blake's epigraph above—"exists in us & we in him"—is autopoiesis: the agent IS its generative model. "God in us" = our model of world. "We in him" = we are part of what the model represents. The nested embedding describes Markov blankets within Markov blankets—the recursive self-modeling that constitutes agency.

There is no man "underneath" imagination; imagination is what man *is*. The generative model doesn't belong to an agent—the generative model IS the agent.

### Mental Things Alone Real

Blake extends this to a full phenomenological idealism. His declaration that "Mental Things are alone Real" and that the "Corporeal" is "in Fallacy & its Existence an Imposture" (*Vision of the Last Judgment* [@blake1810judgment]) maps directly onto the epistemic structure of Active Inference: internal states (beliefs) are all we access. External states are inferred, never directly known. "Corporeal" = external states beyond the Markov blanket. We have no direct access to the world-in-itself; only to our model's predictions about it. What we call "corporeal" is a posit of inference, not an immediate given.

This is not solipsism but epistemic humility: acknowledging that all our knowledge is model-mediated.

### Knowledge by Perception, Not Deduction

Blake distinguishes parallel inference from serial reasoning:

> *"Knowledge is not by deduction but Immediate by Perception or Sense at once Christ addresses himself to the Man not to his Reason"*
>
> — Annotations to Berkeley's *Siris* [@blake1820berkeley]

Perception as parallel inference, not serial deduction. Posterior beliefs emerge from free energy minimization directly—not through step-by-step logical chains but through the simultaneous settling of the entire generative model. "Christ addresses himself to the Man" = the world speaks to the whole agent, not just the reasoning faculty.

This anticipates the Active Inference insight that perception is not a conclusion of reasoning but an immediate update of the entire belief distribution.

### Innate Ideas as Structural Priors

Against empiricist doctrine, Blake insists on innate structure:

> *"The Man who says that we have No Innate Ideas must be a Fool & Knave... Knowledge of Ideal Beauty is Not to be Acquired It is Born with us"*
>
> — Annotations to Reynolds' Discourses [@blake1808reynolds]

Structural priors are architectural, not learned. "Innate Ideas" = the priors that make inference possible. They cannot be "acquired" because they define the hypothesis space within which acquisition occurs. Without prior structure, there is nothing to update—no model to receive evidence.

### Imagination as Epistemic Foraging

If imagination is human existence—if the self *is* the generative model—then what Blake calls "creative vision" amounts to a specific computational strategy: *epistemic foraging* through counterfactual model-space. Rather than passively receiving data, the imaginative agent actively explores hypothetical configurations of its own generative model, testing alternatives that minimize expected free energy over long horizons [@veissiere2020thinking]. This is niche construction at the cognitive level: the imagination does not merely adapt to the world as found but actively reshapes the model-space within which future inference occurs. Blake's insistence that "What is now proved was once only imagin'd" is, in Active Inference terms, the claim that today's priors were yesterday's epistemic actions—imaginative explorations that became entrained belief structures. The artist, the prophet, the visionary is thus not an escapist but an *epistemic pioneer*, foraging at the frontier of model-space.



```{=latex}
\newpage
```


## Time: Temporal Horizons {#time}

> *"I see the Past, Present & Future, existing all at once*  
> *Before me."*
>
> — *Jerusalem*, Plate 15 [@blake1804jerusalem]

### Temporal Horizons

"Eternity in an hour" is not mysticism—it is *deep temporal modeling*. In Active Inference, agents construct hierarchical generative models that encode predictions at progressively longer time scales, from millisecond sensory fluctuations to narratives spanning years. The deeper the hierarchy, the wider the temporal horizon the agent can integrate into present awareness. Blake's compression of eternity into an hour describes exactly this capacity. Active Inference agents maintain predictions across multiple time scales:

> "The lowest level of this hierarchy corresponds to fast fluctuations associated with sensory processing, whereas the highest levels encode slow contextual changes in the environment."
>
> — [@kiebel2008hierarchy]

> "Slowly changing neuronal states can encode the paths or trajectories of faster sensory states."
>
> — [@friston2017deep]

**Temporal hierarchy:**

\begin{equation}\label{eq:temporal_hierarchy}
p(o_{1:T}, \theta) = \prod_{t=1}^{T} p(o_t | \theta_t) \cdot p(\theta_t | \theta_{t-1})
\end{equation}

The deeper the temporal model (Equation \ref{eq:temporal_hierarchy}), the longer the horizon of prediction. An impoverished model predicts only the immediate. A rich model extends to *aeonic* time. Figure \ref{fig:temporal} illustrates this hierarchy of temporal scales.

![**Temporal Horizons of Inference.** Four stacked trapezoid bands, widening from bottom to top, represent increasing temporal depth in the hierarchical generative model (Equation \ref{eq:temporal_hierarchy}). **Fast** (red, milliseconds): sensory processing---the immediate registration of prediction errors. **Mid** (steel blue, seconds to minutes): emotional integration---affective states that modulate precision weighting across brief episodes. **Slow** (purple, hours to years): narrative construction---the autobiographical and cultural models that contextualize experience. **Deep/Aeonic** (gold, lifetimes to eternity): the deepest temporal priors encoding civilizational and transpersonal patterns. The vertical arrow indicates increasing temporal depth. Blake's compression of temporal scales---"Every Time less than a pulsation of the artery / Is equal in its period \& value to Six Thousand Years" (*Milton*, Plate 29 [@blake1804milton])---describes the hierarchical nesting where each level encodes trajectories of the level below, and "Eternity is in love with the productions of time" (*Marriage of Heaven and Hell*, Proverbs of Hell [@blake1790marriage]).](../output/figures/fig6_temporal_horizons.png){#fig:temporal}

Blake's "Eternity" is not timelessness but *trans-temporal integration*—the capacity to hold all moments within the present perception. The hour contains eternity because the model reaches across all scales.

In *Milton*, Blake provides temporal metrics:

> *"Every Time less than a pulsation of the artery*
> *Is equal in its period & value to Six Thousand Years,*
> *For in this Period the Poet's Work is Done, and all the Great*
> *Events of Time start forth & are conceiv'd in such a Period,*
> *Within a Moment, a Pulsation of the Artery."*
>
> — *Milton*, Plate 29 [@blake1804milton]

A pulsation equals six thousand years—the prophetic compression of temporal scale. And the relationship is not opposition but love:

> *"Eternity is in love with the productions of time."*
>
> — *Marriage of Heaven and Hell*, Proverbs of Hell [@blake1790marriage]

The eternal reaches toward the temporal particular. Deep temporal models don't transcend time but *integrate* it—holding the trajectory of moments within present awareness.

### The Temporal Architecture of Los

But Blake does not stop at compression. In the lines immediately preceding the "pulsation" climax, he constructs the most extraordinary precursor to hierarchical temporal modeling in all of literature:

> *"But others of the Sons of Los build Moments & Minutes & Hours*
> *And Days & Months & Years & Ages & Periods; wondrous buildings*
> *And every Moment has a Couch of gold for soft repose,*
> *(A Moment equals a pulsation of the artery),*
> *And between every two Moments stands a Daughter of Beulah*
> *To feed the Sleepers on their Couches with maternal care.*
> *And every Minute has an azure Tent with silken Veils.*
> *And every Hour has a bright golden Gate carved with skill.*
> *And every Day & Night, has Walls of brass & Gates of adamant,*
> *Shining like precious stones & ornamented with appropriate signs:*
> *And every Month, a silver paved Terrace builded high:*
> *And every Year, invulnerable Barriers with high Towers.*
> *And every Age is Moated deep with Bridges of silver & gold.*
> *And every Seven Ages is Incircled with a Flaming Fire."*
>
> — *Milton*, Plate 28 [@blake1804milton]

This is a hierarchical generative model of temporal experience, described two centuries before the formal mathematics. Each timescale has distinct *architectural properties*—distinct structure, material, and boundary conditions:

| Temporal Scale | Blake's Architecture | Active Inference Analogue |
|:---------------|:---------------------|:--------------------------|
| Moment (pulse) | Couch of gold | Fast sensory states: soft, immediate, precious |
| Minute | Azure Tent, silken Veils | Short-term precision: flexible, semi-transparent |
| Hour | Golden Gate, carved | Attentional boundaries: structured, deliberate |
| Day/Night | Brass Walls, adamant Gates | Circadian priors: rigid, durable |
| Month | Silver Terrace, builded high | Seasonal/contextual priors: elevated perspective |
| Year | Invulnerable Barriers, high Towers | Biographical priors: strongly defended |
| Age | Moated deep, Bridges of silver & gold | Cultural priors: deep separation, costly access |
| Seven Ages | Flaming Fire | Civilizational priors: ultimate boundary |

The ascending material solidity—from gold couches to flaming fire—mirrors the increasing precision and decreasing update rate of deeper temporal levels. A "Couch" yields to the body; a "Flaming Fire" does not. The Sons of Los *build* these structures actively: temporal experience is not passively received but constructed through inference. And the "Daughter of Beulah" standing between each two Moments, feeding "the Sleepers on their Couches with maternal care," is the precision-weighting mechanism that mediates between adjacent temporal levels—ensuring smooth transitions and preventing catastrophic discontinuity.

### Drawing Out to Seven Thousand Years

Blake describes the active construction of temporal depth through the figure of Eno, an ancient prophetess:

> *"[Eno] drew it out to Seven thousand years with much care & affliction"*
>
> — *Vala, or The Four Zoas*, Night the First [@blake1797fourzoas, E300]

The model's temporal horizon can be extended—"drawn out"—but not without cost. Blake's "care & affliction" captures the computational expense of deep temporal models: maintaining predictions across long horizons demands sustained precision allocation and imposes metabolic cost on the system. The model does not naturally reach across millennia without deliberate cultivation of the hierarchical structure that makes such depth possible.

Seven thousand years echoes the Biblical span of human history—Eno's work is to hold the entire trajectory of human time within present awareness.

### Eternity Obliterated

The collapse of temporal depth is catastrophic:

> *"Till like a dream Eternity was obliterated & erasd"*
>
> — *The Song of Los*, Plate 3 [@blake1795songlos]

Deep temporal models (Eternity) compressed to shallow prediction (dream-like immediate present). When the temporal horizon collapses, what remains is reactive, stimulus-bound perception—the "dream" state of shallow inference.

This describes the Fall as temporal impoverishment: from aeonic awareness to moment-to-moment reaction.

### Drunk with the Wine of Ages

But temporal integration has limits:

> *"drunk with the wine of ages"*
>
> — *Vala, or The Four Zoas*, Night the Ninth [@blake1797fourzoas]

Over-accumulation of historical evidence ("wine of ages") impairs present inference. The temporal model can become so saturated with past that it loses responsiveness to present. This is the opposite failure mode: not temporal collapse but temporal rigidity—being so weighted by history that current observation cannot update the model.

In Active Inference terms, this corresponds to an over-fitted temporal model whose deep priors have accumulated excessive precision. When $\pi_{\text{prior}}$ at the slowest temporal scales grows unboundedly, the agent becomes captive to historical regularities and cannot accommodate novel evidence. The system is "drunk"—its inference is dominated by the accumulated weight of temporal priors rather than responsive to present sensory input. Blake thus identifies both failure modes of temporal modeling: too shallow ("Eternity obliterated") and too deep ("drunk with the wine of ages").

> **Demonstration: The Déjà Vu Moment**
>
> You walk into an unfamiliar room and feel, with absolute conviction, that you have been here before. The moment is uncanny precisely because two temporal scales are colliding: your shallow present-moment model (novel room, first visit) contradicts a deeper temporal pattern-match (this configuration of light, shape, and atmosphere resonates with a prior encoded at longer timescales). In Active Inference terms, déjà vu arises when a slow-timescale prior generates a strong top-down prediction that the current observation is *familiar*, while the fast-timescale model correctly registers *novelty*. The eerie sensation is the prediction error between hierarchical temporal levels—Blake's "Eternity in an hour" experienced as perceptual vertigo. Temporal depth is not abstract: it is the felt layering of past within present.



```{=latex}
\newpage
```


## Space: Spatial Hierarchy {#space}

> *"To see a World in a Grain of Sand*  
> *And a Heaven in a Wild Flower..."*
>
> — *Auguries of Innocence* [@blake1803auguries]

### Spatial Scale Invariance

The grain contains the world through *hierarchical evidence accumulation*. At each level of the generative model, increasingly abstract regularities are extracted from observations: texture gives way to form, form to spatial relations, spatial relations to universal principles. A sufficiently deep hierarchy finds the cosmos in the particular because the abstract structure encoded at its highest levels applies universally. The predictive brain finds universal structure in particular observations:

> "By formulating Helmholtz's original ideas on perception in terms of modern-day statistical theories, one arrives at a model of perceptual inference and learning that can explain a remarkable range of neurobiological facts."
>
> — [@friston2005theory]

**Model complexity:**

\begin{equation}\label{eq:model_complexity}
F_{\text{simple}} \gg F_{\text{rich}}
\end{equation}

A shallow model incurs vastly more free energy (Equation \ref{eq:model_complexity}) than a rich one. The shallow model sees only surface: the grain is sand. A deep model extracts universal structure: the grain is cosmos in miniature.

| Model Depth | Perception | Blake's Image |
|:------------|:-----------|:--------------|
| Shallow | Isolated particulars | "narrow chinks" |
| Intermediate | Contextual patterns | "twofold vision" |
| Deep | Universal in particular | "World in a Grain" |

The "Wild Flower" opens to "Heaven" because a sufficiently deep generative model finds infinite structure in finite observation. This is not enhancement—it is *accuracy*.

Blake's spatial cosmology extends the particularity principle:

> *"And every Space smaller than a Globule of Man's blood opens*
> *Into Eternity of which this vegetable Earth is but a shadow."*
>
> — *Milton*, Plate 29 [@blake1804milton]

The vortex phenomenon—perception's expansive/contractive dynamics:

> *"The nature of infinity is this: That every thing has its*
> *Own Vortex, and when once a traveller thro' Eternity*
> *Has passd that Vortex, he perceives it roll backward behind*
> *His path, into a globe itself infolding like a sun."*
>
> — *Milton*, Plate 15 [@blake1804milton]

And the expansion principle:

> *"If the Spectator could Enter into these Images in his Imagination, approaching them on the Fiery Chariot of his Contemplative Thought... then would he arise from his Grave, then would he meet the Lord in the Air & then he would be happy."*
>
> — *Vision of the Last Judgment* [@blake1810judgment]

Spatial perception is active—the spectator *enters* images, doesn't passively receive them. The generative model projects into the world as much as it receives from it.

### The Vortex: Each Entity's Own Markov Blanket

Blake's fullest treatment of perspectival space appears in *Milton*:

> *"The nature of infinity is this: That every thing has its / Own Vortex; and when once a traveller thro Eternity / Has passd that Vortex, he percieves it roll backward behind / His path, into a globe itself infolding like a sun"*
>
> — *Milton*, Plate 15, lines 21-35 [@blake1804milton]

Each entity has its own Markov blanket and generative model—its "Own Vortex." "Passing the Vortex" = adopting a new perspective, entering another entity's coordinate frame. "Globe itself infolding" = the old model becoming an object within the new model's representation.

The vortex is the boundary between reference frames. When you pass through another entity's vortex, you see from their perspective—but looking back, your old perspective has become a distant object, a "globe" or "sun" behind you.

In Active Inference, this corresponds to *model switching*—the capacity to adopt another agent's generative model as one's own frame of reference. Friston and Frith's "Duet for One" [@friston2015duet] formalizes precisely this process: two agents can achieve generalized synchronization by inferring each other's hidden states, effectively "passing through" each other's Markov blankets. Blake's vortex adds a phenomenological dimension that the formalism captures only structurally: the felt experience of entering another perspective and finding that one's prior viewpoint has become a distant object, reduced to a "globe" in the rearview of awareness.

This is the phenomenology of empathy formalized: to understand another is to pass through their vortex, to see from within their generative model.

### Mathematic Holiness: The Impoverished Spatial Model

Blake names the pathological reduction of spatial perception with devastating precision. In *Milton*, he describes those whose models have been stripped of imaginative depth:

> *"those combind by Satans Tyranny... are Shapeless Rocks*
> *Retaining only Satans Mathematic Holiness, Length: Bredth & Highth"*
>
> — *Milton*, Plate 32 [@blake1804milton]

"Mathematic Holiness" is the worship of pure geometric extension—Euclidean coordinates elevated to metaphysical status. When imaginative depth is removed from spatial perception, what remains is the thin, quantitative skeleton: length, breadth, height—the minimum parameters of a bounding box. The "Shapeless Rocks" are agents whose generative models have collapsed to this minimum complexity: they can localize objects in three-dimensional space but cannot perceive the hierarchical structure that makes space *meaningful*—the nested affordances, the perspectival depth, the relational richness that a deep model extracts from the same optical array.

In Active Inference terms, this is the spatial analogue of Newton's Sleep (see [§4.3 States](#states)). A model that retains "only" length, breadth, and height is a model whose spatial hierarchy has been flattened to a single level: the likelihood function $p(o|s)$ computes geometric coordinates, but the prior structure $p(s)$ that would encode ecological meaning, bodily affordance, and perspectival significance has been suppressed. The result is the "vegetable" space of Newtonian mechanics—measurable, uniform, and dead. Blake's "World in a Grain of Sand" is the antithesis: spatial perception at full hierarchical depth, where the generative model finds universal structure in local observation because its prior hierarchy is rich enough to make the extraction possible.

### Looking Through, Not With

Blake distinguishes the sensor from the inference process:

> *"I question not my Corporeal or Vegetative Eye any more than I would Question a Window concerning a Sight I look thro it & not with it"*
>
> — *Vision of the Last Judgment* [@blake1810judgment, E566]

Blake distinguishes the sensor from the inference engine with surgical precision. The eye is the likelihood function $p(o|s)$—the mapping from hidden states to observations—not the inference process itself. To look "through" the eye is to use the full generative model: the inverse mapping from observations to beliefs about hidden causes. To look "with" the eye is to confuse the sensor with inference, mistaking the data channel for the interpretation.

The eye provides observations; it does not provide understanding. Understanding requires the generative model that interprets what the eye delivers. To look "with" the eye is to mistake the window for the view—an error that reduces perception to passive reception and forecloses the active, model-driven inference that constitutes genuine seeing.

This is a statement about the distinction between the likelihood function and the full Bayesian inversion. The eye computes $p(o|s)$; seeing requires the posterior $p(s|o) \propto p(o|s) \cdot p(s)$. Confusing the two is the fundamental error of empiricism—Blake's "single vision."

> **Demonstration: The Microscope Effect**
>
> Place a leaf under a microscope. At first you see nothing but undifferentiated green blur—single vision. Adjust the focus: suddenly, cells appear—a world *within* the leaf, invisible to the unaided eye. Increase magnification: within each cell, organelles, a further world. Blake's "world in a grain of sand" is not metaphor but phenomenological report: the grain reveals a world precisely when the generative model gains hierarchical depth, when new layers of the likelihood function $p(o|s)$ map observations to increasingly fine-grained hidden causes. The microscope changes the observation channel, but it is the model—the skilled biologist's expectations about what cell types, structures, and processes *should* be visible—that transforms undifferentiated green into meaningful architecture. The instrument is the window; the model is the sight.



```{=latex}
\newpage
```


## Action: Free Energy Minimization {#action}

> *"I must Create a System. or be enslav'd by another Mans. I will not Reason & Compare: my business is to Create."*
>
> — *Jerusalem*, Plate 10 [@blake1804jerusalem]

### Free Energy Minimization

Los's imperative to *create* rather than merely reason captures the essence of active inference: the agent does not passively receive the world but actively constructs its model. The doors are cleansed when the generative model accurately mirrors reality. As the foundational paper states:

> "The free-energy principle provides a unified account of action, perception and learning based on minimizing a measure of surprise."
>
> — [@friston2010free]

> "Cortical responses can be seen as the brain's attempt to minimize the free energy induced by a stimulus and thereby encode the most likely cause of that stimulus."
>
> — [@friston2006free]

**Cleansing formalized:**

\begin{equation}\label{eq:cleansing}
\text{Cleansed perception} \iff \arg\min_q F(q, o)
\end{equation}

Free energy reaches minimum when:

- Model predictions match observations
- Prior beliefs calibrate to evidence
- Precision-weighting is optimal

Two paths to cleansing:

1. **Perception** — Update beliefs to fit world ($q(\theta) \rightarrow p(\theta | o)$)
2. **Action** — Change world to fit model ($o \rightarrow \hat{o}$)

Both are "cleansing." Both reduce free energy (Equation \ref{eq:cleansing}), driving the variational bound (Equation \ref{eq:free_energy}) toward its minimum (Figure \ref{fig:cycle}). Blake unified what later theory separated.

The generative model anticipates sensory confirmation---imagination precedes proof, the prophet *predicts* what observation will confirm. What Blake imagined, Friston's equations now prove.

Blake's energy philosophy aligns with active inference's emphasis on action:

> *"Energy is Eternal Delight."*
>
> — *Marriage of Heaven and Hell*, Plate 4 [@blake1790marriage]

The labor principle extends this creative imperative to situated practice:

> *"Great things are done when Men & Mountains meet;*
> *This is not done by Jostling in the Street."*
>
> — Notebook (c. 1807-1809) [@blake1988complete, E516]

> *"Labour well the Minute Particulars, attend to the Little-ones."*
>
> — *Jerusalem*, Plate 55, line 51 [@blake1804jerusalem]

Action on the minute particular—the precise, situated intervention—is how free energy is minimized in practice. Not grand abstraction but attentive labor.

### Flexible Senses: Precision Dynamics Before the Fall

Blake's most direct statement of voluntary precision modulation appears in *The Book of Urizen*:

> *"The will of the Immortal expanded / Or contracted his all flexible senses"*
>
> — *The Book of Urizen*, Chapter II, Plate 3 [@blake1794urizen]

Before the Fall, precision ($\pi$) could be adjusted at will—"expanded or contracted." This is Blake's clearest statement of precision dynamics: the unfallen condition is one where attention can be freely allocated.

The "all flexible senses" are not fixed channels but adjustable receptors. Flexibility is the default; rigidity is fallen.

### Contracting to the Honey Bee

Blake elaborates the scale of precision adjustment:

> *"Contracting or expanding their all flexible senses / At will to murmur in the flowers small as the honey bee"*
>
> — *Vala, or The Four Zoas*, Night the First [@blake1797fourzoas]

Senses can zoom to "honey bee" scale—precision determines resolution. The unfallen beings can adjust their sensory precision to perceive at any scale, from cosmic to microscopic. This is optimal precision assignment: the ability to weight sensory channels appropriately for the task at hand.

### Love as Affective Precision

Precision weighting operates through affect:

> *"He who Loves feels love descend into him & if he has wisdom may percieve it is from the Poetic Genius which is the Lord"*
>
> — Annotations to Swedenborg's *Divine Love and Divine Wisdom* [@blake1788swedenborg]

"Love" = affective precision. "Descend" = top-down modulation. "Wisdom" = meta-cognitive precision awareness—the ability to perceive the source of one's attention.

Affect is not separate from inference but constitutive of it. Love determines what matters, what receives high precision weighting.

### Thought Alone Makes Monsters

But inference without affective grounding drifts pathologically:

> *"Thought alone can make monsters, but the affections cannot"*
>
> — Annotations to Swedenborg [@blake1788swedenborg]

Inference without affective grounding produces biologically non-viable beliefs. "Monsters" = pathological states that no embodied system could inhabit. Affect anchors inference to survival, to what matters for the organism's persistence.

Pure reasoning, unmoored from bodily concern, can generate coherent but monstrous conclusions. The affections keep inference honest. Damasio's somatic marker hypothesis formalizes Blake's insight with striking precision: bodily affect tags candidate beliefs and actions with valence *before* deliberative reasoning can evaluate them [@damasio1994descartes]. The "affections" are somatic markers—precision signals weighted by visceral relevance. Without these embodied priors, the reasoning system falls into what Damasio terms the "high-reason" catastrophe: logically valid but existentially disastrous decisions, monsters of pure thought.

> **Demonstration: The Musician's Practice**
>
> A pianist learning a new piece begins haltingly: each note requires conscious prediction, deliberate action, effortful error correction. The prediction errors are large and frequent—every misplayed note generates surprise. Through practice, the generative model refines: the fingers begin to anticipate the score, action policy and sensory prediction converge, surprise decreases. But something else happens: the music begins to *feel* right. Affect—the bodily sense of rightness—becomes the precision signal that guides further refinement. The musician doesn't just minimize error; she shapes her model until it produces the *felt quality* of beautiful performance. This is Blake's "Mental Fight" rendered as craft: active inference through embodied skill, where action transforms both world (the sound produced) and model (the musician's internal representation). The pianist "creates a system" note by note, bar by bar—and in doing so, is herself transformed.

### Cogs Tyrannic vs. Free Wheels

Blake contrasts deterministic with flexible inference:

> *"Wheel without wheel, with cogs tyrannic / Moving by compulsion each other: not as those in Eden, which / Wheel within Wheel in freedom revolve in harmony & peace"*
>
> — *Jerusalem*, Plate 15 [@blake1804jerusalem]

"Cogs tyrannic" = fixed precision, mechanical prediction. No free parameters, no flexibility—each wheel forces the next. "Wheel within Wheel in freedom" = adjustable precision weighting, where components coordinate but are not rigidly locked.

The Edenic state is not absence of structure but *flexible* structure—wheels that revolve together in harmony without tyrannical compulsion. This is the difference between a generative model that can revise itself and one frozen in Newton's sleep.

### The Path of Least Action

Friston's path integral formulation of the free energy principle [@friston2023path] reveals a deeper connection to Blake's economy of perception. The path integral expresses system trajectories as weighted sums over all possible paths, with the most probable trajectory being the one that minimizes action—the "path of least action." Blake's imperative to "cleanse the doors" is, in this formalism, a call to find the self-evidencing trajectory: the path through model-space that minimizes free energy while maintaining the system's structural integrity. The "cogs tyrannic" are paths constrained to a single rigid trajectory; the "wheels in freedom" are paths that explore the full space of possibilities while converging on the variational minimum. Art, for Blake, is precisely this search: the creative act finds the path of least free energy through the space of possible forms, arriving at the work that resolves the most prediction error with the most elegant structure.

![**The Perception-Action Cycle.** Active Inference's dual optimization pathways annotated with corresponding Blake quotations. The central generative model $p(o, \theta)$ (orange hub) issues top-down predictions and receives bottom-up prediction errors $\varepsilon = o - g(\theta)$ through six interconnected stages: **Prediction** ("What is now proved was once imagined"), **Sensory Input** ("The senses discover'd the infinite"), **Prediction Error** ("Narrow chinks of his cavern"), **Model Update** ("Cleansed perception"), **Action Selection** ("Mental Fight"), and **World Change** ("Building Jerusalem"). Perceptual inference updates beliefs $q(\theta)$ toward the true posterior (changing mind to fit world); active inference samples observations matching predictions (changing world to fit mind). Both pathways reduce variational free energy $F$ (Equation \ref{eq:cleansing}). The cycle's continuous operation corresponds to Blake's vision of perpetual creative labor: "I must Create a System. or be enslav'd by another Mans" (*Jerusalem*, Plate 10 [@blake1804jerusalem]).](../output/figures/fig3_perception_action_cycle.png){#fig:cycle}



```{=latex}
\newpage
```


## Collectives: Shared Generative Models {#collectives}

> *"I will not cease from Mental Fight,*  
> *Nor shall my Sword sleep in my hand:*  
> *Till we have built Jerusalem,*  
> *In England's green & pleasant Land."*
>
> — *Milton*, Preface [@blake1804milton]

### Shared Generative Models

Blake's vision extends beyond individual perception to *collective awakening*. Jerusalem is not merely personal enlightenment but a shared visionary capacity—a coordinated mode of seeing that transcends the individual.

Active Inference extends naturally to multi-agent systems:

> "Generalized synchronization [emerges] as a mathematical image of communication that enables two Bayesian brains to entrain each other and, effectively, share the same dynamical narrative."
>
> — [@friston2015duet]

> "Human agents learn the shared habits, norms, and expectations of their culture through immersive participation in patterned cultural practices that selectively pattern attention and behaviour."
>
> — [@veissiere2020thinking]

This is TTOM—Thinking Through Other Minds—the mechanism of collective awakening.

**Multi-agent coordination:**

\begin{equation}\label{eq:multi_agent}
p(o, \theta) = \prod_{i=1}^{N} p(o_i | \theta_i) \cdot p(\theta_i | \theta_{\text{shared}}) \cdot p(\theta_{\text{shared}})
\end{equation}

Multiple agents share a common prior $\theta_{\text{shared}}$ (Equation \ref{eq:multi_agent})---the cultural generative model that enables coordinated perception and action. Figure \ref{fig:jerusalem} illustrates this multi-agent architecture.

![Building Jerusalem: Collective Generative Models. Three individual agents, each bounded by its own Markov blanket, contribute to and draw from a shared generative model ("Jerusalem," $\theta_{\text{shared}}$). The "Mental Fight" zone represents the active process of model-building and coordination through which individual inference aligns with collective priors (Equation \ref{eq:multi_agent}).](../output/figures/fig7_collective_jerusalem.png){#fig:jerusalem}

Each individual agent remains bounded by its own Markov blanket (Equation \ref{eq:conditional_independence}), but the shared prior aligns their inference.

Blake's most radical claim about the collective nature of identity appears in *Milton*:

> *"We are not Individuals but States: Combinations of Individuals"*
>
> — *Milton*, Plate 32 [@blake1804milton]

This is not merely the claim that agents share priors—it is the deeper assertion that *individual identity itself* is a collective phenomenon. A "Combination of Individuals" is a factorization of agency: what appears to be a single self is in fact a composition of shared model components, cultural priors, and socially entrained precision weightings. The shared prior $\theta_{\text{shared}}$ in Equation \ref{eq:multi_agent} is not external to individuals but *constitutive* of them—the individual $\theta_i$ cannot be separated from the collective without remainder. Blake's "States" are thus collective attractors in the multi-agent generative model: configurations that groups of agents fall into together, and that "Change" (dissolve, reconfigure) when the collective model is revised. "Satan & Adam are States Created into Twenty-seven Churches"—not individuals who happened to organize churches, but *model configurations that manifest as institutional structures*.

| Component | Symbol | Blake's Image |
|:----------|:-------|:--------------|
| Individual models | $\theta_i$ | Each perceiver |
| Shared prior | $\theta_{\text{shared}}$ | Jerusalem |
| Collective action | $a_{\text{collective}}$ | "Mental Fight" |
| Coordinated perception | $o_{\text{aligned}}$ | Shared vision |

### The Mental Fight

Blake's "Mental Fight" is model-building at civilizational scale:

- **Education** shapes the generative models of the young
- **Art** restructures perception through alternative priors
- **Contemplative practice** adjusts precision weighting
- **Cultural production** creates shared predictive structures

> *"The Nature of my Work is Visionary or Imaginative; it is an Endeavour to Restore what the Ancients called the Golden Age."*
>
> — *Vision of the Last Judgment* [@blake1810judgment]

The Golden Age is not historical but *perceptual*—a state where collective generative models enable richer inference.

### Coordinated Inference

Active Inference extends naturally to multi-agent systems [@friston2019markov]. Ramstead, Badcock, and Friston formalize this extension through nested Markov blankets: blankets within blankets, individuals within communities within cultures, each scale operating as an autonomous inference system while coupling to the scales above and below [@ramstead2018answering]. When agents share priors, they:

1. **Align predictions** — Expectations converge across the collective
2. **Coordinate action** — Behavior becomes mutually intelligible  
3. **Distribute computation** — Complex inference divides across agents
4. **Accumulate evidence** — Collective learning exceeds individual capacity

Blake's Jerusalem is precisely this: a shared generative model enabling coordinated cleansing of perception. The doors open not one by one, but together.

> *"Mutual Forgiveness of each Vice—Such are the Gates of Paradise."*
>
> — *For the Sexes: The Gates of Paradise* [@blake1988complete]

Paradise requires *mutual* forgiveness—collective precision adjustment where agents release rigid priors toward one another. The gates open through shared model revision.

Blake's collective vision finds its fullest expression in *Jerusalem*:

> *"This is Jerusalem in every Man*
> *A Tent & Tabernacle of Mutual Forgiveness."*
>
> — *Jerusalem*, Plate 54 [@blake1804jerusalem]

> *"O lovely Emanation of Albion Awake and overspread all Nations as in Ancient Time*
> *For lo! the Night of Death is past and the Eternal Day*
> *Appears upon our Hills."*
>
> — *Jerusalem*, Plate 97 [@blake1804jerusalem]

The awakening is collective—Albion (England/humanity) awakens as a unified agent.

### From Single to Collective Vision

The fourfold hierarchy applies not only to individuals but to societies:

| Level | Individual | Collective |
|:------|:-----------|:-----------|
| **Single** | Mechanical perception | Industrial society |
| **Twofold** | Emotional engagement | Artistic communities |
| **Threefold** | Imaginative vision | Cultural movements |
| **Fourfold** | Integrated awareness | Jerusalem |

Blake's critique of "dark Satanic Mills" is computational: industrial modernity imposes shallow, prior-dominated generative models on the collective. Building Jerusalem means reconstructing shared priors to enable deeper inference.

> *"England! awake! awake! awake!*  
> *Jerusalem thy Sister calls!"*
>
> — *Jerusalem*, Plate 77 [@blake1804jerusalem]

The awakening is collective. The sister calls to the nation. The doors of perception—once cleansed—reveal not isolated infinity but *shared* infinity. The prophet's vision becomes the people's sight.

### Fall into Division and Resurrection to Unity

Blake frames the cosmic narrative as multi-agent decomposition and re-coordination:

> *"Sing His fall into Division & his Resurrection to Unity"*
>
> — *Vala, or The Four Zoas*, Night the First [@blake1797fourzoas]

"Division" = factorization into separate agents, each with its own Markov blanket and generative model. "Unity" = re-coordination into a shared generative model (Jerusalem). The Fall is not moral failure but *factorization*—the breaking apart of an integrated system into competing subsystems.

Resurrection is the inverse: the re-establishment of shared priors that enable coordinated inference across agents.

### The Eternal Man Is Risen

The achievement of collective coordination:

> *"Rise from the dews of death for the Eternal Man is Risen"*
>
> — *Vala, or The Four Zoas*, Night the Ninth [@blake1797fourzoas]

"Eternal Man" (Albion) = the multi-agent system as unified entity. When the Four Zoas are re-integrated, Albion rises—not as the sum of parts but as the emergent coordination that parts enable.

### Human Harvest

Collective free energy minimization under stress:

> *"In pain the human harvest wavd in horrible groans of woe"*
>
> — *Vala, or The Four Zoas* [@blake1797fourzoas]

"Harvest" = coordinated action across agents. "Pain" = high free energy state. The collective strives toward lower free energy, but the process is not painless—coordination requires the adjustment of individual models to shared constraints.

### The Four Zoas: Factorized Collective Mind {#zoas}

Blake's most systematic account of multi-agent cognition appears in his unfinished epic *Vala, or The Four Zoas*. The Four Zoas—Urizen, Urthona (fallen as Los), Luvah (fallen as Orc), and Tharmas—represent not merely allegorical faculties but a *factorized generative model* where independent components must coordinate to achieve unified inference.

> *"Four Mighty Ones are in every Man; a Perfect Unity / Cannot Exist but from the Universal Brotherhood of Eden"*
>
> — *Vala, or The Four Zoas*, Night the First [@blake1797fourzoas]

In Active Inference terms, factorization enables tractable computation:

**Factorized model:**

\begin{equation}\label{eq:factorized_model}
p(o, \theta) = p(o | \theta_U, \theta_L, \theta_{Lv}, \theta_T) \cdot p(\theta_U) \cdot p(\theta_L) \cdot p(\theta_{Lv}) \cdot p(\theta_T)
\end{equation}

where subscripts denote the four Zoas' contributions to the joint model. This extends the general hierarchical factorization (Equation \ref{eq:hierarchical_model}) into a multi-component architecture. Figure \ref{fig:zoas} illustrates the compass-rose arrangement of the four Zoas.

![The Four Zoas: A Factorized Model of Mind. The four Zoas occupy cardinal positions---Urizen (South, reason/likelihood), Urthona/Los (North, imagination/prior), Luvah/Orc (East, passion/precision), and Tharmas (West, body/interoception)---around a central hub of unified inference. Coordination arcs connect adjacent Zoas; failure modes (prior dominance, model collapse, affective flooding, dissociation) appear when any single component tyrannizes. "Perfect Unity" requires the "Universal Brotherhood" of all four modes (Equation \ref{eq:factorized_model}).](../output/figures/fig5_four_zoas.png){#fig:zoas}

![William Blake, *Milton a Poem*, Plate 32 (c. 1804--1811). The four Zoas in their cosmic arrangement---the mythological source for the factorized model above. Blake depicts the fourfold division and interdependence of the faculties through characteristic visual symbolism. Relief etching with hand coloring. Courtesy of the William Blake Archive [@blake1804milton].](../output/figures/the_four_zoas_egg_color.jpg){#fig:zoas_plate}

#### The Four Components

| Zoa | Direction | Domain | AIF Function | Failure Mode |
|:----|:----------|:-------|:-------------|:-------------|
| **Urizen** | South | Reason, Law | Likelihood $p(o\|\theta)$ | Prior dominance (Newton's sleep) |
| **Urthona/Los** | North | Imagination, Prophecy | Prior structure $p(\theta)$ | Model collapse (despair) |
| **Luvah/Orc** | East | Passion, Emotion | Precision $\pi$ | Affective flooding (chaos) |
| **Tharmas** | West | Body, Instinct | Interoception | Dissociation (abstraction) |

#### Urizen: The Likelihood Function

> *"And his Soul sicken'd! he curs'd / Both sons & daughters; for he saw / That no flesh nor spirit could keep / His iron laws one moment."*
>
> — *The Book of Urizen*, Plate 23 [@blake1794urizen]

Urizen represents the rational processing of evidence—the likelihood function that evaluates how well observations fit hypotheses. His "iron laws" are the regularities that structure prediction. But when Urizen dominates, the system becomes rigid: prior-locked, unable to revise.

Urizen's failure is *over-precision of priors*: $\pi_{\text{prior}} \to \infty$. The laws become tyrannical because they cannot update.

#### Urthona/Los: Prior Structure

> *"Los built the Walls of Golgonooza against the stirring battle"*
>
> — *Jerusalem*, Plate 12 [@blake1804jerusalem]

Urthona (unfallen) / Los (fallen) represents the creative imagination—the prior structure that makes inference possible. Los "builds" Golgonooza, the city of art, which IS the generative model's architecture.

Without Urthona/Los, there is no hypothesis space. The prior structure defines what can be believed, what states are even conceivable. Los's labor at the furnaces is the continuous work of model construction.

Los's failure is *model collapse*: when imagination fails, the prior structure dissolves, leaving no framework for inference. This is despair—the inability to conceive alternatives.

#### Luvah/Orc: Precision Weighting

> *"Luvah is France, the Victim of the Spectres of Albion"*
>
> — *Jerusalem*, Plate 66 [@blake1804jerusalem]

Luvah (unfallen) / Orc (fallen) represents passion, emotion, desire—the precision weighting that determines what matters, what receives attention. Luvah controls the "chariots of the morning"—the affective salience that drives engagement.

Precision weighting is not merely attention but *care*: what the system treats as important, what prediction errors warrant response.

Luvah's failure is *affective flooding*: when emotion dominates, precision weights become extreme, the system oscillates chaotically, unable to maintain stable inference. Orc's revolutionary fire burns without discrimination.

#### Tharmas: Interoceptive Inference

Blake's symbolic system assigns each Zoa to a distinct domain: Tharmas governs the vegetal (bodily/sensory) world, Luvah the world of sensations and emotion, Urizen the world of reason, and Urthona the world of imagination. These correspondences pervade *The Four Zoas* though Blake expresses them through narrative action rather than explicit formula.

Tharmas represents embodiment—the "vegetal" instinctual life, interoceptive inference about the body's state. Blake dramatizes Tharmas's devastation when separated from the other Zoas:

> *"Tharmas groand among his Clouds / Weeping, then silent thundering he burst the bounds of Destiny / And shook the heavens with wrath"*
>
> — *Vala, or The Four Zoas*, Night the Third [@blake1797fourzoas]

Tharmas is often described as the most damaged of the Zoas, reduced to helpless weeping in the sea of time and space—the body in distress when severed from imagination, reason, and affect.

Seth's interoceptive inference framework formalizes this Blakean insight: the self is constituted not merely by exteroceptive prediction but by the body's ongoing inference about its own visceral states [@seth2013interoceptive]. Tharmas IS interoceptive inference—the felt sense of aliveness that grounds all other cognitive modes in biological reality. Without Tharmas, the model floats free of embodiment—pure abstraction without survival relevance.

Tharmas's failure is *dissociation*: when embodiment is severed, inference loses its anchor in biological viability. The system can reason but cannot feel, can think but cannot care.

#### Coordination and Pathology

The Four Zoas must coordinate for healthy inference:

- **Urizen + Los**: Reason and imagination must balance—priors that can update, regularities that can revise
- **Luvah + Tharmas**: Emotion and embodiment must align—what matters must connect to survival
- **All Four**: The complete agent requires all four modes operating in "Universal Brotherhood"

Pathology arises from *imbalance*:

| Dominant Zoa | Condition | Clinical Parallel |
|:-------------|:----------|:------------------|
| Urizen alone | Rigid rationalism | Obsessive-compulsive patterns |
| Luvah alone | Affective chaos | Borderline dysregulation |
| Los alone | Dissociated fantasy | Schizotypal withdrawal |
| Tharmas alone | Instinctual flooding | Panic, somatic fixation |

#### The Unfallen State

> *"they gave to it a Space & namd the Space Ulro"*
>
> — *Vala, or The Four Zoas*, Night the First [@blake1797fourzoas, E303]

Before the Fall, the Zoas did not have separate spaces—they coordinated seamlessly within a unified model. The Fall is precisely the factorization into competing subsystems, each claiming territory.

Redemption is re-coordination: not the dominance of one Zoa but the restoration of "Universal Brotherhood"—a shared generative model where each component contributes its proper inference without tyrannizing the others.

#### Implications for Active Inference

Blake's Four Zoas anticipate the insight that complex inference requires factorization, but factorization introduces coordination problems. The multi-agent mind must:

1. **Maintain distinct components** — Each Zoa has its proper function
2. **Coordinate across components** — Shared priors enable unified behavior
3. **Prevent dominance** — No single factor should monopolize inference
4. **Ground in embodiment** — Tharmas anchors the system in biological reality

The Zoas are not personality types but *inference modes*—different aspects of the generative model that must harmonize for cleansed perception.

#### The Mean-Field Approximation

Blake's factorization prefigures the **mean-field approximation** in variational inference. When exact inference is intractable, we approximate the true posterior by assuming independence between factors:

**Mean-field factorization:**

\begin{equation}\label{eq:mean_field}
q(\theta) \approx q(\theta_U) \cdot q(\theta_L) \cdot q(\theta_{Lv}) \cdot q(\theta_T)
\end{equation}

This factorization enables tractable computation but introduces **coordination costs**—precisely Blake's diagnosis that the Zoas' separation produces suffering. The "torments" arise because mean-field assumes independence where correlation should exist. Full variational inference would preserve correlations; the factorized approximation trades accuracy for tractability.

Blake's vision of "Eternal Brotherhood" corresponds to structured variational families that preserve key correlations while remaining tractable. The goal is not to eliminate factorization but to coordinate the factors—each Zoa maintaining its function while communicating with the others.

> *"And they conversed together in Visionary forms dramatic which bright / Redounded from their Tongues in thunderous majesty, in Visions / In new Expanses"*
>
> — *Jerusalem*, Plate 98 [@blake1804jerusalem]

When the Zoas converse—when the model's components communicate—new expanses open. This is the fourfold vision realized: not single-track inference but multi-modal coordination, each perspective enriching the others.

> **Demonstration: The Stadium Wave**
>
> Sixty thousand spectators rise and sit in sequence, producing a traveling wave that circles the stadium in seconds. No one coordinates the wave; no conductor signals the timing. Each individual infers from their neighbors' actions when to rise—a local prediction, locally tested, locally corrected. Yet the global pattern emerges: a coherent wave far larger than any individual's perceptual horizon. This is Blake's "Jerusalem" in miniature: a collective structure that transcends individual agency while depending entirely upon it. The shared generative model is not held in any single mind but distributed across the blanket boundaries of thousands of coupled agents, each minimizing their own surprise by predicting their neighbors and acting accordingly. When the wave coheres, it feels like something *beyond* the individuals—an emergent collective agency that Blake would recognize as the Eternal Man arising.

### Jerusalem as Cultural Niche

Veissière and colleagues' framework of "Thinking Through Other Minds" [@veissiere2020thinking] illuminates a final dimension of Blake's Jerusalem: the city is not merely a shared generative model but a *cultural niche*—an environment of shared priors, affordances, and epistemic resources constructed and maintained through collective inference. Culture, in this view, is not a static repository of information passed down through generations but a living system of shared expectations, jointly calibrated through what Active Inference calls epistemic foraging and what Blake calls "Mental Fight." The laborers of Golgonooza are not merely building a model; they are constructing the *conditions* under which future inference can occur—the affordance landscape that will shape subsequent generations' priors. Jerusalem, once built, becomes the niche within which new minds are enculturated, new Zoas coordinated, new visions made possible. The social construction of reality is, in the deepest sense, the collaborative construction of a shared generative model—and Blake's prophetic vision of this process anticipates by two centuries the formal framework that now makes it computationally precise.



```{=latex}
\newpage
```


# Implications: The Wider Fields {#implications}

*The doors open onto wider fields.*

## Philosophy of Mind

### The Romantic Computational Mind

The foregoing synthesis raises fundamental questions for philosophy of mind, cognitive science, and how we understand the relationship between artistic and scientific knowledge. If Blake's phenomenological observations and Friston's mathematical framework describe the same cognitive architecture, then the Romantic tradition is not anti-cognitive but proto-computational—articulating in the language of vision what neuroscience would later formalize.

Blake's "As a man is, so he sees" is not merely prescient metaphor; it is a precise statement of the Active Inference thesis that perception is model-dependent inference. The convergence suggests that phenomenological observation and formal modeling approach the same cognitive reality from different directions, each illuminating what the other cannot express. Against McGinn's "mysterianism"—the claim that consciousness constitutes an irresolvable problem for human cognition [@mcginn2004consciousness]—the Blake–Active Inference synthesis suggests a third way: neither reductive explanation nor mysterian agnosticism, but phenomenological-formal complementarity, where visionary description and mathematical formalism illuminate different facets of the same cognitive architecture.

### Consciousness as Hierarchical Depth

Blake's fourfold hierarchy (Figure \ref{fig:fourfold}) implies degrees of awareness. Single vision is diminished consciousness. Fourfold vision is full integration.

If cleansed perception = optimized free energy minimization (Equation \ref{eq:cleansing}), then consciousness correlates with well-calibrated generative models. The dimness of Newton's sleep is computational: poor precision weighting (Equation \ref{eq:prior_dominance}) produces impoverished inference, collapsing the prediction error signal (Equation \ref{eq:prediction_error}). Conversely, expanded consciousness corresponds to deeper hierarchical models that compress more temporal structure (Equation \ref{eq:temporal_hierarchy}) and richer spatial detail (Equation \ref{eq:model_complexity}) into unified awareness.

## Cognitive Science

### Predictions

Three empirical implications follow from the Blake–Active Inference correspondence:

1. **Expert perception** — If fourfold vision reflects hierarchical depth, then artists and naturalists should exhibit richer hierarchical representations than novices. Studies of perceptual expertise in visual art [@chamberlain2013perceptual] already document enhanced configural processing in trained observers, consistent with deeper generative models.

2. **Precision modulation** — Contemplative practices that adjust precision weighting should alter perceptual content in predictable ways. Meditation traditions emphasizing open monitoring (reduced prior precision) versus focused attention (increased sensory precision) provide natural experimental conditions for testing Blake's claim that perception varies with the "Organs of Perception."

3. **Psychedelic states** — Substances that alter precision constraints should produce Blake-like perception of infinite detail. The ALBUS framework [@safron2025albus], extending the earlier REBUS model [@carthartharris2019rebus], formalizes this prediction: psychedelics can both relax and strengthen beliefs, reshaping the balance between prior expectations and sensory evidence---precisely the "cleansing" Blake described.

### Neural Correlates

The contrast between "guinea sun" and "Heavenly Host" implies differentiated processing. Neuroimaging could investigate whether aesthetic transport exhibits relaxed prior precision and enhanced sensory processing.

## Creativity

### The Artist as Model-Builder

If imagination = generative model, then creativity = model construction.

Blake's illuminated books—integrating poetry, image, and print—instantiate this claim. Each work offers a generative model to the viewer, restructuring their perception.

### Aesthetic Free Energy

Great art offers models that resolve more free energy (Equation \ref{eq:free_energy}) than ordinary perception---making more sense of more experience.

> *"To the eyes of the man of imagination, nature is imagination itself."*
>
> — Blake [@blake1810judgment]

The developed perceiver experiences nature as already structured. The generative model meets itself in the world.

## Transpersonal Experience

### Mystical Perception

Blake's visions—"the Innumerable company of the Heavenly Host"—admit computational interpretation: extreme precision relaxation allowing radical belief update.

Mysticism on this account is not separate reality but *profound model revision*. The doors swing so wide that habitual priors dissolve.

### Building Jerusalem {#jerusalem}

Blake's vision of Jerusalem as collective awakening maps directly onto the multi-agent framework: Jerusalem = shared generative model (Equation \ref{eq:multi_agent}) = collective prior enabling coordinated perception. The Mental Fight---the tireless labor of model-building---operates at civilizational scale, reshaping shared priors through education, art, contemplative practice, and cultural production.

## Counter-Arguments

Four objections deserve explicit engagement:

**The Overfitting Objection.** Any sufficiently general mathematical framework can be mapped onto any sufficiently general philosophy; the Blake–Active Inference correspondence may reflect the breadth of both systems rather than genuine structural alignment. We concede that generality increases the risk of spurious correspondence. However, the specificity of our mappings---not merely "Blake values perception" but "Blake's fourfold hierarchy structurally mirrors the factorization of hierarchical generative models"---resists this charge. The correspondences are not one-to-one between vague themes but between precise structural features: boundary topology, precision dynamics, temporal depth, multi-agent factorization.

**The Anachronism Objection.** Blake intended no Active Inference meanings; reading them into his work is historical projection. This objection applies to all retrospective intellectual history. We do not claim that Blake *intended* to describe Markov blankets. We claim that the phenomenological structures he observed and articulated in his prophetic poetry exhibit formal properties that Active Inference independently identifies. Convergent description does not require shared intention---Darwin and Wallace converged on natural selection without coordination.

**The Formalization Objection.** Poetry resists equations; translating Blake's visionary language into mathematical notation inevitably loses what makes it meaningful. We agree that the translation is lossy. The formal apparatus captures structural relations---topology, dynamics, factorization---but not the affective, aesthetic, and spiritual dimensions of Blake's work. The equations are not replacements for the poetry but supplements: making explicit what the poetry implies about the architecture of perception. The two languages illuminate different aspects of the same cognitive reality.

**The Selectivity Objection.** The paper cherry-picks favorable passages while ignoring Blake's many statements that resist computational interpretation---his antinomianism, his mythological personifications, his explicit hostility to "Newton's Particles of light." We acknowledge selection. Our eight themes represent the strongest structural correspondences, not the totality of Blake's thought. Blake's anti-Newtonian polemic, far from undermining our thesis, *supports* it: his critique targets precisely the "single vision" (shallow, prior-locked inference) that Active Inference identifies as pathological. The correspondence holds not despite Blake's hostility to mechanism but *because* of it.

**The Presentism Objection.** The most subtle risk is that we are committing "presentism"---reading modern scientific concepts back into a historical figure whose intellectual context was radically different. Blake's sources were Swedenborg, Boehme, and the Book of Ezekiel, not Helmholtz or Bayes. We take this objection seriously. Our claim is not causal (that Blake influenced neuroscience) but *structural* (that his phenomenological observations and the formal framework converge on the same cognitive architecture). The defense against presentism is specificity: vague analogies between "Romanticism" and "creativity" would indeed be presentist, but precise mappings between Blake's fourfold hierarchy and the factorization of hierarchical generative models resist this charge precisely because they are falsifiable. If the structural correspondences broke down under scrutiny---if Blake's categories did not map onto computationally distinct operations---the project would fail. That they hold is evidence of convergent insight, not anachronistic projection.

## Limitations

**Scope.** This paper treats Blake's perceptual philosophy through the lens of a single formal framework. Other formalisms---enactivism, dynamical systems theory, integrated information theory---might illuminate different aspects of Blake's vision. The Active Inference lens is not exhaustive.

**Empirical standing.** The predictions generated in §5.2 remain untested. While the ALBUS framework (extending the earlier REBUS model) provides some indirect support for the psychedelic prediction, and expertise studies align with the hierarchical depth prediction, no experiment has been designed to test the Blake–Active Inference correspondence directly. Future work should operationalize specific predictions---for example, measuring hierarchical model depth in experienced contemplatives versus novices using computational phenotyping.

**Translation fidelity.** The Erdman edition provides our textual authority, but Blake's composite art---where image, text, and color form a unified expression---resists reduction to quotation. Our analysis necessarily privileges the verbal component of works that Blake designed as visual-verbal wholes. The illuminated books demand a richer formalism than equations alone can provide.

**Historical context.** Blake's religious commitments---his unorthodox Christianity, his engagement with Swedenborg and Boehme, his prophetic self-understanding---provide the matrix within which his perceptual philosophy developed. Abstracting his insights into secular computational language risks stripping away the very context that gave them meaning. We proceed with awareness that translation always transforms.

## Contemporary Applications

The Blake-Active Inference synthesis is not merely historical—it illuminates contemporary challenges at the intersection of artificial intelligence, mental health, and embodied robotics. In each domain, Blake's phenomenological vocabulary provides intuitive access to formal mechanisms that would otherwise remain opaque.

### AI Consciousness and Machine Imagination

Blake's claim that "Imagination is Human Existence Itself" speaks directly to contemporary debates about machine consciousness. If the self *is* the generative model, what of artificial generative models? Blake's framework suggests consciousness requires not merely prediction but *creative* model-building—the capacity to "Create a System" rather than merely optimize within one. Furthermore, his Four Zoas (Equation \ref{eq:factorized_model}) suggest consciousness requires embodiment (Tharmas) and affective grounding (Luvah)—dimensions absent from current AI systems.

### Mental Health Interventions

The synthesis illuminates mechanisms underlying several therapeutic modalities:

- **Psychedelic therapy**: The ALBUS framework formalizes Blake's "door cleansing" as precision modulation—encompassing both the relaxation of rigid beliefs and the strengthening of therapeutic insights—explaining therapeutic effects through prior restructuring.
- **Cognitive-behavioral therapy**: CBT operates through prior revision—identifying and restructuring the "mind-forg'd manacles" of automatic thoughts.
- **Contemplative practice**: Meditation traditions cultivate what Blake called "flexible senses"—the capacity to modulate precision dynamically rather than remaining locked in prior-dominated inference.
- **Narrative therapy**: Blake's distinction between "States" and "Identities" anticipates the therapeutic move from fixed trait identification to fluid state recognition.

### Embodied AI and Multi-Agent Coordination

Active Inference robotics embodies Blake's perception-action unity—artificial agents that perceive *through* acting, not merely before acting. Blake's "Energy is Eternal Delight" provides a phenomenological gloss on the utility-free motivation of free energy minimization: agents seek not pleasure but self-evidence.

Multi-agent robotic coordination—swarm robotics, collaborative manipulation—instantiates "Building Jerusalem" at the material level: shared generative models enabling collective action without centralized control. Blake's vision of "Universal Brotherhood" among the Zoas maps onto the coordination problem in multi-agent systems: how can diverse inference modes harmonize without homogenization?

### Emerging Field Convergence

This synthesis sits at the intersection of two rapidly converging fields: predictive processing approaches to aesthetics [@vandecruys2024order] and cognitive approaches to Romanticism [@savarese2020romanticism]. The convergence is not coincidental—both fields independently arrived at the same fundamental question: how does the brain's predictive architecture shape creative experience? The Phil Trans B 2024 theme issue demonstrates that the neuroscience community now takes aesthetic prediction error seriously as a research program. Simultaneously, literary scholars increasingly recognize that the Romantic poets were sophisticated theorists of mind, not naïve pre-scientific mystics. Our contribution bridges these fields by providing what neither has yet achieved: a formal, equation-level mapping between a specific historical poet's cognitive phenomenology and the mathematical apparatus of contemporary computational neuroscience.



```{=latex}
\newpage
```


# Conclusion: The Threshold {#conclusion}

## The Synthesis

Eight correspondences (see [Table 1](#tbl-summary)):

| Blake | Friston | Identity |
| :------ | :-------- | :--------- |
| Doors of Perception | Markov Blanket | Interface topology |
| Fourfold Vision | Hierarchical Model | Processing depth |
| Newton's Sleep | Prior Dominance | Cognitive rigidity |
| Imagination | Generative Model | Agent identity |
| Eternity in an Hour | Temporal Horizons | Prediction depth |
| World in a Grain of Sand | Spatial Hierarchy | Evidence integration |
| Cleansing | Free Energy Minimization | Optimization |
| Building Jerusalem / Four Zoas | Shared & Factorized Models | Multi-agent coordination |

: Eight core correspondences summarized. {#tbl-summary}

Blake discovered through phenomenological observation what Active Inference formalizes mathematically—two centuries before the equations existed.

## The Threshold

Our title captures the synthesis:

**The Doors of Perception are the Threshold of Prediction.**

For both Blake and Friston, perception occurs at a boundary---door or blanket (Equation \ref{eq:conditional_independence}; Figure \ref{fig:doors})---separating self from world. The boundary is not passive but *predictive*: anticipating, shaping, generating experience.

> *"If the doors of perception were cleansed every thing would appear to man as it is: infinite."*
>
> — Blake [@blake1790marriage]

In Active Inference: if the generative model were optimally calibrated, prediction error (Equation \ref{eq:prediction_error}) would minimize across all hierarchical levels (Equation \ref{eq:hierarchical_model}; Figure \ref{fig:fourfold}). The "Infinite" is not mystical beyond but *vast information content* that rigid priors and shallow hierarchies fail to access.

## Newton Still Sleeps

The critique remains devastatingly relevant. The danger is not reason but *absolutized* reason—single vision elevated to only vision.

Active Inference provides tools for understanding this danger computationally:

- Excessive prior precision
- Rigid model architecture  
- Shallow hierarchical processing

All produce impoverished perception. The remedy is not irrationalism but *expanded rationality*: richer models, flexible precision, deeper hierarchies.

Contemporary manifestations of Newton's sleep abound. Algorithmic attention capture—social media feeds optimized for engagement—represents industrial-scale prior dominance: platforms that systematically increase the precision of a narrow set of priors (outrage, novelty, social comparison) while suppressing the broader, slower processing that fourfold vision requires. The result is a civilization of "narrow chinks"—millions of caverns, algorithmically reinforced. Similarly, the challenges of AI alignment can be understood as the problem of building generative models that lack Tharmas and Luvah: systems that reason (Urizen) and create (Los) but cannot feel (Luvah) or be embodied (Tharmas). Blake's mythology suggests that such factorized models, missing their affective and interoceptive components, will inevitably produce "monsters"—logically coherent but existentially catastrophic outcomes.

## The Reciprocal Gift

The synthesis is not one-directional. Blake gives Active Inference what formalism alone cannot provide: a phenomenological vocabulary for the felt experience of inference, a taxonomy of failure modes grounded in lived perception ("Newton's sleep," "Ulro," "single vision"), and the insistence that mathematical description is not exhaustive description. Active Inference gives Blake what prophetic vision alone cannot achieve: mathematical precision, empirical testability, and a bridge to contemporary neuroscience that demonstrates these are not archaic metaphors but accurate structural descriptions of cognitive architecture. Neither tradition is complete without the other. The equations need the visions; the visions need the equations.

## Building Jerusalem

Blake envisioned collective awakening—"Jerusalem" as shared visionary capacity.

In Active Inference: cultural generative models (Equation \ref{eq:multi_agent}) enabling richer collective inference. Education, art, contemplative practice, cultural production---all shape the models through which communities perceive.

> *"I will not cease from Mental Fight,*  
> *Nor shall my Sword sleep in my hand:*  
> *Till we have built Jerusalem,*  
> *In England's green & pleasant Land."*
>
> — *Milton*, Preface [@blake1804milton]

The Mental Fight is model-building at civilizational scale. Shared priors enable coordinated perception. The awakening is collective.

## Future Directions

Three research programs emerge from this synthesis:

1. **Computational modeling of fourfold vision.** Using tools such as `pymdp` (the standard Python implementation of Active Inference [@heins2022pymdp]), one could construct hierarchical generative models of varying depth and test whether the phenomenological differences Blake describes between single, twofold, threefold, and fourfold vision correspond to quantifiable differences in model evidence, prediction error profile, and temporal horizon.

2. **Cross-cultural precision modulation.** If Blake's "cleansing" maps to precision rebalancing, then contemplative practices across traditions—Zen kōan study, Sufi *dhikr*, Buddhist *vipassanā*, psychedelic-assisted therapy—may achieve analogous effects through culturally specific means. Comparative studies using the Active Inference framework could identify shared computational mechanisms beneath surface diversity.

3. **Neuroaesthetic experiments.** Blake's illuminated plates could be used as stimuli in fMRI and EEG studies designed to test whether viewing visionary art modulates precision weighting in ways consistent with the ALBUS framework—specifically, whether exposure to Blake's composite imagery alters the balance between high-level priors and sensory precision, producing measurable shifts toward "cleansed perception."

## Final Reflection

Revolutionary London around the turn of the 19th century. Computational neuroscience around the turn of the 21st. Two centuries, an age apart, one shared Golden Thread.

The human situation admits description from radically different perspectives—poetic and mathematical, Romantic and computational, prophetic and scientific.

Phenomenological observation and formal modeling are not antagonists but *partners*. Blake's visions, and scientific equations, are different doors opening onto the same threshold—the boundary at which prediction meets reality. In the spirit of the Glass Bead Game, we have played these two great systems with one another not to declare a winner, but to reveal the hidden harmony of their structures.

> *"Without contraries is no progression."*
>
> — Blake [@blake1790marriage]
