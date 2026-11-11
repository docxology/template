"""Strict opt-in paper layout and deterministic whole-manuscript composition."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Mapping

import yaml

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._pdf_title_page_config import _rendering_options
from infrastructure.rendering._pdf_title_page_images import _cover_image_alt, _cover_image_path
from infrastructure.rendering._slides_accessibility_image_io import _resolve_local_image
from infrastructure.transmission.transmission_bookends import BEGIN_FILENAME, END_FILENAME

# The markers are raw writer instructions, never reader-facing prose.
MARKER: Final = "template-paper-frontmatter"
WEB_ALGORITHM: Final = "web-renderer-paper-frontmatter-v1"
SHARED_ALGORITHM: Final = "shared-paper-frontmatter-markdown-v1"
type ConfigValue = str | int | float | bool | None | list[ConfigValue] | dict[str, ConfigValue]
_METADATA: Final = frozenset(
    {"preamble.md", "agents.md", "readme.md", "syntax.md", "manuscript_status.md", "complete.md"}
)
_PAGE = re.compile(
    r"\A# (?P<heading>[^\n]+)\n\s*\n!\[(?P<caption>.+)\]\((?P<image>[^\s)]+)\)"
    r"\{#(?P<label>fig:[A-Za-z0-9:_-]+)(?:[^}\n]*)\}\s*\Z",
    re.DOTALL,
)


@dataclass(frozen=True, slots=True)
class PaperPage:
    """One complete authored heading and captioned figure."""

    source: Path
    heading: str
    caption: str
    label: str
    image: Path


@dataclass(frozen=True, slots=True)
class PaperLayout:
    """A single ordered source partition; complete inputs retain every derivative."""

    manuscript_dir: Path
    frontmatter: tuple[PaperPage, ...]
    body: tuple[Path, ...]

    @property
    def complete(self) -> tuple[Path, ...]:
        return tuple(page.source for page in self.frontmatter) + self.body


def declared_frontmatter(settings: Mapping[str, ConfigValue] | None) -> tuple[str, ...]:
    """Parse opt-in configuration, preserving absent-field legacy behavior."""
    if not settings:
        return ()
    paper = settings.get("paper")
    if not isinstance(paper, dict) or "frontmatter" not in paper:
        return ()
    raw = paper["frontmatter"]
    if not isinstance(raw, list) or any(not isinstance(v, str) or not v.strip() for v in raw):
        raise RenderingError("paper.frontmatter must be a list of non-empty relative Markdown paths")
    names: list[str] = []
    for value in raw:
        if not isinstance(value, str):
            raise RenderingError("paper.frontmatter entry must be a string")
        path = Path(value)
        if (
            path.is_absolute()
            or ".." in path.parts
            or path.as_posix() != value
            or "\\" in value
            or path.suffix != ".md"
            or path.name.lower() in _METADATA
        ):
            raise RenderingError(f"paper.frontmatter has an unsafe or metadata path: {value}")
        names.append(value)
    if len(set(names)) != len(names):
        raise RenderingError("paper.frontmatter has duplicate paths")
    if names:
        book = settings.get("book")
        publication = settings.get("publication")
        transmission = publication.get("transmission_bookends") if isinstance(publication, dict) else None
        if (isinstance(book, dict) and book.get("title")) or (
            isinstance(transmission, dict) and transmission.get("enabled", False)
        ):
            raise RenderingError("paper.frontmatter is incompatible with book titles or transmission bookends")
    return tuple(names)


def _regular_confined(path: Path, root: Path) -> tuple[int, int]:
    if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise RenderingError(f"paper.frontmatter source is missing or escapes its manuscript: {path}")
    relative = path.absolute().relative_to(root.absolute())
    if any((root / Path(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts) + 1)):
        raise RenderingError(f"paper.frontmatter refuses symlink sources: {path}")
    info = path.stat()
    return info.st_dev, info.st_ino


def resolve_paper_layout(manuscript_dir: Path, source_files: tuple[Path, ...]) -> PaperLayout:
    """Admit the exact supplied input inventory before either combined writer runs."""
    config_file = manuscript_dir / "config.yaml"
    settings = yaml.safe_load(config_file.read_text(encoding="utf-8")) if config_file.is_file() else None
    if settings is None:
        settings = {}
    if not isinstance(settings, dict):
        raise RenderingError("manuscript configuration must be a mapping")
    names = declared_frontmatter(settings)
    if not names:
        return PaperLayout(manuscript_dir, (), source_files)
    if any(
        (manuscript_dir / name).exists() or (manuscript_dir / name).is_symlink()
        for name in (BEGIN_FILENAME, END_FILENAME)
    ):
        raise RenderingError("paper.frontmatter refuses stray transmission bookends")
    project = (
        manuscript_dir.parent.parent if manuscript_dir.parent.name in {"output", "docs"} else manuscript_dir.parent
    )
    image = _cover_image_path(settings, config_file)
    if image is not None and (
        not image.is_file()
        or image.is_symlink()
        or not image.resolve().is_relative_to(project.resolve())
        or not _cover_image_alt(settings)
    ):
        raise RenderingError("paper.frontmatter configured cover requires a confined real image and non-empty alt")
    identities: set[tuple[int, int]] = set()
    supplied: dict[Path, Path] = {}
    for path in source_files:
        identity = _regular_confined(path, manuscript_dir)
        if identity in identities:
            raise RenderingError("paper.frontmatter complete input inventory has duplicate physical sources")
        identities.add(identity)
        supplied[path.absolute()] = path
        content = path.read_text(encoding="utf-8")
        if MARKER in content or re.search(r"\bpaper-(?:frontmatter|body|cover)\b", content):
            raise RenderingError(f"paper.frontmatter reserved marker collision: {path}")
    pages: list[PaperPage] = []
    for name in names:
        path = manuscript_dir / name
        _regular_confined(path, manuscript_dir)
        if path.absolute() not in supplied:
            raise RenderingError(f"paper.frontmatter entry missing from complete inputs: {name}")
        content = path.read_text(encoding="utf-8")
        match = _PAGE.fullmatch(content)
        if match is None or content.count("![") != 1 or "\n#" in content:
            raise RenderingError(f"paper.frontmatter requires one heading and one complete captioned figure: {name}")
        resolved = _resolve_local_image(
            match["image"],
            source=str(path),
            heading=match["heading"],
            authorized_roots=(manuscript_dir, project / "output/figures"),
            figure_root=project / "output/figures",
        )
        if resolved is None or not resolved.path.is_file():
            raise RenderingError(f"paper.frontmatter figure missing: {match['image']}")
        image = resolved.path
        pages.append(PaperPage(supplied[path.absolute()], match["heading"], match["caption"], match["label"], image))
    if len({page.label for page in pages}) != len(pages):
        raise RenderingError("paper.frontmatter has duplicate figure labels")
    selected = {page.source for page in pages}
    return PaperLayout(manuscript_dir, tuple(pages), tuple(p for p in source_files if p not in selected))


def admit_paper_layout(
    manuscript_dir: Path,
    source_files: tuple[Path, ...],
    supplied: PaperLayout | None = None,
) -> PaperLayout:
    """Resolve current inputs and reject any stale or differently ordered layout.

    A supplied layout carries an ordered partition, not authority to skip current
    configuration and physical-source admission. Re-resolution also admits the
    current caption, label, heading and confined image before a writer runs.
    """
    current = resolve_paper_layout(manuscript_dir, source_files)
    if supplied is not None and supplied != current:
        raise RenderingError(
            "paper.frontmatter layout does not match the current configuration and supplied manuscript inputs"
        )
    return current


def compose_frontmatter(bodies: tuple[bytes, ...], count: int, separator: str) -> str:
    """Compose held ordered bytes identically for writers and provenance replay."""
    if count <= 0 or count > len(bodies):
        raise RenderingError("paper.frontmatter composition has an invalid partition")
    contents = tuple(body.decode("utf-8").rstrip() + "\n" for body in bodies)
    if any(MARKER in content or re.search(r"\bpaper-(?:frontmatter|body|cover)\b", content) for content in contents):
        raise RenderingError("paper.frontmatter composition has a reserved marker collision")
    pages = []
    for index, content in enumerate(contents[:count], 1):
        pages.append(
            f'```{{=html}}\n<div id="paper-frontmatter-{index}" class="paper-frontmatter-page">\n```\n\n'
            f"```{{=latex}}\n% {MARKER}-begin:{index}\n```\n\n{content}\n"
            f"```{{=latex}}\n% {MARKER}-end:{index}\n```\n\n```{{=html}}\n</div>\n```\n"
        )
    body_parts: list[str] = []
    for index, content in enumerate(contents[count:]):
        if index and separator:
            body_parts.append(separator)
        body_parts.append(content)
    body = "\n\n".join(body_parts)
    return (
        '```{=html}\n<div id="paper-frontmatter" class="paper-frontmatter">\n```\n\n'
        + "\n\n".join(pages)
        + '\n```{=html}\n</div>\n<div id="paper-body" class="paper-body">\n```\n\n'
        + f"```{{=latex}}\n% {MARKER}-body\n```\n\n"
        + body
        + "\n```{=html}\n</div>\n```\n"
    )


def combine_layout(layout: PaperLayout, *, web: bool = False) -> str:
    """Read an admitted layout once into the opt-in deterministic composition."""
    layout = admit_paper_layout(layout.manuscript_dir, layout.complete, layout)
    settings = yaml.safe_load((layout.manuscript_dir / "config.yaml").read_text(encoding="utf-8"))
    separator = (
        "\n---\n\n"
        if web
        else ("\n```{=latex}\n\\newpage\n```\n" if _rendering_options(settings)["section_breaks"] else "")
    )
    return compose_frontmatter(tuple(path.read_bytes() for path in layout.complete), len(layout.frontmatter), separator)
