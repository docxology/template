# Storybook Package

`storybook/` contains the reusable implementation for the illustrated storybook
exemplar. It loads the story YAML, validates characters and pages, renders
full-page illustrations, and assembles the final PDF.

Use `scripts/10_render_cover.py`, `scripts/20_render_page_*.py`, and
`scripts/90_build_storybook_pdf.py` as orchestration entry points from the
repository pipeline.
