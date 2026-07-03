# Rendering Pipeline

Stage 02 runs the configured scripts in `manuscript/config.yaml`.

The cover and each numbered page render first as PNG files in
`output/figures/storybook_pages/`. The final script assembles those images into
`output/pdf/the-shape-between.pdf` and writes manifest files under
`output/data/` and `output/reports/`.
