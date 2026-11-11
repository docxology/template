"""Exercise actual action-owned mirror policy with real bytes, without host APT writes."""

from pathlib import Path
import runpy
from typing import Any

import pytest


@pytest.fixture(scope="module")
def mirror_policy() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[3]
    return runpy.run_path(str(root / ".github/actions/setup-acceptance-documents/ubuntu_apt_mirrors.py"))


def _fixture_bytes(host: str, primary: int = 1, archive: int = 2) -> bytes:
    return (
        f"http://{host}/ubuntu/\tpriority:{primary}\n"
        f"https://archive.ubuntu.com/ubuntu/\tpriority:{archive}\n"
        "https://security.ubuntu.com/ubuntu/\tpriority:3\n"
    ).encode("ascii")


def _fallback_bytes(host: str) -> bytes:
    fallbacks = (
        ("us-east-1.ec2.archive.ubuntu.com", 4),
        ("us-west-2.ec2.archive.ubuntu.com", 5),
        ("eu-west-1.ec2.archive.ubuntu.com", 6),
    )
    return b"".join(
        f"http://{fallback}/ubuntu/\tpriority:{priority}\n".encode("ascii")
        for fallback, priority in fallbacks
        if fallback != host
    )


@pytest.mark.parametrize(
    "host",
    [
        "azure.archive.ubuntu.com",
        "us-east-2.ec2.archive.ubuntu.com",
        "ap-northeast-1.ec2.archive.ubuntu.com",
        "us-east-1.ec2.archive.ubuntu.com",
        "us-west-2.ec2.archive.ubuntu.com",
        "eu-west-1.ec2.archive.ubuntu.com",
    ],
)
@pytest.mark.parametrize("priorities", [(1, 2), (2, 1)], ids=["original", "already-preferred"])
def test_known_mirror_priorities_change_without_rewriting_urls(mirror_policy, host, priorities):
    before = _fixture_bytes(host, *priorities)
    after = mirror_policy["prefer_primary_archive"](before)
    preferred = _fixture_bytes(host, 2, 1)
    assert after == preferred + _fallback_bytes(host)
    assert after.startswith(preferred)
    assert after.count(f"http://{host}/ubuntu/".encode("ascii")) == 1
    assert mirror_policy["prefer_primary_archive"](after) == after


@pytest.mark.parametrize(
    "alteration",
    [
        (b"us-east-2.ec2.archive.ubuntu.com", b"us-east-99.ec2.archive.ubuntu.com"),
        (b"us-east-2.ec2.archive.ubuntu.com", b"unknown.example.com"),
        (b"us-east-2.ec2.archive.ubuntu.com", b"us-east-2.ec2.archive.ubuntu.com.evil.test"),
        (b"us-east-2.ec2.archive.ubuntu.com", b"user@us-east-2.ec2.archive.ubuntu.com"),
        (b"us-east-2.ec2.archive.ubuntu.com", b"us-east-2.ec2.archive.ubuntu.com:80"),
        (b"/ubuntu/\t", b"/ubuntu/?query=1\t"),
        (b"/ubuntu/\t", b"/ubuntu/#fragment\t"),
        (b"/ubuntu/\t", b"/ubuntu/../other/\t"),
        (b"/ubuntu/\t", b"/ubuntu/%2e%2e/\t"),
        (b"http://us-east-2", b"https://us-east-2"),
        (b"https://archive.ubuntu.com", b"http://archive.ubuntu.com"),
        (b"https://security.ubuntu.com", b"https://unknown.example.com"),
        (b"priority:2", b"priority:1"),
        (b"priority:3", b"priority:2"),
        (b"\t", b" "),
        (b"\n", b"\r\n"),
    ],
    ids=[
        "unknown-region",
        "unknown-host",
        "domain-suffix",
        "userinfo",
        "port",
        "query",
        "fragment",
        "traversal",
        "escaped-path",
        "primary-protocol",
        "archive-protocol",
        "security-host",
        "duplicate-priority",
        "security-priority",
        "space",
        "crlf",
    ],
)
def test_unknown_or_malformed_mirror_rows_are_refused(mirror_policy, alteration):
    before = _fixture_bytes("us-east-2.ec2.archive.ubuntu.com").replace(*alteration)
    with pytest.raises(ValueError, match="unknown Ubuntu APT mirror list"):
        mirror_policy["prefer_primary_archive"](before)


@pytest.mark.parametrize("suffix", [b"\n", b"extra\n", b"x" * 1024], ids=["blank-row", "extra-row", "oversized"])
def test_extra_mirror_bytes_are_refused(mirror_policy, suffix):
    with pytest.raises(ValueError, match="unknown Ubuntu APT mirror list"):
        mirror_policy["prefer_primary_archive"](_fixture_bytes("us-east-2.ec2.archive.ubuntu.com") + suffix)


def test_read_bound_covers_only_the_finite_reviewed_host_policy(mirror_policy):
    host = "ap-northeast-1.ec2.archive.ubuntu.com"
    longest_input = _fixture_bytes(host)
    longest = _fixture_bytes(host, 2, 1) + _fallback_bytes(host)
    assert len(longest) == mirror_policy["MAX_MIRROR_BYTES"] == 334
    assert mirror_policy["prefer_primary_archive"](longest_input) == longest
    assert mirror_policy["prefer_primary_archive"](longest) == longest
    # This is constructed policy input, not claimed to be captured hosted bytes.
    assert len(_fixture_bytes("us-east-2.ec2.archive.ubuntu.com")) == 152
