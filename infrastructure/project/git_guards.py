"""Git index guards for tracked projects and generated artifacts."""

from __future__ import annotations

import fnmatch
import hashlib
import re
import subprocess
from pathlib import Path

from infrastructure.core.files.portability import PUBLICATION_TEXT_SUFFIXES
from infrastructure.fonds.public_scope import PUBLIC_FOND_NAMES
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.rules.public_scope import PUBLIC_RULE_NAMES
from infrastructure.tools.public_scope import PUBLIC_TOOL_NAMES

_GIT_TIMEOUT_SEC = 60

# Derived from PUBLIC_PROJECT_NAMES — the single roster source of truth — so it
# can never drift from the public exemplar roster. (Before 2026-06-10 this was a
# hand-maintained literal.)
ALLOWED_PROJECT_DIRS: tuple[str, ...] = tuple(f"projects/{name}/" for name in PUBLIC_PROJECT_NAMES)

ALLOWED_FONDS_TOPLEVEL_FILES: frozenset[str] = frozenset(
    {
        "fonds/AGENTS.md",
        "fonds/README.md",
    }
)
ALLOWED_FOND_DIRS: tuple[str, ...] = tuple(f"fonds/{name}/" for name in PUBLIC_FOND_NAMES)

ALLOWED_RULES_TOPLEVEL_FILES: frozenset[str] = frozenset(
    {
        "rules/AGENTS.md",
        "rules/README.md",
    }
)
ALLOWED_RULE_DIRS: tuple[str, ...] = tuple(f"rules/{name}/" for name in PUBLIC_RULE_NAMES)

ALLOWED_TOOLS_TOPLEVEL_FILES: frozenset[str] = frozenset(
    {
        "tools/AGENTS.md",
        "tools/README.md",
    }
)
ALLOWED_TOOL_DIRS: tuple[str, ...] = tuple(f"tools/{name}/" for name in PUBLIC_TOOL_NAMES)

# Navigation docs that may live directly under projects/ or the public
# projects/templates/ directory. This is an EXPLICIT allowlist, not a wildcard:
# a name-blind `projects/[^/]+\.md` pattern would let any future top-level
# markdown file (notes, a leaked private roster, an accidental
# `git add -f projects/secret.md`) sail past the confidentiality guard. Adding
# a new nav doc is a deliberate act that must be made here.
ALLOWED_PROJECTS_TOPLEVEL_FILES: frozenset[str] = frozenset(
    {
        "projects/AGENTS.md",
        "projects/PAI.md",
        "projects/PROJECTS_PARADIGM.md",
        "projects/README.md",
        "projects/templates/AGENTS.md",
        "projects/templates/DESIGN.md",
    }
)


class _ExplicitToplevelAllowlist:
    """`.match()`-compatible shim over the explicit nav-doc allowlist.

    Preserves the historical ``ALLOWED_PROJECTS_TOPLEVEL.match(path)`` call site
    in :mod:`infrastructure.project.codegraph` while swapping the permissive
    wildcard regex for a closed set. Returns a truthy object on an exact match,
    ``None`` otherwise — matching ``re.Pattern.match`` truthiness semantics.
    """

    def match(self, path: str) -> str | None:
        """Process match."""
        return path if path in ALLOWED_PROJECTS_TOPLEVEL_FILES else None


ALLOWED_PROJECTS_TOPLEVEL = _ExplicitToplevelAllowlist()

ALWAYS_GENERATED_ARTIFACT_PATTERNS: tuple[str, ...] = (
    ".codegraph",
    ".codegraph/*",
    ".leann",
    ".leann/*",
    ".omo",
    ".omo/*",
    ".coverage",
    ".coverage.*",
    ".DS_Store",
    "*/.codegraph",
    "*/.codegraph/*",
    "*/.leann",
    "*/.leann/*",
    "*/.omo",
    "*/.omo/*",
    "*/.DS_Store",
    "*.egg-info/*",
    "*/.egg-info/*",
    "coverage.json",
    "coverage*.xml",
    "coverage_project.json",
    "htmlcov/*",
)

GENERATED_OUTPUT_PATTERNS: tuple[str, ...] = (
    "output/*",
    "projects/*/output/*",
    "projects/*/*/output/*",
)

PUBLIC_TEMPLATE_OUTPUT_PREFIXES: tuple[str, ...] = tuple(
    f"projects/{name}/output/" for name in PUBLIC_PROJECT_NAMES if name.startswith("templates/")
)

PUBLIC_TEMPLATE_OUTPUT_MAX_BYTES = 50 * 1024 * 1024
PUBLIC_TEMPLATE_OUTPUT_MAX_FILES = 3500
PUBLIC_TEMPLATE_OUTPUT_MAX_TOTAL_BYTES = 200 * 1024 * 1024
PUBLIC_TEMPLATE_OUTPUT_MAX_DUPLICATE_BYTES = 100 * 1024 * 1024
# Advisory per-file ceiling: a single tracked evidence file above this is
# presumed non-regenerable until proven otherwise. Sits well below the 50MB
# hard cap so files approaching the cap surface for review before they become
# a problem, while legitimate regenerable evidence (PDFs, corpora) stays
# green.
PUBLIC_TEMPLATE_OUTPUT_MAX_SINGLE_FILE_BYTES = 20 * 1024 * 1024
_MACHINE_LOCAL_HOME_RE = re.compile(
    rb"(?:"
    rb"(?:file://)?/(?:Users|home)/[^/\s\"'<>]+/"
    rb"|"
    rb"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s\"'<>]+[\\/]+"
    rb")"
)
_PUBLIC_OUTPUT_SECRET_RES: tuple[re.Pattern[bytes], ...] = (
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{30,255}\b"),
    re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,255}\b"),
)
_TRACKED_SECRET_RES: tuple[tuple[str, re.Pattern[bytes]], ...] = (
    ("github-token", re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{30,255}\b")),
    ("aws-access-key", re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("openai-token", re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,255}\b")),
    (
        "private-key",
        re.compile(
            rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
            rb"\s+[A-Za-z0-9+/=\r\n]{64,}"
            rb"-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
        ),
    ),
)
_DOCUMENTED_SECRET_FIXTURE_FRAGMENTS = (
    b"abcdefghijklmnopqrstuvwxyz",
    b"abcdefghijklmnop",
    b"123456",
    b"should_never_be_sent",
    b"secret_material_must_not_be_logged",
)
_STAGED_BLOB_MODES = frozenset({b"100644", b"100755", b"120000"})
_STAGED_GITLINK_MODE = b"160000"


def is_public_template_output_path(path: str) -> bool:
    """Check whether public template output path."""
    normalized = path.replace("\\", "/")
    return any(normalized.startswith(prefix) for prefix in PUBLIC_TEMPLATE_OUTPUT_PREFIXES)


def offending_tracked_projects(repo_root: Path) -> list[str]:
    """Return the list of offending tracked projects."""
    return _offending_tracked_paths(
        repo_root,
        path_prefix="projects/",
        allowed_toplevel=ALLOWED_PROJECTS_TOPLEVEL_FILES,
        allowed_dirs=ALLOWED_PROJECT_DIRS,
    )


def offending_tracked_fonds(repo_root: Path) -> list[str]:
    """Return the list of offending tracked fonds."""
    return _offending_tracked_paths(
        repo_root,
        path_prefix="fonds/",
        allowed_toplevel=ALLOWED_FONDS_TOPLEVEL_FILES,
        allowed_dirs=ALLOWED_FOND_DIRS,
    )


def offending_tracked_rules(repo_root: Path) -> list[str]:
    """Return the list of offending tracked rules."""
    return _offending_tracked_paths(
        repo_root,
        path_prefix="rules/",
        allowed_toplevel=ALLOWED_RULES_TOPLEVEL_FILES,
        allowed_dirs=ALLOWED_RULE_DIRS,
    )


def offending_tracked_tools(repo_root: Path) -> list[str]:
    """Return the list of offending tracked tools."""
    return _offending_tracked_paths(
        repo_root,
        path_prefix="tools/",
        allowed_toplevel=ALLOWED_TOOLS_TOPLEVEL_FILES,
        allowed_dirs=ALLOWED_TOOL_DIRS,
    )


def _offending_tracked_paths(
    repo_root: Path,
    *,
    path_prefix: str,
    allowed_toplevel: frozenset[str],
    allowed_dirs: tuple[str, ...],
) -> list[str]:
    proc = subprocess.run(
        ["git", "ls-files", "-z", path_prefix],
        cwd=repo_root,
        check=True,
        capture_output=True,
        timeout=_GIT_TIMEOUT_SEC,
    )
    paths = [p for p in proc.stdout.decode("utf-8").split("\0") if p]
    offenders: list[str] = []
    for path in paths:
        normalized = path.replace("\\", "/")
        if normalized in allowed_toplevel:
            continue
        if any(normalized.startswith(prefix) for prefix in allowed_dirs):
            continue
        offenders.append(normalized)
    return sorted(offenders)


def is_generated_artifact_path(path: str) -> bool:
    """Check whether generated artifact path."""
    normalized = path.replace("\\", "/")
    if any(fnmatch.fnmatch(normalized, pattern) for pattern in ALWAYS_GENERATED_ARTIFACT_PATTERNS):
        return True
    if is_public_template_output_path(normalized):
        return False
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in GENERATED_OUTPUT_PATTERNS)


def is_oversized_public_template_output(
    repo_root: Path, path: str, *, max_bytes: int = PUBLIC_TEMPLATE_OUTPUT_MAX_BYTES
) -> bool:
    """Check whether oversized public template output."""
    normalized = path.replace("\\", "/")
    if not is_public_template_output_path(normalized):
        return False
    try:
        return (repo_root / normalized).stat().st_size > max_bytes
    except OSError:
        return False


def is_hidden_public_template_output(path: str) -> bool:
    """Return whether a tracked public output path is a local dotfile.

    Canonical exemplar output is publication evidence. Hidden files in that
    tree are caches, workspace markers, or interrupted atomic-write leftovers,
    not portable evidence that should enter the Git index.
    """
    normalized = path.replace("\\", "/")
    if not is_public_template_output_path(normalized):
        return False
    relative = next(
        normalized[len(prefix) :] for prefix in PUBLIC_TEMPLATE_OUTPUT_PREFIXES if normalized.startswith(prefix)
    )
    return any(part.startswith(".") for part in Path(relative).parts)


def is_empty_public_template_output(repo_root: Path, path: str) -> bool:
    """Return whether a tracked public output payload is unexpectedly empty."""
    normalized = path.replace("\\", "/")
    if not is_public_template_output_path(normalized):
        return False
    if Path(normalized).name in {".gitignore", ".gitkeep", "__init__.py"}:
        return False
    candidate = repo_root / normalized
    try:
        return candidate.is_file() and candidate.stat().st_size == 0
    except OSError:
        return False


def tracked_generated_artifacts(
    repo_root: Path, *, public_output_max_bytes: int = PUBLIC_TEMPLATE_OUTPUT_MAX_BYTES
) -> list[str]:
    """Return the set of tracked generated artifacts."""
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        timeout=_GIT_TIMEOUT_SEC,
    )
    paths = [p for p in proc.stdout.decode("utf-8").split("\0") if p]
    return sorted(
        path
        for path in paths
        if is_generated_artifact_path(path)
        or is_hidden_public_template_output(path)
        or is_empty_public_template_output(repo_root, path)
        or is_oversized_public_template_output(repo_root, path, max_bytes=public_output_max_bytes)
    )


def public_template_output_budget_findings(
    repo_root: Path,
    *,
    max_files: int = PUBLIC_TEMPLATE_OUTPUT_MAX_FILES,
    max_total_bytes: int = PUBLIC_TEMPLATE_OUTPUT_MAX_TOTAL_BYTES,
    max_duplicate_bytes: int = PUBLIC_TEMPLATE_OUTPUT_MAX_DUPLICATE_BYTES,
    max_single_file_bytes: int = PUBLIC_TEMPLATE_OUTPUT_MAX_SINGLE_FILE_BYTES,
) -> list[str]:
    """Return ratchet violations for canonical tracked exemplar evidence."""
    proc = subprocess.run(
        ["git", "ls-files", "-z", "projects/templates/*/output/**"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        timeout=_GIT_TIMEOUT_SEC,
    )
    paths = [path for path in proc.stdout.decode("utf-8").split("\0") if path]
    total_bytes = 0
    blobs: dict[str, tuple[int, int]] = {}
    oversized_single: list[str] = []
    for path in paths:
        try:
            data = (repo_root / path).read_bytes()
        except OSError:
            continue
        size = len(data)
        total_bytes += size
        digest = hashlib.sha256(data).hexdigest()
        prior_size, prior_count = blobs.get(digest, (size, 0))
        blobs[digest] = (prior_size, prior_count + 1)
        if max_single_file_bytes > 0 and size > max_single_file_bytes:
            oversized_single.append(f"{path} ({size} bytes)")
    duplicate_bytes = sum(size * (count - 1) for size, count in blobs.values() if count > 1)

    findings: list[str] = []
    if len(paths) > max_files:
        findings.append(f"public output file count {len(paths)} exceeds {max_files}")
    if total_bytes > max_total_bytes:
        findings.append(f"public output aggregate bytes {total_bytes} exceeds {max_total_bytes}")
    if duplicate_bytes > max_duplicate_bytes:
        findings.append(f"public output duplicate bytes {duplicate_bytes} exceeds {max_duplicate_bytes}")
    if oversized_single:
        findings.append(
            "public output single-file bytes exceed advisory ceiling "
            f"{max_single_file_bytes}: " + ", ".join(sorted(oversized_single))
        )
    return findings


def tracked_public_output_local_paths(repo_root: Path) -> list[str]:
    """Return tracked public output files that leak a machine-local home path.

    Canonical exemplar outputs are publication evidence and therefore need to
    be portable across clones. Restrict scanning to text-like extensions so
    binary payloads are never decoded or rejected for coincidental bytes.
    """
    local_paths, _secrets = tracked_public_output_leaks(repo_root)
    return local_paths


def tracked_public_output_secrets(repo_root: Path) -> list[str]:
    """Return tracked text evidence containing high-confidence secret formats.

    The patterns deliberately cover only structured credential formats and
    private-key headers.  Generic words such as ``token`` or ``password`` are
    not evidence of a secret and would create an unsafe ignore culture.
    """
    _local_paths, secrets = tracked_public_output_leaks(repo_root)
    return secrets


def tracked_public_output_leaks(repo_root: Path) -> tuple[list[str], list[str]]:
    """Scan tracked publication text once for local paths and secrets."""
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        timeout=_GIT_TIMEOUT_SEC,
    )
    paths = [p for p in proc.stdout.decode("utf-8").split("\0") if p]
    local_paths: list[str] = []
    secrets: list[str] = []
    for path in paths:
        normalized = path.replace("\\", "/")
        if not is_public_template_output_path(normalized):
            continue
        if Path(normalized).suffix.lower() not in PUBLICATION_TEXT_SUFFIXES:
            continue
        try:
            content = (repo_root / normalized).read_bytes()
        except OSError:
            continue
        if _MACHINE_LOCAL_HOME_RE.search(content):
            local_paths.append(normalized)
        if any(pattern.search(content) for pattern in _PUBLIC_OUTPUT_SECRET_RES):
            secrets.append(normalized)
    return sorted(local_paths), sorted(secrets)


def tracked_secret_findings(repo_root: Path) -> list[str]:
    """Return high-confidence secret findings from every tracked text blob.

    The scanner intentionally reports only ``path:line:kind`` metadata and
    never prints the matched credential. Known low-entropy examples used by
    security tests and documentation are ignored; real credentials must not
    be hidden behind a broad test-directory exclusion.
    """
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        timeout=_GIT_TIMEOUT_SEC,
    )
    findings: list[str] = []
    for raw_path in proc.stdout.decode("utf-8").split("\0"):
        if not raw_path:
            continue
        path = raw_path.replace("\\", "/")
        try:
            content = (repo_root / path).read_bytes()
        except OSError:
            continue
        if b"\x00" in content[:4096]:
            continue
        for kind, pattern in _TRACKED_SECRET_RES:
            for match in pattern.finditer(content):
                value = match.group(0).lower()
                is_documented_fixture = any(fragment in value for fragment in _DOCUMENTED_SECRET_FIXTURE_FRAGMENTS)
                if kind != "private-key" and is_documented_fixture:
                    continue
                line = content.count(b"\n", 0, match.start()) + 1
                findings.append(f"{path}:{line}:{kind}")
    return sorted(set(findings))


def staged_diff_secret_findings(repo_root: Path) -> list[str]:
    """Return high-confidence secret findings from staged index blobs.

    Added, copied, modified, and renamed post-image paths come from
    ``git diff --cached --diff-filter=ACMR``. Stage-zero index metadata
    identifies regular-file and symlink blobs, which are read by object ID so
    partially staged worktree edits cannot hide a credential or create a false
    finding. Verified gitlinks are skipped; unknown modes, unresolved index
    stages, and unreadable blobs fail closed. Findings use the same
    ``path:line:kind`` format as :func:`tracked_secret_findings`.

    Binary files are skipped (NUL byte in the first 4096 bytes), matching the
    tracked-index scanner. Like :func:`tracked_secret_findings`, the scanner
    never prints the matched credential value.
    """
    proc = subprocess.run(
        [
            "git",
            "diff",
            "--cached",
            "--find-renames",
            "--find-copies",
            "--diff-filter=ACMR",
            "--name-only",
            "-z",
            "--",
        ],
        cwd=repo_root,
        check=True,
        capture_output=True,
        timeout=_GIT_TIMEOUT_SEC,
    )
    index_proc = subprocess.run(
        ["git", "ls-files", "--stage", "-z"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        timeout=_GIT_TIMEOUT_SEC,
    )
    index_entries: dict[bytes, list[tuple[bytes, bytes, bytes]]] = {}
    for row in index_proc.stdout.split(b"\0"):
        if not row:
            continue
        try:
            metadata, indexed_path = row.split(b"\t", 1)
            mode, object_id, stage = metadata.split(b" ", 2)
        except ValueError as exc:
            raise RuntimeError("malformed staged index metadata") from exc
        index_entries.setdefault(indexed_path, []).append((mode, object_id, stage))

    findings: list[str] = []
    for raw_path in proc.stdout.split(b"\0"):
        if not raw_path:
            continue
        entries = index_entries.get(raw_path, [])
        if len(entries) != 1 or entries[0][2] != b"0":
            raise RuntimeError("staged diff path has no unique stage-zero index entry")
        mode, object_id, _stage = entries[0]
        if mode == _STAGED_GITLINK_MODE:
            continue
        if mode not in _STAGED_BLOB_MODES:
            raise RuntimeError(f"unsupported staged index mode: {mode.decode('ascii', errors='replace')}")

        path = raw_path.decode("utf-8", errors="surrogateescape")
        blob = subprocess.run(
            ["git", "cat-file", "blob", object_id.decode("ascii")],
            cwd=repo_root,
            check=True,
            capture_output=True,
            timeout=_GIT_TIMEOUT_SEC,
        )
        content = blob.stdout
        if b"\x00" in content[:4096]:
            continue
        for kind, pattern in _TRACKED_SECRET_RES:
            for match in pattern.finditer(content):
                value = match.group(0).lower()
                is_documented_fixture = any(fragment in value for fragment in _DOCUMENTED_SECRET_FIXTURE_FRAGMENTS)
                if kind != "private-key" and is_documented_fixture:
                    continue
                line = content.count(b"\n", 0, match.start()) + 1
                findings.append(f"{path}:{line}:{kind}")
    return sorted(set(findings))
