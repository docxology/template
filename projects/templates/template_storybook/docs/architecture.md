# Architecture

`template_storybook` separates content, rendering behavior, and orchestration.

`content/story.yaml` owns the story. `src/storybook/` validates the story,
generates characters, renders pages, and assembles the PDF. `scripts/` selects
which page or artifact to build.

The primary artifact is not a manuscript figure set; it is a complete picture
book PDF with one full-bleed illustration per page.
