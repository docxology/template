from __future__ import annotations

import sys
from pathlib import Path


def bootstrap_project_paths(project_root: Path | None = None) -> Path:
    root = project_root or Path(__file__).resolve().parent.parent
    repo_root = root.parents[2]
    for candidate in (root, root / "src", repo_root):
        text = str(candidate)
        if text not in sys.path:
            sys.path.insert(0, text)
    return root
