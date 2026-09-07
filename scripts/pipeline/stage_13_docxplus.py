#!/usr/bin/env python3
"""Pipeline stage 13: export the project as a docxplus intelligent document.

Opt-in. Excluded from default runs by its ``docxplus`` tag, and a no-op skip when
the optional extra is not installed, so nobody who does not want this pays for it.

    uv sync --extra docxplus
    uv run python scripts/pipeline/stage_13_docxplus.py --project templates/template_code_project
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.rendering.docxplus_stage import run_docxplus_export  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export the project as a conforming .docx that carries its own source tree"
    )
    parser.add_argument(
        "--project",
        default="project",
        help="Project directory name or qualified path (e.g. templates/template_code_project); "
        "resolves projects/active/<name> first, else projects/working/<name>",
    )
    parser.add_argument(
        "--signing-key",
        default=None,
        help="Path to a hex Ed25519 private key. Without one the document is built "
        "unsigned, which is honest rather than convenient: an unsigned manifest is "
        "not tamper-evident and the validator says so.",
    )
    parser.add_argument(
        "--password",
        default=None,
        help="Seal the carried project under this password (AES-256-GCM).",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    return run_docxplus_export(
        repo_root,
        args.project,
        signing_key_path=args.signing_key,
        password=args.password,
    )


if __name__ == "__main__":
    raise SystemExit(main())
