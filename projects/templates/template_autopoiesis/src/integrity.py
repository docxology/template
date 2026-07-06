"""Integrity hashing utilities for template_autopoiesis."""

from __future__ import annotations

import hashlib


def sha256_text(text: str) -> str:
    """Return hex SHA-256 of *text* encoded as UTF-8."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Return hex SHA-256 of raw *data*."""
    return hashlib.sha256(data).hexdigest()


def tree_hash_from_content_hashes(content_hashes: dict[str, str]) -> str:
    """Produce a stable tree hash from a path→hash mapping.

    Paths are sorted lexicographically before hashing to ensure
    that insertion order does not affect the result.
    """
    parts = [f"{k}:{v}" for k, v in sorted(content_hashes.items())]
    combined = "\n".join(parts)
    return sha256_text(combined)


def tree_hash(tree: dict[str, str]) -> str:
    """Alias for tree_hash_from_content_hashes for convenience."""
    return tree_hash_from_content_hashes(tree)


def merkle_root(hashes: list[str]) -> str:
    """Compute a Merkle root from an ordered list of hex digests.

    Each level pairwise-concatenates adjacent digests (left-to-right),
    hashing the concatenation.  A single node is its own root.  An
    empty list returns the SHA-256 of the empty string.
    """
    if not hashes:
        return sha256_text("")
    nodes = list(hashes)
    while len(nodes) > 1:
        next_level: list[str] = []
        for i in range(0, len(nodes), 2):
            left = nodes[i]
            right = nodes[i + 1] if i + 1 < len(nodes) else left
            next_level.append(sha256_text(left + right))
        nodes = next_level
    return nodes[0]
