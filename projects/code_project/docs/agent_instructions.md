# AI Agent Instructions

When interacting with the `code_project` exemplar, AI Assistants **must** adhere to the following rules constraints:

1. **Read This Hub First**: The `docs/` folder contains the explicit operational boundaries.
2. **Maintain coverage**: If you modify `src/`, extend `tests/` so `projects/code_project/src/` stays **≥90%** covered (current suite ~96%; see `testing_philosophy.md`).
3. **Honor the Thin Orchestrator**: Never implement math or business logic inside `scripts/`. Move logic to `src/` and only use `scripts/` to chain calls together (`architecture.md`).
4. **"Show, Not Tell" Documentation**: When updating `manuscript/` files, use explicit file paths (e.g., `infrastructure.rendering.pdf_renderer.py`) instead of dotted notation or vague descriptions (`rendering_pipeline.md`).
5. **Determinism**: Prefer fixed inputs in `src/` and tests. If a test uses random draws (e.g. timing on random vectors), keep them bounded and avoid unseeded RNG in assertions that must be bitwise reproducible across machines; document intent in the test.
6. **Follow Style and Syntax Guides**: Conform to the rigorous standards defined in `style_guide.md` (for the prohibition of mocks and delegation strategy) and `syntax_guide.md` (for madlib variable injection and LaTeX cross-referencing).
