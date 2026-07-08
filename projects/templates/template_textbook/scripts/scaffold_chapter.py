"""Author tool: materialise missing chapter/lab/question stub files from config.

For every chapter declared in ``manuscript/config.yaml`` this writes (when
absent) a contract-satisfying stub:

* chapter   -> ``manuscript/<part>/<file>``
* lab       -> ``manuscript/labs/<part_id>/lab_<stem>.md``
* questions -> ``manuscript/questions/<part_id>/q_<stem>.md``

Existing files are left untouched unless ``--force`` is given. This is the
intended way to grow the book: add entries to ``config.yaml``, run this, then
fill the stubs.
"""

from __future__ import annotations

import argparse

from _bootstrap import PROJECT as PROJECT_DIR, ensure_project_paths

ensure_project_paths()


def main() -> int:
    """CLI entry point."""
    from textbook import content
    from textbook.config import iter_chapters, iter_unit_intros, load_config
    from textbook_io import write_text_atomic
    from textbook_logging import get_logger

    logger = get_logger(__name__)
    parser = argparse.ArgumentParser(description="Scaffold missing textbook stub files")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument("--part", help="Only scaffold chapters in this part id (e.g. part_I)")
    args = parser.parse_args()

    manuscript = PROJECT_DIR / "manuscript"
    config = load_config(manuscript)

    written = 0
    skipped = 0
    chapters_by_part: dict[str, list] = {}
    for chapter in iter_chapters(config):
        chapters_by_part.setdefault(chapter.part_id, []).append(chapter)

    for intro in iter_unit_intros(config):
        if args.part and intro.part_id != args.part:
            continue
        intro_path = intro.path(manuscript)
        intro_text = content.scaffold_unit_intro(intro, chapters_by_part.get(intro.part_id, []))
        if intro_path.exists() and not args.force:
            skipped += 1
        else:
            write_text_atomic(intro_path, intro_text)
            print(f"  ✓ {intro_path.relative_to(PROJECT_DIR)}")
            written += 1

    for chapter in iter_chapters(config):
        if args.part and chapter.part_id != args.part:
            continue
        targets = [
            (chapter.path(manuscript), content.scaffold_chapter(chapter)),
            (
                manuscript / "labs" / chapter.part_id / f"lab_{chapter.stem}.md",
                content.scaffold_lab(chapter),
            ),
            (
                manuscript / "questions" / chapter.part_id / f"q_{chapter.stem}.md",
                content.scaffold_question_bank(chapter),
            ),
        ]
        for path, text in targets:
            if path.exists() and not args.force:
                skipped += 1
                continue
            write_text_atomic(path, text)
            print(f"  ✓ {path.relative_to(PROJECT_DIR)}")
            written += 1

    logger.info("scaffold complete: %d written, %d skipped", written, skipped)
    print(f"[scaffold_chapter] {written} written, {skipped} skipped (use --force to overwrite)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
