# Discussion {#sec:discussion}

## Language as Constitutive of Scientific Practice

Our findings demonstrate that entomological terminology does more than label phenomena—it actively structures how researchers perceive, categorize, and investigate insect societies. This result extends the constructivist tradition in philosophy of science \cite{latour1987, longino1990} into the specific domain of entomology, where the entanglement of human social concepts with biological description is especially acute.

Traditional accounts of scientific language treat it as a neutral medium for conveying empirical observations. Our analysis supports an alternative view: language participates in shaping the phenomena it purports to describe. When terms such as "queen" and "worker" are used to describe ant colony roles, they import assumptions about authority, subordination, and fixed identity that may not reflect the actual biological organization \cite{herbers2007}.

Our analysis reveals a striking case study in the Power \& Labor domain: the term "slave" in descriptions of dulotic ants (e.g., *Polyergus* and *Formica sanguinea*). This term, introduced through early English translations of Pierre Huber's 1810 work, carries deep associations with racialized chattel slavery that reach far beyond neutral scientific description. More critically, it **stalled research into host resistance** for decades. By framing the relationship as "slavery" (implying total dominance and submission), the term obscured the evolutionary reality of a co-evolutionary arms race. Only recently have researchers begun to systematically investigate "slave rebellions" (host workers killing parasite brood), a phenomenon that the "slave" prior effectively rendered invisible. Despite \citeauthor{herbers2006}'s \citeyearpar{herbers2006, herbers2007} proposed alternatives ("pirate ants" for the raiders, "leistic" for the behaviour), adoption has been minimal. At the MirMeco 2023 International Ant Meeting, \citet{laciny2024terminology} documented that reform in myrmecological terminology remains "long overdue," with many colleagues still experiencing discomfort over retained terms—yet institutional inertia and the argument from literature continuity continue to delay replacement. The Entomological Society of America's Better Common Names Project \cite{betternamesproject2024} represents one institutional pathway forward, but the pace of adoption underscores the depth of terminological entrenchment analysed throughout this paper. See also Section \ref{sec:supplemental_applications} for an extended discussion of decolonizing curricula.

This constructive role of language operates at several levels.

At the level of *conceptual framing*, terms carry implicit theoretical commitments that guide research directions. Our framing analysis shows anthropomorphic framing at 67.3% prevalence across all domains, with hierarchical framing (45.8%) concentrating in Power/Labor and Individuality. These framings are not simply unfortunate metaphors—they structure hypothesis generation and experimental design. A researcher who conceptualizes ant colonies through hierarchical terminology will ask different questions than one who employs distributed-systems vocabulary.

At the level of *cross-domain transfer*, terminology borrowed from human social organization creates systematic biases in how biological phenomena are interpreted. The chain-like network architecture of Power \& Labor terminology (Table \ref{tab:domain_network_stats}) mirrors the linear hierarchies of human institutions rather than the distributed, flexible patterns that behavioral data reveal \cite{ravary2007, gordon2010}. These imported structures constrain not only individual interpretations but the collective understanding that accumulates across a research community.

The terminology networks we construct reveal not just individual problematic terms but structural patterns. The high clustering coefficient (0.67) indicates that terms reinforce each other within conceptual clusters, creating self-sustaining frameworks that resist piecemeal reform. This network-level effect connects to \citeauthor{foucault1972archaeology}'s \citeyearpar{foucault1972archaeology} analysis of how discursive formations constrain what can be said and thought within a field, and extends \citeauthor{lakoff1980metaphors}'s \citeyearpar{lakoff1980metaphors} demonstration of pervasive metaphorical reasoning into formal scientific discourse. Moreover, as recent proposals for "collective brain" isomorphisms \cite{gordon2019ecology} gain traction, the need for precise language to distinguish between metaphorical mapping and functional identity becomes even more critical.

## From Metaphor to Mechanism: An Active Inference Perspective

Viewing ant colonies through an Active Inference lens \cite{friston2010free, clark2013whatever} fundamentally reframes the relationship between language and scientific understanding. Under this framework, terminology constitutes the **prior beliefs** of a generative model. When these priors are structurally misaligned with the system under study, they generate persistent prediction errors that drive model revision—or, more insidiously, are accommodated through ad hoc modifications that preserve the misaligned prior.

The Active Inferants framework \citep{friedman2021active} makes this tension especially vivid. \citet{friedman2021active} demonstrate that ant colonies can be modeled as ensembles of active inference agents—each individual performing approximate Bayesian inference over local pheromone gradients—whose collective behavior emerges from stigmergic coupling without any centralized controller. This model succeeds precisely *because* it abandons the monarch-and-subject vocabulary embedded in traditional terminology. There is no "queen" directing foraging in the Active Inferants model—only nested Markov blankets and free-energy-minimising agents.

This perspective aligns with **Environment-Centric Active Inference (EC-AIF)** \cite{bruineberg2018general}, which defines an "individual" not by its skin but by its *niche*—the set of states it can statistically regulate. In EC-AIF, the "individual" ant and the "colony" superorganism are simply two different scales of niche construction. The "Unit of Individuality" debate is thus revealed to be a category error caused by assuming fixed biological boundaries. Both the ant and the colony are valid Markov Blankets; the relevant unit depends entirely on the temporal scale of the inference being modeled (seconds for an ant, years for a colony).

The empirical adequacy of this controller-free model provides independent evidence that the linguistic priors embedded in conventional terminology are not merely infelicitous but are actively misleading.

In the **Free Energy Principle** framework, biological systems maintain their integrity by minimizing variational free energy—essentially, by acting to fulfill the predictions of their generative models \cite{friston2013life}.

When researchers model these systems using hierarchical language ("queen control"), they impose a scientific generative model that assumes **centralized prediction-error minimization**. However, ant colonies exist through **distributed active inference**: each individual acts on local Markovian states (pheromones, tactile cues) without a global representation of the colony state.

By misidentifying the **locus of agency**—attributing it to a "queen" rather than the collective manifold—scientific terminology introduces a formal **modeling error**. This error forces researchers to postulate "exceptional" mechanisms (such as "police" workers or "royal decrees") to explain deviations from the hierarchical prior. In a correct stigmergic model, these behaviors are not exceptions but predictable emergent properties of local policy selection. Terminology reform, then, is a process of **model selection**: replacing high-entropy priors (anthropomorphism) with lower-entropy, mechanistically accurate descriptors.

## Comparison with Existing Approaches

Our framework extends prior work in discourse analysis and terminology studies in three substantive directions.

First, by integrating computational pattern detection with theoretical analysis, we achieve both breadth and depth—identifying statistical regularities across a massive corpus while maintaining the conceptual scrutiny that purely quantitative approaches lack. Existing computational approaches to scientific discourse \cite{chen2006citespace} primarily model citation networks rather than the semantic content of terminological usage. Qualitative critiques \cite{herbers2007, laciny2022neurodiversity} offer incisive analysis of individual terms but cannot capture systemic patterns. Our framework bridges this gap, supporting both SSK arguments about social construction of scientific facts \cite{latour1987} and feminist epistemological critiques of androcentric category projection \cite{haraway1991}.

Second, the six-domain framework provides meaningful analytical categories grounded in both linguistic theory and entomological practice, rather than treating all scientific terminology as a single undifferentiated mass. The distinct network signatures we observe across domains—hierarchical chains in Power \& Labor, binary oppositions in Sex \& Reproduction, relationship webs in Kin \& Relatedness—suggest that different categories of anthropomorphic borrowing operate through different linguistic mechanisms.

Third, the CACE meta-standards (Section \ref{sec:methodology}) offer a concrete evaluation framework that moves beyond critique toward constructive reform. Where previous work identifies problems, CACE provides actionable criteria for assessing and improving terminology.

## Practical Implications for Scientific Communication

### Terminology Awareness and Reform

Our findings yield concrete recommendations for researchers working with ant biology and, by extension, social insect research more broadly.

Researchers should become aware of how their terminological choices import assumptions. The high ambiguity scores we observed in Power \& Labor (0.81) and Kin \& Relatedness (0.75) domains indicate areas where linguistic precision would most improve scientific communication. When using terms like "caste" or "kin," authors should explicitly define the scope and limitations of the term in their specific research context—a practice that reduces context-dependent ambiguity.

Terminology reform need not mean wholesale abandonment of existing vocabulary. Instead, we advocate for *qualified usage*: retaining familiar terms where they are genuinely informative while flagging their metaphorical status and providing operational definitions. "Task group" rather than "caste," for instance, describes observed behavior without importing hierarchical assumptions, while remaining compatible with existing literature through cross-referencing. Recent community efforts such as the ESA Better Common Names Project \cite{betternamesproject2024} and \citeauthor{herbers2007}'s \citeyearpar{herbers2007} call for language reform provide models for systematic terminology revision.

### Cross-Domain Communication

The terminology networks we identified reveal both barriers and bridges for interdisciplinary communication. Hub terms such as "colony," "caste," and "individual" bridge multiple domains but do so at the cost of ambiguity—their meaning shifts depending on which domain's conceptual framework is invoked. Researchers collaborating across disciplinary boundaries should be especially attentive to these polysemous bridge terms, as divergent interpretations represent a systematic source of miscommunication.

Conversely, the strong domain clustering (clustering coefficient 0.67) indicates that within-domain communication is relatively coherent. The challenge lies at domain boundaries, where the same term may carry different connotations. Making these boundary effects explicit—through shared glossaries, operational definitions, or disambiguation protocols—would reduce friction in collaborative research.

## The "Slave" Terminology Debate: A Case Study in Reform

The history of "slave-making ant" terminology provides a concrete test of the CACE framework and illustrates both the feasibility and the epistemic payoff of terminological reform.

For over a century, species such as *Polyergus* and *Formica sanguinea* were described through a master–slave metaphor: raided brood were "slaves," raiding species were "slave-makers," and the behaviour itself was "slave-making" \cite{hölldobler1990}. \citet{herbers2006, herbers2007} catalysed reform by demonstrating that the terminology naturalized a human institution of extreme moral weight while simultaneously obscuring the biology. Evaluating "slave" through CACE makes the case transparent:

- **Clarity**: "Slave" conflates the social relationship (exploited labour under coercion) with the biological mechanism (brood parasitism and chemical manipulation of host behaviour). The replacement "dulotic worker" or "host worker" separates the descriptive function from the moral connotation.
- **Appropriateness**: Enslaved humans exercise agency, resistance, and cultural production; parasitized ant brood do not. The metaphor projects attributes absent from the target phenomenon.
- **Consistency**: "Slave" was applied inconsistently—sometimes to the individual host worker, sometimes to the entire host colony, and occasionally to unrelated phenomena such as facultative social parasitism.
- **Evolvability**: Modern understanding of superorganism-level immune responses and chemical mimicry \cite{wilson2008superorganism} renders the "slave" metaphor actively misleading, since the host workers' behaviour results from chemical deception rather than submission.

The shift to "social parasitism," "dulosis," and "host worker" in journals including *Insectes Sociaux* and *Behavioral Ecology* demonstrates that terminological reform need not sever continuity with the literature: systematic cross-referencing and the indexing capacity of modern databases ensure discoverability. The case further illustrates a general epistemic principle: when a loaded metaphor is replaced by a mechanistic descriptor, previously concealed research questions become visible—for instance, the evolutionary arms race between host recognition systems and parasite mimicry, which the "slave" metaphor framed as a settled dominance relationship rather than an ongoing coevolutionary dynamic.

Quantitative CACE scoring confirms this qualitative assessment. Computed scores for "slave" (Clarity: 0.40, Appropriateness: 0.40, Consistency: 0.38, Evolvability: 0.33, Aggregate: 0.38) fall well below the replacement "host worker" (Clarity: 0.85, Appropriateness: 1.00, Consistency: 0.72, Evolvability: 0.67, Aggregate: 0.81). The largest improvement occurs in Appropriateness (+0.60), where removing the anthropomorphic term eliminates the entire penalty, followed by Clarity (+0.45), where reduced semantic entropy reflects the unambiguous functional description. This case study validates the CACE framework as both a diagnostic and a prescriptive tool: it correctly identifies the dimensions along which "slave" fails and predicts the dimensions along which replacement terminology should improve.

## Limitations

Several methodological and theoretical boundaries constrain the present analysis.

1. **Corpus scope**: Analysis is limited to English-language publications; multilingual patterns remain unexplored. Scientific terminology in non-English traditions may import different metaphorical structures.
2. **Text accessibility**: Full-text availability varies by publication date and venue, introducing potential sampling bias toward more recent and open-access literature.
3. **Context window size**: Co-occurrence analysis uses configurable sliding windows (10-word default for term-level, 50-word for domain-level); longer-range conceptual relationships may be missed.
4. **Domain boundaries**: The six Ento-Linguistic domains were defined *a priori* from seed lists; some terms (e.g., "colony") span multiple domains, creating classification challenges. Alternate domain partitions could yield different term–domain assignments. Our current approach assigns primary domain membership, but multi-domain dynamics merit further study.
5. **Historical depth**: Cross-sectional analysis does not fully capture the temporal evolution of terminological usage, though our case studies (Section \ref{sec:supplemental_results}) offer preliminary longitudinal evidence.
6. **Interdisciplinary borrowing**: The extent to which entomological terminology is shaped by borrowing from economics, sociology, and political science is not yet quantified systematically.
7. **Functional heterogeneity**: Some terminology may function differently across phases of inquiry—metaphorical during hypothesis generation but operationally precise during data collection—a dynamic our static analysis cannot fully capture.

## Future Directions

The framework opens several research avenues. Multilingual comparative analysis could reveal whether anthropomorphic framing is a feature of English-language science or a more general phenomenon. Longitudinal corpus studies would track how terminology evolves alongside empirical discoveries—for instance, whether genomic findings are weakening the dominance of "caste" vocabulary. Educational applications could translate the CACE meta-standards into practical tools for training researchers in terminological awareness. These directions are developed further in Section \ref{sec:conclusion}.
