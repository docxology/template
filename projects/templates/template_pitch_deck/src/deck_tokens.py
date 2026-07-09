"""Live-sourced facts for the ``template_template`` pitch deck.

Every value returned by :func:`build_deck_tokens` is read from a real
repository artifact at call time — never a hand-typed literal — so
regenerating the deck after the repo changes (a new exemplar added, a new
DOI recorded, coverage moving) picks up the new numbers automatically. This
is the mechanism behind ISC-22/ISC-23 in ``ISA.md``: no business metric here
is fabricated because none of these are business metrics — they are counts,
percentages, and identifiers pulled straight from
``infrastructure.project.public_scope``, ``docs/_generated/COUNTS.md``, and
``template_template``'s own ``manuscript/config.yaml``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import cast

import yaml
from coverage_chart_data import COUNTS_ROW_RE
from infra_facts import build_infra_tokens

from infrastructure.project.public_scope import public_project_names
from infrastructure.publishing.status_report import PublicationState, compile_publishing_status

#: Pitch subjects and this deck's own project name are always a single path
#: segment (a directory name under projects/templates/) — never containing
#: "/" or "..". Enforced before any path construction so a future caller that
#: makes `pitch_subject` configurable (already signaled by manuscript/config.yaml's
#: `deck.pitch_subject` field, not yet wired up) can't read/write outside the
#: intended projects/templates/<name>/ tree (red-team finding, 2026-07-09).
_SAFE_PROJECT_NAME_RE = re.compile(r"^[\w-]+$")


def _validate_project_name(name: str) -> str:
    if not _SAFE_PROJECT_NAME_RE.match(name):
        raise ValueError(f"Not a valid projects/templates/ directory name: {name!r}")
    return name


def _read_counts_row(repo_root: Path, project_name: str) -> tuple[str, str]:
    """Return ``(test_count, coverage_pct)`` for ``project_name`` from COUNTS.md."""
    counts_path = repo_root / "docs" / "_generated" / "COUNTS.md"
    text = counts_path.read_text(encoding="utf-8")
    for match in COUNTS_ROW_RE.finditer(text):
        if match.group("name") == project_name:
            return match.group("tests"), match.group("coverage")
    raise ValueError(f"No COUNTS.md row found for project {project_name!r}")


def _read_pitch_subject_config(repo_root: Path, pitch_subject: str) -> dict:
    _validate_project_name(pitch_subject)
    config_path = repo_root / "projects" / "templates" / pitch_subject / "manuscript" / "config.yaml"
    return cast(dict, yaml.safe_load(config_path.read_text(encoding="utf-8")))


def _read_own_deck_doi_status(repo_root: Path) -> str:
    """Return this deck's own DOI if reserved, else an honest not-yet-reserved status.

    Distinct from ``PITCH_SUBJECT_DOI`` (the DOI of the project being pitched,
    e.g. ``template_template``) — this is the citable identity of the pitch
    deck itself. Reads ``template_pitch_deck``'s own ``manuscript/config.yaml``
    directly (this token-sourcing module lives inside that same project), so
    the value updates automatically the moment a real Zenodo deposit is
    recorded there — no separate step required.
    """
    own_config_path = repo_root / "projects" / "templates" / "template_pitch_deck" / "manuscript" / "config.yaml"
    own_config = cast(dict, yaml.safe_load(own_config_path.read_text(encoding="utf-8")))
    doi = (own_config.get("publication") or {}).get("doi", "")
    if doi:
        return str(doi)
    return "not yet reserved — no Zenodo deposit on file for this deck"


def _exemplar_roster(exemplar_names: list[str]) -> str:
    """Comma-joined list of every public exemplar's short name, sorted."""
    return ", ".join(sorted(name.rsplit("/", 1)[-1] for name in exemplar_names))


#: Human-readable labels for the registry's internal platform slugs. Only
#: covers slugs actually seen PUBLISHED across current exemplars; an unknown
#: slug falls back to a title-cased version of its own name rather than
#: raising, so a newly-published platform never breaks deck rendering.
_PLATFORM_DISPLAY_NAMES: dict[str, str] = {
    "zenodo": "Zenodo",
    "github": "GitHub",
    "github_pages": "GitHub Pages",
    "pypi": "PyPI",
    "osf": "OSF",
    "software_heritage": "Software Heritage",
    "huggingface_hub": "Hugging Face",
    "ipfs_pinata": "IPFS",
    "ipfs_web3storage": "IPFS",
    "netlify": "Netlify",
    "cloudflare_pages": "Cloudflare Pages",
    "arxiv": "arXiv",
}


def _display_platform_name(platform_name: str, reference: str | None) -> str:
    """Return a human-readable label for one published platform.

    Detects PyPI *sandbox* listings live from the actual reference URL
    (`test.pypi.org`) rather than hardcoding a claim about any specific
    project's current listing — a prior deck draft named "PyPI" flatly for a
    listing that is actually on the TestPyPI sandbox, which is checkable and
    would read as false advertising to a skeptical reviewer (red-team
    finding, 2026-07-09). This stays honest automatically if a project later
    moves to production PyPI, and for any project that already is on
    production PyPI, with no per-project special-casing needed.
    """
    label = _PLATFORM_DISPLAY_NAMES.get(platform_name, platform_name.replace("_", " ").title())
    if platform_name == "pypi" and reference and "test.pypi.org" in reference:
        return f"{label} (sandbox)"
    return label


def _published_platform_names_and_count(repo_root: Path, pitch_subject: str) -> tuple[str, int]:
    """Return (comma-joined published platform display names, count) for ``pitch_subject``.

    Delegates to `infrastructure.publishing.status_report.compile_publishing_status`
    — the SAME function every project's README publishing-status block is
    generated from — rather than re-deriving a naive count from raw config
    keys. A prior version of this function counted `doi` and `version_doi` as
    two separate "platforms" (both are Zenodo) and never credited
    `github_repository` at all; it coincidentally summed to the same total as
    the real count on template_template's current config, but for the wrong
    reason, and the two would diverge the moment that config changed (red-team
    finding, 2026-07-09). Naming the actual published platforms (not just a
    count) also lets deck content list exactly the right platforms, instead of
    a hand-typed prose list that can drift out of sync with the number.
    """
    subject_root = repo_root / "projects" / "templates" / _validate_project_name(pitch_subject)
    report = compile_publishing_status(subject_root)
    published = [p for p in report.platforms if p.state is PublicationState.PUBLISHED]
    names = [_display_platform_name(p.name, p.reference) for p in published]
    return ", ".join(names), len(names)


def build_deck_tokens(repo_root: Path, pitch_subject: str = "template_template") -> dict[str, str]:
    """Return the resolved ``{{TOKEN}}`` values for the ``pitch_subject`` deck.

    Args:
        repo_root: The template monorepo root (contains ``infrastructure/``).
        pitch_subject: Directory name under ``projects/templates/`` this deck
            pitches. Defaults to ``template_template``, the flagship content.
    """
    exemplar_names = public_project_names(repo_root)
    exemplar_count = len(exemplar_names)

    subject_config = _read_pitch_subject_config(repo_root, pitch_subject)
    paper = subject_config.get("paper") or {}
    publication = subject_config.get("publication") or {}
    metadata = subject_config.get("metadata") or {}

    published_platform_names, published_count = _published_platform_names_and_count(repo_root, pitch_subject)

    test_count, coverage_pct = _read_counts_row(repo_root, pitch_subject)

    tokens: dict[str, str] = {
        "PITCH_SUBJECT_NAME": pitch_subject,
        "PITCH_SUBJECT_TITLE": str(paper.get("title", pitch_subject)),
        "PITCH_SUBJECT_VERSION": str(paper.get("version", "")),
        "PITCH_SUBJECT_LICENSE": str(metadata.get("license", "")),
        "PITCH_SUBJECT_DOI": str(publication.get("doi", "")),
        "PITCH_SUBJECT_GITHUB": str(publication.get("github_repository", "")),
        "PITCH_SUBJECT_TEST_COUNT": test_count,
        "PITCH_SUBJECT_COVERAGE_PCT": coverage_pct,
        "PITCH_SUBJECT_PUBLISHED_PLATFORM_COUNT": str(published_count),
        "PITCH_SUBJECT_PUBLISHED_PLATFORM_NAMES": published_platform_names,
        "EXEMPLAR_COUNT": str(exemplar_count),
        "EXEMPLAR_COUNT_PLUS_ONE": str(exemplar_count + 1),
        "SECOND_EXEMPLAR_NAME": _second_example_name(exemplar_names, pitch_subject),
        "EXEMPLAR_ROSTER": _exemplar_roster(exemplar_names),
        "PITCH_DECK_DOI_STATUS": _read_own_deck_doi_status(repo_root),
    }
    tokens.update(build_infra_tokens(repo_root))
    return tokens


def _second_example_name(exemplar_names: list[str], pitch_subject: str) -> str:
    """Return a second real exemplar name (not ``pitch_subject``) as a case-study reference."""
    for qualified in sorted(exemplar_names):
        short_name = qualified.rsplit("/", 1)[-1]
        if short_name != pitch_subject:
            return short_name
    raise ValueError(
        f"No second exemplar distinct from {pitch_subject!r} found in the public roster — "
        "cannot honestly claim a case study without one."
    )


__all__ = ["build_deck_tokens"]
