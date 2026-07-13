# Forking Guide

1. Copy the exemplar.
2. Replace `content/story.yaml`.
3. Add scene branches or drawing helpers in `src/storybook/illustration.py` only
   when existing scenes cannot express the new book; keep typography and overlay
   behavior in `src/storybook/text_layout.py`.
4. Keep scripts thin by calling `render_story_page`, `render_story_number`, or
   `build_storybook_pdf`.
5. Rerender and inspect the PDF.
