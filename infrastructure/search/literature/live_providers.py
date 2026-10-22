"""Keyless bounded Crossref retrieval and explicitly licensed full-text custody."""

from __future__ import annotations

import io
import re
from datetime import date
from typing import Any
from urllib.parse import urlencode

from defusedxml import ElementTree

from infrastructure.search.literature.crossref_backend import crossref_item_to_paper
from infrastructure.search.literature.live_contract import (
    LiteratureBlocked,
    LiteratureFailed,
    LiveSession,
    exact_json,
    sha256,
    write_json,
)
from infrastructure.search.literature.live_transport import extract_pdf_text, fetch_bytes
from infrastructure.search.literature.models import Paper, merge_papers

CROSSREF_URL = "https://api.crossref.org/works"
EUROPEPMC_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"


def retrieve_crossref(
    session: LiveSession,
    query: str,
    *,
    label: str = "retrieval",
    endpoint: str = CROSSREF_URL,
) -> list[Paper]:
    """Use the existing field mapper/deduplicator, retaining exact provider bytes.

    This bounded acceptance sample intentionally selects deposited CC-BY-4.0
    version-of-record licenses and typed VOR PDF links, then retains only records
    with mapped authors and a publication year for complete citations. It is not
    exhaustive or unbiased. Downloaded identity, active rights and text are checked.
    """
    if not isinstance(query, str) or not query.strip() or len(query) > 2000:
        raise LiteratureFailed("retrieval query must be a bounded nonempty string")
    url = (
        endpoint
        + "?"
        + urlencode(
            {
                "query": query,
                "rows": session.settings.max_results,
                "filter": (
                    f"has-license:true,has-full-text:true,license.url:{LICENSE_URL}"
                    ",license.version:vor,full-text.version:vor,full-text.type:application/pdf"
                ),
            }
        )
    )
    raw, metadata = fetch_bytes(
        session,
        url,
        label,
        max_bytes=2 * 1024 * 1024,
        allow_loopback=endpoint != CROSSREF_URL,
    )
    payload = exact_json(raw)
    try:
        items = payload["message"]["items"]
    except (KeyError, TypeError) as exc:
        raise LiteratureFailed("Crossref returned an invalid search response") from exc
    if not isinstance(items, list) or len(items) > session.settings.max_results:
        raise LiteratureFailed("Crossref items violate the requested result ceiling")
    papers: list[Paper] = []
    excluded: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict) or not isinstance(item.get("DOI"), str) or not item["DOI"].strip():
            raise LiteratureFailed("Crossref result lacks an actual DOI")
        titles = item.get("title")
        if not isinstance(titles, list) or not titles or not isinstance(titles[0], str) or not titles[0].strip():
            raise LiteratureFailed("Crossref result lacks an actual title")
        paper = crossref_item_to_paper(item)
        if not paper.title.strip() or paper.id != "doi:" + item["DOI"]:
            raise LiteratureFailed("Crossref field mapping lost result identity")
        reasons = []
        if not paper.authors:
            reasons.append("missing_authors")
        if paper.year is None:
            reasons.append("missing_year")
        if reasons:
            excluded.append(
                {
                    "raw_index": index,
                    "paper_id": paper.id,
                    "doi": paper.doi,
                    "reasons": reasons,
                }
            )
        else:
            papers.append(paper)
    unique = merge_papers(papers)
    report = {
        "status": "passed" if unique else "blocked",
        "provider": "crossref",
        "query": query,
        "sample_scope": (
            "citation-complete CC-BY-4.0 VOR licenses/typed VOR PDF links; "
            "bounded eligible acceptance sample, not exhaustive or unbiased"
        ),
        "execution_mode": "live-network" if endpoint == CROSSREF_URL else "controlled-http",
        "raw_count": len(items),
        "eligible_count": len(papers),
        "excluded_count": len(excluded),
        "excluded_records": excluded,
        "unique_count": len(unique),
        "http": metadata,
        "deduplicated_count": len(papers) - len(unique),
        "paper_ids": [paper.id for paper in unique],
    }
    write_json(session.directory / f"{label}_report.json", report)
    if not unique:
        if not items:
            raise LiteratureBlocked("keyless retrieval returned no records for the configured query")
        raise LiteratureBlocked("bounded retrieval returned no citation-complete eligible records")
    return unique


def licensed_pdf_candidates(item: dict[str, Any], *, today: date | None = None) -> list[dict[str, str]]:
    """Require deposited, active CC-BY-4.0 rights for the same declared version.

    An unspecified license version cannot authorize a version-of-record download.
    Crossref's deposited license is provider evidence, not a legal certification.
    """
    current = today or date.today()
    versions: set[str] = set()
    for row in item.get("license", []):
        if not isinstance(row, dict) or row.get("URL") != LICENSE_URL:
            continue
        version = row.get("content-version")
        parts = row.get("start", {}).get("date-parts", [])
        if version not in {"vor", "am", "tdm"} or not parts or not isinstance(parts[0], list):
            continue
        try:
            values = parts[0]
            if len(values) != 3 or any(type(value) is not int for value in values):
                continue
            effective = date(*values)
        except (ValueError, TypeError):
            continue
        if effective <= current:
            versions.add(version)
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in item.get("link", []):
        if not isinstance(row, dict) or row.get("content-version") not in versions:
            continue
        url = row.get("URL")
        if (
            not isinstance(url, str)
            or url in seen
            or not url.startswith("https://")
            or (row.get("content-type") != "application/pdf" and not re.search(r"(?:/pdf|\.pdf)(?:\?|$)", url))
        ):
            continue
        seen.add(url)
        result.append({"url": url, "version": row["content-version"], "license_url": LICENSE_URL})
    return result[:3]


def _pdf_text(raw: bytes, doi: str) -> str:
    if not raw.lstrip().startswith(b"%PDF-"):
        raise LiteratureFailed("licensed full-text response is not a PDF")
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise LiteratureBlocked("pypdf is required for actual licensed PDF extraction") from exc
    try:
        reader = PdfReader(io.BytesIO(raw))
        if reader.is_encrypted or not 1 <= len(reader.pages) <= 200:
            raise LiteratureFailed("licensed PDF is encrypted, empty, or exceeds 200 pages")
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except (ValueError, OSError) as exc:
        raise LiteratureFailed("licensed PDF could not be parsed") from exc
    if len(text.strip()) < 200 or doi.lower() not in re.sub(r"\s+", "", text.lower()):
        raise LiteratureFailed("licensed PDF lacks substantial text or the selected paper DOI")
    return text


def parse_licensed_jats(raw: bytes, doi: str) -> tuple[str, str]:
    """Bind full-text article identity and its embedded reusable license to exact XML bytes."""
    try:
        root = ElementTree.fromstring(raw)
    except Exception as exc:  # defusedxml rejects DTD/entity attacks as well as malformed XML
        raise LiteratureFailed("full-text XML is unsafe or malformed") from exc
    identifiers = {
        "".join(node.itertext()).strip().lower() for node in root.findall(".//article-id[@pub-id-type='doi']")
    }
    if doi.lower() not in identifiers:
        raise LiteratureFailed("full-text XML does not identify the selected DOI")
    license_nodes = root.findall(".//license")
    licenses = {value for node in license_nodes for value in node.attrib.values()}
    licenses.update(value for node in license_nodes for child in node.iter() for value in child.attrib.values())
    valid = {"https://creativecommons.org/licenses/by/4.0/", "http://creativecommons.org/licenses/by/4.0/"}
    if not licenses & valid:
        raise LiteratureBlocked("full-text XML does not supply explicit CC-BY-4.0 license evidence")
    body = root.find(".//body")
    if body is None:
        raise LiteratureFailed("licensed article XML has no full-text body")
    text = " ".join(part.strip() for part in body.itertext() if part.strip())
    if len(text) < 200:
        raise LiteratureFailed("licensed article body is too short to constitute full text")
    return text, LICENSE_URL


def _europepmc_fulltext(
    session: LiveSession, paper: Paper, label: str, endpoint: str = EUROPEPMC_URL
) -> tuple[str, dict[str, Any]]:
    if not isinstance(paper.doi, str) or not paper.doi:
        raise LiteratureFailed("full-text candidate requires a real DOI")
    url = (
        endpoint
        + "/search?"
        + urlencode({"query": f'DOI:"{paper.doi}" AND OPEN_ACCESS:Y', "format": "json", "pageSize": 2})
    )
    raw, metadata = fetch_bytes(
        session, url, label + "_lookup", max_bytes=1024 * 1024, allow_loopback=endpoint != EUROPEPMC_URL
    )
    payload = exact_json(raw)
    if not isinstance(payload, dict) or not isinstance(payload.get("resultList"), dict):
        raise LiteratureFailed("Europe PMC lookup lacks the required result object")
    rows = payload.get("resultList", {}).get("result", [])
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise LiteratureFailed("Europe PMC lookup results must be a list of records")
    for row in rows:
        if any(key in row and not isinstance(row[key], str) for key in ("doi", "pmcid", "isOpenAccess")):
            raise LiteratureFailed("Europe PMC identifier and open-access fields must be strings")
    matches = [
        row
        for row in rows
        if isinstance(row, dict)
        and row.get("doi", "").lower() == paper.doi.lower()
        and row.get("isOpenAccess") == "Y"
        and re.fullmatch(r"PMC[0-9]+", row.get("pmcid", ""))
    ]
    if len(matches) != 1:
        raise LiteratureBlocked("selected DOI lacks a unique Europe PMC open-access full text")
    fulltext_url = endpoint + "/" + matches[0]["pmcid"] + "/fullTextXML"
    body, fulltext_metadata = fetch_bytes(
        session, fulltext_url, label + "_xml", max_bytes=8 * 1024 * 1024, allow_loopback=endpoint != EUROPEPMC_URL
    )
    text, license_url = parse_licensed_jats(body, paper.doi)
    return text, {
        "provider": "europepmc",
        "url": fulltext_url,
        "license_url": license_url,
        "license_evidence": "embedded JATS license URL",
        "doi": paper.doi,
        "source_sha256": sha256(body),
        "metadata_http": metadata,
        "http": fulltext_metadata,
    }


def licensed_fulltext(
    session: LiveSession, papers: list[Paper], *, europepmc_endpoint: str = EUROPEPMC_URL
) -> tuple[Paper, str, dict[str, Any]]:
    """Select one real reusable text from at most three retrieved candidates.

    Candidate unavailability is recorded; malformed responding producers fail
    acceptance immediately. No abstract or synthetic text can replace full text.
    """
    attempts: list[dict[str, Any]] = []
    for index, paper in enumerate(papers[:3]):
        if not isinstance(paper.doi, str) or not paper.doi:
            raise LiteratureFailed("full-text candidate requires a real DOI")
        for number, candidate in enumerate(licensed_pdf_candidates(paper.raw)):
            try:
                raw, metadata = fetch_bytes(
                    session, candidate["url"], f"fulltext_{index}_{number}", max_bytes=16 * 1024 * 1024
                )
                text = extract_pdf_text(
                    session,
                    session.directory / f"fulltext_{index}_{number}/body.bin",
                    paper.doi,
                    f"pdf_extract_{index}_{number}",
                )
                return _persist_fulltext(
                    session,
                    paper,
                    text,
                    {
                        "provider": "crossref-deposited-publisher-link",
                        "doi": paper.doi,
                        **candidate,
                        "license_evidence": "active deposited license for matching content-version",
                        "source_sha256": sha256(raw),
                        "http": metadata,
                        "attempts": attempts,
                    },
                )
            except LiteratureBlocked as exc:
                attempts.append(
                    {"paper_id": paper.id, "url": candidate["url"], "status": "blocked", "reason": str(exc)}
                )
        try:
            text, metadata = _europepmc_fulltext(session, paper, f"fulltext_{index}", europepmc_endpoint)
            metadata["attempts"] = attempts
            return _persist_fulltext(session, paper, text, metadata)
        except LiteratureBlocked as exc:
            attempts.append({"paper_id": paper.id, "provider": "europepmc", "status": "blocked", "reason": str(exc)})
    write_json(session.directory / "fulltext_attempts.json", attempts)
    raise LiteratureBlocked("none of the bounded retrieved candidates supplied identity-bound CC-BY-4.0 full text")


def _persist_fulltext(
    session: LiveSession, paper: Paper, text: str, metadata: dict[str, Any]
) -> tuple[Paper, str, dict[str, Any]]:
    path = session.directory / "fulltext.txt"
    path.write_text(text, encoding="utf-8")
    session.consume(path, text.encode("utf-8"))
    paper.fulltext = text
    metadata.update(status="passed", text_sha256=sha256(text.encode("utf-8")), text_characters=len(text))
    write_json(session.directory / "fulltext_receipt.json", metadata)
    return paper, text, metadata
