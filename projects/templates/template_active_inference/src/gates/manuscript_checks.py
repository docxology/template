"""Manuscript and sheaf structure validation."""

from __future__ import annotations

import re
from pathlib import Path

from gates.claim_ledger import validate_claim_ledger, verify_claim_bindings

_SHEAF_TRACK_MARKER_RE = re.compile(r"^<!--\s*sheaf-track:([a-z_]+)\s*-->\s*$", re.MULTILINE)


def _duplicate_track_markers(manuscript_dir: Path) -> list[str]:
    """Composed sections in which the same sheaf-track marker appears more than once.

    The composer emits exactly one ``<!-- sheaf-track:X -->`` per (section, track) binding,
    so a track id appearing twice in one composed flat file means a fragment self-emitted a
    marker the composer also emits (a doubled stutter). Matches standalone marker lines only,
    so an inline prose mention of the marker syntax is not counted.
    """
    duplicates: list[str] = []
    for md_file in sorted(manuscript_dir.glob("[0-9][0-9]_*.md")):
        counts: dict[str, int] = {}
        for tid in _SHEAF_TRACK_MARKER_RE.findall(md_file.read_text(encoding="utf-8")):
            counts[tid] = counts.get(tid, 0) + 1
        duplicates.extend(f"{md_file.name}:{tid}={count}" for tid, count in sorted(counts.items()) if count > 1)
    return duplicates


def validate_manuscript(project_root: Path) -> dict[str, bool]:
    root = project_root.resolve()
    composed = list((root / "manuscript").glob("[0-9][0-9]_*.md"))
    manifest_path = root / "manuscript" / "sheaf" / "manifest.yaml"
    from manuscript.sheaf import (
        load_coverage_json,
        load_sheaf_coverage_context,
        validate_coverage_json_data,
        validate_manifest,
    )
    from ontology.bindings import validate_all_gnn_ontology

    gnn_ok = not validate_all_gnn_ontology(root)
    ctx = load_sheaf_coverage_context(root)
    manifest = ctx.manifest
    registry = ctx.registry
    promoted_tracks = {
        "sensitivity",
        "uncertainty",
        "benchmark",
        "model_checking",
        "interop",
        "adversarial_audit",
        "assumption_index",
        "animation_delta",
        "manuscript_staleness",
        "provenance",
        "replay_matrix",
        "counterexample",
        "evidence_fields",
        "release_bundle",
        "theorem_traceability",
        "gate_ergonomics",
        "artifact_diffoscope",
        "proof_extraction",
        "state_space_catalog",
        "causal_ablation",
        "artifact_license",
        "release_notes",
    }
    bound_tracks = {track_id for section in manifest.sections for track_id in section.tracks}
    promoted_tracks_bound = promoted_tracks <= set(registry.tracks) and promoted_tracks <= bound_tracks
    empirical_adapter_blocked = (
        "empirical_adapter" not in set(registry.tracks) and "empirical_adapter" not in bound_tracks
    )
    sheaf_issues = validate_manifest(manifest, root, registry=registry, strict_coverage=True)
    sheaf_ok = not any(i.level == "error" for i in sheaf_issues)

    coverage_matrix_valid = False
    json_path = root / "output" / "data" / "sheaf_coverage_matrix.json"
    heatmap_path = root / "output" / "figures" / "sheaf_coverage_heatmap.png"
    figure_registry_yaml = root / "figures.yaml"
    generated_figure_registry = root / "output" / "figures" / "figure_registry.json"
    if json_path.exists():
        data = load_coverage_json(json_path)
        json_issues = validate_coverage_json_data(data, manifest, registry)
        coverage_matrix_valid = not any(i.level == "error" for i in json_issues)

    full_sheaf_path = root / "manuscript" / "16_appendix_full_sheaf.md"
    full_sheaf_appendix_tracks = False
    if full_sheaf_path.exists():
        text = full_sheaf_path.read_text(encoding="utf-8")
        appendix = next((s for s in manifest.sections if s.id == "appendix_full_sheaf"), None)
        if appendix is not None:
            full_sheaf_appendix_tracks = all(f"sheaf-track:{tid}" in text for tid in appendix.tracks)

    imrad_groups_present = sum(1 for s in manifest.sections if s.kind == "group") >= 4
    composed_leaf_count = sum(1 for s in manifest.sections if s.should_compose())

    methods_sheaf_path = root / "manuscript" / "08_methods_sheaf.md"
    methods_sheaf_layers = False
    if methods_sheaf_path.exists():
        sheaf_text = methods_sheaf_path.read_text(encoding="utf-8")
        methods_sheaf_layers = (
            "sheaf_layers_overview.png" in sheaf_text
            and "<!-- sheaf-layers:registry -->" in sheaf_text
            and "<!-- sheaf-layers:binding-matrix -->" in sheaf_text
            and "<!-- sheaf-layers:legend -->" in sheaf_text
            and "<!-- sheaf-layers:section-status -->" in sheaf_text
            and "<!-- sheaf-layers:track-status -->" in sheaf_text
            and "<!-- sheaf-layers:render-log -->" in sheaf_text
        )

    from manuscript.hydrate import EXCLUDED_DOC_FILENAMES, collect_malformed_token_names, validate_manuscript_tokens
    from manuscript.variables import generate_variables
    from manuscript.sheaf.semantic import validate_semantic_gluing
    from roadmap_tracks import (
        validate_integration_audit_artifacts,
        validate_sheaf_track_artifacts,
    )

    integration_issues = validate_integration_audit_artifacts(root)
    sheaf_track_issues = validate_sheaf_track_artifacts(root)

    manuscript_dir = root / "manuscript"
    variable_keys = set(generate_variables(root, require_analysis_outputs=False))
    unknown_tokens = validate_manuscript_tokens(manuscript_dir, variable_keys)
    malformed_tokens: list[str] = []
    for md_file in sorted(manuscript_dir.glob("*.md")):
        if md_file.name in EXCLUDED_DOC_FILENAMES:
            continue
        malformed_tokens.extend(collect_malformed_token_names(md_file.read_text(encoding="utf-8")))
    manuscript_tokens_registered = not unknown_tokens and not malformed_tokens

    resolved_dir = root / "output" / "manuscript"
    resolved_manuscript_hydrated = False
    if resolved_dir.is_dir() and any(resolved_dir.glob("*.md")):
        from manuscript.hydrate import EXCLUDED_DOC_FILENAMES

        resolved_manuscript_hydrated = all(
            "{{" not in md.read_text(encoding="utf-8")
            for md in resolved_dir.glob("*.md")
            if md.name not in EXCLUDED_DOC_FILENAMES
        )

    return {
        "sheaf_manifest": manifest_path.exists(),
        "sheaf_registry": (root / "manuscript" / "sheaf" / "tracks.yaml").exists(),
        "sheaf_valid": sheaf_ok,
        "coverage_matrix_valid": coverage_matrix_valid,
        "full_sheaf_appendix_tracks": full_sheaf_appendix_tracks,
        "imrad_groups_present": imrad_groups_present,
        "claim_ledger_valid": validate_claim_ledger(root),
        "claim_bindings_satisfied": not verify_claim_bindings(root),
        "figure_registry_yaml": figure_registry_yaml.exists(),
        "generated_figure_registry": generated_figure_registry.exists(),
        "composed_sections": len(composed) >= composed_leaf_count,
        "sheaf_coverage_page": (root / "manuscript" / "00_00_sheaf_coverage.md").exists(),
        "sheaf_coverage_json": json_path.exists(),
        "sheaf_coverage_heatmap": heatmap_path.exists(),
        "methods_sheaf_layers": methods_sheaf_layers,
        "manuscript_tokens_registered": manuscript_tokens_registered,
        "no_duplicate_sheaf_track_markers": not _duplicate_track_markers(root / "manuscript"),
        "resolved_manuscript_hydrated": resolved_manuscript_hydrated,
        "gnn_concordance": gnn_ok,
        "semantic_sheaf_gluing": not validate_semantic_gluing(root),
        "promoted_sheaf_tracks_bound": promoted_tracks_bound,
        "integration_audit_artifacts": not integration_issues,
        "canonical_sheaf_tracks": not sheaf_track_issues,
        "blocked_empirical_adapter": empirical_adapter_blocked,
    }
