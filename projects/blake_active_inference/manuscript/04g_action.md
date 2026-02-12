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
