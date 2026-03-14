"""PDF metadata and XMP injection.

Populates the PDF Info dictionary and embeds XMP metadata packets with
document provenance, hash values, timestamps, and encrypted payloads.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infrastructure.core.logging_utils import get_logger
from infrastructure.steganography.config import DocumentMetadata

logger = get_logger(__name__)

def inject_pdf_metadata(
    input_pdf: Path,
    output_pdf: Path,
    metadata: dict[str, str],
    xmp_string: str | None = None,
    attachments: dict[str, bytes | None] = None,
) -> Path:
    """Inject metadata into PDF Info dictionary.

    Args:
        input_pdf: Source PDF file.
        output_pdf: Destination PDF file (may be the same as *input_pdf*).
        metadata: Key → value pairs to set.  Standard PDF keys include
                  ``/Title``, ``/Author``, ``/Subject``, ``/Keywords``,
                  ``/Creator``, ``/Producer``.  Custom keys are also
                  accepted (prefixed with ``/``).
        xmp_string: Optional XMP XML packet to embed in the PDF.
        attachments: Optional dict of ``filename`` → ``bytes`` to embed
                     as PDF file attachments (e.g. hash manifests).

    Returns:
        Path to the output PDF.
    """
    try:
        from pypdf import PdfReader, PdfWriter  # type: ignore[import-untyped]
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
    existing: dict[str, Any] = {}
    if reader.metadata:
        for key, value in reader.metadata.items():
            if isinstance(value, str):
                existing[key] = value

    # Merge: new values override existing
    merged = {**existing, **metadata}
    writer.add_metadata(merged)

    # Embed XMP metadata if provided
    if xmp_string:
        try:
            xmp_bytes = xmp_string.encode("utf-8")
            writer.xmp_metadata = xmp_bytes  # type: ignore[assignment]
            logger.debug(f"XMP metadata stream embedded ({len(xmp_bytes)} bytes)")
        except Exception as xmp_err:  # noqa: BLE001 — pypdf exceptions vary by PDF structure
            logger.warning(f"XMP embedding failed (non-fatal): {xmp_err}")

    # Embed file attachments if provided
    if attachments:
        for filename, content in attachments.items():
            try:
                writer.add_attachment(filename, content)
                logger.debug(f"Attachment embedded: {filename} ({len(content)} bytes)")
            except Exception as att_err:  # noqa: BLE001 — pypdf exceptions vary by PDF structure
                logger.warning(f"Attachment '{filename}' failed (non-fatal): {att_err}")

    with open(output_pdf, "wb") as fh:
        writer.write(fh)

    logger.info(
        "PDF metadata injected (%d keys) → %s",
        len(metadata),
        output_pdf.name,
    )
    return output_pdf

def build_document_metadata(doc: DocumentMetadata) -> dict[str, str]:
    """Build a metadata dictionary ready for PDF injection.

    Args:
        doc: Document identity fields.

    Returns:
        Dictionary of ``/Key`` → string value pairs.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    meta: dict[str, str] = {
        "/Creator": "Research Template Steganography Module",
        "/Producer": "infrastructure.steganography",
        "/CreationDate": timestamp,
        "/ModDate": timestamp,
    }

    if doc.title:
        meta["/Title"] = doc.title
    if doc.authors:
        meta["/Author"] = "; ".join(doc.authors)
    if doc.keywords:
        meta["/Keywords"] = "; ".join(doc.keywords)
    if doc.document_id:
        meta["/Subject"] = f"Document ID: {doc.document_id}"
        meta["/DocumentID"] = doc.document_id

    if doc.hashes:
        for algo, digest in doc.hashes.items():
            meta[f"/Hash_{algo.upper()}"] = digest

    meta["/SteganographyTimestamp"] = timestamp

    if doc.extra:
        for k, v in doc.extra.items():
            safe_key = k if k.startswith("/") else f"/{k}"
            meta[safe_key] = str(v)

    logger.debug(f"Built document metadata with {len(meta)} entries")
    return meta

def build_xmp_packet(doc: DocumentMetadata) -> str:
    """Build an XMP metadata XML packet.

    This generates a minimal Dublin Core + XMP Basic packet that can be
    embedded in the PDF.

    Args:
        doc: Document identity fields.

    Returns:
        XMP XML string.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    authors_xml = ""
    if doc.authors:
        items = "\n".join(f"            <rdf:li>{a}</rdf:li>" for a in doc.authors)
        authors_xml = f"""
        <dc:creator>
          <rdf:Seq>
{items}
          </rdf:Seq>
        </dc:creator>"""

    keywords_xml = ""
    if doc.keywords:
        items = "\n".join(f"            <rdf:li>{k}</rdf:li>" for k in doc.keywords)
        keywords_xml = f"""
        <dc:subject>
          <rdf:Bag>
{items}
          </rdf:Bag>
        </dc:subject>"""

    hash_xml = ""
    if doc.hashes:
        for algo, digest in doc.hashes.items():
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
            <rdf:li xml:lang="x-default">{doc.title}</rdf:li>
          </rdf:Alt>
        </dc:title>{authors_xml}{keywords_xml}
        <xmp:CreateDate>{timestamp}</xmp:CreateDate>
        <xmp:ModifyDate>{timestamp}</xmp:ModifyDate>
        <xmp:CreatorTool>Research Template Steganography</xmp:CreatorTool>
        <steg:document_id>{doc.document_id}</steg:document_id>{hash_xml}
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>"""

    logger.debug(f"XMP packet built ({len(xmp)} bytes)")
    return xmp
