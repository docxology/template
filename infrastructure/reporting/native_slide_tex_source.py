"""Closed source-only cross-deck numbers and portable Beamer writer reconstruction."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from infrastructure.rendering._slides_crossref import (
    bind_displayed_equation_numbers,
    resolve_cross_deck_references,
    transform_tex_prose,
)

SECTION = re.compile(
    r"(?P<escaped_join>\\textasciitilde\{\})?(?P<authored_open>\()?"
    r"\\(?P<command>eqref|ref)\{(?P<label>sec:[^{}]+)\}"
)


def resolve_source_slide_references(tex: str, config: Any, numbers: dict[str, str] | None) -> str:
    """Reproduce current source SDK semantics using admitted source-only numbers.

    The enclosing whole-source scientific reference supplies this exact map;
    candidate AUX paths and recorded status summaries provide no authority.
    """
    numbers = {} if numbers is None else numbers
    if len(numbers) > 10000 or any(
        not isinstance(k, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.\-]*", v) for k, v in numbers.items()
    ):
        raise ValueError("slide source reference number map is not a finite original literal map")
    accessible = config.slides_profile == "accessible"
    if accessible:
        tex = bind_displayed_equation_numbers(tex, numbers)

    def sections(segment: str) -> str:
        def replace(match: re.Match[str]) -> str:
            label = match["label"]
            number = numbers.get(label)
            if accessible and number is not None:
                number = number if match["command"] == "ref" else f"({number})"
                return ("~" if match["escaped_join"] else "") + (match["authored_open"] or "") + number
            if accessible:
                raise ValueError(f"independent whole-source section number required for {label}")
            return match[0]

        return SECTION.sub(replace, segment)

    tex = transform_tex_prose(tex, sections)
    tex, _, unresolved = resolve_cross_deck_references(tex, numbers, resolve_local=accessible)
    if any(not label.startswith("sec:") for label in unresolved):
        raise ValueError("independent whole-source numeric reference map is incomplete")

    def fallback(segment: str) -> str:
        def replace(match: re.Match[str]) -> str:
            join = "~" if match["escaped_join"] else ""
            opening = match["authored_open"] or ""
            if accessible:
                raise ValueError("accessible source reference remained unresolved")
            label = match["label"].replace("_", r"\_")
            return join + opening + rf"\texttt{{{label}}}"

        return SECTION.sub(replace, segment)

    return transform_tex_prose(tex, fallback)


def normalize_writer_path(tex: bytes, manuscript: Path, figures: Path) -> bytes:
    """Only admitted source resource roots may relocate during portable replay."""
    text = tex.decode()
    for path, token in ((manuscript, "<SOURCE-MANUSCRIPT>"), (figures, "<SOURCE-FIGURES>")):
        text = text.replace(path.as_posix(), token)
    return text.encode()


def source_slide_reference_displays(
    tex: str,
    source_aux: Path,
    contract: Any,
    numbers: dict[str, str] | None,
    supplied: dict[str, str] | None,
    *,
    archive_section_labels: tuple[str, ...] = (),
) -> dict[str, str]:
    """Bind original reference identities to genuine source-only native labels.

    Archive section fallbacks and local deck counters reproduce current SDK
    behavior. Only the newly compiled source AUX may supply local counters.
    Whole-manuscript source-only numbers supply foreign labels.
    """
    import json
    from infrastructure.reporting.native_format_pdf_source_labels import (
        original_source_labels,
        reconstruct_source_reference_labels,
    )
    from infrastructure.reporting.native_slide_source import CROSSREF_PREFIXES

    local = {row["label"] for row in original_source_labels(tex.encode())}
    allowed = tuple(label for label in archive_section_labels if label in local)
    label_observation = reconstruct_source_reference_labels(
        tex.encode(),
        source_aux.read_bytes(),
        requested_labels=tuple(sorted(local - set(allowed))),
        allowed_unnumbered_labels=allowed,
    )
    native = label_observation["label_numbers"]
    result = dict(supplied or {})
    for row in contract.occurrences:
        if row.kind != "reference":
            continue
        targets = json.loads(row.target) if row.source_start is None else [row.target]
        for label in targets:
            if not label.startswith(CROSSREF_PREFIXES) and row.source_start is None:
                continue
            if label.startswith("sec:") and (label in local or label not in (numbers or {})):
                result[label] = label
            else:
                number = native.get(label) if label in local else (numbers or {}).get(label)
                if number is None:
                    raise ValueError(f"original source-only slide reference number required for {label}")
                result[label] = number
    return result


def archive_source_section_labels(ast: bytes) -> tuple[str, ...]:
    """Exact current Pandoc Header identifier census for archive fallback policy."""
    import json

    labels = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            if value.get("t") == "Header":
                label = value["c"][1][0]
                if isinstance(label, str) and label.startswith("sec:"):
                    labels.append(label)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(json.loads(ast))
    if len(labels) != len(set(labels)):
        raise ValueError("original archive source repeats a section-label declaration")
    return tuple(labels)
