"""Actual HTML fidelity producer and independent portable component hooks.

Darwin font contours are conditional component evidence. Linux font shaping,
complete OS/decoder/style/hinting custody and whole scientific source coverage
remain unsupported until their genuine source-owned providers are admitted.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
from infrastructure.reporting.native_format_html_admitted_source import AdmittedHTMLSource
from infrastructure.reporting.native_format_html_fidelity_components import inspect_html_fidelity_components
from infrastructure.reporting.native_format_html_font_provider import (
    HTMLFontProvider,
    UNSUPPORTED_PLATFORM,
    select_html_font_provider,
)
from infrastructure.reporting.native_format_html_font_witness import derive_probed_font_contours
from infrastructure.reporting.native_format_html_glyph_reference import inspect_source_glyph_ink
from infrastructure.reporting.native_format_html_reference_runtime import (
    observe_font_probe,
    observe_glyph_reference,
    replay_font_probe,
    replay_glyph_reference,
)
from infrastructure.reporting.native_format_html_resampling_witness import inspect_admitted_resampling
from infrastructure.reporting.native_format_html_style_calibration import observe_source_styles, replay_source_styles
from infrastructure.reporting.native_format_html_source_metadata import remaining_seconds
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

PLATFORM_BLOCKER = UNSUPPORTED_PLATFORM


def _result(
    components: dict[str, Any],
    font: dict[str, Any] | None,
    probe: dict[str, Any] | None,
    reference: dict[str, Any] | None,
    glyph: dict[str, Any] | None,
    resampling: dict[str, Any],
    platform_blockers: list[str],
    provider: HTMLFontProvider | None,
    style_calibration: dict[str, Any] | None = None,
) -> dict[str, Any]:
    findings = [*components["findings"], *resampling["findings"], *(glyph["findings"] if glyph else [])]
    blockers = [
        *components["blockers"],
        *resampling["blockers"],
        *(glyph["blockers"] if glyph else []),
        *platform_blockers,
    ]
    result = {
        "components": components,
        "font": font,
        "probe": probe,
        "reference": reference,
        "glyph_ink": glyph,
        "resampling": resampling,
        "platform_blockers": platform_blockers,
        "provider_profile": provider.description() if provider else None,
        "findings": findings,
        "blockers": blockers,
        "status": "fail" if findings else "blocked" if blockers else "pass",
    }
    if style_calibration is not None:
        result["style_calibration"] = style_calibration
    return {**result, "digest": canonical_digest(result)}


def observe_html_fidelity(
    root: Path,
    directory: Path,
    admitted: AdmittedHTMLSource,
    dom: dict[str, Any],
    pixels: bytes,
    artifact: ArtifactSnapshot,
    reader: SnapshotReader,
    *,
    chrome: str,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> dict[str, Any]:
    """Run genuine source font/projection references on the same caller clock."""
    remaining_seconds(deadline)
    admitted.close(root, reader, deadline=deadline)
    source = admitted.fidelity
    style_calibration = None
    if source["characters"].get("source_style_profile") is not None:
        create_private_native_directory(root, directory)
        source, style_calibration = observe_source_styles(
            root,
            directory / "source-style-calibration",
            admitted,
            reader,
            chrome=chrome,
            width=dom["width"],
            env=env,
            deadline=deadline,
            run_id=run_id,
        )
    components, _ = inspect_html_fidelity_components(source, dom, font_witness=None, deadline=deadline)
    font = probe = reference = glyph = None
    platform_blockers: list[str] = []
    request = components["font_request"]
    provider = select_html_font_provider(request, deadline=deadline)
    if provider is None:
        platform_blockers.append(PLATFORM_BLOCKER)
    elif request["fonts"]:
        if style_calibration is None:
            create_private_native_directory(root, directory)
        native, probe = observe_font_probe(
            root, directory, request, reader, provider=provider, env=env, deadline=deadline, run_id=run_id
        )
        font = derive_probed_font_contours(request, native, deadline=deadline)
        components, page = inspect_html_fidelity_components(source, dom, font_witness=font, deadline=deadline)
        if page is not None and components["glyph_scene"]["glyphs"]:
            scene_directory = directory / "source-glyph-reference"
            create_private_native_directory(root, scene_directory)
            reference_dom, reference_pixels, reference = observe_glyph_reference(
                root,
                scene_directory,
                page,
                dom["width"],
                reader,
                chrome=chrome,
                env=env,
                deadline=deadline,
                run_id=run_id,
            )
            glyph = inspect_source_glyph_ink(
                components["glyph_scene"], font["contours"], reference_dom, reference_pixels, pixels, deadline=deadline
            )
    resampling = inspect_admitted_resampling(admitted, dom, pixels, artifact, reader, deadline=deadline)
    result = _result(
        components, font, probe, reference, glyph, resampling, platform_blockers, provider, style_calibration
    )
    admitted.close(root, reader, deadline=deadline)
    remaining_seconds(deadline)
    return result


def replay_html_fidelity(
    root: Path,
    directory: Path,
    admitted: AdmittedHTMLSource,
    dom: dict[str, Any],
    pixels: bytes,
    artifact: ArtifactSnapshot,
    raw: dict[str, Any],
    reader: SnapshotReader,
    *,
    run_id: str,
    custody: dict[str, str],
    runtime: dict[str, Any],
    env: dict[str, str],
    deadline: float,
    original_deadline: float,
    chrome: str,
) -> dict[str, Any]:
    """Use this reader's own platform fonts and fresh source-only pixels.

    Source AST/config admission happens before this call; transported producer
    witnesses are checked as original observations, never current authority.
    """
    remaining_seconds(deadline)
    admitted.close(root, reader, deadline=deadline)
    source = admitted.fidelity
    style_calibration = raw.get("style_calibration")
    if source["characters"].get("source_style_profile") is not None:
        if not isinstance(style_calibration, dict) or style_calibration["deadline_monotonic"] != original_deadline:
            raise ValueError("original Source font size/style calibration omitted its actual original clock")
        source = replay_source_styles(
            root,
            directory / "source-style-calibration",
            admitted,
            style_calibration,
            reader,
            run_id=run_id,
            custody=custody,
            runtime=runtime,
            chrome=chrome,
            width=dom["width"],
            env=env,
            deadline=deadline,
        )
    elif style_calibration is not None:
        raise ValueError("legacy Source glyph roles acquired unexplained style calibration")
    base, _ = inspect_html_fidelity_components(source, dom, font_witness=None, deadline=deadline)
    request = base["font_request"]
    font = glyph = None
    provider = select_html_font_provider(request, deadline=deadline)
    if raw.get("provider_profile") != (provider.description() if provider else None):
        raise ValueError("HTML current Source font provider profile differs from authenticated original")
    if raw["probe"] is None:
        if raw["font"] is not None or raw["reference"] is not None or raw["glyph_ink"] is not None:
            raise ValueError("HTML source font/reference evidence lacks its genuine source probe")
        expected_blockers = [PLATFORM_BLOCKER] if provider is None else []
        if (provider is not None and request["fonts"]) or raw["platform_blockers"] != expected_blockers:
            raise ValueError("HTML actual Source font provider obligations were silently dropped or replaced")
        components = base
    else:
        if raw["platform_blockers"] or raw["probe"]["deadline_monotonic"] != original_deadline:
            raise ValueError("HTML source probe changed the original caller's deadline/platform obligations")
        if provider is None:
            raise ValueError(PLATFORM_BLOCKER)
        work = Path(tempfile.mkdtemp(prefix="native-html-source-font-reader-"))
        native = replay_font_probe(
            root,
            directory,
            request,
            raw["probe"],
            reader,
            provider=provider,
            run_id=run_id,
            custody=custody,
            runtime=runtime,
            env=env,
            deadline=deadline,
            work=work,
        )
        font = derive_probed_font_contours(request, native, deadline=deadline)
        if raw["font"] != font:
            raise ValueError("independent physical source font bytes/complete contours differ")
        components, page = inspect_html_fidelity_components(source, dom, font_witness=font, deadline=deadline)
        if page is not None and components["glyph_scene"]["glyphs"]:
            if raw["reference"] is None or raw["reference"]["deadline_monotonic"] != original_deadline:
                raise ValueError("HTML complete source glyphs omitted a genuine reference on the original caller clock")
            local_reference = work / "reference"
            local_reference.mkdir(mode=0o700)
            reference_dom, reference_pixels = replay_glyph_reference(
                root,
                directory / "source-glyph-reference",
                page,
                dom["width"],
                raw["reference"],
                reader,
                run_id=run_id,
                custody=custody,
                runtime=runtime,
                env=env,
                deadline=deadline,
                work=local_reference,
                chrome=chrome,
            )
            glyph = inspect_source_glyph_ink(
                components["glyph_scene"],
                font["contours"],
                reference_dom,
                reference_pixels,
                pixels,
                deadline=deadline,
            )
        elif raw["reference"] is not None or raw["glyph_ink"] is not None:
            raise ValueError("unsupported source glyphs acquired unexplained reference evidence")
    resampling = inspect_admitted_resampling(admitted, dom, pixels, artifact, reader, deadline=deadline)
    result = _result(
        components,
        font,
        raw["probe"],
        raw["reference"],
        glyph,
        resampling,
        raw["platform_blockers"],
        provider,
        style_calibration,
    )
    if raw != result:
        raise ValueError("independent actual original-source HTML fidelity observer differs")
    admitted.close(root, reader, deadline=deadline)
    remaining_seconds(deadline)
    return result
