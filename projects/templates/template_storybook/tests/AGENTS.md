# AGENTS - `template_storybook/tests`

Use real content files and real render outputs. Tests may render into `tmp_path`
or inspect deterministic artifacts, but should not mock the storybook renderer.

Test files (run one directory per pytest invocation; live counts belong in
[`docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md)):

- `test_story.py` - YAML story contract, cast pairing, page lookup, and
  validation errors
- `test_rendering.py` - full-page PNG rendering, PDF assembly, manifest
  alt text, contrast palette, stale-image cleanup, family colors,
  caption-position control, and script orchestration
- `test_contrast_audit.py` - WCAG 2.1 raster contrast audit on rendered
  overlay and non-overlay pages
