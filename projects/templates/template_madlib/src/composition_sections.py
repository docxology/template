from __future__ import annotations

from composition_helpers import (
    _comma_join,
    _disabled_section_body,
    _phase_sentence,
    _protocol_sentence,
    _sentence_list,
)
from config import MadlibConfig, SECTION_KEYS
from tokens import TokenPlan


def build_imrad_sections(config: MadlibConfig, token_plan: TokenPlan) -> dict[str, str]:
    sections = {
        "ABSTRACT_BODY": _abstract(config, token_plan),
        "INTRODUCTION_BODY": _introduction(config, token_plan),
        "METHODS_BODY": _methods(config, token_plan),
        "RESULTS_BODY": _results(config, token_plan),
        "DISCUSSION_BODY": _discussion(config, token_plan),
        "CONFIGURATION_BODY": _configuration(config, token_plan),
        "EVALUATION_BODY": _evaluation(config, token_plan),
        "REPRODUCIBILITY_BODY": _reproducibility(config, token_plan),
        "LIMITATIONS_BODY": _limitations(config),
        "SCOPE_BODY": _scope(config),
        "AUTHORING_CONTRACT_BODY": _authoring_contract(config, token_plan),
    }
    for section in SECTION_KEYS:
        if not config.section_conditions.get(section, True):
            sections[f"{section.upper()}_BODY"] = _disabled_section_body(section)
    return sections


def section_title_variables(config: MadlibConfig) -> dict[str, str]:
    return {f"TITLE_{section.upper()}": title for section, title in config.section_titles.items()}


def _abstract(config: MadlibConfig, token_plan: TokenPlan) -> str:
    adjective = token_plan.first_value("adjectives", "configurable")
    noun = token_plan.first_value("nouns", "manuscript")
    verb = token_plan.first_value("verbs", "compose")
    moves = _sentence_list(config.narrative_moves["abstract"])
    return "\n\n".join(
        [
            (
                f"This exemplar asks whether a {adjective} {noun} can {verb} a complete IMRAD manuscript "
                "from configuration-owned lexical data while preserving an audit trail that remains readable "
                "before and after rendering. The project deliberately keeps playful Mad Lib mechanics inside "
                "a serious reproducibility contract: the manuscript shell names large placeholders, the config "
                "declares allowable language, and the source code decides what text is emitted."
            ),
            (
                f"The committed seed is `{config.seed}` and the current schema expands {len(config.slots)} slot "
                f"rule(s) into {len(token_plan.choices)} token choice(s) across {len(config.lexicon)} lexicon "
                f"categories. The configured narrative moves are {moves}. The central hypothesis is: "
                f"{config.hypothesis}"
            ),
            (
                "The result is not a claim that lexical substitution creates scholarship. It is a worked "
                "template for conditional manuscript assembly: section enablement, token provenance, figure "
                "registration, and unresolved-placeholder checks all become inspectable artifacts before the "
                "shared renderer produces PDF, HTML, and slides."
            ),
        ]
    )


def _introduction(config: MadlibConfig, token_plan: TokenPlan) -> str:
    nouns = _comma_join(token_plan.values_for_category("nouns")[:4]) or "tokens"
    verbs = _comma_join(token_plan.values_for_category("verbs")[:4]) or "generate"
    moves = _sentence_list(config.narrative_moves["introduction"])
    return "\n\n".join(
        [
            (
                "Mad Lib style generation is usually treated as a toy because it foregrounds the visible blank "
                "rather than the source of the replacement. In a research pipeline, the blank is not the hard "
                "part. The hard part is making every replacement reviewable, deterministic, and honest about "
                "what it can support. `template_madlib` turns that constraint into the subject of the exemplar."
            ),
            (
                f"The project treats nouns such as {nouns} and verbs such as {verbs} as versioned data. "
                "Changing a lexicon entry is therefore closer to changing an input table than editing prose in "
                "place. That distinction matters because the generated manuscript can be rerendered, diffed, "
                "and validated without asking the reader to trust an invisible drafting session."
            ),
            (
                f"The introduction is configured to {moves}. Those moves keep the manuscript from pretending "
                "to be an open-ended language model. It is a bounded template: authors declare categories, "
                "slots, section switches, method steps, and claim boundaries; source code transforms those "
                "declarations into manuscript bodies and evidence tables."
            ),
            (
                "This exemplar is useful for protocols, educational scaffolds, review forms, templated reports, "
                "and other documents where conditional text is unavoidable but should never become untraceable. "
                "The same pattern can be extended with domain-specific validators while leaving the shared "
                "rendering infrastructure untouched."
            ),
        ]
    )


def _methods(config: MadlibConfig, token_plan: TokenPlan) -> str:
    method = token_plan.first_value("methods", "deterministic hashing")
    constraint = token_plan.first_value("constraints", "source-owned configuration")
    moves = _sentence_list(config.narrative_moves["methods"])
    protocol = _protocol_sentence(config.method_protocol)
    phase_summary = _phase_sentence(config.pipeline_phases)
    principle_names = _comma_join(principle.name for principle in config.design_principles)
    explicit_count = len(config.explicit_paths)
    defaulted_count = len(config.defaulted_paths)
    slot_allocation = _comma_join(
        f"{section}: {count}" for section, count in sorted(token_plan.section_counts.items()) if count
    )
    visual_flags = _comma_join(config.visualizations.enabled_flags)
    quality_probes = _comma_join(probe.name for probe in config.quality_probes)
    failure_modes = _comma_join(mode.name for mode in config.failure_modes)
    obligations = _comma_join(obligation.name for obligation in config.authoring_obligations)
    review_surfaces = (
        "hydrated Markdown, combined PDF, web output, slides, figures, data JSON, reports, "
        "validation results, and copy statistics"
    )
    return "\n\n".join(
        [
            (
                f"The method is {method}. Each slot combines the seed, slot name, category, ordinal, and full "
                "category list into a SHA-256 digest; the digest indexes the configured category. Including the "
                "full category list in the digest input means that a lexicon edit can change the plan in a "
                "deterministic and reviewable way instead of silently preserving stale output."
            ),
            (
                "The deterministic digest recipe is deliberately narrow. It does not sample from ambient prose, "
                "project history, or renderer state; it uses only the committed seed, the slot declaration, the "
                "category name, the ordinal for repeated slots, and the ordered category inventory. A fork can "
                "therefore explain a changed token choice as a changed seed, slot, or lexicon row rather than as "
                "an opaque generation event."
            ),
            (
                "The first review scenario is declared before generation. The project names its scope as a local "
                "exemplar, records enabled sections, keeps DOI and publication claims blank, and treats the copy "
                "stage as a review handoff. That ordering matters because a reader should know the allowed claim "
                "boundary before inspecting fluent generated text."
            ),
            (
                f"The governing constraint is {constraint}. The source manuscript is intentionally sparse: it "
                "contains section titles and large-grain placeholders, not generated claims. The project script "
                "first validates the `madlib:` block, expands slots into a `TokenPlan`, builds section bodies, "
                "writes artifact JSON, emits a figure registry, and only then writes hydrated Markdown under "
                "`output/manuscript/`."
            ),
            (
                f"The configured method moves are {moves}. The protocol sequence is {protocol}. These steps "
                "make the method auditable from three directions: tests inspect the Python behavior, generated "
                "artifacts expose the token plan, and manuscript validation confirms that no unresolved "
                "placeholder survives into rendered outputs."
            ),
            (
                f"The config-origin inventory currently separates {explicit_count} explicit YAML path(s) from "
                f"{defaulted_count} loader-defaulted path(s). Treating origin as method evidence prevents a "
                "rendered field from looking equally authored when it was actually inherited from the loader. "
                "The same inventory drives configured-field tables and figures, so reviewers can inspect which "
                "schema blocks were intentionally set before judging the generated prose."
            ),
            (
                "Method invariants are reviewed as their own artifact. Token choices are allowed to change when "
                "the seed, slot name, category, ordinal, or ordered category inventory changes; they are not "
                "allowed to change because PDF rendering, HTML rendering, file-copy order, or hand-edited output "
                "changed. This separates generation logic from presentation logic."
            ),
            (
                "Lexicon governance is handled as data governance. Required categories must be nonempty, optional "
                f"categories remain project-owned when declared, and the selected {len(token_plan.choices)} token "
                f"choice(s) stay bound to {len(config.lexicon)} configured category list(s). The slot-to-section "
                f"allocation is {slot_allocation}, which lets the Methods, Results, and provenance tables state "
                "where each lexical decision enters the manuscript."
            ),
            (
                "Conditional section generation is handled before prose assembly. A disabled section does not "
                "vanish and does not borrow claims from an enabled section; it resolves to an explicit statement "
                "that names the controlling `madlib.section_conditions` key. That behavior keeps negative or "
                "excluded material visible to reviewers."
            ),
            (
                "Evidence tables and visual audit figures are generated from the same config and `TokenPlan`. "
                f"Enabled visualizations are {visual_flags}; they summarize field origin, token density, injection "
                "flow, section allocation, provenance, and quality gates without adding independent claims. Figure "
                "registration is therefore a method step: every manuscript image has to be written, registered, "
                "and validated as part of the reproducible render path."
            ),
            (
                "Claim-ledger alignment is part of composition. The contribution table can make local method "
                "claims, but publication, empirical, reader-quality, and domain-specific claims must either point "
                "to evidence or remain explicit non-claims. This is why the claim ledger, audit rules, limitations, "
                "and authoring contract are generated beside the Methods rather than written after the fact."
            ),
            (
                "Evaluation is part of the method rather than an afterthought. The config declares quality probes "
                f"({quality_probes}) and failure modes ({failure_modes}); the source turns them into tables and "
                "validation checks the rendered surface. That means methods, results, evaluation, and limitations "
                "all share one source-owned schema instead of drifting as independent prose."
            ),
            (
                f"The method is organized around design principles: {principle_names}. These principles prevent "
                "the Mad Lib surface from becoming a hidden authoring channel. They require the visible manuscript "
                "to stay downstream of declared inputs, the generated outputs to remain disposable, and the audit "
                "surface to be broad enough for a reviewer to reconstruct how a sentence reached the PDF."
            ),
            (
                f"The operational phases are {phase_summary}. Each phase has an explicit input, transformation, "
                "output, and guard. This makes the pipeline explainable at manuscript scale: a reader can follow "
                "the path from YAML declarations to token choices, from token choices to section bodies, from "
                "section bodies to rendered artifacts, and from rendered artifacts to validation reports."
            ),
            (
                f"The reviewer packet is also a method artifact. The handoff surface is {review_surfaces}; a PDF "
                "alone is insufficient because it cannot show the token inventory, field-origin inventory, figure "
                "registry, validation report, or copied-output statistics. The declared authoring obligations are "
                f"{obligations}, which convert that packet into review work a human can actually perform."
            ),
            (
                f"The claim-boundary contract is also generated. The audit-rule list contains "
                f"{len(config.audit_rules)} rule(s), and the contribution table binds each local claim to a "
                "non-publication boundary. The final copy stage is a human-review handoff, not proof that the "
                "Mad Lib surface is empirically valid or ready for a standalone release."
            ),
            (
                "Fork migration closes the method. A downstream project should update config rows, source-owned "
                "composition, validators, claim-ledger entries, and documentation before replacing exemplar "
                "vocabulary with domain claims. Without that migration work, the fork has only changed words, not "
                "the evidential status of the generated manuscript."
            ),
        ]
    )


def _results(config: MadlibConfig, token_plan: TokenPlan) -> str:
    enabled = len(config.enabled_sections)
    density = ", ".join(f"{key}: {value}" for key, value in sorted(token_plan.category_counts.items()))
    moves = _sentence_list(config.narrative_moves["results"])
    visualizations = _comma_join(config.visualizations.enabled_flags)
    return "\n\n".join(
        [
            (
                f"The generated plan enables {enabled} of {len(SECTION_KEYS)} manuscript sections and fills "
                f"{len(token_plan.choices)} token choice(s). Category density is {density}. The result figures "
                "are generated from the same token plan that writes the inventory table, so visual and tabular "
                "claims share one source."
            ),
            (
                f"The configured results moves are {moves}. The important result is therefore not a surprising "
                "word choice; it is the survival of traceability through a complete render path. Each token row "
                "records the variable, category, selected value, section, and config pointer that produced it."
            ),
            (
                "The resolved manuscript also demonstrates the intended failure boundary. If a manuscript "
                "placeholder is added without a corresponding variable, the project test suite detects it. If a "
                "figure is referenced without registry support, the output validator reports it. If a generated "
                "number lacks evidence support, the evidence registry gate reports it before the copied output "
                "stage packages deliverables."
            ),
            (
                f"Visualization is enabled for {visualizations}. The configured-field figures are generated "
                "from the same explicit/default path inventory written to JSON; the pipeline, allocation, "
                "provenance, and gate figures are generated from the same token plan and QA schema."
            ),
        ]
    )


def _discussion(config: MadlibConfig, token_plan: TokenPlan) -> str:
    adjective = token_plan.first_value("adjectives", "bounded")
    moves = _sentence_list(config.narrative_moves["discussion"])
    return "\n\n".join(
        [
            (
                f"The {adjective} result is intentionally modest. The exemplar does not claim that random "
                "lexical replacement creates scholarship, discovers facts, or substitutes for authorship. It "
                "shows that a conditional text generator can be made accountable to configuration, tests, and "
                "render-time validation."
            ),
            (
                f"The configured discussion moves are {moves}. Useful adaptations include templated empirical "
                "reports, structured review memos, classroom exercises, and manuscript sections that need to "
                "toggle across protocols. Risky adaptations include hiding weak claims behind fluent generated "
                "phrasing or allowing a token category to imply evidence that the project never produced."
            ),
            (
                "The pattern scales only when authors preserve the same ownership boundary. Lexicons should be "
                "small enough to review, categories should be named for their manuscript function, and section "
                "switches should state what has been removed. When richer language is needed, the next layer "
                "should add domain-specific validators rather than relaxing provenance."
            ),
        ]
    )


def _configuration(config: MadlibConfig, token_plan: TokenPlan) -> str:
    explicit_count = len(config.explicit_paths)
    defaulted_count = len(config.defaulted_paths)
    return "\n\n".join(
        [
            (
                f"The active composition depth is `{config.composition_depth}`. The lexicon exposes "
                f"{len(config.lexicon)} category list(s), and the slot declaration expands to "
                f"{len(token_plan.choices)} concrete token choice(s). Section switches are evaluated before "
                "composition so disabled sections cannot silently borrow enabled-section claims."
            ),
            (
                "Configuration owns more than vocabulary. It also owns section titles, narrative moves, method "
                "protocol rows, contribution claims, and audit rules. That makes the manuscript shape visible in "
                "one YAML file while preserving the rule that source code, not hand-edited output, performs the "
                "composition."
            ),
            (
                "The tables in this section expose the declared surface that controls rendering. They are useful "
                "during review because a title change, slot expansion, or disabled section appears as a small "
                "config diff and a regenerated artifact diff rather than as scattered prose edits."
            ),
            (
                f"The configured-field inventory separates {explicit_count} explicit YAML path(s) from "
                f"{defaulted_count} loader-defaulted path(s). That distinction matters for forks: a field that "
                "appears in the rendered manuscript may be intentionally authored in `config.yaml`, or it may be "
                "a documented default inherited from the template."
            ),
        ]
    )


def _evaluation(config: MadlibConfig, token_plan: TokenPlan) -> str:
    moves = _sentence_list(config.narrative_moves["evaluation"])
    gates = _comma_join(tuple(sorted({criterion.gate for criterion in config.evaluation_criteria})))
    artifacts = _comma_join(token_plan.values_for_category("artifacts")[:3])
    probes = _comma_join(probe.name for probe in config.quality_probes)
    return "\n\n".join(
        [
            (
                f"The evaluation section is configured to {moves}. The local readiness surface is not a human "
                "preference score; it is a set of deterministic checks that connect generated manuscript claims "
                "to source files and pipeline gates."
            ),
            (
                f"The active criteria use {gates} as gate labels and inspect artifacts such as {artifacts}. "
                "A passing run means the exemplar is locally render-ready: placeholders resolve, token "
                "provenance is present, figure references are registered, evidence scanning has not found "
                "unsupported numbers, and project design overlays remain internally consistent."
            ),
            (
                "That readiness is deliberately narrower than publication readiness. A local pass does not imply "
                "a standalone DOI, external release, reader preference result, or empirical validation. It means "
                "the tracked project tree can regenerate the committed artifact surface through its declared "
                "pipeline."
            ),
            (
                f"The QA probes are {probes}. They are phrased as questions so they can be reused by reviewers "
                "and by forks of the exemplar: did the placeholder disappear, did the provenance survive, did "
                "the figure registry cover every reference, and did copied outputs preserve the same evidence "
                "surface that validation inspected?"
            ),
        ]
    )


def _reproducibility(config: MadlibConfig, token_plan: TokenPlan) -> str:
    protocol_outputs = _comma_join(step.output for step in config.method_protocol)
    return "\n\n".join(
        [
            (
                f"Re-running generation with seed `{config.seed}` and the same lexicon produces the same token "
                "plan. The artifact set records `token_inventory.json`, `section_plan.json`, "
                "`injection_trace.json`, `manuscript_variables.json`, `figure_registry.json`, and the "
                "cover/results/configuration/evaluation figure set so the manuscript can be audited without "
                "reading the PDF."
            ),
            (
                f"The protocol emits {protocol_outputs}. Project tests cover deterministic token choice, seed "
                "sensitivity, category-input sensitivity, malformed config rejection, section disablement, "
                "artifact writing, and unresolved manuscript-token detection. The shared output validator then "
                "checks rendered PDFs, Markdown, figure registry, evidence registry, and design overlays."
            ),
            (
                "The copied root output is therefore a consequence of local source and config. Generated files "
                "remain disposable; the durable contract is the ability to regenerate them from the tracked "
                "project tree and to observe the same validation gates passing."
            ),
        ]
    )


def _limitations(config: MadlibConfig) -> str:
    moves = _sentence_list(config.narrative_moves["limitations"])
    mode_names = _comma_join(tuple(mode.name for mode in config.failure_modes))
    return "\n\n".join(
        [
            (
                f"The limitations section is configured to {moves}. The central limitation is that deterministic "
                "token injection can make manuscript assembly auditable, but it cannot make a weak claim true or "
                "a missing source appear."
            ),
            (
                f"The declared failure modes are {mode_names}. They are included in the manuscript because this "
                "template is meant to teach the boundary, not hide it. A useful fork should extend this table "
                "when it adds domain-specific claims, validators, or publication targets."
            ),
            (
                "The author remains responsible for theory, citations, reader expectations, and domain evidence. "
                "The generator can enforce structure and provenance; it cannot supply judgment. That division is "
                "the main safety property of the exemplar."
            ),
        ]
    )


def _scope(config: MadlibConfig) -> str:
    moves = _sentence_list(config.narrative_moves["scope"])
    return "\n\n".join(
        [
            (
                "The exemplar is a pipeline testbed, not a natural-language quality benchmark. It covers "
                "deterministic token selection, conditional section bodies, section-title injection, provenance "
                "tables, and generated evidence artifacts. It does not evaluate semantic originality, factual "
                "truth beyond the local configuration, or reader preference."
            ),
            (
                f"The configured scope moves are {moves}. The closest related systems are not general-purpose "
                "chatbots but source-owned report generators, literate-programming documents, static-site data "
                "templates, and reproducible manuscript pipelines. `template_madlib` contributes a deliberately "
                "small version of that idea for research manuscripts."
            ),
            (
                "Publication metadata remains conservative. The local `CITATION.cff`, `.zenodo.json`, and "
                "`codemeta.json` describe this exemplar inside the shared template repository; they do not claim "
                "a live standalone DOI, external release, or empirical validation outside the generated local "
                "artifacts."
            ),
        ]
    )


def _authoring_contract(config: MadlibConfig, token_plan: TokenPlan) -> str:
    moves = _sentence_list(config.narrative_moves["authoring_contract"])
    audience = token_plan.first_value("audiences", "template authors")
    quality = token_plan.first_value("qualities", "reviewability")
    obligations = _comma_join(obligation.name for obligation in config.authoring_obligations)
    return "\n\n".join(
        [
            (
                f"The authoring contract is configured to {moves}. It addresses {audience} directly because "
                "the generator can preserve structure, provenance, and reviewability, but it cannot decide what "
                "a field should claim. Human authors remain responsible for theory, interpretation, citations, "
                "and the choice to publish."
            ),
            (
                f"The declared obligations are {obligations}. They convert responsible use into a checklist: "
                "review generated claims in the hydrated manuscript, inspect the generated evidence tables, extend "
                "the claim ledger when new claims appear, and add domain-specific validators before the template is "
                "used for a real empirical or theoretical manuscript."
            ),
            (
                f"The quality standard is {quality}. A fork that only changes words has not preserved the exemplar. "
                "A responsible fork changes the config, adjusts source-owned composition where necessary, regenerates "
                "artifacts, and reruns the same tests and validation gates before treating the output as reader-ready."
            ),
        ]
    )
