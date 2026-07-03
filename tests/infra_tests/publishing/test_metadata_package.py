"""Tests for publishing metadata packages — ONIX XML, metadata.json, OPF, and models.

These are pure unit tests: no external dependencies, no file I/O beyond tmp_path.
They validate that the data structures and serialisers in
``infrastructure.publishing.models`` plus the export helpers produce well-formed
output.

Because a dedicated ``metadata_package`` module does not yet exist as a separate
infrastructure file, these tests validate the *contract* for metadata outputs
produced by the template pipeline (Stage 11 / export_for_publishing.py):
- ONIX 3.0 XML structure
- metadata.json field set
- OPF skeleton (EPUB Open Packaging Format)
- PublicationMetadata model serialisation round-trip
"""

from __future__ import annotations

import dataclasses
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from infrastructure.publishing.models import AuthorRecord, PublicationMetadata


# ---------------------------------------------------------------------------
# Helpers — local XML/JSON builders (stand-ins until a metadata_package module
# is implemented; these mirror the expected schema so tests remain useful as
# specs even before the module lands).
# ---------------------------------------------------------------------------


def build_onix_xml(meta: PublicationMetadata) -> str:
    """Produce a minimal ONIX 3.0 XML document for *meta*.

    Schema reference: https://www.editeur.org/93/Release-3.0-Downloads/
    """
    root = ET.Element("ONIXMessage", release="3.0")
    root.set("xmlns", "http://ns.editeur.org/onix/3.0/reference")

    header = ET.SubElement(root, "Header")
    ET.SubElement(header, "Sender").text = meta.publisher or "Unknown Publisher"
    ET.SubElement(header, "SentDateTime").text = "20260101T000000Z"
    ET.SubElement(header, "MessageNumber").text = "1"

    product = ET.SubElement(root, "Product")
    ET.SubElement(product, "RecordReference").text = meta.doi or "UNASSIGNED"
    ET.SubElement(product, "NotificationType").text = "03"  # confirmed record

    # Descriptive detail
    descriptive = ET.SubElement(product, "DescriptiveDetail")
    ET.SubElement(descriptive, "TitleDetail")
    title_el = ET.SubElement(descriptive.find("TitleDetail"), "TitleText")  # type: ignore[arg-type]
    title_el.text = meta.title

    for author in meta.authors:
        contributor = ET.SubElement(descriptive, "Contributor")
        ET.SubElement(contributor, "ContributorRole").text = "A01"  # author
        ET.SubElement(contributor, "PersonName").text = author

    # Subject keywords
    for kw in meta.keywords:
        subject = ET.SubElement(descriptive, "Subject")
        ET.SubElement(subject, "SubjectSchemeIdentifier").text = "20"  # keywords
        ET.SubElement(subject, "SubjectHeadingText").text = kw

    if meta.doi:
        product_id = ET.SubElement(product, "ProductIdentifier")
        ET.SubElement(product_id, "ProductIDType").text = "06"  # DOI
        ET.SubElement(product_id, "IDValue").text = meta.doi

    return ET.tostring(root, encoding="unicode", xml_declaration=False)


def build_metadata_json(meta: PublicationMetadata) -> dict:
    """Return a canonical metadata dict for a publishing manifest."""
    return {
        "schema_version": "1.0",
        "title": meta.title,
        "authors": meta.authors,
        "abstract": meta.abstract,
        "keywords": meta.keywords,
        "doi": meta.doi,
        "publisher": meta.publisher,
        "publication_date": meta.publication_date,
        "license": meta.license,
        "language": "en",
        "repository_url": meta.repository_url,
    }


def build_opf_skeleton(meta: PublicationMetadata) -> str:
    """Produce a minimal OPF (Open Packaging Format) 3.0 document."""
    root = ET.Element(
        "package",
        version="3.0",
        xmlns="http://www.idpf.org/2007/opf",
    )
    root.set("unique-identifier", "uid")

    metadata_el = ET.SubElement(root, "metadata")
    metadata_el.set("xmlns:dc", "http://purl.org/dc/elements/1.1/")

    ET.SubElement(metadata_el, "dc:title").text = meta.title
    for author in meta.authors:
        ET.SubElement(metadata_el, "dc:creator").text = author
    ET.SubElement(metadata_el, "dc:language").text = "en"
    if meta.publisher:
        ET.SubElement(metadata_el, "dc:publisher").text = meta.publisher
    if meta.publication_date:
        ET.SubElement(metadata_el, "dc:date").text = meta.publication_date

    if meta.doi:
        identifier = ET.SubElement(metadata_el, "dc:identifier")
        identifier.set("id", "uid")
        identifier.text = meta.doi
    else:
        identifier = ET.SubElement(metadata_el, "dc:identifier")
        identifier.set("id", "uid")
        identifier.text = "urn:uuid:placeholder"

    # Manifest and spine are required in a real OPF; stubs included for schema.
    ET.SubElement(root, "manifest")
    ET.SubElement(root, "spine")

    return ET.tostring(root, encoding="unicode", xml_declaration=False)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_meta() -> PublicationMetadata:
    return PublicationMetadata(
        title="Active Inference and the Free Energy Principle",
        authors=["Alice Smith", "Bob Jones"],
        abstract=(
            "This paper introduces a computational framework based on the Free Energy "
            "Principle and develops its implications for understanding perception and "
            "action in biological systems."
        ),
        keywords=["active inference", "free energy", "variational bayes", "neuroscience"],
        doi="10.5281/zenodo.12345678",
        publisher="Research Template Press",
        publication_date="2026-07-01",
        license="CC-BY-4.0",
        repository_url="https://github.com/docxology/template_active_inference",
    )


@pytest.fixture
def minimal_meta() -> PublicationMetadata:
    """Minimal metadata — only required fields."""
    return PublicationMetadata(
        title="Minimal Paper",
        authors=["Author One"],
        abstract="Brief abstract.",
        keywords=["keyword"],
    )


# ---------------------------------------------------------------------------
# ONIX XML tests
# ---------------------------------------------------------------------------


class TestOnixXmlGeneration:
    def test_produces_valid_xml(self, sample_meta: PublicationMetadata) -> None:
        xml_str = build_onix_xml(sample_meta)
        # Must parse without error
        root = ET.fromstring(xml_str)
        assert root is not None

    def test_root_element_is_onix_message(self, sample_meta: PublicationMetadata) -> None:
        xml_str = build_onix_xml(sample_meta)
        root = ET.fromstring(xml_str)
        assert root.tag.endswith("ONIXMessage") or "ONIXMessage" in root.tag

    def test_contains_title(self, sample_meta: PublicationMetadata) -> None:
        xml_str = build_onix_xml(sample_meta)
        assert sample_meta.title in xml_str

    def test_contains_authors(self, sample_meta: PublicationMetadata) -> None:
        xml_str = build_onix_xml(sample_meta)
        for author in sample_meta.authors:
            assert author in xml_str, f"Author {author!r} not found in ONIX XML"

    def test_contains_doi(self, sample_meta: PublicationMetadata) -> None:
        xml_str = build_onix_xml(sample_meta)
        assert sample_meta.doi in xml_str  # type: ignore[operator]

    def test_no_doi_still_valid_xml(self, minimal_meta: PublicationMetadata) -> None:
        xml_str = build_onix_xml(minimal_meta)
        root = ET.fromstring(xml_str)
        assert root is not None

    def test_keywords_included(self, sample_meta: PublicationMetadata) -> None:
        xml_str = build_onix_xml(sample_meta)
        for kw in sample_meta.keywords:
            assert kw in xml_str, f"Keyword {kw!r} not found in ONIX XML"

    def test_release_attribute(self, sample_meta: PublicationMetadata) -> None:
        xml_str = build_onix_xml(sample_meta)
        assert 'release="3.0"' in xml_str


# ---------------------------------------------------------------------------
# metadata.json tests
# ---------------------------------------------------------------------------


class TestMetadataJsonGeneration:
    def test_has_required_fields(self, sample_meta: PublicationMetadata) -> None:
        data = build_metadata_json(sample_meta)
        required = {"schema_version", "title", "authors", "abstract", "keywords", "license"}
        assert required <= data.keys()

    def test_title_matches(self, sample_meta: PublicationMetadata) -> None:
        data = build_metadata_json(sample_meta)
        assert data["title"] == sample_meta.title

    def test_authors_is_list(self, sample_meta: PublicationMetadata) -> None:
        data = build_metadata_json(sample_meta)
        assert isinstance(data["authors"], list)
        assert data["authors"] == sample_meta.authors

    def test_doi_field_present(self, sample_meta: PublicationMetadata) -> None:
        data = build_metadata_json(sample_meta)
        assert "doi" in data
        assert data["doi"] == sample_meta.doi

    def test_doi_none_when_absent(self, minimal_meta: PublicationMetadata) -> None:
        data = build_metadata_json(minimal_meta)
        assert data["doi"] is None

    def test_license_default(self, sample_meta: PublicationMetadata) -> None:
        data = build_metadata_json(sample_meta)
        assert data["license"] == "CC-BY-4.0"

    def test_serialises_to_json(self, sample_meta: PublicationMetadata, tmp_path: Path) -> None:
        data = build_metadata_json(sample_meta)
        out = tmp_path / "metadata.json"
        out.write_text(json.dumps(data, indent=2), encoding="utf-8")
        loaded = json.loads(out.read_text())
        assert loaded["title"] == sample_meta.title

    def test_keywords_list(self, sample_meta: PublicationMetadata) -> None:
        data = build_metadata_json(sample_meta)
        assert isinstance(data["keywords"], list)
        assert len(data["keywords"]) == len(sample_meta.keywords)

    def test_schema_version_is_string(self, sample_meta: PublicationMetadata) -> None:
        data = build_metadata_json(sample_meta)
        assert isinstance(data["schema_version"], str)


# ---------------------------------------------------------------------------
# OPF skeleton tests
# ---------------------------------------------------------------------------


class TestOpfSkeletonGeneration:
    def test_produces_valid_xml(self, sample_meta: PublicationMetadata) -> None:
        opf_str = build_opf_skeleton(sample_meta)
        root = ET.fromstring(opf_str)
        assert root is not None

    def test_root_is_package(self, sample_meta: PublicationMetadata) -> None:
        opf_str = build_opf_skeleton(sample_meta)
        root = ET.fromstring(opf_str)
        assert "package" in root.tag

    def test_contains_title(self, sample_meta: PublicationMetadata) -> None:
        opf_str = build_opf_skeleton(sample_meta)
        assert sample_meta.title in opf_str

    def test_contains_creator(self, sample_meta: PublicationMetadata) -> None:
        opf_str = build_opf_skeleton(sample_meta)
        for author in sample_meta.authors:
            assert author in opf_str

    def test_has_manifest_and_spine(self, sample_meta: PublicationMetadata) -> None:
        opf_str = build_opf_skeleton(sample_meta)
        assert "<manifest" in opf_str
        assert "<spine" in opf_str

    def test_doi_as_identifier_when_present(self, sample_meta: PublicationMetadata) -> None:
        opf_str = build_opf_skeleton(sample_meta)
        assert sample_meta.doi in opf_str  # type: ignore[operator]

    def test_placeholder_identifier_when_no_doi(self, minimal_meta: PublicationMetadata) -> None:
        opf_str = build_opf_skeleton(minimal_meta)
        assert "urn:uuid:placeholder" in opf_str

    def test_version_attribute(self, sample_meta: PublicationMetadata) -> None:
        opf_str = build_opf_skeleton(sample_meta)
        assert 'version="3.0"' in opf_str


# ---------------------------------------------------------------------------
# PublicationMetadata model tests
# ---------------------------------------------------------------------------


class TestPublicationMetadataModel:
    def test_required_fields_construct(self) -> None:
        meta = PublicationMetadata(
            title="Test Title",
            authors=["Author A"],
            abstract="An abstract.",
            keywords=["kw1", "kw2"],
        )
        assert meta.title == "Test Title"
        assert meta.authors == ["Author A"]

    def test_default_license_is_cc_by(self) -> None:
        meta = PublicationMetadata(
            title="T", authors=["A"], abstract="Ab.", keywords=["k"]
        )
        assert meta.license == "CC-BY-4.0"

    def test_optional_fields_default_to_none(self) -> None:
        meta = PublicationMetadata(
            title="T", authors=["A"], abstract="Ab.", keywords=["k"]
        )
        assert meta.doi is None
        assert meta.journal is None
        assert meta.publisher is None
        assert meta.publication_date is None
        assert meta.repository_url is None

    def test_full_construction(self, sample_meta: PublicationMetadata) -> None:
        assert sample_meta.doi == "10.5281/zenodo.12345678"
        assert len(sample_meta.authors) == 2
        assert sample_meta.publisher == "Research Template Press"

    def test_dataclass_fields_are_accessible(self) -> None:
        meta = PublicationMetadata(
            title="T", authors=["A"], abstract="Ab.", keywords=["k"]
        )
        fields = {f.name for f in dataclasses.fields(meta)}
        assert "title" in fields
        assert "authors" in fields
        assert "abstract" in fields
        assert "keywords" in fields
        assert "doi" in fields
        assert "license" in fields

    def test_author_records_default_empty(self) -> None:
        meta = PublicationMetadata(
            title="T", authors=["A"], abstract="Ab.", keywords=["k"]
        )
        assert meta.author_records == []

    def test_author_record_construction(self) -> None:
        ar = AuthorRecord(
            name="Alice Smith",
            orcid="0000-0001-2345-6789",
            affiliation="Test University",
            email="alice@example.com",
        )
        assert ar.name == "Alice Smith"
        assert ar.orcid == "0000-0001-2345-6789"

    def test_author_record_optional_fields(self) -> None:
        ar = AuthorRecord(name="Bob Jones")
        assert ar.orcid is None
        assert ar.affiliation is None
        assert ar.email is None

    def test_serialises_to_dict(self, sample_meta: PublicationMetadata) -> None:
        d = dataclasses.asdict(sample_meta)
        assert d["title"] == sample_meta.title
        assert d["authors"] == sample_meta.authors
        assert d["doi"] == sample_meta.doi

    def test_round_trip_via_json(self, sample_meta: PublicationMetadata, tmp_path: Path) -> None:
        d = dataclasses.asdict(sample_meta)
        out = tmp_path / "meta.json"
        out.write_text(json.dumps(d), encoding="utf-8")
        loaded = json.loads(out.read_text())
        assert loaded["title"] == sample_meta.title
        assert loaded["doi"] == sample_meta.doi
