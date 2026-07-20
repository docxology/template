"""Compose flat manuscript markdown from sheaf section manifests."""

from __future__ import annotations

from pathlib import Path

from manuscript.sheaf.coverage import build_coverage_matrix, emit_coverage_artifacts, validate_coverage_strict
from manuscript.sheaf.manifest import load_manifest
from manuscript.sheaf.models import (
    DEFAULT_MANIFEST_REL,
    ComposeOptions,
    ComposeResult,
    ManifestIssue,
    MissingTrackPolicy,
    SheafManifest,
    SheafSection,
    TrackRegistry,
    TrackSpec,
)
from manuscript.sheaf.registry import load_track_registry, track_order_for_section
from manuscript.sheaf.renderers import GENERATED_RENDERERS, resolve_track_body, validate_renderer_specs


def issues_have_errors(issues: list[ManifestIssue]) -> bool:
    """Process issues have errors."""
    return any(issue.level == "error" for issue in issues)


def validate_manifest(
    manifest: SheafManifest,
    project_root: Path,
    *,
    registry: TrackRegistry | None = None,
    strict_coverage: bool = False,
) -> list[ManifestIssue]:
    """Validate manifest."""
    root = project_root.resolve()
    reg = registry or (
        load_track_registry(root / manifest.registry_path)
        if (root / manifest.registry_path).exists()
        else TrackRegistry(tracks={}, renderer_suffixes={})
    )
    specs = reg.tracks
    issues: list[ManifestIssue] = []
    validate_renderer_specs(reg, issues)
    seen_ids: set[str] = set()
    for section in manifest.sections:
        if section.id in seen_ids:
            issues.append(ManifestIssue("error", "duplicate_section_id", f"Duplicate section id: {section.id}"))
        seen_ids.add(section.id)
        for track_id, rel in section.tracks.items():
            if specs and track_id not in specs:
                issues.append(
                    ManifestIssue(
                        "warn",
                        "unknown_track",
                        f"{section.id}: track `{track_id}` not in registry",
                    )
                )
            spec = specs.get(track_id)
            path = root / rel
            if path.exists() and spec and spec.renderer not in GENERATED_RENDERERS:
                allowed = reg.renderer_suffixes.get(spec.renderer)
                if allowed and path.suffix not in allowed:
                    issues.append(
                        ManifestIssue(
                            "warn",
                            "renderer_suffix_mismatch",
                            f"{section.id}/{track_id}: `{path.suffix}` not in {allowed}",
                        )
                    )
            if not path.exists():
                optional = specs.get(track_id, TrackSpec(track_id, 0, "markdown", track_id, True)).optional
                level = "warn" if optional else "error"
                issues.append(
                    ManifestIssue(
                        level,
                        "missing_track_file",
                        f"{section.id}/{track_id}: missing file {rel}",
                    )
                )
        for track_id in section.track_order or ():
            if track_id not in section.tracks:
                issues.append(
                    ManifestIssue(
                        "error",
                        "track_order_unbound",
                        f"{section.id}: track_order lists `{track_id}` but tracks map has no binding",
                    )
                )
    if strict_coverage and reg.tracks:
        matrix = build_coverage_matrix(reg, manifest, root)
        issues.extend(validate_coverage_strict(matrix))
        issues.extend(sheaf_law_issues(manifest, reg))
    return issues


def sheaf_law_issues(manifest: SheafManifest, registry: TrackRegistry) -> list[ManifestIssue]:
    """Surface sheaf-law violations as error-level manifest issues for the strict gate."""
    from manuscript.sheaf.laws import sheaf_law_violations

    return [
        ManifestIssue("error", f"sheaf_law_{v.law.value}", v.message) for v in sheaf_law_violations(manifest, registry)
    ]


def _imrad_group_titles(manifest: SheafManifest) -> dict[str, str]:
    titles: dict[str, str] = {}
    for section in manifest.sections:
        if section.kind == "group":
            titles[section.imrad] = section.title
    return titles


def _imrad_divider_markdown(title: str) -> str:
    return (
        "```{=latex}\n"
        "\\phantomsection\n"
        f"\\addcontentsline{{toc}}{{section}}{{{title}}}\n"
        f"\\section*{{{title}}}\n"
        "```\n\n"
    )


def compose_section(
    section: SheafSection,
    project_root: Path,
    *,
    registry: TrackRegistry,
    options: ComposeOptions | None = None,
    issues: list[ManifestIssue] | None = None,
) -> str:
    """Process compose section."""
    opts = options or ComposeOptions()
    policy = opts.missing_track or MissingTrackPolicy.SKIP
    parts = [f"# {section.title} {{#sec:{section.id}}}\n"]
    for track_id in track_order_for_section(section, registry):
        if opts.enabled_tracks is not None and track_id not in opts.enabled_tracks:
            continue
        rel = section.tracks.get(track_id)
        if not rel:
            continue
        track_path = project_root / rel
        if track_id not in registry.tracks:
            raise KeyError(f"unknown sheaf track `{track_id}` in section `{section.id}`")
        spec = registry.tracks[track_id]
        if not track_path.exists():
            msg = f"{section.id}/{track_id}: missing {rel}"
            if policy == MissingTrackPolicy.ERROR or (opts.strict and not spec.optional):
                raise FileNotFoundError(msg)
            if policy == MissingTrackPolicy.WARN and issues is not None:
                issues.append(ManifestIssue("warn", "missing_track_at_compose", msg))
            continue
        body = resolve_track_body(section, track_id, track_path, project_root, registry)
        parts.append(f"\n<!-- sheaf-track:{track_id} -->\n\n{body}\n")
    return "".join(parts)


def compose_all_sections(
    project_root: Path,
    *,
    manuscript_dir: Path | None = None,
    manifest_path: Path | None = None,
    options: ComposeOptions | None = None,
) -> ComposeResult:
    """Process compose all sections."""
    root = project_root.resolve()
    manifest_file = manifest_path or (root / DEFAULT_MANIFEST_REL)
    manifest = load_manifest(manifest_file, project_root=root)
    registry = load_track_registry(root / manifest.registry_path)
    opts = options or ComposeOptions()
    issues: list[ManifestIssue] = []
    validation = validate_manifest(manifest, root, registry=registry, strict_coverage=opts.strict)
    issues.extend(validation)
    if opts.strict and issues_have_errors(validation):
        messages = "; ".join(i.message for i in validation if i.level == "error")
        raise ValueError(f"Sheaf manifest validation failed: {messages}")
    out_dir = manuscript_dir or (root / "manuscript")
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    group_titles = _imrad_group_titles(manifest)
    prev_imrad: str | None = None
    for section in manifest.sections:
        if opts.section_ids is not None and section.id not in opts.section_ids:
            continue
        if not section.should_compose():
            continue
        prefix = ""
        if section.imrad != prev_imrad:
            group_title = group_titles.get(
                section.imrad,
                section.imrad.replace("_", " ").title(),
            )
            prefix = _imrad_divider_markdown(group_title)
        content = prefix + compose_section(section, root, registry=registry, options=opts, issues=issues)
        prev_imrad = section.imrad
        target = out_dir / section.output_name
        # Keep generated Markdown compatible with repository-wide formatting
        # hooks.  Some final track bodies intentionally have inconsistent
        # trailing newlines; normalize the composed page boundary so
        # rerendering is stable and diff-clean.
        target.write_text(f"{content.rstrip()}\n", encoding="utf-8")
        written.append(target)
    emit_coverage_artifacts(root)
    return ComposeResult(paths=written, issues=issues)
