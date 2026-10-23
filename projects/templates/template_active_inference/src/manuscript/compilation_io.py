"""Content-idempotent publication of compiled manuscript source."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CompiledTextStage:
    """Derived candidate bytes; filesystem reads still see actual Source."""

    root: Path
    candidates: dict[Path, bytes] = field(default_factory=dict)
    _publishable: bool = field(default=False, init=False, repr=False)

    def matches_current(self) -> bool:
        """Compare final candidates without changing any physical Source file."""
        return all(path.is_file() and path.read_bytes() == body for path, body in self.candidates.items())

    def publish(self) -> bool:
        """Use the ordinary writer once for each final candidate that differs."""
        if not self._publishable:
            raise RuntimeError("compiled Source publication requires a completed staging scope")
        changed = not self.matches_current()
        for path, body in self.candidates.items():
            _write_compiled_bytes(path, body)
        return changed


_STAGED_TEXT: ContextVar[CompiledTextStage | None] = ContextVar("active_compiled_text_stage", default=None)


@contextmanager
def stage_compiled_text(manuscript_root: Path) -> Iterator[CompiledTextStage]:
    """Defer intermediate composition writes during one real generation pass.

    Candidate DATA never replaces filesystem reads or Source admission. Publish
    only after this scope exits, then refresh evidence if Source bytes changed.
    """
    if _STAGED_TEXT.get() is not None:
        raise RuntimeError("compiled Source staging must have one fixed-point owner")
    root = manuscript_root.absolute()
    if ".." in root.parts or root != root.resolve():
        raise ValueError("compiled Source staging needs the fixed non-symlink manuscript root")
    stage = CompiledTextStage(root)
    token = _STAGED_TEXT.set(stage)
    try:
        yield stage
    except BaseException:
        stage.candidates.clear()
        raise
    finally:
        _STAGED_TEXT.reset(token)
    stage._publishable = True


def _write_compiled_bytes(path: Path, encoded: bytes) -> Path:
    if path.is_file() and path.read_bytes() == encoded:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)
    return path


def write_compiled_text(path: Path, content: str) -> Path:
    """Preserve physical source custody when final compilation bytes agree."""
    encoded = content.encode("utf-8")
    stage = _STAGED_TEXT.get()
    if stage is not None:
        absolute = path.absolute()
        if ".." in absolute.parts or not absolute.is_relative_to(stage.root):
            raise ValueError("compiled Source candidate escapes the fixed manuscript root")
        component = absolute
        while component != stage.root:
            if component.is_symlink():
                raise ValueError("compiled Source candidate contains a symlink")
            component = component.parent
        stage.candidates[absolute] = encoded
        return path
    return _write_compiled_bytes(path, encoded)
