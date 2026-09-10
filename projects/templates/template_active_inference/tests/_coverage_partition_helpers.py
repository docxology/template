from __future__ import annotations
import shutil
from pathlib import Path
from orchestration import full_verification


def _write_coverage_partition_tree(tmp_path: Path) -> Path:
    """Create a minimal real-file tree satisfying the live coverage partition."""
    live_root = Path(__file__).resolve().parents[1]
    for module in full_verification._all_test_modules(live_root):
        source = live_root / module
        target = tmp_path / module
        target.parent.mkdir(parents=True, exist_ok=True)
        if module == full_verification._SEMANTIC_SHEAF_COVERAGE_MODULE:
            shutil.copyfile(source, target)
        else:
            target.write_text("# coverage partition fixture\n", encoding="utf-8")
    return tmp_path


def _copied_coverage_groups(project_root: Path) -> list[tuple[str, list[str]]]:
    """Return mutable copies of the validated live coverage groups."""
    return [
        (label, list(selectors)) for label, selectors in full_verification._validated_coverage_test_groups(project_root)
    ]
