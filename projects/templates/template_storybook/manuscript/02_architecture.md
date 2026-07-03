# Architecture

The storybook uses the same Layer-2 project contract as the other public
templates:

- `content/story.yaml` owns cast records and page records.
- `src/storybook/characters.py` validates shape characters.
- `src/storybook/story.py` loads the content file into typed records.
- `src/storybook/illustration.py` renders the full-page scenes.
- `src/storybook/rendering.py` assembles PNG pages into the PDF and writes the
  manifest.
- `scripts/` contains the thin Stage-02 entry points.

The page scripts are deliberately repetitive. Their job is visible
orchestration: cover, page 1, page 2, and so on. The repetition keeps the
creative page surface easy to inspect while preventing scripts from becoming
hidden rendering engines.
