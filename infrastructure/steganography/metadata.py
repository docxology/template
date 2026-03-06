"""PDF metadata and XMP injection.

Populates the PDF Info dictionary and embeds XMP metadata packets with
document provenance, hash values, timestamps, and encrypted payloads.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


def inject_pdf_metadata(
    input_pdf: Path,
    output_pdf: Path,
    metadata: Dict[str, str],
) -> Path:
    """Inject metadata into PDF Info dictionary.

    Args:
        input_pdf: Source PDF file.
        output_pdf: Destination PDF file (may be the same as *input_pdf*).
        metadata: Key → value pairs to set.  Standard PDF keys include
                  ``/Title``, ``/Author``, ``/Subject``, ``/Keywords``,
                  ``/Creator``, ``/Producer``.  Custom keys are also
                  accepted (prefixed with ``/``).

    Returns:
        Path to the output PDF.
    """
    try:
        from pypdf import PdfReader, PdfWriter  # type: ignore
    except ImportError:
        raise ImportError(
            "The 'pypdf' package is required for PDF metadata injection. "
            "Install it with: pip install pypdf"
        )

    reader = PdfReader(str(input_pdf))
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    # Preserve existing metadata and overlay new values
    existing: Dict[str, Any] = {}
    if reader.metadata:
        for key, value in reader.metadata.items():
            if isinstance(value, str):
                existing[key] = value

    # Merge: new values override existing
    merged = {**existing, **metadata}
    writer.add_metadata(merged)

    with open(output_pdf, "wb") as fh:
        writer.write(fh)

    logger.info(
        "PDF metadata injected (%d keys) → %s",
        len(metadata),
        output_pdf.name,
    )
    return output_pdf


def build_document_metadata(
    title: str = "",
    authors: Optional[List[str]] = None,
    hashes: Optional[Dict[str, str]] = None,
    document_id: str = "",
    keywords: Optional[List[str]] = None,
    extra: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Build a metadata dictionary ready for PDF injection.

    Args:
        title: Document title.
        authors: List of author names.
        hashes: Algorithm → digest mapping.
        document_id: Unique document identifier.
        keywords: Keyword list (joined with ``;``).
        extra: Additional custom metadata entries.

    Returns:
        Dictionary of ``/Key`` → string value pairs.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    meta: Dict[str, str] = {
        "/Creator": "Research Template Steganography Module",
        "/Producer": "infrastructure.steganography",
        "/CreationDate": timestamp,
        "/ModDate": timestamp,
    }

    if title:
        meta["/Title"] = title
    if authors:
        meta["/Author"] = "; ".join(authors)
    if keywords:
        meta["/Keywords"] = "; ".join(keywords)
    if document_id:
        meta["/Subject"] = f"Document ID: {document_id}"
        meta["/DocumentID"] = document_id

    # Embed hash values as custom metadata
    if hashes:
        for algo, digest in hashes.items():
            key = f"/Hash_{algo.upper()}"
            meta[key] = digest

    meta["/SteganographyTimestamp"] = timestamp

    if extra:
        for k, v in extra.items():
            safe_key = k if k.startswith("/") else f"/{k}"
            meta[safe_key] = str(v)

    logger.debug("Built document metadata with %d entries", len(meta))
    return meta


def build_xmp_packet(
    title: str = "",
    authors: Optional[List[str]] = None,
    hashes: Optional[Dict[str, str]] = None,
    document_id: str = "",
    keywords: Optional[List[str]] = None,
) -> str:
    """Build an XMP metadata XML packet.

    This generates a minimal Dublin Core + XMP Basic packet that can be
    embedded in the PDF.

    Args:
        title: Document title.
        authors: Author list.
        hashes: Hash algorithm → digest mapping.
        document_id: Document identifier.
        keywords: Keyword list.

    Returns:
        XMP XML string.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    authors_xml = ""
    if authors:
        items = "\n".join(f"            <rdf:li>{a}</rdf:li>" for a in authors)
        authors_xml = f"""
        <dc:creator>
          <rdf:Seq>
{items}
          </rdf:Seq>
        </dc:creator>"""

    keywords_xml = ""
    if keywords:
        items = "\n".join(f"            <rdf:li>{k}</rdf:li>" for k in keywords)
        keywords_xml = f"""
        <dc:subject>
          <rdf:Bag>
{items}
          </rdf:Bag>
        </dc:subject>"""

    hash_xml = ""
    if hashes:
        for algo, digest in hashes.items():
            hash_xml += f'\n        <steg:hash_{algo}>{digest}</steg:hash_{algo}>'

    xmp = f"""<?xpacket begin="\xef\xbb\xbf" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about=""
        xmlns:dc="http://purl.org/dc/elements/1.1/"
        xmlns:xmp="http://ns.adobe.com/xap/1.0/"
        xmlns:steg="http://ns.research-template.org/steganography/1.0/">
        <dc:title>
          <rdf:Alt>
            <rdf:li xml:lang="x-default">{title}</rdf:li>
          </rdf:Alt>
        </dc:title>{authors_xml}{keywords_xml}
        <xmp:CreateDate>{timestamp}</xmp:CreateDate>
        <xmp:ModifyDate>{timestamp}</xmp:ModifyDate>
        <xmp:CreatorTool>Research Template Steganography</xmp:CreatorTool>
        <steg:document_id>{document_id}</steg:document_id>{hash_xml}
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>"""

    logger.debug("XMP packet built (%d bytes)", len(xmp))
    return xmp
