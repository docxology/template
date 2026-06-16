"""Markdown citation key validation against BibTeX sources."""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.core.logging import DiagnosticEvent, DiagnosticSeverity
from infrastructure.core.logging.utils import get_logger
from infrastructure.validation.content.diagnostic_codes import BibtexCode
from infrastructure.validation.content.markdown_strip import strip_code_and_math
from infrastructure.validation.content.validator_pitfalls import NON_RENDERED_MANUSCRIPT_FILES

logger = get_logger(__name__)

CITE_KEY_PATTERN = re.compile(r"(?<![A-Za-z0-9_])@([A-Za-z][\w:.\-]*)")
BIBTEX_KEY_PATTERN = re.compile(r"^@\w+\{\s*([^,\s}]+)\s*[,}]", re.MULTILINE)
CROSSREF_PREFIXES = (
    "sec:",
    "fig:",
    "tbl:",
    "eq:",
    "lst:",
    "def:",
    "prop:",
    "inv:",
    "conj:",
    "alg:",
    "thm:",
)


def validate_citations(
    md_paths: list[str],
    repo_root: str | Path,
    bib_file: str | Path | list[str | Path] | None = None,
) -> list[DiagnosticEvent]:
    """Verify every ``[@key]`` citation resolves in the project's BibTeX file(s)."""
    repo_root_path = Path(repo_root)
    problems: list[DiagnosticEvent] = []
    if not md_paths:
        return problems

    if bib_file is None:
        bib_paths = sorted(Path(md_paths[0]).parent.glob("*.bib"))
    elif isinstance(bib_file, (list, tuple)):
        bib_paths = [Path(p) for p in bib_file if Path(p).exists()]
    else:
        single = Path(bib_file)
        bib_paths = [single] if single.exists() else []

    if not bib_paths:
        return problems

    known_keys: set[str] = set()
    bib_names: list[str] = []
    for bib_path in bib_paths:
        try:
            bib_text = bib_path.read_text(encoding="utf-8", errors="ignore")
        except OSError as e:
            logger.warning(f"Failed to read BibTeX file {bib_path}: {e}")
            continue
        known_keys.update(k.strip() for k in BIBTEX_KEY_PATTERN.findall(bib_text))
        bib_names.append(bib_path.name)

    if not bib_names:
        return problems

    bib_label = bib_names[0] if len(bib_names) == 1 else ", ".join(bib_names)

    for path in md_paths:
        path_obj = Path(path)
        if path_obj.name in NON_RENDERED_MANUSCRIPT_FILES:
            continue
        text = path_obj.read_text(encoding="utf-8")
        try:
            rel: str | Path = path_obj.relative_to(repo_root_path)
        except ValueError:
            rel = path_obj
        rel_str = str(rel)

        prose = strip_code_and_math(text)
        seen_in_file: set[str] = set()
        for m in CITE_KEY_PATTERN.finditer(prose):
            key = m.group(1)
            if key in known_keys or key in seen_in_file:
                continue
            if any(key.startswith(prefix) for prefix in CROSSREF_PREFIXES):
                continue
            seen_in_file.add(key)
            problems.append(
                DiagnosticEvent(
                    severity=DiagnosticSeverity.ERROR,
                    category="MARKDOWN_CITATION",
                    message=f"Undefined citation key '@{key}' (not in {bib_label})",
                    code=BibtexCode.UNDEFINED_KEY,
                    file_path=rel_str,
                    fix_suggestion=(
                        f"Add an entry '@type{{{key}, ...}}' to {bib_names[0]} or "
                        "correct the citation key in the markdown."
                    ),
                )
            )
    return problems
