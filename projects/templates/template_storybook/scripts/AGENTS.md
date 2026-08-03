# AGENTS - `template_storybook/scripts`

Scripts in this directory are Stage-02 orchestrators. They choose a page or
final artifact and delegate all rendering behavior to `src/storybook/`.

The script order is intentional:

1. `10_render_cover.py`
2. `20_render_page_01.py`
3. `21_render_page_02.py`
4. `22_render_page_03.py`
5. `23_render_page_04.py`
6. `24_render_page_05.py`
7. `25_render_page_06.py`
8. `26_render_page_07.py`
9. `27_render_page_08.py`
10. `28_render_page_09.py`
11. `29_render_page_10.py`
12. `30_render_page_11.py`
13. `31_render_page_12.py`
14. `32_render_page_13.py`
15. `90_build_storybook_pdf.py`

The final script also emits the deterministic contact sheet and page-level
alt-text manifest; neither is hand-edited.

Keep new scripts small and support `--project-root` so tests can run against a
temporary content tree.
