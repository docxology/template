# AGENTS - `template_storybook/scripts`

Scripts in this directory are Stage-02 orchestrators. They choose a page or
final artifact and delegate all rendering behavior to `src/storybook/`.

The script order is intentional:

1. `10_render_cover.py`
2. `20_render_page_01.py` through `32_render_page_13.py`
3. `90_build_storybook_pdf.py`

Keep new scripts small and support `--project-root` so tests can run against a
temporary content tree.
