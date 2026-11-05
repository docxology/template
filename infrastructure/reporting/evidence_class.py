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


class ClassUnavailable(Exception):
    """A scope-owned class that cannot be substantiated in this checkout.

    Failing closed means refusing when a class cannot be proved. It does not
    mean substituting the repository-wide fingerprint, which is a broader claim
    that would admit stale per-scope evidence. The cause is carried so a refusal
    names what is missing instead of looking like a generic staleness.

    This must NOT be a frozen dataclass. CPython assigns ``__traceback__`` on
    every raised exception and pytest's ``pytest.raises(...) as info`` handler
    assigns it again, so freezing the instance raises ``FrozenInstanceError``
    from inside the exception machinery. A plain ``raise``/``except`` never
    touches that attribute, which is why only tests that inspect the exception
    object exposed it.
    """

    def __init__(self, kind: str, scope: str, cause: str) -> None:
        super().__init__(kind, scope, cause)
        self.kind = kind
        self.scope = scope
        self.cause = cause

    def __str__(self) -> str:
        """Return the refusal text recorded on the gate."""
        return f"evidence class unavailable for {self.kind} ({self.scope}): {self.cause}"


def unavailable_cause(root: Path) -> str:
    """Return why the stage closure cannot be established for ``root``."""
    missing = uninitialized_submodules(root)
    if missing:
        return f"declared submodule not checked out: {', '.join(missing)}"
    return "tracked infrastructure/scripts closure is unreadable in this checkout"


def uninitialized_submodules(root: Path) -> tuple[str, ...]:
    """Return declared submodule paths that are not checked out.

    A submodule contributes tracked files to the stage closure (the ``kmyth``
    subtree adds 125 of 1725 records). If one is not initialized, the stage
    digest is silently *smaller* and will not match a receipt produced from a
    complete checkout, so the same commit appears to have two different
    identities. That ambiguity must be refused rather than resolved by whichever
    checkout happened to run first.
    """
    import subprocess

    observed = subprocess.run(
        ["git", "-C", str(root), "submodule", "status"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        env={
            "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
            "LC_ALL": "C",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_TERMINAL_PROMPT": "0",
        },
    )
    if observed.returncode != 0:
        return ()
    missing: list[str] = []
    for line in observed.stdout.splitlines():
        # ' <sha> <path>' is initialized; '-<sha> <path>' is not.
        if line.startswith("-"):
            parts = line[1:].split()
            if len(parts) >= 2:
                missing.append(parts[1])
    return tuple(missing)


def stage_digest(root: Path, *, require_submodules: bool = True) -> str | None:
    """Return the shared stage-implementation digest, or ``None`` if unavailable.

    The stage closure covers every tracked file under ``infrastructure/`` and
    ``scripts/``, so it is one value for all exemplars. It is deliberately NOT
    cached: a process that admits evidence and then observes the tree again must
    see a changed stage closure, or the currency check in ``_check_class_binding``
    would silently accept stale evidence. Importing modules and writing
    ``__pycache__`` does not alter it, because only tracked source bytes
    participate.

    ``None`` means the closure cannot be established (a synthetic root, a
    partial checkout, an uninitialized submodule). A caller must then REFUSE the
    scope-owned class rather than substitute a broader closure; widening is how a
    gate ends up admitting stale per-scope evidence while looking green.
    """
    from infrastructure.validation.rendered_snapshot import RenderedSnapshotError, _fingerprint, _stage_records

    if require_submodules and uninitialized_submodules(root):
        # A smaller closure is not a different state of the same tree; it is an
        # incomplete observation of it.
        return None
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
            # Refuse, never widen. Widening to ``repository_fingerprint`` here is
            # a different and stronger claim than the one the gate owns, and it
            # makes every scope-owned class inert on any checkout whose stage
            # closure is incomplete -- which is every runner that does not
            # initialize declared submodules.
            raise ClassUnavailable(kind, str(getattr(requirement, "scope", "")), unavailable_cause(root))
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


# Kinds whose evidence genuinely cannot be produced in a local checkout. A
# Darwin window-server observation, a real upload/retrieval custody proof, and
# the cross-host Root cells are properties of the host, not of the commit, so a
# local run cannot re-establish them.
_HOSTED_ONLY_KINDS = frozenset({"platform", "transfer"})
_HOSTED_ONLY_ROOT_CASE_PLATFORMS = frozenset({"darwin"})


def hosted_required(requirements: Any) -> bool:
    """Return whether any required class can only be produced on a hosted run."""
    for requirement in requirements:
        if getattr(requirement, "kind", "") in _HOSTED_ONLY_KINDS:
            return True
        if (
            getattr(requirement, "kind", "") == "root-case"
            and getattr(requirement, "case_platform", "") in _HOSTED_ONLY_ROOT_CASE_PLATFORMS
        ):
            return True
    return False


def _compose(values: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for key in sorted(values):
        digest.update(key.encode())
        digest.update(b"\0")
        digest.update(values[key].encode())
        digest.update(b"\n")
    return digest.hexdigest()
