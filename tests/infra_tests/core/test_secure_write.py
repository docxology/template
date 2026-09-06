"""Permission contract for the shared confined publication writer."""

from pathlib import Path
import stat

import pytest

from infrastructure.core.files.secure_write import atomic_write_text_confined


def test_confined_write_retains_default_publication_permissions(tmp_path: Path) -> None:
    target = tmp_path / "evidence.json"

    atomic_write_text_confined(tmp_path, target, '{"verified": true}')

    assert target.read_text(encoding="utf-8") == '{"verified": true}'
    assert stat.S_IMODE(target.stat().st_mode) == 0o644
    assert set(tmp_path.iterdir()) == {target}


@pytest.mark.parametrize("mode", [0o600, 0o640, 0o644])
def test_confined_write_applies_requested_permissions(tmp_path: Path, mode: int) -> None:
    target = tmp_path / "publication.html"
    target.write_text("old", encoding="utf-8")

    atomic_write_text_confined(tmp_path, target, "new", mode=mode)

    assert target.read_text(encoding="utf-8") == "new"
    assert stat.S_IMODE(target.stat().st_mode) == mode
    assert set(tmp_path.iterdir()) == {target}
