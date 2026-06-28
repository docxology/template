# FAQ

## What is the gold-refining analogy?

The analogy maps gold-refining metallurgy (ore → smelting → assaying →
cupellation → certification) onto scientific manuscript composition. Each
metallurgical stage corresponds to a real template-infrastructure operation:
smelting removes dross (filler), assaying validates claims against evidence,
cupellation resolves cross-references, and certification runs full pipeline
validation.

## Is the analogy load-bearing or rhetorical?

Both. It frames the methods paper (rhetorical) and operationalizes each stage
against real infrastructure (load-bearing). The open question is not whether
to use the analogy, but where the mapping breaks.

## What is "nine-nines" purity?

Nine-nines (99.9999999%) is the ultra-high-purity standard used in
electronics-grade gold. In this exemplar, it represents the final
certification stage: a fully validated, reproducible manuscript.

## How does the mega-madlib token engine work?

Token selection uses a seeded SHA-256 digest over category inventories.
The inputs are: seed, slot name, category, ordinal, and the full ordered
category inventory. The digest determines which value is selected. Same
seed + same lexicon = same token plan, every time.

## How do I add a new lexicon category?

Add it under `gold_refinement.lexicon` in `manuscript/config.yaml`. Required
categories are: `metallurgical_terms`, `manuscript_terms`, `purity_adjectives`,
`refinement_verbs`. Optional categories are allowed.

## How do I add a new manuscript token?

1. Add a slot in `manuscript/config.yaml` under `gold_refinement.slots`
2. The variable name is auto-generated: `SLOT_NAME` (count=1) or
   `SLOT_NAME_1`, `SLOT_NAME_2`, ... (count>1)
3. The live cross-reference test in `test_manuscript_variables.py` will fail
   if a manuscript `{{TOKEN}}` is not generated.

## How do I fork this exemplar?

See [STANDALONE.md](../STANDALONE.md) for the fork checklist,
[docs/domain_fork_guide.md](domain_fork_guide.md) for the stage-remap pattern,
and [docs/quickstart.md](quickstart.md) for getting started.
