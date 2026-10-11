"""Compile the actual Source web stylesheet and original AST text ancestry.

Candidate computed styles never define expected font family, weight or italic
ancestry. Browser defaults and unmodeled styles retain independent obligations.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest

STYLE_SCHEMA = "template-original-source-html-styles-v1"
SOURCE_UA_CALIBRATION_BLOCKER = "actual independent Source writer/Chromium UA font-size calibration is required"


def compile_source_html_styles(stylesheet: bytes, config: bytes) -> dict[str, Any]:
    """Read the Source renderer's finite authored rules, not candidate HTML CSS."""
    if len(stylesheet) > 1024 * 1024 or len(config) > 4 * 1024 * 1024:
        raise ValueError("Source HTML stylesheet/config exceeds its finite bound")
    css = re.sub(r"/\*.*?\*/", "", stylesheet.decode("utf-8"), flags=re.S)
    rules: dict[str, dict[str, str]] = {}
    # These selectors occur outside media rules in the actual Source stylesheet.
    for selector in (
        "body",
        "code",
        "h1, h2, h3, h4, h5, h6",
        "a",
        "th",
        "pre",
        ".figure-caption",
    ):
        match = re.search(r"(?:^|\})\s*" + re.escape(selector) + r"\s*\{([^{}]*)\}", css)
        if match is None:
            raise ValueError("Source HTML stylesheet omitted the declared authored selector " + selector)
        rules[selector] = {}
        for declaration in match[1].split(";"):
            if not declaration.strip():
                continue
            key, value = declaration.split(":", 1)
            rules[selector][key.strip()] = value.strip()
    families = {}
    for role, selector in (("body", "body"), ("code", "code")):
        family = rules[selector].get("font-family")
        if not family:
            raise ValueError("Source HTML authored family is missing")
        families[role] = [item.strip().strip("'\"") for item in family.split(",")]
    for values in families.values():
        if not values or any(not re.fullmatch(r"[A-Za-z0-9 _-]{1,128}", item) for item in values):
            raise ValueError("Source HTML font family syntax is not modeled")
    base = {
        "schema_version": STYLE_SCHEMA,
        "stylesheet_sha256": hashlib.sha256(stylesheet).hexdigest(),
        "source_config_sha256": hashlib.sha256(config).hexdigest(),
        "families": families,
        "authored_rules": rules,
        "stylesheet_text": stylesheet.decode("utf-8"),
        "default_style_contract": {
            "writer": "actual Source-selected Pandoc standalone html5 template/default stylesheet",
            "user_agent": "independent bounded actual Chromium Source-only document",
            "font_size_expectation": "Source template and original tag ancestry; candidate font_px cannot nominate it",
        },
        "config_typography_applied_by_current_web_renderer": False,
        "blockers": [
            SOURCE_UA_CALIBRATION_BLOCKER,
            "actual Chromium consumed shaping/hinting and loaded runtime require their independent observations",
        ],
    }
    return {**base, "digest": canonical_digest(base)}


def expected_source_text_style(profile: dict[str, Any], ancestry: list[str]) -> dict[str, Any]:
    """Retain original Strong/Emph/Header/Code roles and explicit Source colors."""
    if profile.get("schema_version") != STYLE_SCHEMA or profile.get("digest") != canonical_digest(
        {key: value for key, value in profile.items() if key != "digest"}
    ):
        raise ValueError("Source-authored HTML style profile changed")
    rules = profile["authored_rules"]
    code = any(tag in {"Code", "CodeBlock"} for tag in ancestry)
    header = next((tag for tag in ancestry if tag.startswith("Header:")), None)
    table_head = any(tag in {"TableHead", "TableRowHead"} for tag in ancestry)
    weight = 700 if "Strong" in ancestry or header or table_head else 400
    italic = "Emph" in ancestry
    color = rules["body"].get("color")
    if header:
        color = rules["h1, h2, h3, h4, h5, h6"].get("color", color)
    if "CodeBlock" in ancestry:
        color = rules["pre"].get("color", color)
    if "Link" in ancestry:
        color = rules["a"].get("color", color)
    if table_head and "Link" not in ancestry:
        color = rules["th"].get("color", color)
    background = rules["body"].get("background-color")
    if code:
        background = rules["pre" if "CodeBlock" in ancestry else "code"].get("background-color", background)
    if table_head:
        background = rules["th"].get("background-color", background)
    blockers = []
    unsupported = {
        "SmallCaps",
        "Superscript",
        "Subscript",
        "Underline",
        "Strikeout",
    }.intersection(ancestry)
    if unsupported:
        blockers.append(
            "original Source inline presentation requires its exact projection: " + ",".join(sorted(unsupported))
        )
    role = "code" if code else "body"
    family = profile["families"][role][0]
    bases = {
        "Liberation Serif": "LiberationSerif",
        "Liberation Mono": "LiberationMono",
        "Liberation Sans": "LiberationSans",
    }
    physical = bases.get(family)
    if physical is None:
        blockers.append("Source-authored primary family needs independently resolved physical font: " + family)
    elif weight == 700 and italic:
        physical += "-BoldItalic"
    elif weight == 700:
        physical += "-Bold"
    elif italic:
        physical += "-Italic"
    return {
        "source_style_digest": profile["digest"],
        "original_ancestry": ancestry,
        "font_role": role,
        "family": family,
        "expected_postscript_name": physical,
        "font_weight": str(weight),
        "font_style": "italic" if italic else "normal",
        "authored_color": color,
        "authored_background": background,
        "default_style_contract": profile["default_style_contract"],
        "direction": "ltr",
        "kerning": "auto",
        "ligatures": "normal",
        "blockers": blockers,
    }
