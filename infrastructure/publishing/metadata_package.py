"""ONIX 3.0, metadata.json, and EPUB 3.0 OPF metadata package generation.

Given a :class:`PublicationMetadata` model this module produces three
machine-readable artefacts for ebook distribution and retail platform ingestion:

* ``onix.xml``     — ONIX 3.0 XML feed (book trade standard)
* ``metadata.json``— Portable JSON bundle (Amazon KDP, Google Play, Gumroad,
                     Leanpub, and similar direct-sale platforms)
* ``package.opf``  — Bare EPUB 3.0 OPF metadata skeleton (embed in EPUB /
                     use as a standalone OPF for calibre / Sigil)

Usage::

    from infrastructure.publishing.metadata_package import (
        PublicationMetadata,
        generate_metadata_package,
    )

    meta = PublicationMetadata(
        title="My Research Ebook",
        authors=[{"name": "Jane Doe", "orcid": "0000-0001-2345-6789"}],
        isbn="978-3-16-148410-0",
        ...
    )
    paths = generate_metadata_package(meta, output_dir=Path("output/metadata"))
    # paths == {"onix_xml": Path(...), "metadata_json": Path(...), "opf": Path(...)}
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any
from xml.dom import minidom
from xml.etree import ElementTree as ET

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

# ── Data model ────────────────────────────────────────────────────────────────


@dataclass
class PublicationMetadata:
    """Structured metadata for an ebook / printed publication.

    Attributes:
        title: Primary title string.
        subtitle: Subtitle or series subtitle (may be empty).
        authors: List of author dicts.  Each dict must have ``"name"``; optional
            keys are ``"orcid"`` (bare 0000-… string) and ``"email"``.
        doi: DOI string without URL prefix, e.g. ``"10.5281/zenodo.1234567"``.
        isbn: ISBN-13 or ISBN-10 string (hyphens optional).
        publication_date: Publication date as :class:`datetime.date` or ISO
            string ``"YYYY-MM-DD"``; defaults to today.
        publisher: Publisher display name.
        description: Plain-text book blurb / abstract.
        keywords: List of keyword strings.
        language: BCP-47 language tag, e.g. ``"en"`` or ``"en-US"``.
        license: SPDX licence identifier or free-form licence name.
        price: Dict with ``"amount"`` (float/str) and ``"currency"`` (ISO 4217).
        page_count: Approximate page count (for print metadata).
        dimensions: Dict with ``"width_mm"``, ``"height_mm"``, ``"depth_mm"``
            for physical dimensions.
        bisac_codes: List of BISAC subject codes, e.g. ``["COM000000"]``.
        subjects: Human-readable subject/category strings (complementary to
            BISAC).
    """

    title: str
    subtitle: str = ""
    authors: list[dict[str, str]] = field(default_factory=list)
    doi: str = ""
    isbn: str = ""
    publication_date: date | str = field(default_factory=date.today)
    publisher: str = ""
    description: str = ""
    keywords: list[str] = field(default_factory=list)
    language: str = "en"
    license: str = ""
    price: dict[str, Any] | None = field(default_factory=lambda: None)
    page_count: int = 0
    dimensions: dict[str, Any] = field(default_factory=dict)
    bisac_codes: list[str] = field(default_factory=list)
    subjects: list[str] = field(default_factory=list)

    def _pub_date_str(self) -> str:
        """Return publication date as an ISO YYYY-MM-DD string."""
        if isinstance(self.publication_date, date):
            return self.publication_date.isoformat()
        return str(self.publication_date)

    def _pub_date_yyyymmdd(self) -> str:
        """Return publication date as YYYYMMDD (ONIX format)."""
        return self._pub_date_str().replace("-", "")


# ── ONIX 3.0 generator ────────────────────────────────────────────────────────


def _onix_subelement(parent: ET.Element, tag: str, text: str | None = None) -> ET.Element:
    el = ET.SubElement(parent, tag)
    if text is not None:
        el.text = text
    return el


def generate_onix_xml(meta: PublicationMetadata) -> str:
    """Generate an ONIX 3.0 XML string for *meta*.

    Follows the ONIX for Books International Standard 3.0 short-tag format.
    Produces a single-product message suitable for retail ingestion (Amazon,
    IngramSpark, Gardners, etc.).
    """
    root = ET.Element("ONIXMessage", release="3.0")
    root.set("xmlns", "http://ns.editeur.org/onix/3.0/reference")

    # ── Header ────────────────────────────────────────────────────────────────
    header = _onix_subelement(root, "Header")
    _onix_subelement(header, "Sender")
    sender = header.find("Sender")
    assert sender is not None
    _onix_subelement(sender, "SenderName", meta.publisher or "Unknown Publisher")
    _onix_subelement(header, "SentDateTime", meta._pub_date_yyyymmdd())
    _onix_subelement(header, "MessageNote", "Generated by infrastructure.publishing.metadata_package")

    # ── Product ───────────────────────────────────────────────────────────────
    product = _onix_subelement(root, "Product")
    _onix_subelement(product, "RecordReference", meta.isbn or meta.doi or "UNKNOWN")
    _onix_subelement(product, "NotificationType", "03")  # 03 = Confirmed record

    # Product identifiers
    if meta.isbn:
        pid = _onix_subelement(product, "ProductIdentifier")
        _onix_subelement(pid, "ProductIDType", "15")  # 15 = ISBN-13
        _onix_subelement(pid, "IDValue", meta.isbn.replace("-", "").replace(" ", ""))
    if meta.doi:
        pid = _onix_subelement(product, "ProductIdentifier")
        _onix_subelement(pid, "ProductIDType", "06")  # 06 = DOI
        _onix_subelement(pid, "IDValue", meta.doi)

    # Descriptive detail
    dd = _onix_subelement(product, "DescriptiveDetail")
    _onix_subelement(dd, "ProductComposition", "00")  # 00 = Single item
    _onix_subelement(dd, "ProductForm", "ED")  # ED = Digital download
    _onix_subelement(dd, "ProductFormDetail", "E101")  # E101 = EPUB

    # Title
    title_detail = _onix_subelement(dd, "TitleDetail")
    _onix_subelement(title_detail, "TitleType", "01")  # 01 = Distinctive title
    title_el = _onix_subelement(title_detail, "TitleElement")
    _onix_subelement(title_el, "TitleElementLevel", "01")
    _onix_subelement(title_el, "TitleText", meta.title)
    if meta.subtitle:
        _onix_subelement(title_el, "Subtitle", meta.subtitle)

    # Contributors (authors)
    for seq, author in enumerate(meta.authors, start=1):
        contrib = _onix_subelement(dd, "Contributor")
        _onix_subelement(contrib, "SequenceNumber", str(seq))
        _onix_subelement(contrib, "ContributorRole", "A01")  # A01 = Author
        _onix_subelement(contrib, "PersonName", author.get("name", ""))
        if author.get("orcid"):
            name_id = _onix_subelement(contrib, "NameIdentifier")
            _onix_subelement(name_id, "NameIDType", "21")  # 21 = ORCID
            _onix_subelement(name_id, "IDValue", author["orcid"])

    # Language
    lang = _onix_subelement(dd, "Language")
    _onix_subelement(lang, "LanguageRole", "01")
    _onix_subelement(lang, "LanguageCode", meta.language[:2].lower())

    # Page count
    if meta.page_count:
        extent = _onix_subelement(dd, "Extent")
        _onix_subelement(extent, "ExtentType", "00")  # 00 = Main content
        _onix_subelement(extent, "ExtentValue", str(meta.page_count))
        _onix_subelement(extent, "ExtentUnit", "03")  # 03 = Pages

    # BISAC subjects
    for code in meta.bisac_codes:
        subj = _onix_subelement(dd, "Subject")
        _onix_subelement(subj, "SubjectSchemeIdentifier", "10")  # 10 = BISAC
        _onix_subelement(subj, "SubjectCode", code)
    for kw in meta.keywords:
        subj = _onix_subelement(dd, "Subject")
        _onix_subelement(subj, "SubjectSchemeIdentifier", "20")  # 20 = Keywords
        _onix_subelement(subj, "SubjectHeadingText", kw)

    # Physical dimensions (for print edition)
    dims = meta.dimensions
    if dims.get("height_mm"):
        meas = _onix_subelement(dd, "Measure")
        _onix_subelement(meas, "MeasureType", "01")  # 01 = Height
        _onix_subelement(meas, "Measurement", str(dims["height_mm"]))
        _onix_subelement(meas, "MeasureUnitCode", "mm")
    if dims.get("width_mm"):
        meas = _onix_subelement(dd, "Measure")
        _onix_subelement(meas, "MeasureType", "02")  # 02 = Width
        _onix_subelement(meas, "Measurement", str(dims["width_mm"]))
        _onix_subelement(meas, "MeasureUnitCode", "mm")
    if dims.get("depth_mm"):
        meas = _onix_subelement(dd, "Measure")
        _onix_subelement(meas, "MeasureType", "08")  # 08 = Thickness
        _onix_subelement(meas, "Measurement", str(dims["depth_mm"]))
        _onix_subelement(meas, "MeasureUnitCode", "mm")

    # Collateral detail (description)
    if meta.description:
        cd = _onix_subelement(product, "CollateralDetail")
        txt_content = _onix_subelement(cd, "TextContent")
        _onix_subelement(txt_content, "TextType", "03")  # 03 = Description
        _onix_subelement(txt_content, "ContentAudience", "00")
        _onix_subelement(txt_content, "Text", meta.description)

    # Publishing detail
    pd_el = _onix_subelement(product, "PublishingDetail")
    if meta.publisher:
        pub = _onix_subelement(pd_el, "Publisher")
        _onix_subelement(pub, "PublishingRole", "01")
        _onix_subelement(pub, "PublisherName", meta.publisher)
    _onix_subelement(pd_el, "PublishingStatus", "04")  # 04 = Active
    pub_date = _onix_subelement(pd_el, "PublishingDate")
    _onix_subelement(pub_date, "PublishingDateRole", "01")
    _onix_subelement(pub_date, "Date", meta._pub_date_yyyymmdd())
    if meta.license:
        sales_rights = _onix_subelement(pd_el, "CopyrightStatement")
        _onix_subelement(sales_rights, "CopyrightYear", meta._pub_date_str()[:4])
        _onix_subelement(pd_el, "ROWSalesRightsType", "00")

    # Product supply (pricing)
    if meta.price:
        supply_detail = _onix_subelement(product, "ProductSupply")
        market = _onix_subelement(supply_detail, "Market")
        _onix_subelement(market, "Territory")
        terr = market.find("Territory")
        assert terr is not None
        _onix_subelement(terr, "RegionsIncluded", "WORLD")
        supply = _onix_subelement(supply_detail, "SupplyDetail")
        _onix_subelement(supply, "ProductAvailability", "20")  # 20 = Available
        price_el = _onix_subelement(supply, "Price")
        _onix_subelement(price_el, "PriceType", "01")  # 01 = RRP excl. tax
        _onix_subelement(price_el, "PriceAmount", str(meta.price.get("amount", "0") if meta.price else "0"))
        _onix_subelement(price_el, "CurrencyCode", str(meta.price.get("currency", "USD") if meta.price else "USD"))

    # Pretty-print via minidom
    raw = ET.tostring(root, encoding="unicode", xml_declaration=False)
    pretty = minidom.parseString(raw).toprettyxml(indent="  ")
    # minidom adds a redundant first line; strip it and add our own declaration
    lines = pretty.splitlines()
    body = "\n".join(lines[1:])  # drop minidom's declaration
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + body


# ── metadata.json generator ───────────────────────────────────────────────────


def generate_metadata_json(meta: PublicationMetadata) -> dict[str, Any]:
    """Generate a portable ebook metadata dict for retail platform ingestion.

    The structure is compatible with:
    * Amazon KDP (Kindle Direct Publishing) bulk metadata import
    * Google Play Books content upload
    * Gumroad product creation
    * Leanpub manifest

    Returns a plain Python dict; call ``json.dumps()`` to serialise.
    """
    authors_list = [
        {
            "name": a.get("name", ""),
            **({"orcid": a["orcid"]} if a.get("orcid") else {}),
            **({"email": a["email"]} if a.get("email") else {}),
        }
        for a in meta.authors
    ]

    payload: dict[str, Any] = {
        "title": meta.title,
        "subtitle": meta.subtitle,
        "authors": authors_list,
        "language": meta.language,
        "publication_date": meta._pub_date_str(),
        "publisher": meta.publisher,
        "description": meta.description,
        "keywords": meta.keywords,
        "license": meta.license,
        "subjects": meta.subjects,
        "bisac_codes": meta.bisac_codes,
        # Identifiers
        "identifiers": {
            **({"isbn": meta.isbn} if meta.isbn else {}),
            **({"doi": meta.doi} if meta.doi else {}),
        },
        # Distribution pricing
        "price": meta.price,
        # Physical specs
        "page_count": meta.page_count,
        "dimensions": meta.dimensions,
        # Platform-specific sections (populated from shared fields)
        "amazon_kdp": {
            "title": meta.title,
            "subtitle": meta.subtitle,
            "authors": [a.get("name", "") for a in meta.authors],
            "description": meta.description,
            "keywords": meta.keywords[:7],  # KDP max 7 keywords
            "bisac_primary": meta.bisac_codes[0] if meta.bisac_codes else "",
            "bisac_secondary": meta.bisac_codes[1] if len(meta.bisac_codes) > 1 else "",
            "language": meta.language,
            "publication_date": meta._pub_date_str(),
            "publisher": meta.publisher,
            "isbn": meta.isbn,
            "list_price": meta.price,
        },
        "google_play_books": {
            "title": meta.title,
            "subtitle": meta.subtitle,
            "authors": [a.get("name", "") for a in meta.authors],
            "description": meta.description,
            "isbn": meta.isbn,
            "language": meta.language,
            "subjects": meta.subjects,
            "publisher": meta.publisher,
            "on_sale_date": meta._pub_date_str(),
            "retail_price": meta.price,
        },
        "gumroad": {
            "name": meta.title,
            "description": meta.description,
            "price": int(float(meta.price.get("amount", 0) if meta.price else 0) * 100),
            "currency": (meta.price.get("currency", "usd") if meta.price else "usd").lower(),
            "tags": meta.keywords,
            "published": True,
        },
        "leanpub": {
            "title": meta.title,
            "subtitle": meta.subtitle,
            "short_description": meta.description[:255] if meta.description else "",
            "long_description": meta.description,
            "language": meta.language,
            "authors": [a.get("name", "") for a in meta.authors],
            "categories": meta.subjects,
            "minimum_price": meta.price.get("amount", 0) if meta.price else 0,
            "suggested_price": meta.price.get("amount", 0) if meta.price else 0,
        },
    }
    return payload


# ── EPUB 3.0 OPF generator ────────────────────────────────────────────────────

# OPF namespace map
_OPF_NS = "http://www.idpf.org/2007/opf"
_DC_NS = "http://purl.org/dc/elements/1.1/"


def generate_epub_opf(meta: PublicationMetadata) -> str:
    """Generate an EPUB 3.0 OPF (Open Packaging Format) metadata skeleton.

    The returned XML string can be saved as ``content.opf`` inside an EPUB
    ``META-INF/`` directory, or used as input to calibre / Sigil.
    """
    ET.register_namespace("", _OPF_NS)
    ET.register_namespace("dc", _DC_NS)

    package = ET.Element(
        "{%s}package" % _OPF_NS,
        attrib={
            "version": "3.0",
            "unique-identifier": "book-id",
            "{http://www.w3.org/XML/1998/namespace}lang": meta.language,
        },
    )

    # ── metadata element ──────────────────────────────────────────────────────
    metadata = ET.SubElement(package, "{%s}metadata" % _OPF_NS)
    metadata.set("xmlns:dc", _DC_NS)

    # Dublin Core basics
    dc_id = ET.SubElement(metadata, "{%s}identifier" % _DC_NS, attrib={"id": "book-id"})
    dc_id.text = meta.isbn or meta.doi or "urn:uuid:unknown"

    dc_title = ET.SubElement(metadata, "{%s}title" % _DC_NS, attrib={"id": "title"})
    dc_title.text = meta.title
    if meta.subtitle:
        dc_subtitle = ET.SubElement(metadata, "{%s}title" % _DC_NS, attrib={"id": "subtitle", "refines": "#title"})
        dc_subtitle.text = meta.subtitle

    ET.SubElement(metadata, "{%s}language" % _DC_NS).text = meta.language

    if meta.publisher:
        ET.SubElement(metadata, "{%s}publisher" % _DC_NS).text = meta.publisher
    if meta.description:
        ET.SubElement(metadata, "{%s}description" % _DC_NS).text = meta.description
    if meta.license:
        ET.SubElement(metadata, "{%s}rights" % _DC_NS).text = meta.license

    for author in meta.authors:
        creator = ET.SubElement(metadata, "{%s}creator" % _DC_NS)
        creator.text = author.get("name", "")
        if author.get("orcid"):
            # OPF3 refinement for ORCID
            creator.set("id", f"creator-{author.get('orcid', '').replace('-', '')[:8]}")

    if meta.doi:
        source = ET.SubElement(metadata, "{%s}source" % _DC_NS)
        source.text = f"https://doi.org/{meta.doi}"

    # OPF3 meta elements
    ET.SubElement(
        metadata,
        "{%s}meta" % _OPF_NS,
        attrib={"property": "dcterms:modified"},
    ).text = meta._pub_date_str() + "T00:00:00Z"

    for kw in meta.keywords:
        ET.SubElement(metadata, "{%s}subject" % _DC_NS).text = kw

    for code in meta.bisac_codes:
        ET.SubElement(
            metadata,
            "{%s}meta" % _OPF_NS,
            attrib={"property": "schema:about"},
        ).text = code

    # ── manifest (skeleton — real items added by ebook toolchain) ─────────────
    manifest = ET.SubElement(package, "{%s}manifest" % _OPF_NS)
    ET.SubElement(
        manifest,
        "{%s}item" % _OPF_NS,
        attrib={
            "id": "ncx",
            "href": "toc.ncx",
            "media-type": "application/x-dtbncx+xml",
        },
    )
    ET.SubElement(
        manifest,
        "{%s}item" % _OPF_NS,
        attrib={
            "id": "nav",
            "href": "nav.xhtml",
            "media-type": "application/xhtml+xml",
            "properties": "nav",
        },
    )

    # ── spine (skeleton) ──────────────────────────────────────────────────────
    ET.SubElement(package, "{%s}spine" % _OPF_NS, attrib={"toc": "ncx"})

    raw = ET.tostring(package, encoding="unicode", xml_declaration=False)
    pretty = minidom.parseString(raw).toprettyxml(indent="  ")
    lines = pretty.splitlines()
    body = "\n".join(lines[1:])
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + body


# ── Orchestrator ──────────────────────────────────────────────────────────────


def generate_metadata_package(
    meta: PublicationMetadata,
    output_dir: Path,
) -> dict[str, Path]:
    """Generate all three metadata artefacts and write them to *output_dir*.

    Args:
        meta: Populated :class:`PublicationMetadata` instance.
        output_dir: Directory to write artefacts into; created if missing.

    Returns:
        Dict mapping ``"onix_xml"``, ``"metadata_json"``, ``"opf"`` to the
        written :class:`~pathlib.Path` objects.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # ONIX 3.0
    onix_path = output_dir / "onix.xml"
    onix_xml = generate_onix_xml(meta)
    onix_path.write_text(onix_xml, encoding="utf-8")
    logger.info("  Generated ONIX 3.0 metadata: %s (%d bytes)", onix_path.name, len(onix_xml.encode()))

    # metadata.json
    json_path = output_dir / "metadata.json"
    meta_dict = generate_metadata_json(meta)
    json_text = json.dumps(meta_dict, indent=2, ensure_ascii=False)
    json_path.write_text(json_text, encoding="utf-8")
    logger.info("  Generated metadata JSON: %s (%d bytes)", json_path.name, len(json_text.encode()))

    # EPUB 3.0 OPF
    opf_path = output_dir / "package.opf"
    opf_xml = generate_epub_opf(meta)
    opf_path.write_text(opf_xml, encoding="utf-8")
    logger.info("  Generated EPUB OPF skeleton: %s (%d bytes)", opf_path.name, len(opf_xml.encode()))

    return {
        "onix_xml": onix_path,
        "metadata_json": json_path,
        "opf": opf_path,
    }


__all__ = [
    "PublicationMetadata",
    "generate_metadata_package",
    "generate_onix_xml",
    "generate_metadata_json",
    "generate_epub_opf",
]
