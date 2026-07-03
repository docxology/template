# Storybook Scripts

Run from the project root:

```bash
uv run python scripts/10_render_cover.py
uv run python scripts/20_render_page_01.py
uv run python scripts/29_render_page_10.py
uv run python scripts/90_build_storybook_pdf.py
```

The repository Stage-02 command runs the configured list in
`manuscript/config.yaml`:

```bash
uv run python scripts/02_run_analysis.py --project templates/template_storybook
```
