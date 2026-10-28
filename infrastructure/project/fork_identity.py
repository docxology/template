"""Fork identity for a copied exemplar: SDK binding and authorship.

`copy_exemplar` moves files; this module makes the copy describe itself. A fork
must resolve the platform SDK from a build input it can actually reach, and it
must not inherit the source exemplar's authors, DOI, ORCID or repository URL.
"""

from __future__ import annotations

import json
import os
import re
import tomllib
from pathlib import Path

import yaml

_SDK_PACKAGE = "research-project-template"
_SDK_SOURCE_LINE = re.compile(rf"^{re.escape(_SDK_PACKAGE)}\s*=\s*\{{[^}}]*\}}\s*$", re.MULTILINE)
_PYPROJECT_AUTHORS = re.compile(r"^authors\s*=\s*\[.*?\]\s*$", re.MULTILINE | re.DOTALL)


def apply_fork_identity(
    destination: Path,
    *,
    repo_root: Path,
    sdk_source: str | None,
    author_name: str | None,
    author_email: str | None,
) -> None:
    """Make the copied tree self-describing as a fork.

    The SDK requirement is the fork's build input: an in-checkout copy keeps a
    correct relative path, and an opt-in ``sdk_source`` rewrites it for a tree
    that lives outside the checkout. Author fields are rewritten only when the
    caller states the fork's own identity.
    """
    pyproject = destination / "pyproject.toml"
    if not pyproject.is_file():
        return
    text = pyproject.read_text(encoding="utf-8")
    rewritten = _rewrite_sdk_source(text, destination=destination, repo_root=repo_root, sdk_source=sdk_source)
    if author_name is not None:
        rewritten = _rewrite_pyproject_authors(rewritten, author_name=author_name, author_email=author_email)
    if rewritten != text:
        pyproject.write_text(rewritten, encoding="utf-8")
    if author_name is not None:
        version = _pyproject_version(rewritten)
        _rewrite_citation_authors(destination, author_name=author_name, author_email=author_email, version=version)
        for name in ("codemeta.json", ".zenodo.json"):
            _rewrite_json_author(
                destination / name, author_name=author_name, author_email=author_email, version=version
            )


def _pyproject_version(text: str) -> str | None:
    """Return the fork's own declared version, or ``None`` when unreadable."""
    try:
        payload = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return None
    version = payload.get("project", {}).get("version")
    return version if isinstance(version, str) and version.strip() else None


def _parse_sdk_source(spec: str, destination: Path) -> tuple[str, str]:
    """Parse ``path:``, ``url:`` or ``version-only`` and validate a local path."""
    kind, _, value = spec.partition(":")
    kind = kind.strip()
    value = value.strip()
    if kind == "version-only":
        return kind, ""
    if kind == "url":
        if not value:
            raise ValueError("--sdk-source url: requires a URL or VCS reference")
        return kind, value
    if kind == "path":
        if not value:
            raise ValueError("--sdk-source path: requires a directory containing the template SDK")
        candidate = Path(value).expanduser()
        resolved = candidate if candidate.is_absolute() else (destination / candidate).resolve()
        pyproject = resolved / "pyproject.toml"
        if not resolved.is_dir() or not pyproject.is_file():
            raise ValueError(f"--sdk-source path: {value!r} is not a template SDK checkout")
        try:
            declared = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["name"]
        except (tomllib.TOMLDecodeError, KeyError) as error:
            raise ValueError(f"--sdk-source path: {value!r} has no readable [project].name") from error
        if declared != _SDK_PACKAGE:
            raise ValueError(f"--sdk-source path: {value!r} declares {declared!r}, not {_SDK_PACKAGE!r}")
        return kind, candidate.as_posix()
    raise ValueError("--sdk-source must start with path:, url: or be version-only")


def _rewrite_sdk_source(text: str, *, destination: Path, repo_root: Path, sdk_source: str | None) -> str:
    """Point the exemplar's SDK requirement at the fork's actual build input."""
    line = _SDK_SOURCE_LINE.search(text)
    if sdk_source is None:
        # A copy that stays inside the checkout keeps a resolvable relative path for
        # its own depth. A copy *outside* the checkout must not embed a path back
        # into this repository: that is an undeclared external provider for the
        # standalone projection and publication lanes, so the original declaration
        # is left exactly as the publication tooling expects.
        if not destination.is_relative_to(repo_root):
            return text
        relative = Path(os.path.relpath(repo_root, destination)).as_posix()
        if line is None or f'path = "{relative}"' in line.group(0):
            return text
        replacement = f'{_SDK_PACKAGE} = {{ path = "{relative}", editable = true }}'
        return text[: line.start()] + replacement + text[line.end() :]
    kind, value = _parse_sdk_source(sdk_source, destination)
    if kind == "version-only":
        if line is None:
            return text
        return text[: line.start()] + text[line.end() :].lstrip("\n")
    replacement = (
        f'{_SDK_PACKAGE} = {{ url = "{value}" }}'
        if kind == "url"
        else f'{_SDK_PACKAGE} = {{ path = "{value}", editable = true }}'
    )
    if line is not None:
        return text[: line.start()] + replacement + text[line.end() :]
    anchor = "\n[tool.uv.sources]\n" if "[tool.uv.sources]" in text else "\n[tool.uv.sources]\n"
    block = f"{anchor}{replacement}\n"
    if "[tool.template]" in text:
        return text.replace("\n[tool.template]", block + "\n[tool.template]", 1)
    return text.rstrip("\n") + "\n" + block


def _rewrite_pyproject_authors(text: str, *, author_name: str, author_email: str | None) -> str:
    """Replace the fork's author entry, keeping the surrounding TOML intact."""
    if author_email:
        entry = f'    {{ name = "{author_name}", email = "{author_email}" }},'
    else:
        entry = f'    {{ name = "{author_name}" }},'
    block = f"authors = [\n{entry}\n]"
    if _PYPROJECT_AUTHORS.search(text):
        return _PYPROJECT_AUTHORS.sub(block, text, count=1)
    return text.replace("\n[project]", f"\n[project]\n{block}\n", 1)


def _split_author_name(author_name: str) -> tuple[str, str]:
    """Split ``"Given Family"`` into given names and family name."""
    parts = author_name.split()
    if len(parts) < 2:
        return author_name, author_name
    return " ".join(parts[:-1]), parts[-1]


_CITATION_ORIGINAL_KEYS = ("doi", "repository-code", "date-released")
_JSON_ORIGINAL_KEYS = ("identifier", "codeRepository", "related_identifiers")


def _rewrite_citation_authors(
    destination: Path, *, author_name: str, author_email: str | None, version: str | None
) -> None:
    """Replace the CFF authors and drop the source artifact's own identifiers.

    A fork that keeps the source DOI, repository URL or release date would claim
    someone else's publication identity, so those fields are removed rather than
    copied. The version follows the fork's own package metadata.
    """
    citation = destination / "CITATION.cff"
    if not citation.is_file():
        return
    try:
        payload = yaml.safe_load(citation.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return
    if not isinstance(payload, dict):
        return
    given, family = _split_author_name(author_name)
    entry: dict[str, str] = {"family-names": family, "given-names": given}
    if author_email:
        entry["email"] = author_email
    payload["authors"] = [entry]
    for key in _CITATION_ORIGINAL_KEYS:
        payload.pop(key, None)
    if version:
        payload["version"] = version
    citation.write_text(yaml.safe_dump(payload, sort_keys=True, allow_unicode=True), encoding="utf-8")


def _rewrite_json_author(path: Path, *, author_name: str, author_email: str | None, version: str | None) -> None:
    """Rewrite a JSON metadata author entry and drop the source identifiers."""
    if not path.is_file():
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    if not isinstance(payload, dict):
        return
    given, family = _split_author_name(author_name)
    if "creators" in payload:
        creator: dict[str, str] = {"name": f"{family}, {given}"}
        if author_email:
            creator["email"] = author_email
        payload["creators"] = [creator]
    if "author" in payload:
        author: dict[str, str] = {"@type": "Person", "familyName": family, "givenName": given}
        if author_email:
            author["email"] = author_email
        payload["author"] = [author] if isinstance(payload["author"], list) else author
    for key in _JSON_ORIGINAL_KEYS:
        payload.pop(key, None)
    if version and "version" in payload:
        payload["version"] = version
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


__all__ = ["apply_fork_identity"]
