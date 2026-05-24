"""Review HTML generation for skill-eval harness runs."""

from __future__ import annotations

import json
import re
from pathlib import Path

from skill_eval.config import DEFAULT_RUN_DIR, REVIEW_TEMPLATE
from skill_eval.workspace import load_benchmark, load_gradings_by_eval


def build_embedded_data(run_dir: Path) -> dict:
    benchmark = load_benchmark(run_dir)
    gradings_by_eval = load_gradings_by_eval(run_dir)
    runs: list[dict] = []

    for eval_dir in sorted(p for p in run_dir.iterdir() if p.is_dir()):
        meta_path = eval_dir / "eval_metadata.json"
        if not meta_path.is_file():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        eval_name = meta["eval_name"]
        prompt = meta["prompt"]
        eval_id = meta["eval_id"]

        for mode in ("with_skill", "without_skill"):
            response_path = eval_dir / mode / "outputs" / "response.md"
            grading = gradings_by_eval.get(eval_name, {}).get(mode)
            if not response_path.is_file() or grading is None:
                continue
            runs.append(
                {
                    "id": f"{eval_name}-{mode}",
                    "prompt": prompt,
                    "eval_id": eval_id,
                    "outputs": [
                        {
                            "name": "response.md",
                            "type": "text",
                            "content": response_path.read_text(encoding="utf-8"),
                        }
                    ],
                    "grading": grading,
                    "configuration": mode,
                }
            )

    return {
        "skill_name": benchmark.get("skill_name", "template-workflows"),
        "runs": runs,
        "previous_feedback": {},
        "previous_outputs": {},
        "benchmark": benchmark,
    }


def inject_embedded_data(template_html: str, payload: dict) -> str:
    serialized = json.dumps(payload, ensure_ascii=False)
    pattern = r"const EMBEDDED_DATA = \{.*?\};"
    replacement = f"const EMBEDDED_DATA = {serialized};"
    if not re.search(pattern, template_html, flags=re.DOTALL):
        msg = "Template missing EMBEDDED_DATA assignment"
        raise ValueError(msg)
    return re.sub(pattern, replacement, template_html, count=1, flags=re.DOTALL)


def generate_review(run_dir: Path, *, template_path: Path = REVIEW_TEMPLATE) -> Path:
    if not template_path.is_file():
        msg = f"Review template not found: {template_path}"
        raise FileNotFoundError(msg)
    payload = build_embedded_data(run_dir)
    html = inject_embedded_data(template_path.read_text(encoding="utf-8"), payload)
    out_path = run_dir / "review.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path


def main() -> int:
    import sys

    if len(sys.argv) > 2:
        print(f"Usage: {Path(sys.argv[0]).name} [<run-dir>]", file=sys.stderr)
        return 2
    run_dir = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else DEFAULT_RUN_DIR.resolve()
    out = generate_review(run_dir)
    print(str(out))
    return 0
