"""Source-pinned, unmodified OFL font bodies for the existing web typography.

The font constructor consumes whole held bytes; installed fonts, network URLs
and receipt JSON never select a replacement body. This does not grant browser
decoder, shaping, dependency or native-runtime admission.
"""

from __future__ import annotations

import base64
import hashlib
import json
import lzma
import math
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import read_bytes_confined

# Fixed Source nominations, generated from the genuine unchanged2.1.5 body
# inventory retained privately with this amendment, not from runtime requests.
FONT_BODIES: dict[str, dict[str, Any]] = {
    "LiberationMono-Bold": {
        "filename": "LiberationMono-Bold.ttf",
        "family": "Liberation Mono",
        "sha256": "bd62a0672d0b9b6710b01df434c80ad54fa5f0835207eb7b17b7a761463067bb",
        "bytes": 307996,
        "weight": "700",
        "style": "normal",
    },
    "LiberationMono-BoldItalic": {
        "filename": "LiberationMono-BoldItalic.ttf",
        "family": "Liberation Mono",
        "sha256": "79451f3c09fe25116098853b7a2ca6e2436220ccc11af022979adbcf195be130",
        "bytes": 284068,
        "weight": "700",
        "style": "italic",
    },
    "LiberationMono-Italic": {
        "filename": "LiberationMono-Italic.ttf",
        "family": "Liberation Mono",
        "sha256": "605c01c711b44480a7508d349dfbf3264e81fa43d69e61cfa7d10b86e764c4d1",
        "bytes": 281536,
        "weight": "400",
        "style": "italic",
    },
    "LiberationMono": {
        "filename": "LiberationMono-Regular.ttf",
        "family": "Liberation Mono",
        "sha256": "f2b83c763e8afd21709333370bed4774337fae82267937e2b5aea7e2fbd922c1",
        "bytes": 319508,
        "weight": "400",
        "style": "normal",
    },
    "LiberationSans-Bold": {
        "filename": "LiberationSans-Bold.ttf",
        "family": "Liberation Sans",
        "sha256": "788abee4c806d660e8aee46689dd8540cd4bb98da03dcc9d171ce3efd99a9173",
        "bytes": 414456,
        "weight": "700",
        "style": "normal",
    },
    "LiberationSans-BoldItalic": {
        "filename": "LiberationSans-BoldItalic.ttf",
        "family": "Liberation Sans",
        "sha256": "698da70fc191cc5f33ad4d6d3fe830fe4624b898ea2e3169955928b7c491f1ee",
        "bytes": 408996,
        "weight": "700",
        "style": "italic",
    },
    "LiberationSans-Italic": {
        "filename": "LiberationSans-Italic.ttf",
        "family": "Liberation Sans",
        "sha256": "e5bae5c4cde31f22142753855f4f8fb86da6ff39955ed3c0a11248b0d16948b0",
        "bytes": 415816,
        "weight": "400",
        "style": "italic",
    },
    "LiberationSans": {
        "filename": "LiberationSans-Regular.ttf",
        "family": "Liberation Sans",
        "sha256": "76d04c18ea243f426b7de1f3ad208e927008f961dc5945e5aad352d0dfde8ee8",
        "bytes": 410712,
        "weight": "400",
        "style": "normal",
    },
    "LiberationSerif-Bold": {
        "filename": "LiberationSerif-Bold.ttf",
        "family": "Liberation Serif",
        "sha256": "d754ba427cfe0bca54ae052384baa8f842da5bd6550ad4da024ac441e7a7d5ce",
        "bytes": 370096,
        "weight": "700",
        "style": "normal",
    },
    "LiberationSerif-BoldItalic": {
        "filename": "LiberationSerif-BoldItalic.ttf",
        "family": "Liberation Serif",
        "sha256": "f17db8af71e24d2066b587546021d4f0b296be389512b658dec3c09affeb11a7",
        "bytes": 376772,
        "weight": "700",
        "style": "italic",
    },
    "LiberationSerif-Italic": {
        "filename": "LiberationSerif-Italic.ttf",
        "family": "Liberation Serif",
        "sha256": "0e3dea9f8d613e006ccfa62201f33e265d19167bd0907725c3e145368b04fc2e",
        "bytes": 375632,
        "weight": "400",
        "style": "italic",
    },
    "LiberationSerif": {
        "filename": "LiberationSerif-Regular.ttf",
        "family": "Liberation Serif",
        "sha256": "058ea80864aef09a23f45cbec2bb5400bc3dfbdea01c3f10538a21fcb497fb74",
        "bytes": 393576,
        "weight": "400",
        "style": "normal",
    },
}
LICENSE_SHA256 = "a0c060f758d33ee59a674cd7b45914a560d0a5935968af5e87b0c6981fd89ddc"
FONT_BUFFER_SCHEMA = "template-source-web-font-buffer-v1"
LZMA_DECODER_SHA256 = "850305b783d09b71731f6f293d1f1ed58180892ff0e68c73475873b510f753a3"
LZMA_LICENSE_SHA256 = "2a85a87a012b6f2099902bc20e94f4292c222a80f66072ecf5151d1377377385"


def _clock(deadline: float | None) -> None:
    if deadline is not None and (
        type(deadline) not in (float, int) or not math.isfinite(deadline) or time.monotonic() >= deadline
    ):
        raise TimeoutError("Source web font body read exhausted its original caller clock")


def source_web_font_directory() -> Path:
    """Derive only the actually selected Source package asset directory."""
    return Path(__file__).resolve(strict=True).parent / "assets/fonts/liberation"


def _read(name: str, *, maximum: int, deadline: float | None) -> tuple[bytes, dict[str, Any]]:
    _clock(deadline)
    directory = source_web_font_directory()
    path = directory / name
    try:
        if path.is_symlink() or path.resolve(strict=True) != path:
            raise ValueError("Source web font nomination must be a physical package member")
    except OSError as error:
        raise ValueError("required Source web font/license package member is unavailable") from error
    before = path.stat()
    raw = read_bytes_confined(directory, path, max_bytes=maximum)
    after = path.stat()
    keys = ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns", "st_nlink")
    if any(getattr(before, key) != getattr(after, key) for key in keys):
        raise ValueError("actual Source web font/license bytes changed during read")
    _clock(deadline)
    return raw, {
        "path": str(path),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "metadata": {key: getattr(after, key) for key in keys},
    }


def read_source_web_font(name: str, *, deadline: float) -> tuple[bytes, dict[str, Any]]:
    """Read a fixed Source physical body; the caller supplies native authority."""
    declared = FONT_BODIES.get(name)
    if declared is None:
        raise ValueError("Source web font request is outside the declared physical cohort")
    raw, binding = _read(declared["filename"], maximum=512 * 1024, deadline=deadline)
    if binding["sha256"] != declared["sha256"] or binding["bytes"] != declared["bytes"]:
        raise ValueError("actual Source web font body differs from its fixed nomination")
    return raw, binding


def source_web_font_bundle(*, deadline: float | None = None) -> tuple[list[dict[str, Any]], str]:
    """Embed bodies and full OFL notice without modifying installed fonts."""
    license_bytes, license_binding = _read("OFL.txt", maximum=8192, deadline=deadline)
    if license_binding["sha256"] != LICENSE_SHA256:
        raise ValueError("Source web font distribution license changed")
    bodies = []
    for postscript, declared in FONT_BODIES.items():
        raw, binding = _read(declared["filename"], maximum=512 * 1024, deadline=deadline)
        if binding["sha256"] != declared["sha256"] or binding["bytes"] != declared["bytes"]:
            raise ValueError("Source renderer font body differs from its exact nomination")
        bodies.append(
            {
                "schema_version": FONT_BUFFER_SCHEMA,
                "postscript_name": postscript,
                "family": declared["family"],
                "weight": declared["weight"],
                "style": declared["style"],
                "sha256": binding["sha256"],
                "bytes": len(raw),
                "data": base64.b64encode(raw).decode("ascii"),
            }
        )
    return bodies, license_bytes.decode("utf-8")


@lru_cache(maxsize=1)
def _compressed_font_stream(raw: bytes) -> bytes:
    """Cache only compression; every caller first reads and hashes physical fonts."""
    if not raw or len(raw) > 6 * 1024 * 1024:
        raise ValueError("Source font transport exceeds its decoded byte bound")
    packed = lzma.compress(raw, format=lzma.FORMAT_ALONE, preset=6)
    if packed[:5] != b"\x5d\x00\x00\x80\x00" or len(packed) > 4 * 1024 * 1024:
        raise ValueError("Source font transport has unsupported LZMA properties or size")
    # FORMAT_ALONE streams normally use an unknown length. Pin the actual length
    # so the browser decoder has a finite, verified output bound before decoding.
    return packed[:5] + len(raw).to_bytes(8, "little") + packed[13:]


def _source_web_font_decoder() -> tuple[str, str]:
    directory = source_web_font_directory().parent
    bodies = []
    for name, expected in (("lzma-d-min.js", LZMA_DECODER_SHA256), ("LZMA-JS-LICENSE.txt", LZMA_LICENSE_SHA256)):
        path = directory / name
        if path.is_symlink() or path.resolve(strict=True) != path:
            raise ValueError("Source font transport decoder/license must be physical package members")
        before = path.stat()
        raw = read_bytes_confined(directory, path, max_bytes=8192)
        after = path.stat()
        keys = ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns", "st_nlink")
        if (
            any(getattr(before, key) != getattr(after, key) for key in keys)
            or hashlib.sha256(raw).hexdigest() != expected
        ):
            raise ValueError("Source font transport decoder/license differs from its exact nomination")
        bodies.append(raw.decode("utf-8"))
    return bodies[0], bodies[1]


def _source_web_font_payload(*, compressed: bool = False) -> str:
    bodies, license_text = source_web_font_bundle()
    payload: dict[str, Any] = {"faces": bodies, "license": license_text}
    if compressed:
        raw = b"".join(base64.b64decode(face.pop("data"), validate=True) for face in bodies)
        payload["stream"] = {
            "encoding": "lzma-alone-base64-v1",
            "bytes": len(raw),
            "data": base64.b64encode(_compressed_font_stream(raw)).decode("ascii"),
        }
    return json.dumps(payload, separators=(",", ":")).replace("<", "\\u003c")


def _source_web_font_loader() -> str:
    decoder, license_text = _source_web_font_decoder()
    return (
        "/*\n" + license_text + "\n*/\n"
        "window.templateSourceFontsPromise=(async()=>{\n"
        "const decoder=(function(){\n" + decoder + "\nreturn this.LZMA;}).call({});\n"
        "const payload=JSON.parse(document.getElementById('template-source-font-bodies').textContent);\n"
        "let packedRaw=null,offset=0;\n"
        "if(payload.stream!==undefined){\n"
        "const stream=payload.stream;\n"
        "if(!stream||stream.encoding!=='lzma-alone-base64-v1'||payload.faces.length!==12)"
        "throw Error('Unsupported Source font stream');\n"
        "const expected=payload.faces.reduce((sum,face)=>{"
        "if(!Number.isInteger(face.bytes)||face.bytes<1||face.bytes>512*1024)"
        "throw Error('Invalid Source font size');return sum+face.bytes;},0);\n"
        "if(expected>6*1024*1024||stream.bytes!==expected||typeof stream.data!=='string'||"
        "stream.data.length>Math.ceil(4*1024*1024/3)*4)throw Error('Invalid Source font stream size');\n"
        "const encoded=Uint8Array.from(atob(stream.data),c=>c.charCodeAt(0));\n"
        "if(encoded.length<13||encoded.length>4*1024*1024)throw Error('Invalid Source LZMA stream');\n"
        "const header=new DataView(encoded.buffer);\n"
        "if(encoded[0]!==0x5d||header.getUint32(1,true)!==8388608||"
        "header.getUint32(9,true)!==0||header.getUint32(5,true)!==expected)"
        "throw Error('Unsupported Source LZMA header');\n"
        "const decoded=decoder.decompress(encoded);\n"
        "if(!Array.isArray(decoded)||decoded.length!==expected)throw Error('Source font stream changed');\n"
        "packedRaw=Uint8Array.from(decoded);\n"
        "}\n"
        "const observations=[];\n"
        "for(const face of payload.faces){\n"
        "let raw;\n"
        "if(packedRaw){\n"
        "if(face.data!==undefined||face.encoding!==undefined)throw Error('Mixed Source font transports');\n"
        "raw=packedRaw.slice(offset,offset+face.bytes);offset+=face.bytes;\n"
        "}else{\n"
        "const encoded=Uint8Array.from(atob(face.data),c=>c.charCodeAt(0));\n"
        "const encoding=face.encoding===undefined?'base64':face.encoding;\n"
        "if(encoding==='base64')raw=encoded;\n"
        "else if(encoding==='gzip-base64'){\n"
        "const stream=new Blob([encoded]).stream().pipeThrough(new DecompressionStream('gzip'));\n"
        "raw=new Uint8Array(await new Response(stream).arrayBuffer());\n"
        "}else throw Error('Unsupported Source font transport encoding');\n"
        "}\n"
        "const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',raw)))"
        ".map(n=>n.toString(16).padStart(2,'0')).join('');\n"
        "if(raw.length!==face.bytes||hash!==face.sha256)throw Error('Source font buffer changed');\n"
        "const actual=new FontFace(face.family,raw.buffer,{weight:face.weight,style:face.style});\n"
        "await actual.load();document.fonts.add(actual);\n"
        "observations.push({schema_version:face.schema_version,postscript_name:face.postscript_name,"
        "family:face.family,weight:face.weight,style:face.style,sha256:hash,bytes:raw.length});\n"
        "}\n"
        "await document.fonts.ready;window.templateSourceFontBuffers=observations;return observations;\n"
        "})();\n"
        "window.templateSourceFontsPromise.catch(error=>{window.templateSourceFontError=String(error)});\n"
    )


def source_web_font_script() -> str:
    """Use actual FontFace buffers; retain constructor hashes in the document."""
    return (
        '<script type="application/json" id="template-source-font-bodies">'
        + _source_web_font_payload()
        + "</script>\n<script data-template-source-font-loader>\n"
        + _source_web_font_loader()
        + "</script>\n"
    )


def source_web_font_javascript() -> str:
    """Publish a lossless shared font stream and its local bounded decoder."""
    return (
        '(()=>{const node=document.createElement("script");'
        'node.type="application/json";node.id="template-source-font-bodies";'
        "node.textContent=JSON.stringify("
        + _source_web_font_payload(compressed=True)
        + ");document.head.appendChild(node);})();\n"
        + _source_web_font_loader()
    )
