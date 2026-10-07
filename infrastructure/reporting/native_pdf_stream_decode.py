"""Finite supported PDF stream decoders used before native page parsing."""

from __future__ import annotations

from typing import Any

MAX_REFERENCE_BYTES = 250 * 1024 * 1024


def _bounded_predictor(data: bytes, params: dict[str, Any], limit: int) -> bytes:
    """Reverse supported predictors using byte buffers, with pre-allocation bounds."""
    from pdfminer.pdftypes import resolve1

    pred = resolve1(params.get("Predictor", 1))
    if pred == 1:
        return data
    colors, columns, bits = (
        resolve1(params.get(key, default)) for key, default in (("Colors", 1), ("Columns", 1), ("BitsPerComponent", 8))
    )
    if (
        any(type(value) is not int or value < 1 for value in (colors, columns, bits))
        or bits not in {1, 8}
        or type(pred) is not int
        or pred not in {2, 10, 11, 12, 13, 14, 15}
    ):
        raise ValueError("native Office bounded stream predictor is unsupported")
    row_bytes = (colors * columns * bits + 7) // 8
    if row_bytes > limit:
        raise ValueError("native Office stream predictor row exceeds finite decode budget")
    stride = row_bytes + (0 if pred == 2 else 1)
    if not data or len(data) % stride or (pred == 2 and bits != 8):
        raise ValueError("native Office stream predictor rows are malformed")
    output = bytearray()
    previous = bytearray(row_bytes)
    bpp = max(1, (colors * bits + 7) // 8)
    for offset in range(0, len(data), stride):
        filter_type = 1 if pred == 2 else data[offset]
        if filter_type not in {0, 1, 2, 3, 4}:
            raise ValueError("native Office stream predictor filter is unsupported")
        if len(output) + row_bytes > limit:
            raise ValueError("native Office predictor exceeds finite decode budget")
        start = offset + (0 if pred == 2 else 1)
        row = bytearray(data[start : start + row_bytes])
        for index in range(row_bytes):
            left = row[index - bpp] if index >= bpp else 0
            above = previous[index]
            upper_left = previous[index - bpp] if index >= bpp else 0
            if filter_type == 1:
                row[index] = (row[index] + left) & 255
            elif filter_type == 2:
                row[index] = (row[index] + above) & 255
            elif filter_type == 3:
                row[index] = (row[index] + (left + above) // 2) & 255
            elif filter_type == 4:
                distance = (abs(above - upper_left), abs(left - upper_left), abs(left + above - 2 * upper_left))
                predictor = (
                    left if distance[0] <= min(distance[1:]) else above if distance[1] <= distance[2] else upper_left
                )
                row[index] = (row[index] + predictor) & 255
        output.extend(row)
        previous = row
    return bytes(output)


def _bounded_ascii85(data: bytes, limit: int) -> bytes:
    output = bytearray()
    group: list[int] = []
    data = data.strip()
    if data.startswith(b"<~"):
        data = data[2:]
    for value in data:
        if value in b" \t\r\n\f\x00":
            continue
        if value == 126:
            break
        if value == 122:
            if group or len(output) + 4 > limit:
                raise ValueError("native Office ASCII85 exceeds finite decode budget or is malformed")
            output.extend(b"\x00" * 4)
            continue
        if not 33 <= value <= 117:
            raise ValueError("native Office ASCII85 stream is malformed")
        group.append(value - 33)
        if len(group) == 5:
            if len(output) + 4 > limit:
                raise ValueError("native Office ASCII85 exceeds finite decode budget")
            number = sum(item * 85 ** (4 - index) for index, item in enumerate(group))
            if number > 0xFFFFFFFF:
                raise ValueError("native Office ASCII85 group is malformed")
            output.extend(number.to_bytes(4, "big"))
            group = []
    if group:
        if len(group) == 1 or len(output) + len(group) - 1 > limit:
            raise ValueError("native Office ASCII85 final group exceeds finite budget or is malformed")
        size = len(group) - 1
        group.extend([84] * (5 - len(group)))
        number = sum(item * 85 ** (4 - index) for index, item in enumerate(group))
        if number > 0xFFFFFFFF:
            raise ValueError("native Office ASCII85 final group is malformed")
        output.extend(number.to_bytes(4, "big")[:size])
    return bytes(output)


def _bounded_stream_data(stream: Any, limit: int) -> bytes:
    """Decode supported image filters with a finite cap at every expansion.

    Unknown filters are explicit failures, never silently ignored. Opaque image
    codecs match PDFminer's unchanged encoded-stream treatment; their decoded
    visual pixels are observed separately by the actual native rasterizer.
    """
    import zlib
    from pdfminer.pdftypes import resolve1

    if type(limit) is not int or limit < 0 or stream.decipher:
        raise ValueError("native Office image decode requires a finite unencrypted stream")
    data = stream.get_rawdata()
    if not isinstance(data, bytes) or len(data) > MAX_REFERENCE_BYTES:
        raise ValueError("native Office image raw stream exceeds finite decode budget or was already decoded")
    for filter_name, params in stream.get_filters():
        name = filter_name.name
        if name in {"FlateDecode", "Fl"}:
            decoder = zlib.decompressobj()
            data = decoder.decompress(data, limit + 1)
            if len(data) > limit or decoder.unconsumed_tail:
                raise ValueError("native Office image expansion exceeds finite decode budget")
            if not decoder.eof or decoder.unused_data:
                raise ValueError("native Office compressed image stream is malformed")
        elif name in {"ASCII85Decode", "A85"}:
            data = _bounded_ascii85(data, limit)
        elif name in {"ASCIIHexDecode", "AHx"}:
            encoded = b"".join(data.split()).split(b">", 1)[0]
            if (len(encoded) + 1) // 2 > limit:
                raise ValueError("native Office ASCIIHex exceeds finite decode budget")
            data = bytes.fromhex((encoded + (b"0" if len(encoded) % 2 else b"")).decode("ascii"))
        elif name not in {"DCTDecode", "DCT", "JPXDecode", "JBIG2Decode"}:
            raise ValueError(f"native Office bounded image filter is unsupported: {name}")
        parameters = resolve1(params) if params else {}
        if not isinstance(parameters, dict):
            raise ValueError("native Office image filter parameters are malformed")
        data = _bounded_predictor(data, parameters, limit)
        if len(data) > limit:
            raise ValueError("native Office image filter exceeds finite decode budget")
    if len(data) > limit:
        raise ValueError("native Office image exceeds finite decode budget")
    return data
