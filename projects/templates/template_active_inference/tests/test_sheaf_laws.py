"""Sheaf-law oracle tests with negative controls.

Every law check is paired with a mutation that *breaks* the law, proving the
check bites (a structural test that only verifies shape does not bind truth —
see memory `feedback-shape-tests-dont-bind-truth`). The base object for each
negative control is the live, all-passing manifest; exactly one mutation is
applied so the targeted violation is isolated.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from manuscript.sheaf import (
    ComposeOptions,
    SheafLaw,
    SheafManifest,
    TrackRegistry,
    TrackSpec,
    compose_all_sections,
    load_manifest,
    load_track_registry,
    sheaf_law_violations,
    verify_sheaf_laws,
)

ROOT = Path(__file__).resolve().parents[1]


def _live() -> tuple[SheafManifest, TrackRegistry]:
    manifest = load_manifest(ROOT / "manuscript" / "sheaf" / "manifest.yaml", project_root=ROOT)
    registry = load_track_registry(ROOT / manifest.registry_path)
    return manifest, registry


def _replace_section(manifest: SheafManifest, section_id: str, **changes: object) -> SheafManifest:
    sections = tuple(
        dataclasses.replace(s, **changes) if s.id == section_id else s for s in manifest.sections
    )
    return dataclasses.replace(manifest, sections=sections)


def _codes(violations: list, law: SheafLaw) -> set[str]:
    return {v.code for v in violations if v.law == law}


# ---------------------------------------------------------------------------
# Positive control: the live manifest satisfies every sheaf law.
# ---------------------------------------------------------------------------


def test_live_manifest_satisfies_all_sheaf_laws() -> None:
    report = verify_sheaf_laws(ROOT)
    assert report.ok, report.summary() + " :: " + "; ".join(v.message for v in report.violations)
    assert len(report.checked) == 6
    assert set(report.passed_laws) == set(report.checked)


def test_every_law_is_actually_checked() -> None:
    manifest, registry = _live()
    # The pure entrypoint reports zero violations on the live manifest...
    assert sheaf_law_violations(manifest, registry) == []
    # ...and the enumeration covers all six laws.
    assert {law for law in SheafLaw} == {
        SheafLaw.POSET,
        SheafLaw.PRESHEAF,
        SheafLaw.SEPARATION,
        SheafLaw.GLUING,
        SheafLaw.TYPING,
        SheafLaw.COMPOSITIONALITY,
    }


# ---------------------------------------------------------------------------
# Negative controls: one mutation per law must be caught.
# ---------------------------------------------------------------------------


def test_negative_control_separation_output_name_collision() -> None:
    manifest, registry = _live()
    # Two composing sections glue to the same output file → separation broken.
    target = next(s for s in manifest.sections if s.id == "discussion_outlook")
    broken = _replace_section(manifest, "appendix_full_sheaf", output_name=target.output_name)
    codes = _codes(sheaf_law_violations(broken, registry), SheafLaw.SEPARATION)
    assert "output_name_collision" in codes


def test_negative_control_typing_suffix_error() -> None:
    manifest, registry = _live()
    section = next(s for s in manifest.sections if s.id == "methods_analytical")
    bad_tracks = {**section.tracks, "prose": "manuscript/sections/imrad/methods_analytical/prose.txt"}
    broken = _replace_section(manifest, "methods_analytical", tracks=bad_tracks)
    codes = _codes(sheaf_law_violations(broken, registry), SheafLaw.TYPING)
    assert "suffix_type_error" in codes


def test_negative_control_typing_exempts_generated_renderers() -> None:
    # A generated renderer (section_figures / layers_report) carries no file-type
    # contract: binding it to an arbitrary suffix must NOT raise a typing error.
    manifest, registry = _live()
    section = next(s for s in manifest.sections if s.id == "methods_analytical")
    viz_tracks = {**section.tracks, "visualization": "manuscript/sections/imrad/methods_analytical/figs.bin"}
    mutated = _replace_section(manifest, "methods_analytical", tracks=viz_tracks)
    codes = _codes(sheaf_law_violations(mutated, registry), SheafLaw.TYPING)
    assert "suffix_type_error" not in codes


def test_negative_control_gluing_or_poset_non_linear_extension() -> None:
    manifest, registry = _live()
    # Force the last (appendix) section into the introduction block while keeping
    # it last in compose order → the introduction block reappears after methods,
    # so compose order is no longer a linear extension of the base poset.
    broken = _replace_section(manifest, "appendix_full_sheaf", imrad="introduction")
    violations = sheaf_law_violations(broken, registry)
    gluing = _codes(violations, SheafLaw.GLUING)
    poset = _codes(violations, SheafLaw.POSET)
    assert "block_not_contiguous" in gluing or "non_monotone_block_order" in poset


def test_negative_control_presheaf_unknown_track() -> None:
    manifest, registry = _live()
    section = next(s for s in manifest.sections if s.id == "results_free_energy")
    bad_tracks = {**section.tracks, "bogus_track": "manuscript/sections/x.md"}
    broken = _replace_section(manifest, "results_free_energy", tracks=bad_tracks)
    codes = _codes(sheaf_law_violations(broken, registry), SheafLaw.PRESHEAF)
    assert "unbound_track" in codes


def test_negative_control_presheaf_duplicate_track_order() -> None:
    manifest, registry = _live()
    # Collapse two tracks onto the same compose order → global order not strict.
    specs = dict(registry.tracks)
    formalism = specs["formalism"]
    specs["formalism"] = TrackSpec(
        id=formalism.id,
        order=specs["prose"].order,
        renderer=formalism.renderer,
        label=formalism.label,
        optional=formalism.optional,
    )
    broken_registry = TrackRegistry(tracks=specs, renderer_suffixes=registry.renderer_suffixes)
    codes = _codes(sheaf_law_violations(manifest, broken_registry), SheafLaw.PRESHEAF)
    assert "duplicate_track_order" in codes


def test_negative_control_compositionality_shared_fragment() -> None:
    manifest, registry = _live()
    shared = next(s for s in manifest.sections if s.id == "methods_sheaf").tracks["prose"]
    section = next(s for s in manifest.sections if s.id == "results_invariants")
    bad_tracks = {**section.tracks, "prose": shared}
    broken = _replace_section(manifest, "results_invariants", tracks=bad_tracks)
    codes = _codes(sheaf_law_violations(broken, registry), SheafLaw.COMPOSITIONALITY)
    assert "shared_fragment" in codes


def test_negative_control_poset_section_without_group() -> None:
    manifest, registry = _live()
    # Drop the appendix group row → the appendix section loses group containment.
    sections = tuple(s for s in manifest.sections if s.id != "appendix")
    broken = dataclasses.replace(manifest, sections=sections)
    codes = _codes(sheaf_law_violations(broken, registry), SheafLaw.POSET)
    assert "section_without_group" in codes


# ---------------------------------------------------------------------------
# Integration: the strict compose gate refuses a law-violating manifest.
# ---------------------------------------------------------------------------


def test_strict_compose_rejects_law_violation(tmp_path: Path) -> None:
    manifest, _ = _live()
    target = next(s for s in manifest.sections if s.id == "discussion_outlook")
    # Write a manifest where two sections collide on output_name (separation broken),
    # but every fragment file still exists so only the law gate can reject it.
    bad_manifest = tmp_path / "manifest.yaml"
    appendix = next(s for s in manifest.sections if s.id == "appendix_full_sheaf")
    lines = ["schema_version: 2", "defaults:", "  missing_track: skip", "sections:"]
    for section in manifest.sections:
        lines.append(f"  - id: {section.id}")
        lines.append(f"    order: {section.order}")
        lines.append(f"    kind: {section.kind}")
        lines.append(f"    imrad: {section.imrad}")
        lines.append(f"    depth: {section.depth}")
        lines.append(f"    compose: {str(section.compose).lower()}")
        lines.append(f'    title: "{section.title}"')
        lines.append(f"    short: {section.short}")
        out = target.output_name if section.id == "appendix_full_sheaf" else section.output_name
        lines.append(f"    output_name: {out}")
        if section.tracks:
            lines.append("    tracks:")
            for tid, rel in section.tracks.items():
                lines.append(f"      {tid}: {rel}")
        else:
            lines.append("    tracks: {}")
    bad_manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert appendix is not None
    with pytest.raises(ValueError, match="validation failed"):
        compose_all_sections(
            ROOT,
            manuscript_dir=tmp_path / "out",
            manifest_path=bad_manifest,
            options=ComposeOptions(strict=True),
        )
