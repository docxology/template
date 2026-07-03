# Test Patterns

- Keep content checks tied to `content/story.yaml`.
- Render temporary PDFs in `tmp_path` when possible.
- Exercise at least one page script with `--project-root` so script orchestration
  remains thin and testable.
