# Introduction {#sec:introduction}

Every other public exemplar in this monorepo renders a manuscript: prose,
figures, citations, a combined PDF. None of them render a *pitch* — a
short-form, persuasion-oriented artifact whose job is not to document a
method but to move an audience to a decision. Pitch decks live outside the
repository's reproducibility guarantees entirely: built by hand in
proprietary tools, their claims untethered from any generator, their content
unchecked for the boilerplate language ("synergy," "disruptive," "10x") that
makes a real pitch land badly with a sophisticated audience.

`template_pitch_deck` treats a pitch deck the same way this repository treats
a manuscript: as a build artifact with a single source of truth, a validation
gate, and a reproducibility guarantee. Three properties make that possible.

**One content source, six artifacts.** `manuscript/deck_content_{short,medium,long}.yaml`
define the slide-by-slide narrative at three lengths; `manuscript/deck_tokens.yaml`
supplies the facts. `scripts/render_decks.py` resolves tokens once and calls
both renderers — `infrastructure.rendering.slide_deck.render_pdf` and
`infrastructure.rendering.pptx_deck.render_pptx` — against the identical
resolved content, so PDF and PPTX cannot drift from each other.

**Facts, not fabrication.** Every numeric claim in `deck_tokens.yaml` about the
pitch subject (`template_template`) is generated from a live read of that
project's own `README.md`/`AGENTS.md` or the repository's public exemplar
roster — never hand-typed, never a plausible-sounding invented metric.
`src/token_resolution.py` raises loudly if any `{{TOKEN}}` in the content
source has no corresponding resolved value, and a rendered artifact's
extracted text is checked to contain zero leftover `{{` literals.

**Cliché is a lint, not a vibe.** `src/cliche_lint.py` runs a word-boundary
denylist of pitch-deck stock phrases over every resolved slide before
render. A pitch that reads as generic — regardless of how factually accurate
it is — fails the same way an uncovered line of code fails a coverage gate.

The remainder of this manuscript covers the deck-rendering architecture
([@sec:architecture]), the validation model ([@sec:validation]), and the
reproducibility guarantees ([@sec:reproducibility]) that let
`uv run python scripts/render_decks.py --project templates/template_pitch_deck`
produce the same six files, byte-for-byte, on any machine with this repo
checked out.
