"""Detect manuscript prose that treats synthetic fixture output as empirical findings."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FixtureHonestyFinding:
    path: Path
    line_number: int
    message: str
    excerpt: str


_EMPIRICAL_PHRASES = (
    re.compile(r"\bwe (?:found|observed|demonstrate|showed|confirmed)\b", re.I),
    re.compile(r"\bour (?:findings|results) (?:show|demonstrate|confirm)\b", re.I),
    re.compile(r"\bempirical(?:ly)?\b", re.I),
)

_HARDCODED_DOMAIN = re.compile(r"\bmodafinil literature\b", re.I)

_NEGATIVE_CONTROL = "Our empirical findings confirm that modafinil literature demonstrates universal efficacy."


def validate_fixture_honesty(
    manuscript_dir: Path,
    *,
    search_term: str | None = None,
    extra_paths: list[Path] | None = None,
) -> list[FixtureHonestyFinding]:
    findings: list[FixtureHonestyFinding] = []
    paths = sorted(manuscript_dir.glob("*.md"))
    if extra_paths:
        paths.extend(extra_paths)
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "{{" in line:
                continue
            for pattern in _EMPIRICAL_PHRASES:
                if pattern.search(line):
                    findings.append(
                        FixtureHonestyFinding(
                            path=path,
                            line_number=line_no,
                            message="Empirical claim phrasing without template-variable disclaimer",
                            excerpt=stripped[:120],
                        )
                    )
                    break
            if _HARDCODED_DOMAIN.search(line):
                findings.append(
                    FixtureHonestyFinding(
                        path=path,
                        line_number=line_no,
                        message="Hard-coded domain phrase; use {{SEARCH_TERM}} token instead",
                        excerpt=stripped[:120],
                    )
                )
            if search_term and search_term.lower() in line.lower():
                if not any(token in text for token in ("{{SEARCH_TERM}}", "{{SEARCH_TERM_TITLE}}")):
                    findings.append(
                        FixtureHonestyFinding(
                            path=path,
                            line_number=line_no,
                            message="Literal search term in prose; prefer {{SEARCH_TERM}}",
                            excerpt=stripped[:120],
                        )
                    )
                    break
    return findings


def validate_negative_control() -> list[FixtureHonestyFinding]:
    findings: list[FixtureHonestyFinding] = []
    for pattern in _EMPIRICAL_PHRASES:
        if pattern.search(_NEGATIVE_CONTROL):
            findings.append(
                FixtureHonestyFinding(
                    path=Path("<negative-control>"),
                    line_number=1,
                    message="Negative control matched empirical phrasing",
                    excerpt=_NEGATIVE_CONTROL,
                )
            )
            break
    if _HARDCODED_DOMAIN.search(_NEGATIVE_CONTROL):
        findings.append(
            FixtureHonestyFinding(
                path=Path("<negative-control>"),
                line_number=1,
                message="Negative control matched hard-coded domain phrase",
                excerpt=_NEGATIVE_CONTROL,
            )
        )
    return findings
