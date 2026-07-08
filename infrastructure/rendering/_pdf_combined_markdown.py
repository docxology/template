"""Combined markdown preprocessing for PDF rendering."""

from __future__ import annotations

import re

import yaml
from pathlib import Path
from typing import Any, NamedTuple

from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._pdf_mermaid import replace_inline_mermaid

logger = get_logger(__name__)

_FIG_PATH_REPLACEMENTS = [
    ("../../output/figures/", "../figures/"),
    ("../output/figures/", "../figures/"),
    ("output/figures/", "../figures/"),
]

_PLACEHOLDER_RE = re.compile(r"\{\{([^}]+)\}\}")

# Substitution boundary (do not merge with manuscript_injection.py):
# - This module: dotted YAML keys from flattened manuscript_vars (e.g. {{maturity.real}}).
# - manuscript_injection.py: UPPER_SNAKE project tokens from output/data/manuscript_variables.json.
# Regex patterns differ intentionally; unifying them is a separate behavior change.


class CombinedMarkdownResult(NamedTuple):
    """Result of preprocess_combined_markdown."""

    content: str
    mermaid_blocks_processed: int
    fig_paths_fixed: int
    manuscript_vars_substitutions: int


def flatten_manuscript_vars(data: Any, prefix: str = "") -> dict[str, str]:
    """Flatten nested YAML mapping to dotted keys with string values (for {{key}} substitution)."""
    flat: dict[str, str] = {}
    if isinstance(data, dict):
        for k, v in data.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            if isinstance(v, dict):
                flat.update(flatten_manuscript_vars(v, key))
            elif isinstance(v, list):
                flat[key] = ", ".join(str(x) for x in v)
            elif isinstance(v, bool):
                flat[key] = str(v).lower()
            elif v is None:
                flat[key] = ""
            else:
                flat[key] = str(v)
    return flat


def substitute_manuscript_var_placeholders(content: str, flat: dict[str, str]) -> tuple[str, int]:
    """Replace ``{{name}}`` placeholders using flattened manuscript_vars.

    Handles ``{{maturity.*}}`` and ``{{verify.*}}`` summaries. Unknown keys are left unchanged.
    """
    maturity_summary = (
        f"{flat.get('maturity.real', '?')} real, "
        f"{flat.get('maturity.partial', '?')} partial, "
        f"{flat.get('maturity.aspirational', '?')} aspirational"
    )
    verify_parts = [f"{k}={flat[k]}" for k in sorted(flat) if k.startswith("verify.")]
    verify_summary = "; ".join(verify_parts) if verify_parts else "(no verify metrics in manuscript_vars)"

    n_subs = 0

    def repl(match: re.Match[str]) -> str:
        """Process repl."""
        nonlocal n_subs
        key = match.group(1).strip()
        if key == "maturity.*":
            n_subs += 1
            return maturity_summary
        if key == "verify.*":
            n_subs += 1
            return verify_summary
        if key in flat:
            n_subs += 1
            return flat[key]
        return match.group(0)

    out = _PLACEHOLDER_RE.sub(repl, content)
    return out, n_subs


def preprocess_combined_markdown(
    combined_content: str,
    manuscript_dir: Path | None = None,
) -> CombinedMarkdownResult:
    """Render Mermaid fences, normalise figure paths, and substitute variables.

    If ``manuscript_dir/manuscript_vars.yaml`` exists, ``{{dotted.key}}`` placeholders in the
    combined markdown are replaced with string values from the flattened YAML tree. Special
    keys ``{{maturity.*}}`` and ``{{verify.*}}`` expand to short summaries.

    Returns:
        CombinedMarkdownResult with processed content and counts of Mermaid renders,
        figure path fixes, and variable substitutions.
    """
    mermaid_result = replace_inline_mermaid(combined_content, manuscript_dir)
    content = mermaid_result.content
    n_mermaid = mermaid_result.diagrams_rendered
    if n_mermaid:
        logger.info(f"✓ Rendered {n_mermaid} Mermaid diagram block(s) into combined markdown")
    else:
        logger.debug("No Mermaid blocks rendered in combined markdown")

    n_fig_paths = 0
    for old_prefix, new_prefix in _FIG_PATH_REPLACEMENTS:
        count = content.count(old_prefix)
        if count:
            content = content.replace(old_prefix, new_prefix)
            n_fig_paths += count
    if n_fig_paths:
        logger.info(f"✓ Normalised {n_fig_paths} figure path(s) to ../figures/ in combined markdown")

    n_vars = 0
    if manuscript_dir is not None:
        vars_path = manuscript_dir / "manuscript_vars.yaml"
        if vars_path.is_file():
            try:
                raw = yaml.safe_load(vars_path.read_text(encoding="utf-8"))
            except (OSError, yaml.YAMLError) as e:
                logger.warning("Could not load manuscript_vars.yaml for placeholder substitution: %s", e)
            else:
                if raw is None:
                    raw = {}
                if isinstance(raw, dict):
                    flat = flatten_manuscript_vars(raw)

                    # Augment with synthetic variables if present
                    if isinstance(raw.get("topics"), dict):
                        topics_dict = raw["topics"]
                        flat["total_topics"] = str(len(topics_dict))
                        # Build synthetic topic data dynamically
                        for topic_id, topic_data in topics_dict.items():
                            if isinstance(topic_data, dict):
                                # lean_chars derived from lean_sketch
                                sketch = topic_data.get("lean_sketch", "")
                                flat[f"topics.{topic_id}.lean_chars"] = str(len(sketch))

                                # Update maturity display string and icon based on mathlib_status
                                ml_status = topic_data.get("mathlib_status", "")
                                if ml_status == "real":
                                    flat[f"topics.{topic_id}.maturity"] = "real"
                                    flat[f"topics.{topic_id}.maturity_icon"] = "✅"
                                elif ml_status == "partial":
                                    flat[f"topics.{topic_id}.maturity"] = "partial"
                                    flat[f"topics.{topic_id}.maturity_icon"] = "🔶"
                                elif ml_status == "aspirational":
                                    flat[f"topics.{topic_id}.maturity"] = "aspirational"
                                    flat[f"topics.{topic_id}.maturity_icon"] = "🔷"

                    if isinstance(raw.get("areas"), dict):
                        areas_dict = raw["areas"]
                        flat["total_areas"] = str(len(areas_dict))
                        # Alias areas.X -> areas.X.count for legacy scalar
                        # shapes only. Nested {count: N} entries are already
                        # flattened to areas.X.count by flatten_manuscript_vars;
                        # overwriting with str(dict) would emit "{'count': N}".
                        for area_name, area_value in areas_dict.items():
                            if isinstance(area_value, dict):
                                continue
                            flat[f"areas.{area_name}.count"] = str(area_value)

                    content, n_vars = substitute_manuscript_var_placeholders(content, flat)
                    if n_vars:
                        logger.info(
                            "✓ Substituted %s manuscript_vars placeholder(s) from %s",
                            n_vars,
                            vars_path.name,
                        )
                else:
                    logger.warning("manuscript_vars.yaml root must be a mapping; skipping placeholder substitution")

    return CombinedMarkdownResult(content, n_mermaid, n_fig_paths, n_vars)
