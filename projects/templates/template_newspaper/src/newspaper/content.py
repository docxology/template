"""Editorial content model and YAML loaders for an edition.

The newspaper's content lives as data, not code: an edition manifest
(``content/edition.yaml``) carries the masthead and the ordered page list, and
one file per page (``content/pages/*.yaml``) carries that page's stories, boxes
and figures. This module parses those files into a typed object graph that the
layout engine consumes. Swapping in a different edition is a pure data edit —
the engine never changes.

The parser is deliberately forgiving about *shape* (a body block may be a bare
string or a tagged mapping) but strict about *structure* (an unknown page
template or a missing required edition field raises ``ValueError`` naming the
offending value). This mirrors the strict-loader contract used across the
sibling templates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Page templates select inside-page *furniture*. Only ``front`` (nameplate) and
# ``classified`` (dense unboxed grid) change the layout path (see layout.py);
# ``standard``/``opinion``/``feature`` share the standard inside-page furniture
# and act as semantic/section tags — their distinct look on A4/A5 comes from
# *content* (boxes, mastheads, jumps), not from the template branch.
VALID_TEMPLATES: frozenset[str] = frozenset({"front", "standard", "opinion", "feature", "classified"})
VALID_LEVELS: frozenset[str] = frozenset({"lead", "primary", "secondary", "minor"})
VALID_BLOCK_KINDS: frozenset[str] = frozenset({"p", "subhead", "pull"})
VALID_BOX_KINDS: frozenset[str] = frozenset(
    {"index", "weather", "tides", "staff", "briefs", "table", "calendar", "generic", "almanac", "display"}
)


@dataclass
class Block:
    """One body element of a story: a paragraph, a subhead, or a pull quote."""

    kind: str = "p"
    text: str = ""
    attribution: str = ""

    def __post_init__(self) -> None:
        if self.kind not in VALID_BLOCK_KINDS:
            raise ValueError(f"unknown block kind {self.kind!r}; allowed: {sorted(VALID_BLOCK_KINDS)}")


@dataclass
class Figure:
    """A photo / illustration / chart placed in the flow, with cutline.

    The image is fit to the width of the column it flows into (single-column
    measure). Multi-column spanning is intentionally not supported by the flow
    model — see ISA "Out of Scope".
    """

    path: str
    caption: str = ""
    credit: str = ""
    height: float = 150.0  # points; height hint for the missing-image placeholder

    def __post_init__(self) -> None:
        if not self.path:
            raise ValueError("figure requires a non-empty 'path'")
        if self.height <= 0:
            raise ValueError(f"figure height must be > 0, got {self.height}")


@dataclass
class Story:
    """A single article."""

    headline: str
    kicker: str = ""
    deck: str = ""
    byline: str = ""
    dateline: str = ""
    level: str = "secondary"
    body: list[Block] = field(default_factory=list)
    jump: str = ""
    figure: Figure | None = None
    drop_cap: bool = False

    def __post_init__(self) -> None:
        if self.level not in VALID_LEVELS:
            raise ValueError(f"unknown story level {self.level!r}; allowed: {sorted(VALID_LEVELS)}")


@dataclass
class Box:
    """A boxed, ruled module: index, weather, tide table, staff masthead, etc."""

    kind: str
    title: str = ""
    items: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    body: list[Block] = field(default_factory=list)
    footnote: str = ""

    def __post_init__(self) -> None:
        if self.kind not in VALID_BOX_KINDS:
            raise ValueError(f"unknown box kind {self.kind!r}; allowed: {sorted(VALID_BOX_KINDS)}")


VALID_AD_BORDERS: frozenset[str] = frozenset({"box", "double", "thick", "none"})


@dataclass
class Ad:
    """A display advertisement — color-capable, bordered, centered.

    Newspapers are monochrome editorial type wrapped around *color advertising*.
    An ``Ad`` flows like any boxed module but supports a background tint, an
    accent (border + headline) color, an optional graphic, and ad-style
    centered copy, so the template can demonstrate real color display ads
    alongside the black-and-white news.
    """

    sponsor: str
    tagline: str = ""
    body: list[Block] = field(default_factory=list)
    contact: str = ""
    graphic: str = ""  # optional image path (color or mono)
    background: str = ""  # hex fill, e.g. "#FBE9D0" (empty = paper white)
    accent: str = ""  # hex for border + sponsor name (empty = ink)
    border: str = "box"  # box | double | thick | none
    height: float = 0.0  # optional fixed height hint in points
    graphic_height: float = 70.0

    def __post_init__(self) -> None:
        if not self.sponsor:
            raise ValueError("ad requires a 'sponsor'")
        if self.border not in VALID_AD_BORDERS:
            raise ValueError(f"unknown ad border {self.border!r}; allowed: {sorted(VALID_AD_BORDERS)}")


@dataclass
class Page:
    """One printed page: furniture metadata plus rail and main column content."""

    number: int
    section: str = "A"
    department: str = ""
    template: str = "standard"
    columns: int = 5
    rail: bool = False
    lead: Story | None = None
    rail_items: list[Box | Story | Ad] = field(default_factory=list)
    main_items: list[Story | Box | Figure | Ad] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.number < 1:
            raise ValueError(f"page number must be >= 1, got {self.number}")
        if self.template not in VALID_TEMPLATES:
            raise ValueError(
                f"page {self.number}: unknown template {self.template!r}; allowed: {sorted(VALID_TEMPLATES)}"
            )
        if self.columns < 1:
            raise ValueError(f"page {self.number}: columns must be >= 1, got {self.columns}")


@dataclass
class Edition:
    """A complete edition: masthead identity plus the ordered pages."""

    nameplate: str
    city: str
    state: str
    date: str
    volume: str = ""
    number: str = ""
    price: str = ""
    established: str = ""
    motto: str = ""
    edition_label: str = ""
    weather_strip: str = ""
    pages: list[Page] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Reject duplicate folios before rendering can overwrite evidence.

        The empty edition remains constructible for renderer smoke tests, but
        every page in a non-empty edition must have a unique positive number.
        Duplicate folios are otherwise especially dangerous: ``RenderResult``
        stores oversets by page number, so a later duplicate could hide the
        earlier page's failure in machine-readable evidence.
        """
        numbers = [page.number for page in self.pages]
        if len(numbers) != len(set(numbers)):
            duplicates = sorted({number for number in numbers if numbers.count(number) > 1})
            raise ValueError(f"duplicate page number(s): {duplicates}")

    @property
    def page_count(self) -> int:
        """Return the total number of pages."""
        return len(self.pages)


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _parse_block(raw: Any) -> Block:
    if isinstance(raw, str):
        return Block(kind="p", text=raw)
    if isinstance(raw, dict):
        if "subhead" in raw:
            return Block(kind="subhead", text=str(raw["subhead"]))
        if "pull" in raw:
            pull = raw["pull"] or {}
            if isinstance(pull, str):
                return Block(kind="pull", text=pull)
            if isinstance(pull, dict):
                return Block(kind="pull", text=str(pull.get("quote", "")), attribution=str(pull.get("by", "")))
            raise ValueError(f"'pull' block must be a string or mapping, got {type(pull).__name__}")
        if "p" in raw:
            return Block(kind="p", text=str(raw["p"]))
    raise ValueError(f"cannot parse body block: {raw!r}")


def _parse_body(raw: Any) -> list[Block]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError(f"story body must be a list, got {type(raw).__name__}")
    return [_parse_block(b) for b in raw]


def _parse_figure(raw: Any) -> Figure | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError(f"figure must be a mapping, got {type(raw).__name__}")
    if "path" not in raw:
        raise ValueError(f"figure requires a 'path' field; got keys {sorted(raw)}")
    try:
        height = float(raw.get("height", 150.0))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"figure 'height' must be a number, got {raw.get('height')!r}") from exc
    return Figure(
        path=str(raw["path"]),
        caption=str(raw.get("caption", "")),
        credit=str(raw.get("credit", "")),
        height=height,
    )


def _parse_story(raw: dict[str, Any]) -> Story:
    if not isinstance(raw, dict):
        raise ValueError(f"story must be a mapping, got {type(raw).__name__}")
    if "headline" not in raw:
        raise ValueError(f"story requires a 'headline' field; got keys {sorted(raw)}")
    return Story(
        headline=str(raw["headline"]),
        kicker=str(raw.get("kicker", "")),
        deck=str(raw.get("deck", "")),
        byline=str(raw.get("byline", "")),
        dateline=str(raw.get("dateline", "")),
        level=str(raw.get("level", "secondary")),
        body=_parse_body(raw.get("body")),
        jump=str(raw.get("jump", "")),
        figure=_parse_figure(raw.get("figure")),
        drop_cap=bool(raw.get("drop_cap", False)),
    )


def _parse_box(raw: dict[str, Any]) -> Box:
    if not isinstance(raw, dict):
        raise ValueError(f"box item must be a mapping, got {type(raw).__name__}")
    if "box" not in raw:
        raise ValueError(f"box requires a 'box' field; got keys {sorted(raw)}")

    items_raw = raw.get("items")
    if items_raw is not None and not isinstance(items_raw, list):
        raise ValueError(f"box 'items' must be a list, got {type(items_raw).__name__}")
    columns_raw = raw.get("columns")
    if columns_raw is not None and not isinstance(columns_raw, list):
        raise ValueError(f"box 'columns' must be a list, got {type(columns_raw).__name__}")
    rows_raw = raw.get("rows")
    if rows_raw is not None and not isinstance(rows_raw, list):
        raise ValueError(f"box 'rows' must be a list, got {type(rows_raw).__name__}")
    rows: list[list[str]] = []
    for index, row in enumerate(rows_raw or []):
        if not isinstance(row, list):
            raise ValueError(f"box row {index} must be a list, got {type(row).__name__}")
        rows.append([str(cell) for cell in row])

    return Box(
        kind=str(raw["box"]),
        title=str(raw.get("title", "")),
        items=[str(x) for x in (items_raw or [])],
        rows=rows,
        columns=[str(c) for c in (columns_raw or [])],
        body=_parse_body(raw.get("body")),
        footnote=str(raw.get("footnote", "")),
    )


def _parse_ad(raw: Any) -> Ad:
    if not isinstance(raw, dict):
        raise ValueError(f"ad must be a mapping, got {type(raw).__name__}")
    if "sponsor" not in raw:
        raise ValueError(f"ad requires a 'sponsor' field; got keys {sorted(raw)}")
    try:
        height = float(raw.get("height", 0.0))
        graphic_height = float(raw.get("graphic_height", 70.0))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"ad height fields must be numbers: {exc}") from exc
    return Ad(
        sponsor=str(raw["sponsor"]),
        tagline=str(raw.get("tagline", "")),
        body=_parse_body(raw.get("body")),
        contact=str(raw.get("contact", "")),
        graphic=str(raw.get("graphic", "")),
        background=str(raw.get("background", "")),
        accent=str(raw.get("accent", "")),
        border=str(raw.get("border", "box")),
        height=height,
        graphic_height=graphic_height,
    )


def _parse_item(raw: dict[str, Any]) -> Story | Box | Figure | Ad:
    """Dispatch a main/rail item by its discriminator key."""
    if not isinstance(raw, dict):
        raise ValueError(f"page item must be a mapping, got {type(raw).__name__}")
    if "ad" in raw:
        return _parse_ad(raw["ad"])
    if "box" in raw:
        return _parse_box(raw)
    if "figure" in raw and "headline" not in raw:
        fig = _parse_figure(raw["figure"])
        assert fig is not None
        return fig
    if "headline" in raw:
        return _parse_story(raw)
    raise ValueError(f"cannot classify page item (need 'headline', 'box', 'figure', or 'ad'): {sorted(raw)}")


def _parse_page(raw: dict[str, Any]) -> Page:
    if not isinstance(raw, dict):
        raise ValueError(f"page must be a mapping, got {type(raw).__name__}")
    lead_raw = raw.get("lead")
    if lead_raw is not None and not isinstance(lead_raw, dict):
        raise ValueError(f"page 'lead' must be a mapping, got {type(lead_raw).__name__}")
    lead = _parse_story(lead_raw) if lead_raw is not None else None
    if lead is not None:
        lead.level = "lead"

    rail_items: list[Box | Story | Ad] = []
    rail_raw = raw.get("rail")
    if rail_raw is not None and not isinstance(rail_raw, list):
        raise ValueError(f"page 'rail' must be a list, got {type(rail_raw).__name__}")
    rail_list = rail_raw or []
    for item in rail_list:
        parsed = _parse_item(item)
        if isinstance(parsed, Figure):
            raise ValueError(f"page {raw.get('number')}: figures are not allowed in the rail")
        rail_items.append(parsed)

    main_raw = raw.get("main")
    if main_raw is not None and not isinstance(main_raw, list):
        raise ValueError(f"page 'main' must be a list, got {type(main_raw).__name__}")
    main_items: list[Story | Box | Figure | Ad] = [_parse_item(it) for it in (main_raw or [])]

    if "number" not in raw:
        raise ValueError("page requires a 'number' field")
    try:
        number = int(raw["number"])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"page 'number' must be an integer, got {raw['number']!r}") from exc

    return Page(
        number=number,
        section=str(raw.get("section", "A")),
        department=str(raw.get("department", "")),
        template=str(raw.get("template", "standard")),
        columns=int(raw.get("columns", 5)),
        rail=bool(raw.get("rail_enabled", isinstance(raw.get("rail"), list))),
        lead=lead,
        rail_items=rail_items,
        main_items=main_items,
    )


def load_edition(content_dir: Path | str) -> Edition:
    """Load an :class:`Edition` from ``content/edition.yaml`` + ``content/pages/``."""
    content_dir = Path(content_dir)
    manifest_path = content_dir / "edition.yaml"
    if not manifest_path.exists():
        raise FileNotFoundError(f"edition manifest not found: {manifest_path}")

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    if not isinstance(manifest, dict):
        raise ValueError(f"{manifest_path} must be a YAML mapping at the top level")

    masthead = manifest.get("masthead") or {}
    for required in ("nameplate", "city", "state", "date"):
        if not masthead.get(required):
            raise ValueError(f"edition masthead missing required field: {required!r}")

    page_files = manifest.get("pages") or []
    if not isinstance(page_files, list) or not page_files:
        raise ValueError("edition manifest 'pages' must be a non-empty list of page filenames")

    pages: list[Page] = []
    pages_dir = content_dir / "pages"
    pages_root = pages_dir.resolve()
    seen_files: set[Path] = set()
    for fname in page_files:
        if not isinstance(fname, str) or not fname.strip():
            raise ValueError(f"edition manifest page filenames must be non-empty strings, got {fname!r}")
        requested_path = pages_dir / fname
        page_path = requested_path.resolve()
        try:
            page_path.relative_to(pages_root)
        except ValueError as exc:
            raise ValueError(f"page file {fname!r} must resolve inside the content/pages directory") from exc
        if page_path in seen_files:
            raise ValueError(f"duplicate page file in manifest: {fname!r}")
        seen_files.add(page_path)
        if not page_path.is_file():
            raise FileNotFoundError(f"page file referenced by manifest not found: {requested_path}")
        raw = yaml.safe_load(page_path.read_text(encoding="utf-8")) or {}
        if not isinstance(raw, dict):
            raise ValueError(f"{page_path} must be a YAML mapping at the top level")
        page = _parse_page(raw)
        if any(existing.number == page.number for existing in pages):
            raise ValueError(f"duplicate page number in manifest: {page.number}")
        pages.append(page)

    return Edition(
        nameplate=str(masthead["nameplate"]),
        city=str(masthead["city"]),
        state=str(masthead["state"]),
        date=str(masthead["date"]),
        volume=str(masthead.get("volume", "")),
        number=str(masthead.get("number", "")),
        price=str(masthead.get("price", "")),
        established=str(masthead.get("established", "")),
        motto=str(masthead.get("motto", "")),
        edition_label=str(masthead.get("edition_label", "")),
        weather_strip=str(masthead.get("weather_strip", "")),
        pages=pages,
    )


__all__ = [
    "Ad",
    "Block",
    "Box",
    "Edition",
    "Figure",
    "Page",
    "Story",
    "load_edition",
    "VALID_TEMPLATES",
    "VALID_LEVELS",
    "VALID_BOX_KINDS",
    "VALID_AD_BORDERS",
]
