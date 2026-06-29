# {{TITLE_INTRODUCTION}} {#sec:introduction}

Gold refining is one of humanity's oldest purification technologies. From ancient cupellation to modern nine-nines electrolysis, the process of separating noble metal from base ore has evolved into a rigorous, staged pipeline with measurable purity at every step. This paper asks: can that pipeline serve as a **load-bearing** operational model for scientific manuscript composition — not merely a decorative analogy, but a real mapping from metallurgical stages to template-infrastructure operations?

## The problem

A scientific manuscript accumulates impurities through its drafting lifecycle: unsupported claims, unresolved references, redundant prose, and citation gaps. The template repository provides infrastructure to detect and remove these impurities — validation gates, cross-reference checks, evidence registries, and coverage enforcement. What it lacks is a unifying model that names the purification stages and measures purity progression.

This exemplar treats {{INTRO_INTEGRITY_TERM_1}} and {{INTRO_INTEGRITY_TERM_2}} as first-class manuscript objects. A claim is not considered refined because it sounds plausible; it is refined when its source path, generated variable, figure label, citation key, and validation gate can all be inspected.

## The analogy as pipeline

We map five gold-refining stages onto manuscript operations:

{{REFINERY_STAGE_LABELS}}

Each stage has a metallurgical operation, a manuscript operation, an input purity, and an output purity. Purity increases monotonically — a constraint enforced by `src/purity.py::assert_monotone_increase` and tested in `tests/test_refinery.py`.

## Mega-madlib token engine

The manuscript's domain vocabulary is not hand-authored prose but config-owned lexical data, selected deterministically by a seeded SHA-256 digest. The engine generates {{TOKEN_COUNT}} tokens across {{CONFIG_NUM_SLOTS}} slots and {{CONFIG_NUM_LEXICON_CATEGORIES}} lexicon categories. Every token choice is reproducible, traceable to its config key, and bound to a manuscript section.

The deeper token inventory is deliberately spread across the paper. Introduction tokens name the integrity frame; methods tokens bind {{METHOD_GATE_TERM_1}}, {{METHOD_GATE_TERM_2}}, and {{METHOD_GATE_TERM_3}} to source-owned operations; results tokens surface {{RESULTS_EVIDENCE_TERM_1}}, {{RESULTS_EVIDENCE_TERM_2}}, and {{RESULTS_EVIDENCE_TERM_3}}; discussion tokens mark the {{DISCUSSION_BOUNDARY_TERM_1}} and {{DISCUSSION_BOUNDARY_TERM_2}} where the analogy must stop.

## Implementation circuit

The metaphor becomes operational only when every transformation has an implementation owner. In this exemplar, configuration creates the ore, `src/refinery.py` defines the purity stages, `src/composition.py` turns slots into deterministic tokens, `src/formalisms.py` owns the equation registry, the `src/figures/` package turns those sources into registered visuals, and the template validators decide whether the hydrated manuscript can be treated as publication metal. The loop is deliberately closed: failures from the validators point back to source files, not to hand-polished output.

## Open question pinned

Is the analogy load-bearing or rhetorical? We assert it is **both**: it frames the methods paper (rhetorical) and operationalizes each stage against real infrastructure (load-bearing). The open question is not whether to use the analogy, but where the mapping breaks — a question the discussion addresses.
