# Abstract {#sec:abstract}

Research groups routinely need to pitch their work — to funders, partners, or
collaborators — yet pitch decks are almost never treated as reproducible
research artifacts: they are hand-assembled in proprietary slide tools,
contain unverifiable claims, and cannot be regenerated when the underlying
facts change. `template_pitch_deck` closes that gap. It generates six
artifacts from one token-resolved content source — short, medium, and long
decks, each in both PDF and PPTX — with every numeric claim traced back to a
live introspection of the repository it describes, every `{{TOKEN}}`
substitution verified to have actually landed, and every sentence checked
against a denylist of pitch-deck clichés.

The flagship content pitches [`template_template`](../../template_template/), this
monorepo's own autopoietic meta-project, to a meta-science and
science-integrity audience — the kind of pitch an organization like the
Active Inference Institute or COGSEC would actually hand to a funder. The
rendering engine itself is new, reusable infrastructure:
`infrastructure/rendering/slide_deck.py` (ReportLab, PDF) and
`infrastructure/rendering/pptx_deck.py` (python-pptx) both consume the same
`DeckContent` model, so a PDF and a PPTX built from identical content carry
identical slide counts and identical text — verified by direct read-back of
both file formats, not by inspection.

**Keywords:** pitch deck, slide generation, reproducible research
communication, meta-science infrastructure, token validation, PPTX, PDF
rendering.
