"""Placeholder injection into manuscript markdown."""

from __future__ import annotations

import re

from manuscript.variables._logging import logger


def inject_variables(
    content: str,
    variables: dict[str, str],
    filename: str = "<unknown>",
    lenient: bool = False,
) -> str:
    replaced_count = 0
    missing_vars: list[str] = []

    def replacer(match: re.Match[str]) -> str:
        nonlocal replaced_count
        var_name = match.group(1)
        if var_name in variables:
            replaced_count += 1
            return variables[var_name]
        missing_vars.append(var_name)
        return match.group(0)

    result = re.sub(r"\{\{(\w+)\}\}", replacer, content)
    if replaced_count > 0:
        logger.info("Injected %d variables into %s", replaced_count, filename)
    if missing_vars:
        unique_missing = sorted(set(missing_vars))
        if lenient:
            logger.warning("Unresolved variables in %s: %s", filename, ", ".join(unique_missing))
        else:
            raise RuntimeError(f"Unresolved variables in {filename}: {', '.join(unique_missing)}")
    return result
