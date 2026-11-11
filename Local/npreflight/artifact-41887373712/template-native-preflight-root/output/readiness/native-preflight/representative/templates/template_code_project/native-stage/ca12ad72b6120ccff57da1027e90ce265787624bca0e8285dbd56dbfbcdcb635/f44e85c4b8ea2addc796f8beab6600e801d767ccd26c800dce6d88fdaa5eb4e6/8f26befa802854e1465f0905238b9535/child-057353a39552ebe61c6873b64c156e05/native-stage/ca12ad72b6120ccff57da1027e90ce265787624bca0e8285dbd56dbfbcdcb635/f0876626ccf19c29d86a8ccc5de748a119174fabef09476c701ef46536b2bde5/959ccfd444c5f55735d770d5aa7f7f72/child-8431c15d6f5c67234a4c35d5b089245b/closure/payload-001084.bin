"""README/AGENTS file-list inventory checks."""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.validation.docs.consistency._shared import Inconsistency, line_has_noqa

_FILES_LIST_RE = re.compile(r"^\s*[-*]\s*`?(?P<f>[A-Za-z_]\w*\.py)`?\s*(?:[—:-].*)?$")


def check_readme_files_list(repo_root: Path) -> list[Inconsistency]:
    """Flag ``foo.py`` listed in a package README/AGENTS that exists nowhere in that package."""
    infra = repo_root / "infrastructure"
    if not infra.is_dir():
        return []
    issues: list[Inconsistency] = []
    for doc_name in ("README.md", "AGENTS.md"):
        for doc in infra.rglob(doc_name):
            pkg_dir = doc.parent
            if not (pkg_dir / "__init__.py").is_file():
                continue
            present = {p.name for p in pkg_dir.rglob("*.py")}
            try:
                lines = doc.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            in_fence = False
            for n, line in enumerate(lines, 1):
                if re.match(r"^[ \t]*(`{3,}|~{3,})", line):
                    in_fence = not in_fence
                    continue
                if in_fence or line_has_noqa(line):
                    continue
                fm = _FILES_LIST_RE.match(line)
                if fm and fm.group("f") not in present:
                    issues.append(
                        Inconsistency(
                            file=doc,
                            line=n,
                            category="doc-files-list",
                            detail=(
                                f"lists `{fm.group('f')}` but no such file exists under "
                                f"{pkg_dir.relative_to(repo_root)}/ (vanished or renamed)"
                            ),
                        )
                    )
    return issues
