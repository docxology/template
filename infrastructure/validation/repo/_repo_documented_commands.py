"""Verify documented shell/Python script references exist on disk."""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.validation.docs.models import ScanAccuracyIssue

logger = get_logger(__name__)


def check_documented_commands(
    repo_root: Path,
    src_modules: set[str],
) -> list[ScanAccuracyIssue]:
    """Scan README and docs/*.md for backticked script paths; report missing files."""
    issues: list[ScanAccuracyIssue] = []

    md_candidates = [repo_root / "README.md"]
    docs_dir = repo_root / "docs"
    if docs_dir.is_dir():
        md_candidates.extend(docs_dir.glob("*.md"))

    for md_file in md_candidates:
        if not md_file.exists():
            continue
        try:
            content = md_file.read_text(encoding="utf-8")
            script_pattern = r"`([\w/]+\.(?:py|sh))`|\./([\w/]+\.(?:py|sh))"
            for match in re.finditer(script_pattern, content):
                script_ref = match.group(1) or match.group(2)

                if script_ref.startswith("src/") or script_ref in src_modules:
                    continue

                before_match = content[: match.start()]
                code_block_count = before_match.count("```")
                if code_block_count % 2 == 1:
                    continue

                script_path = repo_root / script_ref
                if not script_path.exists():
                    for script_dir in ("scripts", "repo_utilities"):
                        alt_path = repo_root / script_dir / Path(script_ref).name
                        if alt_path.exists():
                            break
                    else:
                        if (
                            md_file.name == "EXAMPLES.md"
                            and "Create"
                            in content[max(0, match.start() - 50) : match.start()]
                        ):
                            continue

                        if (
                            script_ref.endswith(".sh")
                            or "scripts/" in script_ref
                            or "repo_utilities/" in script_ref
                        ):
                            line_num = content[: match.start()].count("\n") + 1
                            issues.append(
                                ScanAccuracyIssue(
                                    category="command",
                                    severity="error",
                                    file=str(md_file.relative_to(repo_root)),
                                    line=line_num,
                                    message=f"Documented script does not exist: {script_ref}",
                                )
                            )
        except (OSError, UnicodeDecodeError) as e:
            logger.debug("Failed to check code accuracy in %s: %s", md_file, e)

    return issues
