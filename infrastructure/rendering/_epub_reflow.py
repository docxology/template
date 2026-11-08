"""Keep intrinsic EPUB content within the reader viewport without clipping it."""

from __future__ import annotations

import os
import stat
import tempfile
import zipfile
from pathlib import Path

from infrastructure.rendering._epub_package_validation import _preflight_members

_REFLOW_RULES = """
/* Keep content reader-sized; oversized blocks remain horizontally scrollable. */
body {
  overflow-wrap: anywhere;
}
table {
  display: block;
  max-width: 100%;
  overflow-x: auto;
}
pre {
  max-width: 100%;
  overflow-x: auto;
}
math {
  max-width: 100%;
  overflow-x: auto;
}
math[display="block"] {
  display: block;
}
"""


def apply_epub_reflow(epub_path: Path) -> None:
    """Extend packaged styles while preserving theme, markup, and ZIP custody.

    Apply layout rules before effective-package identity finalization. Existing
    stylesheet bytes, including reader color schemes, remain intact; chapter
    text, image bytes, and the EPUB manifest are never rewritten by this pass.
    """
    if epub_path.is_symlink():
        raise ValueError(f"refusing to rewrite EPUB through symlink: {epub_path}")
    original_mode = stat.S_IMODE(epub_path.stat().st_mode)
    temporary_path: Path | None = None
    try:
        with zipfile.ZipFile(epub_path) as source:
            members = _preflight_members(source.infolist())
            replacements: dict[str, bytes] = {}
            for name, info in members.items():
                if info.is_dir() or not name.lower().endswith(".css"):
                    continue
                payload = source.read(info)
                if payload.startswith(b"\xff\xfe"):
                    encoding = "utf-16-le"
                elif payload.startswith(b"\xfe\xff"):
                    encoding = "utf-16-be"
                else:
                    encoding = "utf-8"
                suffix = _REFLOW_RULES.encode(encoding)
                if not payload.endswith(suffix):
                    replacements[name] = payload + suffix
            if not replacements:
                return
            with tempfile.NamedTemporaryFile(
                prefix=f".{epub_path.name}.",
                suffix=".tmp",
                dir=epub_path.parent,
                delete=False,
            ) as handle:
                temporary_path = Path(handle.name)
            with zipfile.ZipFile(temporary_path, "w") as destination:
                destination.comment = source.comment
                for info in source.infolist():
                    replacement = replacements.get(info.filename)
                    destination.writestr(info, source.read(info) if replacement is None else replacement)
        assert temporary_path is not None
        temporary_path.chmod(original_mode)
        os.replace(temporary_path, epub_path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
