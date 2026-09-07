"""Shared helpers for the split combined-exports test modules."""

from __future__ import annotations

import zipfile
from pathlib import Path

import defusedxml.ElementTree as safe_et

from infrastructure.core.logging.diagnostic import DiagnosticReporter
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.core import RenderManager


def _make_reporter(tmp_path: Path) -> DiagnosticReporter:
    """Build a DiagnosticReporter backed by tmp_path."""
    return DiagnosticReporter("test_project")


def _make_manager(tmp_path: Path, **overrides: object) -> RenderManager:
    """Create a RenderManager with all output dirs under tmp_path."""
    cfg = RenderingConfig(
        pdf_dir=str(tmp_path / "output/pdf"),
        docx_dir=str(tmp_path / "output/docx"),
        epub_dir=str(tmp_path / "output/epub"),
        figures_dir=str(tmp_path / "output/figures"),
        web_dir=str(tmp_path / "output/web"),
        output_dir=str(tmp_path / "output"),
    )
    for attr, val in overrides.items():
        setattr(cfg, attr, val)
    return RenderManager(config=cfg)


def _epub_package_identifiers(path: Path) -> tuple[str, str]:
    """Read the OPF and NCX identities from one real combined export."""

    with zipfile.ZipFile(path) as archive:
        opf_name = next(name for name in archive.namelist() if name.endswith(".opf"))
        ncx_name = next(name for name in archive.namelist() if name.endswith(".ncx"))
        opf = safe_et.fromstring(archive.read(opf_name))
        ncx = safe_et.fromstring(archive.read(ncx_name))
    package_identifier = opf.find(".//{http://purl.org/dc/elements/1.1/}identifier")
    assert package_identifier is not None and package_identifier.text is not None
    navigation_identifier = next(
        node.get("content")
        for node in ncx.findall(".//{http://www.daisy.org/z3986/2005/ncx/}meta")
        if node.get("name") == "dtb:uid"
    )
    assert navigation_identifier is not None
    return package_identifier.text, navigation_identifier
