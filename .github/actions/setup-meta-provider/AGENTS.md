# Meta provider setup

This composite action owns only genuine Meta wheel preparation for an explicitly
prepared environment. Source is the canonical public
projects/templates/template_literature_meta_analysis tree.

Keep checkout, interpreter setup and uv sync --locked --group installed-build
explicit in each caller. Use the existing project-only exemplar exporter without
a rename to create an
independent runner-temporary packaging copy. Build there with the absolute
locked root .venv/bin/python; build and egg-info metadata belong to that owned
copy, never the canonical checkout. Do not clean canonical Source or relax its
Git-body inventory. Install into python-executable, defaulting to the same
interpreter. Pass that input
through the quoted PROVIDER_PYTHON environment variable;
retain noneditable installation and --no-deps so provider preparation cannot
change the locked dependency selection.

Verify with actionlint and the real Advanced/hydration tests. See
[README.md](README.md) for the caller contract.
