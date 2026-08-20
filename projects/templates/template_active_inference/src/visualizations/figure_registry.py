"""Figure metadata registry (paths, captions, alt text)."""

from __future__ import annotations

import copy
import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path, PureWindowsPath
from tempfile import NamedTemporaryFile
from typing import Any

import yaml

from manuscript.hydrate import collect_malformed_token_names, format_variables, substitute_snake_case_tokens

logger = logging.getLogger(__name__)

ALLOWED_FIGURE_SUFFIXES = frozenset({".png"})


@dataclass(frozen=True)
class FigureSpec:
    """Data container for FigureSpec."""

    figure_id: str
    filename: str
    alt: str
    caption: str
    width: float = 0.9
    visual_role: str = ""
    evidence_role: str = ""
    paper_claim: str = ""


@dataclass(frozen=True)
class SectionFigureRef:
    """Data container for SectionFigureRef."""

    figure_id: str
    number: int | None = None
    caption_prefix: str = ""
    labeled: bool = True


def _figures_yaml_path(project_root: Path) -> Path:
    return project_root.resolve() / "figures.yaml"


@lru_cache(maxsize=64)
def _parse_figures_yaml_cached(path_str: str, payload: bytes) -> dict[str, Any]:
    """Parse exact registry bytes once per path/content pair.

    Figure-path validation is a high-fan-out dependency-graph operation.  Keying
    the cache on the payload itself avoids trusting mutable size/mtime metadata,
    while the path component keeps otherwise identical project copies isolated.
    Callers receive a deepcopy so they cannot mutate the cached parse tree.
    """
    del path_str
    return yaml.safe_load(payload.decode("utf-8")) or {}


def _load_figures_yaml(project_root: Path) -> dict[str, Any]:
    path = _figures_yaml_path(project_root)
    if path.is_symlink():
        raise ValueError(f"figure registry must not be a symlink: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"missing figure registry: {path}")
    return copy.deepcopy(_parse_figures_yaml_cached(str(path), path.read_bytes()))


def _validate_figure_filename(figure_id: str, value: object) -> str:
    filename = str(value)
    path = Path(filename)
    windows_path = PureWindowsPath(filename)
    if (
        not filename
        or path.is_absolute()
        or windows_path.is_absolute()
        or windows_path.drive
        or len(path.parts) != 1
        or path.name != filename
        or "\\" in filename
    ):
        raise ValueError(f"figure {figure_id!r} filename must be a basename: {filename!r}")
    if path.suffix.lower() not in ALLOWED_FIGURE_SUFFIXES:
        allowed = ", ".join(sorted(ALLOWED_FIGURE_SUFFIXES))
        raise ValueError(f"figure {figure_id!r} filename must use an allowed image suffix ({allowed}): {filename!r}")
    return filename


def _confined_figure_output_path(project_root: Path, figure_id: str, filename: str) -> Path:
    root = project_root.resolve()
    output_dir = root / "output"
    figures_dir = output_dir / "figures"
    target = figures_dir / filename
    for candidate in (output_dir, figures_dir, target):
        if candidate.is_symlink():
            raise ValueError(f"figure {figure_id!r} output path must not contain symlinks: {candidate}")
    resolved_dir = figures_dir.resolve(strict=False)
    resolved_target = target.resolve(strict=False)
    if resolved_target.parent != resolved_dir:
        raise ValueError(f"figure {figure_id!r} output path escapes output/figures: {filename!r}")
    return target


def load_figure_registry(project_root: Path) -> dict[str, FigureSpec]:
    """Load figure registry from a file."""
    raw = _load_figures_yaml(project_root)
    figures_raw = raw.get("figures") or {}
    registry: dict[str, FigureSpec] = {}
    for figure_id, entry in figures_raw.items():
        if not isinstance(entry, dict):
            logger.warning("figures.yaml entry %s is not a mapping; skipped", figure_id)
            continue
        fid = str(figure_id)
        filename = _validate_figure_filename(fid, entry.get("filename", f"{fid}.png"))
        _confined_figure_output_path(project_root, fid, filename)
        registry[fid] = FigureSpec(
            figure_id=fid,
            filename=filename,
            alt=str(entry.get("alt", fid)),
            caption=str(entry.get("caption", "")),
            width=float(entry.get("width", 0.9)),
            visual_role=str(entry.get("visual_role", "")),
            evidence_role=str(entry.get("evidence_role", "")),
            paper_claim=str(entry.get("paper_claim", "")),
        )
    if not registry:
        raise ValueError("figures.yaml must declare at least one figure entry")
    return registry


def load_section_figures(project_root: Path) -> dict[str, tuple[SectionFigureRef, ...]]:
    """Load section figures from a file."""
    raw = _load_figures_yaml(project_root)
    section_raw = raw.get("section_figures") or {}
    mapping: dict[str, tuple[SectionFigureRef, ...]] = {}
    for section_id, entries in section_raw.items():
        refs: list[SectionFigureRef] = []
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, str):
                refs.append(SectionFigureRef(figure_id=entry))
            elif isinstance(entry, dict):
                refs.append(
                    SectionFigureRef(
                        figure_id=str(entry["id"]),
                        number=int(entry["number"]) if entry.get("number") is not None else None,
                        caption_prefix=str(entry.get("caption_prefix", "")),
                        labeled=bool(entry.get("labeled", True)),
                    )
                )
        mapping[str(section_id)] = tuple(refs)
    return mapping


def figure_output_path(project_root: Path, figure_id: str) -> Path:
    """Process figure output path."""
    spec = load_figure_registry(project_root)[figure_id]
    return _confined_figure_output_path(project_root, figure_id, spec.filename)


def _resolve_figure_field(
    figure_id: str,
    field_name: str,
    text: str,
    variables: dict[str, str],
) -> str:
    """Resolve one registry field, rejecting malformed or unknown tokens."""
    malformed = collect_malformed_token_names(text)
    if malformed:
        raise ValueError(f"malformed figure tokens for {figure_id}.{field_name}: {', '.join(malformed)}")
    resolved_value, unresolved = substitute_snake_case_tokens(text, variables)
    resolved = str(resolved_value)
    if unresolved:
        raise ValueError(f"unresolved figure tokens for {figure_id}.{field_name}: {', '.join(sorted(set(unresolved)))}")
    # A residual double-opening brace is always token syntax on this surface.
    # Do not reject a bare ``}}``: valid LaTeX such as ``A_{\text{true}}``
    # naturally ends with two closing braces.
    if "{{" in resolved:
        raise ValueError(f"malformed double-brace figure token for {figure_id}.{field_name}")
    return resolved


def render_figure_markdown(
    project_root: Path,
    figure_id: str,
    *,
    figure_number: int | None = None,
    caption_prefix: str = "",
    variables: dict[str, Any] | None = None,
    labeled: bool = True,
) -> str:
    # `figure_number` / `caption_prefix` are retained for signature back-compat but are
    # intentionally unused: pandoc-crossref owns figure numbering (single source of truth).
    # Hand-written "Figure N (section)." prefixes previously double-numbered every figure
    # against pandoc's auto-caption — see manuscript/SYNTAX.md and src/visualizations/AGENTS.md.
    """Render figure markdown."""
    del figure_number, caption_prefix
    spec = load_figure_registry(project_root)[figure_id]
    _confined_figure_output_path(project_root, figure_id, spec.filename)
    rel = f"../output/figures/{spec.filename}"
    alt = spec.alt
    caption = spec.caption
    if variables:
        formatted = format_variables(variables)
        alt = _resolve_figure_field(figure_id, "alt", alt, formatted)
        caption = _resolve_figure_field(figure_id, "caption", caption, formatted)
    width_pct = int(round(spec.width * 100))
    if labeled:
        # The caption is the image alt text, so pandoc-crossref emits exactly one
        # numbered "Figure N: {caption}". The verbose description rides along as fig-alt
        # for accessibility without producing a second caption.
        fig_alt = alt.replace('"', "'")
        return f'![{caption}]({rel}){{#fig:{figure_id} width={width_pct}% fig-alt="{fig_alt}"}}'
    # Reused figure: empty alt → unnumbered graphic (no second "Figure N"); cite the
    # canonical labeled occurrence so the reader is pointed at the authoritative number.
    return f"![]({rel}){{width={width_pct}%}}\n\n*Reproduced from [@fig:{figure_id}]. {caption}*"


def render_section_figures(
    project_root: Path,
    section_id: str,
    *,
    variables: dict[str, Any] | None = None,
) -> str:
    """Render section figures."""
    refs = load_section_figures(project_root).get(section_id, ())
    if not refs:
        return ""
    blocks = [
        render_figure_markdown(
            project_root,
            ref.figure_id,
            figure_number=ref.number,
            caption_prefix=ref.caption_prefix,
            variables=variables,
            labeled=ref.labeled,
        )
        for ref in refs
    ]
    return "\n\n".join(blocks)


def build_figure_registry_payload(
    project_root: Path,
    variables: dict[str, Any],
) -> dict[str, dict[str, object]]:
    """Build a fully hydrated registry keyed by ``fig:{id}`` labels.

    ``variables`` must be the final canonical manuscript-variable snapshot.
    Requiring it explicitly prevents the figure producer from silently binding
    the registry to an older on-disk snapshot.
    """
    if not variables:
        raise ValueError("canonical manuscript variables must be a non-empty mapping")
    registry = load_figure_registry(project_root)
    formatted = format_variables(variables)
    payload: dict[str, dict[str, object]] = {}
    for figure_id, spec in registry.items():
        label = f"fig:{figure_id}"
        payload[label] = {
            "label": label,
            "figure_id": figure_id,
            "filename": spec.filename,
            "alt": _resolve_figure_field(figure_id, "alt", spec.alt, formatted),
            "caption": _resolve_figure_field(figure_id, "caption", spec.caption, formatted),
            "width": spec.width,
            "visual_role": spec.visual_role,
            "evidence_role": spec.evidence_role,
            "paper_claim": spec.paper_claim,
            "generated_by": f"visualizations.figures::{figure_id}",
        }
    return payload


def write_figure_registry_json(project_root: Path, variables: dict[str, Any]) -> Path:
    """Atomically persist the hydrated registry from ``figures.yaml``.

    Resolution and JSON serialization finish before a temporary file is
    opened, so missing or unknown tokens leave any prior canonical registry
    byte-for-byte intact.
    """
    root = project_root.resolve()
    out = root / "output" / "figures" / "figure_registry.json"
    serialized = (
        json.dumps(
            build_figure_registry_payload(root, variables),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            "w",
            dir=out.parent,
            encoding="utf-8",
            prefix=f".{out.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(serialized)
            temporary_path = Path(handle.name)
        temporary_path.replace(out)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return out


def validate_figure_registry_json(project_root: Path, variables: dict[str, Any]) -> list[str]:
    """Return drift issues for the persisted hydrated registry."""
    root = project_root.resolve()
    path = root / "output" / "figures" / "figure_registry.json"
    if not path.is_file():
        return ["missing output/figures/figure_registry.json"]
    try:
        persisted: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"invalid output/figures/figure_registry.json: {exc}"]
    try:
        expected = build_figure_registry_payload(root, variables)
    except ValueError as exc:
        return [f"cannot hydrate output/figures/figure_registry.json: {exc}"]
    if persisted != expected:
        return ["output/figures/figure_registry.json is not hydrated from canonical manuscript variables"]
    return []
