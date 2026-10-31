"""Finite Ubuntu mirror priority policy for the prepared GitHub Actions runner.

The host policy follows Canonical cloud-init's ec2_region namespace and the
34 standard commercial AWS regions reviewed on 2026-10-30. It does not claim
that an unobserved hosted mirror file has any particular byte hash.

Sources:
https://github.com/canonical/cloud-init/blob/90f8d467c851c559a84a42f2e37c71f9cc4ba377/config/cloud.cfg.tmpl
https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-regions.html
https://github.com/actions/runner-images/blob/c74a28e5f8943ae6a39cac7c3701dd6bd0a2ea51/images/ubuntu/scripts/build/configure-apt-sources.sh
"""

# Admit reviewed regions explicitly; an unknown future region fails closed.
_EC2_REGIONS = (
    "af-south-1",
    "ap-east-1",
    "ap-east-2",
    "ap-northeast-1",
    "ap-northeast-2",
    "ap-northeast-3",
    "ap-south-1",
    "ap-south-2",
    "ap-southeast-1",
    "ap-southeast-2",
    "ap-southeast-3",
    "ap-southeast-4",
    "ap-southeast-5",
    "ap-southeast-6",
    "ap-southeast-7",
    "ca-central-1",
    "ca-west-1",
    "eu-central-1",
    "eu-central-2",
    "eu-north-1",
    "eu-south-1",
    "eu-south-2",
    "eu-west-1",
    "eu-west-2",
    "eu-west-3",
    "il-central-1",
    "me-central-1",
    "me-south-1",
    "mx-central-1",
    "sa-east-1",
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
)
_PRIMARY_HOSTS = ("azure.archive.ubuntu.com", *(f"{region}.ec2.archive.ubuntu.com" for region in _EC2_REGIONS))


def _rows(host: str, primary_priority: int, archive_priority: int) -> bytes:
    return (
        f"http://{host}/ubuntu/\tpriority:{primary_priority}\n"
        f"https://archive.ubuntu.com/ubuntu/\tpriority:{archive_priority}\n"
        "https://security.ubuntu.com/ubuntu/\tpriority:3\n"
    ).encode("ascii")


# Exact serialization gives three rows, fixed paths/protocols and only the two
# reviewed priority permutations. No URL or whitespace normalization occurs.
_PREFERRED_BY_INPUT = {
    _rows(host, primary, archive): _rows(host, 2, 1) for host in _PRIMARY_HOSTS for primary, archive in ((1, 2), (2, 1))
}
MAX_MIRROR_BYTES = max(map(len, _PREFERRED_BY_INPUT))


def prefer_primary_archive(data: bytes) -> bytes:
    """Return the approved priority swap, preserving every URL and row order."""
    if type(data) is not bytes:
        raise ValueError("Ubuntu mirror input must be bytes")
    try:
        return _PREFERRED_BY_INPUT[data]
    except KeyError:
        raise ValueError("Refusing an unknown Ubuntu APT mirror list") from None
