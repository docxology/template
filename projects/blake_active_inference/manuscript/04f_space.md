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
