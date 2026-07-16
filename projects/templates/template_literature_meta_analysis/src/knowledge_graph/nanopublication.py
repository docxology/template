"""Nanopublication dataclasses for literature assertions.

Provides Assertion and Nanopublication dataclasses along with factory,
serialization, and deserialization helpers. Nanopublications package a
single assertion together with provenance metadata following the
nanopublication standard (https://nanopub.net/): a small knowledge graph
with (1) Assertion, (2) Provenance, and (3) Publication Info.

- JSON Lines (one JSON object per line) is used for efficient streaming
  and append-friendly storage in the pipeline.
- RDF/TriG export produces standards-compliant nanopublications suitable
  for the nanopublication network and FAIR dissemination.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rdflib import Dataset

logger = logging.getLogger(__name__)

# RDF namespaces for nanopublication standard (https://nanopub.net/)
NP_NS = "http://www.nanopub.org/nschema#"
PROV_NS = "http://www.w3.org/ns/prov#"
DC_NS = "http://purl.org/dc/terms/"
XSD_NS = "http://www.w3.org/2001/XMLSchema#"
AIF_NS = "http://example.org/litmeta/ontology/"
AIF_NANOPUB_BASE = "http://example.org/litmeta/nanopub/"
DEFAULT_LICENSE = "https://creativecommons.org/publicdomain/zero/1.0/"


@dataclass
class Assertion:
    """A claim extracted from a paper about a concept in the literature.

    Attributes:
        assertion_id: Unique identifier for this assertion.
        paper_id: Canonical ID of the source paper.
        claim: The assertion text.
        assertion_type: One of ``"supports"``, ``"contradicts"``, ``"neutral"``.
        hypothesis_id: Which hypothesis this relates to (key from
            ``HYPOTHESIS_CATEGORIES``).
        confidence: Confidence level in the range ``[0.0, 1.0]``.
        citation_count: Citations of the source paper (used for scoring weight).
    """

    assertion_id: str
    paper_id: str
    claim: str
    assertion_type: str  # "supports", "contradicts", "neutral"
    hypothesis_id: str  # key from HYPOTHESIS_CATEGORIES
    confidence: float = 1.0
    citation_count: int = 0


@dataclass
class Nanopublication:
    """A nanopublication packaging an assertion with provenance.

    Attributes:
        nanopub_id: Unique identifier for this nanopublication.
        assertion: The core assertion being published.
        attribution: Who created this nanopublication.
        created_date: ISO-format timestamp of creation.
    """

    nanopub_id: str
    assertion: Assertion
    attribution: str = ""
    created_date: str = ""


def create_nanopub(assertion: Assertion, attribution: str = "") -> Nanopublication:
    """Create a new nanopublication wrapping the given assertion.

    Generates a unique nanopub_id and sets created_date to the current
    UTC timestamp in ISO format.

    Args:
        assertion: The assertion to wrap.
        attribution: Optional attribution string (e.g. author or pipeline name).

    Returns:
        A fully populated Nanopublication instance.
    """
    return Nanopublication(
        nanopub_id=f"nanopub:{uuid.uuid4().hex[:12]}",
        assertion=assertion,
        attribution=attribution,
        created_date=datetime.now(timezone.utc).isoformat(),
    )


def nanopub_to_dict(nanopub: Nanopublication) -> dict:
    """Serialize a Nanopublication to a plain dictionary.

    Args:
        nanopub: The nanopublication to serialize.

    Returns:
        Dictionary suitable for JSON serialization.
    """
    return {
        "nanopub_id": nanopub.nanopub_id,
        "assertion": {
            "assertion_id": nanopub.assertion.assertion_id,
            "paper_id": nanopub.assertion.paper_id,
            "claim": nanopub.assertion.claim,
            "assertion_type": nanopub.assertion.assertion_type,
            "hypothesis_id": nanopub.assertion.hypothesis_id,
            "confidence": nanopub.assertion.confidence,
            "citation_count": nanopub.assertion.citation_count,
        },
        "attribution": nanopub.attribution,
        "created_date": nanopub.created_date,
    }


def nanopub_from_dict(data: dict) -> Nanopublication:
    """Deserialize a Nanopublication from a plain dictionary.

    Args:
        data: Dictionary previously produced by ``nanopub_to_dict``.

    Returns:
        Reconstructed Nanopublication instance.
    """
    a = data["assertion"]
    assertion = Assertion(
        assertion_id=a["assertion_id"],
        paper_id=a["paper_id"],
        claim=a["claim"],
        assertion_type=a["assertion_type"],
        hypothesis_id=a["hypothesis_id"],
        confidence=a.get("confidence", 1.0),
        citation_count=a.get("citation_count", 0),
    )
    return Nanopublication(
        nanopub_id=data["nanopub_id"],
        assertion=assertion,
        attribution=data.get("attribution", ""),
        created_date=data.get("created_date", ""),
    )


def serialize_nanopubs(nanopubs: list[Nanopublication], path: Path) -> None:
    """Write nanopublications to a JSON Lines file.

    Each line contains one JSON object representing a single nanopublication.

    Args:
        nanopubs: List of nanopublications to serialize.
        path: Destination file path (will be overwritten if it exists).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for np_obj in nanopubs:
            line = json.dumps(nanopub_to_dict(np_obj), ensure_ascii=False)
            fh.write(line + "\n")


def deserialize_nanopubs(path: Path) -> list[Nanopublication]:
    """Read nanopublications from a JSON Lines file.

    Args:
        path: Source file path containing one JSON object per line.

    Returns:
        List of deserialized Nanopublication instances.
    """
    nanopubs: list[Nanopublication] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                data = json.loads(line)
                nanopubs.append(nanopub_from_dict(data))
    return nanopubs


def merge_nanopubs(
    existing: list[Nanopublication],
    new: list[Nanopublication],
) -> list[Nanopublication]:
    """Merge two lists of nanopublications, deduplicating by assertion key.

    The composite key ``(paper_id, hypothesis_id)`` uniquely identifies an
    assertion.  When duplicates exist the *new* entry wins so that re-runs
    with improved models can overwrite stale results.

    Args:
        existing: Previously saved nanopublications.
        new: Freshly extracted nanopublications to merge in.

    Returns:
        Merged list with duplicates removed.
    """
    seen: dict[tuple[str, str], Nanopublication] = {}
    for np_obj in existing:
        key = (np_obj.assertion.paper_id, np_obj.assertion.hypothesis_id)
        seen[key] = np_obj
    for np_obj in new:
        key = (np_obj.assertion.paper_id, np_obj.assertion.hypothesis_id)
        seen[key] = np_obj  # new wins
    return list(seen.values())


def get_processed_paper_ids(nanopubs: list[Nanopublication]) -> set[str]:
    """Extract the set of unique paper IDs from nanopublications.

    Useful for determining which papers have already been processed
    so that incremental runs can skip them.

    Args:
        nanopubs: List of nanopublications to inspect.

    Returns:
        Set of canonical paper IDs.
    """
    return {np_obj.assertion.paper_id for np_obj in nanopubs}


def append_nanopubs(
    new_nanopubs: list[Nanopublication],
    path: Path,
) -> list[Nanopublication]:
    """Atomically append nanopublications to an existing JSONL file.

    Reads the existing file (if present), merges with the new entries
    (deduplicating by ``(paper_id, hypothesis_id)`` — new wins), and
    writes the result atomically via a temporary file + rename.

    This is the **single source of truth** for incremental persistence:
    every checkpoint flush writes directly to the nanopublications file
    so that interrupts never lose already-checkpointed work.

    Args:
        new_nanopubs: Freshly extracted nanopublications to persist.
        path: Destination JSONL file (created if absent).

    Returns:
        The merged list of all nanopublications now on disk.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = deserialize_nanopubs(path) if path.exists() else []
    merged = merge_nanopubs(existing, new_nanopubs)
    # Atomic write: temp file → rename
    tmp = path.with_suffix(".jsonl.tmp")
    serialize_nanopubs(merged, tmp)
    tmp.rename(path)
    logger.info(
        "📄 Wrote %d nanopubs → %s",
        len(merged),
        path,
    )
    return merged


def _nanopub_resource_uri(nanopub_id: str, base_uri: str = AIF_NANOPUB_BASE) -> str:
    """Turn nanopub_id (e.g. nanopub:abc123) into a full resource URI."""
    local = nanopub_id.replace("nanopub:", "").strip()
    if not local:
        local = uuid.uuid4().hex[:12]
    return base_uri.rstrip("/") + "/" + local


def _safe_uri_fragment(s: str) -> str:
    """Replace characters that are unsafe in URI fragments."""
    return re.sub(r"[^A-Za-z0-9_.-]", "_", s)


def nanopub_to_rdf(
    nanopub: Nanopublication,
    base_uri: str = AIF_NANOPUB_BASE,
) -> "Dataset":
    """Serialize a single nanopublication to RDF (TriG) per https://nanopub.net/.

    Produces a nanopublication with four named graphs:
    - **Head**: the nanopub resource with np:hasAssertion, np:hasProvenance,
      np:hasPublicationInfo linking to the three graphs below.
    - **Assertion**: the main content (paper → assertion → hypothesis; claim;
      confidence; citation count).
    - **Provenance**: how the assertion was generated (agent, time, method).
    - **Publication info**: creator, created date, license.

    Args:
        nanopub: The nanopublication to serialize.
        base_uri: Base URI for nanopub resources (default generic ontology).

    Returns:
        An rdflib Dataset containing the four named graphs for this nanopub.
    """
    from rdflib import Dataset, Literal, Namespace, URIRef
    from rdflib.namespace import RDF

    np_ns = Namespace(NP_NS)
    prov_ns = Namespace(PROV_NS)
    dc_ns = Namespace(DC_NS)
    aif_ns = Namespace(AIF_NS)
    xsd_ns = Namespace(XSD_NS)
    np_nanopub_class = URIRef(NP_NS + "Nanopublication")

    ds: Dataset = Dataset()
    np_uri = _nanopub_resource_uri(nanopub.nanopub_id, base_uri)
    head_uri = URIRef(np_uri + "#head")
    assertion_graph_uri = URIRef(np_uri + "#assertion")
    provenance_graph_uri = URIRef(np_uri + "#provenance")
    pubinfo_graph_uri = URIRef(np_uri + "#pubinfo")

    np_res = URIRef(np_uri)
    a = nanopub.assertion
    paper_uri = URIRef(aif_ns["paper/" + _safe_uri_fragment(a.paper_id)])
    assertion_uri = URIRef(aif_ns["assertion/" + _safe_uri_fragment(a.assertion_id)])
    hypothesis_uri = URIRef(aif_ns["hypothesis/" + a.hypothesis_id.lower()])

    # Head graph: this nanopublication links to the three components (nanopub.net)
    head_g = ds.graph(head_uri)
    head_g.add((np_res, np_ns.hasAssertion, assertion_graph_uri))
    head_g.add((np_res, np_ns.hasProvenance, provenance_graph_uri))
    head_g.add((np_res, np_ns.hasPublicationInfo, pubinfo_graph_uri))
    head_g.add((np_res, RDF.type, np_nanopub_class))

    # Assertion graph: main content (atomic unit of information)
    assn_g = ds.graph(assertion_graph_uri)
    assn_g.add((paper_uri, aif_ns["asserts"], assertion_uri))
    if a.assertion_type == "supports":
        assn_g.add((assertion_uri, aif_ns["supports"], hypothesis_uri))
    elif a.assertion_type == "contradicts":
        assn_g.add((assertion_uri, aif_ns["contradicts"], hypothesis_uri))
    else:
        assn_g.add((assertion_uri, aif_ns["neutral"], hypothesis_uri))
    assn_g.add((assertion_uri, aif_ns["claim"], Literal(a.claim, datatype=xsd_ns.string)))
    assn_g.add((assertion_uri, aif_ns["confidence"], Literal(a.confidence, datatype=xsd_ns.double)))
    assn_g.add((assertion_uri, aif_ns["citationCount"], Literal(a.citation_count, datatype=xsd_ns.integer)))

    # Provenance graph: how the assertion came to be
    prov_g = ds.graph(provenance_graph_uri)
    prov_g.add((assertion_uri, prov_ns.wasGeneratedBy, np_res))
    if nanopub.created_date:
        prov_g.add((assertion_uri, prov_ns.generatedAtTime, Literal(nanopub.created_date, datatype=xsd_ns.dateTime)))
    if nanopub.attribution:
        prov_g.add((assertion_uri, prov_ns.wasAttributedTo, Literal(nanopub.attribution, datatype=xsd_ns.string)))
    prov_g.add((assertion_uri, prov_ns.hadPrimarySource, paper_uri))

    # Publication info graph: metadata about the nanopublication
    pub_g = ds.graph(pubinfo_graph_uri)
    pub_g.add((np_res, dc_ns.created, Literal(nanopub.created_date or "", datatype=xsd_ns.dateTime)))
    if nanopub.attribution:
        pub_g.add((np_res, dc_ns.creator, Literal(nanopub.attribution, datatype=xsd_ns.string)))
    pub_g.add((np_res, dc_ns.license, URIRef(DEFAULT_LICENSE)))

    return ds


def serialize_nanopubs_to_trig(
    nanopubs: list[Nanopublication],
    path: Path,
    base_uri: str = AIF_NANOPUB_BASE,
) -> None:
    """Write nanopublications to a TriG file in RDF format per https://nanopub.net/.

    Each nanopublication is represented as four named graphs (head, assertion,
    provenance, publication info). The resulting file can be published to the
    nanopublication network and is suitable for FAIR dissemination.

    Args:
        nanopubs: List of nanopublications to serialize.
        path: Destination .trig file path (will be overwritten if exists).
        base_uri: Base URI for nanopub resources.
    """
    from rdflib import Dataset

    path.parent.mkdir(parents=True, exist_ok=True)
    combined: Dataset = Dataset()
    for np_obj in nanopubs:
        ds = nanopub_to_rdf(np_obj, base_uri)
        for g in ds.graphs():
            for t in g:
                combined.get_context(g.identifier).add(t)
    serialized = combined.serialize(format="trig", encoding="utf-8")
    path.write_bytes(serialized.rstrip() + b"\n")
    logger.info("📄 Wrote %d nanopublication(s) in RDF/TriG → %s", len(nanopubs), path)
