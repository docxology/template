"""Separable evidence classes: which sub-digest each required gate actually binds.

A required gate is admitted against the smallest closure of digests that can
change its outcome, never against one repository-wide fingerprint. The taxonomy
mirrors :func:`infrastructure.validation.publication.gate.publication_affected_projects`,
which already distinguishes an exact-exemplar change (one scope), a documentation
change (no scope) and a shared-implementation change (every scope); that
classification was previously consulted only for roster selection.

Two properties keep this a narrowing rather than a weakening:

* every sub-digest is an existing producer, not a new hash;
* a gate whose artifact carries no class closure falls back to the historical
  repository-wide fingerprint comparison, so retained evidence is admitted with
  exactly today's strictness and no receipt becomes newly admissible.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Kinds whose outcome can be moved by ANY tracked public file. These keep the
# repository-wide fingerprint: narrowing them would be a real weakening.
_REPO_SPANNING_KINDS = frozenset(
    {
        "roster",
        "docs",
        "oracle",
        "root-policy",
        "root-case",
        "platform",
        "transfer",
    }
)

# Kinds owned by one scope. Their artifact already records that scope's own
# source and deliverable identities, which is the correct binding. ``coverage``
# belongs here because each coverage gate declares the exact ``source_files`` it
# must cover; the repo-wide 75% union floor is a different metric and is not a
# per-scope Requirement.
_SCOPE_OWNED_KINDS = frozenset(
    {"runtime", "coverage", "pipeline", "formats", "domain", "installed", "export", "live", "publication"}
)


@dataclass(frozen=True)
class ClassBinding:
    """The digests one gate is admitted against, with its recorded provenance."""

    digest: str
    members: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return the serialized form written into a gate artifact."""
        return {"sha256": self.digest, "members": list(self.members)}


def stage_digest(root: Path) -> str | None:
    """Return the shared stage-implementation digest, or ``None`` if unavailable.

    The stage closure covers every tracked file under ``infrastructure/`` and
    ``scripts/``, so it is one value for all exemplars. It is deliberately NOT
    cached: a process that admits evidence and then observes the tree again must
    see a changed stage closure, or the currency check in ``_check_class_binding``
    would silently accept stale evidence. Importing modules and writing
    ``__pycache__`` does not alter it, because only tracked source bytes
    participate.

    ``None`` means the closure cannot be established (a synthetic root, a
    partial checkout). Callers must then keep the strongest binding rather than
    admit a narrowed class it cannot substantiate.
    """
    from infrastructure.validation.rendered_snapshot import RenderedSnapshotError, _fingerprint, _stage_records

    try:
        return _fingerprint(_stage_records(Path(root))).sha256
    except (RenderedSnapshotError, OSError):
        return None


def class_binding(
    requirement: Any, root: Path, *, repository_fingerprint: str, stage: str | None = None
) -> ClassBinding:
    """Return the closure a gate of ``requirement``'s kind must be admitted against.

    ``stage`` may be supplied by a caller that resolves many gates in one pass;
    it is the same value for every scope-owned gate. When the stage closure is
    unavailable, a scope-owned gate is not narrowed: an unsubstantiated class
    falls back to the repository-wide digest.
    """
    kind = getattr(requirement, "kind", "")
    if kind in _SCOPE_OWNED_KINDS:
        resolved = stage if stage is not None else stage_digest(root)
        if resolved is None:
            return ClassBinding(repository_fingerprint, ("repository_fingerprint",))
        digest = _compose(
            {
                "source_identity": getattr(requirement, "source_identity", ""),
                "deliverables_identity": getattr(requirement, "deliverables_identity", ""),
                "stage": resolved,
            }
        )
        return ClassBinding(digest, ("source_identity", "deliverables_identity", "stage"))
    if kind in _REPO_SPANNING_KINDS:
        return ClassBinding(repository_fingerprint, ("repository_fingerprint",))
    # An unrecognized kind is never silently narrowed.
    return ClassBinding(repository_fingerprint, ("repository_fingerprint",))


def _compose(values: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for key in sorted(values):
        digest.update(key.encode())
        digest.update(b"\0")
        digest.update(values[key].encode())
        digest.update(b"\n")
    return digest.hexdigest()
