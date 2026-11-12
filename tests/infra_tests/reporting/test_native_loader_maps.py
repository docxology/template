"""DATA predicate controls; these tests cannot qualify original native custody."""

import time

import pytest

from infrastructure.reporting.native_loader_maps import census_images, executable_census, parse_maps


def _maps():
    return parse_maps(
        b"1000-2000 r-xp 00000000 08:01 11 /original/tool\n3000-4000 r-xp 00000000 08:01 22 /owned/audit.so\n",
        deadline=time.monotonic() + 2,
    )


def _image():
    row = _maps()[0]
    return {
        "base": 4096,
        "body": {"identity": {"device": row["device"], "inode": 11}},
        "segments": [{"address": 4096, "memory_bytes": 4096, "file_offset": 0, "flags": 5}],
    }


def _census(rows, images):
    return executable_census(
        rows,
        images,
        helper_identity={"device": rows[0]["device"], "inode": 22},
        compiler={"path": "owned/compiler.json", "sha256": "0" * 64},
        page=4096,
        deadline=time.monotonic() + 2,
    )


def test_complete_callback_kernel_mapping_is_reconstructed():
    result = _census(_maps(), {1: _image()})
    assert [(row["kind"], row.get("object_id")) for row in result["rows"]] == [
        ("consumer-image", 1),
        ("source-instrumentation", None),
    ]


@pytest.mark.parametrize("change", ["inode", "offset", "anonymous", "writable", "alias"])
def test_actual_map_mismatch_cannot_qualify(change):
    rows, images = _maps(), {1: _image()}
    if change == "inode":
        rows[0]["inode"] += 1
    elif change == "offset":
        rows[0]["offset"] += 4096
    elif change == "anonymous":
        rows.insert(
            1, {"low": 8192, "high": 12288, "protection": "r-xp", "offset": 0, "device": 0, "inode": 0, "label": ""}
        )
    elif change == "writable":
        rows[0]["protection"] = "rwxp"
    else:
        images[2] = _image()
    with pytest.raises(ValueError):
        _census(rows, images)


def test_fini_resident_mapping_retains_its_original_closed_body():
    image = _image()
    rows = _maps()
    selected = census_images(rows, {1: image}, {}, [1], deadline=time.monotonic() + 2)
    assert selected == {1: image}
    assert _census(rows, selected)["rows"][0]["object_id"] == 1


def test_reloaded_live_image_supersedes_closed_lifetime_without_aliasing():
    image = _image()
    selected = census_images(_maps(), {1: image, 2: image}, {2: image}, [1], deadline=time.monotonic() + 2)
    assert selected == {2: image}


def test_reordered_kernel_map_is_refused():
    with pytest.raises(ValueError, match="order"):
        parse_maps(
            b"3000-4000 r-xp 0 08:01 22 /audit\n1000-2000 r-xp 0 08:01 11 /tool\n", deadline=time.monotonic() + 2
        )


def test_map_parser_uses_existing_finite_clock():
    with pytest.raises(TimeoutError):
        parse_maps(b"1000-2000 r-xp 0 08:01 11 /tool\n", deadline=time.monotonic() - 1)


def _auditor_elf():
    import struct

    content = bytearray(512)
    struct.pack_into(
        "<16sHHIQQQIHHHHHH",
        content,
        0,
        b"\x7fELF\x02\x01\x01" + b"\0" * 9,
        3,
        62,
        1,
        0,
        64,
        0,
        0,
        64,
        56,
        1,
        0,
        0,
        0,
    )
    struct.pack_into("<II6Q", content, 64, 1, 5, 0, 0, 0, len(content), len(content), 4096)
    return bytes(content)


def test_auditor_complete_source_elf_ranges_match_actual_kernel_body():
    from infrastructure.reporting.native_loader_helper_memory import helper_ranges

    base, ranges = helper_ranges(
        _maps(),
        {"device": _maps()[1]["device"], "inode": 22},
        _auditor_elf(),
        page=4096,
        deadline=time.monotonic() + 2,
    )
    assert base == 12288
    assert ranges == [{"address": 12288, "file_offset": 0, "bytes": 512}]


@pytest.mark.parametrize("change", ["extra", "missing", "file_offset", "extent", "writable"])
def test_auditor_source_code_cannot_admit_wrong_or_extra_mapping(change):
    from infrastructure.reporting.native_loader_helper_memory import helper_ranges

    rows = _maps()
    identity = {"device": rows[1]["device"], "inode": rows[1]["inode"]}
    if change == "extra":
        rows.append({**rows[1], "low": 20480, "high": 24576})
    elif change == "missing":
        rows.pop()
    elif change == "file_offset":
        rows[1]["offset"] = 4096
    elif change == "extent":
        rows[1]["high"] += 4096
    else:
        rows[1]["protection"] = "rwxp"
    with pytest.raises(ValueError):
        helper_ranges(rows, identity, _auditor_elf(), page=4096, deadline=time.monotonic() + 2)
