"""Registry-backed structural counts for manuscript variable injection."""

from __future__ import annotations

from pathlib import Path

from manuscript.sheaf.coverage import load_sheaf_coverage_context
from manuscript.sheaf.laws import verify_sheaf_laws
from manuscript.sheaf.report import build_coverage_report, default_coverage_config_path, load_coverage_config


def structural_counts(project_root: Path) -> dict[str, int]:
    """Counts derived from sheaf manifest, registry, and coverage matrix."""
    root = project_root.resolve()
    ctx = load_sheaf_coverage_context(root)
    config = load_coverage_config(default_coverage_config_path(root), project_root=root)
    report = build_coverage_report(ctx.matrix, ctx.manifest, config)
    appendix = next((section for section in ctx.manifest.sections if section.id == "appendix_full_sheaf"), None)
    laws = verify_sheaf_laws(root, manifest=ctx.manifest, registry=ctx.registry)
    return {
        "sheaf_law_count": len(laws.checked),
        "sheaf_laws_verified": len(laws.passed_laws),
        "sheaf_track_count": len(ctx.registry.tracks),
        "imrad_manifest_rows": len(ctx.manifest.sections),
        "composed_section_count": sum(1 for section in ctx.manifest.sections if section.should_compose()),
        "imrad_group_count": sum(1 for section in ctx.manifest.sections if section.kind == "group"),
        "coverage_present": report.total_present,
        "coverage_bound": report.total_bound,
        "coverage_missing": report.total_missing,
        "appendix_sheaf_track_count": len(appendix.tracks) if appendix else 0,
    }
