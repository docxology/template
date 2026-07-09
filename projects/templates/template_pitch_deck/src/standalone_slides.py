"""Per-slide standalone GitHub pages + the QR deep-links that point at them.

Each slide in a rendered deck gets its own small, standalone Markdown file
under ``output/slides_standalone/{pitch_subject}_{length}/slide_NN.md`` —
real content (title, body, citation, back-links to the full deck), not a
redirect stub. `attach_qr_urls` then computes a deterministic GitHub blob URL
for each slide's own file and returns a new `DeckContent` with `Slide.qr_url`
populated, so `infrastructure.rendering.{slide_deck,pptx_deck}` can draw a
scannable QR code on every slide: scan a photo of a projected/printed slide,
land on that exact slide's standalone page, complete with the citation trail
back to the repo file that backs its claim.

This is the diligence system's deep-link taken one step further — `source`
citations point *out* to evidence; a slide's own QR points *at* the slide
itself, so a viewer can always find "was this actually said, and can I verify
it" starting from nothing but a photo of the slide.
"""

from __future__ import annotations

import dataclasses
import re
import shutil
from pathlib import Path

from infrastructure.rendering.slide_deck import DeckContent, Slide, source_url

STANDALONE_SUBDIR = "slides_standalone"

#: `pitch_subject`/`length` are always a single path segment. Enforced before
#: any path construction — `Path.relative_to()` alone does not reject ".."
#: segments (it is a purely lexical prefix check), so a future caller passing
#: an attacker- or config-controlled `pitch_subject` could otherwise write
#: outside `output/` entirely (red-team finding, 2026-07-09; verified via
#: direct reproduction with `pitch_subject="../../../../tmp/pwned"`).
_SAFE_PATH_SEGMENT_RE = re.compile(r"^[\w-]+$")


def _validate_path_segment(value: str, *, what: str) -> str:
    if not _SAFE_PATH_SEGMENT_RE.match(value):
        raise ValueError(f"Not a valid {what} (must be a single path segment): {value!r}")
    return value


def standalone_slide_relpath(pitch_subject: str, length: str, index: int) -> str:
    """Repo-relative path (posix-style) to one slide's standalone Markdown file."""
    _validate_path_segment(pitch_subject, what="pitch_subject")
    _validate_path_segment(length, what="length")
    return (
        f"projects/templates/template_pitch_deck/output/{STANDALONE_SUBDIR}/"
        f"{pitch_subject}_{length}/slide_{index:02d}.md"
    )


def _slide_body_markdown(slide: Slide) -> str:
    """Render the kind-specific body of one slide as Markdown."""
    if slide.kind == "stat":
        value = slide.stat_value or (slide.bullets[0] if slide.bullets else "")
        lines = [f"## {value}"]
        if slide.stat_label:
            lines.append("")
            lines.append(slide.stat_label)
        return "\n".join(lines)

    if slide.kind == "quote":
        lines = [f"> {slide.quote_text}"]
        if slide.quote_attribution:
            lines.append("")
            lines.append(f"— {slide.quote_attribution}")
        return "\n".join(lines)

    if slide.bullets:
        return "\n".join(f"- {bullet}" for bullet in slide.bullets)

    return "*(no body content — section/title slide)*"


def standalone_slide_markdown(
    slide: Slide,
    *,
    index: int,
    total: int,
    length: str,
    pitch_subject: str,
    source_base_url: str,
) -> str:
    """Render one slide's standalone Markdown page."""
    lines: list[str] = []
    title = slide.title or f"({slide.kind} slide)"
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"*Slide {index} of {total} — {pitch_subject} pitch, {length} deck — kind: `{slide.kind}`*")
    lines.append("")
    lines.append(_slide_body_markdown(slide))
    lines.append("")
    lines.append("---")
    lines.append("")

    if slide.source:
        url = source_url(slide.source, source_base_url)
        if url:
            lines.append(f"**Source:** [{slide.source}]({url})")
        else:
            lines.append(f"**Source:** `{slide.source}`")
        lines.append("")

    lines.append(
        f"**Full deck:** "
        f"[PDF](../../pdf/{pitch_subject}_pitch_{length}.pdf) · "
        f"[PPTX](../../pptx/{pitch_subject}_pitch_{length}.pptx)"
    )
    lines.append(
        f"**Deck content source:** [manuscript/deck_content_{length}.yaml](../../../manuscript/deck_content_{length}.yaml)"
    )
    lines.append("")
    lines.append(
        "*This page is generated — it exists so a QR code on the rendered slide "
        "can point somewhere real and citable on GitHub, not just at the deck as "
        "a whole. Regenerate via `scripts/20_render_decks.py`; do not hand-edit.*"
    )
    return "\n".join(lines) + "\n"


def write_standalone_slides(
    deck: DeckContent,
    *,
    length: str,
    pitch_subject: str,
    project_root: Path,
    source_base_url: str,
) -> list[Path]:
    """Write one standalone Markdown file per slide; return the written paths.

    Clears any pre-existing files under this length's own standalone
    directory first — a deck that shrinks between regenerations (a slide
    removed) would otherwise leave a stale, orphaned `slide_NN.md` on disk
    that no longer corresponds to any real slide, but still looks like a
    legitimately generated, citable page (red-team finding, 2026-07-09).
    """
    _validate_path_segment(pitch_subject, what="pitch_subject")
    _validate_path_segment(length, what="length")
    total = len(deck.slides)

    standalone_dir = project_root / "output" / STANDALONE_SUBDIR / f"{pitch_subject}_{length}"
    if standalone_dir.is_dir():
        shutil.rmtree(standalone_dir)
    standalone_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for index, slide in enumerate(deck.slides, start=1):
        out_path = standalone_dir / f"slide_{index:02d}.md"
        content = standalone_slide_markdown(
            slide,
            index=index,
            total=total,
            length=length,
            pitch_subject=pitch_subject,
            source_base_url=source_base_url,
        )
        out_path.write_text(content, encoding="utf-8")
        written.append(out_path)
    return written


def attach_qr_urls(
    deck: DeckContent,
    *,
    length: str,
    pitch_subject: str,
    source_base_url: str,
) -> DeckContent:
    """Return a new `DeckContent` with every slide's `qr_url` set to its own
    standalone page's deterministic GitHub URL.

    Pure function: `Slide` is frozen, so each slide is replaced via
    `dataclasses.replace` rather than mutated.
    """
    if not source_base_url:
        return deck

    new_slides = []
    for index, slide in enumerate(deck.slides, start=1):
        relpath = standalone_slide_relpath(pitch_subject, length, index)
        qr_url = source_base_url.rstrip("/") + "/" + relpath
        new_slides.append(dataclasses.replace(slide, qr_url=qr_url))

    return DeckContent(
        title=deck.title,
        subtitle=deck.subtitle,
        slides=tuple(new_slides),
        metadata=dict(deck.metadata),
    )


__all__ = [
    "STANDALONE_SUBDIR",
    "standalone_slide_relpath",
    "standalone_slide_markdown",
    "write_standalone_slides",
    "attach_qr_urls",
]
