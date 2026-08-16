"""Import-safe structural and resource validation for EPUB packages.

Rendering and later publication gates share this module so an EPUB accepted by
Stage 3 cannot be rejected later under a different package policy.  ZIP entry
metadata is validated before any member is read or ``ZipFile.testzip()`` is
called; this keeps corrupt or hostile archives from triggering unbounded
decompression during validation.
"""

from __future__ import annotations

import stat
import zipfile
from collections import Counter
from collections.abc import Iterable
from pathlib import PurePosixPath
from typing import Protocol, cast
from urllib.parse import unquote, urlsplit

_CONTAINER_MEMBER = "META-INF/container.xml"
_CONTAINER_NAMESPACE = "urn:oasis:names:tc:opendocument:xmlns:container"
_OPF_NAMESPACE = "http://www.idpf.org/2007/opf"
_XHTML_NAMESPACE = "http://www.w3.org/1999/xhtml"
_XHTML_MEDIA_TYPE = "application/xhtml+xml"
_SVG_NAMESPACE = "http://www.w3.org/2000/svg"
_XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"

# These limits are intentionally generous relative to the template's real
# publication packages while still bounding memory, CPU, and archive fan-out.
MAX_EPUB_MEMBERS = 4_096
MAX_EPUB_MEMBER_BYTES = 128 * 1024 * 1024
MAX_EPUB_TOTAL_COMPRESSED_BYTES = 512 * 1024 * 1024
MAX_EPUB_TOTAL_UNCOMPRESSED_BYTES = 512 * 1024 * 1024
MAX_EPUB_COMPRESSION_RATIO = 1_000
MAX_EPUB_XML_MEMBER_BYTES = 16 * 1024 * 1024


class _XmlElement(Protocol):
    """Structural subset of an Element used by the EPUB package checks."""

    tag: str

    def find(self, path: str) -> _XmlElement | None: ...

    def findall(self, path: str) -> list[_XmlElement]: ...

    def get(self, key: str, default: str | None = None) -> str | None: ...

    def itertext(self) -> Iterable[str]: ...


def _canonical_member_name(value: str) -> str | None:
    """Return canonical file-member syntax, rejecting ZIP path aliases."""

    if not value or "\x00" in value or "\\" in value or value.startswith("/"):
        return None
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts) or (
        len(parts[0]) == 2 and parts[0][0].isalpha() and parts[0][1] == ":"
    ):
        return None
    path = PurePosixPath(*parts)
    return path.as_posix() if not path.is_absolute() else None


def _canonical_entry_name(info: zipfile.ZipInfo) -> str | None:
    """Return an entry's canonical name, including a directory slash."""

    raw_name = info.filename
    if info.is_dir():
        if not raw_name.endswith("/"):
            return None
        canonical = _canonical_member_name(raw_name[:-1])
        return f"{canonical}/" if canonical is not None else None
    if raw_name.endswith("/"):
        return None
    return _canonical_member_name(raw_name)


def _preflight_members(infos: list[zipfile.ZipInfo]) -> dict[str, zipfile.ZipInfo]:
    """Validate all ZIP metadata before any decompression or member read."""

    if not infos:
        raise ValueError("EPUB archive is empty")
    if len(infos) > MAX_EPUB_MEMBERS:
        raise ValueError(f"EPUB archive exceeds member-count limit ({MAX_EPUB_MEMBERS})")
    if infos[0].filename != "mimetype" or infos[0].is_dir():
        raise ValueError("EPUB mimetype must be the first archive member")

    duplicate_members = sorted(name for name, count in Counter(info.filename for info in infos).items() if count > 1)
    if duplicate_members:
        raise ValueError(f"duplicate EPUB archive member: {duplicate_members[0]}")

    members: dict[str, zipfile.ZipInfo] = {}
    path_kinds: dict[str, bool] = {}
    total_compressed = 0
    total_uncompressed = 0
    for info in infos:
        canonical = _canonical_entry_name(info)
        if canonical is None or canonical != info.filename:
            raise ValueError(f"unsafe or non-canonical EPUB archive member: {info.filename}")

        logical_path = canonical[:-1] if info.is_dir() else canonical
        previous_kind = path_kinds.get(logical_path)
        if previous_kind is not None and previous_kind != info.is_dir():
            raise ValueError(f"EPUB archive member collides with a directory: {logical_path}")
        path_kinds[logical_path] = info.is_dir()

        if info.create_system == 3:
            file_type = stat.S_IFMT(info.external_attr >> 16)
            expected_types = {0, stat.S_IFDIR} if info.is_dir() else {0, stat.S_IFREG}
            if file_type not in expected_types:
                raise ValueError(f"EPUB archive contains a symlink or special member: {canonical}")

        if info.file_size < 0 or info.compress_size < 0:
            raise ValueError(f"EPUB archive member has impossible size metadata: {canonical}")
        if info.file_size > MAX_EPUB_MEMBER_BYTES:
            raise ValueError(f"EPUB archive member exceeds size limit: {canonical}")
        if info.compress_size > MAX_EPUB_MEMBER_BYTES:
            raise ValueError(f"EPUB compressed member exceeds size limit: {canonical}")
        if info.is_dir():
            if info.file_size != 0 or info.compress_size != 0:
                raise ValueError(f"EPUB directory member has nonzero size: {canonical}")
            continue
        if info.flag_bits & 0x1:
            raise ValueError(f"encrypted EPUB archive member is unsupported: {canonical}")
        if info.compress_type == zipfile.ZIP_STORED and info.file_size != info.compress_size:
            raise ValueError(f"stored EPUB member has inconsistent size metadata: {canonical}")
        if info.file_size and info.compress_size == 0:
            raise ValueError(f"EPUB archive member has an impossible compression ratio: {canonical}")
        if info.compress_size and info.file_size / info.compress_size > MAX_EPUB_COMPRESSION_RATIO:
            raise ValueError(f"EPUB archive member exceeds compression-ratio limit: {canonical}")

        total_compressed += info.compress_size
        if total_compressed > MAX_EPUB_TOTAL_COMPRESSED_BYTES:
            raise ValueError(
                f"EPUB archive exceeds aggregate compressed-size limit ({MAX_EPUB_TOTAL_COMPRESSED_BYTES} bytes)"
            )
        total_uncompressed += info.file_size
        if total_uncompressed > MAX_EPUB_TOTAL_UNCOMPRESSED_BYTES:
            raise ValueError(
                f"EPUB archive exceeds aggregate uncompressed-size limit ({MAX_EPUB_TOTAL_UNCOMPRESSED_BYTES} bytes)"
            )
        members[canonical] = info

    file_paths = {path for path, is_directory in path_kinds.items() if not is_directory}
    for logical_path in path_kinds:
        parts = PurePosixPath(logical_path).parts
        for depth in range(1, len(parts)):
            parent = PurePosixPath(*parts[:depth]).as_posix()
            if parent in file_paths:
                raise ValueError(f"EPUB file member is also a parent directory: {parent}")
    return members


def _resolve_reference(value: object, *, base: PurePosixPath, allow_fragment: bool) -> str | None:
    """Resolve one package URI to an archive-confined canonical member name."""

    if not isinstance(value, str) or not value.strip():
        return None
    parsed = urlsplit(value.strip())
    if parsed.scheme or parsed.netloc or parsed.query or (parsed.fragment and not allow_fragment):
        return None
    decoded = unquote(parsed.path)
    if not decoded or "\x00" in decoded or "\\" in decoded or decoded.startswith("/"):
        return None

    parts = list(base.parts)
    for part in decoded.split("/"):
        if part in {"", "."}:
            if part == "":
                return None
            continue
        if part == "..":
            if not parts:
                return None
            parts.pop()
            continue
        parts.append(part)
    if not parts:
        return None
    return _canonical_member_name(PurePosixPath(*parts).as_posix())


def _read_xml_member(
    archive: zipfile.ZipFile,
    members: dict[str, zipfile.ZipInfo],
    member_name: str,
) -> _XmlElement:
    """Read and safely parse one preflighted, bounded XML member."""

    info = members.get(member_name)
    if info is None:
        raise ValueError(f"missing EPUB package member: {member_name}")
    if info.file_size > MAX_EPUB_XML_MEMBER_BYTES:
        raise ValueError(f"EPUB XML member exceeds size limit: {member_name}")
    try:
        import defusedxml.ElementTree as safe_et
        from defusedxml.common import DefusedXmlException
    except ImportError as exc:
        raise ValueError("safe EPUB XML validation requires the 'defusedxml' package") from exc
    try:
        return cast(_XmlElement, safe_et.fromstring(archive.read(info)))
    except (DefusedXmlException, safe_et.ParseError, UnicodeError) as exc:
        raise ValueError(f"malformed EPUB XML member {member_name}: {exc}") from exc


def _normalized_element_text(element: _XmlElement | None) -> str:
    """Return collapsed descendant text for one XML element."""

    if element is None:
        return ""
    return " ".join("".join(str(value) for value in element.itertext()).split())


def _is_decorative_image(element: _XmlElement) -> bool:
    """Return whether an XHTML/SVG image explicitly opts out of announcement."""

    return element.get("aria-hidden") == "true" or element.get("role") in {"none", "presentation"}


def _require_local_image_target(
    source: object,
    *,
    document_member: str,
    members: dict[str, zipfile.ZipInfo],
    manifest_targets: set[str],
) -> str:
    """Resolve one image source and require a packaged, manifested target."""

    resolved = _resolve_reference(
        source,
        base=PurePosixPath(document_member).parent,
        allow_fragment=False,
    )
    if resolved is None:
        raise ValueError(f"EPUB image source is unsafe or invalid: {document_member}")
    if resolved not in members:
        raise ValueError(f"missing EPUB image member: {resolved}")
    if resolved not in manifest_targets:
        raise ValueError(f"EPUB image member is not declared in the OPF manifest: {resolved}")
    return resolved


def _validate_xhtml_images(
    document: _XmlElement,
    *,
    document_member: str,
    members: dict[str, zipfile.ZipInfo],
    manifest_targets: set[str],
) -> None:
    """Validate local image references and explicit accessibility semantics."""

    for image in document.findall(f".//{{{_XHTML_NAMESPACE}}}img"):
        _require_local_image_target(
            image.get("src"),
            document_member=document_member,
            members=members,
            manifest_targets=manifest_targets,
        )
        alt = image.get("alt")
        if alt is None:
            raise ValueError(f"EPUB XHTML image is missing an alt attribute: {document_member}")
        if not alt.strip() and not _is_decorative_image(image):
            raise ValueError(f"EPUB XHTML image has blank non-decorative alt text: {document_member}")

    for svg in document.findall(f".//{{{_SVG_NAMESPACE}}}svg"):
        svg_images = svg.findall(f".//{{{_SVG_NAMESPACE}}}image")
        if not svg_images:
            continue
        for image in svg_images:
            source = image.get(f"{{{_XLINK_NAMESPACE}}}href") or image.get("href")
            _require_local_image_target(
                source,
                document_member=document_member,
                members=members,
                manifest_targets=manifest_targets,
            )
        if _is_decorative_image(svg):
            continue
        if svg.get("role") != "img":
            raise ValueError(f"EPUB SVG image requires role=img: {document_member}")

        accessible_name = " ".join((svg.get("aria-label") or "").split())
        if not accessible_name:
            title = svg.find(f"{{{_SVG_NAMESPACE}}}title")
            labelled_by = (svg.get("aria-labelledby") or "").split()
            if labelled_by:
                if title is None or title.get("id") not in labelled_by:
                    raise ValueError(f"EPUB SVG image has unresolved aria-labelledby: {document_member}")
                accessible_name = _normalized_element_text(title)
            elif title is not None:
                accessible_name = _normalized_element_text(title)
        if not accessible_name:
            raise ValueError(f"EPUB SVG image requires non-blank accessible text: {document_member}")


def validate_epub_package(archive: zipfile.ZipFile) -> None:
    """Validate one open EPUB's bounded ZIP, container, OPF, and XHTML chain."""

    members = _preflight_members(archive.infolist())

    mimetype_info = members.get("mimetype")
    if mimetype_info is None:
        raise ValueError("missing EPUB mimetype member")
    if mimetype_info.compress_type != zipfile.ZIP_STORED:
        raise ValueError("EPUB mimetype member must be uncompressed")
    expected_mimetype = b"application/epub+zip"
    if mimetype_info.file_size != len(expected_mimetype) or archive.read(mimetype_info) != expected_mimetype:
        raise ValueError("invalid EPUB mimetype payload")
    if archive.testzip() is not None:
        raise ValueError("EPUB archive contains a member with a failed CRC")

    container = _read_xml_member(archive, members, _CONTAINER_MEMBER)
    if container.tag != f"{{{_CONTAINER_NAMESPACE}}}container":
        raise ValueError("EPUB container document has an invalid root element")
    rootfile_nodes = container.findall(f".//{{{_CONTAINER_NAMESPACE}}}rootfile")
    if not rootfile_nodes:
        raise ValueError("EPUB container declares no rootfile package")

    rootfile_members: list[str] = []
    for node in rootfile_nodes:
        if node.get("media-type") != "application/oebps-package+xml":
            continue
        resolved = _resolve_reference(
            node.get("full-path"),
            base=PurePosixPath(),
            allow_fragment=False,
        )
        if resolved is None:
            raise ValueError("EPUB container rootfile path is unsafe or invalid")
        rootfile_members.append(resolved)
    if not rootfile_members:
        raise ValueError("EPUB container declares no OPF rootfile")
    if len(set(rootfile_members)) != len(rootfile_members):
        raise ValueError("EPUB container declares a duplicate rootfile target")

    for rootfile_member in rootfile_members:
        package = _read_xml_member(archive, members, rootfile_member)
        if package.tag != f"{{{_OPF_NAMESPACE}}}package":
            raise ValueError(f"EPUB rootfile is not an OPF package document: {rootfile_member}")
        manifest = package.find(f"{{{_OPF_NAMESPACE}}}manifest")
        if manifest is None:
            raise ValueError(f"EPUB OPF package has no manifest: {rootfile_member}")

        item_ids: set[str] = set()
        local_targets: set[str] = set()
        xhtml_item_ids: set[str] = set()
        xhtml_targets: list[str] = []
        for item in manifest.findall(f"{{{_OPF_NAMESPACE}}}item"):
            item_id = item.get("id")
            if not item_id or item_id in item_ids:
                raise ValueError(f"EPUB OPF manifest has a missing or duplicate item id: {rootfile_member}")
            item_ids.add(item_id)

            href = item.get("href")
            parsed_href = urlsplit(href.strip()) if isinstance(href, str) else None
            is_remote = parsed_href is not None and bool(parsed_href.scheme or parsed_href.netloc)
            if is_remote:
                if item.get("media-type") == _XHTML_MEDIA_TYPE:
                    raise ValueError(f"EPUB XHTML manifest target must be local: {item_id}")
                continue
            target = _resolve_reference(
                href,
                base=PurePosixPath(rootfile_member).parent,
                allow_fragment=False,
            )
            if target is None:
                raise ValueError(f"EPUB manifest target is unsafe or invalid: {item_id}")
            if target in local_targets:
                raise ValueError(f"EPUB OPF manifest declares a duplicate local target: {target}")
            local_targets.add(target)
            if target not in members:
                raise ValueError(f"missing EPUB manifest member: {target}")
            if item.get("media-type") == _XHTML_MEDIA_TYPE:
                xhtml_item_ids.add(item_id)
                xhtml_targets.append(target)
        if not xhtml_targets:
            raise ValueError(f"EPUB OPF package declares no XHTML documents: {rootfile_member}")

        spine = package.find(f"{{{_OPF_NAMESPACE}}}spine")
        if spine is None:
            raise ValueError(f"EPUB OPF package has no spine: {rootfile_member}")
        spine_ids: list[str] = []
        for itemref in spine.findall(f"{{{_OPF_NAMESPACE}}}itemref"):
            idref = itemref.get("idref")
            if not idref or idref not in xhtml_item_ids:
                raise ValueError(f"EPUB spine references a missing or non-XHTML item: {idref}")
            spine_ids.append(idref)
        if not spine_ids:
            raise ValueError(f"EPUB OPF package has an empty spine: {rootfile_member}")
        if len(set(spine_ids)) != len(spine_ids):
            raise ValueError(f"EPUB OPF package has a duplicate spine reference: {rootfile_member}")

        for target in xhtml_targets:
            document = _read_xml_member(archive, members, target)
            if document.tag != f"{{{_XHTML_NAMESPACE}}}html":
                raise ValueError(f"EPUB XHTML member has a non-XHTML root element: {target}")
            _validate_xhtml_images(
                document,
                document_member=target,
                members=members,
                manifest_targets=local_targets,
            )
