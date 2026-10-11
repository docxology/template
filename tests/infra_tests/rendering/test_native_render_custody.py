"""Rendering's native-custody seam: scoped launchers and native-origin refusal.

Real functions and environment only. The seam is how a live native owner hands
rendering its custody launchers without rendering importing reporting
(``RENDERING-LAYERING-1``).
"""

from __future__ import annotations

import inspect
import subprocess
from pathlib import Path

import pytest

from infrastructure.rendering.native_render_custody import (
    NATIVE_ORIGIN_KEYS,
    NativeTexSectionPass,
    SourceNativeMermaid,
    SourceNativePandoc,
    installed_native_render_custody,
    native_render_custody,
)


class _RecordingLaunchers:
    """Launchers whose functions record the frame that actually called them."""

    def __init__(self) -> None:
        self.callers: list[str] = []

    def pandoc_launcher(self) -> SourceNativePandoc:
        def run(
            command: list[str],
            combined: Path,
            source_files: list[Path],
            *,
            writer: str,
            environment: dict[str, str] | None = None,
        ) -> bool:
            frame = inspect.currentframe()
            assert frame is not None and frame.f_back is not None
            self.callers.append(frame.f_back.f_code.co_name)
            return writer == "html"

        return run

    def mermaid_launcher(self) -> SourceNativeMermaid:
        def run(
            command: list[str],
            source_path: Path,
            output_path: Path,
            *,
            role: str,
            raw_source: str,
            input_paths: tuple[Path, ...],
            environment: dict[str, str],
            timeout: int,
        ) -> None:
            return None

        return run

    def tex_section_launcher(self) -> NativeTexSectionPass:
        def run(
            command: list[str], tex: Path, output: Path, *, environment: dict[str, str]
        ) -> subprocess.CompletedProcess[str] | None:
            return None

        return run


@pytest.fixture
def ordinary_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in NATIVE_ORIGIN_KEYS:
        monkeypatch.delenv(key, raising=False)


@pytest.mark.usefixtures("ordinary_environment")
def test_ordinary_call_without_launchers_keeps_the_ordinary_path() -> None:
    assert native_render_custody("unused refusal") is None


@pytest.mark.parametrize("key", NATIVE_ORIGIN_KEYS)
def test_native_origin_without_live_launchers_is_refused(
    monkeypatch: pytest.MonkeyPatch, ordinary_environment: None, key: str
) -> None:
    monkeypatch.setenv(key, "nominated-origin")

    with pytest.raises(ValueError, match="^caller-specific refusal$"):
        native_render_custody("caller-specific refusal")


@pytest.mark.usefixtures("ordinary_environment")
def test_launchers_are_visible_only_for_the_installing_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    launchers = _RecordingLaunchers()

    with installed_native_render_custody(launchers):
        assert native_render_custody("unused refusal") is launchers
        # An installed owner is consulted even when a native origin is nominated.
        monkeypatch.setenv(NATIVE_ORIGIN_KEYS[0], "nominated-origin")
        assert native_render_custody("unused refusal") is launchers
        monkeypatch.delenv(NATIVE_ORIGIN_KEYS[0])

    assert native_render_custody("unused refusal") is None


@pytest.mark.usefixtures("ordinary_environment")
def test_installed_launcher_runs_from_the_rendering_caller_frame(tmp_path: Path) -> None:
    """Custody functions that verify their caller see the rendering function itself."""
    launchers = _RecordingLaunchers()
    combined = tmp_path / "combined.md"

    def rendering_call_site() -> bool:
        custody = native_render_custody("unused refusal")
        assert custody is not None
        return custody.pandoc_launcher()(["pandoc", str(combined)], combined, [combined], writer="html")

    with installed_native_render_custody(launchers):
        assert rendering_call_site() is True

    assert launchers.callers == ["rendering_call_site"]


def test_reporting_owner_supplies_its_real_custody_functions() -> None:
    """The producer owner's launchers resolve to reporting's actual custody functions."""
    from infrastructure.reporting.native_mermaid_production_tool import run_source_native_mermaid
    from infrastructure.reporting.native_renderer_source_call import run_source_native_pandoc
    from infrastructure.reporting.native_tex_section_render import run_native_tex_section_pass
    from infrastructure.reporting.native_tool_producer import _NativeRenderLaunchers

    launchers = _NativeRenderLaunchers()

    assert launchers.pandoc_launcher() is run_source_native_pandoc
    assert launchers.mermaid_launcher() is run_source_native_mermaid
    assert launchers.tex_section_launcher() is run_native_tex_section_pass
