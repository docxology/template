#!/usr/bin/env python3
"""Generate (or check) docs/_generated/exemplar_roster.md.

Thin orchestrator: all logic lives in ``infrastructure.project.exemplar_roster``.

Usage::

    uv run python scripts/generate_exemplar_roster_doc.py          # write the doc
    uv run python scripts/generate_exemplar_roster_doc.py --check  # verify, no write

``--check`` exits non-zero if any public exemplar README lacks the
``## When to use this template`` section (beyond pinned known exceptions) or
if the committed doc is out of sync with a fresh render.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.project.exemplar_roster import (  # noqa: E402
    DOC_RELATIVE_PATH,
    collect_entries,
    render_roster_markdown,
    unexpected_missing_use_when,
    write_roster_doc,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify use-when coverage and doc sync without writing",
    )
    args = parser.parse_args()

    entries = collect_entries(REPO_ROOT)
    unexpected = unexpected_missing_use_when(entries)
    if unexpected:
        for name in unexpected:
            print(f"MISSING use-when section: projects/{name}/README.md")
        return 1

    doc_path = REPO_ROOT / DOC_RELATIVE_PATH
    if args.check:
        rendered = render_roster_markdown(entries)
        on_disk = doc_path.read_text(encoding="utf-8") if doc_path.is_file() else ""
        if rendered != on_disk:
            print(f"STALE: {DOC_RELATIVE_PATH} differs from a fresh render — regenerate it")
            return 1
        print(f"exemplar_roster: OK ({len(entries)} exemplars, doc in sync)")
        return 0

    written = write_roster_doc(REPO_ROOT)
    print(str(written))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
