# Discussion {#sec:discussion}

## Language as Constitutive of Scientific Practice

Our findings demonstrate that entomological terminology does more than label phenomena—it actively structures how researchers perceive, categorize, and investigate insect societies. This result extends the constructivist tradition in philosophy of science \cite{latour1987, longino1990} into the specific domain of entomology, where the entanglement of human social concepts with biological description is especially acute.

Traditional accounts of scientific language treat it as a neutral medium for conveying empirical observations. Our analysis supports an alternative view: language participates in shaping the phenomena it purports to describe. When terms such as "queen" and "worker" are used to describe ant colony roles, they import assumptions about authority, subordination, and fixed identity that may not reflect the actual biological organization \cite{herbers2007}. This constructive role of language operates at several levels.

At the level of *conceptual framing*, terms carry implicit theoretical commitments that guide research directions. Our framing analysis shows anthropomorphic framing at 67.3% prevalence across all domains, with hierarchical framing (45.8%) concentrating in Power/Labor and Individuality. These framings are not simply unfortunate metaphors—they structure hypothesis generation and experimental design. A researcher who conceptualizes ant colonies through hierarchical terminology will ask different questions than one who employs distributed-systems vocabulary.

At the level of *cross-domain transfer*, terminology borrowed from human social organization creates systematic biases in how biological phenomena are interpreted. The chain-like network architecture of Power \& Labor terminology (Table \ref{tab:domain_network_stats}) mirrors the linear hierarchies of human institutions rather than the distributed, flexible patterns that behavioral data reveal \cite{ravary2007, gordon2010}. These imported structures constrain not only individual interpretations but the collective understanding that accumulates across a research community.

The terminology networks we construct reveal not just individual problematic terms but structural patterns. The high clustering coefficient (0.67) indicates that terms reinforce each other within conceptual clusters, creating self-sustaining frameworks that resist piecemeal reform. This network-level effect connects to Foucault's \cite{foucault1972archaeology} analysis of how discursive formations constrain what can be said and thought within a field, and extends Lakoff and Johnson's \cite{lakoff1980metaphors} demonstration of pervasive metaphorical reasoning into formal scientific discourse.

## Comparison with Existing Approaches

Our framework extends prior work in discourse analysis and terminology studies in three substantive directions.

First, by integrating computational pattern detection with theoretical analysis, we achieve both breadth and depth—identifying statistical regularities across a corpus while maintaining the conceptual scrutiny that purely quantitative approaches lack. Existing computational approaches to scientific discourse \cite{chen2006citespace} primarily model citation networks rather than the semantic content of terminological usage. Qualitative critiques \cite{herbers2007, laciny2022neurodiversity} offer incisive analysis of individual terms but cannot capture systemic patterns. Our framework bridges this gap, supporting both SSK arguments about social construction of scientific facts \cite{latour1987} and feminist epistemological critiques of androcentric category projection \cite{haraway1991}.

Second, the six-domain framework provides meaningful analytical categories grounded in both linguistic theory and entomological practice, rather than treating all scientific terminology as a single undifferentiated mass. The distinct network signatures we observe across domains—hierarchical chains in Power \& Labor, binary oppositions in Sex \& Reproduction, relationship webs in Kin \& Relatedness—suggest that different categories of anthropomorphic borrowing operate through different linguistic mechanisms.

Third, the CACE meta-standards (Section \ref{sec:methodology}) offer a concrete evaluation framework that moves beyond critique toward constructive reform. Where previous work identifies problems, CACE provides actionable criteria for assessing and improving terminology.

## Practical Implications for Scientific Communication

### Terminology Awareness and Reform

Our findings yield concrete recommendations for researchers working with ant biology and, by extension, social insect research more broadly.

Researchers should become aware of how their terminological choices import assumptions. The high ambiguity scores we observed in Power \& Labor (0.81) and Kin \& Relatedness (0.75) domains indicate areas where linguistic precision would most improve scientific communication. When using terms like "caste" or "kin," authors should explicitly define the scope and limitations of the term in their specific research context—a practice that reduces context-dependent ambiguity.

Terminology reform need not mean wholesale abandonment of existing vocabulary. Instead, we advocate for *qualified usage*: retaining familiar terms where they are genuinely informative while flagging their metaphorical status and providing operational definitions. "Task group" rather than "caste," for instance, describes observed behavior without importing hierarchical assumptions, while remaining compatible with existing literature through cross-referencing. Recent community efforts such as the ESA Better Common Names Project \cite{betternamesproject2024} and Herbers' \cite{herbers2007} call for language reform provide models for systematic terminology revision.

### Cross-Domain Communication

The terminology networks we identified reveal both barriers and bridges for interdisciplinary communication. Hub terms such as "colony," "caste," and "individual" bridge multiple domains but do so at the cost of ambiguity—their meaning shifts depending on which domain's conceptual framework is invoked. Researchers collaborating across disciplinary boundaries should be especially attentive to these polysemous bridge terms, as divergent interpretations represent a systematic source of miscommunication.

Conversely, the strong domain clustering (clustering coefficient 0.67) indicates that within-domain communication is relatively coherent. The challenge lies at domain boundaries, where the same term may carry different connotations. Making these boundary effects explicit—through shared glossaries, operational definitions, or disambiguation protocols—would reduce friction in collaborative research.

## The "Slave" Terminology Debate: A Case Study in Reform

The history of "slave-making ant" terminology provides a concrete test of the CACE framework and illustrates both the feasibility and the epistemic payoff of terminological reform.

For over a century, species such as *Polyergus* and *Formica sanguinea* were described through a master–slave metaphor: raided brood were "slaves," raiding species were "slave-makers," and the behaviour itself was "slave-making" \cite{hölldobler1990}. Herbers \cite{herbers2006, herbers2007} catalysed reform by demonstrating that the terminology naturalized a human institution of extreme moral weight while simultaneously obscuring the biology. Evaluating "slave" through CACE makes the case transparent:

- **Clarity**: "Slave" conflates the social relationship (exploited labour under coercion) with the biological mechanism (brood parasitism and chemical manipulation of host behaviour). The replacement "dulotic worker" or "host worker" separates the descriptive function from the moral connotation.
- **Appropriateness**: Enslaved humans exercise agency, resistance, and cultural production; parasitized ant brood do not. The metaphor projects attributes absent from the target phenomenon.
- **Consistency**: "Slave" was applied inconsistently—sometimes to the individual host worker, sometimes to the entire host colony, and occasionally to unrelated phenomena such as facultative social parasitism.
- **Evolvability**: Modern understanding of superorganism-level immune responses and chemical mimicry \cite{wilson2008superorganism} renders the "slave" metaphor actively misleading, since the host workers' behaviour results from chemical deception rather than submission.

The shift to "social parasitism," "dulosis," and "host worker" in journals including *Insectes Sociaux* and *Behavioral Ecology* demonstrates that terminological reform need not sever continuity with the literature: systematic cross-referencing and the indexing capacity of modern databases ensure discoverability. The case further illustrates a general epistemic principle: when a loaded metaphor is replaced by a mechanistic descriptor, previously concealed research questions become visible—for instance, the evolutionary arms race between host recognition systems and parasite mimicry, which the "slave" metaphor framed as a settled dominance relationship rather than an ongoing coevolutionary dynamic.

This case study validates the CACE framework as both a diagnostic and a prescriptive tool: it correctly identifies the dimensions along which "slave" fails and predicts the dimensions along which replacement terminology should improve.

## Limitations

Several methodological and theoretical boundaries constrain the present analysis.

1. **Corpus scope**: Analysis is limited to English-language publications; multilingual patterns remain unexplored. Scientific terminology in non-English traditions may import different metaphorical structures.
2. **Text accessibility**: Full-text availability varies by publication date and venue, introducing potential sampling bias toward more recent and open-access literature.
3. **Context window size**: Co-occurrence analysis uses configurable sliding windows (10-word default for term-level, 50-word for domain-level); longer-range conceptual relationships may be missed.
4. **Domain boundaries**: Some terms (e.g., "colony") span multiple domains, creating classification challenges. Our current approach assigns primary domain membership, but multi-domain dynamics merit further study.
5. **Historical depth**: Cross-sectional analysis does not fully capture the temporal evolution of terminological usage, though our case studies (Section \ref{sec:supplemental_results}) offer preliminary longitudinal evidence.
6. **Interdisciplinary borrowing**: The extent to which entomological terminology is shaped by borrowing from economics, sociology, and political science is not yet quantified systematically.

## Future Directions

The framework opens several research avenues. Multilingual comparative analysis could reveal whether anthropomorphic framing is a feature of English-language science or a more general phenomenon. Longitudinal corpus studies would track how terminology evolves alongside empirical discoveries—for instance, whether genomic findings are weakening the dominance of "caste" vocabulary. Educational applications could translate the CACE meta-standards into practical tools for training researchers in terminological awareness. These directions are developed further in Section \ref{sec:conclusion}.
