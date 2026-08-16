"""Exact, format-neutral access to source-owned figure alternative text."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit

from infrastructure.core.exceptions import RenderingError


@dataclass(frozen=True)
class FigureAltRecord:
    """A normalized figure-registry record used at render boundaries."""

    label: str
    filename: str | None
    alt_text: str | None


@dataclass(frozen=True)
class FigureAltRegistry:
    """Label- and filename-addressable figure accessibility metadata."""

    path: Path
    records: tuple[FigureAltRecord, ...]

    @classmethod
    def load_optional(cls, registry_path: Path) -> FigureAltRegistry:
        """Load ``registry_path`` when present, accepting all validator shapes."""
        if not registry_path.is_file():
            return cls(path=registry_path, records=())
        try:
            payload = json.loads(registry_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RenderingError(
                f"Failed to load figure accessibility registry: {exc}",
                context={"registry": str(registry_path)},
            ) from exc

        raw_records = _registry_records(payload, registry_path)
        records: list[FigureAltRecord] = []
        seen_labels: set[str] = set()
        for fallback_label, record in raw_records:
            parsed = _parse_record(fallback_label, record, registry_path)
            if parsed is None:
                continue
            if parsed.label in seen_labels:
                raise RenderingError(
                    f"Duplicate figure registry label: {parsed.label}",
                    context={"registry": str(registry_path)},
                )
            seen_labels.add(parsed.label)
            records.append(parsed)
        return cls(path=registry_path, records=tuple(records))

    def by_label(self, label: str | None) -> FigureAltRecord | None:
        """Return the exact record for ``label``, if one exists."""
        if label is None:
            return None
        return next((record for record in self.records if record.label == label), None)

    def by_filename(self, filename: str | None) -> tuple[FigureAltRecord, ...]:
        """Return every record whose normalized filename equals ``filename``."""
        if filename is None:
            return ()
        return tuple(record for record in self.records if record.filename == filename)


def normalize_registry_filename(value: object) -> str | None:
    """Normalize a registry path to its path relative to ``output/figures``."""
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = unquote(value.strip()).replace("\\", "/")
    parsed = urlsplit(normalized)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        return None
    normalized = parsed.path
    while normalized.startswith("./"):
        normalized = normalized[2:]
    prefixes = (
        "../../output/figures/",
        "../output/figures/",
        "output/figures/",
        "../figures/",
        "figures/",
    )
    for prefix in prefixes:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
            break
    return _canonical_safe_relative_path(normalized)


def rendered_figure_filename(source: str) -> str | None:
    """Return a local rendered image path relative to ``output/figures``."""
    decoded = unquote(source).replace("\\", "/")
    parsed = urlsplit(decoded)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        return None
    normalized = parsed.path
    prefixes = ("../figures/", "./figures/", "figures/")
    for prefix in prefixes:
        if normalized.startswith(prefix):
            relative = normalized[len(prefix) :]
            return _canonical_safe_relative_path(relative)
    return None


def _canonical_safe_relative_path(value: str) -> str | None:
    if not value or "\x00" in value or value.startswith("/"):
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value:
        return None
    if any(part in {"", ".", ".."} for part in path.parts):
        return None
    return value


def require_record_alt(record: FigureAltRecord, *, rendered_target: str) -> str:
    """Return non-empty registry alt text or fail the current render."""
    if record.alt_text is not None:
        return record.alt_text
    raise RenderingError(
        f"Referenced figure is missing accessibility alt text: {record.label}",
        context={
            "registry": str(rendered_target),
            "figure": record.label,
        },
    )


def _registry_records(
    payload: object,
    registry_path: Path,
) -> list[tuple[str | None, dict[str, object]]]:
    if isinstance(payload, dict) and "figures" in payload:
        figures = payload["figures"]
        if not isinstance(figures, list):
            raise RenderingError(
                "Figure accessibility registry 'figures' field must be an array",
                context={"registry": str(registry_path)},
            )
        if any(not isinstance(item, dict) for item in figures):
            raise RenderingError(
                "Figure accessibility registry entries must be objects",
                context={"registry": str(registry_path)},
            )
        return [(None, item) for item in figures]
    if isinstance(payload, dict):
        if any(not str(label).startswith("fig:") or not isinstance(item, dict) for label, item in payload.items()):
            raise RenderingError(
                "Label-keyed figure accessibility registry requires fig:* object entries",
                context={"registry": str(registry_path)},
            )
        return [(str(label), item) for label, item in payload.items()]
    if isinstance(payload, list):
        if any(not isinstance(item, dict) for item in payload):
            raise RenderingError(
                "Figure accessibility registry entries must be objects",
                context={"registry": str(registry_path)},
            )
        return [(None, item) for item in payload]
    raise RenderingError(
        "Figure accessibility registry must be an object or array",
        context={"registry": str(registry_path), "top_level_type": type(payload).__name__},
    )


def _parse_record(
    fallback_label: str | None,
    record: dict[str, object],
    registry_path: Path,
) -> FigureAltRecord | None:
    explicit_label = record.get("label")
    if explicit_label is not None and (not isinstance(explicit_label, str) or not explicit_label.strip()):
        raise RenderingError(
            "Figure registry label must be a non-empty string",
            context={"registry": str(registry_path)},
        )
    label = explicit_label.strip() if isinstance(explicit_label, str) else fallback_label
    if label is None or not label.startswith("fig:"):
        raise RenderingError(
            "Figure registry entries require a non-empty fig:* label",
            context={"registry": str(registry_path)},
        )
    if fallback_label is not None and fallback_label.startswith("fig:") and fallback_label != label:
        raise RenderingError(
            f"Figure registry key/label mismatch: {fallback_label} != {label}",
            context={"registry": str(registry_path)},
        )

    declared_filenames = [record[field] for field in ("filename", "path") if field in record]
    normalized_filenames = [normalize_registry_filename(value) for value in declared_filenames]
    if not declared_filenames or any(value is None for value in normalized_filenames):
        raise RenderingError(
            f"Figure registry record requires a safe relative filename/path for {label}",
            context={"registry": str(registry_path)},
        )
    filenames = {value for value in normalized_filenames if value is not None}
    if len(filenames) > 1:
        raise RenderingError(
            f"Figure registry filename/path mismatch for {label}: {sorted(filenames)}",
            context={"registry": str(registry_path)},
        )
    filename = next(iter(filenames), None)

    # ``alt_text`` is the canonical Active Fedference/report-schema field.
    # ``alt`` remains a compact renderer-facing compatibility alias, and
    # nested metadata is accepted for older figure registries.
    top_alt = _normalized_alt(record.get("alt_text"))
    renderer_alt = _normalized_alt(record.get("alt"))
    metadata = record.get("metadata")
    metadata_alt = _normalized_alt(metadata.get("alt_text")) if isinstance(metadata, dict) else None
    declared_alts = [value for value in (top_alt, renderer_alt, metadata_alt) if value is not None]
    if len(set(declared_alts)) > 1:
        raise RenderingError(
            f"Figure registry has conflicting alternative text fields for {label}",
            context={"registry": str(registry_path)},
        )
    return FigureAltRecord(
        label=label,
        filename=filename,
        alt_text=top_alt or renderer_alt or metadata_alt,
    )


def _normalized_alt(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return " ".join(value.split())
