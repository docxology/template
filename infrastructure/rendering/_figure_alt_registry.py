"""Exact, format-neutral access to source-owned figure alternative text."""

from __future__ import annotations

import json
import re
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
    long_description: str | None = None
    exact_value_fallback: str | None = None
    exact_value_href: str | None = None


@dataclass(frozen=True)
class FigureExactValueArtifact:
    """Safe source-owned exact-value companion declared by a registry."""

    json_path: str
    markdown_path: str
    identifiers: tuple[str, ...]

    @property
    def web_markdown_href(self) -> str:
        """Return the deployed link from ``output/web`` or ``output/slides``."""

        prefix = "output/figures/"
        return "../figures/" + self.markdown_path.removeprefix(prefix)


@dataclass(frozen=True)
class FigureAltRegistry:
    """Label- and filename-addressable figure accessibility metadata."""

    path: Path
    records: tuple[FigureAltRecord, ...]
    exact_value_artifact: FigureExactValueArtifact | None = None

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

        exact_value_artifact = _parse_exact_value_artifact(payload, registry_path)
        raw_records = _registry_records(payload, registry_path)
        records: list[FigureAltRecord] = []
        seen_labels: set[str] = set()
        for fallback_label, record in raw_records:
            parsed = _parse_record(
                fallback_label,
                record,
                registry_path,
                exact_value_artifact=exact_value_artifact,
            )
            if parsed is None:
                continue
            if parsed.label in seen_labels:
                raise RenderingError(
                    f"Duplicate figure registry label: {parsed.label}",
                    context={"registry": str(registry_path)},
                )
            seen_labels.add(parsed.label)
            records.append(parsed)
        declared_identifiers = tuple(
            sorted(record.exact_value_fallback for record in records if record.exact_value_fallback is not None)
        )
        if declared_identifiers and exact_value_artifact is None:
            raise RenderingError(
                "Figure registry declares exact-value fallbacks without an exact-value artifact",
                context={"registry": str(registry_path)},
            )
        if exact_value_artifact is not None and declared_identifiers != exact_value_artifact.identifiers:
            raise RenderingError(
                "Figure registry exact-value artifact identifiers do not match figure declarations",
                context={
                    "registry": str(registry_path),
                    "declared_identifiers": list(declared_identifiers),
                    "artifact_identifiers": list(exact_value_artifact.identifiers),
                },
            )
        return cls(
            path=registry_path,
            records=tuple(records),
            exact_value_artifact=exact_value_artifact,
        )

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
    *,
    exact_value_artifact: FigureExactValueArtifact | None,
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
    top_long_description = _normalized_long_description(record.get("long_description"))
    metadata_long_description = (
        _normalized_long_description(metadata.get("long_description")) if isinstance(metadata, dict) else None
    )
    declared_long_descriptions = [
        value for value in (top_long_description, metadata_long_description) if value is not None
    ]
    if len(set(declared_long_descriptions)) > 1:
        raise RenderingError(
            f"Figure registry has conflicting long-description fields for {label}",
            context={"registry": str(registry_path)},
        )
    top_exact_value = _normalized_exact_value_fallback(record.get("exact_value_fallback"))
    metadata_exact_value = (
        _normalized_exact_value_fallback(metadata.get("exact_value_fallback")) if isinstance(metadata, dict) else None
    )
    declared_exact_values = [value for value in (top_exact_value, metadata_exact_value) if value is not None]
    if len(set(declared_exact_values)) > 1:
        raise RenderingError(
            f"Figure registry has conflicting exact-value fallback fields for {label}",
            context={"registry": str(registry_path)},
        )
    exact_value_fallback = top_exact_value or metadata_exact_value
    exact_value_href = None
    if exact_value_fallback is not None and exact_value_artifact is not None:
        anchor = exact_value_fallback.replace(":", "-")
        exact_value_href = f"{exact_value_artifact.web_markdown_href}#{anchor}"
    return FigureAltRecord(
        label=label,
        filename=filename,
        alt_text=top_alt or renderer_alt or metadata_alt,
        long_description=top_long_description or metadata_long_description,
        exact_value_fallback=exact_value_fallback,
        exact_value_href=exact_value_href,
    )


def _normalized_alt(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return " ".join(value.split())


def _normalized_long_description(value: object) -> str | None:
    """Normalize prose paragraphs while retaining meaningful boundaries."""

    if not isinstance(value, str) or not value.strip():
        return None
    paragraphs = [" ".join(paragraph.split()) for paragraph in re.split(r"\n\s*\n", value.strip())]
    return "\n\n".join(paragraph for paragraph in paragraphs if paragraph)


def _normalized_exact_value_fallback(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or value != value.strip():
        raise RenderingError("Figure registry exact-value fallback must be a canonical string")
    if re.fullmatch(r"fig-values:[a-z0-9][a-z0-9-]*", value) is None:
        raise RenderingError(
            "Figure registry exact-value fallback must match fig-values:<identifier>",
        )
    return value


def _artifact_path(value: object, *, field: str, registry_path: Path) -> str:
    if not isinstance(value, str) or value != value.strip():
        raise RenderingError(
            f"Figure registry {field} must be a canonical relative path",
            context={"registry": str(registry_path)},
        )
    normalized = value.replace("\\", "/")
    decoded = unquote(normalized)
    parsed = urlsplit(decoded)
    if decoded != normalized or parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        raise RenderingError(
            f"Figure registry {field} must not contain URI syntax or encoded path segments",
            context={"registry": str(registry_path)},
        )
    canonical = _canonical_safe_relative_path(parsed.path)
    if canonical is None or not canonical.startswith("output/figures/"):
        raise RenderingError(
            f"Figure registry {field} must remain under output/figures",
            context={"registry": str(registry_path)},
        )
    return canonical


def _parse_exact_value_artifact(
    payload: object,
    registry_path: Path,
) -> FigureExactValueArtifact | None:
    if not isinstance(payload, dict) or "exact_value_artifact" not in payload:
        return None
    raw_artifact = payload["exact_value_artifact"]
    if not isinstance(raw_artifact, dict):
        raise RenderingError(
            "Figure registry exact_value_artifact must be an object",
            context={"registry": str(registry_path)},
        )
    expected_fields = {"json_path", "markdown_path", "identifiers"}
    if set(raw_artifact) != expected_fields:
        raise RenderingError(
            "Figure registry exact_value_artifact has unknown or missing fields",
            context={
                "registry": str(registry_path),
                "expected_fields": sorted(expected_fields),
                "observed_fields": sorted(str(field) for field in raw_artifact),
            },
        )
    json_path = _artifact_path(
        raw_artifact["json_path"],
        field="exact_value_artifact.json_path",
        registry_path=registry_path,
    )
    markdown_path = _artifact_path(
        raw_artifact["markdown_path"],
        field="exact_value_artifact.markdown_path",
        registry_path=registry_path,
    )
    if not json_path.endswith(".json") or not markdown_path.endswith(".md"):
        raise RenderingError(
            "Figure registry exact-value artifact paths require .json and .md suffixes",
            context={"registry": str(registry_path)},
        )
    raw_identifiers = raw_artifact["identifiers"]
    if not isinstance(raw_identifiers, list):
        raise RenderingError(
            "Figure registry exact-value artifact identifiers must be an array",
            context={"registry": str(registry_path)},
        )
    normalized_identifiers: list[str] = []
    for value in raw_identifiers:
        normalized = _normalized_exact_value_fallback(value)
        if normalized is None:  # Array entries may not use the absent-field sentinel.
            raise RenderingError(
                "Figure registry exact-value artifact identifiers cannot be null",
                context={"registry": str(registry_path)},
            )
        normalized_identifiers.append(normalized)
    identifiers = tuple(normalized_identifiers)
    if identifiers != tuple(sorted(set(identifiers))):
        raise RenderingError(
            "Figure registry exact-value artifact identifiers must be sorted and unique",
            context={"registry": str(registry_path)},
        )
    return FigureExactValueArtifact(
        json_path=json_path,
        markdown_path=markdown_path,
        identifiers=identifiers,
    )
