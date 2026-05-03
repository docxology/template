"""Hydrate manuscript variables for the prose project.

Mirrors the pattern in ``template_code_project`` and
``template_search_project``: read the manuscript-report JSON, compute a
small set of substitution variables, write them to JSON, and (when used
with :func:`substitute_in_text`) replace ``{{UPPER_NAME}}`` markers in
the manuscript markdown.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class ManuscriptVariables:
    """Variables substituted into manuscript markdown."""

    config_title: str
    total_words: int
    total_sentences: int
    total_paragraphs: int
    avg_grade_level: float
    avg_reading_ease: float
    avg_gunning_fog: float
    citation_count: int
    files_analysed: int
    longest_section_words: int
    shortest_section_words: int

    def as_dict(self) -> dict[str, object]:
        return asdict(self)

    def as_uppercase_keys(self) -> dict[str, str]:
        return {f"{{{{{k.upper()}}}}}": str(v) for k, v in asdict(self).items()}


def compute_variables(
    *,
    config_title: str,
    manuscript_report: Mapping[str, object],
) -> ManuscriptVariables:
    """Pure computation: no I/O. Tests construct the inputs directly."""
    files = list(manuscript_report.get("files") or [])
    section_word_counts: list[int] = []
    for f in files:
        m = f.get("metrics") or {}
        section_word_counts.append(int(m.get("word_count", 0)))
    longest = max(section_word_counts) if section_word_counts else 0
    shortest = min(section_word_counts) if section_word_counts else 0

    return ManuscriptVariables(
        config_title=config_title,
        total_words=int(manuscript_report.get("total_words", 0)),
        total_sentences=int(manuscript_report.get("total_sentences", 0)),
        total_paragraphs=int(manuscript_report.get("total_paragraphs", 0)),
        avg_grade_level=float(manuscript_report.get("avg_flesch_kincaid_grade", 0.0)),
        avg_reading_ease=float(manuscript_report.get("avg_flesch_reading_ease", 0.0)),
        avg_gunning_fog=float(manuscript_report.get("avg_gunning_fog", 0.0)),
        citation_count=len(list(manuscript_report.get("citation_keys") or [])),
        files_analysed=len(files),
        longest_section_words=longest,
        shortest_section_words=shortest,
    )


def load_manuscript_report(path: Path | str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_variables(variables: ManuscriptVariables, output_path: Path | str) -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(variables.as_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return out


def substitute_in_text(text: str, variables: ManuscriptVariables) -> str:
    """Replace ``{{KEY}}`` markers in *text* with the variable values."""
    out = text
    for marker, value in variables.as_uppercase_keys().items():
        out = out.replace(marker, value)
    return out


def write_resolved_manuscript_tree(
    project_root: Path | str,
    variables: ManuscriptVariables,
) -> Path:
    """Write ``manuscript/*.md`` with substitutions plus aux files into ``output/manuscript``.

    PDF rendering prefers ``output/manuscript`` when it contains markdown
    (see :func:`infrastructure.rendering.pipeline._resolve_manuscript_dir`),
    matching the contract used by the code and search exemplars.
    """
    root = Path(project_root)
    manuscript_dir = root / "manuscript"
    out_dir = root / "output" / "manuscript"
    out_dir.mkdir(parents=True, exist_ok=True)

    for md_file in sorted(manuscript_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        out_dir.joinpath(md_file.name).write_text(
            substitute_in_text(text, variables),
            encoding="utf-8",
        )

    for aux in ["config.yaml"]:
        src = manuscript_dir / aux
        if src.is_file():
            shutil.copy2(src, out_dir / aux)

    for bib in sorted(manuscript_dir.glob("*.bib")):
        shutil.copy2(bib, out_dir / bib.name)

    return out_dir
