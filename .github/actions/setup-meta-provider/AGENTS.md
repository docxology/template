# Meta provider setup

This composite action owns only genuine Meta wheel preparation for the root
environment. Source is the canonical public
projects/templates/template_literature_meta_analysis tree.

Keep checkout, interpreter setup and uv sync --locked --group installed-build
explicit in each caller. Build and install with the same .venv/bin/python;
retain noneditable installation and --no-deps so provider preparation cannot
change the locked dependency selection.

Verify with actionlint and the real Advanced/hydration tests. See
[README.md](README.md) for the caller contract.
