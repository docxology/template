# Troubleshooting

If a page is missing from the PDF, rerun Stage 02 and inspect
`output/data/storybook_manifest.json`.

If text is difficult to read, switch the page's `overlay_box` value in
`content/story.yaml` or adjust the page palette.

If a fork adds a new scene name, add the scene branch in
`src/storybook/illustration.py` and add a test that renders it.
