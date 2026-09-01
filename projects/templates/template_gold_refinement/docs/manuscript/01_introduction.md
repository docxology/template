# {{TITLE_INTRODUCTION}} {#sec:introduction}

Gold refining is one of humanity's oldest purification technologies. The pre-1800 record is not a single modern pipeline, but it gives the analogy a real source domain: Pliny's Book XXXIII treats metals, gold extraction, and touchstone testing as recognizable ancient practices; Biringuccio's *De la Pirotechnia* and Agricola's *De re metallica* turn mining, smelting, cupellation, assaying, and parting into printed technical sequences; Cramer's assay manual codifies the theory/practice split of metal testing [@pliny_natural_history_33; @biringuccio_pirotechnia_1540; @agricola_de_re_metallica_1556; @cramer_assaying_metals_1741]. Hallmarking regimes make the verification layer socially and legally visible: a seventeenth-century manual for goldsmiths frames "true standard allay," statutes, weights, and counterfeit coin detection as public controls, while the Goldsmiths' Company Assay Office traces the London leopard's-head mark, maker's mark, and date-letter system through pre-1800 milestones [@badcock_touchstone_1678; @goldsmiths_hallmarking_history]. This paper asks: can that historically plural pipeline serve as a **load-bearing** operational model for scientific manuscript composition - not merely a decorative analogy, but a real mapping from metallurgical stages to template-infrastructure operations?

We operationalize that question through three narrower research questions. **RQ1:** Can each analogical stage be bound to an ordered executable transformation with a source owner and failure condition? **RQ2:** Can prose choices, claims, equations, and figures be regenerated with inspectable provenance? **RQ3:** Can the workflow state its stopping boundary clearly enough that local certification is not mistaken for domain truth, historical authority, or security compliance? The paper answers these questions by constructing and validating one exemplar; it does not compare writing interventions or estimate effects on readers.

## The problem

A scientific manuscript accumulates impurities through its drafting lifecycle: unsupported claims, unresolved references, redundant prose, and citation gaps. The template repository provides infrastructure to detect and remove these impurities - validation gates, cross-reference checks, evidence registries, and coverage enforcement. This aligns with a broader reproducible-research literature that treats code, data, environment, and provenance as first-class scientific materials [@buckheit_donoho_1995; @peng2011reproducible; @stodden2011default; @sandve2013ten]. What this exemplar adds is a unifying model that names the purification stages and measures local purity progression.

This exemplar treats {{INTRO_INTEGRITY_TERM_1}} and {{INTRO_INTEGRITY_TERM_2}} as first-class manuscript objects. A claim is not considered refined because it sounds plausible; it is refined when its source path, generated variable, figure label, citation key, and validation gate can all be inspected. That is a narrower claim than empirical truth: reproducibility can set a minimum computational standard without replacing independent replication, domain expertise, or peer review [@peng2011reproducible; @ioannidis2005false].

## The analogy as pipeline

We map five gold-refining stages onto manuscript operations:

{{REFINERY_STAGE_LABELS}}

Each stage has a metallurgical operation, a manuscript operation, an input purity, and an output purity. Purity increases monotonically, stage order is sequential, and each stage input must equal the preceding output. These invariants are enforced by `src/refinery.py::run_refinery` and `src/purity.py::assert_monotone_increase` and exercised by positive and negative tests. `stages_to_target()` supplies the inverse query: given a target, return the shortest valid prefix rather than selecting later stages out of order.

## Mega-madlib token engine

The manuscript's domain vocabulary is not hand-authored prose but config-owned lexical data, selected deterministically by a seeded SHA-256 digest. The engine generates {{TOKEN_COUNT}} tokens across {{CONFIG_NUM_SLOTS}} slots and {{CONFIG_NUM_LEXICON_CATEGORIES}} lexicon categories. Every token choice is reproducible, traceable to its config key, and bound to a manuscript section. In this respect the exemplar extends literate programming and dynamic statistical reporting: code, data, and prose are kept synchronized, but the prose-level choices are also made inspectable [@knuth1984literate; @leisch2002sweave; @marwick2018packaging].

The deeper token inventory is deliberately spread across the paper. Introduction tokens name the integrity frame; methods tokens bind {{METHOD_GATE_TERM_1}}, {{METHOD_GATE_TERM_2}}, and {{METHOD_GATE_TERM_3}} to source-owned operations; results tokens surface {{RESULTS_EVIDENCE_TERM_1}}, {{RESULTS_EVIDENCE_TERM_2}}, and {{RESULTS_EVIDENCE_TERM_3}}; discussion tokens mark the {{DISCUSSION_BOUNDARY_TERM_1}} and {{DISCUSSION_BOUNDARY_TERM_2}} where the analogy must stop.

## Implementation circuit

The metaphor becomes operational only when every transformation has an implementation owner. In this exemplar, configuration creates the ore, `src/refinery.py` defines the purity stages, `src/composition.py` turns slots into deterministic tokens, `src/formalisms.py` owns the equation registry, the `src/figures/` package turns those sources into registered visuals, and the template validators decide whether the hydrated manuscript can be treated as publication metal. The loop is deliberately closed: failures from the validators point back to source files, not to hand-polished output.

## Open question pinned

Is the analogy load-bearing or rhetorical? We assert it is **both**: it frames the methods paper (rhetorical) and operationalizes each stage against real infrastructure (load-bearing). Analogy theory gives the discipline for that claim: preserve relational structure, declare negative analogies, and do not transfer unsupported source-domain properties into the target domain [@gentner1983structure; @hesse1966models; @holyoak_thagard_1995]. The open question is not whether to use the analogy, but where the mapping breaks - a question the discussion addresses.
