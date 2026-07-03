"""Metadata package generation orchestrator script.

This thin orchestrator generates structured metadata packages from the
project's manuscript/config.yaml:
1. Reads project metadata from manuscript/config.yaml
2. Generates ONIX 3.0 XML for book/publication registries
3. Generates metadata.json for downstream tooling and APIs
4. Generates an OPF (Open Packaging Format) skeleton for e-readers
5. Writes all files to output/metadata/ under the project's output directory
6. Reports results with file paths

Stage 08 of the pipeline orchestration (opt-in metadata stage).

Exit codes:
    0: Metadata package generated successfully
    1: Generation failed (missing config or write error)
    2: Graceful skip — manuscript/config.yaml not found (allow_skip compatible)
"""

from __future__ import annotations

import json
import textwrap
import uuid
from datetime import date
from pathlib import Path
from typing import Any, cast

from infrastructure.core.logging.utils import get_logger, log_header, log_success
from infrastructure.project.discovery import resolve_project_root

# Set up logger for this module
logger = get_logger(__name__)


def _as_config_mapping(value: object) -> dict[str, Any] | None:
    return cast(dict[str, Any], value) if isinstance(value, dict) else None


def _load_config(project_root: Path) -> dict[str, Any] | None:
    """Load manuscript/config.yaml; return None if absent."""
    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.is_file():
        return None

    try:
        import yaml
    except ImportError:
        # Fallback: try the infrastructure loader
        from infrastructure.core.config.loader import load_config as _load

        loaded_config = _load(config_path)
        return _as_config_mapping(loaded_config)

    with config_path.open("r", encoding="utf-8") as fh:
        loaded_yaml = yaml.safe_load(fh) or {}
        return _as_config_mapping(loaded_yaml)


def _extract_metadata(config: dict[str, Any], project_slug: str) -> dict[str, Any]:
    """Flatten config.yaml into a normalised metadata dict."""
    paper = config.get("paper", {}) or {}
    publication = config.get("publication", {}) or {}
    authors_raw = config.get("authors", []) or []
    keywords = config.get("keywords", []) or []
    meta_block = config.get("metadata", {}) or {}

    title = paper.get("title") or project_slug.replace("_", " ").title()
    subtitle = paper.get("subtitle", "") or ""
    version = paper.get("version", "1.0") or "1.0"
    doi = publication.get("doi", "") or ""
    journal = publication.get("journal", "") or ""
    volume = publication.get("volume", "") or ""
    pages = publication.get("pages", "") or ""
    language = meta_block.get("language", "en") or "en"
    license_id = meta_block.get("license", "Apache-2.0") or "Apache-2.0"

    authors: list[dict[str, str]] = []
    for a in authors_raw:
        if isinstance(a, dict):
            authors.append(
                {
                    "name": a.get("name", ""),
                    "orcid": a.get("orcid", ""),
                    "email": a.get("email", ""),
                    "affiliation": a.get("affiliation", ""),
                }
            )
        elif isinstance(a, str):
            authors.append({"name": a, "orcid": "", "email": "", "affiliation": ""})

    return {
        "title": title,
        "subtitle": subtitle,
        "version": version,
        "doi": doi,
        "journal": journal,
        "volume": volume,
        "pages": pages,
        "language": language,
        "license": license_id,
        "authors": authors,
        "keywords": list(keywords),
        "date": date.today().isoformat(),
        "project_slug": project_slug,
    }


# ── ONIX 3.0 XML generator ────────────────────────────────────────────────────


def _generate_onix_xml(meta: dict[str, Any]) -> str:
    """Return a minimal ONIX 3.0 XML document for the publication."""
    doi_line = ""
    if meta["doi"]:
        doi_line = f"            <IDValue>{meta['doi']}</IDValue>\n"
        doi_line = textwrap.dedent(f"""\
            <ProductIdentifier>
              <ProductIDType>06</ProductIDType>  <!-- DOI -->
              <IDValue>{meta["doi"]}</IDValue>
            </ProductIdentifier>
        """)

    authors_xml = ""
    for idx, author in enumerate(meta["authors"], start=1):
        role = "A01" if idx == 1 else "A01"  # author
        orcid_block = ""
        if author.get("orcid"):
            orcid_block = f"""
      <NameIdentifier>
        <NameIDType>21</NameIDType>  <!-- ORCID -->
        <IDValue>{author["orcid"]}</IDValue>
      </NameIdentifier>"""
        authors_xml += textwrap.dedent(f"""\
            <Contributor>
              <SequenceNumber>{idx}</SequenceNumber>
              <ContributorRole>{role}</ContributorRole>
              <PersonName>{author["name"]}</PersonName>{orcid_block}
            </Contributor>
        """)

    keywords_xml = ""
    for kw in meta["keywords"]:
        keywords_xml += (
            "  <Subject><SubjectSchemeIdentifier>20</SubjectSchemeIdentifier>"
            f"<SubjectHeadingText>{kw}</SubjectHeadingText></Subject>\n"
        )

    subtitle_el = ""
    if meta["subtitle"]:
        subtitle_el = f"\n  <Subtitle>{meta['subtitle']}</Subtitle>"

    return textwrap.dedent(f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <ONIXMessage release="3.0"
          xmlns="http://ns.editeur.org/onix/3.0/reference">
          <Header>
            <Sender>
              <SenderName>{meta["project_slug"]}</SenderName>
              <EmailAddress></EmailAddress>
            </Sender>
            <SentDateTime>{meta["date"].replace("-", "")}</SentDateTime>
          </Header>
          <Product>
            <RecordReference>{uuid.uuid4()}</RecordReference>
            <NotificationType>03</NotificationType>  <!-- Confirmed -->
            {doi_line}
            <DescriptiveDetail>
              <ProductComposition>00</ProductComposition>
              <ProductForm>EA</ProductForm>  <!-- Digital download -->
              <TitleDetail>
                <TitleType>01</TitleType>
                <TitleElement>
                  <TitleElementLevel>01</TitleElementLevel>
                  <TitleText>{meta["title"]}</TitleText>{subtitle_el}
                </TitleElement>
              </TitleDetail>
              {authors_xml}
              <Language>
                <LanguageRole>01</LanguageRole>
                <LanguageCode>{meta["language"]}</LanguageCode>
              </Language>
              {keywords_xml}
            </DescriptiveDetail>
            <PublishingDetail>
              <PublishingDate>
                <PublishingDateRole>01</PublishingDateRole>
                <Date>{meta["date"].replace("-", "")}</Date>
              </PublishingDate>
            </PublishingDetail>
          </Product>
        </ONIXMessage>
    """)


# ── OPF skeleton generator ────────────────────────────────────────────────────


def _generate_opf(meta: dict[str, Any]) -> str:
    """Return a minimal OPF 3.0 (EPUB container) skeleton."""
    book_id = f"urn:uuid:{uuid.uuid4()}"
    dc_creator = ""
    if meta["authors"]:
        dc_creator = f"\n    <dc:creator>{meta['authors'][0]['name']}</dc:creator>"

    dc_identifier = f'<dc:identifier id="BookId">{book_id}</dc:identifier>'
    if meta["doi"]:
        dc_identifier = f'<dc:identifier id="BookId">{meta["doi"]}</dc:identifier>'

    return textwrap.dedent(f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <package version="3.0"
          xmlns="http://www.idpf.org/2007/opf"
          unique-identifier="BookId"
          xml:lang="{meta["language"]}">
          <metadata
            xmlns:dc="http://purl.org/dc/elements/1.1/"
            xmlns:opf="http://www.idpf.org/2007/opf">
            {dc_identifier}
            <dc:title>{meta["title"]}</dc:title>{dc_creator}
            <dc:language>{meta["language"]}</dc:language>
            <dc:date>{meta["date"]}</dc:date>
            <dc:rights>{meta["license"]}</dc:rights>
            <meta property="dcterms:modified">{meta["date"]}T00:00:00Z</meta>
          </metadata>
          <manifest>
            <!-- Add item entries for all content documents and resources -->
            <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml"
                  properties="nav"/>
          </manifest>
          <spine>
            <!-- Add itemref entries in reading order -->
          </spine>
        </package>
    """)


def run_metadata_package(repo_root: Path, project: str) -> int:
    """Execute metadata package generation orchestration."""
    log_header(f"STAGE 12: Metadata Package (Project: {project})", logger)

    project_root = resolve_project_root(repo_root, project)

    # Load manuscript config
    config = _load_config(project_root)
    if config is None:
        config_path = project_root / "manuscript" / "config.yaml"
        logger.warning(
            "manuscript/config.yaml not found at %s — cannot generate metadata package (exit 2 = graceful skip)",
            config_path,
        )
        return 2

    project_slug = project_root.name
    meta = _extract_metadata(config, project_slug)

    logger.info("Project: %s", project_slug)
    logger.info("Title: %s", meta["title"])
    if meta["doi"]:
        logger.info("DOI: %s", meta["doi"])
    logger.info("Authors: %s", ", ".join(a["name"] for a in meta["authors"]) or "(none)")

    # Prepare output directory
    metadata_out_dir = project_root / "output" / "metadata"
    metadata_out_dir.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    failures: list[str] = []

    try:
        # ── metadata.json ──────────────────────────────────────────────────
        json_path = metadata_out_dir / "metadata.json"
        json_path.write_text(
            json.dumps(meta, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        generated.append(json_path)
        logger.info("  ✅ metadata.json: %s", json_path)

        # ── ONIX XML ───────────────────────────────────────────────────────
        onix_path = metadata_out_dir / "onix.xml"
        onix_xml = _generate_onix_xml(meta)
        onix_path.write_text(onix_xml, encoding="utf-8")
        generated.append(onix_path)
        logger.info("  ✅ onix.xml: %s", onix_path)

        # ── OPF skeleton ───────────────────────────────────────────────────
        opf_path = metadata_out_dir / f"{project_slug}.opf"
        opf_xml = _generate_opf(meta)
        opf_path.write_text(opf_xml, encoding="utf-8")
        generated.append(opf_path)
        logger.info("  ✅ %s.opf: %s", project_slug, opf_path)

    except Exception as exc:
        logger.error("Unexpected error during metadata generation: %s", exc, exc_info=True)
        return 1

    # ── Summary ───────────────────────────────────────────────────────────
    logger.info("")
    logger.info("Metadata package summary:")
    for path in generated:
        size_bytes = path.stat().st_size
        size_str = f"{size_bytes / 1024:.1f} KB" if size_bytes >= 1024 else f"{size_bytes} B"
        logger.info("  %s  (%s)", path.name, size_str)

    if failures:
        logger.error("Metadata generation failures: %s", "; ".join(failures))
        return 1

    log_success(
        f"✅ Metadata package complete — {len(generated)} file(s) in {metadata_out_dir}",
        logger,
    )
    return 0


__all__ = ["run_metadata_package"]
