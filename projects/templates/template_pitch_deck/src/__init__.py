"""template_pitch_deck — pitch-deck content, token resolution, and cliche linting.

All slide-layout/drawing code lives in `infrastructure/rendering/{slide_deck,pptx_deck}.py`;
this package holds only pitch-deck-domain logic: loading YAML content into
`DeckContent` objects, resolving `{{TOKEN}}` values against live repository
facts, and linting resolved text for cliche.
"""
